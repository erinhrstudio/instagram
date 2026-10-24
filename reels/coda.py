"""Coda dei caroselli: sceglie il prossimo post da pubblicare oggi.

state/coda.json contiene l'ordine dei post, la data di inizio e ogni quanti giorni pubblicare.
Con "pausa": true non pubblica niente finché non si toglie.
Stampa il nome del post da pubblicare oggi (o niente) e, su GitHub Actions, lo scrive in GITHUB_OUTPUT.

Uso: python -m reels.coda
"""
import json, os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CODA = ROOT / "state" / "coda.json"
STATE = ROOT / "state" / "published.json"


ROMA = ZoneInfo("Europe/Rome")
ORA = 18  # ora di uscita (ora italiana) se coda.json non ha "orari"


def ora_uscita(oggi):
    """Dal 22/10 si alterna: un giorno alle 12, il giorno dopo alle 18 ("orari" in coda.json)."""
    o = json.loads(CODA.read_text()).get("orari")
    if not o or oggi < date.fromisoformat(o["da"]):
        return ORA
    return o["ore"][(oggi - date.fromisoformat(o["da"])).days % len(o["ore"])]


def prossimo(oggi=None, manuale=False):
    if oggi is None and not manuale:
        adesso = datetime.now(ROMA)
        ora = ora_uscita(adesso.date())
        if adesso.hour < ora:
            return None, f"sono le {adesso:%H:%M} in Italia, oggi si pubblica dalle {ora}"
        oggi = adesso.date()
    oggi = oggi or datetime.now(ROMA).date()
    reel_day = formato(oggi) == "reel"
    coda = json.loads(CODA.read_text())
    if coda.get("pausa"):
        return None, "coda in pausa (\"pausa\": true in state/coda.json)"
    if oggi.isoformat() in coda.get("salta", []):
        return None, "giorno saltato apposta (\"salta\" in state/coda.json)"
    state = json.loads(STATE.read_text()) if STATE.exists() else []
    fatti = {s["id"]: date.fromisoformat(s["published_at"][:10]) for s in state}
    if oggi < date.fromisoformat(coda["inizio"]):
        return None, "la coda parte il " + coda["inizio"]
    date_coda = [fatti[f"post:{n}"] for n in coda["post"] if f"post:{n}" in fatti]
    if date_coda and oggi - max(date_coda) < timedelta(days=coda["ogni_giorni"]):
        return None, f"ultimo post della coda il {max(date_coda)}"
    for n in coda["post"]:
        if f"post:{n}" not in fatti:
            if coda.get("formato_da_post"):
                if not pronto(n):
                    continue  # post non ancora costruito (es. aspetta la foto): passa al successivo
                reel_day = formato_post(n, coda) == "reel"
            if reel_day:
                # l'API pubblica i Reel senza musica di libreria: se il Reel ha già il suo audio
                # (reel_musica.txt dice NESSUNA) esce in automatico, altrimenti lo pubblica Giuseppe dall'app
                auto = audio_proprio(n)
                if auto and manuale:
                    return None, f"{n} ha il suo audio: esce in automatico all'ora di oggi"
                if not auto and not manuale:
                    return None, f"giorno Reel: {n} lo pubblica Giuseppe dall'app (python -m reels.coda --manuale)"
            return n, "da pubblicare oggi"
    return None, "coda finita: aggiungi altri post in state/coda.json"


def audio_proprio(nome):
    """True se il Reel non vuole musica di libreria: l'audio del video è il contenuto."""
    f = ROOT / "posts" / nome / "reel_musica.txt"
    return f.exists() and f.read_text(encoding="utf-8").strip().upper().startswith("NESSUNA")


def pronto(nome):
    """Il post esiste: slide del carosello o video del Reel."""
    return (ROOT / "posts" / nome / "01.jpg").exists() or (ROOT / "media" / "tiktok" / f"{nome}.mp4").exists() and audio_proprio(nome)


def formato_post(nome, coda):
    """Dal 22/10 il formato lo decide il post: Reel se ha il suo audio o è in "reel_manuali"."""
    return "reel" if audio_proprio(nome) or nome in coda.get("reel_manuali", []) else "carosello"


def formato(oggi=None):
    """Formato di oggi. Con "formato_da_post" è quello del prossimo post pronto;
    altrimenti dal giorno "reel_da" si alterna: un giorno Reel, il giorno dopo carosello."""
    coda = json.loads(CODA.read_text())
    if coda.get("formato_da_post"):
        state = json.loads(STATE.read_text()) if STATE.exists() else []
        fatti = {s["id"] for s in state}
        for n in coda["post"]:
            if f"post:{n}" not in fatti and pronto(n):
                return formato_post(n, coda)
        return "carosello"
    if not coda.get("reel_da"):
        return "carosello"
    oggi = oggi or datetime.now(ROMA).date()
    # giorni carosello trasformati in Reel (dal 19/10: 4 Reel e 3 caroselli a settimana)
    if oggi.isoformat() in coda.get("reel_extra", []):
        return "reel"
    return "reel" if (oggi - date.fromisoformat(coda["reel_da"])).days % 2 == 0 else "carosello"


def segna_manuale():
    """Segna come uscito il Reel di oggi, che Giuseppe pubblica a mano con la musica."""
    nome, motivo = prossimo(manuale=True)
    if not nome:
        print("niente da segnare -", motivo)
        return None
    state = json.loads(STATE.read_text()) if STATE.exists() else []
    state.append({"id": f"post:{nome}", "media_id": None, "formato": "reel-manuale",
                  "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(nome)
    return nome


if __name__ == "__main__":
    import sys
    if "--manuale" in sys.argv:
        segna_manuale()
        sys.exit(0)
    nome, motivo = prossimo()
    fmt = formato()
    print(nome or "nessun post oggi", "-", motivo, "-", fmt)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"name={nome or ''}\nreel={'--reel' if fmt == 'reel' else ''}\n")
