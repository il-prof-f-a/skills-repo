import urllib.request
import json
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Config
GMAIL_USER = "prof.f.adriani@gmail.com"
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TO_EMAIL = "prof.f.adriani@gmail.com"

# Città di Castello (PG) coordinates
LAT = 43.4569
LON = 12.2378
CITY = "Città di Castello (PG)"


def weather_desc(code):
    if code == 0:
        return "☀️ Sereno"
    elif code <= 3:
        return "⛅ Poco nuvoloso"
    elif code <= 48:
        return "🌫️ Nebbia"
    elif code <= 67:
        return "🌧️ Pioggia"
    elif code <= 77:
        return "❄️ Neve"
    elif code <= 82:
        return "🌦️ Rovesci"
    elif code <= 86:
        return "🌨️ Neve forte"
    else:
        return "⛈️ Temporale"


def fetch_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&hourly=temperature_2m,precipitation_probability,weathercode,windspeed_10m"
        f"&timezone=Europe%2FRome"
        f"&forecast_days=1"
    )
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def build_html(data):
    hourly = data["hourly"]
    times = hourly["time"]
    temps = hourly["temperature_2m"]
    prec = hourly["precipitation_probability"]
    codes = hourly["weathercode"]
    winds = hourly["windspeed_10m"]

    date_str = datetime.now().strftime("%d/%m/%Y")

    rows = ""
    for i in range(24):
        hour = times[i][11:16]
        bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
        rows += f"""
        <tr style="background:{bg}">
            <td style="padding:8px 12px; text-align:center;">{hour}</td>
            <td style="padding:8px 12px;">{weather_desc(codes[i])}</td>
            <td style="padding:8px 12px; text-align:center;"><b>{temps[i]:.1f}°C</b></td>
            <td style="padding:8px 12px; text-align:center;">{prec[i]}%</td>
            <td style="padding:8px 12px; text-align:center;">{winds[i]:.1f} km/h</td>
        </tr>"""

    return f"""
<html><body style="font-family:Arial,sans-serif; margin:20px;">
<h2 style="color:#2c5f8a;">🌤️ Meteo {CITY} &mdash; {date_str}</h2>
<p style="color:#555;">Previsioni prossime 24 ore</p>
<table style="border-collapse:collapse; width:100%; max-width:600px; font-size:14px; box-shadow:0 1px 4px #ccc;">
    <thead>
        <tr style="background:#2c5f8a; color:white;">
            <th style="padding:10px;">Ora</th>
            <th style="padding:10px;">Condizione</th>
            <th style="padding:10px;">Temp.</th>
            <th style="padding:10px;">Prob. pioggia</th>
            <th style="padding:10px;">Vento</th>
        </tr>
    </thead>
    <tbody>{rows}</tbody>
</table>
<p style="color:#aaa; font-size:11px; margin-top:16px;">Fonte: Open-Meteo.com</p>
</body></html>
"""


def send_email(html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌤️ Meteo {CITY} — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())

    print(f"OK - Email inviata a {TO_EMAIL}")


if __name__ == "__main__":
    if not GMAIL_PASSWORD:
        print("ERRORE: variabile GMAIL_APP_PASSWORD non impostata")
        exit(1)
    print(f"Fetching meteo {CITY}...")
    data = fetch_weather()
    html = build_html(data)
    send_email(html)
