import streamlit as st
import sys
import os

# Dodaj src do path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.data_loader import DataLoaderFactory


def main():
    st.set_page_config(
        page_title="Eurostat Vehicle Data Analyzer",
        page_icon="🚗",
        layout="wide"
    )
    
    st.title("Eurostat Vehicle Data Analyzer")
    st.markdown("System analizy danych o pojazdach w Europie")
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
        st.session_state.env_data = None
        st.session_state.tran_data = None
    
    # Sidebar
    with st.sidebar:
        st.header("Kontrolki")
        
        # Przycisk wczytywania danych
        if st.button("Wczytaj dane Eurostatu", type="primary"):
            load_data()
        
        # Status danych
        if st.session_state.data_loaded:
            st.success("Dane załadowane pomyślnie")
            if st.session_state.env_data:
                st.write(f"Kraje środowiskowe: {len(st.session_state.env_data)}")
            if st.session_state.tran_data:
                st.write(f"Regiony transportowe: {len(st.session_state.tran_data)}")
        
        # Suwak zakresu lat
        if st.session_state.data_loaded:
            st.subheader("Zakres czasowy")
            year_range = st.slider(
                "Wybierz lata",
                min_value=2013,
                max_value=2022,
                value=(2018, 2022),
                key="year_range"
            )
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
    """Wczytaj dane z plików Excel"""
    try:
        factory = DataLoaderFactory()
        
        # Wczytaj dane środowiskowe
        env_file = "in/env_waselvtdefaultview_spreadsheet.xlsx"
        if os.path.exists(env_file):
            with st.spinner("Wczytywanie danych środowiskowych..."):
                env_loader = factory.create_loader('environmental')
                st.session_state.env_data = env_loader.load(env_file)
        
        # Wczytaj dane transportowe
        tran_file = "in/tran_r_elvehstdefaultview_spreadsheet.xlsx"
        if os.path.exists(tran_file):
            with st.spinner("Wczytywanie danych transportowych..."):
                tran_loader = factory.create_loader('transport')
                st.session_state.tran_data = tran_loader.load(tran_file)
        
        # Sprawdź czy cokolwiek załadowano
        if st.session_state.env_data or st.session_state.tran_data:
            st.session_state.data_loaded = True
            st.success("Dane załadowane pomyślnie!")
            st.rerun()
        else:
            st.error("Nie udało się załadować żadnych danych")
            
    except Exception as e:
        st.error(f"Błąd wczytywania danych: {str(e)}")


def show_environmental_tab():
    """Zakładka z mapą środowiskową"""
    st.header("Pojazdy zutylizowane")
    
    if not st.session_state.data_loaded or not st.session_state.env_data:
        st.warning("Brak danych środowiskowych. Wczytaj dane za pomocą przycisku w sidebarze.")
        return
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        view_mode = st.radio("Widok", ["Europa", "Polska"], key="env_view")
        
        st.subheader("Informacje")
        st.write(f"Liczba krajów: {len(st.session_state.env_data)}")
        
        # Pokaż przykładowe kraje
        if st.session_state.env_data:
            sample_countries = [c.country_name for c in st.session_state.env_data[:5]]
            st.write("Przykładowe kraje:")
            for country in sample_countries:
                st.write(f"- {country}")
    
    with col2:
        st.info("Mapa interaktywna - w implementacji...")
        
        # Placeholder dla mapy
        if st.session_state.env_data:
            # Pokaż dane dla wybranego zakresu lat
            year_range = st.session_state.get('year_range', (2018, 2022))
            st.write(f"Zakres lat: {year_range[0]} - {year_range[1]}")
            
            # Przykładowe dane
            sample_data = []
            for country in st.session_state.env_data[:10]:
                total = country.get_total_for_period(year_range[0], year_range[1])
                sample_data.append({
                    'Kraj': country.country_name,
                    'Suma': f"{total:,.0f}"
                })
            
            st.dataframe(sample_data)


def show_transport_tab():
    """Zakładka z mapą transportową"""
    st.header("Pojazdy elektryczne")
    
    if not st.session_state.data_loaded or not st.session_state.tran_data:
        st.warning("Brak danych transportowych. Wczytaj dane za pomocą przycisku w sidebarze.")
        return
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        view_mode = st.radio("Widok", ["Europa", "Polska"], key="tran_view")
        
        st.subheader("Informacje")
        st.write(f"Liczba regionów: {len(st.session_state.tran_data)}")
        
        # Pokaż kraje
        countries = set(r.country_code for r in st.session_state.tran_data)
        st.write(f"Kraje: {len(countries)}")
        
        # Polskie regiony
        poland_regions = [r for r in st.session_state.tran_data if r.country_code == 'PL']
        st.write(f"Regiony polskie: {len(poland_regions)}")
    
    with col2:
        st.info("Mapa regionów NUTS - w implementacji...")
        
        # Pokaż przykładowe dane polskie
        if view_mode == "Polska":
            poland_regions = [r for r in st.session_state.tran_data if r.country_code == 'PL'][:10]
            
            if poland_regions:
                sample_data = []
                for region in poland_regions:
                    value_2022 = region.get_value_for_year(2022) or 0
                    sample_data.append({
                        'Region': region.region_name,
                        'NUTS': region.nuts_level,
                        '2022': f"{value_2022:,.0f}"
                    })
                
                st.dataframe(sample_data)


def show_analysis_tab():
    """Zakładka z analizą krajów"""
    st.header("Porównanie krajów")
    
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
        
        # Lista krajów w zależności od źródła
        if data_source == "Pojazdy zutylizowane" and st.session_state.env_data:
            available_countries = [c.country_name for c in st.session_state.env_data]
        elif data_source == "Pojazdy elektryczne" and st.session_state.tran_data:
            # Tylko kraje (NUTS level 0)
            countries_set = set()
            for region in st.session_state.tran_data:
                if region.nuts_level <= 1:  # Kraje i regiony główne
                    countries_set.add(region.region_name)
            available_countries = sorted(list(countries_set))
        else:
            available_countries = []
        
        # Wyszukiwanie
        search_term = st.text_input("Szukaj kraju:", key="country_search")
        
        if search_term:
            filtered_countries = [c for c in available_countries 
                                if search_term.lower() in c.lower()]
        else:
            filtered_countries = available_countries
        
        # Wybór krajów
        selected_countries = st.multiselect(
            "Wybierz kraje",
            filtered_countries,
            default=filtered_countries[:3] if filtered_countries else []
        )
        
        # Export do PDF
        if st.button("Eksportuj do PDF"):
            st.success("Export PDF - w implementacji...")
    
    with col2:
        if selected_countries:
            st.subheader(f"Wykres dla: {', '.join(selected_countries)}")
            st.info("Wykres słupkowy - w implementacji...")
            
            # Pokazuj przykładowe dane
            st.write("Wybrane kraje:")
            for country in selected_countries:
                st.write(f"- {country}")
        else:
            st.write("Wybierz kraje aby wygenerować wykres")


if __name__ == "__main__":
    main()
