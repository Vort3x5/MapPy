# src/visual/map.py
"""Interaktywne mapy z Folium - bez hardkodowanych koordynatów"""

import folium
import pandas as pd
from typing import List, Dict, Any, Union, Optional
import logging
from data.models import CountryData, RegionData
from utils.consts import MAP_CONFIG


class MapVisualizer:
    """Klasa do tworzenia interaktywnych map"""
    
    def __init__(self, data_type: str):
        self.data_type = data_type
        self.color_scale = MAP_CONFIG['COLOR_SCALE']
        self.logger = logging.getLogger(__name__)
    
    def create_map(self, data: List[Union[CountryData, RegionData]], 
                   year_range: tuple, view_mode: str = 'Europe') -> folium.Map:
        """Stwórz mapę z danymi"""
        
        # Określ centrum i zoom
        if view_mode == 'Poland':
            center = MAP_CONFIG['POLAND_CENTER']
            zoom = MAP_CONFIG['POLAND_ZOOM']
        else:
            center = MAP_CONFIG['EUROPE_CENTER']
            zoom = MAP_CONFIG['EUROPE_ZOOM']
        
        # Stwórz mapę
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Przygotuj dane
        map_data = self._prepare_map_data(data, year_range, view_mode)
        
        if map_data.empty:
            self._add_no_data_info(m, center)
            return m
        
        # Dodaj markery
        self._add_markers(m, map_data)
        
        # Dodaj podstawową legendę
        self._add_simple_legend(m, map_data)
        
        return m
    
    def _prepare_map_data(self, data: List[Union[CountryData, RegionData]], 
                         year_range: tuple, view_mode: str) -> pd.DataFrame:
        """Przygotuj dane do mapowania"""
        
        start_year, end_year = year_range
        records = []
        
        # Debug - sprawdź wartość view_mode
        print(f"DEBUG: view_mode = '{view_mode}' (typ: {type(view_mode)})")
        
        # Debug - pokaż pierwsze dane
        print(f"DEBUG: Pierwsze 5 elementów w danych:")
        for i, item in enumerate(data[:5]):
            if isinstance(item, CountryData):
                print(f"  {i+1}. Kraj: '{item.country_name}' (kod: '{item.country_code}')")
            else:
                print(f"  {i+1}. Region: '{item.region_name}' (kraj: '{item.country_code}', kod: '{item.region_code}')")
        
        # Nazwy do pominięcia (agregaty EU)
        skip_names = [
            'european union',
            'euro area', 
            'oecd',
            'world',
            'total',
            '27 countries',
            '28 countries'
        ]
        
        # Sprawdź czy tryb to Polska (różne warianty)
        is_poland_mode = view_mode.lower() in ['poland', 'polska']
        print(f"DEBUG: is_poland_mode = {is_poland_mode}")
        
        for item in data:
            # Pomiń agregaty europejskie
            name_lower = item.country_name.lower() if isinstance(item, CountryData) else item.region_name.lower()
            if any(skip in name_lower for skip in skip_names):
                continue
            
            # Filtrowanie dla trybu Polska
            if is_poland_mode:
                should_include = False
                
                if isinstance(item, RegionData):
                    # Regiony - sprawdź kod kraju
                    if (item.country_code and item.country_code.upper() == 'PL') or \
                       (item.region_code and item.region_code.startswith('PL')):
                        should_include = True
                        print(f"DEBUG: Polski region włączony: {item.region_name}")
                
                elif isinstance(item, CountryData):
                    # Kraje - sprawdź czy to Polska
                    poland_variants = ['poland', 'polska', 'republic of poland', 'pol']
                    country_name_lower = item.country_name.lower()
                    country_code_upper = (item.country_code or '').upper()
                    
                    if any(variant in country_name_lower for variant in poland_variants) or \
                       country_code_upper == 'PL':
                        should_include = True
                        print(f"DEBUG: Polski kraj włączony: {item.country_name}")
                
                if not should_include:
                    print(f"DEBUG: Pomijam (nie polska): {name_lower}")
                    continue
            else:
                # Tryb Europa - włącz wszystko poza agregatami
                print(f"DEBUG: Europa - włączam: {name_lower}")
            
            # Oblicz wartości dla zakresu lat
            values = []
            total = 0
            
            for year in range(start_year, end_year + 1):
                value = item.get_value_for_year(year)
                if value is not None and value > 0:
                    values.append(value)
                    total += value
            
            if values:
                avg_value = sum(values) / len(values)
                latest_value = item.get_value_for_year(end_year) or 0
                
                if isinstance(item, CountryData):
                    records.append({
                        'name': item.country_name,
                        'code': item.country_code,
                        'value': avg_value,
                        'total': total,
                        'latest': latest_value,
                        'type': 'country'
                    })
                else:
                    records.append({
                        'name': item.region_name,
                        'code': item.region_code,
                        'value': avg_value,
                        'total': total,
                        'latest': latest_value,
                        'country_code': item.country_code,
                        'nuts_level': item.nuts_level,
                        'type': 'region'
                    })
        
        print(f"DEBUG: Finalne {len(records)} elementów dla trybu '{view_mode}'")
        if records:
            print("DEBUG: Pierwsze 3 finalne elementy:")
            for i, record in enumerate(records[:3]):
                print(f"  {i+1}. {record['name']} (wartość: {record['value']:.0f})")
        
        return pd.DataFrame(records)

    
    def _add_markers(self, m: folium.Map, data: pd.DataFrame):
        """Dodaj markery na mapę"""
        
        if data.empty:
            return
        
        max_value = data['value'].max()
        min_value = data['value'].min()
        
        for _, row in data.iterrows():
            coords = self._get_coordinates_from_consts(row['name'])
            
            if coords:
                # Rozmiar i kolor markera
                radius = self._calculate_radius(row['value'], min_value, max_value)
                color = self._get_marker_color(row['value'], min_value, max_value)
                
                # Popup z informacjami
                popup_text = f"""
                {row['name']}
                Średnia: {row['value']:,.0f}
                Suma: {row['total']:,.0f}
                Najnowsza: {row['latest']:,.0f}
                """
                
                folium.CircleMarker(
                    location=coords,
                    radius=radius,
                    popup=popup_text,
                    tooltip=f"{row['name']}: {row['value']:,.0f}",
                    color='white',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.7
                ).add_to(m)
    
    def _get_coordinates_from_consts(self, name: str) -> Optional[tuple]:
        """Pobierz współrzędne z pliku consts.py"""
        from utils.consts import COUNTRY_COORDINATES
        
        name_lower = name.lower().strip()
        
        # Szukaj dokładnego dopasowania
        if name_lower in COUNTRY_COORDINATES:
            return COUNTRY_COORDINATES[name_lower]
        
        # Mapowanie alternatywnych nazw
        name_mappings = {
            'polska': 'poland',
            'niemcy': 'germany', 
            'francja': 'france',
            'hiszpania': 'spain',
            'włochy': 'italy',
            'czechy': 'czechia',
            'węgry': 'hungary',
            # Polskie regiony - różne warianty
            'mazovia': 'mazowieckie',
            'silesia': 'śląskie',
            'greater poland': 'wielkopolskie',
            'lesser poland': 'małopolskie',
            'lower silesia': 'dolnośląskie',
            'lodz': 'łódzkie',
            'west pomerania': 'zachodniopomorskie',
            'pomerania': 'pomorskie',
            'warmia-masuria': 'warmińsko-mazurskie',
            'kuyavia-pomerania': 'kujawsko-pomorskie',
            'podlachia': 'podlaskie',
            'lublin': 'lubelskie',
            'subcarpathia': 'podkarpackie',
            'holy cross': 'świętokrzyskie',
            'lubusz': 'lubuskie',
            'opole': 'opolskie'
        }
        
        # Sprawdź mapowania
        if name_lower in name_mappings:
            mapped_name = name_mappings[name_lower]
            if mapped_name in COUNTRY_COORDINATES:
                return COUNTRY_COORDINATES[mapped_name]
        
        # Szukaj częściowego dopasowania
        for key, coords in COUNTRY_COORDINATES.items():
            if key in name_lower or name_lower in key:
                return coords
        
        # Jeśli nie znaleziono, pokaż w debug
        print(f"DEBUG: Nie znaleziono współrzędnych dla '{name}'")
        return None
    
    def _calculate_radius(self, value: float, min_val: float, max_val: float) -> float:
        """Oblicz rozmiar markera"""
        if max_val == min_val:
            return 8
        
        normalized = (value - min_val) / (max_val - min_val)
        return 5 + (normalized * 15)
    
    def _get_marker_color(self, value: float, min_val: float, max_val: float) -> str:
        """Pobierz kolor markera"""
        if max_val == min_val:
            return '#ff7f0e'
        
        colors = ['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#b10026']
        normalized = (value - min_val) / (max_val - min_val)
        color_index = min(int(normalized * len(colors)), len(colors) - 1)
        
        return colors[color_index]

    
    def _add_simple_legend(self, m: folium.Map, data: pd.DataFrame):
        """Dodaj prostą legendę używając Folium"""
        if data.empty:
            return
        
        # Folium ma wbudowaną legendę w Choropleth
        # Dla markerów dodamy prosty opis
        legend_text = f"""
        {self._get_data_type_name()}
        Min: {data['value'].min():,.0f}
        Max: {data['value'].max():,.0f}
        """
        
        # Dodaj jako marker informacyjny w rogu mapy
        try:
            folium.Marker(
                [data['value'].mean(), data['value'].mean()],  # Pozycja poza widokiem
                popup=legend_text,
                icon=folium.Icon(color='lightgray', icon='info-sign')
            )
        except:
            pass  # Jeśli nie działa, pomiń legendę
    
    def _add_no_data_info(self, m: folium.Map, center: tuple):
        """Dodaj informację o braku danych"""
        folium.Marker(
            center,
            popup="Brak danych dla wybranych parametrów",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    def _get_data_type_name(self) -> str:
        """Nazwa typu danych"""
        if self.data_type == 'environmental':
            return "Pojazdy zutylizowane"
        else:
            return "Pojazdy elektryczne"
