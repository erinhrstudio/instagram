"""Carica un video nelle bozze (inbox) di TikTok: poi da app si aggiunge il suono e si pubblica.

Il collegamento è in state/tiktok.enc, cifrato con TIKTOK_CLIENT_SECRET(_SANDBOX).
TikTok può restituire un refresh token nuovo: in quel caso il file viene riscritto.

Uso (su GitHub Actions): python -m tools.tiktok_bozza media/tiktok/basso-fantasma.mp4
"""
import json, os, subprocess, sys, time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENC = ROOT / "state" / "tiktok.enc"
API = "https://open.tiktokapis.com/v2"


def _openssl(args, data):
    return subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", *args, "-pass", "env:CLIENT_SECRET"],
                          input=data, capture_output=True, check=True).stdout


def access_token():
    saved = json.loads(_openssl(["-d"], ENC.read_bytes()))
    r = requests.post(f"{API}/oauth/token/", data={
        "client_key": os.environ["CLIENT_KEY"], "client_secret": os.environ["CLIENT_SECRET"],
        "grant_type": "refresh_token", "refresh_token": saved["refresh_token"]}, timeout=30).json()
    if not r.get("access_token"):
        sys.exit(f"Rinnovo del collegamento fallito: {r.get('error')} {r.get('error_description', '')}")
    print(f"::add-mask::{r['access_token']}")
    if r.get("refresh_token") and r["refresh_token"] != saved["refresh_token"]:
        saved["refresh_token"] = r["refresh_token"]
        ENC.write_bytes(_openssl(["-salt"], json.dumps(saved).encode()))
        print("Collegamento rinnovato: state/tiktok.enc aggiornato.")
    return r["access_token"]


def upload(path):
    tok = access_token()
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    data = Path(path).read_bytes()
    n = len(data)
    init = requests.post(f"{API}/post/publish/inbox/video/init/", headers=h, timeout=30, json={
        "source_info": {"source": "FILE_UPLOAD", "video_size": n, "chunk_size": n, "total_chunk_count": 1}}).json()
    if init.get("error", {}).get("code") != "ok":
        sys.exit(f"TikTok ha rifiutato il caricamento: {init.get('error')}")
    pid, url = init["data"]["publish_id"], init["data"]["upload_url"]
    up = requests.put(url, data=data, timeout=300, headers={
        "Content-Type": "video/mp4", "Content-Length": str(n), "Content-Range": f"bytes 0-{n - 1}/{n}"})
    if up.status_code not in (200, 201):
        sys.exit(f"Invio del file fallito: HTTP {up.status_code} {up.text[:300]}")
    for _ in range(30):
        time.sleep(5)
        st = requests.post(f"{API}/post/publish/status/fetch/", headers=h, json={"publish_id": pid}, timeout=30).json()
        s = st.get("data", {}).get("status")
        print("stato:", s)
        if s == "SEND_TO_USER_INBOX" or s == "PUBLISH_COMPLETE":
            print("Video nelle bozze di TikTok: apri l'app, notifiche in alto, e completa il post.")
            return
        if s == "FAILED":
            sys.exit(f"TikTok non ha accettato il video: {st['data'].get('fail_reason')}")
    print("TikTok sta ancora elaborando il video: controlla le notifiche dell'app tra qualche minuto.")


if __name__ == "__main__":
    upload(sys.argv[1])
