# app.py
"""Główna aplikacja Streamlit z pełną wizualizacją"""

import streamlit as st
import sys
import os

# Dodaj src do path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.data_loader import DataLoaderFactory
from data.data_processor import DataProcessor, CountryAggregationStrategy, RegionAggregationStrategy, TopNStrategy
from utils.observers import DataManager, StreamlitObserverBridge
from visual.map import MapVisualizer
from visual.chart import ChartVisualizer
from visual.pdf import PDFExporter


def main():
    st.set_page_config(
        page_title="Eurostat Vehicle Data Analyzer",
        page_icon="🚗",
        layout="wide"
    )
    
    st.title("🚗 Eurostat Vehicle Data Analyzer")
    st.markdown("System analizy danych o pojazdach w Europie")
    
    # Initialize session state z wzorcami projektowymi
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
        st.session_state.observer_bridge = StreamlitObserverBridge(st.session_state.data_manager)
        st.session_state.data_processor = DataProcessor(CountryAggregationStrategy())
        st.session_state.chart_visualizer = ChartVisualizer()
        st.session_state.pdf_exporter = PDFExporter()
    
    # Initialize other session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Kontrolki")
        
        # Przycisk wczytywania danych
        if st.button("📂 Wczytaj dane Eurostatu", type="primary"):
            load_data()
        
        # Status danych
        if st.session_state.data_loaded:
            stats = st.session_state.data_manager.get_summary_stats()
            st.success("✅ Dane załadowane pomyślnie")
            
            if stats['env_countries_total'] > 0:
                st.write(f"🌍 Kraje środowiskowe: {stats['env_countries_total']}")
            if stats['tran_regions_total'] > 0:
                st.write(f"🚗 Regiony transportowe: {stats['tran_regions_total']}")
        
        # Suwak zakresu lat z Observer Pattern
        if st.session_state.data_loaded:
            st.subheader("📅 Zakres czasowy")
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
                st.rerun()
                
        else:
            st.info("👈 Wczytaj dane aby aktywować kontrolki")
    
    # Główne zakładki
    tab1, tab2, tab3 = st.tabs([
        "🗺️ Mapa środowiskowa", 
        "⚡ Mapa transportowa", 
        "📊 Analiza krajów"
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
        env_file = "in/env_waselvtdefaultview_spreadsheet.xlsx"
        if os.path.exists(env_file):
            with st.spinner("🔄 Wczytywanie danych środowiskowych..."):
                env_loader = factory.create_loader('environmental')
                env_data = env_loader.load(env_file)
                # Użyj Observer Pattern do powiadomienia o załadowaniu
                st.session_state.data_manager.load_environmental_data(env_data)
        
        # Wczytaj dane transportowe
        tran_file = "in/tran_r_elvehstdefaultview_spreadsheet.xlsx"
        if os.path.exists(tran_file):
            with st.spinner("🔄 Wczytywanie danych transportowych..."):
                tran_loader = factory.create_loader('transport')
                tran_data = tran_loader.load(tran_file)
                # Użyj Observer Pattern do powiadomienia o załadowaniu
                st.session_state.data_manager.load_transport_data(tran_data)
        
        # Sprawdź czy cokolwiek załadowano
        if st.session_state.data_manager.env_data or st.session_state.data_manager.tran_data:
            st.session_state.data_loaded = True
            st.success("✅ Dane załadowane pomyślnie!")
            st.rerun()
        else:
            st.error("❌ Nie udało się załadować żadnych danych")
            
    except Exception as e:
        st.error(f"❌ Błąd wczytywania danych: {str(e)}")


def show_environmental_tab():
    """Zakładka z mapą środowiskową używająca wszystkich wzorców"""
    st.header("🌍 Pojazdy zutylizowane")
    
    data_manager = st.session_state.data_manager
    
    if not st.session_state.data_loaded or not data_manager.env_data:
        st.warning("⚠️ Brak danych środowiskowych. Wczytaj dane za pomocą przycisku w sidebarze.")
        return
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.subheader("🎛️ Kontrolki mapy")
        
        # Przełącznik widoku
        view_mode = st.radio(
            "Widok mapy:", 
            ["Europa", "Polska"], 
            key="env_view",
            help="Wybierz zasięg geograficzny mapy"
        )
        
        # Typ wizualizacji
        viz_type = st.radio(
            "Typ wizualizacji:",
            ["Mapa interaktywna", "Tabela danych"],
            key="env_viz_type"
        )
        
        st.subheader("ℹ️ Informacje")
        
        # Użyj Strategy Pattern do przetworzenia danych
        processor = st.session_state.data_processor
        processor.set_strategy(CountryAggregationStrategy())
        
        processed_data = processor.process_data(
            data_manager.get_filtered_env_data(),
            data_manager.year_range
        )
        
        st.write(f"📊 Liczba krajów: {len(processed_data['countries'])}")
        st.write(f"📅 Zakres lat: {data_manager.year_range[0]} - {data_manager.year_range[1]}")
        
        if processed_data['totals']:
            total_sum = sum(processed_data['totals'])
            st.write(f"🔢 Suma wszystkich wartości: {total_sum:,.0f}")
            
            # Top 3 kraje
            st.subheader("🏆 Top 3 krajów")
            top_countries = sorted(
                zip(processed_data['countries'], processed_data['totals']),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for i, (country, total) in enumerate(top_countries):
                st.write(f"{i+1}. **{country}**: {total:,.0f}")
    
    with col2:
        if viz_type == "Mapa interaktywna":
            st.subheader("🗺️ Mapa interaktywna")
            
            try:
                # Stwórz mapę używając MapVisualizer
                map_visualizer = MapVisualizer('environmental')
                folium_map = map_visualizer.create_map(
                    data_manager.get_filtered_env_data(),
                    data_manager.year_range,
                    view_mode
                )
                
                # Wyświetl mapę
                from streamlit_folium import st_folium
                st_folium(folium_map, width=800, height=500)
                
            except Exception as e:
                st.error(f"❌ Błąd generowania mapy: {str(e)}")
                st.info("🔄 Spróbuj odświeżyć stronę lub zmienić ustawienia")
        
        else:  # Tabela danych
            st.subheader("📋 Szczegółowe dane")
            
            if processed_data['countries']:
                # Użyj TopNStrategy do pokazania najlepszych krajów
                top_processor = DataProcessor(TopNStrategy(n=15, sort_by='total'))
                top_data = top_processor.process_data(
                    data_manager.get_filtered_env_data(),
                    data_manager.year_range
                )
                
                # Przygotuj dane do wyświetlenia
                display_data = []
                for i, (name, values, total, avg) in enumerate(zip(
                    top_data['names'], 
                    top_data['values'], 
                    top_data['totals'],
                    top_data['averages']
                )):
                    display_data.append({
                        'Pozycja': i + 1,
                        'Kraj': name,
                        'Suma': f"{total:,.0f}",
                        'Średnia': f"{avg:,.0f}",
                        f'🔚 {data_manager.year_range[1]}': f"{values[-1]:,.0f}" if len(values) > 0 else "0",
                        f'🔙 {data_manager.year_range[0]}': f"{values[0]:,.0f}" if len(values) > 0 else "0"
                    })
                
                st.dataframe(display_data, use_container_width=True)
                
                # Przycisk do pobrania CSV
                import pandas as pd
                df = pd.DataFrame(display_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="💾 Pobierz jako CSV",
                    data=csv,
                    file_name="environmental_data.csv",
                    mime="text/csv"
                )


def show_transport_tab():
    """Zakładka z mapą transportową używająca wszystkich wzorców"""
    st.header("⚡ Pojazdy elektryczne")
    
    data_manager = st.session_state.data_manager
    
    if not st.session_state.data_loaded or not data_manager.tran_data:
        st.warning("⚠️ Brak danych transportowych. Wczytaj dane za pomocą przycisku w sidebarze.")
        return
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.subheader("🎛️ Kontrolki mapy")
        
        # Przełącznik widoku
        view_mode = st.radio("Widok mapy:", ["Europa", "Polska"], key="tran_view")
        
        # Typ wizualizacji
        viz_type = st.radio(
            "Typ wizualizacji:",
            ["Mapa interaktywna", "Tabela regionów", "Wykres regionalny"],
            key="tran_viz_type"
        )
        
        st.subheader("🔧 Filtry")
        
        # Filtr kraju
        countries = sorted(set(r.country_code for r in data_manager.tran_data))
        selected_country = st.selectbox("🌍 Kraj:", ["Wszystkie"] + countries)
        
        # Filtr poziomu NUTS
        nuts_levels = sorted(set(r.nuts_level for r in data_manager.tran_data))
        selected_nuts = st.selectbox("📍 Poziom NUTS:", ["Wszystkie"] + nuts_levels)
        
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
        
        st.subheader("ℹ️ Statystyki")
        st.write(f"📊 Liczba regionów: {len(region_data['regions'])}")
        
        # Statystyki per poziom NUTS
        if region_data['regions']:
            nuts_stats = {}
            for nuts_level in region_data['nuts_levels']:
                nuts_stats[nuts_level] = nuts_stats.get(nuts_level, 0) + 1
            
            st.write("**Regiony per poziom NUTS:**")
            for level, count in sorted(nuts_stats.items()):
                st.write(f"🎯 NUTS {level}: {count}")
    
    with col2:
        if viz_type == "Mapa interaktywna":
            st.subheader("🗺️ Mapa regionów NUTS")
            
            try:
                # Stwórz mapę używając MapVisualizer
                map_visualizer = MapVisualizer('transport')
                folium_map = map_visualizer.create_map(
                    data_manager.get_filtered_tran_data(),
                    data_manager.year_range,
                    view_mode
                )
                
                # Wyświetl mapę
                from streamlit_folium import st_folium
                st_folium(folium_map, width=800, height=500)
                
            except Exception as e:
                st.error(f"❌ Błąd generowania mapy: {str(e)}")
                st.info("💡 Mapy regionów NUTS wymagają dodatkowych danych geograficznych")
        
        elif viz_type == "Tabela regionów":
            st.subheader("📋 Dane regionalne")
            
            if region_data['regions']:
                # Użyj TopNStrategy dla regionów
                top_processor = DataProcessor(TopNStrategy(n=20, sort_by='total'))
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
                        'NUTS': f"Level {item.nuts_level}",
                        'Suma': f"{total:,.0f}",
                        f'🔚 {data_manager.year_range[1]}': f"{values[-1]:,.0f}" if len(values) > 0 else "0"
                    })
                
                st.dataframe(display_data, use_container_width=True)
        
        else:  # Wykres regionalny
            st.subheader("📊 Wykres regionalny")
            
            if selected_country != "Wszystkie":
                try:
                    # Stwórz wykres regionalny
                    chart_viz = st.session_state.chart_visualizer
                    fig = chart_viz.create_regional_breakdown_chart(
                        data_manager.get_filtered_tran_data(),
                        selected_country,
                        data_manager.year_range[1]  # Najnowszy rok
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Błąd generowania wykresu: {str(e)}")
            else:
                st.info("💡 Wybierz konkretny kraj aby zobaczyć wykres regionalny")


def show_analysis_tab():
    """Zakładka z analizą krajów używająca wszystkich wzorców"""
    st.header("📊 Porównanie krajów i analiza")
    
    data_manager = st.session_state.data_manager
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Wczytaj dane aby rozpocząć analizę.")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Wybór danych")
        
        # Wybór źródła danych
        data_source = st.radio(
            "📊 Źródło danych",
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
        search_term = st.text_input("🔍 Szukaj:", key="analysis_search", 
                                   placeholder="Wpisz nazwę kraju...")
        
        if search_term:
            filtered_items = [item for item in available_items 
                            if search_term.lower() in item.lower()]
        else:
            filtered_items = available_items[:20]  # Pierwszych 20 dla wydajności
        
        # Wybór krajów/regionów
        selected_items = st.multiselect(
            "🎯 Wybierz do porównania",
            filtered_items,
            default=filtered_items[:3] if filtered_items else [],
            help="Wybierz maksymalnie 10 elementów dla czytelności wykresów"
        )
        
        # Ogranicz wybór do 10 elementów
        if len(selected_items) > 10:
            st.warning("⚠️ Wybrano za dużo elementów. Wyświetlane będzie pierwszych 10.")
            selected_items = selected_items[:10]
        
        # Aktualizuj wybór w DataManager (Observer Pattern)
        if data_source == "Pojazdy zutylizowane":
            if selected_items != data_manager.selected_countries:
                data_manager.set_selected_countries(selected_items)
        else:
            if selected_items != data_manager.selected_regions:
                data_manager.set_selected_regions(selected_items)
        
        st.subheader("🔧 Opcje analizy")
        
        analysis_type = st.radio(
            "📈 Typ analizy:",
            ["Porównanie wybranych", "Top N krajów", "Wykres czasowy", "Wykres kołowy"]
        )
        
        if analysis_type == "Top N krajów":
            top_n = st.slider("Liczba elementów", 5, 20, 10, key="top_n_slider")
            sort_criterion = st.selectbox("Sortuj według", 
                                        ["total", "average", "latest"],
                                        format_func=lambda x: {
                                            "total": "Suma całkowita",
                                            "average": "Średnia",
                                            "latest": "Najnowsza wartość"
                                        }[x])
        
        elif analysis_type == "Wykres kołowy":
            pie_year = st.selectbox(
                "Rok dla wykresu kołowego:",
                list(range(data_manager.year_range[0], data_manager.year_range[1] + 1)),
                index=-1  # Najnowszy rok
            )
        
        # Export do PDF
        st.subheader("📄 Export")
        if st.button("📥 Eksportuj do PDF", type="primary"):
            export_to_pdf(selected_items, data_source, analysis_type)
    
    with col2:
        # Wybierz odpowiednią strategię i dane
        if data_source == "Pojazdy zutylizowane":
            if analysis_type == "Top N krajów":
                strategy = TopNStrategy(n=top_n, sort_by=sort_criterion)
                data_to_process = data_manager.env_data
            else:
                strategy = CountryAggregationStrategy()
                data_to_process = data_manager.get_filtered_env_data()
        else:
            if analysis_type == "Top N krajów":
                strategy = TopNStrategy(n=top_n, sort_by=sort_criterion)
                data_to_process = data_manager.tran_data
            else:
                strategy = RegionAggregationStrategy()
                data_to_process = data_manager.get_filtered_tran_data()
        
        # Przetwórz dane używając Strategy Pattern
        processor = DataProcessor(strategy)
        result = processor.process_data(data_to_process, data_manager.year_range)
        
        # Wyświetl wyniki
        try:
            chart_viz = st.session_state.chart_visualizer
            
            if analysis_type == "Top N krajów":
                st.subheader(f"🏆 Top {len(result.get('names', []))} - {data_source}")
                
                # Wykres
                fig = chart_viz.create_top_n_chart(result, data_source)
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela
                if 'names' in result and result['names']:
                    chart_data = []
                    for i, (name, total, avg) in enumerate(zip(
                        result['names'], 
                        result['totals'], 
                        result['averages']
                    )):
                        chart_data.append({
                            'Pozycja': i + 1,
                            'Nazwa': name,
                            'Suma': f"{total:,.0f}",
                            'Średnia': f"{avg:,.0f}"
                        })
                    
                    st.dataframe(chart_data, use_container_width=True)
            
            elif analysis_type == "Wykres czasowy" and selected_items:
                st.subheader(f"📈 Trendy czasowe: {', '.join(selected_items[:3])}")
                
                fig = chart_viz.create_line_chart(result, data_source)
                st.plotly_chart(fig, use_container_width=True)
            
            elif analysis_type == "Wykres kołowy" and selected_items:
                st.subheader(f"🥧 Udział w {pie_year}: {data_source}")
                
                fig = chart_viz.create_pie_chart(result, data_source, pie_year)
                st.plotly_chart(fig, use_container_width=True)
            
            elif analysis_type == "Porównanie wybranych" and selected_items:
                st.subheader(f"📊 Porównanie: {', '.join(selected_items[:3])}")
                
                if len(selected_items) == 2:
                    fig = chart_viz.create_comparison_chart(result, data_source)
                else:
                    fig = chart_viz.create_bar_chart(result, data_source)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Dodatkowa tabela porównawcza
                if 'countries' in result or 'regions' in result or 'names' in result:
                    st.subheader("📋 Szczegóły porównania")
                    
                    items_key = 'countries' if 'countries' in result else ('regions' if 'regions' in result else 'names')
                    
                    comparison_data = []
                    for i, (item, values, total) in enumerate(zip(
                        result[items_key], 
                        result['values'], 
                        result.get('totals', [])
                    )):
                        comparison_data.append({
                            'Element': item,
                            'Suma': f"{total:,.0f}" if total else "N/A",
                            f'Rok {data_manager.year_range[0]}': f"{values[0]:,.0f}" if values else "0",
                            f'Rok {data_manager.year_range[1]}': f"{values[-1]:,.0f}" if values else "0",
                            'Trend': "📈" if values and len(values) > 1 and values[-1] > values[0] else "📉"
                        })
                    
                    st.dataframe(comparison_data, use_container_width=True)
            
            else:
                st.info("💡 Wybierz elementy do analizy lub użyj analizy Top N")
            
        except Exception as e:
            st.error(f"❌ Błąd generowania wykresu: {str(e)}")
            st.info("🔄 Spróbuj odświeżyć stronę lub zmienić parametry")


def export_to_pdf(selected_items: list, data_source: str, analysis_type: str):
    """Eksportuj wykres do PDF używając PDF Exportera"""
    try:
        data_manager = st.session_state.data_manager
        chart_viz = st.session_state.chart_visualizer
        pdf_exporter = st.session_state.pdf_exporter
        
        if not selected_items and analysis_type != "Top N krajów":
            st.error("❌ Wybierz elementy do eksportu")
            return
        
        with st.spinner("📄 Generowanie raportu PDF..."):
            # Przygotuj dane
            if data_source == "Pojazdy zutylizowane":
                strategy = CountryAggregationStrategy()
                data_to_process = data_manager.get_filtered_env_data()
            else:
                strategy = RegionAggregationStrategy()
                data_to_process = data_manager.get_filtered_tran_data()
            
            processor = DataProcessor(strategy)
            result = processor.process_data(data_to_process, data_manager.year_range)
            
            # Stwórz wykres
            if analysis_type == "Top N krajów":
                top_strategy = TopNStrategy(n=10, sort_by='total')
                top_processor = DataProcessor(top_strategy)
                top_result = top_processor.process_data(data_to_process, data_manager.year_range)
                fig = chart_viz.create_top_n_chart(top_result, data_source)
                items_for_pdf = top_result.get('names', [])[:5]  # Pierwszych 5 w nazwie pliku
            else:
                fig = chart_viz.create_bar_chart(result, data_source)
                items_for_pdf = selected_items
            
            # Przygotuj dodatkowe dane
            additional_data = {
                'total_values': sum(result.get('totals', [])),
                'average_value': sum(result.get('totals', [])) / len(result.get('totals', [])) if result.get('totals') else 0,
                'analysis_type': analysis_type,
                'countries': result.get('countries', result.get('regions', result.get('names', []))),
                'years': result.get('years', []),
                'values': result.get('values', []),
                'totals': result.get('totals', [])
            }
            
            # Eksportuj do PDF
            pdf_path = pdf_exporter.export_chart(
                figure=fig,
                countries=items_for_pdf,
                data_source=data_source,
                year_range=data_manager.year_range,
                additional_data=additional_data
            )
            
            st.success(f"✅ Raport PDF wygenerowany: {os.path.basename(pdf_path)}")
            
            # Oferuj pobranie
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📥 Pobierz raport PDF",
                    data=pdf_file.read(),
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
    
    except Exception as e:
        st.error(f"❌ Błąd eksportu PDF: {str(e)}")


if __name__ == "__main__":
    main()
