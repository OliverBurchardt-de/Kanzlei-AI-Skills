import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputPath = process.argv[2];
const previewDir = process.argv[3];

if (!outputPath || !previewDir) {
  throw new Error("Usage: node build_workpaper.mjs <output.xlsx> <preview-dir>");
}

const colors = {
  navy: "#18324A",
  teal: "#0F6B78",
  tealLight: "#DDEFF1",
  blueLight: "#EAF1F8",
  yellow: "#FFF4CC",
  gray: "#E7EBEF",
  border: "#C8D0D8",
  white: "#FFFFFF",
  ready: "#D9EAD3",
  review: "#FFF2CC",
  request: "#FCE5CD",
  blocked: "#E6B8AF",
};

const workbook = Workbook.create();
const sheetNames = [
  "Steuerfall",
  "Eintragungen",
  "Berechnungen",
  "Belege",
  "Vermietung",
  "Vorjahresabgleich",
  "Prueffalle",
  "Uploadmanifest",
  "Listen",
];
const sheets = Object.fromEntries(sheetNames.map((name) => [name, workbook.worksheets.add(name)]));

function titleBlock(sheet, lastCol, title, subtitle) {
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: colors.navy,
    font: { bold: true, color: colors.white, size: 16 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 30;
  sheet.getRange(`A2:${lastCol}3`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${lastCol}3`).format = {
    fill: colors.blueLight,
    font: { color: colors.navy, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: colors.border },
  };
  sheet.getRange(`A2:${lastCol}3`).format.rowHeight = 24;
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(5);
}

function setHeaders(sheet, rangeAddress, headers) {
  const range = sheet.getRange(rangeAddress);
  range.values = [headers];
  range.format = {
    fill: colors.teal,
    font: { bold: true, color: colors.white, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: colors.border },
  };
  range.format.rowHeight = 32;
}

function setDataArea(sheet, rangeAddress) {
  sheet.getRange(rangeAddress).format = {
    font: { color: "#20262D", size: 10 },
    verticalAlignment: "top",
    wrapText: true,
    borders: {
      insideHorizontal: { style: "thin", color: colors.gray },
      bottom: { style: "thin", color: colors.border },
    },
  };
}

function setWidths(sheet, rowEnd, widths) {
  for (const [column, width] of Object.entries(widths)) {
    sheet.getRange(`${column}1:${column}${rowEnd}`).format.columnWidth = width;
  }
}

function addStatusValidationAndColors(range, values = ["bereit", "prüfen", "nachfordern", "nicht verarbeitet"]) {
  range.dataValidation = { rule: { type: "list", values } };
  const mappings = [
    ["bereit", colors.ready],
    ["prüfen", colors.review],
    ["nachfordern", colors.request],
    ["nicht verarbeitet", colors.blocked],
  ];
  for (const [text, fill] of mappings) {
    range.conditionalFormats.add("containsText", {
      text,
      format: { fill, font: { color: colors.navy } },
    });
  }
}

function addTable(sheet, address, name) {
  const table = sheet.tables.add(address, true, name);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  table.showFilterButton = true;
  return table;
}

function idRows(prefix, count = 50) {
  return Array.from({ length: count }, (_, index) => [[prefix, String(index + 1).padStart(4, "0")].join("-")]);
}

function formulaRows(count, factory) {
  return Array.from({ length: count }, (_, index) => [factory(index + 6)]);
}

// Steuerfall
{
  const sheet = sheets.Steuerfall;
  titleBlock(
    sheet,
    "H",
    "Einkommensteuer - Steuerfall und Bearbeitungsstand",
    "Gelbe Felder sind Eingaben. Das Veranlagungsjahr je Fall festlegen; Zielsystem ist DATEV Einkommensteuer. Die Statusübersicht aktualisiert sich aus den weiteren Tabellenblättern."
  );
  sheet.getRange("A5:B11").values = [
    ["Falldaten", "Wert"],
    ["Fall-ID", ""],
    ["Veranlagungsjahr", ""],
    ["Person(en)", ""],
    ["Veranlagungsart", ""],
    ["Eingabeprogramm", "DATEV Einkommensteuer"],
    ["Belegkanal", "DATEV Meine Steuern"],
  ];
  sheet.getRange("A5:B5").format = { fill: colors.teal, font: { bold: true, color: colors.white } };
  sheet.getRange("A6:A11").format = { fill: colors.gray, font: { bold: true, color: colors.navy } };
  sheet.getRange("B6:B10").format = { fill: colors.yellow };
  sheet.getRange("A5:B11").format.borders = { preset: "outside", style: "thin", color: colors.border };
  sheet.getRange("D5:E11").values = [
    ["Bearbeitungsstatus", "Anzahl"],
    ["bereit", null],
    ["prüfen", null],
    ["nachfordern", null],
    ["nicht verarbeitet", null],
    ["offene Prüffälle", null],
    ["Uploaddateien bereit", null],
  ];
  sheet.getRange("D5:E5").format = { fill: colors.teal, font: { bold: true, color: colors.white } };
  sheet.getRange("D6:D11").format = { fill: colors.gray, font: { bold: true, color: colors.navy } };
  sheet.getRange("E6:E11").formulas = [
    ["=COUNTIF('Eintragungen'!$M$6:$M$55,\"bereit\")"],
    ["=COUNTIF('Eintragungen'!$M$6:$M$55,\"prüfen\")"],
    ["=COUNTIF('Eintragungen'!$M$6:$M$55,\"nachfordern\")"],
    ["=COUNTIF('Eintragungen'!$M$6:$M$55,\"nicht verarbeitet\")"],
    ["=COUNTIF('Prueffalle'!$I$6:$I$55,\"offen\")"],
    ["=COUNTIF('Uploadmanifest'!$K$6:$K$55,\"bereit\")"],
  ];
  sheet.getRange("D5:E11").format.borders = { preset: "outside", style: "thin", color: colors.border };
  sheet.getRange("E6:E11").format.numberFormat = "0";
  sheet.getRange("A14:H17").merge();
  sheet.getRange("A14").values = [["Freigabehinweis: Der Status 'bereit' bedeutet nur, dass Beleg, Berechnung und Zuordnung nachvollziehbar sind. Die fachliche Schlussprüfung und Dateneingabe bleiben menschliche Tätigkeiten."]];
  sheet.getRange("A14:H17").format = { fill: colors.review, font: { color: colors.navy, bold: true }, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: colors.border } };
  setWidths(sheet, 20, { A: 24, B: 42, C: 4, D: 24, E: 14, F: 4, G: 16, H: 16 });
}

// Eintragungen
{
  const sheet = sheets.Eintragungen;
  titleBlock(sheet, "N", "Eintragungen je Mantelbogen oder Anlage", "Eine Zeile je vorgeschlagener Eintragungsposition. Programmspezifische Felder nur verwenden, wenn sie für das Veranlagungsjahr bestätigt sind; andernfalls Status 'prüfen'.");
  const headers = ["Positions-ID", "Person", "VZ", "Formularstand", "Anlage", "Kennziffer/Feld", "DATEV-Zielfeld", "Betrag EUR", "Berechnungs-ID", "Quellen-IDs", "Vorjahr EUR", "Abweichung EUR", "Status", "Prüfhinweis"];
  setHeaders(sheet, "A5:N5", headers);
  setDataArea(sheet, "A6:N55");
  sheet.getRange("A6:A55").values = idRows("POS");
  sheet.getRange("L6:L55").formulas = formulaRows(50, (row) => '=IF(OR(H' + row + '="",K' + row + '=""),"",H' + row + '-K' + row + ')');
  sheet.getRange("C6:C55").format.numberFormat = "0";
  sheet.getRange("H6:H55").format.numberFormat = "#,##0.00";
  sheet.getRange("K6:L55").format.numberFormat = "#,##0.00;[Red]-#,##0.00";
  addStatusValidationAndColors(sheet.getRange("M6:M55"));
  addTable(sheet, "A5:N55", "EintragungenTable");
  setWidths(sheet, 55, { A: 15, B: 18, C: 9, D: 15, E: 17, F: 24, G: 22, H: 14, I: 16, J: 20, K: 14, L: 16, M: 20, N: 38 });
}

// Berechnungen
{
  const sheet = sheets.Berechnungen;
  titleBlock(sheet, "I", "Berechnungen und Aufteilungen", "Einfache Aufteilungen über Ausgangsbetrag und Anteil rechnen. Komplexe Berechnungen in mehrere prüfbare Zeilen zerlegen und Quellen-IDs angeben.");
  const headers = ["Berechnungs-ID", "Positions-ID", "Beschreibung", "Quellen-IDs", "Ausgangsbetrag EUR", "Anteil", "Ergebnis EUR", "Methode/Annahme", "Status"];
  setHeaders(sheet, "A5:I5", headers);
  setDataArea(sheet, "A6:I55");
  sheet.getRange("A6:A55").values = idRows("BER");
  sheet.getRange("G6:G55").formulas = formulaRows(50, (row) => '=IF(OR(E' + row + '="",F' + row + '=""),"",E' + row + '*F' + row + ')');
  sheet.getRange("E6:E55").format.numberFormat = "#,##0.00";
  sheet.getRange("F6:F55").format.numberFormat = "0.00%";
  sheet.getRange("G6:G55").format.numberFormat = "#,##0.00";
  addStatusValidationAndColors(sheet.getRange("I6:I55"));
  addTable(sheet, "A5:I55", "BerechnungenTable");
  setWidths(sheet, 55, { A: 17, B: 15, C: 34, D: 22, E: 20, F: 12, G: 17, H: 34, I: 20 });
}

// Belege
{
  const sheet = sheets.Belege;
  titleBlock(sheet, "N", "Belegregister der Mandantenunterlagen", "Jede Originaldatei genau einmal inventarisieren. Originale unverändert lassen; abgeleitete Dateien ausschließlich im Uploadmanifest führen.");
  const headers = ["Beleg-ID", "Originalpfad", "Originaldateiname", "SHA-256 Original", "Seiten", "Person", "Zeitraum", "Thema", "Objekt-ID", "Lesestatus", "Trennung nötig", "Upload-IDs", "Status", "Hinweis"];
  setHeaders(sheet, "A5:N5", headers);
  setDataArea(sheet, "A6:N55");
  sheet.getRange("A6:A55").values = idRows("BEL");
  sheet.getRange("E6:E55").format.numberFormat = "0";
  sheet.getRange("K6:K55").dataValidation = { rule: { type: "list", values: ["ja", "nein", "prüfen"] } };
  addStatusValidationAndColors(sheet.getRange("M6:M55"));
  addTable(sheet, "A5:N55", "BelegeTable");
  setWidths(sheet, 55, { A: 14, B: 34, C: 28, D: 34, E: 9, F: 18, G: 16, H: 26, I: 14, J: 18, K: 16, L: 20, M: 20, N: 34 });
}

// Vermietung
{
  const sheet = sheets.Vermietung;
  titleBlock(sheet, "L", "Vermietungsobjekte", "Objektkennzeichnungen aus Ordnern und Dateinamen gegen den Beleginhalt plausibilisieren. Aufteilungsquoten nicht ohne dokumentierte Flächen- oder Nutzungsgrundlage übernehmen.");
  const headers = ["Objekt-ID", "Bezeichnung", "Anschrift", "Person", "Eigentumsanteil", "Vermietungszeitraum", "Gesamtfläche qm", "Vermietete Fläche qm", "Flächenanteil", "Quellen-IDs", "Status", "Prüfhinweis"];
  setHeaders(sheet, "A5:L5", headers);
  setDataArea(sheet, "A6:L55");
  sheet.getRange("A6:A55").values = idRows("OBJ");
  sheet.getRange("I6:I55").formulas = formulaRows(50, (row) => '=IF(OR(G' + row + '="",H' + row + '="",G' + row + '=0),"",H' + row + '/G' + row + ')');
  sheet.getRange("E6:E55").format.numberFormat = "0.00%";
  sheet.getRange("G6:H55").format.numberFormat = "#,##0.00";
  sheet.getRange("I6:I55").format.numberFormat = "0.00%";
  addStatusValidationAndColors(sheet.getRange("K6:K55"));
  addTable(sheet, "A5:L55", "VermietungTable");
  setWidths(sheet, 55, { A: 14, B: 24, C: 34, D: 18, E: 18, F: 22, G: 20, H: 22, I: 16, J: 22, K: 20, L: 38 });
}

// Vorjahresabgleich
{
  const sheet = sheets.Vorjahresabgleich;
  titleBlock(sheet, "J", "Vorjahresabgleich", "Vorjahreswerte nur als Erwartungs- und Plausibilitätsgerüst nutzen. Jede Position als fortgeführt, geändert, weggefallen, neu oder ungeklärt klassifizieren.");
  const headers = ["Abgleich-ID", "Person", "Objekt-ID", "Anlage/Sachverhalt", "Vorjahr EUR", "Aktuell EUR", "Abweichung EUR", "Klassifikation", "Quellen-/Positions-IDs", "Prüfhinweis"];
  setHeaders(sheet, "A5:J5", headers);
  setDataArea(sheet, "A6:J55");
  sheet.getRange("A6:A55").values = idRows("ABG");
  sheet.getRange("G6:G55").formulas = formulaRows(50, (row) => '=IF(OR(E' + row + '="",F' + row + '=""),"",F' + row + '-E' + row + ')');
  sheet.getRange("E6:G55").format.numberFormat = "#,##0.00;[Red]-#,##0.00";
  sheet.getRange("H6:H55").dataValidation = { rule: { type: "list", values: ["fortgeführt", "geändert", "weggefallen", "neu", "ungeklärt"] } };
  addTable(sheet, "A5:J55", "VorjahresabgleichTable");
  setWidths(sheet, 55, { A: 15, B: 18, C: 14, D: 30, E: 16, F: 16, G: 17, H: 18, I: 25, J: 38 });
}

// Prueffalle
{
  const sheet = sheets.Prueffalle;
  titleBlock(sheet, "J", "Prüf- und Nachforderungsprotokoll", "Jede offene Annahme oder fehlende Unterlage mit Auswirkung, vorläufiger Behandlung und konkreter nächster Handlung ausweisen.");
  const headers = ["Prüffall-ID", "Kategorie", "Betroffene IDs", "Sachverhalt", "Vorläufige Behandlung", "Fehlende Angabe/Unterlage", "Nächste Handlung", "Priorität", "Status", "Erledigungsnachweis"];
  setHeaders(sheet, "A5:J5", headers);
  setDataArea(sheet, "A6:J55");
  sheet.getRange("A6:A55").values = idRows("PRF");
  sheet.getRange("H6:H55").dataValidation = { rule: { type: "list", values: ["hoch", "mittel", "niedrig"] } };
  sheet.getRange("I6:I55").dataValidation = { rule: { type: "list", values: ["offen", "in Prüfung", "erledigt"] } };
  sheet.getRange("I6:I55").conditionalFormats.add("containsText", { text: "offen", format: { fill: colors.request } });
  sheet.getRange("I6:I55").conditionalFormats.add("containsText", { text: "in Prüfung", format: { fill: colors.review } });
  sheet.getRange("I6:I55").conditionalFormats.add("containsText", { text: "erledigt", format: { fill: colors.ready } });
  addTable(sheet, "A5:J55", "PrueffalleTable");
  setWidths(sheet, 55, { A: 16, B: 20, C: 22, D: 38, E: 32, F: 34, G: 34, H: 12, I: 16, J: 32 });
}

// Uploadmanifest
{
  const sheet = sheets.Uploadmanifest;
  titleBlock(sheet, "L", "Uploadmanifest DATEV Meine Steuern", "Nur eindeutig getrennte, erneut geöffnete und per SHA-256 geprüfte Dateien als 'bereit' kennzeichnen. Originaldateien niemals ersetzen.");
  const headers = ["Upload-ID", "Upload-Dateiname", "Beleg-ID Original", "Originaldateiname", "Seite von", "Seite bis", "Person", "Thema/Anlage", "Objekt-ID", "SHA-256 Upload", "Status", "Hinweis"];
  setHeaders(sheet, "A5:L5", headers);
  setDataArea(sheet, "A6:L55");
  sheet.getRange("A6:A55").values = idRows("UPL");
  sheet.getRange("E6:F55").format.numberFormat = "0";
  addStatusValidationAndColors(sheet.getRange("K6:K55"));
  addTable(sheet, "A5:L55", "UploadmanifestTable");
  setWidths(sheet, 55, { A: 14, B: 36, C: 20, D: 30, E: 12, F: 12, G: 18, H: 26, I: 14, J: 36, K: 20, L: 34 });
}

// Listen
{
  const sheet = sheets.Listen;
  titleBlock(sheet, "F", "Auswahllisten und Begriffe", "Diese Werte definieren die zulässigen Status- und Klassifikationsbegriffe. Änderungen nur abgestimmt vornehmen.");
  sheet.getRange("A5:F11").values = [
    ["Bearbeitungsstatus", "Prüffallstatus", "Priorität", "Vorjahresklassifikation", "Ja/Nein/Prüfen", "Belegkanal"],
    ["bereit", "offen", "hoch", "fortgeführt", "ja", "DATEV Meine Steuern"],
    ["prüfen", "in Prüfung", "mittel", "geändert", "nein", ""],
    ["nachfordern", "erledigt", "niedrig", "weggefallen", "prüfen", ""],
    ["nicht verarbeitet", "", "", "neu", "", ""],
    ["", "", "", "ungeklärt", "", ""],
    ["", "", "", "", "", ""],
  ];
  setHeaders(sheet, "A5:F5", ["Bearbeitungsstatus", "Prüffallstatus", "Priorität", "Vorjahresklassifikation", "Ja/Nein/Prüfen", "Belegkanal"]);
  setDataArea(sheet, "A6:F11");
  setWidths(sheet, 15, { A: 24, B: 22, C: 16, D: 28, E: 20, F: 26 });
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const inspection = await workbook.inspect({
  kind: "sheet,formula",
  maxChars: 8000,
  tableMaxRows: 8,
  tableMaxCols: 14,
});
const errorScan = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
await fs.writeFile(path.join(previewDir, "inspection.ndjson"), `${inspection.ndjson}\n${errorScan.ndjson}\n`, "utf8");

const previewRanges = {
  Steuerfall: "A1:H18",
  Eintragungen: "A1:N12",
  Berechnungen: "A1:I12",
  Belege: "A1:N12",
  Vermietung: "A1:L12",
  Vorjahresabgleich: "A1:J12",
  Prueffalle: "A1:J12",
  Uploadmanifest: "A1:L12",
  Listen: "A1:F12",
};
for (const [sheetName, range] of Object.entries(previewRanges)) {
  const preview = await workbook.render({ sheetName, range, scale: 1.5, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

console.log(JSON.stringify({ outputPath, previewDir, sheets: sheetNames }, null, 2));
