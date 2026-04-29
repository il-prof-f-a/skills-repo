---
name: report-tecnico
description: Use when user asks to generate a technical activity report, "report tecnico attività", "genera report", "crea report intervento", or /report-tecnico — creates a professional PDF with activities table, hours total, and conclusions
---

# Report Tecnico Attività — PDF Generator

Genera PDF professionale con tabella attività, totale ore e considerazioni finali.

## Execution

### Modalità interattiva (Claude chiede i dati)

```bash
cd ".claude/skills/report-tecnico" && python genera_report.py
```

Claude deve raccogliere dall'utente:
1. **Titolo** (default: "Report Intervento Tecnico")
2. **Mittente** (nome e cognome / azienda)
3. **Destinatario**
4. **Periodo** (es. "Aprile 2026")
5. **Attività** — ripetere per ogni riga: data (gg/mm/aaaa), descrizione, ore
6. **Considerazioni finali** (testo libero)

Poi costruire il file JSON e passarlo con `--json`.

### Modalità JSON (preferita)

```bash
cd ".claude/skills/report-tecnico" && python genera_report.py --json dati.json
```

### Output custom

```bash
python genera_report.py --json dati.json --output "Report_Marzo_2026.pdf"
```

## Formato JSON

```json
{
  "titolo": "Report Intervento Tecnico",
  "mittente": "Francesco Adriani",
  "destinatario": "Comune di Città di Castello",
  "periodo": "Aprile 2026",
  "considerazioni": "Testo conclusioni...",
  "attivita": [
    {"data": "02/04/2026", "descrizione": "Analisi requisiti", "ore": "3"},
    {"data": "07/04/2026", "descrizione": "Configurazione server", "ore": "5"}
  ]
}
```

## Struttura PDF generato

| Sezione | Contenuto |
|---------|-----------|
| Header blu | Titolo + data emissione |
| Intestazione | Mittente, Destinatario, Periodo |
| Tabella attività | Data / Descrizione / Ore (righe alternate) |
| Totale ore | Somma automatica |
| Considerazioni finali | Testo libero |
| Firma | Spazio + nome mittente |

## Dipendenze

- `fpdf2` — già installato (`pip install fpdf2`)
- Nessuna env var richiesta

## Workflow consigliato

1. Chiedi all'utente i dati mancanti
2. Scrivi file JSON temporaneo (es. `/tmp/report_dati.json`)
3. Esegui script con `--json`
4. Apri il PDF generato con `start <percorso>.pdf` (Windows)

## Common mistakes

- `ore` deve essere numero (intero o decimale con `.` o `,`)
- `data` in formato gg/mm/aaaa
- File JSON con encoding UTF-8
