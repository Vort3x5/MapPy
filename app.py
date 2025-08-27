# app.py
"""Główna aplikacja Streamlit"""

import streamlit as st
import sys
import os
import pandas as pd

# Dodaj src do path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.data_loader import DataLoaderFactory
from data.data_processor import DataProcessor, CountryAggregationStrategy, RegionAggregationStrategy
from utils.observers import DataManager
from visual.chart import ChartVisualizer
from visual.pdf import PDFExporter

# Próbuj zaimportować komponenty map
try:
    from visual.map import MapVisualizer
    import streamlit_folium as st_folium
    HAS_MAPS = True
except ImportError:
    HAS_MAPS = False


def init_session_state():
    """Inicjalizuj stan sesji z Observer Pattern"""
    if 'initialized' not in st.session_state:
        st.session_state.data_manager = DataManager()
        st.session_state.data_processor = DataProcessor(CountryAggregationStrategy())
        st.session_state.chart_visualizer = ChartVisualizer()
        st.session_state.pdf_exporter = PDFExporter()
        st.session_state.data_loaded = False
        
        # Setup Observer Pattern
        from utils.observers import StreamlitObserverBridge, DataObserver
        st.session_state.observer_bridge = StreamlitObserverBridge(st.session_state.data_manager)
        
        # Rejestruj observerów dla komponentów
        def map_refresh_callback(event_type, data):
            if event_type in ['year_range_changed', 'countries_selected', 'filter_applied']:
                # Oznacz że mapy wymagają odświeżenia
                st.session_state.refresh_maps = True
        
        def chart_refresh_callback(event_type, data):
            if event_type in ['year_range_changed', 'countries_selected']:
                # Oznacz że wykresy wymagają odświeżenia
                st.session_state.refresh_charts = True
        
        # Zarejestruj observerów
        st.session_state.observer_bridge.register_component("maps", map_refresh_callback)
        st.session_state.observer_bridge.register_component("charts", chart_refresh_callback)
        
        st.session_state.initialized = True


def main():
    st.set_page_config(
        page_title="Eurostat Vehicle Data Analyzer",
        page_icon="🚗",
        layout="wide"
    )
    
    st.title("Eurostat Vehicle Data Analyzer")
    st.markdown("System analizy danych o pojazdach w Europie")
    
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.header("Panel kontrolny")
        
        # Upload plików
        st.subheader("Pliki danych")
        
        env_file = st.file_uploader(
            "Plik środowiskowy (env_waselvt):",
            type=['xlsx'],
            key="env_upload",
            help="Wybierz plik Excel z danymi o pojazdach zutylizowanych"
        )
        
        tran_file = st.file_uploader(
            "Plik transportowy (tran_r_elvehst):",
            type=['xlsx'],
            key="tran_upload", 
            help="Wybierz plik Excel z danymi o pojazdach elektrycznych"
        )
        
        # Wczytywanie danych
        if st.button("Wczytaj dane", type="primary", disabled=not (env_file or tran_file)):
            load_data(env_file, tran_file)
        
        # Kontrolki gdy dane załadowane
        if st.session_state.data_loaded:
            st.subheader("Załadowane dane")
            stats = st.session_state.data_manager.get_summary_stats()
            
            if stats['env_countries_total'] > 0:
                st.metric("Kraje (środowiskowe)", stats['env_countries_total'])
            
            if stats['tran_regions_total'] > 0:
                st.metric("Regiony (transportowe)", stats['tran_regions_total'])
            
            # Zakres lat z Observer Pattern
            st.subheader("Zakres czasowy")
            current_range = st.session_state.data_manager.year_range
            
            year_range = st.slider(
                "Wybierz lata",
                min_value=2013,
                max_value=2022,
                value=current_range,
                key="year_range_slider"
            )
            
            # Aktualizuj DataManager przez Observer Pattern
            if year_range != current_range:
                st.session_state.data_manager.set_year_range(year_range)
                # Observer Pattern automatycznie powiadomi komponenty
                # ale musimy również odświeżyć Streamlit
                st.rerun()
    
    # Główne zakładki
    if not st.session_state.data_loaded:
        show_welcome_screen()
    else:
        tab1, tab2, tab3 = st.tabs([
            "Mapa środowiskowa", 
            "Mapa transportowa", 
            "Analiza krajów"
        ])
        
        with tab1:
            show_environmental_tab()
        
        with tab2:
            show_transport_tab()
        
        with tab3:
            show_analysis_tab()


def load_data(env_file, tran_file):
    """Wczytaj dane z uploadowanych plików"""
    try:
        factory = DataLoaderFactory()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Dane środowiskowe
        if env_file is not None:
            status_text.text("Wczytywanie danych środowiskowych...")
            progress_bar.progress(20)
            
            # Zapisz tymczasowo plik
            with open("temp_env.xlsx", "wb") as f:
                f.write(env_file.getvalue())
            
            env_loader = factory.create_loader('environmental')
            env_data = env_loader.load("temp_env.xlsx")
            
            if env_data:
                st.session_state.data_manager.load_environmental_data(env_data)
                progress_bar.progress(50)
            
            os.remove("temp_env.xlsx")
        
        # Dane transportowe
        if tran_file is not None:
            status_text.text("Wczytywanie danych transportowych...")
            progress_bar.progress(70)
            
            # Zapisz tymczasowo plik
            with open("temp_tran.xlsx", "wb") as f:
                f.write(tran_file.getvalue())
            
            tran_loader = factory.create_loader('transport')
            tran_data = tran_loader.load("temp_tran.xlsx")
            
            if tran_data:
                st.session_state.data_manager.load_transport_data(tran_data)
                progress_bar.progress(90)
            
            os.remove("temp_tran.xlsx")
        
        progress_bar.progress(100)
        
        if st.session_state.data_manager.env_data or st.session_state.data_manager.tran_data:
            st.session_state.data_loaded = True
            status_text.empty()
            progress_bar.empty()
            st.success("Dane załadowane pomyślnie")
            st.rerun()
        else:
            st.error("Nie udało się załadować żadnych danych")
            
    except Exception as e:
        st.error(f"Błąd wczytywania danych: {str(e)}")


def show_welcome_screen():
    """Ekran powitalny"""
    st.markdown("## Witaj w systemie analizy danych Eurostat")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Funkcje systemu:
        - Analiza danych o pojazdach zutylizowanych
        - Analiza pojazdów elektrycznych w regionach
        - Interaktywne mapy dla Europy i Polski
        - Wykresy porównawcze i trendy czasowe
        - Export raportów do PDF
        
        ### Jak zacząć:
        1. Wybierz pliki danych w panelu bocznym
        2. Kliknij "Wczytaj dane"
        3. Eksploruj dane używając zakładek
        """)
    
    with col2:
        st.info("Użyj przycisków 'Browse files' w panelu bocznym aby wybrać pliki Excel z danymi Eurostat")
        
        if not HAS_MAPS:
            st.warning("Mapy interaktywne niedostępne - brakuje pakietu streamlit-folium")


def show_environmental_tab():
    """Zakładka danych środowiskowych"""
    data_manager = st.session_state.data_manager
    
    if not data_manager.env_data:
        st.warning("Brak danych środowiskowych")
        return
    
    st.header("Pojazdy zutylizowane w krajach Europy")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Kontrolki")
        
        # Widok mapy
        view_mode = st.radio("Widok mapy:", ["Europa", "Polska"], key="env_view")
        
        # Typ wizualizacji
        viz_options = ["Tabela krajów", "Statystyki", "Wykres porównawczy"]
        if HAS_MAPS:
            viz_options.insert(0, "Mapa interaktywna")
        
        viz_type = st.radio("Typ wizualizacji:", viz_options)
        
        # Filtr krajów
        available_countries = [c.country_name for c in data_manager.env_data]
        selected_countries = st.multiselect(
            "Wybierz kraje:",
            available_countries,
            default=available_countries[:5]
        )
        
        if selected_countries != data_manager.selected_countries:
            data_manager.set_selected_countries(selected_countries)
            # Observer Pattern powiadomi o zmianie, ale wymuszamy też rerun
            st.rerun()
    
    with col2:
        if viz_type == "Mapa interaktywna" and HAS_MAPS:
            show_environmental_map(view_mode)
        elif viz_type == "Tabela krajów":
            show_environmental_table()
        elif viz_type == "Wykres porównawczy":
            show_environmental_chart()
        else:
            show_environmental_statistics()


def show_environmental_map(view_mode):
    """Mapa środowiskowa"""
    try:
        st.subheader("Mapa interaktywna - Pojazdy zutylizowane")
        
        data_manager = st.session_state.data_manager
        map_visualizer = MapVisualizer('environmental')
        
        with st.spinner("Generowanie mapy..."):
            folium_map = map_visualizer.create_map(
                data_manager.get_filtered_env_data(),
                data_manager.year_range,
                view_mode
            )
        
        st_folium.st_folium(folium_map, width=800, height=500)
    
    except Exception as e:
        st.error(f"Błąd generowania mapy: {str(e)}")
        st.info("Przełączam na tabelę:")
        show_environmental_table()


def show_environmental_table():
    """Tabela danych środowiskowych"""
    st.subheader("Dane krajów - Pojazdy zutylizowane")
    
    data_manager = st.session_state.data_manager
    processor = DataProcessor(CountryAggregationStrategy())
    
    result = processor.process_data(
        data_manager.get_filtered_env_data(),
        data_manager.year_range
    )
    
    if result['countries']:
        display_data = []
        for i, (country, values, total, avg) in enumerate(zip(
            result['countries'], result['values'], result['totals'], result['averages']
        )):
            display_data.append({
                'Lp.': i + 1,
                'Kraj': country,
                'Suma': f"{total:,.0f}",
                'Średnia': f"{avg:,.0f}",
                f'{data_manager.year_range[0]}': f"{values[0]:,.0f}" if values else "0",
                f'{data_manager.year_range[1]}': f"{values[-1]:,.0f}" if len(values) > 1 else "0"
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Pobieranie CSV
        csv = df.to_csv(index=False)
        st.download_button(
            "Pobierz CSV",
            data=csv,
            file_name="environmental_data.csv",
            mime="text/csv"
        )
    else:
        st.info("Brak danych do wyświetlenia")


def show_environmental_chart():
    """Wykres dla danych środowiskowych"""
    st.subheader("Wykres porównawczy krajów")
    
    data_manager = st.session_state.data_manager
    processor = DataProcessor(CountryAggregationStrategy())
    
    result = processor.process_data(
        data_manager.get_filtered_env_data(),
        data_manager.year_range
    )
    
    if result['countries']:
        chart_viz = st.session_state.chart_visualizer
        fig = chart_viz.create_bar_chart(result, "Pojazdy zutylizowane")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych do wyświetlenia")


def show_environmental_statistics():
    """Statystyki środowiskowe"""
    st.subheader("Statystyki - Pojazdy zutylizowane")
    
    data_manager = st.session_state.data_manager
    processor = DataProcessor(CountryAggregationStrategy())
    
    result = processor.process_data(
        data_manager.get_filtered_env_data(),
        data_manager.year_range
    )
    
    if result['totals']:
        col1, col2, col3, col4 = st.columns(4)
        
        total_sum = sum(result['totals'])
        avg_total = total_sum / len(result['totals'])
        max_country = max(zip(result['countries'], result['totals']), key=lambda x: x[1])
        min_country = min(zip(result['countries'], result['totals']), key=lambda x: x[1])
        
        with col1:
            st.metric("Suma wszystkich", f"{total_sum:,.0f}")
        with col2:
            st.metric("Średnia na kraj", f"{avg_total:,.0f}")
        with col3:
            st.metric("Najwyższy", max_country[0], f"{max_country[1]:,.0f}")
        with col4:
            st.metric("Najniższy", min_country[0], f"{min_country[1]:,.0f}")
        
        # Wykres krajów
        processor = DataProcessor(CountryAggregationStrategy())
        result = processor.process_data(
            data_manager.get_filtered_env_data(),
            data_manager.year_range
        )
        
        if result['countries']:
            # Sortuj po sumie i weź top 10
            sorted_data = list(zip(result['countries'], result['totals']))
            sorted_data.sort(key=lambda x: x[1], reverse=True)
            top_countries = sorted_data[:10]
            
            if top_countries:
                chart_viz = st.session_state.chart_visualizer
                # Przygotuj dane dla wykresu
                top_result = {
                    'names': [item[0] for item in top_countries],
                    'totals': [item[1] for item in top_countries]
                }
                fig = chart_viz.create_top_n_chart(top_result, "Pojazdy zutylizowane")
                st.plotly_chart(fig, use_container_width=True)


def show_transport_tab():
    """Zakładka danych transportowych"""
    data_manager = st.session_state.data_manager
    
    if not data_manager.tran_data:
        st.warning("Brak danych transportowych")
        return
    
    st.header("Pojazdy elektryczne w regionach Europy")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Kontrolki")
        
        view_mode = st.radio("Widok mapy:", ["Europa", "Polska"], key="tran_view")
        
        viz_options = ["Tabela regionów", "Wykres krajów"]
        if HAS_MAPS:
            viz_options.insert(0, "Mapa interaktywna")
            
        viz_type = st.radio("Typ wizualizacji:", viz_options)
        
        # Filtry
        st.subheader("Filtry")
        
        countries = sorted(set(r.country_code for r in data_manager.tran_data))
        selected_country = st.selectbox("Kraj:", ["Wszystkie"] + countries)
        
        nuts_levels = sorted(set(r.nuts_level for r in data_manager.tran_data))
        selected_nuts = st.selectbox("Poziom NUTS:", ["Wszystkie"] + nuts_levels)
        
        # Zastosuj filtry
        filters = {}
        if selected_country != "Wszystkie":
            filters['country_code'] = selected_country
        if selected_nuts != "Wszystkie":
            filters['nuts_level'] = selected_nuts
        
        if filters != data_manager.data_filter:
            data_manager.apply_filter(filters)
            # Observer Pattern powiadomi o zmianie, ale wymuszamy też rerun
            st.rerun()
    
    with col2:
        if viz_type == "Mapa interaktywna" and HAS_MAPS:
            show_transport_map(view_mode)
        elif viz_type == "Tabela regionów":
            show_transport_table()
        else:
            show_transport_chart(selected_country)


def show_transport_map(view_mode):
    """Mapa transportowa"""
    try:
        st.subheader("Mapa regionalna - Pojazdy elektryczne")
        
        data_manager = st.session_state.data_manager
        map_visualizer = MapVisualizer('transport')
        
        with st.spinner("Generowanie mapy regionów..."):
            folium_map = map_visualizer.create_map(
                data_manager.get_filtered_tran_data(),
                data_manager.year_range,
                view_mode
            )
        
        st_folium.st_folium(folium_map, width=800, height=500)
    
    except Exception as e:
        st.error(f"Błąd generowania mapy: {str(e)}")
        show_transport_table()


def show_transport_table():
    """Tabela danych transportowych"""
    st.subheader("Dane regionalne - Pojazdy elektryczne")
    
    data_manager = st.session_state.data_manager
    processor = DataProcessor(RegionAggregationStrategy())
    result = processor.process_data(
        data_manager.get_filtered_tran_data(),
        data_manager.year_range
    )
    
    if result['regions']:
        # Sortuj po sumie i weź top 20
        region_data = list(zip(
            result['regions'], 
            result['totals'], 
            result['country_codes'],
            result['nuts_levels']
        ))
        region_data.sort(key=lambda x: x[1], reverse=True)
        top_regions = region_data[:20]
        
        display_data = []
        for i, (name, total, country_code, nuts_level) in enumerate(top_regions):
            display_data.append({
                'Lp.': i + 1,
                'Region': name,
                'Kraj': country_code,
                'NUTS': f"Level {nuts_level}",
                'Suma': f"{total:,.0f}"
            })
        
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("Brak danych dla wybranych filtrów")


def show_transport_chart(selected_country):
    """Wykres transportowy dla kraju"""
    st.subheader("Wykres regionalny")
    
    if selected_country != "Wszystkie":
        try:
            data_manager = st.session_state.data_manager
            chart_viz = st.session_state.chart_visualizer
            
            fig = chart_viz.create_regional_breakdown_chart(
                data_manager.get_filtered_tran_data(),
                selected_country,
                data_manager.year_range[1]
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Błąd generowania wykresu: {str(e)}")
    else:
        st.info("Wybierz konkretny kraj aby zobaczyć wykres regionalny")


def show_analysis_tab():
    """Zakładka analizy"""
    st.header("Analiza i porównania")
    
    data_manager = st.session_state.data_manager
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Konfiguracja")
        
        # Wybór źródła danych
        data_source = st.radio(
            "Źródło danych",
            ["Pojazdy zutylizowane", "Pojazdy elektryczne"]
        )
        
        # Lista elementów
        if data_source == "Pojazdy zutylizowane" and data_manager.env_data:
            available_items = [c.country_name for c in data_manager.env_data]
        elif data_source == "Pojazdy elektryczne" and data_manager.tran_data:
            available_items = []
            for region in data_manager.tran_data:
                if region.nuts_level <= 1:
                    available_items.append(f"{region.region_name} ({region.country_code})")
            available_items = sorted(list(set(available_items)))
        else:
            available_items = []
        
        # Wyszukiwanie
        search_term = st.text_input("Szukaj:", placeholder="Wpisz nazwę...")
        
        if search_term:
            filtered_items = [item for item in available_items 
                            if search_term.lower() in item.lower()]
        else:
            filtered_items = available_items[:20]
        
        # Wybór do porównania
        selected_items = st.multiselect(
            "Wybierz do porównania",
            filtered_items,
            default=filtered_items[:3] if filtered_items else []
        )
        
        # Typ analizy
        st.subheader("Typ analizy")
        analysis_type = st.radio(
            "Wybierz:",
            ["Porównanie wybranych", "Wykres czasowy", "Wykres kołowy"]
        )
        
        # Parametry dodatkowe
        if analysis_type == "Wykres kołowy":
            pie_year = st.selectbox(
                "Rok:",
                list(range(data_manager.year_range[0], data_manager.year_range[1] + 1)),
                index=-1
            )
        
        # Export
        st.subheader("Export")
        if st.button("Eksportuj PDF", type="primary"):
            export_to_pdf(selected_items, data_source, analysis_type)
    
    with col2:
        # Wykonaj analizę
        try:
            perform_analysis(data_source, analysis_type, selected_items, locals())
        except Exception as e:
            st.error(f"Błąd analizy: {str(e)}")


def perform_analysis(data_source, analysis_type, selected_items, context):
    """Wykonaj analizę"""
    data_manager = st.session_state.data_manager
    
    # Wybierz strategię
    if data_source == "Pojazdy zutylizowane":
        strategy = CountryAggregationStrategy()
        data_to_process = data_manager.get_filtered_env_data()
    else:
        strategy = RegionAggregationStrategy()
        data_to_process = data_manager.get_filtered_tran_data()
    
    # Przetwórz dane
    processor = DataProcessor(strategy)
    result = processor.process_data(data_to_process, data_manager.year_range)
    
    # Wyświetl wyniki
    chart_viz = st.session_state.chart_visualizer
    
    if analysis_type == "Wykres czasowy" and selected_items:
        st.subheader(f"Trendy czasowe: {', '.join(selected_items[:3])}")
        fig = chart_viz.create_line_chart(result, data_source)
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Wykres kołowy" and selected_items:
        pie_year = context.get('pie_year', data_manager.year_range[1])
        st.subheader(f"Udział w {pie_year}")
        fig = chart_viz.create_pie_chart(result, data_source, pie_year)
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Porównanie wybranych" and selected_items:
        st.subheader(f"Porównanie: {', '.join(selected_items[:3])}")
        
        if len(selected_items) == 2:
            fig = chart_viz.create_comparison_chart(result, data_source)
        else:
            fig = chart_viz.create_bar_chart(result, data_source)
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Wybierz elementy do analizy")


def export_to_pdf(selected_items, data_source, analysis_type):
    """Export do PDF"""
    try:
        if not selected_items:
            st.error("Wybierz elementy do eksportu")
            return
        
        data_manager = st.session_state.data_manager
        chart_viz = st.session_state.chart_visualizer
        pdf_exporter = st.session_state.pdf_exporter
        
        with st.spinner("Generowanie PDF..."):
            # Przygotuj dane
            if data_source == "Pojazdy zutylizowane":
                strategy = CountryAggregationStrategy()
                data_to_process = data_manager.get_filtered_env_data()
            else:
                strategy = RegionAggregationStrategy()
                data_to_process = data_manager.get_filtered_tran_data()
            
            processor = DataProcessor(strategy)
            result = processor.process_data(data_to_process, data_manager.year_range)
            
            # Wykres
            fig = chart_viz.create_bar_chart(result, data_source)
            
            # Export
            pdf_path = pdf_exporter.export_chart(
                figure=fig,
                countries=selected_items[:5],
                data_source=data_source,
                year_range=data_manager.year_range,
                additional_data=result
            )
            
            st.success("Raport PDF wygenerowany")
            
            # Download
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    "Pobierz PDF",
                    data=pdf_file.read(),
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
    
    except Exception as e:
        st.error(f"Błąd eksportu: {str(e)}")


if __name__ == "__main__":
    main()
