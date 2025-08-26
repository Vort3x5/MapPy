# app.py
"""Główna aplikacja Streamlit z wzorcami projektowymi"""

import streamlit as st
import sys
import os

# Dodaj src do path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.data_loader import DataLoaderFactory
from data.data_processor import DataProcessor, CountryAggregationStrategy, RegionAggregationStrategy, TopNStrategy
from utils.observers import DataManager, StreamlitObserverBridge


def main():
    st.set_page_config(
        page_title="Eurostat Vehicle Data Analyzer",
        page_icon="🚗",
        layout="wide"
    )
    
    st.title("Eurostat Vehicle Data Analyzer")
    st.markdown("System analizy danych o pojazdach w Europie")
    
    # Initialize session state z wzorcami projektowymi
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
        st.session_state.observer_bridge = StreamlitObserverBridge(st.session_state.data_manager)
        st.session_state.data_processor = DataProcessor(CountryAggregationStrategy())
    
    # Initialize other session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Sidebar
    with st.sidebar:
        st.header("Kontrolki")
        
        # Przycisk wczytywania danych
        if st.button("Wczytaj dane Eurostatu", type="primary"):
            load_data()
        
        # Status danych
        if st.session_state.data_loaded:
            stats = st.session_state.data_manager.get_summary_stats()
            st.success("Dane załadowane pomyślnie")
            
            if stats['env_countries_total'] > 0:
                st.write(f"Kraje środowiskowe: {stats['env_countries_total']}")
            if stats['tran_regions_total'] > 0:
                st.write(f"Regiony transportowe: {stats['tran_regions_total']}")
        
        # Suwak zakresu lat z Observer Pattern
        if st.session_state.data_loaded:
            st.subheader("Zakres czasowy")
            current_range = st.session_state.data_manager.year_range
            
            year_range = st.slider(
                "Wybierz lata",
                min_value=2013,
                max_value=2022,
                value=current_range,
                key="year_range"
            )
            
            # Aktualizuj DataManager jeśli zmienił się zakres
            if year_range != current_range:
                st.session_state.data_manager.set_year_range(year_range)
                
        else:
            st.info("Wczytaj dane aby aktywować kontrolki")
    
    # Główne zakładki
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


def load_data():
    """Wczytaj dane używając Factory Pattern"""
    try:
        factory = DataLoaderFactory()
        
        # Wczytaj dane środowiskowe
        env_file = "data/env_waselvtdefaultview_spreadsheet.xlsx"
        if os.path.exists(env_file):
            with st.spinner("Wczytywanie danych środowiskowych..."):
                env_loader = factory.create_loader('environmental')
                env_data = env_loader.load(env_file)
                # Użyj Observer Pattern do powiadomienia o załadowaniu
                st.session_state.data_manager.load_environmental_data(env_data)
        
        # Wczytaj dane transportowe
        tran_file = "data/tran_r_elvehstdefaultview_spreadsheet.xlsx"
        if os.path.exists(tran_file):
            with st.spinner("Wczytywanie danych transportowych..."):
                tran_loader = factory.create_loader('transport')
                tran_data = tran_loader.load(tran_file)
                # Użyj Observer Pattern do powiadomienia o załadowaniu
                st.session_state.data_manager.load_transport_data(tran_data)
        
        # Sprawdź czy cokolwiek załadowano
        if st.session_state.data_manager.env_data or st.session_state.data_manager.tran_data:
            st.session_state.data_loaded = True
            st.success("Dane załadowane pomyślnie!")
            st.rerun()
        else:
            st.error("Nie udało się załadować żadnych danych")
            
    except Exception as e:
        st.error(f"Błąd wczytywania danych: {str(e)}")


def show_environmental_tab():
    """Zakładka z mapą środowiskową używająca Strategy Pattern"""
    st.header("Pojazdy zutylizowane")
    
    data_manager = st.session_state.data_manager
    
    if not st.session_state.data_loaded or not data_manager.env_data:
        st.warning("Brak danych środowiskowych. Wczytaj dane za pomocą przycisku w sidebarze.")
        return
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        view_mode = st.radio("Widok", ["Europa", "Polska"], key="env_view")
        
        st.subheader("Informacje")
        
        # Użyj Strategy Pattern do przetworzenia danych
        processor = st.session_state.data_processor
        processor.set_strategy(CountryAggregationStrategy())
        
        processed_data = processor.process_data(
            data_manager.get_filtered_env_data(),
            data_manager.year_range
        )
        
        st.write(f"Liczba krajów: {len(processed_data['countries'])}")
        st.write(f"Zakres lat: {data_manager.year_range[0]} - {data_manager.year_range[1]}")
        
        # Top N krajów
        if processed_data['countries']:
            st.subheader("Top 5 krajów")
            top_countries = sorted(
                zip(processed_data['countries'], processed_data['totals']),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for i, (country, total) in enumerate(top_countries):
                st.write(f"{i+1}. {country}: {total:,.0f}")
    
    with col2:
        st.info("Mapa interaktywna - w implementacji...")
        
        # Pokaż przetworzone dane
        if processed_data['countries']:
            # Użyj TopNStrategy do pokazania najlepszych krajów
            top_processor = DataProcessor(TopNStrategy(n=10, sort_by='total'))
            top_data = top_processor.process_data(
                data_manager.get_filtered_env_data(),
                data_manager.year_range
            )
            
            # Przygotuj dane do wyświetlenia
            display_data = []
            for i, (name, values, total) in enumerate(zip(top_data['names'], top_data['values'], top_data['totals'])):
                display_data.append({
                    'Pozycja': i + 1,
                    'Kraj': name,
                    'Suma': f"{total:,.0f}",
                    f'{data_manager.year_range[0]}': f"{values[0]:,.0f}" if len(values) > 0 else "0",
                    f'{data_manager.year_range[1]}': f"{values[-1]:,.0f}" if len(values) > 0 else "0"
                })
            
            st.dataframe(display_data, use_container_width=True)


def show_transport_tab():
    """Zakładka z mapą transportową używająca Strategy Pattern"""
    st.header("Pojazdy elektryczne")
    
    data_manager = st.session_state.data_manager
    
    if not st.session_state.data_loaded or not data_manager.tran_data:
        st.warning("Brak danych transportowych. Wczytaj dane za pomocą przycisku w sidebarze.")
        return
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        view_mode = st.radio("Widok", ["Europa", "Polska"], key="tran_view")
        
        st.subheader("Filtry")
        
        # Filtr kraju
        countries = sorted(set(r.country_code for r in data_manager.tran_data))
        selected_country = st.selectbox("Kraj:", ["Wszystkie"] + countries)
        
        # Filtr poziomu NUTS
        nuts_levels = sorted(set(r.nuts_level for r in data_manager.tran_data))
        selected_nuts = st.selectbox("Poziom NUTS:", ["Wszystkie"] + nuts_levels)
        
        # Zastosuj filtry przez Observer Pattern
        filters = {}
        if selected_country != "Wszystkie":
            filters['country_code'] = selected_country
        if selected_nuts != "Wszystkie":
            filters['nuts_level'] = selected_nuts
        
        if filters != data_manager.data_filter:
            data_manager.apply_filter(filters)
        
        # Użyj Strategy Pattern do agregacji
        processor = DataProcessor(RegionAggregationStrategy())
        
        region_data = processor.process_data(
            data_manager.get_filtered_tran_data(),
            data_manager.year_range,
            country_filter=selected_country if selected_country != "Wszystkie" else None,
            nuts_level=selected_nuts if selected_nuts != "Wszystkie" else None
        )
        
        st.write(f"Liczba regionów: {len(region_data['regions'])}")
        
        # Statystyki per poziom NUTS
        if region_data['regions']:
            nuts_stats = {}
            for nuts_level in region_data['nuts_levels']:
                if nuts_level not in nuts_stats:
                    nuts_stats[nuts_level] = 0
                nuts_stats[nuts_level] += 1
            
            st.subheader("Regiony per poziom NUTS")
            for level, count in sorted(nuts_stats.items()):
                st.write(f"NUTS {level}: {count}")
    
    with col2:
        st.info("Mapa regionów NUTS - w implementacji...")
        
        # Pokaż dane regionalne
        if region_data['regions']:
            # Użyj TopNStrategy dla regionów
            top_processor = DataProcessor(TopNStrategy(n=15, sort_by='total'))
            top_regions = top_processor.process_data(
                data_manager.get_filtered_tran_data(),
                data_manager.year_range
            )
            
            display_data = []
            for i, (name, values, total, item) in enumerate(zip(
                top_regions['names'], 
                top_regions['values'], 
                top_regions['totals'],
                top_regions['items']
            )):
                display_data.append({
                    'Pozycja': i + 1,
                    'Region': name,
                    'Kraj': item.country_code,
                    'NUTS': item.nuts_level,
                    'Suma': f"{total:,.0f}",
                    f'{data_manager.year_range[1]}': f"{values[-1]:,.0f}" if len(values) > 0 else "0"
                })
            
            st.dataframe(display_data, use_container_width=True)


def show_analysis_tab():
    """Zakładka z analizą krajów używająca wszystkich wzorców"""
    st.header("Porównanie krajów")
    
    data_manager = st.session_state.data_manager
    
    if not st.session_state.data_loaded:
        st.warning("Wczytaj dane aby rozpocząć analizę.")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Wybór danych")
        
        # Wybór źródła danych
        data_source = st.radio(
            "Źródło danych",
            ["Pojazdy zutylizowane", "Pojazdy elektryczne"],
            key="data_source"
        )
        
        # Lista krajów/regionów w zależności od źródła
        if data_source == "Pojazdy zutylizowane" and data_manager.env_data:
            available_items = [c.country_name for c in data_manager.env_data]
        elif data_source == "Pojazdy elektryczne" and data_manager.tran_data:
            # Tylko na poziomie krajów lub NUTS 1
            available_items = []
            for region in data_manager.tran_data:
                if region.nuts_level <= 1:
                    available_items.append(region.region_name)
            available_items = sorted(list(set(available_items)))
        else:
            available_items = []
        
        # Wyszukiwanie
        search_term = st.text_input("Szukaj:", key="analysis_search")
        
        if search_term:
            filtered_items = [item for item in available_items 
                            if search_term.lower() in item.lower()]
        else:
            filtered_items = available_items
        
        # Wybór krajów/regionów
        selected_items = st.multiselect(
            "Wybierz do porównania",
            filtered_items,
            default=filtered_items[:3] if filtered_items else []
        )
        
        # Aktualizuj wybór w DataManager (Observer Pattern)
        if data_source == "Pojazdy zutylizowane":
            if selected_items != data_manager.selected_countries:
                data_manager.set_selected_countries(selected_items)
        else:
            if selected_items != data_manager.selected_regions:
                data_manager.set_selected_regions(selected_items)
        
        # Opcje analizy
        st.subheader("Opcje analizy")
        analysis_type = st.radio(
            "Typ analizy:",
            ["Top N", "Porównanie", "Trend czasowy"]
        )
        
        if analysis_type == "Top N":
            top_n = st.slider("Liczba elementów", 5, 20, 10)
            sort_criterion = st.selectbox("Sortuj według", ["total", "average", "latest"])
        
        # Export do PDF
        if st.button("Eksportuj do PDF"):
            st.success("Export PDF - w implementacji...")
    
    with col2:
        if selected_items or analysis_type == "Top N":
            # Wybierz odpowiednią strategię
            if data_source == "Pojazdy zutylizowane":
                if analysis_type == "Top N":
                    strategy = TopNStrategy(n=top_n, sort_by=sort_criterion)
                    data_to_process = data_manager.env_data
                else:
                    strategy = CountryAggregationStrategy()
                    data_to_process = data_manager.get_filtered_env_data()
            else:
                if analysis_type == "Top N":
                    strategy = TopNStrategy(n=top_n, sort_by=sort_criterion)
                    data_to_process = data_manager.tran_data
                else:
                    strategy = RegionAggregationStrategy()
                    data_to_process = data_manager.get_filtered_tran_data()
            
            # Przetwórz dane używając Strategy Pattern
            processor = DataProcessor(strategy)
            result = processor.process_data(data_to_process, data_manager.year_range)
            
            # Wyświetl wyniki
            if analysis_type == "Top N":
                st.subheader(f"Top {len(result.get('names', []))} - {data_source}")
                
                if 'names' in result:
                    chart_data = []
                    for i, (name, total) in enumerate(zip(result['names'], result['totals'])):
                        chart_data.append({
                            'Pozycja': i + 1,
                            'Nazwa': name,
                            'Suma': f"{total:,.0f}",
                            'Średnia': f"{result['averages'][i]:,.0f}"
                        })
                    
                    st.dataframe(chart_data, use_container_width=True)
                    
                    # Prosty wykres słupkowy
                    import pandas as pd
                    chart_df = pd.DataFrame({
                        'Nazwa': result['names'][:10],  # Top 10 dla czytelności
                        'Wartość': result['totals'][:10]
                    })
                    st.bar_chart(chart_df.set_index('Nazwa'))
                    
            else:
                st.subheader(f"Analiza: {', '.join(selected_items)}")
                st.info("Szczegółowe wykresy porównawcze - w implementacji...")
                
                # Pokaż dane dla wybranych elementów
                if 'countries' in result:
                    items_key = 'countries'
                elif 'regions' in result:
                    items_key = 'regions'
                else:
                    items_key = 'names'
                
                if items_key in result and result[items_key]:
                    st.write("Wybrane elementy:")
                    for item in result[items_key]:
                        st.write(f"- {item}")
        else:
            st.write("Wybierz elementy do analizy lub użyj analizy Top N")


if __name__ == "__main__":
    main()
