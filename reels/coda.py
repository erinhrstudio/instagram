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
ORA = 18  # si pubblica dalle 18 ora italiana (il workflow gira alle 16:30 e 17:30 UTC)


def prossimo(oggi=None, manuale=False):
    if oggi is None and not manuale:
        adesso = datetime.now(ROMA)
        if adesso.hour < ORA:
            return None, f"sono le {adesso:%H:%M} in Italia, si pubblica dalle {ORA}"
        oggi = adesso.date()
    oggi = oggi or datetime.now(ROMA).date()
    if formato(oggi) == "reel" and not manuale:
        # l'API pubblica i Reel senza musica: nei giorni Reel il video lo pubblica Giuseppe dall'app
        return None, "giorno Reel: lo pubblica Giuseppe dall'app (python -m reels.coda --manuale)"
    coda = json.loads(CODA.read_text())
    if coda.get("pausa"):
        return None, "coda in pausa (\"pausa\": true in state/coda.json)"
    state = json.loads(STATE.read_text()) if STATE.exists() else []
    fatti = {s["id"]: date.fromisoformat(s["published_at"][:10]) for s in state}
    if oggi < date.fromisoformat(coda["inizio"]):
        return None, "la coda parte il " + coda["inizio"]
    date_coda = [fatti[f"post:{n}"] for n in coda["post"] if f"post:{n}" in fatti]
    if date_coda and oggi - max(date_coda) < timedelta(days=coda["ogni_giorni"]):
        return None, f"ultimo post della coda il {max(date_coda)}"
    for n in coda["post"]:
        if f"post:{n}" not in fatti:
            return n, "da pubblicare oggi"
    return None, "coda finita: aggiungi altri post in state/coda.json"


def formato(oggi=None):
    """Dal giorno "reel_da" si alterna: un giorno Reel, il giorno dopo carosello."""
    coda = json.loads(CODA.read_text())
    if not coda.get("reel_da"):
        return "carosello"
    oggi = oggi or datetime.now(ROMA).date()
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
