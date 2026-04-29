---
name: meteo-report
description: Use when user asks for meteo report, weather email, manda meteo, or /meteo-report — fetches 24h forecast for Città di Castello and sends HTML email
---

# Meteo Report — Città di Castello (PG)

Fetch prossime 24h da Open-Meteo, invia email HTML a prof.f.adriani@gmail.com.

## Execution

```bash
cd ".claude/skills/meteo-report" && python meteo_report.py
```

**Richiede:** `GMAIL_APP_PASSWORD` env var — impostata in `.claude/settings.local.json` (git-ignored).

## Config inside script

| Parametro | Valore |
|-----------|--------|
| City | Città di Castello (PG) — 43.4569°N, 12.2378°E |
| From / To | prof.f.adriani@gmail.com |
| API | Open-Meteo (nessuna chiave necessaria) |
| Dati | temp, prob. pioggia, vento, codice meteo |

## Common mistakes

- `GMAIL_APP_PASSWORD` vuota → script esce con errore, controllare settings.local.json
- Password con spazi: `"ctiy shtb wavr zenv"` va usata esatta (con spazi)
