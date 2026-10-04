from pathlib import Path
import json, re, hashlib, csv, shutil
from decimal import Decimal
from datetime import datetime
import pdfplumber

ROOT = Path(r'C:\Projekte\Kanzlei-AI-Skills')
BASE = ROOT / 'outputs' / 'Medino_MT940_2026-10-03'
SOURCE = BASE / 'original' / 'Dokument_2026_10_03_09_59.pdf'
WORK = Path(__file__).parent
PROFILE = 'dortmunder-volksbank-onlinebanking-business-pdf-2026'
BANK_ID = 'dortmunder-volksbank-genodem1dor'
VARIANT = 'onlinebanking-business-pdf-umsatzliste-2026'

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def iso(text):
    return datetime.strptime(text, '%d.%m.%Y').date().isoformat()

def amount(text):
    return f"{Decimal(text.replace('.', '').replace(',', '.')):.2f}"

# Explicitly checked on the rendered originals. These restore failed PDF glyph
# decoding; they do not change spelling or punctuation in the source.
GLYPHS = {
    'haftungsbeschr\ufffdnkt': 'haftungsbeschränkt',
    'f\ufffdr': 'für',
    'Richardstra\ufffde': 'Richardstraße',
    'F\ufffdlligkeit': 'Fälligkeit',
    'G\ufffdltig': 'Gültig',
}

def normalize(line):
    for old, new in GLYPHS.items():
        line = line.replace(old, new)
    if '\ufffd' in line:
        raise ValueError(f'Unreviewed glyph: {line}')
    return ' '.join(line.split())

def fields(lines):
    text = ' '.join(lines)
    out = {'counterparty_or_booking_label': lines[0]}
    if len(lines) > 1 and re.fullmatch(r'DE\d{20}', lines[1]):
        out['counterparty_iban'] = lines[1]
    patterns = {
        'bic_in_description': r'BIC: ([A-Z0-9]+)',
        'end_to_end_reference': r'EREF: (\S+)',
        'mandate_reference': r'MREF: (\S+)',
        'creditor_identifier': r'CRED: (\S+)',
        'reference_in_description': r'\bREF (\S+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            out[key] = match.group(1)
    # Every other detail, including card data and invoice numbers, is preserved
    # verbatim in the full description and its original physical lines.
    return out

# Manifest acquisition: parse the original PDF. The independent review file
# below is never used to supply or repair these transaction values.
parsed = []
pages = []
start_re = re.compile(r'^(.*?)\s+([+-]\d[\d.,]*)\s+EUR$')
with pdfplumber.open(SOURCE) as pdf:
    for page_no, page in enumerate(pdf.pages, 1):
        lines = page.extract_text().splitlines()
        pages.append(lines)
        current = None
        block = 0
        for line_no, raw in enumerate(lines, 1):
            match = start_re.fullmatch(raw)
            if match:
                if current:
                    parsed.append(current)
                block += 1
                current = {
                    'source_page': page_no, 'source_block': block,
                    'source_line_start': line_no, 'source_line_end': line_no,
                    'amount': amount(match.group(2)),
                    'source_description_lines': [normalize(match.group(1))],
                    'booking_date': None, 'value_date': None,
                }
                continue
            if current is None:
                continue
            if raw.startswith('Seite ') or raw in ('(Startsaldo)', '(Endsaldo)'):
                parsed.append(current)
                current = None
                continue
            current['source_line_end'] = line_no
            if current['booking_date'] is None:
                date_match = re.search(r'(?:Valuta (\d{2}\.\d{2}\.\d{4}) - )?(\d{2}\.\d{2}\.\d{4})$', raw)
                if not date_match:
                    raise ValueError(f'Missing transaction date: {page_no}/{line_no}: {raw}')
                current['booking_date'] = iso(date_match.group(2))
                if date_match.group(1):
                    current['value_date'] = iso(date_match.group(1))
                    current['source_date_display'] = date_match.group(0)
                left = raw[:date_match.start()].strip()
                if left:
                    current['source_description_lines'].append(normalize(left))
                continue
            current['source_description_lines'].append(normalize(raw))
        if current:
            parsed.append(current)

header = '\n'.join(pages[0])
iban = re.search(r'IBAN (DE\d{20})', header).group(1)
bic = re.search(r'BIC (\S+)', header).group(1)
period = re.search(r'Filterparameter (\d{2}\.\d{2}\.\d{4}) - (\d{2}\.\d{2}\.\d{4})', header)
end_balance = amount(pages[0][pages[0].index('(Endsaldo)') + 1].replace('EUR', ''))
opening_balance = amount(pages[3][pages[3].index('(Startsaldo)') + 1].replace('EUR', ''))

manifest = {
    'bank_id': BANK_ID, 'bank_profile': PROFILE, 'profile_version': 1,
    'source_variant': VARIANT, 'source_type': 'pdf', 'target_system': 'DATEV',
    'field86_mode': 'bank_profile', 'output_scope': 'production',
    'preparation_status': 'blocked_missing_bank_reference_and_source_fields',
    'generation_allowed': False, 'delivery_approved': False,
    'iban': iban, 'bic': bic, 'currency': 'EUR',
    'account_holder': re.search(r'Kontoinhaber (.*?) Abgefragt von', header).group(1),
    'account_label': 'Business',
    'statement_start': iso(period.group(1)), 'statement_end': iso(period.group(2)),
    'period_basis': 'PDF filter interval, not numbered bank statement',
    'statement_number': None, 'sequence_number': None, 'statement_reference': None,
    'opening_balance_date': None, 'opening_balance': opening_balance,
    'closing_balance_date': None, 'closing_balance': end_balance,
    'source_order': 'booking_date_descending',
    'source_files': [{'id':'auszug', 'path':'original/'+SOURCE.name, 'sha256':digest(SOURCE)}],
    'review_report': {'value_date_exceptions': []},
    'transactions': [],
}
for index, transaction in enumerate(parsed, 1):
    t = dict(transaction)
    t.update({
        'source_file': 'auszug',
        'source_locator': f"Seite {t['source_page']}, Buchungsblock {t['source_block']}, Textextraktionszeilen {t['source_line_start']} bis {t['source_line_end']}",
        'description': ' '.join(t['source_description_lines']),
        'source_fields': fields(t['source_description_lines']),
        'code': None, 'customer_reference': None, 'bank_reference': None,
        'source_transaction_number': index,
        'value_date_source_confirmed': t['value_date'] is not None,
        'source_text_verified': False,
    })
    if t['value_date'] is not None:
        manifest['review_report']['value_date_exceptions'].append(index)
    manifest['transactions'].append(t)

# Separate evidence: manually transcribed from the actual page images before
# this parser ran. Only provenance and derivations of those independent values
# are added here; no transaction value is copied from the manifest.
review = json.loads((WORK / 'source-review-manual.json').read_text(encoding='utf-8'))
review['source_files'] = [{'id':'auszug','path':'original/'+SOURCE.name,'sha256':digest(SOURCE)}]
review['missing_fields_are_not_confirmed_values'] = True
for index, t in enumerate(review['transactions'], 1):
    t.update({
        'source_file':'auszug',
        'source_locator':f"Seite {t['source_page']}, Buchungsblock {t['source_block']} (vollständiger sichtbarer Block)",
        'source_transaction_number': index,
        'source_text_verified': True,
        'value_date_source_confirmed': t['value_date'] is not None,
        'description': ' '.join(t['source_description_lines']),
        'source_fields': fields(t['source_description_lines']),
        'code': None, 'customer_reference': None, 'bank_reference': None,
    })

comparison = []
for key in ['iban','bic','currency','account_holder','statement_start','statement_end','opening_balance','closing_balance']:
    comparison.append({'field':key, 'source_value':review[key], 'manifest_value':manifest[key], 'match':review[key]==manifest[key], 'mt940_value':None, 'mt940_result':'not_generated'})
if len(parsed) != len(review['transactions']):
    raise ValueError('Different transaction counts')
for i, (s, m) in enumerate(zip(review['transactions'], manifest['transactions']), 1):
    comparisons = {}
    for key in ['source_page','source_block','booking_date','value_date','amount','source_description_lines','description','source_fields']:
        comparisons[key] = {'source_value':s[key],'manifest_value':m[key],'match':s[key]==m[key], 'mt940_value':None,'mt940_result':'not_generated'}
    comparison.append({'transaction':i,'source_locator':s['source_locator'],'fields':comparisons,'full_text_match':s['description']==m['description'],'text_start':s['description'][:60],'text_end':s['description'][-60:]})
    if not all(v['match'] for v in comparisons.values()):
        raise ValueError(f'Original/manifest discrepancy in transaction {i}: {comparisons}')
    m['source_text_verified'] = True
if not all(c.get('match', True) for c in comparison):
    raise ValueError('Header discrepancy')

values = [Decimal(t['amount']) for t in review['transactions']]
credit = sum((v for v in values if v > 0), Decimal(0))
debit = sum((v for v in values if v < 0), Decimal(0))
delta = Decimal(review['opening_balance']) + sum(values) - Decimal(review['closing_balance'])
if delta != 0:
    raise ValueError(f'Balance discrepancy {delta}')

questions = [
    'Bankindividuelle MT940-Feldzuordnung, Referenzregeln und Textsyntax anhand einer nativen Originaldatei dieser Bank und Exportvariante oder ihrer konkreten Formatdokumentation belegen.',
    'Originale Auszugs-/Sequenznummer und Auszugsreferenz oder belegte Fehlwertbehandlung beschaffen; in der PDF nicht vorhanden.',
    'Daten zu Start- und Endsaldo beschaffen; PDF nennt nur Filterzeitraum und Saldenbeträge, keine separaten Saldendaten.',
    'Valutadaten für 29 Umsätze und bankseitige Buchungscodes/Kunden-/Bankreferenzen bzw. belegte Regeln für nicht angezeigte Werte beschaffen.',
    'Für eine neu rekonstruierte DATEV-Variante erfolgreichen Probeimport und Löschung der Testumsätze dokumentieren.',
]

template = json.loads((ROOT/'mt940-dateien-erstellen'/'profiles'/'unverified-example.json').read_text(encoding='utf-8-sig'))
template.pop('template_only', None)
template.update({
    'profile_name':PROFILE, 'bank_id':BANK_ID, 'bank_name':'Dortmunder Volksbank eG',
    'source_variant':VARIANT,'profile_version':1,'source_types':['pdf'],'status':'draft',
    'charset':None,'line_endings':None,
    'generation_allowed':False,
    'bank_identity_evidence':{
        'source_file':str(SOURCE),'sha256':digest(SOURCE),'source_page':1,
        'visible_logo':'Dortmunder Volksbank','bic':bic,'blz':iban[4:12],
    },
    'source_observations':{
        'account_label':'Business','sort_order':'Buchungsdatum, absteigend',
        'pages':4,'transactions':len(parsed),'filter_start':manifest['statement_start'],
        'filter_end':manifest['statement_end'],'visible_value_date_exceptions':[15,25,26],
        'statement_number_visible':False,'balance_dates_visible':False,
        'transaction_codes_visible':False,
    },
    'open_questions':questions,
    'research_checked':[
        {'url':'https://www.dovoba.de/service/banking/banking-fuer-firmenkunden/banking-software-geno-cash.html','result':'Bestätigt die Unterstützung von MT940 und CAMT durch GENO cash; liefert keine bankbezogene Feldzuordnung oder Zuordnung aus dieser PDF-Variante.'},
        {'url':'https://atruvia.de/profi-cash','result':'Nennt MT940/CAMT-Verarbeitung; keine geeignete bankbezogene Syntaxreferenz für diesen PDF-Export.'},
    ],
})
for key in template['field_mappings']:
    source_description = {
        'iban':'Seite 1, Kopf, IBAN', 'currency':'EUR bei jedem Umsatz und Saldo',
        'opening_balance':'Seite 4, Startsaldo', 'closing_balance':'Seite 1, Endsaldo',
        'booking_date':'Datum rechts im Buchungsblock; bei expliziter Valuta das Datum rechts nach dem Trennstrich',
        'value_date':'Explizit nur bei drei Abschlussumsätzen angezeigt; andere Valutadaten nicht separat sichtbar',
        'amount':'Vorzeichen und Betrag rechts im Buchungsblock',
        'description':'Vollständiger sichtbarer Buchungsblock: Überschrift/Gegenpartei, Gegenkonto und sämtliche Textzeilen in sichtbarer Reihenfolge',
    }.get(key,'In der PDF-Umsatzübersicht nicht separat vorhanden oder Zuordnung unbelegt')
    template['field_mappings'][key] = {'source':source_description, 'transformation':None,'target':None,'status':'unmapped'}
for key in ['counterparty_or_booking_label','counterparty_iban','bic_in_description','end_to_end_reference','mandate_reference','creditor_identifier','reference_in_description']:
    template['field_mappings'][key] = {'source':'Sichtbarer Buchungstext bzw. Überschrift im PDF; vollständiger Wert im Quellprüfnachweis', 'transformation':None,'target':None,'status':'unmapped'}

save(BASE/'manifest.json',manifest)
save(BASE/'source-review.json',review)
save(ROOT/'mt940-dateien-erstellen'/'profiles'/f'{PROFILE}.json',template)
save(BASE/'profiles'/f'{PROFILE}.json',template)

report = {
    'report_type':'source_preparation_and_reconciliation_only',
    'delivery_approved':False,'mt940_created':False,'generation_blocked':True,
    'bank_profile_status':'draft','bank_profile':PROFILE,'profile_version':1,
    'iban':iban,'currency':'EUR','period':[manifest['statement_start'],manifest['statement_end']],
    'source_sha256':digest(SOURCE),'manifest_sha256':digest(BASE/'manifest.json'),
    'source_review_sha256':digest(BASE/'source-review.json'),'mt940_sha256':None,
    'pages_reviewed':[1,2,3,4],'transactions_reviewed':len(parsed),
    'source_to_manifest_all_available_fields_passed':True,
    'transaction_count':len(values),'credit_count':sum(v>0 for v in values),'debit_count':sum(v<0 for v in values),
    'credit_sum':f'{credit:.2f}','debit_sum':f'{debit:.2f}',
    'transaction_sum':f'{sum(values):.2f}',
    'opening_balance':review['opening_balance'],'closing_balance':review['closing_balance'],
    'balance_difference':f'{delta:.2f}','balance_check_passed':delta==0,
    'value_date_exceptions':[15,25,26],
    'source_notes':[
        'Originalfolge absteigend erhalten. Drei separate girocard-Umsätze über je 12 EUR und die beiden Wohnungskaufgutschriften bleiben getrennt.',
        'PDF-Glyphersetzungen anhand der Seitenbilder korrigiert: ä, ü, ß. Schreibweisen Richardstrase/Ubergabe und Fälligkeit 15.11.2015 werden unverändert erhalten.',
        'MREF beim HORNBACH-Umsatz 21.01.2026 beginnt im Original mit G514; nicht in 6514 geändert.',
        'Keine Annahme identischer Valuta/Buchungstage für die 29 nicht separat ausgewiesenen Valutadaten.',
    ],
    'blocking_questions':questions,'datev_probe_import':'not_performed',
    'field_comparison':comparison,
}
save(BASE/'Pruefbericht.json',report)
with (BASE/'Umsaetze_quellgeprueft.csv').open('w', encoding='utf-8-sig', newline='') as f:
    columns = ['Quellnummer','Seite','Block','Buchungsdatum','Valuta_explizit','Betrag_EUR','Name_oder_Buchungsbezeichnung','Gegenkonto_IBAN','Buchungstext_vollstaendig','Textzeilen_original','Quellfundstelle']
    writer = csv.writer(f, delimiter=';')
    writer.writerow(columns)
    for t in review['transactions']:
        writer.writerow([t['source_transaction_number'],t['source_page'],t['source_block'],t['booking_date'],t['value_date'] or '',t['amount'].replace('.',','),t['source_fields']['counterparty_or_booking_label'],t['source_fields'].get('counterparty_iban',''),t['description'],'\n'.join(t['source_description_lines']),t['source_locator']])

summary = f'''Medino – Vorbereitung der MT940-Erstellung, Stand 03.10.2026

Status: MT940-Erzeugung gesperrt. Keine STA-Datei erstellt und keine DATEV-Freigabe erteilt.

Quelle: Dokument_2026_10_03_09_59.pdf, vier Seiten, unverändert gesichert.
Bank: Dortmunder Volksbank; BIC {bic}
Konto: {iban}, MeDiNo Immobilien UG, Business, EUR
Filterzeitraum: {manifest['statement_start']} bis {manifest['statement_end']}
Umsätze: {len(values)}; {sum(v>0 for v in values)} Gutschriften, {sum(v<0 for v in values)} Belastungen
Gutschriften: {credit:.2f} EUR; Belastungen: {debit:.2f} EUR
Startsaldo: {review['opening_balance']} EUR
Umsatzsumme: {sum(values):.2f} EUR
Endsaldo: {review['closing_balance']} EUR
Rechnerische Differenz: {delta:.2f} EUR

Alle vier Seitenbilder visuell geprüft. Alle 32 Buchungsblöcke einschließlich vollständiger Texte, Referenzenden, Gegenkonten und explizit angezeigter Valuta unabhängig aus dem Original erfasst und mit dem getrennt aus der PDF extrahierten Manifest verglichen. Alle verfügbaren Werte stimmen überein. Die CSV ist eine Arbeitsliste; kein DATEV-Importformat. Fehlende Quellwerte bleiben leer/null.

Explizite Valutaabweichungen (Quellnummern): 15 = Buchung 29.05.2026 / Valuta 31.05.2026; 25 = Buchung 27.02.2026 / Valuta 28.02.2026; 26 = Buchung 30.01.2026 / Valuta 31.01.2026.

Die PDF ist eine Umsatzübersicht. Separate Saldendaten, Auszugs-/Sequenznummern, MT940-Buchungscodes und technische Bank-/Kundenreferenzen sind nicht vollständig enthalten. Der Filterzeitraum darf nicht als Nachweis der Saldendaten verwendet werden. Für 29 Umsätze wird keine separate Valuta angezeigt.

Bankmodell: {PROFILE}, Version 1, Entwurf. Die PDF belegt die sichtbaren Werte, keine MT940-Unterfeldsyntax. Kein passendes bestätigtes Modell vorhanden. Öffentlich gefundene Produktinformationen der Bank und Atruvia nennen Formatunterstützung, belegen jedoch nicht die benötigte Feldzuordnung dieser Variante. Es wurden keine Formatregeln einer fremden Bank übernommen.

Benötigt: nativer MT940/STA- oder CAMT-Bankexport für dieses Konto/Zeitraum, oder konkrete bankbezogene Formatdokumentation plus fehlende Originalfelder. Für eine neue rekonstruierte DATEV-Variante außerdem dokumentierter Probeimport samt Löschung der Testumsätze. Vor einem erneuten Import für bereits importierte Zeiträume müssen frühere Test-/Importumsätze bereinigt sein.

Quell-SHA256: {digest(SOURCE)}
MT940-SHA256: entfällt, keine Datei erzeugt.
DATEV-Probeimport: nicht durchgeführt.

Dateien:
original/ = unveränderter E-Mail-Anhang
manifest.json = getrennt aus der PDF extrahierte, noch unvollständige Generator-Eingabe; gesperrt
source-review.json = unabhängige visuelle Quellabschrift mit Fundstellen
Pruefbericht.json = vollständiger Quelle/Manifest-Feldvergleich und Saldenrechnung
Umsaetze_quellgeprueft.csv = Quellumsätze in unveränderter Reihenfolge, mit vollständigem Text
profiles/ = bankindividueller Entwurf ohne erfundene Zielzuordnungen

Skill-Vorgabe: „Fehlt diese Evidenz, den Entwurf trotzdem sichern, die benötigte Bankreferenz benennen und die Erzeugung sperren.“
'''
(BASE/'Pruefbericht.txt').write_text(summary, encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('field_comparison','blocking_questions')},ensure_ascii=False,indent=2))
