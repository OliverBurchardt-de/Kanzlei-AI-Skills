import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = path.dirname(new URL(import.meta.url).pathname.replace(/^\/(?:[A-Za-z]:)/, m => m.slice(1)));
const data = JSON.parse(await fs.readFile(path.join(root, 'workpaper_data.json'), 'utf8'));
const outDir = 'C:/Projekte/Kanzlei-AI-Skills/outputs/01a0bea8-f4c0-74a2-b3e0-eafdb8a43b7c';
const outFile = path.join(outDir, 'jamso-opos-neuberechnung-2026-09-20.xlsx');
const wb = Workbook.create();
const work = wb.worksheets.add('Arbeitspapier');
const compare = wb.worksheets.add('Kontenabgleich');
const later = wb.worksheets.add('Nachtrag');
const split = wb.worksheets.add('Aufteilung 2024-25');
const src = wb.worksheets.add('Mandantenzeilen');
const dv = wb.worksheets.add('DATEV 31.12.24');
const tracker = wb.worksheets.add('Zahlungstracker');
const storno = wb.worksheets.add('Stornoliste');
const sheets = [work, compare, later, split, src, dv, tracker, storno];
const dark = '#18334B', blue = '#285875', teal = '#1F6D68', pale = '#E8F2F1', amber = '#FFF2D4', red = '#FDE7E7';
const fmtMoney = '#,##0.00;[Red](#,##0.00);–';

for (const s of sheets) {
  s.showGridLines = false;
  s.getRange('A1:N20').format.font = { name: 'Arial', size: 10, color: '#24313A' };
  s.getRange('A1:N20').format.verticalAlignment = 'center';
}
work.tabColor = dark;

function header(s, address) {
  const r = s.getRange(address);
  r.format = { fill: dark, font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' }, verticalAlignment: 'center', rowHeight: 30 };
}
function dates(s, address) { s.getRange(address).setNumberFormat('dd.mm.yyyy'); }
function money(s, address) { s.getRange(address).setNumberFormat(fmtMoney); }
function writeRows(s, start, rows) {
  if (rows.length) s.getRangeByIndexes(start - 1, 0, rows.length, rows[0].length).values = rows;
}

// Detailed source values. The source's result/formula column G is never read or copied.
src.getRange('A1').values = [['Quelle: Jamso Trainee, Debitorenaufstellung 18.0.9.2024.xlsx; E-Mail vom 18.09.2026, „3/3“']];
src.getRange('A2').values = [['Originale Ergebnisspalte G ausgeschlossen. Zeile 200 ist eine Quell-Summenzeile und wird nicht gerechnet.']];
src.getRange('A4:N4').values = [[
  'Quellzeile','Abschnitt','Konto original','Konto zugeordnet','Name / Text','RE-Nr.',
  'Rechnungsbetrag D','Zahlung E','Datum original','Datum geprüft','Jahr Zahlung',
  'Saldo neu D − E','Saldo 31.12.24','Quellenhinweis'
]];
header(src, 'A4:N4');
const srcStart=5, srcEnd=srcStart+data.source_rows.length-1;
writeRows(src,srcStart,data.source_rows.map(x=>[
  x.source_row,x.section,x.raw_account,x.account,x.name,x.reference,x.debit,x.paid,x.raw_date,
  x.parsed_date ? new Date(`${x.parsed_date}T12:00:00Z`) : null,x.payment_year,null,null,x.note
]));
src.getRange(`L${srcStart}:L${srcEnd}`).formulas = data.source_rows.map((_,i)=>[`=G${i+srcStart}-H${i+srcStart}`]);
src.getRange(`M${srcStart}:M${srcEnd}`).formulas = data.source_rows.map((_,i)=>{
  const r=i+srcStart;
  return [`=IF(B${r}="Hauptliste",G${r}-IF(AND(ISNUMBER(K${r}),K${r}<=2024),H${r},0),0)`];
});
src.getRange('A:A').format.columnWidth=10;
src.getRange('B:B').format.columnWidth=15;
src.getRange('C:D').format.columnWidth=15;
src.getRange('E:E').format.columnWidth=27;
src.getRange('F:F').format.columnWidth=17;
src.getRange('G:H').format.columnWidth=17;
src.getRange('I:J').format.columnWidth=18;
src.getRange('K:K').format.columnWidth=12;
src.getRange('L:M').format.columnWidth=18;
src.getRange('N:N').format.columnWidth=62;
money(src,`G${srcStart}:H${srcEnd}`); money(src,`L${srcStart}:M${srcEnd}`); dates(src,`J${srcStart}:J${srcEnd}`);
src.freezePanes.freezeRows(4);

// DATEV fiscal-year-2024 extract: only uncleared component postings, each with its own signed amount.
dv.getRange('A1').values = [['Quelle: Klardaten DATEV, Mandant 12521, datev://accounting/condensed_accounts_receivable, Geschäftsjahr 2024']];
dv.getRange('A2').values = [['Nur is_cleared=false; Saldo je Buchungszeile = Soll − Haben. Wiederholtes open_balance_of_item nicht summiert.']];
dv.getRange('A4:J4').values = [['Quellindex','Debitor','Buchungsdatum','Belegfeld 1','OP-Nummer','Buchungstext','Soll','Haben','Offen netto','DATEV-ID']];
header(dv,'A4:J4');
const dvStart=5,dvEnd=dvStart+data.datev_open_rows.length-1;
writeRows(dv,dvStart,data.datev_open_rows.map(x=>[
  x.source_index,x.account,new Date(`${x.date}T12:00:00Z`),x.document,x.open_item,x.description,x.debit,x.credit,null,x.id
]));
dv.getRange(`I${dvStart}:I${dvEnd}`).formulas=data.datev_open_rows.map((_,i)=>{const r=i+dvStart;return [`=G${r}-H${r}`]});
dv.getRange('A:B').format.columnWidth=12;
dv.getRange('C:C').format.columnWidth=18;
dv.getRange('D:E').format.columnWidth=19;
dv.getRange('F:F').format.columnWidth=51;
dv.getRange('G:I').format.columnWidth=17;
dv.getRange('J:J').format.columnWidth=44;
dates(dv,`C${dvStart}:C${dvEnd}`); money(dv,`G${dvStart}:I${dvEnd}`);
dv.freezePanes.freezeRows(4);

// Payments below the source total. An invoice reference can suggest a debtor but is not proof of payment allocation.
later.getRange('A1').values = [['Quelle: dieselbe Jamso-Debitorenaufstellung, Zeilen 201–224 unterhalb der alten Summenzeile']];
later.getRange('A2').values = [['Rechnungstreffer sind Vorschläge; Bankbeleg und Zahler müssen für die Auszifferung geprüft werden.']];
later.getRange('A4:J4').values = [['Quellzeile','Name / Zahler','RE-Nr. zugeordnet','Zahlung','Datum','DATEV-Konto Vorschlag','Trefferqualität','Hinweis','2025-Folgerechnung','2025-Betrag laut Liste']];
header(later,'A4:J4');
const laterStart=5,laterEnd=laterStart+data.later_rows.length-1;
writeRows(later,laterStart,data.later_rows.map(x=>[
  x.source_row,x.name,x.reference,x.paid,x.date?new Date(`${x.date}T12:00:00Z`):null,
  x.account,x.status,x.note,x.ref_2025,x.part_2025
]));
later.getRange('A:A').format.columnWidth=12;
later.getRange('B:B').format.columnWidth=29;
later.getRange('C:C').format.columnWidth=21;
later.getRange('D:D').format.columnWidth=17;
later.getRange('E:E').format.columnWidth=17;
later.getRange('F:F').format.columnWidth=21;
later.getRange('G:G').format.columnWidth=46;
later.getRange('H:H').format.columnWidth=57;
later.getRange('I:I').format.columnWidth=22;
later.getRange('J:J').format.columnWidth=18;
money(later,`D${laterStart}:D${laterEnd}`); dates(later,`E${laterStart}:E${laterEnd}`);
money(later,`J${laterStart}:J${laterEnd}`);
later.freezePanes.freezeRows(4);

// 2024/25 invoice split. The source's D subtotal formula is ignored and recomputed here.
split.getRange('A1').values=[['Quelle: Jamso Trainee, Aufgeteilte Rechnung 2024-2025.xlsx, Blatt „2024_2025“']];
split.getRange('A2').values=[['E+G ist nur eine Rechensumme: 2025-Rechnung kann 2024-Anteil erneut enthalten. Originale D-Ergebnisspalte ignoriert.']];
split.getRange('A4:K4').values=[['Quellzeile','Debitor','Name','Rechnung 2024','2024-Betrag E/F','Rechnung 2025','2025-Betrag H','E+G rechnerisch','Quellenvermerk','Tracker-Rechnung 2024','Differenz H−J']];
header(split,'A4:K4');
const splitStart=5,splitEnd=splitStart+data.split_rows.length-1;
writeRows(split,splitStart,data.split_rows.map(x=>[x.source_row,x.account,x.name,x.ref_2024,x.part_2024,x.ref_2025,x.part_2025,null,x.note,x.tracker_invoice,null]));
split.getRange(`H${splitStart}:H${splitEnd}`).formulas=data.split_rows.map((_,i)=>{const r=i+splitStart;return [`=E${r}+G${r}`]});
split.getRange(`K${splitStart}:K${splitEnd}`).formulas=data.split_rows.map((_,i)=>{const r=i+splitStart;return [`=IF(ISNUMBER(J${r}),H${r}-J${r},"")`]});
split.getRange('A:B').format.columnWidth=12;
split.getRange('C:C').format.columnWidth=32;
split.getRange('D:D').format.columnWidth=20;
split.getRange('E:E').format.columnWidth=17;
split.getRange('F:F').format.columnWidth=20;
split.getRange('G:H').format.columnWidth=17;
split.getRange('I:I').format.columnWidth=72;
split.getRange('J:K').format.columnWidth=20;
money(split,`E${splitStart}:E${splitEnd}`);money(split,`G${splitStart}:H${splitEnd}`);money(split,`J${splitStart}:K${splitEnd}`);
split.freezePanes.freezeRows(4);

// Booking tracker and cancellation list are separate source clues, not confirmed bank statements.
tracker.getRange('A1').values=[['Quelle: Jamso Trainee, Excel Zahlungsverlauf.xlsx, Blatt „2024“']];
tracker.getRange('A2').values=[['Auszug zu in Hauptliste/Aufteilung genannten Rechnungen; Vermerke J/L/N/P/Q/S/U/V in Originalspalten.']];
tracker.getRange('A4:E4').values=[['Quellzeile','Name','Rechnung','Rechnungsbetrag I','Zahlungs-/Terminvermerke original']];
header(tracker,'A4:E4');
const trStart=5,trEnd=trStart+data.tracker_rows.length-1;
writeRows(tracker,trStart,data.tracker_rows.map(x=>[x.source_row,x.name,x.reference,x.invoice_amount,x.evidence]));
tracker.getRange('A:A').format.columnWidth=12;tracker.getRange('B:B').format.columnWidth=32;
tracker.getRange('C:C').format.columnWidth=19;tracker.getRange('D:D').format.columnWidth=20;
tracker.getRange('E:E').format.columnWidth=115;money(tracker,`D${trStart}:D${trEnd}`);
tracker.freezePanes.freezeRows(4);

storno.getRange('A1').values=[['Quelle: Jamso Trainee, Excel Zahlungsverlauf.xlsx, Blatt „Stornorechnungen“']];
storno.getRange('A2').values=[['Mandantenvermerke; Wirksamkeit und DATEV-Buchung der Stornos einzeln prüfen.']];
storno.getRange('A4:H4').values=[['Quellzeile','Name','Bezeichnung','Bezug / Grund','Stornonummer','Datum original','Betrag','Vermerk']];
header(storno,'A4:H4');
const stStart=5,stEnd=stStart+data.storno_rows.length-1;
writeRows(storno,stStart,data.storno_rows.map(x=>[x.source_row,x.name,x.description,x.reason,x.number,x.date,x.amount,x.note]));
storno.getRange('A:A').format.columnWidth=12;storno.getRange('B:B').format.columnWidth=30;
storno.getRange('C:D').format.columnWidth=68;storno.getRange('E:E').format.columnWidth=17;
storno.getRange('F:F').format.columnWidth=18;storno.getRange('G:G').format.columnWidth=18;
storno.getRange('H:H').format.columnWidth=50;money(storno,`G${stStart}:G${stEnd}`);
storno.freezePanes.freezeRows(4);

// Account-level bridge. Different-period values are displayed side by side, never silently netted.
compare.getRange('A1').values = [['Jamso Trainee | Kontenabgleich Excel zu DATEV 31.12.2024']];
compare.getRange('A2').values = [['„Excel aktuell“ folgt der Mandantenvorgabe. „Nachtrag“ ist getrennt; keine doppelte Verrechnung.']];
compare.getRange('A4:H4').values = [[
  'Debitor','Name / Buchungstext','Excel aktuell','Excel 31.12.24',
  'DATEV 31.12.24','Differenz 31.12','Nachtrag Hinweis','Befund'
]];
header(compare,'A4:H4');
const cmpStart=5,cmpEnd=cmpStart+data.accounts.length-1;
writeRows(compare,cmpStart,data.accounts.map(x=>[x.account,x.name,null,null,null,null,null,null]));
const compForm=[];
for(let i=0;i<data.accounts.length;i++){
  const r=cmpStart+i;
  compForm.push([
    `=SUMIFS('Mandantenzeilen'!$L$${srcStart}:$L$${srcEnd},'Mandantenzeilen'!$D$${srcStart}:$D$${srcEnd},A${r},'Mandantenzeilen'!$B$${srcStart}:$B$${srcEnd},"Hauptliste")`,
    `=SUMIFS('Mandantenzeilen'!$M$${srcStart}:$M$${srcEnd},'Mandantenzeilen'!$D$${srcStart}:$D$${srcEnd},A${r},'Mandantenzeilen'!$B$${srcStart}:$B$${srcEnd},"Hauptliste")`,
    `=SUMIFS('DATEV 31.12.24'!$I$${dvStart}:$I$${dvEnd},'DATEV 31.12.24'!$B$${dvStart}:$B$${dvEnd},A${r})`,
    `=D${r}-E${r}`,
    `=SUMIFS('Nachtrag'!$D$${laterStart}:$D$${laterEnd},'Nachtrag'!$F$${laterStart}:$F$${laterEnd},A${r})`,
    `=IF(A${r}=10069,"2023-Sammelbetrag einzeln klären",IF(COUNTIFS('Mandantenzeilen'!$D$${srcStart}:$D$${srcEnd},A${r},'Mandantenzeilen'!$B$${srcStart}:$B$${srcEnd},"Hauptliste")=0,"Nur in DATEV-OPOS",IF(ABS(F${r})>0.01,"Abweichung zum 31.12.","Kontensaldo gleich")))`
  ]);
}
compare.getRange(`C${cmpStart}:H${cmpEnd}`).formulas=compForm;
compare.getRange('A:A').format.columnWidth=13;
compare.getRange('B:B').format.columnWidth=35;
compare.getRange('C:G').format.columnWidth=19;
compare.getRange('H:H').format.columnWidth=37;
money(compare,`C${cmpStart}:G${cmpEnd}`);
compare.freezePanes.freezeRows(4);

// Handout and decision view for Jamso's two recipients.
work.getRange('A2').values = [['Jamso Trainee | Arbeitspapier zur OPOS-Bereinigung']];
work.getRange('A2:F2').format.font={name:'Arial',size:15,bold:true,color:dark};
work.getRange('A3').values = [['DATEV-Stichtag 31.12.2024 · Mandantenliste laut Vorgabe aktueller Stand zum 20.09.2026']];
work.getRange('A3:F3').format.font={name:'Arial',size:10,italic:true,color:'#536776'};
work.getRange('A5:B5').values = [['Belegte Forderungsausbuchung jetzt',0]];
work.getRange('A5:B5').format={fill:pale,font:{name:'Arial',size:11,bold:true,color:dark},rowHeight:29};
work.getRange('C5').values = [['Aus den vorliegenden Listen ist kein endgültiger Forderungsausfall belegt.']];
work.getRange('C5:F5').format.font={name:'Arial',size:10,color:'#7C3D11'};
work.getRange('A7:B7').values = [['Kennzahl','EUR']]; header(work,'A7:B7');
work.getRange('A8:A14').values = [
  ['Excel-Hauptliste, D minus E'],['davon 2023-Sammelposten 10069'],['übrige Einzelkonten, netto'],
  ['Excel-Hauptliste rechnerisch 31.12.24'],['Zahlungen nach Summenzeile, separat'],
  ['DATEV-OPOS 31.12.24, gesamter Mandant'],['DATEV-Konto 10069, netto']
];
work.getRange('B8:B14').formulas = [
  [`=SUMIFS('Mandantenzeilen'!$L$${srcStart}:$L$${srcEnd},'Mandantenzeilen'!$B$${srcStart}:$B$${srcEnd},"Hauptliste")`],
  [`=SUMIFS('Mandantenzeilen'!$L$${srcStart}:$L$${srcEnd},'Mandantenzeilen'!$D$${srcStart}:$D$${srcEnd},10069,'Mandantenzeilen'!$B$${srcStart}:$B$${srcEnd},"Hauptliste")`],
  ['=B8-B9'],
  [`=SUMIFS('Mandantenzeilen'!$M$${srcStart}:$M$${srcEnd},'Mandantenzeilen'!$B$${srcStart}:$B$${srcEnd},"Hauptliste")`],
  [`=SUM('Nachtrag'!$D$${laterStart}:$D$${laterEnd})`],
  [`=SUM('DATEV 31.12.24'!$I$${dvStart}:$I$${dvEnd})`],
  [`=SUMIFS('DATEV 31.12.24'!$I$${dvStart}:$I$${dvEnd},'DATEV 31.12.24'!$B$${dvStart}:$B$${dvEnd},10069)`]
];
work.getRange('C8:C14').values=[
  ['Ohne übernommene Ergebniswerte der Originaldatei.'],
  ['Kein belegter Saldo einzelner Rechnungen.'],
  ['Enthält auch negative Salden und einen 2023er Rechnungsbezug.'],
  ['Nur aus Quelldaten und Zahlungsdaten rekonstruiert; nicht DATEV-bestätigt.'],
  ['Aufteilung 2024/25: viele Zahlungen passen zur 2025-Folgerechnung; nicht pauschal abziehen.'],
  ['Alle 789 offenen DATEV-Buchungszeilen, auch außerhalb der Jamso-Liste.'],
  ['Abweichung zum Excel-Sammelposten zeigt fehlende Einzelzuordnung.']
];
work.getRange('A15').values=[['DATEV-Debitoren nicht in Excel-Hauptliste']];
work.getRange('B15').formulas=[[`=COUNTIFS('Kontenabgleich'!$H$${cmpStart}:$H$${cmpEnd},"Nur in DATEV-OPOS")`]];
work.getRange('C15').values=[['Für diese Konten lässt die Hauptliste den Zahlungsstatus nach 2024 offen.']];
work.getRange('B15').setNumberFormat('0');
work.getRange('A16:F16').values=[['Konto','Rechnung / Sachverhalt','EUR','Entscheidung','Beleglage','Konkreter Arbeitsschritt']];
header(work,'A16:F16');
const caseStart=17,caseEnd=caseStart+data.cases.length-1;
writeRows(work,caseStart,data.cases);
work.getRange(`A${caseStart}:F${caseEnd}`).format.rowHeight=49;
work.getRange(`D${caseStart}:F${caseEnd}`).format.wrapText=true;
work.getRange(`A${caseStart}:F${caseEnd}`).format.verticalAlignment='center';
work.getRange('A:A').format.columnWidth=39;
work.getRange('B:B').format.columnWidth=33;
work.getRange('C:C').format.columnWidth=19;
work.getRange('D:D').format.columnWidth=27;
work.getRange('E:E').format.columnWidth=75;
work.getRange('F:F').format.columnWidth=79;
money(work,'B5');money(work,'B8:B14');money(work,`C${caseStart}:C${caseEnd}`);
work.getRange('A9:C9').format.fill=amber;
work.getRange('A13:C13').format.fill=amber;
work.getRange(`A${caseStart}:F${caseStart}`).format.fill=amber;
const noteRow=caseEnd+2;
work.getRange(`A${noteRow}`).values=[['Bearbeitungsregel']];
work.getRange(`A${noteRow}:F${noteRow}`).format.font={name:'Arial',size:11,bold:true,color:dark};
work.getRange(`A${noteRow+1}`).values=[['Zahlung → Auszifferung; Storno → Gegenbuchung; Fehlzuordnung → Umbuchung. Forderungsausfall/Wertberichtigung nur mit belegter Einzelprüfung.']];
work.getRange(`A${noteRow+2}`).values=[['Der DATEV-Auszug endet 31.12.2024. Mandantenlisten und Zahlungstracker ersetzen keine DATEV-Jahre 2025/26 oder Bankbelege.']];
work.getRange(`A${noteRow+3}`).values=[['Datumsfehler: Zeile 50 „11.04.024“ mit DATEV auf 11.04.2024 normalisiert; Zeilen 77/82 im Original belassen und markiert.']];
work.getRange(`A${noteRow+4}`).values=[['Rechtsgrundlagen: HGB § 253 Abs. 4 (Bewertung); UStG § 17 Abs. 2 Nr. 1 (Uneinbringlichkeit).']];
work.getRange(`A${noteRow+5}`).values=[['https://www.gesetze-im-internet.de/hgb/__253.html  |  https://www.gesetze-im-internet.de/ustg_1980/__17.html']];
work.getRange(`A${noteRow+6}`).values=[['BFH V R 49/10: Uneinbringlichkeit verlangt eine objektiv auf absehbare Zeit nicht durchsetzbare Forderung.']];
work.getRange(`A${noteRow+7}`).values=[['https://www.bundesfinanzhof.de/de/entscheidung/entscheidungen-online/detail/STRE201250444/']];
work.getRange(`A${noteRow+1}:A${noteRow+7}`).format.font={name:'Arial',size:10,color:'#455560'};

wb.recalculate();
const checks = {};
for(const [key, sheet, range] of [
  ['summary',work,'A5:C14'],['compare',compare,'A4:H9'],['source',src,'A4:N7'],['later',later,'A4:H8'],['datev',dv,'A4:J7']
]) {
  const result=await wb.inspect({kind:'region',sheetId:sheet.name,range,maxChars:4500});
  checks[key]=result.ndjson;
}
const err=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'final formula error scan'});
console.log(JSON.stringify({checks,errors:err.ndjson}));
for(const [name,range,file] of [
  ['Arbeitspapier','A2:F14','preview-arbeitspapier.png'],
  ['Arbeitspapier','A16:F22','preview-faelle.png'],
  ['Arbeitspapier','A32:F43','preview-regeln.png'],
  ['Kontenabgleich','A1:H10','preview-kontenabgleich.png'],
  ['Nachtrag','A1:H9','preview-nachtrag.png'],
  ['Aufteilung 2024-25','A1:K9','preview-aufteilung.png'],
  ['Mandantenzeilen','A1:N8','preview-mandantenzeilen.png'],
  ['DATEV 31.12.24','A1:J8','preview-datev.png'],
  ['Zahlungstracker','A1:E8','preview-zahlungstracker.png'],
  ['Stornoliste','A1:H9','preview-storno.png']
]) {
  const image=await wb.render({sheetName:name,range,scale:1,format:'png'});
  await fs.writeFile(path.join(root,file),new Uint8Array(await image.arrayBuffer()));
}
await fs.mkdir(outDir,{recursive:true});
const result=await SpreadsheetFile.exportXlsx(wb);
await result.save(outFile);
console.log(JSON.stringify({output:outFile,source_rows:data.source_rows.length,datev_rows:data.datev_open_rows.length}));
