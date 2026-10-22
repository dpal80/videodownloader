# Grabby Video Downloader — dossier per la revisione legale

Documento preparato per l'avvocato che deve valutare la pubblicazione online di
Grabby. Riassume cosa fa il servizio, quali dati raccoglie, quali testi vanno
rivisti e le domande aperte. **Grabby non verrà pubblicato prima di questa
revisione.**

Bozza del 22 ottobre 2026.

## 1. Che cos'è Grabby

Una pagina web che, dato il link di un video pubblico di **YouTube** o
**Facebook**, ne scarica una copia (video MP4/WebM o solo audio MP3/M4A) usando
il software open source [yt-dlp](https://github.com/yt-dlp/yt-dlp) e
[ffmpeg](https://ffmpeg.org/).

Esiste in due modalità:

| | Locale (oggi) | Online (da valutare) |
| --- | --- | --- |
| Dove gira | Sul computer dell'utente | Su un server del titolare |
| Chi fa la copia | Il computer dell'utente | **Il server del titolare** |
| Dove finisce il file | Cartella Download dell'utente | Consegnato al browser, poi cancellato dal server (al più tardi dopo 1 ora) |
| Dati raccolti | Registro locale sul computer | Registro sul server (vedi §3) |

Il passaggio a online è il punto centrale: il titolare diventa il gestore del
servizio che materialmente effettua la copia.

## 2. Il percorso dell'utente online

1. Incolla il link e, facoltativamente, preme **Analizza** per vedere titolo e
   anteprima.
2. Sceglie formato e risoluzione e preme **Scarica**.
3. Compare un **avviso**: l'uso dei file scaricati è consentito solo nei casi
   indicati in verde nelle note legali; chi continua si assume la piena
   responsabilità legale. L'utente deve spuntare la casella "Dichiaro che il
   video rientra nei casi consentiti e mi assumo la piena responsabilità del
   suo utilizzo" (dalla versione v3 non si chiede più il nome). Pulsanti:
   *Annulla* / *Continua e scarica*.
4. Il server scarica il video, lo consegna al browser e lo cancella.
5. Ogni passaggio (richiesta, completamento o errore) finisce nel registro.

Limiti anti-abuso: 10 download all'ora per IP (configurabile), massimo 2
contemporanei, 60 analisi all'ora.

## 3. Dati personali raccolti

Registro CSV sul server, una riga per evento (richiesto / completato / errore):

| Campo | Note |
| --- | --- |
| data_ora | con fuso orario |
| ip, porta | IP reale dell'utente e porta di origine (letti dietro il proxy HTTPS). Con IP, porta e ora il provider può risalire all'abbonato anche con IP condivisi (CGNAT) |
| paese, citta, provider | stimati dall'IP con i database DB-IP installati sul server, nessun invio a terzi |
| browser | user-agent |
| lingua | lingua della pagina e del browser |
| provenienza | pagina da cui l'utente è arrivato (referrer) |
| dichiarazione | versione del testo accettato con la casella (oggi v3) |
| link, titolo, formato, risoluzione | il contenuto richiesto |
| esito, file, errore | come è andata; "bloccato" se il link era stato segnalato |

Dalla v3 il **nome non viene più chiesto**: non era verificabile e quindi
difficile da giustificare come dato necessario. Si registrano solo dati che il
browser invia da solo; niente lettura di informazioni dal dispositivo con
JavaScript, quindi nessun banner di consenso.

- Nessun cookie di profilazione, nessun fingerprinting, nessuna registrazione.
- Il proxy HTTPS (Caddy) non tiene log degli accessi.
- Le righe più vecchie di **30 giorni** (configurabile con `GRABBY_CONSERVAZIONE_GIORNI`) si cancellano in automatico
  (`GRABBY_CONSERVAZIONE_GIORNI`).
- Base giuridica ipotizzata: **legittimo interesse** (art. 6.1.f GDPR) per la
  tutela in caso di contestazioni e per la sicurezza del servizio.

## 3-bis. Procedura di segnalazione e rimozione

Pagina `/segnalazioni`: i titolari dei diritti segnalano un link via e-mail; il
link viene aggiunto all'elenco dei contenuti bloccati e da quel momento Grabby
rifiuta di analizzarlo o scaricarlo (risposta HTTP 451) e annota ogni tentativo
nel registro. Da completare: indirizzo e-mail e tempi di risposta.

## 4. Testi da rivedere

| Testo | Dove si trova |
| --- | --- |
| Avviso / dichiarazione di responsabilità | `registro.py`, costante `DICHIARAZIONE` (mostrato al clic su Scarica) |
| Note legali "Grabby e il diritto d'autore" | `static/note-legali.html`, pagina `/note-legali` |
| Informativa privacy (bozza con campi `[DA COMPLETARE]`) | `static/privacy.html`, pagina `/privacy` |
| Procedura di segnalazione (bozza) | `static/segnalazioni.html`, pagina `/segnalazioni` |

## 5. Rischi già individuati

Approfonditi, con le fonti, nella pagina `/note-legali`.

- **Termini di YouTube e di Meta**: vietano il download fuori dalle funzioni
  ufficiali e la raccolta automatizzata. Conseguenze possibili: blocco degli IP
  del server, diffide, segnalazioni al provider.
- **Legge sul diritto d'autore (L. 633/1941)**: la copia privata (art.
  71-sexies) ha limiti stretti; la riproduzione e la diffusione non autorizzate
  sono illecite (art. 171 e seguenti, 174-ter per l'utente finale).
- **Responsabilità del gestore**: in Germania (OLG Amburgo, 2024, caso
  Uberspace) un provider che ospitava il sito di youtube-dl è stato ritenuto
  responsabile per l'elusione di misure tecniche di protezione. Un servizio
  online che fa la copia sul proprio server è esposto più di un'app locale.
- **Efficacia della dichiarazione**: documenta la consapevolezza dell'utente, ma
  non è chiaro quanto sposti la responsabilità verso il gestore.

## 6. Domande per l'avvocato

1. Il servizio online è compatibile con la legge italiana ed europea? A quali
   condizioni (es. solo contenuti propri o con licenza libera)?
2. Il testo della dichiarazione è adeguato? Va cambiato il meccanismo (es.
   casella da spuntare, accettazione dei termini d'uso)?
3. Servono **Termini d'uso** veri e propri? Chi li redige?
4. Il legittimo interesse regge come base giuridica per IP, porta, paese,
   città e provider? 30 giorni di conservazione sono proporzionati?
5. Va fatta una valutazione d'impatto (DPIA) o basta il bilanciamento del
   legittimo interesse?
6. Serve un registro dei trattamenti (art. 30 GDPR) e una nomina del provider
   come responsabile (art. 28)?
7. La procedura di segnalazione e blocco (§3-bis, pagina `/segnalazioni`) è
   adeguata? Quali tempi di risposta indicare?
8. Ci sono rischi nel fatto che yt-dlp aggiri le protezioni tecniche di
   YouTube (art. 102-quater e 171-ter L. 633/1941)?

## 7. Da completare prima della pubblicazione

- [ ] Dati del titolare e contatto privacy in `static/privacy.html`
- [ ] Provider e paese dei server
- [ ] Revisione e approvazione dei tre testi del §4
- [ ] Termini d'uso, se richiesti
- [ ] Dominio e certificato HTTPS (`deploy/`, vedi README)
