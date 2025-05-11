# Importiert benötigte Bibliotheken:
# - pandas: Für Datenmanipulation
# - KMeans: Für Clustering zur Regime-Erkennung
# - yahooquery: (nicht aktiv genutzt, vorgesehen für spätere Yahoo-Daten)
# - pairwise_distances: Für Distanzberechnung zwischen Datenpunkten
# - StandardScaler: Für Datenstandardisierung (wichtiger Schritt vor KMeans)
# - numpy: Für numerische Operationen
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler
import numpy as np
import yfinance as yf


# Lädt die historische Makroklassifikation aus einer CSV-Datei
# Diese Datei enthält Zeitpunkte mit zugewiesenen Regimen (z. B. Boom, Rezession etc.)
def load_macro_classification():
    return pd.read_csv('data/processed/macro_classification.csv')

# Holt aktuelle Makrodaten über die FRED-API
# Diese Funktion ersetzt frühere lokale CSV-Daten und liefert ein Live-Bild des aktuellen Wirtschaftszyklus
# Wird im Projektkontext verwendet, um das aktuelle Regime zu identifizieren (Schritt 1–2 der Projektlogik)
def fetch_live_macro_data(fred_api_key):
    from fredapi import Fred
    fred = Fred(api_key=fred_api_key)

    # Holt Zeitreihe des Verbraucherpreisindex (CPI) und berechnet daraus die Inflation als YoY-Veränderung
    cpi_series = fred.get_series('CPIAUCSL').dropna()
    latest_date = cpi_series.index.max()  # Aktuellster Eintrag
    cpi_now = cpi_series.loc[latest_date]
    one_year_ago = latest_date - pd.DateOffset(years=1)  # Datum vor einem Jahr
    nearest_idx = cpi_series.index.get_indexer([one_year_ago], method='nearest')[0]  # Index der nächsten passenden Zeitreihe
    cpi_old = cpi_series.iloc[nearest_idx]
    inflation = (cpi_now / cpi_old - 1) * 100  # Prozentuale Veränderung

    # Holt aktuelle Arbeitslosenquote
    unemployment = fred.get_series('UNRATE').dropna().iloc[-1]

    # Holt letztes verfügbares reales BIP-Wachstum (annualisiert, Quartalswert)
    gdp_growth = fred.get_series('A191RL1Q225SBEA').dropna().iloc[-1]

    # Holt aktuelle Treasury-Yields für 10 Jahre und 2 Jahre
    treasury_yield_10y = fred.get_series('GS10').dropna().iloc[-1]
    treasury_yield_2y = fred.get_series('GS2').dropna().iloc[-1]

    # Berechnet die Zinsstrukturkurve (10Y – 2Y), ein Indikator für mögliche Rezessionen
    yield_curve = treasury_yield_10y - treasury_yield_2y

    # Holt aktuellen VIX-Wert über yfinance (kein Fallback)
    vix_data = yf.download("^VIX", period="5d", interval="1d", progress=False)
    vix_series = vix_data["Close"].dropna()
    vix = float(vix_series.iloc[-1])

    # Aggregiert alle Werte in ein Dictionary
    latest_data = {
        'Inflation': inflation,
        'Unemployment': unemployment,
        'GDP_Growth': gdp_growth,
        'Yield_Curve_10Y_2Y': yield_curve,
        'Treasury_10Y': treasury_yield_10y,
        'Treasury_2Y': treasury_yield_2y,
        'VIX': vix,
    }

    # Erstellt einen DataFrame mit einer Zeile aus den aktuellen Makrodaten
    df = pd.DataFrame([latest_data])
    return df

# Klassifiziert das aktuelle Marktregime basierend auf Live-Makrodaten im Vergleich zur historischen Klassifikation
# Nutzt ein KMeans-Modell zur Clustereinteilung und weist anschließend ein Regime zu
# Gibt das erkannte Regime und die drei ähnlichsten historischen Zeiträume zurück
def classify_market_regime(live_macro_data, macro_classification):
    # Definiert die verwendeten Features, die für die Klassifikation genutzt werden
    features = ['Inflation', 'Unemployment', 'GDP_Growth', 'Yield_Curve_10Y_2Y', 'Treasury_10Y', 'Treasury_2Y', 'VIX']

    # Extrahiert nur die numerischen Daten aus der Klassifikation, ohne fehlende Werte
    historical_data = macro_classification[features].dropna()

    # Standardisiert die Features (wichtig für Clustering, damit alle Features gleich gewichtet sind)
    scaler = StandardScaler()
    historical_scaled = scaler.fit_transform(historical_data)  # Fit auf historische Daten
    live_scaled = scaler.transform(live_macro_data[features])  # Transformation des Live-Datensatzes

    # Berechnet die Distanz (Ähnlichkeit) aller historischen Punkte zum aktuellen Punkt
    distances = pairwise_distances(historical_scaled, live_scaled)

    # Sortiert die Indizes der 3 historisch ähnlichsten Zeitpunkte aufsteigend nach Distanz
    sorted_indices = np.argsort(distances.flatten())[:3]

    # Bestimme das Regime anhand der historisch ähnlichsten Periode (Index mit geringster Distanz)
    regime = macro_classification.iloc[sorted_indices[0]]["Regime"]

    # Liste zur Speicherung der drei ähnlichsten Zeitpunkte
    top_periods = []

    # Fügt die Distanzwerte in die macro_classification-Tabelle ein (optional, z. B. zur Visualisierung)
    macro_classification['Distance'] = np.nan
    for idx in sorted_indices:
        macro_classification.at[idx, 'Distance'] = distances.flatten()[idx]
        top_periods.append(macro_classification.at[idx, 'Date']) 

    # Gibt das ermittelte Regime und die Liste der drei ähnlichsten historischen Perioden zurück
    return regime, top_periods
