# ERIN Audio Fact #01–#25 · revisione scientifica (22/10/2026)

**Esito complessivo.** Le 25 affermazioni di base sono corrette: nessuna è falsa. I problemi sono di altro tipo:
- 3 errori veri (#13 norma superata, #22 numero sbagliato, #25 misura non trovata);
- 4 esperimenti A/B che così non funzionano o ingannano (#1, #7, #19, #22);
- fonti vaghe o "da verificare" in 9 schede: ora tutte hanno citazioni precise;
- testi molto prudenti ("dipende da…" ripetuto ovunque): giusti ma poco agganciati. Per ognuno propongo un titolo-gancio (la domanda per la copertina).

Legenda: ✅ ok com'è · ✏️ corretto o precisato · ❌ errore corretto.

---

## #01 · Psicoacustica · ✏️
**Gancio:** Perché dopo un po' l'eco "sparisce"?
**Testo IT:** Senti un suono e la sua eco, ripetuti più volte di fila: dopo qualche ripetizione l'eco si sente meno. È l'accumulo della soppressione dell'eco (build-up dell'effetto precedenza). Se cambi improvvisamente la situazione, per esempio scambi da quale lato arriva l'eco, l'eco torna a sentirsi.
**Cosa ho cambiato:** il fenomeno è stato misurato con *coppie suono + eco* ripetute (treni di click), non con un suono singolo. Nella bozza mancava che servono entrambe, originale e ritardo, nelle ripetizioni (con il solo originale l'effetto non c'è).
**A/B (due casse, non cuffie):** click nella cassa sinistra, la stessa copia ritardata di 8–15 ms nella destra. A: una sola coppia. B: la stessa coppia ripetuta 10–15 volte, 4 al secondo. Ascolta se l'eco a destra si affievolisce lungo la sequenza.
**Fonti:** Freyman, Clifton & Litovsky (1991), "Dynamic processes in the precedence effect", JASA 90(2), 874–884 · Brown, Stecker & Tollin (2015), "The precedence effect in sound localization", JARO 16, 1–28.

## #02 · Recording · ✅
**Gancio:** Il tuo cardioide è cardioide solo a metà?
Il diagramma polare cambia con la frequenza: fuori asse il suono non è solo più basso ma anche più scuro o colorato. Va bene così; aggiungerei solo che di solito agli acuti il microfono diventa più direttivo.
**Fonti:** DPA Mic University, "How to read microphone specifications / polar patterns" · IEC 60268-4 (misure sui microfoni).

## #03 · Mixing/Mastering · ✏️
**Gancio:** 0 dBFS sul meter, clip nel lettore?
Corretto. Aggiunto il dato pratico: EBU R 128 indica un massimo di **−1 dBTP**; per questo si lascia margine anche se i campioni non toccano 0.
**Fonti:** ITU-R BS.1770 (Annex 2, true peak) · EBU R 128.

## #04 · Psicoacustica · ✏️
**Gancio:** Il cervello "ricuce" i buchi nel suono?
Corretto. Aggiunta la condizione chiave: funziona se il rumore è abbastanza forte e copre le frequenze del suono mancante. Esempio classico di Warren: in una frase, un colpo di tosse al posto di una /s/ e nessuno si accorge che la /s/ manca.
**Fonti:** Warren (1970), "Perceptual restoration of missing speech sounds", Science 167, 392–393 · Warren, Obusek & Ackroff (1972), "Auditory induction: perceptual synthesis of absent sounds", Science 176, 1149–1151.

## #05 · Recording · ✏️
**Gancio:** Metà distanza, metà stanza?
Corretto (legge dell'inverso del quadrato, −6 dB per ogni raddoppio di distanza in campo libero). Precisato: in una stanza il campo riverberato resta circa uguale, quindi avvicinandoti a metà il diretto sale di circa 6 dB e il rapporto diretto/stanza migliora di circa altrettanto, finché sei dentro il raggio critico.
**Fonti:** Shure, "Microphone techniques for recording" · Everest & Pohlmann, Master Handbook of Acoustics.

## #06 · Mixing · ✏️
**Gancio:** Il tuo EQ "suona" prima della nota?
Corretto. Aggiunto il caso più interessante: gli EQ a fase lineare spostano il ringing anche *prima* del transiente (pre-ringing), e un taglio molto ripido lo allunga.
**Fonti:** J. O. Smith, "Introduction to Digital Filters" (CCRMA) · R. Lyons, Understanding Digital Signal Processing.

## #07 · Psicoacustica · ❌ (esperimento)
**Gancio:** Senti un basso che non c'è?
Il fenomeno è corretto (180-240-300-360 Hz fanno sentire 60 Hz). Problema nell'esperimento: piccoli speaker e volumi alti generano distorsione che **crea davvero** un po' di 60 Hz, e il test non dimostra più niente. Correzione: volume moderato, e controlla con un analizzatore che a 60 Hz non ci sia energia.
**Fonti:** Schouten (1940) sul "residue pitch" · Moore, An Introduction to the Psychology of Hearing (cap. sull'altezza).

## #08 · Recording · ✏️
**Gancio:** Il microfono sul pavimento suona meglio?
Corretto. Spiegato il perché: con la capsula a filo della superficie, suono diretto e riflesso arrivano in fase, quindi niente cancellazioni a pettine da quella superficie e circa +6 dB di sensibilità.
**Fonti:** Crown, "Boundary Microphone Application Guide" · Shure, note tecniche sui microfoni boundary.

## #09 · Mixing · ✏️
**Gancio:** Saturare il bus o le tracce: è uguale?
Corretto. Reso concreto: con due toni (es. 200 e 310 Hz) saturati separatamente ottieni solo le loro armoniche; saturati insieme compaiono anche le somme e differenze (110, 510 Hz…): l'intermodulazione. Si vede bene con l'analizzatore.
**Fonti:** qualsiasi testo di sistemi non lineari; manuale del saturatore usato.

## #10 · Psicoacustica · ✏️
**Gancio:** Un suono può cancellare quello prima?
Corretto. Aggiunto: il mascheramento all'indietro è breve (circa 20 ms) e debole rispetto a quello in avanti, e si riduce molto con l'allenamento.
**Fonti:** Moore, An Introduction to the Psychology of Hearing (cap. mascheramento) · Oxenham & Moore (1994), Hearing Research 80, 105–118.

## #11 · Recording · ✅
**Gancio:** Il 32-bit float salva tutto?
Corretto e ben spiegato.
**Fonti:** Sound Devices, note su 32-bit float · manuale del registratore.

## #12 · Mixing · ✏️
**Gancio:** Il compressore distorce il tuo basso?
Corretto. Reso concreto: un'onda a 40 Hz dura 25 ms; se il release è più corto, il compressore segue la forma d'onda invece del volume e la distorce.
**Fonti:** FabFilter Pro-C, manuale (compression) · Giannoulis, Massberg & Reiss (2012), "Digital dynamic range compressor design", JAES 60(6).

## #13 · Psicoacustica · ❌ (fonte)
**Gancio:** Abbassa il volume: dov'è finito il basso?
Il link era alla ISO 226:2003, **sostituita dalla ISO 226:2023**. Precisato: a basso volume si perdono soprattutto i bassi; gli acuti molto meno.
**Fonti:** ISO 226:2023 · Suzuki & Takeshima (2004), JASA 116, 918 (base dei dati ISO).

## #14 · Recording · ✏️
**Gancio:** Inverti la fase e hai risolto?
Corretto. Aggiunto un numero utile: il suono fa circa 34 cm per millisecondo, quindi 1 m di differenza tra due microfoni è circa 2,9 ms di ritardo.
**Fonti:** Shure, "Phase cancellation and microphone placement".

## #15 · Mixing · ✅
**Gancio:** Stesso EQ piatto, picchi diversi?
Corretto.
**Fonti:** J. O. Smith, "Introduction to Digital Filters" (all-pass).

## #16 · Psicoacustica · ✏️
**Gancio:** Il tuo mix è scuro o è la reference?
Corretto, mancavano le fonti: è l'effetto di contrasto spettrale, studiato da decenni. Dopo un contesto più brillante, lo stesso suono viene percepito più scuro.
**Fonti:** Ladefoged & Broadbent (1957), JASA 29, 98–104 · Stilp, Alexander, Kiefte & Kluender (2010), Attention, Perception & Psychophysics 72, 470–480 (anche su strumenti musicali).

## #17 · Recording · ✅
**Gancio:** Picchi bassi, microfono già saturo?
Corretto.
**Fonti:** manuale del microfono (max SPL, posizione del pad).

## #18 · Mixing · ✅
**Gancio:** Il compressore sposta la tua voce?
Corretto; i parametri dell'esperimento vanno bene.
**Fonti:** FabFilter Pro-C, manuale (stereo linking).

## #19 · Psicoacustica · ✏️ (esperimento)
**Gancio:** Inverti la fase e il tono esce dal rumore?
Corretto. Nell'esperimento mancava la frequenza: l'effetto è grande solo sulle basse. Usa un tono a **500 Hz**: invertendolo in un solo canale diventa udibile fino a circa 12–15 dB più piano.
**Fonti:** Hirsh (1948), "The influence of interaural phase on interaural summation and inhibition", JASA 20, 536–544 · Moore, An Introduction to the Psychology of Hearing (cap. udito binaurale).

## #20 · Recording · ✅
**Gancio:** Il vento ti satura prima che tu lo senta?
Corretto.
**Fonti:** DPA, guida al rumore del vento · Shure, protezioni antivento.

## #21 · Mixing · ✏️
**Gancio:** Il crossfade che alza il volume?
Corretto. Aggiunto il numero: con due copie identiche l'equal-power dà circa **+3 dB** a metà dissolvenza.
**Fonti:** REAPER User Guide (fade shapes).

## #22 · Psicoacustica · ❌ (numero)
**Gancio:** Quando un'armonica diventa un altro strumento?
Il principio è corretto, il numero no: **pochi millisecondi di anticipo non bastano**. Per sentire separata un'armonica servono alcune decine di millisecondi; per toglierla dal calcolo dell'altezza oltre 100 ms. Esperimento corretto: anticipa una sola armonica di 30, 60 e 120 ms e confronta.
**Fonti:** Bregman, Auditory Scene Analysis (1990) · Darwin & Hill (1993), atti ASA, sul "few tens of ms" contro "over 100 ms".

## #23 · Recording · ✅
**Gancio:** Il cavo cambia il suono della chitarra?
Corretto: la capacità del cavo abbassa la risonanza del pickup e scurisce il suono; un buffer vicino alla chitarra la rende quasi indipendente dal cavo.
**Fonti:** documentazione tecnica di pickup e cavi; misure del costruttore.

## #24 · Mixing · ✅
**Gancio:** Il kick comanda il tuo compressore?
Corretto.
**Fonti:** FabFilter Pro-C, manuale (side-chain).

## #25 · Recording · ❌ (misura)
Già rivista: vedi 25-effetto-prossimita.md. Tolta la misura DPA "Genelec da 64 a 1 cm", che non risulta in nessuna fonte.

---

## Proposta editoriale
- **Formato:** carosello di 5-6 slide (gancio, cosa succede, perché, A/B, nota onesta, CTA "salvalo"), italiano nelle slide e inglese in didascalia. Le schede di psicoacustica con l'A/B in audio (#01, #04, #07, #19, #22) rendono di più come Reel con il suono vero.
- **Ordine consigliato per partire:** #07 basso che non c'è (Reel), #14 inverti la fase, #13 abbassa il volume, #03 true peak, #04 cervello che ricuce, #25 prossimità.
