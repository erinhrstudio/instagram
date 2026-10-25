"""Carica su YouTube gli Shorts di state/youtube.json, privati con l'uscita programmata (publishAt).

Il collegamento è in state/youtube.enc, cifrato con YOUTUBE_CLIENT_SECRET (workflow "YouTube: collega canale").
Ogni caricamento costa 1600 unità di quota su 10.000 al giorno: al massimo ~6 video per esecuzione.
Finché Google non verifica il progetto (audit API), YouTube blocca come privati i video caricati via API:
lo script lo controlla e si ferma se succede.

Uso (GitHub Actions): python -m tools.youtube_carica   env QUANTI=6, SOLO=<nome> per una prova
"""
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENC = ROOT / "state" / "youtube.enc"
PIANO = ROOT / "state" / "youtube.json"
API = "https://www.googleapis.com/youtube/v3"


def token():
    raw = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-pass", "env:CLIENT_SECRET",
                          "-in", str(ENC)], capture_output=True, check=True).stdout
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["CLIENT_ID"], "client_secret": os.environ["CLIENT_SECRET"],
        "refresh_token": json.loads(raw)["refresh_token"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    t = r.json()["access_token"]
    print(f"::add-mask::{t}")
    return t


def carica(it, tok):
    meta = {"snippet": {"title": it["titolo"], "description": it["descrizione"], "tags": it["tag"],
                        "categoryId": "10", "defaultLanguage": "it", "defaultAudioLanguage": "it"},
            "status": {"privacyStatus": "private", "publishAt": it["publish_at"],
                       "selfDeclaredMadeForKids": False}}
    h = {"Authorization": f"Bearer {tok}"}
    data = (ROOT / it["file"]).read_bytes()
    r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={**h, "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(data))},
                      data=json.dumps(meta), timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"avvio caricamento: {r.status_code} {r.text[:500]}")
    r = requests.put(r.headers["Location"], headers={**h, "Content-Type": "video/mp4"}, data=data, timeout=600)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"caricamento: {r.status_code} {r.text[:500]}")
    return r.json()


def main():
    piano = json.loads(PIANO.read_text())
    adesso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    quanti, solo = int(os.environ.get("QUANTI") or 6), os.environ.get("SOLO", "").strip()
    da_fare = [it for it in piano if not it.get("video_id") and (it["nome"] == solo if solo else True)]
    passati = [it["nome"] for it in da_fare if it["publish_at"] <= adesso]
    if passati:
        print("::warning::Ora di uscita già passata, saltati:", ", ".join(passati))
    da_fare = [it for it in da_fare if it["publish_at"] > adesso][:quanti]
    if not da_fare:
        print("Niente da caricare.")
        return
    tok = token()
    for it in da_fare:
        v = carica(it, tok)
        st = v.get("status", {})
        it["video_id"] = v["id"]
        PIANO.write_text(json.dumps(piano, ensure_ascii=False, indent=1) + "\n")
        print(f"{it['nome']}: https://youtu.be/{v['id']} · uscita {st.get('publishAt')} · {st.get('uploadStatus')}")
        if not st.get("publishAt"):
            print("::error::YouTube non ha accettato l'uscita programmata: probabilmente il video è bloccato "
                  "come privato perché il progetto non ha ancora superato l'audit API. Mi fermo.")
            sys.exit(1)


if __name__ == "__main__":
    main()
