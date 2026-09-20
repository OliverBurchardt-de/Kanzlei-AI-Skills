"""Encoder restricted to Dortmunder Volksbank Kontokorrent PDF 2025."""
import hashlib
import importlib.util
import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROFILE=json.loads((ROOT/"profile.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("dvb_independent_decoder",ROOT/"decode.py")
DECODER=importlib.util.module_from_spec(spec)
spec.loader.exec_module(DECODER)

def require(condition,message):
    if not condition:
        raise ValueError(message)

def amount(value):
    require(isinstance(value,str) and re.fullmatch(r"-?\d+\.\d{2}",value),"Exact decimal string required")
    return Decimal(value)

def signed(value):
    x=amount(value)
    return ("C" if x>=0 else "D")+format(abs(x),".2f").replace(".",",")

def day(value):
    require(isinstance(value,str) and re.fullmatch(r"20\d{2}-\d{2}-\d{2}",value),"ISO date required")
    return date.fromisoformat(value)

def valid_iban(iban):
    if not re.fullmatch(r"DE\d{20}",iban):
        return False
    numeric="".join(str(ord(c)-55) if c.isalpha() else c for c in iban[4:]+iban[:4])
    return int(numeric)%97==1

def clean(value):
    require(isinstance(value,str),"Text required")
    require(not any(ord(c)<32 for c in value) and "?" not in value,"Control/delimiter in source text")
    require(value==value.strip(),"Unreviewed leading/trailing source whitespace")
    value.encode("cp850",errors="strict")
    return value

def parts(value,codes):
    clean(value)
    require(len(value)<=27*len(codes),"Bank model field capacity exceeded; do not truncate")
    return ["?"+str(codes[i//27]).zfill(2)+value[i:i+27] for i in range(0,len(value),27)]

def encode86(tx):
    require(tx["gvc"] in PROFILE["allowed_gvc"],"Unknown GVC")
    mapping={"Überweisungsgutschr.":("051",1),"Überweisungsauftrag":("020",-1),
             "Echtzeitüberweisung":("118",-1),"Abschluss lt. Anlage 1":("805",-1),
             "Entgelt/Auslagen":("835",-1),"Geschäftsanteilbel.":("835",-1),
             "Kartenzahlung girocard":("835",-1)}
    require(tx["type"] in mapping,"Unknown bank transaction type; extend this bank model first")
    gvc,sign=mapping[tx["type"]]
    require(tx["gvc"]==gvc and amount(tx["amount"])*sign>0,"GVC/type/sign mismatch")
    if gvc in ("020","051","118"):
        require(bool(tx["counterparty"]),"Transfer counterparty missing")
    require(isinstance(tx.get("classification_basis"),str) and tx["classification_basis"].strip(),"GVC source/classification basis missing")
    kind=clean(tx["type"])
    require(0<len(kind)<=27,"Booking type must fit ?00")
    tokens=["?00"+kind]+parts(tx["purpose"],list(range(20,30)))+parts(tx["counterparty"],[32,33])
    lines=[":86:"+tx["gvc"]]
    for token in tokens:
        if len(lines[-1])+len(token)>65:
            lines.append(token)
        else:
            lines[-1]+=token
    require(len(lines)<=6,"Bank model :86: capacity exceeded")
    return lines

def check_source(tx,source_kind):
    for key in ("type","counterparty","purpose"):
        clean(tx[key])
    if source_kind=="pdf":
        require(tx.get("source_reviewed") is True,"PDF needs actual visual review")
        require(type(tx.get("source_page")) is int and tx["source_page"]>0,"Source page missing")
        lines=tx.get("source_lines")
        joiners=tx.get("source_joiners")
        require(isinstance(lines,list) and isinstance(joiners,list),"Source lines/joiners missing")
        require(len(joiners)==max(0,len(lines)-1) and all(x in (""," ") for x in joiners),"Explicit source joins required")
        for line in lines:
            clean(line)
        combined=lines[0] if lines else ""
        for joiner,line in zip(joiners,lines[1:]):
            combined+=joiner+line
        expected=" ".join(v for v in (tx["counterparty"],tx["purpose"]) if v)
        require(combined==expected,"PDF-to-manifest text mismatch")
    if "source_value_date" in tx and tx["source_value_date"]!=tx["value_date"]:
        correction=tx.get("value_date_correction",{})
        require(correction.get("confirmed") is True and bool(correction.get("authority")) and bool(correction.get("reason")),"Unconfirmed source date change")

def normalize(data):
    require(data.get("profile_id")==PROFILE["profile_id"],"Exact bank profile required; no fallback")
    require(data.get("bank")=={"name":PROFILE["bank_name"],"blz":PROFILE["blz"],"bic":PROFILE["bic"],"variant":PROFILE["source_variant"]},"Bank/variant mismatch")
    require(data.get("currency")=="EUR","Currency mismatch")
    iban=data.get("iban","")
    require(valid_iban(iban) and iban[4:12]==PROFILE["blz"],"IBAN invalid or wrong bank")
    source_kind=data.get("source_kind")
    require(source_kind in ("pdf","synthetic_reference"),"Unsupported source variant")
    source_inventory=data.get("source_inventory")
    require(isinstance(source_inventory,list) and source_inventory,"Independent source inventory required")
    counts=data.get("source_month_counts")
    require(isinstance(counts,dict) and all(re.fullmatch(r"20\d{2}-\d{2}",k) and type(v) is int and v>=0 for k,v in counts.items()),"Independent month counts invalid")
    statements=data.get("statements")
    require(isinstance(statements,list) and len(statements)==len(source_inventory),"Missing/extra statement")
    month_count=Counter()
    expected=[]
    seen=set()
    for s,control in zip(statements,source_inventory):
        number=s["number"]
        require(type(number) is int and 1<=number<=99999,"Invalid original statement number")
        require(control.get("number")==number,"Statement inventory mismatch")
        require(type(control.get("count")) is int and control["count"]>=0,"Source count must be an integer")
        year=day(s["closing"]["date"]).year
        require((year,number) not in seen,"Duplicate statement")
        seen.add((year,number))
        for balance in ("opening","closing"):
            day(s[balance]["date"]);amount(s[balance]["amount"])
        require(day(s["opening"]["date"])<=day(s["closing"]["date"]),"Reversed statement dates")
        require(s["opening"]==control.get("opening") and s["closing"]==control.get("closing"),"Source balances differ")
        txs=s["transactions"]
        require(len(txs)==control.get("count"),"Missing/extra transactions")
        if source_kind=="pdf":
            require(isinstance(control.get("source_file"),str) and bool(control["source_file"]),"Source file identity missing")
            require(re.fullmatch(r"[0-9a-f]{64}",control.get("source_file_sha256","")) is not None,"Source hash missing")
            pages=control.get("page_count")
            require(type(pages) is int and pages>0,"Source page count missing")
            require(control.get("reviewed_pages")==list(range(1,pages+1)),"Not all source pages reviewed")
            require(all(type(t.get("source_page")) is int and 1<=t["source_page"]<=pages for t in txs),"Transaction page outside source")
        if expected:
            require(expected[-1]["closing"]==s["opening"],"Broken source balance chain")
        debit=credit=Decimal(0)
        last=None
        normalized_txs=[]
        for tx in txs:
            bd=day(tx["booking_date"]);day(tx["value_date"])
            require(day(s["opening"]["date"])<=bd<=day(s["closing"]["date"]),"Booking outside statement")
            require(last is None or last<=bd,"Source order changed")
            last=bd
            val=amount(tx["amount"])
            require(val!=0,"Zero transaction")
            if val<0:debit-=val
            else:credit+=val
            month_count[tx["booking_date"][:7]]+=1
            check_source(tx,source_kind)
            encode86(tx)
            require(tx["code"] in ("NMSC","NTRF","NCHG"),"Unreviewed SWIFT code")
            ref=tx.get("customer_reference","NONREF")
            require(re.fullmatch(r"[A-Za-z0-9 .-]{1,16}",ref) is not None,"Invalid reference; do not truncate")
            normalized_txs.append({k:tx[k] for k in ("booking_date","value_date","amount","code","gvc","type","counterparty","purpose")}|{"customer_reference":ref})
        require(debit==amount(control["debits"]) and credit==amount(control["credits"]),"Source debit/credit totals differ")
        require(amount(s["opening"]["amount"])+credit-debit==amount(s["closing"]["amount"]),"Source balance mismatch")
        expected.append({"reference":f"DV{year}{number:05d}","iban":iban,"number":number,
                         "opening":s["opening"],"closing":s["closing"],"transactions":normalized_txs})
    require(dict(month_count)==data.get("source_month_counts"),"Source month count mismatch")
    return expected

def validate(data,payload):
    expected=normalize(data)
    actual=DECODER.parse(payload)
    require(actual==expected,"Decoded file differs from source fields")
    return {"profile_id":PROFILE["profile_id"],"file_sha256":hashlib.sha256(payload).hexdigest(),
            "source_manifest_sha256":hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest(),
            "technical_validation":"passed","source_kind":data["source_kind"],
            "datev_import_status":"not_verified",
            "bank_model_import_status":PROFILE["datev_import"]["status"],
            "encoding":PROFILE["encoding"],
            "acceptance_evidence":None,
            "statement_count":len(actual),"transaction_count":sum(len(s["transactions"]) for s in actual),
            "month_counts":data["source_month_counts"],"closing":actual[-1]["closing"],
            "source_inventory":data["source_inventory"],
            "transaction_audit":[{"statement":s["number"],"source_page":t.get("source_page"),
                                 "booking_date":t["booking_date"],"value_date":t["value_date"],
                                 "source_value_date":t.get("source_value_date",t["value_date"]),
                                 "value_date_correction":t.get("value_date_correction"),
                                 "amount":t["amount"],"gvc":t["gvc"],
                                 "classification_basis":t["classification_basis"],
                                 "type":t["type"],"counterparty":t["counterparty"],"purpose":t["purpose"],
                                 "source_reviewed":t.get("source_reviewed",False)}
                                for s in data["statements"] for t in s["transactions"]],
            "warning":"File creation is not a DATEV import; replacement must not be added to previously imported transactions."}

def build(data):
    reference=(ROOT/"reference.sta").read_bytes()
    require(hashlib.sha256(reference).hexdigest()==PROFILE["reference_sha256"],"Stored bank reference changed")
    reference_expected=json.loads((ROOT/"reference-expected.json").read_text(encoding="utf-8"))
    require(DECODER.parse(reference)==reference_expected,"Stored bank reference semantic mismatch")
    reference_input=json.loads((ROOT/"reference-input.json").read_text(encoding="utf-8"))
    require(normalize(reference_input)==reference_expected,"Reference source mismatch")
    expected=normalize(data)
    lines=[]
    for s,raw in zip(expected,data["statements"]):
        lines += [":20:"+s["reference"],":25:"+s["iban"],f":28C:{s['number']:05d}/001"]
        opening=s["opening"]
        lines += [":60F:"+signed(opening["amount"])[0]+day(opening["date"]).strftime("%y%m%d")+"EUR"+signed(opening["amount"])[1:]]
        for tx,source_tx in zip(s["transactions"],raw["transactions"]):
            lines += [":61:"+day(tx["value_date"]).strftime("%y%m%d")+day(tx["booking_date"]).strftime("%m%d")+signed(tx["amount"])+tx["code"]+tx["customer_reference"]]
            lines += encode86(source_tx)
        closing=s["closing"]
        lines += [":62F:"+signed(closing["amount"])[0]+day(closing["date"]).strftime("%y%m%d")+"EUR"+signed(closing["amount"])[1:],"-"]
    require(all(len(x)<=65 for x in lines),"Physical line capacity exceeded")
    payload=("\r\n".join(lines)+"\r\n").encode("cp850",errors="strict")
    return payload,validate(data,payload)
