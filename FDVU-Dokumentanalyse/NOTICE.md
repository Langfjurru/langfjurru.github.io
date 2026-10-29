# NOTICE – FDVU Dokumentanalyse 2.4

**Oppdatert:** 29. oktober 2026  
**Status:** Offentlig test-/utviklingsversjon. Rettighetshaver, publiseringstillatelse og lisens for viderebruk er ikke endelig avklart.

## Hva verktøyet gjør

FDVU Dokumentanalyse er et nettleserbasert hjelpemiddel som leser PDF- og DOCX-dokumenter og foreslår dokumenttype, teknisk system, relevante dokumentkrav og standardiserte filnavn. Det benytter regelbasert analyse og innebygde koder og kravdata. Funksjonaliteten utvikles og endres fortsatt.

## Rettighets- og lisensstatus

Det er per dato **ikke gitt noen åpen kildekodelisens** til FDVU Dokumentanalyse. Filen `LICENSE` inneholder kun en midlertidig rettighetserklæring. EUPL-1.2 er vurdert som et mulig framtidig alternativ, men er **ikke** innført.

NTNU kan være rettighetshaver til programvaren som er utviklet i forbindelse med arbeidet; dette og hvem som kan godkjenne offentlig publisering må bekreftes. At verktøyet allerede er tilgjengelig på GitHub Pages, er ikke i seg selv dokumentasjon på slik godkjenning.

Kildehenvisninger og rettighetsforbehold for Statsbygg, NTNU, Standard Norge og andre finnes i `SOURCES.md`. Løsningen inneholder omfattende innebygde registre; rettighetene til disse er ikke endelig avklart.

## Lokal dokumentbehandling og sikkerhet

Programmet er **utformet for å analysere dokumenter lokalt i brukerens nettleser**, uten opplasting til en ekstern dokumentanalysetjeneste. Kildekoden inneholder begrensninger på flere typer utgående kommunikasjon og funksjonalitet for å tømme arbeidsøkten.

Det kan imidlertid gjøres nettverksforespørsler for å hente eksterne programbiblioteker og OCR-språkdata. En fullstendig dynamisk nettverks- og sikkerhetsrevisjon er ikke dokumentert. Det gis derfor ingen ubetinget garanti for at all mulig dataoverføring er teknisk utelukket. Ikke bruk fortrolig, sikkerhetsgradert eller annen beskyttet dokumentasjon uten nødvendig intern godkjenning og sikkerhetsvurdering.

## Faglig forbehold

Automatisk klassifisering, systemkode, dokumentkrav, dato og filnavn kan være feil eller ufullstendige. Alle forslag må kontrolleres av brukeren mot originaldokumentene og de gjeldende kravene for prosjektet. «Godkjent» i verktøyet betyr at brukeren har markert et resultat som gjennomgått, **ikke** at et dokument er formelt FDVU-godkjent.

Verktøyet er ingen offisiell tjeneste, standardtolkning eller godkjenning fra Statsbygg eller Standard Norge. Det er heller ikke dokumentert som en formelt godkjent NTNU-tjeneste.

## Ansvarsbegrensning

Verktøyet tilbys for utprøving og faglig vurdering uten løfte om feilfri klassifisering eller egnethet for et bestemt formål. Dette avsnittet endrer ikke ansvar som følger av ufravikelig lovgivning eller rettigheter etter andre bindende avtaler.

## Før en åpen lisens eller bred lansering

- Avklar publiseringsmyndighet og rettighetshaver.
- Avklar rettigheter til innebygde ST10004-, PA 0702- og PA 0802-data.
- Kontroller tredjepartsbiblioteker og deres lisenser.
- Verifiser sikkerhets- og personvernpåstander ved praktisk nettverkstest.
- Erstatt midlertidig `LICENSE` med godkjent lisens **først etter** beslutning fra rettighetshaver, og angi presist hvilke komponenter/data den omfatter.

**Faglig dokumentasjon:** se `SOURCES.md`.  
**Gjeldende lisensstatus:** se `LICENSE`.
