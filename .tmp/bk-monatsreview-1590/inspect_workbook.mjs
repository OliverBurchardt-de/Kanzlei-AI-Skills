import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "../../bk-monatsreview/assets/Monatsreview Arbeitspapier.xlsx";
const renderDir = "renders-before";

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

console.log((await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 12000,
  tableMaxRows: 5,
  tableMaxCols: 20,
  tableMaxCellChars: 120,
})).ndjson);

console.log((await workbook.inspect({
  kind: "region",
  sheetId: "1590 Klärungsliste",
  range: "A1:K8",
  maxChars: 5000,
})).ndjson);

console.log((await workbook.inspect({
  kind: "computedStyle",
  sheetId: "1590 Klärungsliste",
  range: "A1:K4",
  maxChars: 5000,
})).ndjson);

await fs.mkdir(renderDir, { recursive: true });
for (const sheetName of [
  "Übersicht",
  "Prüfergebnisse",
  "Auszifferungsliste",
  "Umbuchungsvorschläge",
  "1590 Klärungsliste",
  "Geprüfte Bereiche",
]) {
  const image = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  const safeName = sheetName.replaceAll(" ", "_");
  await fs.writeFile(`${renderDir}/${safeName}.png`, new Uint8Array(await image.arrayBuffer()));
}
