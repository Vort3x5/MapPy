import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.data_loader import DataLoaderFactory
from data.data_processor import DataProcessor, CountryAggregationStrategy, RegionAggregationStrategy
from utils.observers import DataManager
from utils.consts import MAP_CONFIG
from visual.chart import ChartVisualizer
from visual.pdf import PDFExporter

try:
    from visual.map import MapVisualizer
    import streamlit_folium as st_folium
    HAS_MAPS = True
except ImportError:
    HAS_MAPS = False


def init_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.data_manager = DataManager()
        st.session_state.data_processor = DataProcessor(CountryAggregationStrategy())
        st.session_state.chart_visualizer = ChartVisualizer()
        st.session_state.pdf_exporter = PDFExporter()
        st.session_state.data_loaded = False
        
        from utils.observers import StreamlitObserverBridge
        st.session_state.observer_bridge = StreamlitObserverBridge(st.session_state.data_manager)
        
        def refresh_callback(event_type, data):
            if event_type in ['year_range_changed', 'countries_selected', 'filter_applied']:
                st.session_state.refresh_needed = True
        
        st.session_state.observer_bridge.register_component("main", refresh_callback)
        st.session_state.initialized = True


def main():
    st.set_page_config(
        page_title="Eurostat Vehicle Data Analyzer",
        layout="wide"
    )
    
    st.title("Eurostat Vehicle Data Analyzer")
    st.markdown("System analizy danych o pojazdach w Europie")
    
    init_session_state()
    
    with st.sidebar:
        st.header("Panel kontrolny")
        
        st.subheader("Pliki danych")
        
        env_file = st.file_uploader(
            "Plik środowiskowy (env_waselvt):",
            type=['xlsx'],
            key="env_upload"
        )
        
        tran_file = st.file_uploader(
            "Plik transportowy (tran_r_elvehst):",
            type=['xlsx'],
            key="tran_upload"
        )
        
        if st.button("Wczytaj dane", type="primary", disabled=not (env_file or tran_file)):
            load_data(env_file, tran_file)
        
        if st.session_state.data_loaded:
            st.subheader("Załadowane dane")
            stats = st.session_state.data_manager.get_summary_stats()
            
            if stats['env_countries_total'] > 0:
                st.metric("Kraje (środowiskowe)", stats['env_countries_total'])
            
            if stats['tran_regions_total'] > 0:
                st.metric("Regiony (transportowe)", stats['tran_regions_total'])
            
            st.subheader("Zakres czasowy")
            current_range = st.session_state.data_manager.year_range
            
            year_range = st.slider(
                "Wybierz lata",
                min_value=2013,
                max_value=2022,
                value=current_range,
                key="year_range_slider"
            )
            
            if year_range != current_range:
                st.session_state.data_manager.set_year_range(year_range)
                st.rerun()
    
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
    try:
        factory = DataLoaderFactory()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if env_file is not None:
            status_text.text("Wczytywanie danych środowiskowych...")
            progress_bar.progress(20)
            
            with open("temp_env.xlsx", "wb") as f:
                f.write(env_file.getvalue())
            
            env_loader = factory.create_loader('environmental')
            env_data = env_loader.load("temp_env.xlsx")
            
            if env_data:
                st.session_state.data_manager.load_environmental_data(env_data)
                progress_bar.progress(50)
            
            os.remove("temp_env.xlsx")
        
        if tran_file is not None:
            status_text.text("Wczytywanie danych transportowych...")
            progress_bar.progress(70)
            
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
    data_manager = st.session_state.data_manager
    
    if not data_manager.env_data:
        st.warning("Brak danych środowiskowych")
        return
    
    st.header("Pojazdy zutylizowane w krajach Europy")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Kontrolki")
        
        view_mode = st.radio("Widok mapy:", ["Europa", "Polska"], key="env_view")
        
        viz_options = ["Tabela krajów"]
        if HAS_MAPS:
            viz_options.insert(0, "Mapa interaktywna")
        
        viz_type = st.radio("Typ wizualizacji:", viz_options)
        
        available_countries = [c.country_name for c in data_manager.env_data]
        selected_countries = st.multiselect(
            "Wybierz kraje:",
            available_countries,
            default=available_countries[:5]
        )
        
        if selected_countries != data_manager.selected_countries:
            data_manager.set_selected_countries(selected_countries)
            st.rerun()
    
    with col2:
        if viz_type == "Mapa interaktywna" and HAS_MAPS:
            show_environmental_map(view_mode)
        else:
            show_environmental_table()


def show_environmental_map(view_mode):
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
        
        csv = df.to_csv(index=False)
        st.download_button(
            "Pobierz CSV",
            data=csv,
            file_name="environmental_data.csv",
            mime="text/csv"
        )
    else:
        st.info("Brak danych do wyświetlenia")


def show_transport_tab():
    data_manager = st.session_state.data_manager
    
    if not data_manager.tran_data:
        st.warning("Brak danych transportowych")
        return
    
    st.header("Pojazdy elektryczne w regionach Europy")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Kontrolki")
        
        view_mode = st.radio("Widok mapy:", ["Europa", "Polska"], key="tran_view")
        
        viz_options = ["Tabela regionów"]
        if HAS_MAPS:
            viz_options.insert(0, "Mapa interaktywna")
            
        viz_type = st.radio("Typ wizualizacji:", viz_options)
        
        st.subheader("Filtry")
        
        countries = sorted(set(r.country_code for r in data_manager.tran_data))
        selected_country = st.selectbox("Kraj:", ["Wszystkie"] + countries)
        
        nuts_levels = sorted(set(r.nuts_level for r in data_manager.tran_data))
        selected_nuts = st.selectbox("Poziom NUTS:", ["Wszystkie"] + nuts_levels)
        
        filters = {}
        if selected_country != "Wszystkie":
            filters['country_code'] = selected_country
        if selected_nuts != "Wszystkie":
            filters['nuts_level'] = selected_nuts
        
        if filters != data_manager.data_filter:
            data_manager.apply_filter(filters)
            st.rerun()
    
    with col2:
        if viz_type == "Mapa interaktywna" and HAS_MAPS:
            show_transport_map(view_mode)
        else:
            show_transport_table()


def show_transport_map(view_mode):
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
    st.subheader("Dane regionalne - Pojazdy elektryczne")
    
    data_manager = st.session_state.data_manager
    processor = DataProcessor(RegionAggregationStrategy())
    result = processor.process_data(
        data_manager.get_filtered_tran_data(),
        data_manager.year_range
    )
    
    if result['regions']:
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


def show_analysis_tab():
    st.header("Analiza i porównania")
    
    data_manager = st.session_state.data_manager
    
    st.subheader("Wybierz źródło danych")
    data_source = st.radio(
        "",
        ["Pojazdy zutylizowane (kraje)", "Pojazdy elektryczne (regiony)"],
        horizontal=True
    )
    
    if "zutylizowane" in data_source and data_manager.env_data:
        available_items = [c.country_name for c in data_manager.env_data 
                          if not any(skip in c.country_name.lower() 
                                   for skip in ['european union', 'euro area'])]
    elif "elektryczne" in data_source and data_manager.tran_data:
        available_items = []
        seen = set()
        for region in data_manager.tran_data:
            if region.nuts_level <= 1:
                name = f"{region.region_name} ({region.country_code})"
                if name not in seen:
                    available_items.append(name)
                    seen.add(name)
        available_items = sorted(available_items)
    else:
        available_items = []
    
    st.subheader("Lista krajów/regionów")
    
    search_term = st.text_input(
        "Filtrowanie po nazwie:",
        placeholder="Wpisz nazwę kraju lub regionu...",
        key="search_countries"
    )
    
    if search_term:
        filtered_items = [item for item in available_items 
                        if search_term.lower() in item.lower()]
    else:
        filtered_items = available_items
    
    st.caption(f"Znaleziono: {len(filtered_items)} elementów")
    
    selected_items = st.multiselect(
        "Wybierz kraje/regiony:",
        filtered_items,
        default=filtered_items[:3] if len(filtered_items) >= 3 else filtered_items,
        key="selected_countries_analysis"
    )
    
    if selected_items:
        if st.button("Wygeneruj wykres słupkowy", type="primary"):
            generate_bar_chart(data_source, selected_items)
        
        st.subheader("Export")
        if st.button("Eksportuj wykres do PDF"):
            export_chart_pdf(data_source, selected_items)
    else:
        st.info("Wybierz kraje/regiony z listy aby wygenerować wykres")


def generate_bar_chart(data_source, selected_items):
    data_manager = st.session_state.data_manager
    chart_viz = st.session_state.chart_visualizer
    
    try:
        if "zutylizowane" in data_source:
            all_data = data_manager.env_data
            filtered_data = [c for c in all_data if c.country_name in selected_items]
            strategy = CountryAggregationStrategy()
            chart_data_source = "Pojazdy zutylizowane"
        else:
            all_data = data_manager.tran_data
            selected_region_names = []
            for item in selected_items:
                if " (" in item:
                    region_name = item.split(" (")[0]
                    selected_region_names.append(region_name)
                else:
                    selected_region_names.append(item)
            
            filtered_data = [r for r in all_data if r.region_name in selected_region_names]
            strategy = RegionAggregationStrategy()
            chart_data_source = "Pojazdy elektryczne"
        
        if not filtered_data:
            st.error("Nie znaleziono danych dla wybranych elementów")
            return
        
        processor = DataProcessor(strategy)
        result = processor.process_data(filtered_data, data_manager.year_range)
        
        fig = chart_viz.create_bar_chart(result, chart_data_source)
        st.plotly_chart(fig, use_container_width=True, key=f"analysis_chart_{len(selected_items)}")
        
        st.success("Wykres wygenerowany!")
        
    except Exception as e:
        st.error(f"Błąd generowania wykresu: {str(e)}")


def export_chart_pdf(data_source, selected_items):
    try:
        data_manager = st.session_state.data_manager
        chart_viz = st.session_state.chart_visualizer
        pdf_exporter = st.session_state.pdf_exporter
        
        with st.spinner("Generowanie PDF..."):
            if "zutylizowane" in data_source:
                all_data = data_manager.env_data
                filtered_data = [c for c in all_data if c.country_name in selected_items]
                strategy = CountryAggregationStrategy()
                chart_data_source = "Pojazdy zutylizowane"
            else:
                all_data = data_manager.tran_data
                selected_region_names = []
                for item in selected_items:
                    if " (" in item:
                        region_name = item.split(" (")[0]
                        selected_region_names.append(region_name)
                    else:
                        selected_region_names.append(item)
                
                filtered_data = [r for r in all_data if r.region_name in selected_region_names]
                strategy = RegionAggregationStrategy()
                chart_data_source = "Pojazdy elektryczne"
            
            if not filtered_data:
                st.error("Nie znaleziono danych dla wybranych elementów")
                return
            
            processor = DataProcessor(strategy)
            result = processor.process_data(filtered_data, data_manager.year_range)
            
            fig = chart_viz.create_bar_chart(result, chart_data_source)
            
            pdf_path = pdf_exporter.export_chart(
                figure=fig,
                countries=selected_items[:5],
                data_source=chart_data_source,
                year_range=data_manager.year_range,
                additional_data=result
            )
            
            st.success("Raport PDF wygenerowany!")
            
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    "Pobierz PDF",
                    data=pdf_file.read(),
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    key="download_minimal_pdf"
                )
                
    except Exception as e:
        st.error(f"Błąd eksportu: {str(e)}")


if __name__ == "__main__":
    main()
