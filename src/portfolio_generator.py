# Importiert Pandas zur Arbeit mit Tabellen (DataFrames) und NumPy für numerische Operationen
import pandas as pd
import numpy as np

# Lädt die CSV-Datei mit der Zielallokation je Assetklasse
# Diese Datei gibt an, wie viel Prozent des Gesamtportfolios in jede Klasse (z. B. Aktien, Bonds) fließen soll
def load_asset_allocation():
    return pd.read_csv('data/processed/asset_allocation.csv')

# Lädt die CSV-Datei mit der Liste der verfügbaren Einzelassets pro Klasse
# Diese Datei enthält alle verfügbaren ETFs, Aktien, Bonds usw., die später auf die Portfolios verteilt werden
def load_asset_list():
    return pd.read_csv('data/processed/asset_list.csv')

# Generiert eine große Anzahl zufälliger Portfolios auf Basis der Zielverteilung auf Assetklassen
# Dabei wird sichergestellt, dass jedes Asset innerhalb einer Klasse ein realistisches Gewicht (zwischen min_weight und max_weight) erhält
# Die Funktion wird im Projekt im Schritt 4 verwendet (vgl. Projekt Erklärung), wo aus 25 Assets 1000 zufällige Kombinationen erstellt werden
def generate_portfolios(asset_allocation, assets_by_class, num_portfolios=1000, min_weight=0.025, max_weight=0.3):
    """
    Generiert zufällige Portfolios auf Basis der Zielgewichtung je Assetklasse.
    Die Gewichte einzelner Assets werden zufällig verteilt, unter Einhaltung von min_weight/max_weight.
    """

    # Leere Liste zur Speicherung aller generierten Portfolios
    portfolios = []

    # Schleife über die gewünschte Anzahl an Portfolios
    for _ in range(num_portfolios):
        # Initialisiert ein leeres Portfolio (Dictionary), in das später Asset-Gewichte geschrieben werden
        portfolio = {}

        # Iteration über alle Assetklassen (z. B. 'Stocks', 'Bonds', 'ETFs') und deren Zielgewicht (z. B. 60%)
        for asset_class, target_weight in asset_allocation.items():
            # Holt sich die Liste der verfügbaren Titel in der aktuellen Klasse
            assets = assets_by_class.get(asset_class, [])

            # Überspringt die Klasse, falls keine Assets verfügbar sind oder das Zielgewicht 0 ist
            if not assets or target_weight == 0:
                continue

            # Durchmischt die Liste zufällig, damit jedes Portfolio eine andere Reihenfolge bekommt
            np.random.shuffle(assets)

            # Initialisiert das aktuell zugewiesene Gewicht auf 0
            assigned_weight = 0

            # Erzeugt ein Dictionary mit allen Assets in der Klasse und setzt deren Gewicht auf 0
            asset_weights = {asset: 0 for asset in assets}

            # Solange das Zielgewicht noch nicht vollständig auf Assets verteilt wurde:
            while assigned_weight < target_weight / 100:
                # Berechnet, wie viel Gewicht noch zugewiesen werden muss
                remaining_weight = (target_weight / 100) - assigned_weight

                # Wenn das verbleibende Gewicht kleiner als das Minimum ist (z. B. < 2.5%)
                if remaining_weight < min_weight:
                    # Wählt nur Assets, die schon Gewicht bekommen haben und das Restgewicht noch vertragen können
                    eligible_assets = [
                        a for a in assets
                        if asset_weights[a] > 0 and asset_weights[a] + remaining_weight <= max_weight
                    ]
                    # Wenn solche Assets existieren, wird eines zufällig gewählt und das Restgewicht zugewiesen
                    if eligible_assets:
                        selected = np.random.choice(eligible_assets)
                        asset_weights[selected] += remaining_weight
                        assigned_weight += remaining_weight
                    # Danach wird die Schleife verlassen
                    break

                # Alle Assets, die noch unter dem Maximalgewicht liegen, sind wählbar
                eligible_assets = [a for a in assets if asset_weights[a] < max_weight]

                # Falls keine wählbaren Assets mehr vorhanden sind, bricht die Schleife ab
                if not eligible_assets:
                    break

                # Wählt zufällig ein Asset aus der zulässigen Liste
                selected = np.random.choice(eligible_assets)

                # Bestimmt, wie viel noch maximal zugewiesen werden darf (nicht über max_weight)
                max_assignable = min(max_weight - asset_weights[selected], remaining_weight)

                # Zieht zufälliges Gewicht zwischen min_weight und dem maximal Zuweisbaren
                weight = np.random.uniform(min_weight, max_assignable)

                # Fügt dem ausgewählten Asset das Gewicht hinzu
                asset_weights[selected] += weight
                # Erhöht das zugewiesene Gesamtgewicht
                assigned_weight += weight

            # Fügt die Asset-Gewichte des aktuellen Assetklasse zum Portfolio hinzu
            portfolio.update(asset_weights)

        # Fügt das fertige Portfolio zur Liste aller Portfolios hinzu
        portfolios.append(portfolio)

    # Wandelt die Liste aus Dictionaries in einen DataFrame um
    # Assets ohne Zuweisung erhalten 0
    df_portfolios = pd.DataFrame(portfolios).fillna(0)

    # Gibt den Portfolio-DataFrame zurück
    return df_portfolios
