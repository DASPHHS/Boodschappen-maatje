"""One daily HTML digest from approved Github Actions SMTP secrets."""
import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

def main():
    missing=[k for k in ("SMTP_HOST","SMTP_USER","SMTP_PASSWORD","EMAIL_TO") if not os.getenv(k)]
    if missing:
        raise SystemExit("Geen e-mail verstuurd: configureer GitHub Actions secrets: "+", ".join(missing))
    data=json.loads(Path("data/buitenkansjes.json").read_text(encoding="utf8"))
    body=Path("docs/buitenkansjes.html").read_text(encoding="utf8")
    day=datetime.now(ZoneInfo("Europe/Amsterdam"))
    count=len(data.get("confirmed",[]))
    msg=EmailMessage()
    msg["Subject"]=f"Koopkracht Radar | {count} bewezen buitenkansjes | {day:%d-%m-%Y}"
    msg["From"]=os.environ["SMTP_USER"]
    msg["To"]=os.environ["EMAIL_TO"]
    msg.set_content(f"Vandaag {count} onderbouwde buitenkansjes.\n\nBekijk de aanbiedingen, kandidaten en komende-week-acties op https://dasphhs.github.io/koopkracht/buitenkansjes.html\n\nBron: PrijsProfeet (https://www.prijsprofeet.nl).\n")
    msg.add_alternative(body,subtype="html")
    port=int(os.getenv("SMTP_PORT") or "587")
    if port==465:
        with smtplib.SMTP_SSL(os.environ["SMTP_HOST"],port,timeout=30) as s:
            s.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(os.environ["SMTP_HOST"],port,timeout=30) as s:
            s.starttls()
            s.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
            s.send_message(msg)
    print("E-mail bevestigd verzonden met",count,"bewezen buitenkansjes")

if __name__=="__main__": main()
