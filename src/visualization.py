# Importiert benötigte Bibliotheken für Visualisierungen:
# - matplotlib.pyplot für klassische Diagramme (z. B. Linienplots)
# - plotly.graph_objects und plotly.express für interaktive Grafiken (z. B. Treemaps, Pie Charts)
# - numpy für numerische Arrays, pandas für Tabellen, ast wird nicht genutzt
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Erstellt ein Kreisdiagramm (Pie Chart) für die Allokation nach Assetklassen (z. B. Aktien, Bonds etc.)
# Wird im Projekt verwendet, um die Aufteilung der Strategien (z. B. konservativ) visuell darzustellen
def plot_allocation_pie(allocation: pd.Series):
    # Filtert nur Allokationen mit Gewicht > 0 und sortiert sie absteigend
    allocation = allocation[allocation > 0].sort_values(ascending=False)

    # Erstellt DataFrame zur Übergabe an Plotly mit Assetklasse und Gewichtung
    df = pd.DataFrame({
        'Assetklasse': allocation.index,
        'Gewichtung': allocation.values
    })

    # Feste Farbkodierung pro Assetklasse
    farben_map = {
        'Single Stocks': '#3C7D3A',
        'ETFs': '#84A7AE',
        'Bonds': '#E6DDC7',
        'Commodities': '#D67067'
    }

    # Erstellt interaktives Kreisdiagramm mit Plotly Express
    fig = px.pie(
        df,
        names='Assetklasse',
        values='Gewichtung',
        color='Assetklasse',
        color_discrete_map=farben_map,
        hole=0  # kein Loch → klassischer Pie Chart
    )

    # Optische Anpassung der Abschnitte (Beschriftung außen, keine Abhebung, weiße Linien)
    fig.update_traces(
        textinfo='label+percent',
        textfont_size=16,
        textposition='outside',
        pull=[0] * len(df),
        marker=dict(line=dict(color='white', width=1))
    )

    # Layout-Einstellungen für Positionierung, Farben und Format
    fig.update_layout(
        showlegend=False,
        width=520,
        height=520,
        margin=dict(l=20, r=20, t=50, b=80),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    return fig

# Visualisiert den Verlauf eines Monte-Carlo-Pfads als Liniendiagramm
# Wird genutzt, um das beste Portfolio über die simulierten Handelstage darzustellen
def plot_monte_carlo(simulation_path):
    # Initialisiert leere Plotly-Figur
    fig = go.Figure()

    # Fügt den simulierten Pfad als Linie hinzu
    fig.add_trace(go.Scatter(
        y=simulation_path,
        mode='lines',
        name='Ø Pfad',
        line=dict(color='#3C7D3A', width=3)
    ))

    # Fügt Achsentitel und Diagrammtitel hinzu
    fig.update_layout(
        title='Monte-Carlo-Simulation: Bestes Portfolio über 252 Handelstage',
        xaxis_title='Tage',
        yaxis_title='Portfoliowert',
        template='plotly_white'  # helles Standardlayout
    )

    # Gibt die Visualisierung zurück
    return fig

# Erstellt eine interaktive Treemap zur Darstellung der Portfolio-Allokation
# Die einzelnen Titel sind nach Assetklasse gruppiert dargestellt
def plot_portfolio_allocation(portfolio: pd.Series):
    # Filtert Portfolio auf Positionen mit Gewicht > 0 und sortiert absteigend
    allocation = portfolio[portfolio > 0].sort_values(ascending=False)

    # 📥 Lädt ergänzende Informationen aus CSV-Datei
    # Erwartet Spalten: Asset (Ticker), Class (Kategorie), FullName (Volltext-Name)
    asset_df = pd.read_csv('data/processed/asset_list.csv')

    # Erstellt Mapping: Ticker → Assetklasse
    asset_class_map = dict(zip(asset_df['Asset'], asset_df['Class']))
    # Erstellt Mapping: Ticker → Volltext-Name
    asset_name_map = dict(zip(asset_df['Asset'], asset_df['FullName']))

    # 📊 Treemap-Daten vorbereiten für jede Asset-Position im Portfolio
    treemap_data = []
    for ticker, weight in allocation.items():
        treemap_data.append({
            'Category': asset_class_map.get(ticker, 'Unknown'),  # Fallback auf 'Unknown' bei Fehlern
            'Asset': asset_name_map.get(ticker, ticker),         # vollständiger Name oder Ticker
            'Weight': weight,                                    # relativer Anteil (0–1)
            'Percentage': round(weight * 100, 1)                 # Prozentwert gerundet auf 1 Nachkommastelle
        })

    # Erstellt DataFrame für die Treemap-Visualisierung
    treemap_df = pd.DataFrame(treemap_data)

    # 📦 Erstellt Treemap (interaktive Baumstruktur) mit Plotly Express
    fig = px.treemap(
        data_frame=treemap_df,
        path=['Category', 'Asset'],                     # Hierarchie: Kategorie > Assetname
        values='Weight',                                # Flächengröße basierend auf Gewicht
        color='Percentage',                             # Farbverlauf nach Anteil in %
        color_continuous_scale=[
        [0.0, '#d5f5e3'],
        [0.5, '#3c7d3a'],
        [1.0, '#0b3d2e']
        ],
        title="Portfolio Allocation Treemap",           # Titel der Grafik
        hover_data={'Weight': True, 'Percentage': True} # Mouseover-Infos
        )

    # Feintuning des Designs der Kästchen und Schrift
    fig.update_traces(
        textinfo="label+percent entry",                  # zeigt Label + Prozentangabe
        marker=dict(line=dict(width=1, color='white'))   # weiße Trennlinien
    )

    # Layout-Einstellungen für Platzierung, Schrift und Hintergrund
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(color='white', size=15),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title=dict(x=0.01, xanchor='left', font=dict(size=20, color='white'))  # linkbündiger Titel
    )

    # Gibt die Grafik zurück
    return fig

# Visualisiert den durchschnittlichen Pfad jedes simulierten Assets als interaktives Liniendiagramm (Plotly)
# Wird genutzt zur Qualitätsprüfung und zum Vergleich von Assetverläufen
def plot_asset_averages(asset_averages):
    import plotly.graph_objects as go

    # Initialisiert eine neue Plotly-Figur
    fig = go.Figure()

    # Fügt für jedes Asset eine Linie hinzu
    for asset, path in asset_averages.items():
        fig.add_trace(go.Scatter(
            y=path,
            mode='lines',
            name=asset,
            line=dict(width=2)
        ))

    # Layout-Einstellungen
    fig.update_layout(
        title='Durchschnittliche Asset-Pfade (Simulation)',
        xaxis_title='Tage',
        yaxis_title='Asset Wert',
        template='plotly_white',
        hovermode='x unified',
        legend_title='Assets'
    )

    return fig
