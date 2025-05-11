# 📊 Intelligenter Portfolio Simulator

Eine interaktive Streamlit-App zur Simulation und Analyse von Portfolios auf Basis makroökonomischer Daten und historischer Marktphasen.


## 🚀 Überblick

Diese App erkennt auf Basis aktueller Makrodaten (Inflation, Arbeitslosigkeit, Treasury Yields, Zinskurve etc.) das derzeitige Marktregime (z. B. Boom, Rezession) und schlägt eine passende Anlagestrategie vor. Darauf aufbauend werden 1000 zufällige Portfolios generiert und deren Wertentwicklung mittels Monte Carlo Simulation simuliert und bewertet.


## 🧠 Hauptfunktionen

- 🔍 **Makro-Analyse:** Erkennt Marktregime via KMeans-Clustering aus FRED-Daten
- 🎯 **Strategievorschlag:** Konservativ / Ausgewogen / Wachstum – automatisch oder manuell anpassbar
- 📈 **Portfolio-Simulation:** Monte Carlo Simulation mit historischen Preisverläufen
- 📊 **Analyse:** Berechnung von Return, Sharpe Ratio, Score und Visualisierung der besten Portfolios
- 🎨 **Interaktive Grafiken:** Kreise, Treemaps, Verlaufslinien (Plotly)
- 🧮 **Regelbasierte Asset-Allokation:** auf Basis CSV-gesteuerter Makro- & Strategie-Kombinationen


## ⚙️ Installation & Ausführung (lokal)

1. Stelle sicher, dass du [Python 3.11.6](https://www.python.org/downloads/) installiert hast.
2. Navigiere im Terminal in das Projektverzeichnis und installiere die Abhängigkeiten:

```bash
pip install -r requirements.txt
```

3. Starte die Anwendung lokal mit:

```bash
streamlit run streamlit_app.py
```

4. Stelle sicher, dass eine `.env`-Datei mit deinem FRED API Key im Projektverzeichnis liegt:

FRED_API_KEY=dein_fred_api_key



## 📁 Projektstruktur

streamlit_app.py               # Haupt-App (Streamlit UI)
src/
├── monte_carlo.py             # Logik für Monte Carlo Simulation
├── portfolio_generator.py     # Erzeugt zufällige Portfolios basierend auf Allokation
├── simulation_analyzer.py     # Bewertet Simulationen: Return, Sharpe, Score
├── utils.py                   # Makrodatenabruf & Regime-Erkennung
├── visualization.py           # Alle interaktiven Plots (Plotly)
data/
├── processed/
│   ├── asset_list.csv         # Liste aller Assets & Kategorien
│   ├── asset_allocation.csv   # Allokation je Regime & Strategie
│   └── macro_classification.csv # Historische Makro-Regime-Daten
.env                           # → enthält deinen API-Key



## 💡 Voraussetzungen

- Python **3.11.6** (getestet mit dieser Version – gewährleistet stabile Kompatibilität mit allen eingesetzten Bibliotheken wie `streamlit`, `pandas` etc.)
- Internetverbindung für FRED & Yahoo Finance API
- Siehe `requirements.txt` für alle genutzten Pakete
