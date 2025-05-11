# Importiert NumPy für numerische Berechnungen und Pandas zur Arbeit mit tabellarischen Daten
import numpy as np
import pandas as pd

# Funktion zur Analyse und Bewertung von simulierten Portfolios
# Verwendet die durchschnittlichen Simulationspfade je Asset und gewichtet sie gemäß den Portfolio-Zusammensetzungen
# Bewertet jedes Portfolio anhand von Total Return und Sharpe Ratio, gemäß Projekt-Schritt 6–7 (vgl. Projekt Erklärung)
def analyze_simulation_results(asset_avg_paths, portfolios):
    """
    Nimmt durchschnittliche Asset-Pfade und berechnet daraus gewichtete Portfolio-Pfade.
    Bewertet alle Portfolios nach Total Return & Sharpe Ratio.
    """

    # Leere Liste zur Speicherung der Analyseergebnisse jedes Portfolios
    records = []

    # Iteriert über alle Portfolios im DataFrame (jede Zeile = ein Portfolio)
    for portfolio_id, (_, weights_row) in enumerate(portfolios.iterrows()):
        # Konvertiert die Gewichtungen der einzelnen Assets aus der aktuellen Zeile in ein Dictionary
        weights = weights_row.to_dict()

        # Bestimmt die Anzahl der Zeitschritte (Tage) anhand eines beliebigen Asset-Pfads
        days = next(iter(asset_avg_paths.values())).shape[0]

        # Initialisiert einen leeren Pfad (Numpy-Array) mit Nullen für den Gesamtverlauf des Portfolios
        portfolio_path = np.zeros(days)

        # Iteriert über alle Asset-Gewichte im aktuellen Portfolio
        for asset, weight in weights.items():
            # Nur wenn das Asset simuliert wurde (d. h. in asset_avg_paths vorhanden), wird es berücksichtigt
            if asset in asset_avg_paths:
                # Gewichteter Beitrag des Asset-Simulationspfads zum Gesamtportfolio
                portfolio_path += weight * asset_avg_paths[asset]

        # Berechnet tägliche prozentuale Renditen aus dem Portfolioverlauf
        returns = pd.Series(portfolio_path).pct_change().dropna()

        # Gesamtperformance über den gesamten Simulationszeitraum (Endwert - Startwert relativ zum Start)
        total_return = (portfolio_path[-1] - portfolio_path[0]) / portfolio_path[0]

        # Berechnung der Sharpe Ratio als Maß für risikoadjustierte Rendite (Durchschnittsrendite / Volatilität)
        # Der kleine Wert 1e-9 verhindert Division durch Null
        sharpe_ratio = returns.mean() / (returns.std() + 1e-9)

        # Fügt die Analyseergebnisse als Dictionary zur Recordliste hinzu
        records.append({
            "portfolio_id": portfolio_id,               # ID des Portfolios
            "portfolio_path": portfolio_path.tolist(),  # Verlauf (für spätere Visualisierung)
            "total_return": total_return,               # Gesamtrendite
            "sharpe_ratio": sharpe_ratio,               # Risikoadjustierte Rendite
            "weights": weights                          # Gewichtungen des Portfolios
        })

    # Wandelt die Liste der Ergebnisse in einen DataFrame um
    df = pd.DataFrame(records)

    # Speichert die Scores separat ab (vorbereitend für gewichtete Gesamtauswertung)
    df["score_total_return"] = df["total_return"]
    df["score_sharpe_ratio"] = df["sharpe_ratio"]

    # Kombinierter Score zur Gesamtbewertung: 90% Total Return + 10% Sharpe Ratio
    df["final_score"] = (
        0.9 * df["score_total_return"] + 0.1 * df["score_sharpe_ratio"]
    )

    # Identifiziert das Portfolio mit dem höchsten kombinierten Score
    best_row = df.loc[df["final_score"].idxmax()]
    best_portfolio_id = int(best_row["portfolio_id"])           # ID des besten Portfolios
    best_portfolio_path = best_row["portfolio_path"]            # Verlauf des besten Portfolios

    # Gibt zurück:
    # - den vollständigen DataFrame mit allen Portfolioergebnissen
    # - die ID des besten Portfolios
    # - dessen gewichteten Verlauf (Pfad) zur späteren Visualisierung
    return df, best_portfolio_id, best_portfolio_path
