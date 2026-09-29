"""Pubblica un Reel con l'API di Instagram (accesso con Instagram, account Professionale).

Il video viene caricato direttamente (upload "resumable"), senza bisogno di un server pubblico.
Richiede la variabile d'ambiente INSTAGRAM_TOKEN.
"""
import os, time

import requests

API = "https://graph.instagram.com/v23.0"


def _check(r):
    if r.status_code >= 400:
        raise RuntimeError(f"Errore API Instagram {r.status_code}: {r.text}")
    return r.json()


def account(token):
    return _check(requests.get(f"{API}/me", params={"fields": "user_id,username", "access_token": token},
                               timeout=30))


def publish_reel(video_path, caption, token, wait_s=900):
    me = account(token)
    uid = me["user_id"]

    # 1. crea il contenitore del Reel
    c = _check(requests.post(f"{API}/{uid}/media", data={
        "media_type": "REELS", "upload_type": "resumable", "caption": caption,
        "share_to_feed": "true", "access_token": token}, timeout=60))
    cid = c["id"]
    upload_uri = c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/v23.0/{cid}"

    # 2. carica il file video
    size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        _check(requests.post(upload_uri, data=f, timeout=600, headers={
            "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}))

    # 3. aspetta che Instagram finisca di elaborare il video
    deadline = time.time() + wait_s
    while True:
        s = _check(requests.get(f"{API}/{cid}", params={"fields": "status_code,status",
                                                         "access_token": token}, timeout=30))
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED") or time.time() > deadline:
            raise RuntimeError(f"Elaborazione del video fallita: {s}")
        time.sleep(10)

    # 4. pubblica
    p = _check(requests.post(f"{API}/{uid}/media_publish",
                             data={"creation_id": cid, "access_token": token}, timeout=60))
    return {"media_id": p["id"], "username": me.get("username")}


def _wait(cid, token, wait_s):
    deadline = time.time() + wait_s
    while True:
        s = _check(requests.get(f"{API}/{cid}", params={"fields": "status_code,status",
                                                         "access_token": token}, timeout=30))
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") in ("ERROR", "EXPIRED") or time.time() > deadline:
            raise RuntimeError(f"Elaborazione fallita: {s}")
        time.sleep(5)


def _carousel_video(uid, urls, token, wait_s):
    """Video come elemento del carosello. Instagram vuole un URL pubblico (video_url):
    si prova ogni URL della lista finché uno viene accettato."""
    err = None
    for url in urls:
        try:
            c = _check(requests.post(f"{API}/{uid}/media", data={
                "media_type": "VIDEO", "video_url": url, "is_carousel_item": "true",
                "access_token": token}, timeout=60))
            _wait(c["id"], token, wait_s)
            print("  video accettato da", url)
            return c["id"]
        except RuntimeError as e:
            print("  video rifiutato da", url, "->", e)
            err = e
    raise err


def _carousel_image(uid, urls, token, wait_s):
    """Immagine del carosello. Instagram a volte non riesce a scaricare un URL:
    riprova e poi passa all'URL alternativo."""
    err = None
    for url in [u for u in urls for _ in range(2)]:
        try:
            c = _check(requests.post(f"{API}/{uid}/media", data={
                "image_url": url, "is_carousel_item": "true", "access_token": token}, timeout=60))
            _wait(c["id"], token, wait_s)
            return c["id"]
        except RuntimeError as e:
            print("  immagine rifiutata da", url, "->", str(e)[:200])
            err = e
            time.sleep(5)
    raise err


def publish_carousel(items, caption, token, wait_s=300, publish=True):
    """Pubblica un carosello (2-10 elementi). Un elemento è l'URL pubblico di un JPEG
    una lista di URL alternativi dello stesso JPEG,
    oppure {"video": [URL alternativi]} per un video MP4. Con publish=False crea solo i contenitori
    (verifica che Instagram accetti tutto) senza pubblicare nulla."""
    me = account(token)
    uid = me["user_id"]
    children = []
    for item in items:
        if isinstance(item, dict):
            children.append(_carousel_video(uid, item["video"], token, max(wait_s, 600)))
            continue
        children.append(_carousel_image(uid, item if isinstance(item, (list, tuple)) else [item], token, wait_s))
    c = _check(requests.post(f"{API}/{uid}/media", data={
        "media_type": "CAROUSEL", "children": ",".join(children), "caption": caption,
        "access_token": token}, timeout=60))
    _wait(c["id"], token, wait_s)
    if not publish:
        return {"media_id": None, "container_id": c["id"], "username": me.get("username")}
    p = _check(requests.post(f"{API}/{uid}/media_publish",
                             data={"creation_id": c["id"], "access_token": token}, timeout=60))
    return {"media_id": p["id"], "username": me.get("username")}


def refresh_token(token):
    """Rinnova il token (vale 60 giorni). Restituisce il nuovo token."""
    r = _check(requests.get("https://graph.instagram.com/refresh_access_token",
                            params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30))
    return r["access_token"], r.get("expires_in")
