import json, os, smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

def main():
    today = datetime.now(ZoneInfo("Europe/Amsterdam"))
    if today.weekday() not in (0, 2, 5):  # maandag woensdag zaterdag
        print("Vandaag geen e-maildag.")
        return
    env = ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO")
    if not all(os.getenv(k) for k in env):
        print("SMTP niet ingesteld; e-mail overgeslagen.")
        return
    data = json.loads(Path("docs/data.json").read_text())
    folders = data.get("folders", [])
    offers = data.get("offers", [])
    recent = sorted(folders, key=lambda x:x.get("last_seen", ""), reverse=True)[:25]
    body = "Koopkracht radar: openbare folderinformatie, niet alle prijzen geverifieerd.\n\n"
    body += f"Geregistreerde folders: {len(folders)}, aanbiedingen/tekstfragmenten: {len(offers)}\n\n"
    body += "Folders:\n" + "\n".join(f"- {x.get('store','Winkel')}: {x['url']}" for x in recent)
    body += "\n\nBekijk het dashboard via GitHub Pages."
    msg=EmailMessage()
    msg["Subject"]="Koopkracht: aanbiedingenoverzicht "+today.strftime("%d-%m-%Y")
    msg["From"]=os.environ["SMTP_USER"]
    msg["To"]=os.environ["EMAIL_TO"]
    msg.set_content(body)
    port=int(os.getenv("SMTP_PORT","587"))
    if port==465:
        with smtplib.SMTP_SSL(os.environ["SMTP_HOST"],port,timeout=30) as server:
            server.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
    else:
        with smtplib.SMTP(os.environ["SMTP_HOST"],port,timeout=30) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
    print("E-mail verzonden.")
if __name__=="__main__": main()
