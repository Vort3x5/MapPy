# src/visualization/map_viz.py
"""Interaktywne mapy z Folium"""

import folium
import pandas as pd
from typing import List, Dict, Any, Union
import logging
import requests
import json
from data.models import CountryData, RegionData
from utils.consts import MAP_CONFIG


class MapVisualizer:
    """Główna klasa do tworzenia interaktywnych map"""
    
    def __init__(self, data_type: str):
        self.data_type = data_type  # 'environmental' lub 'transport'
        self.color_scale = MAP_CONFIG['COLOR_SCALE']
    
    def create_map(self, data: List[Union[CountryData, RegionData]], 
                   year_range: tuple, view_mode: str = 'Europe') -> folium.Map:
        """Stwórz interaktywną mapę choropleth"""
        
        # Określ centrum i zoom mapy
        if view_mode == 'Poland':
            center = MAP_CONFIG['POLAND_CENTER']
            zoom = MAP_CONFIG['POLAND_ZOOM']
        else:
            center = MAP_CONFIG['EUROPE_CENTER']
            zoom = MAP_CONFIG['EUROPE_ZOOM']
        
        # Inicjalizuj mapę
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Przygotuj dane do mapowania
        map_data = self._prepare_map_data(data, year_range, view_mode)
        
        if not map_data.empty:
            # Dodaj warstwę choropleth lub markery
            if self._should_use_choropleth(view_mode):
                self._add_choropleth_layer(m, map_data, view_mode)
            else:
                self._add_circle_markers(m, map_data)
            
            # Dodaj legendę
            self._add_legend(m, map_data)
        else:
            # Dodaj informację o braku danych
            folium.Marker(
                center,
                popup="Brak danych dla wybranego zakresu",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        return m
    
    def _prepare_map_data(self, data: List[Union[CountryData, RegionData]], 
                         year_range: tuple, view_mode: str) -> pd.DataFrame:
        """Przygotuj i agreguj dane do mapowania"""
        start_year, end_year = year_range
        map_records = []
        
        for item in data:
            # Filtruj dla Polski jeśli potrzeba
            if view_mode == 'Poland':
                if isinstance(item, RegionData) and item.country_code != 'PL':
                    continue
                elif isinstance(item, CountryData) and item.country_name != 'Poland':
                    continue
            
            # Oblicz średnią wartość dla zakresu lat
            values = []
            total = 0
            latest_value = 0
            
            for year in range(start_year, end_year + 1):
                value = item.get_value_for_year(year)
                if value is not None and value > 0:
                    values.append(value)
                    total += value
                    if year == end_year:
                        latest_value = value
            
            if values:
                avg_value = sum(values) / len(values)
                
                if isinstance(item, CountryData):
                    map_records.append({
                        'id': item.country_code,
                        'name': item.country_name,
                        'value': avg_value,
                        'total': total,
                        'latest': latest_value,
                        'type': 'country'
                    })
                else:  # RegionData
                    map_records.append({
                        'id': item.region_code,
                        'name': item.region_name,
                        'value': avg_value,
                        'total': total,
                        'latest': latest_value,
                        'country_code': item.country_code,
                        'nuts_level': item.nuts_level,
                        'type': 'region'
                    })
        
        return pd.DataFrame(map_records)
    
    def _should_use_choropleth(self, view_mode: str) -> bool:
        """Określ czy użyć choropleth czy markerów"""
        # Dla krajów używamy choropleth jeśli mamy dostęp do GeoJSON
        # Dla regionów NUTS - też choropleth jeśli możliwe
        # W przeciwnym przypadku - markery kolorowe
        return self.data_type == 'environmental' and view_mode == 'Europe'
    
    def _add_choropleth_layer(self, m: folium.Map, data: pd.DataFrame, view_mode: str):
        """Dodaj warstwę choropleth do mapy"""
        try:
            # Pobierz dane geograficzne
            if self.data_type == 'environmental':
                geo_data = self._get_country_geojson()
                key_on = 'feature.properties.ISO_A2'
                columns = ['id', 'value']
            else:
                geo_data = self._get_nuts_geojson(view_mode)
                key_on = 'feature.properties.NUTS_ID'
                columns = ['id', 'value']
            
            # Stwórz choropleth
            choropleth = folium.Choropleth(
                geo_data=geo_data,
                data=data,
                columns=columns,
                key_on=key_on,
                fill_color=self.color_scale,
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name=self._get_legend_name(),
                highlight=True,
                nan_fill_color='lightgray',
                nan_fill_opacity=0.3
            )
            
            choropleth.add_to(m)
            
            # Dodaj tooltips z danymi
            self._add_choropleth_tooltips(m, choropleth, data)
            
        except Exception as e:
            logging.warning(f"Choropleth failed: {e}, falling back to markers")
            self._add_circle_markers(m, data)
    
    def _add_circle_markers(self, m: folium.Map, data: pd.DataFrame):
        """Dodaj kolorowe markery kołowe jako fallback"""
        if data.empty:
            return
        
        max_value = data['value'].max()
        min_value = data['value'].min()
        
        for _, row in data.iterrows():
            # Współrzędne na podstawie nazwy/kodu
            coords = self._get_coordinates(row['name'], row.get('id', ''))
            
            if coords:
                # Rozmiar proporcjonalny do wartości
                radius = self._calculate_marker_size(row['value'], min_value, max_value)
                color = self._get_color_for_value(row['value'], min_value, max_value)
                
                # Tekst popup
                popup_text = self._create_popup_text(row)
                
                folium.CircleMarker(
                    location=coords,
                    radius=radius,
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"{row['name']}: {row['value']:,.0f}",
                    color='white',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.8
                ).add_to(m)
    
    def _get_country_geojson(self) -> dict:
        """Pobierz dane GeoJSON dla krajów europejskich"""
        try:
            # Użyj uproszczonych granic krajów z Natural Earth
            url = "https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson"
            response = requests.get(url, timeout=10)
            geojson_data = response.json()
            
            # Filtruj tylko kraje europejskie
            european_countries = {
                'PL', 'DE', 'FR', 'ES', 'IT', 'BE', 'NL', 'AT', 'DK', 'SE', 
                'FI', 'NO', 'CZ', 'SK', 'HU', 'SI', 'HR', 'RO', 'BG', 'LT', 
                'LV', 'EE', 'PT', 'GR', 'IE', 'GB'
            }
            
            filtered_features = []
            for feature in geojson_data['features']:
                country_code = feature['properties'].get('ISO_A2', '')
                if country_code in european_countries:
                    filtered_features.append(feature)
            
            return {
                'type': 'FeatureCollection',
                'features': filtered_features
            }
            
        except Exception as e:
            logging.error(f"Error loading country GeoJSON: {e}")
            return self._get_fallback_country_geojson()
    
    def _get_nuts_geojson(self, view_mode: str) -> dict:
        """Pobierz dane GeoJSON dla regionów NUTS"""
        try:
            if view_mode == 'Poland':
                # Regiony polskie NUTS
                url = "https://raw.githubusercontent.com/ppatrzyk/data/master/poland-nuts/nuts-2.geojson"
            else:
                # Wszystkie regiony europejskie (duży plik!)
                url = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2021_3035_LEVL_2.geojson"
            
            response = requests.get(url, timeout=30)
            return response.json()
            
        except Exception as e:
            logging.error(f"Error loading NUTS GeoJSON: {e}")
            return self._get_fallback_nuts_geojson()
    
    def _get_fallback_country_geojson(self) -> dict:
        """Fallback GeoJSON z podstawowymi krajami"""
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ISO_A2": "PL", "NAME": "Poland"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[14.0, 49.0], [24.0, 49.0], [24.0, 55.0], [14.0, 55.0], [14.0, 49.0]]]
                    }
                },
                {
                    "type": "Feature", 
                    "properties": {"ISO_A2": "DE", "NAME": "Germany"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[5.5, 47.0], [15.5, 47.0], [15.5, 55.5], [5.5, 55.5], [5.5, 47.0]]]
                    }
                }
            ]
        }
    
    def _get_fallback_nuts_geojson(self) -> dict:
        """Fallback GeoJSON dla regionów NUTS"""
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"NUTS_ID": "PL12", "NAME": "Mazowieckie"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[19.0, 51.0], [23.0, 51.0], [23.0, 53.5], [19.0, 53.5], [19.0, 51.0]]]
                    }
                }
            ]
        }
    
    def _add_choropleth_tooltips(self, m: folium.Map, choropleth, data: pd.DataFrame):
        """Dodaj tooltips do warstwy choropleth"""
        # Dodaj tooltips z szczegółowymi danymi
        for _, row in data.iterrows():
            coords = self._get_coordinates(row['name'], row.get('id', ''))
            if coords:
                tooltip_text = f"<b>{row['name']}</b><br/>Wartość: {row['value']:,.0f}"
                
                folium.CircleMarker(
                    location=coords,
                    radius=0.1,
                    tooltip=tooltip_text,
                    opacity=0,
                    fillOpacity=0
                ).add_to(m)
    
    def _get_coordinates(self, name: str, code: str = '') -> tuple:
        """Pobierz współrzędne dla lokalizacji"""
        # Mapa współrzędnych głównych krajów i regionów
        coords_map = {
            # Kraje
            'Poland': (51.9, 19.1),
            'Germany': (51.2, 10.4),
            'Belgium': (50.8, 4.3),
            'France': (46.6, 2.2),
            'Spain': (40.4, -3.7),
            'Italy': (41.9, 12.6),
            'Netherlands': (52.1, 5.3),
            'Austria': (47.5, 14.6),
            'Denmark': (56.3, 9.5),
            'Sweden': (60.1, 18.6),
            'Finland': (61.9, 25.7),
            'Norway': (60.5, 8.5),
            'Czech Republic': (49.8, 15.5),
            'Czechia': (49.8, 15.5),
            'Slovakia': (48.7, 19.7),
            'Hungary': (47.2, 19.5),
            'Slovenia': (46.1, 14.8),
            'Croatia': (45.1, 15.2),
            'Romania': (45.9, 24.6),
            'Bulgaria': (42.8, 25.5),
            'Lithuania': (55.2, 23.9),
            'Latvia': (56.9, 24.6),
            'Estonia': (58.6, 25.0),
            'Portugal': (39.4, -8.2),
            'Greece': (39.1, 21.8),
            'Ireland': (53.1, -7.7),
            
            # Polskie regiony (NUTS 2)
            'Mazowieckie': (52.4, 21.0),
            'Śląskie': (50.2, 19.0),
            'Wielkopolskie': (52.4, 17.0),
            'Małopolskie': (50.1, 20.0),
            'Dolnośląskie': (51.1, 16.3),
            'Łódzkie': (51.8, 19.5),
            'Zachodniopomorskie': (53.4, 15.6),
            'Pomorskie': (54.2, 18.6),
            'Warmińsko-mazurskie': (54.0, 20.5),
            'Kujawsko-pomorskie': (53.0, 18.6),
            'Podlaskie': (53.1, 23.2),
            'Lubelskie': (51.2, 22.9),
            'Podkarpackie': (49.6, 22.0),
            'Świętokrzyskie': (50.6, 20.6),
            'Lubuskie': (52.0, 15.2),
            'Opolskie': (50.5, 17.9)
        }
        
        # Szukaj po nazwie
        if name in coords_map:
            return coords_map[name]
        
        # Szukaj po częściowej nazwie
        for key, coords in coords_map.items():
            if key.lower() in name.lower() or name.lower() in key.lower():
                return coords
        
        # Domyślnie centrum Europy
        return (54.5, 15.2)
    
    def _calculate_marker_size(self, value: float, min_val: float, max_val: float) -> float:
        """Oblicz rozmiar markera na podstawie wartości"""
        if max_val == min_val:
            return 10
        
        # Skaluj między 5 a 30 pikseli
        normalized = (value - min_val) / (max_val - min_val)
        return 5 + (normalized * 25)
    
    def _get_color_for_value(self, value: float, min_val: float, max_val: float) -> str:
        """Pobierz kolor dla wartości"""
        if max_val == min_val:
            return '#ff7f0e'
        
        # Paleta kolorów YlOrRd
        colors = ['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#b10026']
        
        normalized = (value - min_val) / (max_val - min_val)
        color_index = int(normalized * (len(colors) - 1))
        
        return colors[color_index]
    
    def _create_popup_text(self, row: pd.Series) -> str:
        """Stwórz tekst popup dla markera"""
        popup_html = f"""
        <div style='min-width: 200px'>
            <h4>{row['name']}</h4>
            <b>Średnia wartość:</b> {row['value']:,.0f}<br/>
            <b>Suma całkowita:</b> {row['total']:,.0f}<br/>
            <b>Najnowsza wartość:</b> {row['latest']:,.0f}<br/>
        """
        
        if row.get('type') == 'region':
            popup_html += f"<b>Kraj:</b> {row['country_code']}<br/>"
            popup_html += f"<b>Poziom NUTS:</b> {row['nuts_level']}<br/>"
        
        popup_html += f"""
            <b>Typ danych:</b> {self._get_data_type_name()}
        </div>
        """
        
        return popup_html
    
    def _add_legend(self, m: folium.Map, data: pd.DataFrame):
        """Dodaj legendę do mapy"""
        if data.empty:
            return
        
        min_val = data['value'].min()
        max_val = data['value'].max()
        
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 160px; height: 110px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px; border-radius: 5px;">
        <h4 style="margin: 0 0 10px 0;">{self._get_legend_name()}</h4>
        <i style="background: #ffffb2; width: 20px; height: 10px; display: inline-block;"></i> 
        <span>Niskie ({min_val:,.0f})</span><br/>
        <i style="background: #fd8d3c; width: 20px; height: 10px; display: inline-block;"></i> 
        <span>Średnie</span><br/>
        <i style="background: #b10026; width: 20px; height: 10px; display: inline-block;"></i> 
        <span>Wysokie ({max_val:,.0f})</span><br/>
        <br/><small>Kliknij obszar aby zobaczyć szczegóły</small>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
    
    def _get_legend_name(self) -> str:
        """Pobierz nazwę dla legendy"""
        if self.data_type == 'environmental':
            return "Pojazdy zutylizowane"
        else:
            return "Pojazdy elektryczne"
    
    def _get_data_type_name(self) -> str:
        """Pobierz czytelną nazwę typu danych"""
        if self.data_type == 'environmental':
            return "Utylizacja pojazdów"
        else:
            return "Pojazdy elektryczne"
