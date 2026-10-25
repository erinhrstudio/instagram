# YouTube: progetto Google nostro

Tempo: circa 15 minuti, dal computer. Nessuna password va scritta in chat: le chiavi vanno solo nei secrets di GitHub.

1. Apri https://console.cloud.google.com, accedi con l'account Google del canale e crea un progetto: **ERIN Shorts**.
2. **API e servizi → Libreria**: cerca **YouTube Data API v3** e premi **Abilita**.
3. **Google Auth Platform → Branding / Schermata di consenso**:
   - nome app **ERIN Shorts**, la tua email come supporto e come contatto sviluppatore;
   - tipo di utenti **Esterno**;
   - in **Pubblico** premi **Pubblica app** (stato "In produzione"). Così il collegamento non scade dopo 7 giorni. Google mostrerà "app non verificata": va bene, la usi solo tu.
4. **Client → Crea client**: tipo **TV e dispositivi con input limitato**, nome "ERIN GitHub". Copia **ID client** e **Client secret**.
5. Su GitHub: repo erinhrstudio/instagram → **Settings → Secrets and variables → Actions → New repository secret**:
   - `YOUTUBE_CLIENT_ID` = l'ID client
   - `YOUTUBE_CLIENT_SECRET` = il client secret
6. Scrivi "fatto" nel thread: lancio "YouTube: collega canale" e ti mando un codice da inserire su https://www.google.com/device (scegli il canale Erinhrstudio).
7. Audit API (sblocca la pubblicazione pubblica): modulo https://support.google.com/youtube/contact/yt_api_form. Le risposte te le preparo io.

Finché l'audit non è approvato, YouTube blocca come privati i video caricati via API: nel frattempo si carica a mano con youtube_pacchetto.md.
