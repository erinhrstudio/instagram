"""Carica un video nelle bozze (inbox) di TikTok: poi da app si aggiunge il suono e si pubblica.

Il collegamento è in state/tiktok.enc, cifrato con TIKTOK_CLIENT_SECRET(_SANDBOX).
TikTok può restituire un refresh token nuovo: in quel caso il file viene riscritto.

Uso (su GitHub Actions): python -m tools.tiktok_bozza media/tiktok/basso-fantasma.mp4,billie-eilish,...
Un .mp4 viene caricato come video; un nome di posts/ come carosello di foto, letto da GitHub Pages
(docs/tt/<nome>/), perché TikTok scarica le foto solo da un dominio verificato.
Quello che è già stato mandato è in state/tiktok_sent.json e viene saltato.
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


PAGES = "https://erinhrstudio.github.io/instagram/tt"
SENT = ROOT / "state" / "tiktok_sent.json"


class TroppiInSospeso(Exception):
    pass


def _check(r, cosa):
    err = r.get("error", {})
    if err.get("code") == "ok":
        return r["data"]
    if "pending" in err.get("code", "") or "spam_risk" in err.get("code", ""):
        raise TroppiInSospeso(err.get("message", ""))
    sys.exit(f"TikTok ha rifiutato {cosa}: {err}")


def _wait(h, pid):
    for _ in range(30):
        time.sleep(5)
        st = requests.post(f"{API}/post/publish/status/fetch/", headers=h, json={"publish_id": pid}, timeout=30).json()
        s = st.get("data", {}).get("status")
        print("  stato:", s)
        if s in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return
        if s == "FAILED":
            sys.exit(f"TikTok non ha accettato il contenuto: {st['data'].get('fail_reason')}")
    print("  TikTok sta ancora elaborando: arriverà tra qualche minuto.")


def photos(h, name):
    from reels.captions import with_brand_tags
    spec = json.loads((ROOT / "posts" / name / "spec.json").read_text())
    imgs = sorted((ROOT / "docs" / "tt" / name).glob("*.jpg"))
    if not imgs:
        sys.exit(f"Nessuna foto in docs/tt/{name}")
    cap = with_brand_tags(spec["caption"])
    title = cap.split("\n")[0][:89]
    r = requests.post(f"{API}/post/publish/content/init/", headers=h, timeout=30, json={
        "post_info": {"title": title, "description": cap[:3900]},
        "source_info": {"source": "PULL_FROM_URL", "photo_cover_index": 0,
                        "photo_images": [f"{PAGES}/{name}/{p.name}" for p in imgs]},
        "post_mode": "MEDIA_UPLOAD", "media_type": "PHOTO"}).json()
    _wait(h, _check(r, f"le foto di {name}")["publish_id"])


def upload(path, tok=None):
    tok = tok or access_token()
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    data = Path(path).read_bytes()
    n = len(data)
    init = requests.post(f"{API}/post/publish/inbox/video/init/", headers=h, timeout=30, json={
        "source_info": {"source": "FILE_UPLOAD", "video_size": n, "chunk_size": n, "total_chunk_count": 1}}).json()
    d = _check(init, path)
    pid, url = d["publish_id"], d["upload_url"]
    up = requests.put(url, data=data, timeout=300, headers={
        "Content-Type": "video/mp4", "Content-Length": str(n), "Content-Range": f"bytes 0-{n - 1}/{n}"})
    if up.status_code not in (200, 201):
        sys.exit(f"Invio del file fallito: HTTP {up.status_code} {up.text[:300]}")
    _wait(h, pid)


def main(items):
    sent = json.loads(SENT.read_text()) if SENT.exists() else []
    tok = access_token()
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    for it in [i.strip() for i in items.split(",") if i.strip()]:
        if it in sent:
            print(f"{it}: già mandato, salto")
            continue
        print(f"{it}: invio…")
        try:
            upload(it, tok) if it.endswith(".mp4") else photos(h, it)
        except TroppiInSospeso as e:
            print(f"::warning::TikTok non accetta altre bozze finché non pubblichi quelle in sospeso ({e}). Mi fermo prima di {it}.")
            break
        sent.append(it)
        SENT.write_text(json.dumps(sent, indent=1))
        print(f"{it}: nelle bozze")


if __name__ == "__main__":
    main(sys.argv[1])
