# Market Server – API-Aufrufe

Server läuft auf Port 9000 (Gunicorn).

---

## /market/quotes – Aktienkurse

- [AAPL](http://localhost:9000/market/quotes?symbols=AAPL)
- [ALV.DE, NESN.SW, CRM](http://localhost:9000/market/quotes?symbols=ALV.DE,NESN.SW,CRM)

---

## /market/financials – Finanzdaten

- [AAPL (JSON)](http://localhost:9000/market/financials?symbol=AAPL)
- [SAP.DE (TSV)](http://localhost:9000/market/financials?symbol=SAP.DE&format=tsv)
- [NESN.SW (JSON)](http://localhost:9000/market/financials?symbol=NESN.SW&format=json)

---

## /market/excel – Analyse-Excel herunterladen

- [AAPL](http://localhost:9000/market/excel?symbol=AAPL)
- [ALV.DE](http://localhost:9000/market/excel?symbol=ALV.DE)
- [NESN.SW](http://localhost:9000/market/excel?symbol=NESN.SW)

---

## /market/analysis – KI-Investmentanalyse

- [AAPL (Ticker)](http://localhost:9000/market/analysis?company=AAPL)
- [Allianz SE (Name)](http://localhost:9000/market/analysis?company=Allianz+SE)
- [DE0008404005 (ISIN)](http://localhost:9000/market/analysis?company=DE0008404005)
- [SAP.DE mit Kontext](http://localhost:9000/market/analysis?company=SAP.DE&context=Fokus+auf+Cloud-Transformation+und+Margenpotenzial)
