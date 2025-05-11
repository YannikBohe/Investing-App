# NumPy für numerische Operationen, z. B. Log-Renditen und Zufallsziehungen
# Pandas zur Arbeit mit Zeitreihen-Daten in DataFrame-Form
import numpy as np

# Führt für jedes Asset eine Monte-Carlo-Simulation mit Bootstrapping durch
# Führt pro Asset eine simulationsbasierte Zukunftsprojektion durch
# Kernbaustein der Projektlogik: Grundlage für spätere Portfoliobewertung (gewichtete Pfade)
def run_monte_carlo(prices, num_simulations=30, num_days=252):
    """ 
    Führt Monte Carlo Simulation mit Bootstrapping für jedes Asset durch.

    Parameter:
    - prices: DataFrame mit historischen Preisen (Spalten = Asset-Ticker, Zeilen = Zeitpunkte)
    - num_simulations: Anzahl der zufällig gezogenen Pfade (Simulationen) pro Asset
    - num_days: Anzahl der Tage, die jede Simulation umfassen soll (standardmäßig 1 Jahr = 252 Handelstage)

    Rückgabe:
    - Dictionary, in dem jedem Asset der durchschnittliche Pfad (numpy array) über alle Simulationen zugeordnet ist. 
    """

    # Berechnung täglicher Log-Renditen für alle Assets
    log_returns = np.log(prices / prices.shift(1)).dropna()

    # Speichert Simulationen je Asset
    asset_paths = {}

    # Schleife über alle enthaltenen Assets
    for asset in prices.columns:

        # Isolieren der Log-Renditen für das aktuelle Asset
        asset_returns = log_returns[asset].dropna()

        # Skippen, falls keine gültigen Daten vorhanden sind (z. B. wenn Asset nur NaNs enthält)
        if asset_returns.empty:
            continue

        # Liste zur Zwischenspeicherung aller Simulationen für das aktuelle Asset
        simulations = []

        # Durchführung der Simulationen (z. B. 30 Pfade)
        for _ in range(num_simulations):

            # Ziehen von Tagesrenditen mit Zurücklegen (Bootstrapping)
            # Dadurch wird keine Verteilung angenommen, sondern aus realen historischen Daten geschätzt
            sampled_returns = np.random.choice(asset_returns, size=num_days, replace=True)

            # Transformation der Log-Renditen in Preisverläufe:
            # exp(sampled_returns) → tägliche Wachstumsfaktoren
            # cumprod() → Aufsummierung dieser Faktoren über die Zeit + insert() fügt den Startwert 1.0 ein
            path = np.insert(np.cumprod(np.exp(sampled_returns)), 0, 1.0)

            # Speichern des simulierten Pfads in der Liste
            simulations.append(path)

        # Konvertierung der Liste in ein NumPy-Array und Zuordnung zum aktuellen Asset
        asset_paths[asset] = np.array(simulations)

    # Berechnung des **durchschnittlichen Pfads** je Asset über alle Simulationen
    # Dieser Durchschnittspfad dient später als Basis für Portfolio-Simulation durch Gewichtung je Titel
    asset_avg_path = {
        asset: np.mean(paths, axis=0) for asset, paths in asset_paths.items()
    }

    # Rückgabe der geglätteten Erwartungspfade -> später für Visualisierung + Analyse
    return asset_avg_path
