"""Tests für scripts/build_eml.py (Aufruf: python3 -I tests/test_build_eml.py)."""
import base64
import json
import os
import subprocess
import sys
import tempfile
from email import policy
from email.parser import BytesParser

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "build_eml.py")

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def base_msg():
    return {
        "subject": "AW: Kündigung Test",
        "sender": {"name": "Invoices", "address": "invoices@example.com"},
        "toRecipients": [{"name": "Burchardt, Oliver", "address": "o.b@example.de"}],
        "ccRecipients": [{"name": "", "address": "cc@example.de"}],
        "sentDateTime": "2026-10-08T14:15:00.000Z",
        "receivedDateTime": "2026-10-08T14:15:31.000Z",
        "internetMessageId": "<abc@example.com>",
        "body": {"contentType": "html", "content": "<div>Guten Tag,<br/>Vertragsende <b>31.12.2026</b>.</div>"},
        "attachments": [
            {"name": "logo.png", "contentType": "image/png", "isInline": True, "file": "logo.png"},
            {"name": "rechnung.pdf", "contentType": "application/pdf", "isInline": False, "file": "rechnung.pdf"},
        ],
    }


def run(msg, extra, tmp, with_files=True):
    if with_files:
        open(os.path.join(tmp, "logo.png"), "wb").write(PNG)
        open(os.path.join(tmp, "rechnung.pdf"), "wb").write(b"%PDF-1.4 test")
    inp = os.path.join(tmp, "m.json")
    json.dump(msg, open(inp, "w", encoding="utf-8"), ensure_ascii=False)
    out = os.path.join(tmp, "m.eml")
    r = subprocess.run([sys.executable, "-I", SCRIPT, "--input", inp, "--output", out,
                        "--attachments-dir", tmp] + extra, capture_output=True, text=True)
    return r, out


def parse(path):
    return BytesParser(policy=policy.strict).parse(open(path, "rb"))


def test_full():
    with tempfile.TemporaryDirectory() as tmp:
        r, out = run(base_msg(), [], tmp)
        assert r.returncode == 0, r.stderr
        m = parse(out)
        assert m["From"] == "Invoices <invoices@example.com>"
        assert "o.b@example.de" in m["To"] and "cc@example.de" in m["Cc"]
        assert m["Message-ID"] == "<abc@example.com>"
        assert m["Date"].startswith("Thu, 08 Oct 2026 14:15:00")
        assert m["X-BK-EML-Source"] == "reconstructed-from-graph"
        assert "Received" not in m and "Return-Path" not in m and "DKIM-Signature" not in m
        atts = list(m.iter_attachments())
        assert [a.get_filename() for a in atts] == ["logo.png", "rechnung.pdf"]
        assert atts[0].get_content_disposition() == "inline"
        assert atts[1].get_content_disposition() == "attachment"
        assert atts[0].get_payload(decode=True) == PNG
        assert m.get_body(preferencelist=("html",)).get_content().strip() == base_msg()["body"]["content"]
        assert "31.12.2026" in m.get_body(preferencelist=("plain",)).get_content()
        assert not m.defects and not any(p.defects for p in m.walk())


def test_missing_attachment_aborts():
    with tempfile.TemporaryDirectory() as tmp:
        msg = base_msg()
        msg["attachments"][1]["file"] = "gibt-es-nicht.pdf"
        r, out = run(msg, [], tmp)
        assert r.returncode == 2 and "rechnung.pdf" in r.stderr, r.stderr
        assert not os.path.exists(out)


def test_missing_attachment_documented():
    with tempfile.TemporaryDirectory() as tmp:
        msg = base_msg()
        msg["attachments"][1]["file"] = "gibt-es-nicht.pdf"
        r, out = run(msg, ["--allow-missing"], tmp)
        assert r.returncode == 0, r.stderr
        m = parse(out)
        assert "rechnung.pdf" in m["X-BK-Missing-Attachments"]
        assert [a.get_filename() for a in m.iter_attachments()] == ["logo.png"]


def test_omit_requires_reason():
    with tempfile.TemporaryDirectory() as tmp:
        r, out = run(base_msg(), ["--omit-attachments", "all"], tmp)
        assert r.returncode != 0 and "omit-reason" in r.stderr


def test_omit_selected_documented():
    with tempfile.TemporaryDirectory() as tmp:
        r, out = run(base_msg(), ["--omit-attachments", "logo.png", "--omit-reason", "Signaturgrafik"], tmp)
        assert r.returncode == 0, r.stderr
        m = parse(out)
        assert "logo.png" in m["X-BK-Omitted-Attachments"]
        assert m["X-BK-Omitted-Reason"] == "Signaturgrafik"
        assert [a.get_filename() for a in m.iter_attachments()] == ["rechnung.pdf"]
        rep = json.loads(r.stdout)
        assert rep["attachments_omitted"] and rep["attachments_included"]


def test_text_body_without_message_id():
    with tempfile.TemporaryDirectory() as tmp:
        msg = base_msg()
        msg["body"] = {"contentType": "text", "content": "Nur Text"}
        msg["attachments"] = []
        msg["internetMessageId"] = ""
        r, out = run(msg, [], tmp, with_files=False)
        assert r.returncode == 0, r.stderr
        m = parse(out)
        assert m.get_content_type() == "text/plain"
        assert m["Message-ID"].endswith("@reconstructed.invalid>")
        assert m["X-BK-Message-ID-Note"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} Tests bestanden")
