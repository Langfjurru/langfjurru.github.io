# SOURCES – FDVU Dokumentanalyse 2.4

**Status:** Foreløpig kilderegister, 29. oktober 2026. Beskriver faglige referanser identifisert i `index.html` og under utviklingen. Det dokumenterer **ikke** at rettigheter til reproduksjon eller redistribusjon er innhentet.

## Formål og avgrensning

FDVU Dokumentanalyse analyserer PDF- og DOCX-filer lokalt i nettleseren og foreslår blant annet dokumenttype, teknisk system, dokumentkrav og standardiserte filnavn. Klassifiseringen bruker både egenutviklet regel-/analysekode og innebygde kodelister/kravdata. Henvisning til en offentlig tilgjengelig kilde må ikke tolkes som at innholdet er fritt lisensiert.

## Faglige kilder identifisert

| Kilde | Bruk i løsningen | Status / forbehold |
| --- | --- | --- |
| **Statsbygg PA 0702**, med dokumentasjonskrav/vedlegg | Faglig grunnlag for dokumentkategorier og kravkobling; kode inneholder et stort PA-relatert kravregister | Publisert dokumentasjon; rett til videreformidling av omfattende tabeller/register er **ikke avklart**. Eksakt dokumentversjon og uttrekksomfang må etterprøves. |
| **Statsbygg PA 0802** og tilhørende system-/komponentkodelister | System- og komponentklassifisering; innebygde kode-/betegnelsesregistre | Rett til videreformidling av hele eller vesentlige deler av kodelistene er **ikke avklart**. Potensielt overlapp med NS-baserte kodeverk må undersøkes. |
| **NTNU ST10002** (leveransekrav FDV) | Faglige prinsipper for filnavn og dokumentidentifikasjon | Bruk og omfang bør verifiseres mot riktig revisjon; rettighetsforhold må bekreftes ved publisering. |
| **NTNU ST10003** (DAK-/tegningskrav) | Gjenkjenning og bevaring av tegningsidentifikatorer | Faglig referanse i kildekoden; bekreft riktig revisjon og eventuelle viderebruksrettigheter. |
| **NTNU ST10004** (FDVU-dokumentplan) | Matching mot dokumentkrav; `index.html` inneholder et omfattende, maskinlesbart kravregister | **Særskilt avklaring kreves** om offentlig distribusjon av registeret og eventuell opprinnelse i tredjepartsmateriale. |
| **NS 3451/NS 3456 og øvrige NS-standarder** | Kan være relevante som indirekte faglig bakgrunn gjennom kilder og teknisk terminologi | Ingen direkte gjengivelsesrett er dokumentert. Det må kontrolleres om beskyttede tabeller eller tekst er tatt inn direkte eller indirekte. |

**Offisielle kildesteder (kontroller gjeldende revisjoner):**

- Statsbygg – dokumenter og krav: https://statsbygg.no/for-leverandorer/dokumenter-og-krav/
- NTNU – prosjekteringsanvisninger: https://i.ntnu.no/wiki/-/wiki/Norsk/Prosjekteringsanvisninger
- Standard Norge: https://standard.no/

## Kildedata som faktisk er bygd inn

En gjennomgang av den fremlagte `index.html` viser innebygde datastrukturer for dokumentkrav og PA-tilknyttede system-, komponent- og kravregistre, blant annet med navnene `REQUIREMENTS`, `FDVU_PA_SYSTEMS`, `FDVU_PA_COMPONENTS` og `FDVU_PA_REQUIREMENTS`.

Dette er **ikke bare kildehenvisninger**: tabeller/data finnes i distribusjonsfilen. Før disse kan lisensieres eller distribueres videre under en åpen lisens, må rettighetshaver og rettigheter til det konkrete datainnholdet avklares. Det er ikke gjennomført en fullstendig rad-for-rad-sammenligning mot originalkildene.

## Eksterne programvareavhengigheter

Koden inneholder dynamisk lasting/bruk av biblioteker for PDF og OCR, blant annet PDF.js, Tesseract.js og OCRAD.js. Versjoner og lisenser må kvalitetssikres mot faktisk lastede ressurser. Disse tredjepartskomponentene omfattes **ikke** automatisk av en framtidig lisens til FDVU Dokumentanalyse. Før offentlig lisensiering bør det utarbeides et eget `THIRD_PARTY_NOTICES.md` med nøyaktige pakker, versjoner og lisenshenvisninger.

## Ikke-offisiell implementasjon

Programmet er et selvstendig hjelpemiddel og er **ikke** en offisiell implementasjon eller godkjenningsordning fra Statsbygg, NTNU eller Standard Norge. Ved avvik gjelder gjeldende prosjekt-/kontraktskrav og originaldokumenter foran programvarens automatiske forslag.

## Gjenstående avklaringer

1. Bekreft eierskap og publiseringsmyndighet for selve koden.
2. Bekreft hvilke revisjoner av PA- og ST-dokumentene som faktisk er benyttet.
3. Avklar videreformidling av ST10004- og Statsbygg-registrene, inkludert mulige tredjepartsrettigheter.
4. Dokumenter alle eksterne programvarebiblioteker og lisensene deres.
5. Oppdater denne filen når avklaringene foreligger.
