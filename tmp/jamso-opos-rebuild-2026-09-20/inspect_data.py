from pathlib import Path
from collections import Counter
from datetime import datetime
from decimal import Decimal
import json
import openpyxl

ROOT=Path(__file__).parent
w=openpyxl.load_workbook(ROOT/'debit.xlsx',data_only=False)
s=w.active
for row in s.iter_rows(min_row=1,max_row=224):
    r=row[0].row
    a,b,c,d,e,f,g=[x.value for x in row[:7]]
    if r<=6 or r>=190 or (e is not None and not isinstance(f,datetime)) or r in (50,51,52,53,54,55,57,170):
        print('SRC',r,repr(a),repr(b),repr(c),repr(d),repr(e),repr(f),repr(g))
datev=json.loads((ROOT/'datev_2024.json').read_text(encoding='utf-8'))
for a in (10001,10068,10069,10072,10096,10103,10105,10143,10154,10161,10171,10173,10174,10177,10213):
    print('\nDATEV ACCOUNT',a)
    for x in datev:
        if int(x['account_number'])//10000==a:
            print(x.get('date'),x.get('document_field1'),x.get('open_item_number'),x.get('amount_debit'),x.get('amount_credit'),'clear' if x.get('is_cleared') else 'OPEN',x.get('posting_description'))
