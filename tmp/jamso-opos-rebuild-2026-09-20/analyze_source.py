from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import openpyxl

ROOT = Path(__file__).parent
sheet = openpyxl.load_workbook(ROOT / "debit.xlsx", data_only=False).active
datev = json.loads((ROOT / "datev_2024.json").read_text(encoding="utf-8"))


def dec(value):
    return Decimal(str(value)) if isinstance(value, (float, int)) else Decimal(0)


by_account = defaultdict(lambda: {"name": "", "excel_now": Decimal(0), "excel_2024": Decimal(0), "rows": [], "invoices": []})
account = None
for r in range(2, 200):
    a = sheet.cell(r, 1).value
    if isinstance(a, int):
        account = a
        by_account[a]["name"] = str(sheet.cell(r, 2).value or "")
    if account is None:
        continue
    row = by_account[account]
    row["rows"].append(r)
    ref = sheet.cell(r, 3).value
    d = dec(sheet.cell(r, 4).value)
    e = dec(sheet.cell(r, 5).value)
    dt = sheet.cell(r, 6).value
    row["excel_now"] += d - e
    if not (r == 170 and account == 10171):
        row["excel_2024"] += d
    if isinstance(dt, datetime) and dt.year <= 2024:
        row["excel_2024"] -= e
    if d and isinstance(ref, str) and ref.startswith("2024-"):
        row["invoices"].append((ref, d, r))

datev_by_account = defaultdict(lambda: {"all": Decimal(0), "open": Decimal(0), "open_count": 0, "rows": []})
for obj in datev:
    a = int(obj["account_number"]) // 10000
    delta = dec(obj.get("amount_debit")) - dec(obj.get("amount_credit"))
    datev_by_account[a]["all"] += delta
    datev_by_account[a]["rows"].append(obj)
    if not obj.get("is_cleared"):
        datev_by_account[a]["open"] += delta
        datev_by_account[a]["open_count"] += 1

print("account|name|excel_all_D-E|excel_2024_cutoff|datev_open_net|datev_all_net|datev_open_rows|invoice_refs")
for a, source in sorted(by_account.items()):
    dv = datev_by_account[a]
    if a != 10069 and not source["excel_now"] and not source["excel_2024"] and not dv["open"]:
        continue
    print(f"{a}|{source['name']}|{source['excel_now']}|{source['excel_2024']}|{dv['open']}|{dv['all']}|{dv['open_count']}|{','.join(x[0] for x in source['invoices'])}")

print("TOTAL EXCEL NOW", sum(x["excel_now"] for x in by_account.values()))
print("TOTAL EXCEL 2024", sum(x["excel_2024"] for x in by_account.values()))
print("DATEV open net all", sum(x["open"] for x in datev_by_account.values()))
print("DATEV open net source accounts", sum(datev_by_account[a]["open"] for a in by_account))
vals=[v['excel_now'] for k,v in by_account.items() if k!=10069]
print('2024 invoice gross positive',sum((x for x in vals if x>0),Decimal(0)))
print('2024 invoice credits negative',sum((x for x in vals if x<0),Decimal(0)))
