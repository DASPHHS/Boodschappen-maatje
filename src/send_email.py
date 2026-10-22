"""Daily plain-text offer digest. Uses SMTP repository secrets."""
import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

def main():
    env = ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO")
    missing = [key for key in env if not os.getenv(key)]
    if missing:
        raise SystemExit("Dagelijkse e-mail NIET verstuurd: ontbrekende GitHub Actions secrets: " + ", ".join(missing))
    path = Path("docs/data.json")
    if not path.is_file():
        raise SystemExit("Dagelijkse e-mail NIET verstuurd: docs/data.json ontbreekt")
    data = json.loads(path.read_text(encoding="utf-8"))
    offers = data.get("offers", [])
    stores = ("Albert Heijn", "Jumbo", "Lidl")
    sections = []
    for store in stores:
        rows = [o for o in offers if str(o.get("store", "")).casefold() == store.casefold() and o.get("price") is not None]
        if not rows:
            raise SystemExit(f"Dagelijkse e-mail NIET verstuurd: geen prijzen voor {store}")
        lines = [f"{store}: {len(rows)} gevonden aanbiedingen"]
        for o in sorted(rows, key=lambda x: x.get("savings_percentage") or 0, reverse=True)[:30]:
            p = f"EUR {o['price']:.2f}" if isinstance(o["price"], (float,int)) else str(o["price"])
            expiry = f" (t/m {o['valid_until']})" if o.get("valid_until") else ""
            lines.append(f"- {o.get('text','Product')}: {p}{expiry}")
        sections.append("\n".join(lines))
    day = datetime.now(ZoneInfo("Europe/Amsterdam"))
    body = ("KOOPKRACHT DAGELIJKSE SCAN | " + day.strftime("%d-%m-%Y") +
            "\n\n" + "\n\n".join(sections) +
            "\n\nLET OP: Dit zijn aanbiedingen, NIET een volledig berekende boodschappenmand of 48 geprijsde recepten." +
            "\nZie het dashboard voor meer details: https://dasphhs.github.io/koopkracht/" +
            "\nBron: PrijsProfeet (https://www.prijsprofeet.nl).")
    msg = EmailMessage()
    msg["Subject"] = "Koopkracht: AH, Jumbo en Lidl | " + day.strftime("%d-%m-%Y")
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["EMAIL_TO"]
    msg.set_content(body)
    port = int(os.getenv("SMTP_PORT", "587"))
    if port == 465:
        with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], port, timeout=30) as server:
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
    else:
        with smtplib.SMTP(os.environ["SMTP_HOST"], port, timeout=30) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
    print("Dagelijkse e-mail verstuurd met aanbiedingen AH, Jumbo en Lidl.")

if __name__ == "__main__":
    main()
