#!/usr/bin/env python3
"""Erzeugt aus den über einen Outlook-/Graph-Connector verfügbaren Nachrichtendaten
eine RFC-5322/MIME-konforme EML-Datei.

Aufruf:
    python3 build_eml.py --input nachricht.json --output nachricht.eml [--attachments-dir DIR]

Eingabe (JSON, Felder wie vom Microsoft-365-Connector geliefert):
{
  "subject": "...",
  "sender":       {"name": "...", "address": "..."},
  "toRecipients": [{"name": "...", "address": "..."}],
  "ccRecipients": [...],
  "sentDateTime":     "2026-10-08T14:15:00.000Z",
  "receivedDateTime": "2026-10-08T14:15:31.000Z",
  "internetMessageId": "<...>",
  "body": {"contentType": "html" | "text", "content": "..."},
  "attachments": [
    {"name": "image001.png", "contentType": "image/png", "isInline": true,
     "file": "image001.png",                 # Datei im --attachments-dir ODER
     "contentBytes": "<base64>",             # Base64-Inhalt direkt ODER
     "contentId": "..."                      # optional, nur wenn vom Connector geliefert
    }
  ],
  "sourceMessageId": "<Outlook-Nachrichten-ID, optional>"
}

Grundsätze:
- Es werden nur Werte übernommen, die der Connector tatsächlich geliefert hat.
  Keine Received-, Return-Path-, DKIM- oder sonstigen Transportheader werden erfunden.
- Die Datei wird als Rekonstruktion gekennzeichnet: Header X-Reconstructed-EML: yes und
  X-BK-EML-Source: reconstructed-from-graph; dem Text- und dem HTML-Teil wird der Hinweis
  "Rekonstruierte EML; keine durch Outlook exportierte Original-MIME-Datei" vorangestellt,
  der gelieferte HTML-Inhalt folgt danach unverändert (--no-body-marker unterdrückt den
  Hinweis im Nachrichtentext, nicht die Header).
- Liegt ein Anhang aus dem JSON nicht vor (weder Datei noch contentBytes), bricht das
  Skript mit Exit-Code 2 ab, damit keine stillen Anhangauslassungen entstehen.
  Mit --allow-missing werden fehlende Anhänge stattdessen im Header
  X-BK-Missing-Attachments dokumentiert.
- Mit --omit-attachments all|name1,name2 und --omit-reason "..." werden Anhänge bewusst
  weggelassen (z. B. wenn der Übertragungsweg nur kleine Dateien zulässt); sie werden in
  X-BK-Omitted-Attachments / X-BK-Omitted-Reason dokumentiert. Eine solche EML ist
  unvollständig und muss in der DMS-Notiz so bezeichnet werden.
- Ein text/plain-Teil wird aus dem HTML abgeleitet und als solcher gekennzeichnet
  (X-BK-Derived: text/plain from text/html); der HTML-Teil bleibt unverändert.
"""
import argparse
import base64
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime, formataddr, make_msgid


MARKER = "Rekonstruierte EML; keine durch Outlook exportierte Original-MIME-Datei"
MARKER_HTML = ('<div style="border:1px solid #999;padding:6px;margin-bottom:8px;'
               'font-family:sans-serif;font-size:10pt">' + MARKER + '</div>\n')


def _addr(entry):
    if not entry:
        return None
    name = (entry.get("name") or "").strip()
    address = (entry.get("address") or "").strip()
    if not address:
        return None
    return formataddr((name, address)) if name and name != address else address


def _addr_list(entries):
    return [a for a in (_addr(e) for e in (entries or [])) if a]


def _iso_to_rfc2822(value):
    if not value:
        return None
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    v = re.sub(r"(\.\d{3})\d+", r"\1", v)
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt)


def html_to_text(src):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", src)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|tr|li|h[1-6]|table)>", "\n", s)
    s = re.sub(r"(?i)<hr[^>]*>", "\n" + "-" * 40 + "\n", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("​", "").replace("\xa0", " ")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"


def build(data, attachments_dir, allow_missing, omit=None, omit_reason=None, body_marker=True):
    msg = EmailMessage(policy=policy.SMTP)

    sender = _addr(data.get("sender")) or _addr(data.get("from"))
    if sender:
        msg["From"] = sender
    to = _addr_list(data.get("toRecipients"))
    if to:
        msg["To"] = ", ".join(to)
    cc = _addr_list(data.get("ccRecipients"))
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = data.get("subject") or ""

    date = _iso_to_rfc2822(data.get("sentDateTime")) or _iso_to_rfc2822(data.get("receivedDateTime"))
    if date:
        msg["Date"] = date

    mid = (data.get("internetMessageId") or "").strip()
    if mid:
        msg["Message-ID"] = mid
    else:
        msg["Message-ID"] = make_msgid(domain="reconstructed.invalid")
        msg["X-BK-Message-ID-Note"] = "Message-ID vom Connector nicht geliefert; lokal erzeugt"

    msg["MIME-Version"] = "1.0"
    msg["X-Reconstructed-EML"] = "yes"
    msg["X-BK-EML-Source"] = "reconstructed-from-graph"
    msg["X-BK-Reconstructed-At"] = format_datetime(datetime.now(timezone.utc))
    if data.get("receivedDateTime"):
        msg["X-BK-Received-DateTime"] = data["receivedDateTime"]
    if data.get("sourceMessageId"):
        msg["X-BK-Source-Message-Id"] = data["sourceMessageId"]
    if data.get("conversationId"):
        msg["X-BK-Source-Conversation-Id"] = data["conversationId"]

    body = data.get("body") or {}
    content = body.get("content") or ""
    ctype = (body.get("contentType") or "text").lower()
    text_prefix = (MARKER + "\n\n") if body_marker else ""
    html_prefix = MARKER_HTML if body_marker else ""
    if ctype == "html":
        msg.set_content(text_prefix + html_to_text(content), subtype="plain", charset="utf-8")
        msg.add_alternative(html_prefix + content, subtype="html", charset="utf-8")
        msg["X-BK-Derived"] = "text/plain from text/html"
    else:
        msg.set_content(text_prefix + content, subtype="plain", charset="utf-8")
    if body_marker:
        msg["X-BK-Body-Marker"] = "yes"

    missing = []
    included = []
    omitted = []
    for att in data.get("attachments") or []:
        name = att.get("name") or "anhang.bin"
        if omit == "all" or (isinstance(omit, set) and name in omit):
            omitted.append(f"{name} ({att.get('contentType') or 'unbekannt'}, "
                           f"{'inline' if att.get('isInline') else 'attachment'})")
            continue
        ct = att.get("contentType") or "application/octet-stream"
        maintype, _, subtype = ct.partition("/")
        if not subtype:
            maintype, subtype = "application", "octet-stream"
        raw = None
        if att.get("contentBytes"):
            raw = base64.b64decode(att["contentBytes"])
        elif att.get("file"):
            path = att["file"]
            if attachments_dir and not os.path.isabs(path):
                path = os.path.join(attachments_dir, path)
            if os.path.isfile(path):
                with open(path, "rb") as fh:
                    raw = fh.read()
        if raw is None:
            missing.append(name)
            continue
        disposition = "inline" if att.get("isInline") else "attachment"
        cid = att.get("contentId")
        kwargs = dict(maintype=maintype, subtype=subtype, filename=name, disposition=disposition)
        if cid:
            kwargs["cid"] = cid if cid.startswith("<") else f"<{cid}>"
        msg.add_attachment(raw, **kwargs)
        included.append(f"{name} ({len(raw)} Bytes, {disposition})")

    if missing and not allow_missing:
        sys.stderr.write("FEHLER: Anhänge ohne Inhalt: " + ", ".join(missing) + "\n")
        sys.exit(2)
    if missing:
        msg["X-BK-Missing-Attachments"] = "; ".join(missing)
    if included:
        msg["X-BK-Included-Attachments"] = "; ".join(included)
    if omitted:
        msg["X-BK-Omitted-Attachments"] = "; ".join(omitted)
        msg["X-BK-Omitted-Reason"] = omit_reason or "nicht angegeben"

    return msg, included, missing, omitted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--attachments-dir", default=None)
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--omit-attachments", default=None,
                    help="'all' oder kommagetrennte Namen: diese Anhänge bewusst weglassen; "
                         "wird im Header X-BK-Omitted-Attachments dokumentiert (Pflicht: --omit-reason)")
    ap.add_argument("--omit-reason", default=None)
    ap.add_argument("--no-body-marker", action="store_true",
                    help="Hinweis im Nachrichtentext unterdrücken (Header bleiben gesetzt)")
    args = ap.parse_args()
    if args.omit_attachments and not args.omit_reason:
        ap.error("--omit-attachments erfordert --omit-reason")

    with open(args.input, encoding="utf-8") as fh:
        data = json.load(fh)

    omit = None
    if args.omit_attachments:
        omit = "all" if args.omit_attachments.strip().lower() == "all" else \
            {n.strip() for n in args.omit_attachments.split(",") if n.strip()}
    msg, included, missing, omitted = build(data, args.attachments_dir, args.allow_missing, omit,
                                            args.omit_reason, body_marker=not args.no_body_marker)
    with open(args.output, "wb") as fh:
        fh.write(msg.as_bytes())

    print(json.dumps({
        "output": args.output,
        "bytes": os.path.getsize(args.output),
        "message_id": msg["Message-ID"],
        "attachments_included": included,
        "attachments_missing": missing,
        "attachments_omitted": omitted,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
