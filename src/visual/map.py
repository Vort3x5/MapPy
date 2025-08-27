import folium
import pandas as pd
from typing import List, Dict, Any, Union, Optional
import logging
from data.models import CountryData, RegionData
from utils.consts import MAP_CONFIG


class MapVisualizer:
    
    def __init__(self, data_type: str):
        self.data_type = data_type
        self.color_scale = MAP_CONFIG['COLOR_SCALE']
        self.logger = logging.getLogger(__name__)
    
    def create_map(self, data: List[Union[CountryData, RegionData]], 
                   year_range: tuple, view_mode: str = 'Europe') -> folium.Map:
        
        if view_mode == 'Poland':
            center = MAP_CONFIG['POLAND_CENTER']
            zoom = MAP_CONFIG['POLAND_ZOOM']
        else:
            center = MAP_CONFIG['EUROPE_CENTER']
            zoom = MAP_CONFIG['EUROPE_ZOOM']
        
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        map_data = self._prepare_map_data(data, year_range, view_mode)
        
        if map_data.empty:
            self._add_no_data_info(m, center)
            return m
        
        self._add_markers(m, map_data)
        self._add_simple_legend(m, map_data)
        
        return m
    
    def _prepare_map_data(self, data: List[Union[CountryData, RegionData]], 
                         year_range: tuple, view_mode: str) -> pd.DataFrame:
        
        start_year, end_year = year_range
        records = []
        
        skip_names = [
            'european union',
            'euro area', 
            'oecd',
            'world',
            'total',
            '27 countries',
            '28 countries'
        ]
        
        is_poland_mode = view_mode.lower() in ['poland', 'polska']
        
        for item in data:
            name_lower = item.country_name.lower() if isinstance(item, CountryData) else item.region_name.lower()
            if any(skip in name_lower for skip in skip_names):
                continue
            
            if is_poland_mode:
                should_include = False
                
                if isinstance(item, RegionData):
                    if (item.country_code and item.country_code.upper() == 'PL') or \
                       (item.region_code and item.region_code.startswith('PL')):
                        should_include = True
                
                elif isinstance(item, CountryData):
                    poland_variants = ['poland', 'polska', 'republic of poland', 'pol']
                    country_name_lower = item.country_name.lower()
                    country_code_upper = (item.country_code or '').upper()
                    
                    if any(variant in country_name_lower for variant in poland_variants) or \
                       country_code_upper == 'PL':
                        should_include = True
                
                if not should_include:
                    continue
            
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
        
        return pd.DataFrame(records)
    
    def _add_markers(self, m: folium.Map, data: pd.DataFrame):
        
        if data.empty:
            return
        
        max_value = data['value'].max()
        min_value = data['value'].min()
        
        for _, row in data.iterrows():
            coords = self._get_coordinates_from_consts(row['name'])
            
            if coords:
                radius = self._calculate_radius(row['value'], min_value, max_value)
                color = self._get_marker_color(row['value'], min_value, max_value)
                
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
        from utils.consts import COUNTRY_COORDINATES
        
        name_lower = name.lower().strip()
        
        if name_lower in COUNTRY_COORDINATES:
            return COUNTRY_COORDINATES[name_lower]
        
        name_mappings = {
            'polska': 'poland',
            'niemcy': 'germany', 
            'francja': 'france',
            'hiszpania': 'spain',
            'włochy': 'italy',
            'czechy': 'czechia',
            'węgry': 'hungary',
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
        
        if name_lower in name_mappings:
            mapped_name = name_mappings[name_lower]
            if mapped_name in COUNTRY_COORDINATES:
                return COUNTRY_COORDINATES[mapped_name]
        
        for key, coords in COUNTRY_COORDINATES.items():
            if key in name_lower or name_lower in key:
                return coords
        
        return None
    
    def _calculate_radius(self, value: float, min_val: float, max_val: float) -> float:
        if max_val == min_val:
            return 8
        
        normalized = (value - min_val) / (max_val - min_val)
        return 5 + (normalized * 15)
    
    def _get_marker_color(self, value: float, min_val: float, max_val: float) -> str:
        if max_val == min_val:
            return '#ff7f0e'
        
        colors = ['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#b10026']
        normalized = (value - min_val) / (max_val - min_val)
        color_index = min(int(normalized * len(colors)), len(colors) - 1)
        
        return colors[color_index]
    
    def _add_simple_legend(self, m: folium.Map, data: pd.DataFrame):
        if data.empty:
            return
        
        legend_text = f"""
        {self._get_data_type_name()}
        Min: {data['value'].min():,.0f}
        Max: {data['value'].max():,.0f}
        """
        
        try:
            folium.Marker(
                [data['value'].mean(), data['value'].mean()],
                popup=legend_text,
                icon=folium.Icon(color='lightgray', icon='info-sign')
            )
        except:
            pass
    
    def _add_no_data_info(self, m: folium.Map, center: tuple):
        folium.Marker(
            center,
            popup="Brak danych dla wybranych parametrów",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    def _get_data_type_name(self) -> str:
        if self.data_type == 'environmental':
            return "Pojazdy zutylizowane"
        else:
            return "Pojazdy elektryczne"
