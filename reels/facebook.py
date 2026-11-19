"""Pubblica lo stesso Reel anche sulla Pagina Facebook (API Reels delle Pagine).

È indipendente dall'account Instagram: usa solo FB_PAGE_ID e FB_PAGE_TOKEN
(token della Pagina, senza scadenza, con pages_manage_posts, pages_read_engagement, pages_show_list).
Se mancano, non fa niente. Un errore qui non blocca mai Instagram.
"""
import os, time

import requests

API = "https://graph.facebook.com/v23.0"


def _check(r):
    if r.status_code >= 400:
        raise RuntimeError(f"Errore API Facebook {r.status_code}: {r.text}")
    return r.json()


def configured():
    return bool(os.environ.get("FB_PAGE_ID") and os.environ.get("FB_PAGE_TOKEN"))


def check_page():
    """Verifica token e Pagina senza pubblicare niente."""
    pid, tok = os.environ["FB_PAGE_ID"], os.environ["FB_PAGE_TOKEN"]
    return _check(requests.get(f"{API}/{pid}", params={"fields": "id,name", "access_token": tok}, timeout=30))


def publish_reel(urls, description, wait_s=600):
    """Carica il video da un URL pubblico e lo pubblica come Reel della Pagina.
    Restituisce l'id del video su Facebook."""
    pid, tok = os.environ["FB_PAGE_ID"], os.environ["FB_PAGE_TOKEN"]
    err = None
    for url in urls:
        try:
            s = _check(requests.post(f"{API}/{pid}/video_reels",
                                     data={"upload_phase": "start", "access_token": tok}, timeout=60))
            vid = s["video_id"]
            _check(requests.post(s.get("upload_url") or f"https://rupload.facebook.com/video-upload/v23.0/{vid}",
                                 headers={"Authorization": f"OAuth {tok}", "file_url": url}, timeout=300))
            break
        except RuntimeError as e:
            print("  Facebook: video rifiutato da", url, "->", str(e)[:300])
            err = e
    else:
        raise err
    _check(requests.post(f"{API}/{pid}/video_reels", data={
        "upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
        "description": description, "access_token": tok}, timeout=60))
    deadline = time.time() + wait_s
    while time.time() < deadline:
        st = _check(requests.get(f"{API}/{vid}", params={"fields": "status", "access_token": tok}, timeout=30))
        status = st.get("status", {})
        if status.get("video_status") == "ready" or status.get("publishing_phase", {}).get("status") == "complete":
            break
        if status.get("video_status") == "error":
            raise RuntimeError(f"Facebook: elaborazione fallita: {status}")
        time.sleep(10)
    return vid
