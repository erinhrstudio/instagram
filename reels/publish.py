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


def publish_carousel(image_urls, caption, token, wait_s=300):
    """Pubblica un carosello (2-10 immagini JPEG). Le immagini devono avere un URL pubblico."""
    me = account(token)
    uid = me["user_id"]
    children = []
    for url in image_urls:
        c = _check(requests.post(f"{API}/{uid}/media", data={
            "image_url": url, "is_carousel_item": "true", "access_token": token}, timeout=60))
        _wait(c["id"], token, wait_s)
        children.append(c["id"])
    c = _check(requests.post(f"{API}/{uid}/media", data={
        "media_type": "CAROUSEL", "children": ",".join(children), "caption": caption,
        "access_token": token}, timeout=60))
    _wait(c["id"], token, wait_s)
    p = _check(requests.post(f"{API}/{uid}/media_publish",
                             data={"creation_id": c["id"], "access_token": token}, timeout=60))
    return {"media_id": p["id"], "username": me.get("username")}


def refresh_token(token):
    """Rinnova il token (vale 60 giorni). Restituisce il nuovo token."""
    r = _check(requests.get("https://graph.instagram.com/refresh_access_token",
                            params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30))
    return r["access_token"], r.get("expires_in")
