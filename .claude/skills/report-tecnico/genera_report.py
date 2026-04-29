"""
Genera PDF report tecnico attività.
Usage:
    python genera_report.py                  # modalità interattiva
    python genera_report.py --json dati.json # da file JSON
    python genera_report.py --help
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ── colori corporate ──────────────────────────────────────────
BLUE_DARK  = (23, 55, 94)
BLUE_MID   = (41, 98, 166)
BLUE_LIGHT = (210, 228, 255)
GRAY_LIGHT = (245, 245, 245)
WHITE      = (255, 255, 255)
BLACK      = (30, 30, 30)


class ReportPDF(FPDF):
    def __init__(self, titolo: str, data_emissione: str):
        super().__init__()
        self.titolo = titolo
        self.data_emissione = data_emissione

    def header(self):
        # barra superiore blu
        self.set_fill_color(*BLUE_DARK)
        self.rect(0, 0, 210, 18, "F")
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 11)
        self.set_xy(10, 4)
        self.cell(0, 10, self.titolo.upper(), new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
        self.set_font("Helvetica", "", 9)
        self.set_xy(0, 5)
        self.cell(200, 8, f"Emesso il {self.data_emissione}", new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*BLUE_MID)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")


def _section_title(pdf: ReportPDF, testo: str):
    pdf.set_fill_color(*BLUE_LIGHT)
    pdf.set_text_color(*BLUE_DARK)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"  {testo}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(2)
    pdf.set_text_color(*BLACK)


def _body(pdf: ReportPDF, testo: str, bold: bool = False):
    pdf.set_font("Helvetica", "B" if bold else "", 10)
    pdf.set_text_color(*BLACK)
    pdf.multi_cell(0, 6, testo)


def build_pdf(
    titolo: str,
    mittente: str,
    destinatario: str,
    periodo: str,
    attivita: list[dict],   # [{data, descrizione, ore}]
    considerazioni: str,
    output_path: Path,
) -> Path:
    data_emissione = datetime.now().strftime("%d/%m/%Y")
    pdf = ReportPDF(titolo=titolo, data_emissione=data_emissione)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(12, 22, 12)

    # ── intestazione ──────────────────────────────────────────
    _section_title(pdf, "INTESTAZIONE")
    pdf.set_font("Helvetica", "", 10)
    rows = [
        ("Mittente",    mittente),
        ("Destinatario", destinatario),
        ("Periodo",     periodo),
        ("Data emissione", data_emissione),
    ]
    for label, valore in rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 7, f"{label}:", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, valore, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # ── tabella attività ──────────────────────────────────────
    _section_title(pdf, "ELENCO ATTIVITÀ")

    col_w = [28, 122, 28]
    headers = ["Data", "Descrizione attività", "Ore"]

    # intestazione tabella
    pdf.set_fill_color(*BLUE_MID)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 10)
    for w, h in zip(col_w, headers):
        pdf.cell(w, 8, h, border=1, align="C", fill=True)
    pdf.ln()

    # righe alternate
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "", 9)
    for i, row in enumerate(attivita):
        fill = (i % 2 == 0)
        pdf.set_fill_color(*GRAY_LIGHT if fill else WHITE)

        data_str = str(row.get("data", ""))
        desc_str  = str(row.get("descrizione", ""))
        ore_str   = str(row.get("ore", ""))

        # calcola altezza per multi-line descrizione
        lines = pdf.multi_cell(col_w[1], 6, desc_str, dry_run=True, output="LINES")
        row_h = max(6, len(lines) * 6)

        y0 = pdf.get_y()
        x0 = pdf.get_x()

        pdf.cell(col_w[0], row_h, data_str, border=1, align="C", fill=fill)
        pdf.multi_cell(col_w[1], row_h / max(1, len(lines)), desc_str,
                       border=1, fill=fill, max_line_height=6)
        pdf.set_xy(x0 + col_w[0] + col_w[1], y0)
        pdf.cell(col_w[2], row_h, ore_str, border=1, align="C", fill=fill)
        pdf.set_xy(x0, y0 + row_h)

    # totale
    totale = sum(float(str(r.get("ore", 0)).replace(",", ".")) for r in attivita)
    pdf.set_fill_color(*BLUE_DARK)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[0] + col_w[1], 8, "TOTALE ORE", border=1, align="R", fill=True)
    totale_str = f"{totale:.1f}".rstrip("0").rstrip(".")
    pdf.cell(col_w[2], 8, totale_str, border=1, align="C", fill=True)
    pdf.ln(8)

    # ── considerazioni finali ─────────────────────────────────
    _section_title(pdf, "CONSIDERAZIONI FINALI")
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, considerazioni)
    pdf.ln(10)

    # ── firma ─────────────────────────────────────────────────
    pdf.set_x(130)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Firma: ___________________________", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(130)
    pdf.cell(0, 6, mittente, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(str(output_path))
    return output_path


# ── input interattivo ─────────────────────────────────────────

def chiedi(prompt: str, default: str = "") -> str:
    risposta = input(f"{prompt}{' [' + default + ']' if default else ''}: ").strip()
    return risposta if risposta else default


def input_interattivo() -> dict:
    print("\n=== REPORT TECNICO ATTIVITÀ ===\n")
    titolo      = chiedi("Titolo report", "Report Intervento Tecnico")
    mittente    = chiedi("Mittente (nome e cognome / azienda)")
    destinatario = chiedi("Destinatario")
    periodo     = chiedi("Periodo di riferimento (es. Marzo 2026)")
    considerazioni = chiedi("Considerazioni finali")

    attivita = []
    print("\nInserisci le attività (lascia 'Data' vuota per terminare):")
    while True:
        data = chiedi("  Data (gg/mm/aaaa)")
        if not data:
            break
        descrizione = chiedi("  Descrizione")
        ore = chiedi("  Ore")
        attivita.append({"data": data, "descrizione": descrizione, "ore": ore})

    return {
        "titolo": titolo,
        "mittente": mittente,
        "destinatario": destinatario,
        "periodo": periodo,
        "considerazioni": considerazioni,
        "attivita": attivita,
    }


def main():
    parser = argparse.ArgumentParser(description="Genera PDF report tecnico attività")
    parser.add_argument("--json", metavar="FILE", help="Dati da file JSON")
    parser.add_argument("--output", metavar="FILE", help="File PDF output (default: auto)")
    args = parser.parse_args()

    if args.json:
        with open(args.json, encoding="utf-8") as f:
            dati = json.load(f)
    else:
        dati = input_interattivo()

    if not dati.get("attivita"):
        print("Errore: nessuna attività inserita.")
        sys.exit(1)

    periodo_safe = dati.get("periodo", "").replace(" ", "_").replace("/", "-")
    default_out = f"Report_Tecnico_{periodo_safe}.pdf"
    output_path = Path(args.output or default_out)

    build_pdf(
        titolo        = dati.get("titolo", "Report Tecnico Attività"),
        mittente      = dati.get("mittente", ""),
        destinatario  = dati.get("destinatario", ""),
        periodo       = dati.get("periodo", ""),
        attivita      = dati["attivita"],
        considerazioni = dati.get("considerazioni", ""),
        output_path   = output_path,
    )

    print(f"\nReport generato: {output_path.resolve()}")


if __name__ == "__main__":
    main()
