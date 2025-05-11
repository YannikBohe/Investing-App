# === Bibliotheken importieren ===
import streamlit as st # Streamlit wird für die Benutzeroberfläche verwendet

import pandas as pd # Pandas dient zur Datenverarbeitung in Tabellenform

import os # Betriebssystemfunktionen – hier für Zugriff auf Umgebungsvariablen

import yfinance as yf #Laden von Preisdaten über Yahoo

from dotenv import load_dotenv # dotenv ermöglicht das Einlesen von API-Keys aus einer .env-Datei

from datetime import datetime, timedelta #wird für Zeitberechnungen verwendet


# === Projektinterne Module importieren ===
# Makro-Datenabfrage, Regime-Erkennung und Klassifikation
from src.utils import fetch_live_macro_data, load_macro_classification, classify_market_regime

# Laden der Asset-Liste und Zuweisung der Allokationen, Portfoliogenerierung
from src.portfolio_generator import load_asset_list, generate_portfolios, load_asset_allocation

# Monte-Carlo-Modul zur Simulation von Preisentwicklungen auf Asset-Basis
from src.monte_carlo import run_monte_carlo

# Bewertungsmodul zur Berechnung von Scores, Sharpe Ratios etc.
from src.simulation_analyzer import analyze_simulation_results

# Visualisierungsfunktionen für Kreisdiagramme, Treemaps und Zeitreihen
from src.visualization import plot_allocation_pie, plot_monte_carlo, plot_portfolio_allocation, plot_asset_averages


# === Streamlit Setup ===

# Setzt den Seitentitel und das Layout der App (breit)
st.set_page_config(page_title="Intelligenter Portfolio-Simulator", layout="wide")

# Initialisiert Zustand zur Steuerung des App-Ablaufs (nur wenn noch nicht gesetzt)
if "strategy_locked" not in st.session_state:
    st.session_state.strategy_locked = False
if "simulation_started" not in st.session_state:
    st.session_state.simulation_started = False
if "simulation_locked" not in st.session_state:
    st.session_state.simulation_locked = False

# Fügt benutzerdefiniertes CSS ein, um die Schriftgröße in der Seitenleiste zu erhöhen
st.markdown(
    """
    <style>
        
    [data-testid="stSidebar"] .css-1d391kg, [data-testid="stSidebar"] .css-1v3fvcr {
        font-size: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Titel der App mit Icon
st.title("\U0001F4C8 Intelligenter Portfolio-Simulator")

# Begrüßungstext – erklärt die Kernfunktion der App in einem Satz
st.markdown("Willkommen zur interaktiven App für Asset-Allokation und Monte Carlo Simulation.")

# HTML-formatierte Einführung, die dem Nutzer den Ablauf der App erklärt
st.markdown("""
<div style='font-size:16px; line-height:1.6'>
Diese App unterstützt dich dabei, basierend auf aktuellen makroökonomischen Daten eine passende Anlagestrategie zu wählen und eine intelligente Portfolio-Allokation zu simulieren.

🔍 Du erhältst zu Beginn eine Einschätzung des aktuellen Marktregimes.<br>
📊 Dann wählst du eine Anlagestrategie oder passt die Allokation individuell an.<br>
🧪 Anschließend generiert die App 1000 mögliche Portfolios und simuliert deren Entwicklung mit Hilfe einer Monte Carlo Simulation.<br>
🏆 Am Ende siehst du das beste Portfolio und erhältst Visualisierungen zur Performance.

<br><b>Hinweis:</b> Die App basiert auf historischen Daten und liefert keine Anlageberatung im rechtlichen Sinne.
</div>
""", unsafe_allow_html=True)

# === API-Keys laden ===

# Liest lokale Umgebungsvariablen ein (.env-Datei muss im Projekt enthalten sein)
load_dotenv()

# Holt API-Key für FRED (Makrodatenanbieter)
fred_api_key = os.getenv("FRED_API_KEY")

# === Live-Makrodaten laden und Regime bestimmen ===
try:
    # Holt aktuelle Makrodaten (Inflation, Arbeitslosigkeit, Treasury Yields, VIX etc.)
    live_macro_data = fetch_live_macro_data(fred_api_key)

    # Lädt historische Makroklassifikationen (inkl. manuell zugewiesener Regime-Labels)
    macro_classification = load_macro_classification()

    # Führt KMeans-Clustering durch und weist aktueller Makrolage ein Regime zu
    regime, top_periods = classify_market_regime(live_macro_data, macro_classification)

    # Überschrift zur Darstellung der aktuellen Lage
    st.markdown("### Aktuelle Makroökonomische Lage")

    # Umbenennung der Spaltennamen für die Anzeige (z. B. Inflation → Inflation %)
    display_macro = live_macro_data.rename(columns={
        'Inflation': 'Inflation (%)',
        'Unemployment': 'Arbeitslosenquote (%)',
        'GDP_Growth': 'BIP-Wachstum (%)',
        'Yield_Curve_10Y_2Y': 'Zinskurve 10J-2J',
        'Treasury_10Y': 'US Treasury 10J (%)',
        'Treasury_2Y': 'US Treasury 2J (%)',
        'VIX': 'Volatilitätsindex (VIX)'
    }).T

    # Setzt die neue Spalte zur Anzeige der Werte
    display_macro.columns = ["Wert"]

    # Cast zu String/Objekt, um gemischte Typen zu erlauben (verhindert FutureWarning)
    display_macro["Wert"] = display_macro["Wert"].round(2).astype("object")

    # Liste der Variablen, die als Prozent dargestellt werden sollen
    percent_cols = [
        "Inflation (%)", 
        "Arbeitslosenquote (%)", 
        "BIP-Wachstum (%)",
        "US Treasury 10J (%)",
        "US Treasury 2J (%)"
    ]

    # Wandelt numerische Werte in Prozentstrings um (z. B. 2.34 → "2.34%")
    display_macro.loc[percent_cols, "Wert"] = display_macro.loc[percent_cols, "Wert"].map(lambda x: f"{x:.2f}%")
    
    # ❗ Letzter Schritt – ALLES als String casten für Arrow-Kompatibilität:
    display_macro["Wert"] = display_macro["Wert"].astype(str)

    # Setzt Achsentitel für die Anzeige
    display_macro.index.name = "Bezeichnung"
    
    # Zeigt Tabelle mit den aktuellen Makrowerten an
    st.table(display_macro)

    # Hebt das aktuell erkannte Marktregime in einer farbigen Box hervor
    st.markdown(
        f"""
        <div style='padding: 1rem; background-color: #1f3d2c; border-radius: 8px; color: white; font-size: 16px; text-align: left;'>
            📌 <b>Erkanntes Marktregime:</b> <span style="color: #F8EB59;">{regime}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Überschrift zur Anzeige der historisch ähnlichsten Zeiträume
    st.markdown("### 🗓 Ähnlichste historische Perioden zum aktuellen Regime:")

    # Erstellt eine HTML-Liste, um die Top 3 ähnlichen historischen Perioden zu formatieren
    html_list = "<ul style='line-height: 1.9; margin-top: 0.5rem;'>"

    # Iteriert über die Liste der ähnlichsten Zeiträume, die vom Klassifikator zurückgegeben wurden
    for i, period in enumerate(top_periods, 1):
        # Holt die Zeile aus dem Klassifikations-Datensatz, die zum Periodenzeitpunkt gehört
        row = macro_classification[macro_classification['Date'] == period].iloc[0]

        # Extrahiert den Distanzwert zwischen aktuellem Zustand und diesem Zeitraum
        distance = row.get('Distance', None)

        # Formatiert die Distanz als String oder zeigt N/A, falls nicht vorhanden
        distance_str = f"{distance:.4f}" if isinstance(distance, float) else "N/A"

        # Holt das zugeordnete Regime aus der Zeile
        regime_text = row['Regime']

        # Fügt einen Listeneintrag zur HTML-Liste hinzu
        html_list += f"<li><b>Platz {i}:</b> {period} | Regime: <i>{regime_text}</i> | Abstand: {distance_str}</li>"

    # Schliesst die HTML-Liste ab
    html_list += "</ul>"

    # Zeigt die HTML-Liste in der App an
    st.markdown(html_list, unsafe_allow_html=True)

# === Fehlerbehandlung für Makro-Klassifikation oder Datenabruf ===
except Exception as e:
    # Zeigt eine Fehlermeldung bei Ausnahme
    st.error("❌ Fehler beim Laden oder Verarbeiten der Daten.")
    # Gibt die Exception mit Stacktrace aus
    st.exception(e)
    
    # Trennt den Abschnitt visuell
    st.markdown("---")
    # Setzt Titel für den nächsten Abschnitt: Strategieauswahl
    st.markdown("### \U0001F3AF Anlagestrategie")

# === Initialisiere Session-State erneut, falls nötig ===
if "strategy_locked" not in st.session_state:
    st.session_state.strategy_locked = False
if "simulation_started" not in st.session_state:
    st.session_state.simulation_started = False

# === Strategieauswahl im Sidebar-Bereich ===
if not st.session_state.strategy_locked:
    # Dropdown-Menü zur Auswahl der gewünschten Strategie
    strategie_input = st.sidebar.selectbox(
        "\U0001F4CC Anlagestrategie wählen",
        ["Konservativ", "Ausgewogen", "Wachstum"],
        key="strategie_input"
    )

    # Auswahl der Anzahl an zu generierenden Portfolios
    num_portfolios_input = st.sidebar.number_input(
        "Anzahl zu generierender Portfolios",
        min_value=100,
        max_value=5000,
        step=100,
        value=1000,
        key="num_portfolios_input"
    )

    # Option für benutzerdefinierte Allokation aktivieren
    use_custom = st.sidebar.checkbox("⚙️ Eigene Allokation eingeben", key="use_custom_allocation_checkbox")
else:
    # Wenn Strategie bereits festgelegt wurde, benutze gespeicherte Werte
    st.sidebar.success("✅ Strategie & Anzahl Portfolios gesetzt.")
    strategie_input = st.session_state.get("strategie", "Konservativ")
    num_portfolios_input = st.session_state.get("num_portfolios", 1000)
    use_custom = st.session_state.get("use_custom", False)

# === Empfehlung laden anhand Regime & Strategie ===
asset_allocation_df = load_asset_allocation()

# Filtert passende Allokation für erkannte Regime-Strategie-Kombination
recommended_allocation = asset_allocation_df[
    (asset_allocation_df['Makro_Regime'] == regime) &
    (asset_allocation_df['Strategie'] == strategie_input)
].iloc[0].drop(['Makro_Regime', 'Strategie'])

# === Empfehlung anzeigen ===
st.markdown("### 🧮 Empfohlene Asset-Allokation")

# Bereitet Daten für Tabellenanzeige auf
display_allocation = recommended_allocation.rename_axis("Bezeichnung").rename("Wert").to_frame()
display_allocation["Wert"] = display_allocation["Wert"].map(lambda x: f"{x:.0f} %")

# Zeigt die Tabelle in der App
st.table(display_allocation)

# === Optional: Benutzerdefinierte Allokation aktivieren ===
allocation_valid = True
if use_custom and not st.session_state.strategy_locked:
    st.sidebar.markdown("### 🛠 Benutzerdefinierte Allokation")

    # Initialisiert Wörterbuch und Zähler
    custom_allocation = {}
    total = 0

    # Erstelle Slider pro Assetklasse
    for asset_class in recommended_allocation.index:
        val = st.sidebar.slider(
            f"{asset_class} (%)", 0, 100,
            int(recommended_allocation[asset_class]),
            key=f"slider_{asset_class}"
        )
        custom_allocation[asset_class] = val
        total += val

    # Konvertiert in Series
    current_allocation = pd.Series(custom_allocation)

    # Anzeige der benutzerdefinierten Allokation
    st.markdown("### 📊 Eigene Asset-Allokation")
    display_custom = current_allocation.rename_axis("Bezeichnung").rename("Wert").to_frame()
    display_custom["Wert"] = display_custom["Wert"].map(lambda x: f"{x:.0f} %")
    st.table(display_custom)

    # Validierung: Summe muss genau 100 % ergeben
    if total != 100:
        st.sidebar.error(f"❌ Die Gesamtallokation beträgt {total} %. Bitte stelle sicher, dass die Summe genau 100 % ergibt.")
        allocation_valid = False
    else:
        st.sidebar.success("✅ Die Gesamtallokation beträgt genau 100 %.")
else:
    # Falls keine benutzerdefinierte Eingabe → Systemempfehlung verwenden
    if st.session_state.get("use_custom", False):
        current_allocation = st.session_state.get("current_allocation", recommended_allocation)
    else:
        current_allocation = recommended_allocation

# === Anzeige der aktuellen Allokation als Diagramm ===
if allocation_valid:
    st.markdown("### 📊 Deine aktuelle Asset-Allokation")
    st.markdown(" ")
    
    # Layout mit zwei Spalten: links Grafik, rechts Legende
    col1, col2 = st.columns([1.5, 1])

    # Linke Spalte: Kreisdiagramm (Pie Chart)
    with col1:
        fig = plot_allocation_pie(current_allocation)
        st.plotly_chart(fig, use_container_width=True)

    # Rechte Spalte: Farbliche Legende der Kategorien
    with col2:
        st.markdown("**Legende:**")
        farben = ['#3C7D3A', '#84A7AE', '#E6DDC7', '#D67067', '#F8EB59']
        for label, color in zip(current_allocation.index, farben):
            st.markdown(f"<span style='color:{color}'>⬤</span> {label}", unsafe_allow_html=True)

    # Speichert Zustände für spätere Verarbeitung
    st.session_state.current_allocation = current_allocation
    st.session_state.regime = regime
    st.session_state.top_periods = top_periods
else:
    # Warnung, wenn Allokation ≠ 100 %
    st.warning("⚠️ Visualisierung wird nur angezeigt, wenn die Allokation genau 100% beträgt.")


# === Button zur Portfoliogenerierung ===
if not st.session_state.strategy_locked:
    start_simulation = st.sidebar.button(
        "📈 Portfolios generieren & weiter zur Simulation",
        key="generate_simulation"
    )

    # Wenn Button gedrückt wurde und Allokation gültig ist:
    if allocation_valid and start_simulation:
        with st.spinner("Generiere Portfolios basierend auf deiner Allokation..."):

            # Holt Assetliste und gruppiert nach Assetklassen
            asset_list = load_asset_list()
            assets_by_class = asset_list.groupby('Class')['Asset'].apply(list).to_dict()

            # Erstellt 1000 Portfolios mit Zufallsgewichtung innerhalb der Klassen
            portfolios = generate_portfolios(current_allocation, assets_by_class, num_portfolios=num_portfolios_input)

            # Falls Portfolios erfolgreich erzeugt wurden
            if portfolios is not None and not portfolios.empty:
                st.success("✅ Portfolios wurden erfolgreich generiert.")

                # Speichert aktuelle Konfiguration im Session-State
                st.session_state.strategy_locked = True
                st.session_state.strategie = strategie_input
                st.session_state.num_portfolios = num_portfolios_input
                st.session_state.use_custom = use_custom
                st.session_state.current_allocation = current_allocation
                st.session_state.portfolios = portfolios

                # Reset relevanter Simulationsdaten
                st.session_state.sim_result_df = None
                st.session_state.asset_averages = None
                st.session_state.best_portfolio_id = None

                # Löst App-Neustart aus, um nahtlos in Simulationsabschnitt zu wechseln
                st.rerun()
            else:
                # Fehleranzeige, falls keine Portfolios erzeugt werden konnten
                st.error("❌ Es wurden keine gültigen Portfolios generiert.")

# === Sicherstellen, dass Portfolios existieren ===
if "portfolios" not in st.session_state:
    # Wenn keine Portfolios vorhanden sind, wird eine Fehlermeldung angezeigt
    st.error("⚠️ Du musst zuerst Portfolios generieren.")
    # Beendet die Streamlit-Ausführung an dieser Stelle
    st.stop()

# === Simulations-Block mit Fehlerbehandlung ===
try:
    # Holt alle notwendigen Session-States
    current_allocation = st.session_state.current_allocation
    top_periods = st.session_state.top_periods
    portfolios = st.session_state.portfolios

    # Liste aller Assets im Portfolio
    assets = portfolios.columns.tolist()

    # Leerer DataFrame zur Aufnahme aller Preisverläufe
    price_data_all = pd.DataFrame()

    # Schleife über alle ähnlichen Perioden (z. B. Top 3 aus Regime-Vergleich)
    for period in top_periods:
        start_date = datetime.strptime(period, "%Y-%m-%d")
        end_date = start_date + timedelta(days=365)

        # Lade Daten über yfinance (mehrere Ticker gleichzeitig)
        try:
            data = yf.download(
                tickers=assets,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                progress=False,
                group_by='ticker',
                auto_adjust=False
            )

            # Datenstruktur anpassen
            if isinstance(data.columns, pd.MultiIndex):
                adj_close = pd.DataFrame({
                    t: data[t]["Adj Close"]
                    for t in assets if (t in data.columns.get_level_values(0))
                })
            else:
                adj_close = data["Adj Close"].to_frame() if "Adj Close" in data.columns else data

            adj_close.index = pd.to_datetime(adj_close.index)
            price_data_all = pd.concat([price_data_all, adj_close])

        except Exception as e:
            st.warning(f"⚠️ Fehler beim Abrufen der Daten für Zeitraum {period}: {e}")
            continue

    # Duplikate im Index entfernen
    price_data_all = price_data_all[~price_data_all.index.duplicated(keep='first')]

    # Schnittmenge der Assets mit dem Portfolio
    common_assets = price_data_all.columns.intersection(portfolios.columns)
    price_data_all = price_data_all[common_assets]
    portfolios = portfolios[common_assets].copy()

    st.success("\U0001F4C8 Reale Preisdaten erfolgreich geladen und abgestimmt.")


    # Sidebar-Bereich für Simulationseinstellungen
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎲 Monte Carlo Simulation")

    # Initialisierung des Simulation-Status, falls nicht vorhanden
    if "simulation_locked" not in st.session_state:
        st.session_state.simulation_locked = False

    # Auswahl der Simulationsanzahl (falls nicht gesperrt)
    if not st.session_state.simulation_locked:
        temp_simulations = st.sidebar.number_input(
            "Anzahl Simulationen pro Portfolio",
            min_value=10,
            max_value=1000,
            step=10,
            value=30,
            key="temp_n_simulations"
        )

        # Button zum Starten der Simulation
        start_mc_sim = st.sidebar.button(
            "▶️ Monte Carlo Simulation starten",
            key="start_mc_sim_btn"
        )
    else:
        # Zeigt an, dass Simulationseinstellungen eingefroren sind
        st.sidebar.success("✅ Simulationseinstellungen sind eingefroren.")
        temp_simulations = st.session_state.get("n_simulations", 30)
        start_mc_sim = False

    # Wenn Simulation gestartet wurde
    if start_mc_sim:
        with st.spinner("Monte Carlo Simulation läuft... bitte einen Moment Geduld..."):
            # Führt Monte Carlo Simulation durch
            asset_avg_paths = run_monte_carlo(
                price_data_all,
                num_simulations=temp_simulations
            )

            # Bewertet alle Portfolios anhand der simulierten Pfade
            analyzed_df, best_portfolio_id, best_simulation_path = analyze_simulation_results(asset_avg_paths, portfolios)

            # Speichert Ergebnisse im Session-State
            st.session_state.simulation_locked = True
            st.session_state["n_simulations"] = temp_simulations
            st.session_state.simulation_done = True
            st.session_state.sim_result_df = analyzed_df
            st.session_state.best_portfolio_id = best_portfolio_id
            st.session_state.best_simulation_path = best_simulation_path
            st.session_state.asset_averages = asset_avg_paths

            # Löst Neustart der App aus für Visualisierungsteil
            st.rerun()

    # === Reset-Button zur vollständigen App-Rücksetzung ===
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Neustart", key="reset_simulation_button_unique"):
        for key in [
            "strategy_locked", "simulation_started", "strategie", "num_portfolios",
            "use_custom", "portfolios", "current_allocation", "sim_result_df",
            "asset_averages", "best_portfolio_id", "top_periods", "regime",
            "simulation_locked", "simulation_done", "n_simulations"
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    # === Anzeige der Simulationsergebnisse ===
    if "simulation_done" in st.session_state and st.session_state.simulation_done:
        # Holt relevante Ergebnisse aus dem Session-State
        analyzed_df = st.session_state.sim_result_df
        best_portfolio_id = st.session_state.best_portfolio_id
        asset_averages = st.session_state.asset_averages

        st.success("✅ Portfolios wurden erfolgreich simuliert.")

        # 1. Bestimme Top-5 Portfolios anhand des finalen Scores
        top5_ids = (
            analyzed_df.groupby("portfolio_id")["final_score"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
            .index.tolist()
        )

        # 2. Hole beste Simulation pro Portfolio-ID
        best_simulations = (
            analyzed_df[analyzed_df["portfolio_id"].isin(top5_ids)]
            .sort_values("final_score", ascending=False)
            .groupby("portfolio_id")
            .first()
            .reset_index()
        )

        # 3. Sortiere Ergebnisse und ergänze "Rating" als Rangfolge
        best_simulations = best_simulations.sort_values("final_score", ascending=False).reset_index(drop=True)
        best_simulations.insert(0, "Rating", [f"{i+1}" for i in range(len(best_simulations))])

        # 4. Definiere Spalten zur Anzeige + Mapping schöner Namen
        columns_to_show = ["Rating", "total_return", "sharpe_ratio"]
        display_names = {
            "total_return": "Total Return",
            "sharpe_ratio": "Sharpe Ratio"
        }

        # Erzeuge formatiertes DataFrame mit Hervorhebung
        pretty_df = best_simulations[columns_to_show].rename(columns=display_names).set_index("Rating")
        styled_df = pretty_df.style\
            .format({
                "Total Return": "{:.2%}",
                "Sharpe Ratio": "{:.3f}"
            })\
            .highlight_max(axis=0, color='#3C7D3A', subset=["Total Return", "Sharpe Ratio"])\
            .set_properties(**{
                'text-align': 'center',
                'font-size': '14px'
            })

        # Zeige Ergebnisse in Streamlit
        st.markdown("### 🏆 Simulationsergebnisse – Beste Simulation je Top 5 Portfolio")
        st.dataframe(styled_df, use_container_width=True)

        # === Download und Visualisierung des besten Portfolios ===
        if best_portfolio_id in portfolios.index:
            # Hole Portfolio
            best_portfolio = portfolios.loc[best_portfolio_id]

            # Konvertiere in DataFrame für CSV-Export
            best_df = best_portfolio.reset_index()
            best_df.columns = ['Asset', 'Anteil']

            # Biete Downloadbutton an
            csv = best_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Beste Portfolioallokation als CSV herunterladen",
                data=csv,
                file_name='bestes_portfolio.csv',
                mime='text/csv'
            )

            try:
                # Visualisierung 1: Monte Carlo Pfad
                fig1 = plot_monte_carlo(st.session_state.best_simulation_path)
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning("Keine Simulationspfade für das beste Portfolio gefunden.")

                # Visualisierung 2: Treemap der Portfolio-Zusammensetzung
                st.markdown("### 🧭 Verteilung des besten Portfolios")
                fig2 = plot_portfolio_allocation(best_portfolio)
                st.plotly_chart(fig2, use_container_width=True)

                # Visualisierung 3: Durchschnittliche Assetpfade über alle Simulationen
                st.markdown("### 📈 Durchschnittliche Entwicklung pro Asset (Simulation)")
                fig3 = plot_asset_averages(asset_averages)
                st.plotly_chart(fig3, use_container_width=True)

            except Exception as e:
                st.error("⚠️ Fehler bei der Visualisierung.")
                st.exception(e)

# === Fehlerbehandlung für Gesamtsimulation ===
except Exception as e:
    st.error("❌ Fehler während der Vorbereitung der Simulation.")
    st.exception(e)
       