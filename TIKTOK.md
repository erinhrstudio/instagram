# TikTok: come collegare ERIN (bozze automatiche)

**Cosa otteniamo.** Ogni video pronto viene caricato da solo nelle **bozze** del tuo TikTok. Tu apri l'app, aggiungi un suono di tendenza e premi Pubblica.

**Perché le bozze.** Con l'API di TikTok, finché l'app non supera la loro revisione i post diretti escono **solo privati**. Il caricamento in bozza invece non ha questo limite.

## 1. Pagine che TikTok chiede (le ho già preparate)
Nel repo ci sono tre pagine in `docs/`. Le rendi pubbliche così:
GitHub → erinhrstudio/instagram → **Settings → Pages** → Source: *Deploy from a branch* → Branch **main**, cartella **/docs** → Save.

Dopo un paio di minuti saranno online:
- Privacy: https://erinhrstudio.github.io/instagram/privacy.html
- Termini: https://erinhrstudio.github.io/instagram/terms.html
- Indirizzo di ritorno (redirect): https://erinhrstudio.github.io/instagram/tiktok.html

## 2. App sviluppatore TikTok (gratis, circa 10 minuti)
1. Vai su **developers.tiktok.com** ed entra con l'account TikTok di ERIN.
2. Apri **Manage apps** e crea una nuova app.
   - Nome: *ERIN Uploader*
   - Categoria: *Video / Entertainment*
   - Descrizione: "Carica nelle bozze i video del mio profilo"
   - Icona: il logo del corvo
3. Incolla i link di Privacy e Termini del punto 1.
4. Aggiungi i prodotti **Login Kit** e **Content Posting API**.
   - In Login Kit, come Redirect URI metti l'indirizzo `tiktok.html` del punto 1.
   - In Content Posting API attiva lo scope **video.upload**. *Non* serve "Direct Post".
5. Mandala in revisione (*Submit for review*). Nel frattempo puoi usare la modalità **Sandbox**: aggiungi il tuo account TikTok come *target user* e il collegamento funziona già.
6. Copia **Client key** e **Client secret** e mettili nei secrets del repo GitHub (Settings → Secrets and variables → Actions):
   - `TIKTOK_CLIENT_KEY`
   - `TIKTOK_CLIENT_SECRET`

   **Non incollarli in chat.**

## 3. Collegamento (lo preparo io quando hai finito il punto 2)
Avvii il workflow «TikTok: collega account», apri il link che ti dà e autorizzi. Il codice che compare sulla pagina lo incolli nel workflow. Da lì in poi i video vanno nelle bozze da soli.

## Cosa mandiamo su TikTok
Solo video verticali: gli esperimenti di psicoacustica (basso fantasma, SA o FA, mix più forte, parlato → canto) e il Diario di un fuzz.

Per TikTok li adattiamo così:
- domanda a schermo dal primo secondo
- 15-25 secondi
- testi al centro, perché bordi e lato destro sono coperti dai pulsanti
- risposta alla fine, così lo riguardano
- suono di tendenza aggiunto da te in app
