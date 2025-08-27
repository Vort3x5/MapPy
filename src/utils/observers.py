# src/utils/observers.py
"""Uproszczony Observer Pattern"""

from abc import ABC, abstractmethod
from typing import List, Any, Dict
import logging
from data.models import CountryData, RegionData


class Observer(ABC):
    """Abstrakcyjna klasa observer"""
    
    @abstractmethod
    def update(self, subject: 'Subject', event_type: str, data: Any):
        pass


class Subject(ABC):
    """Abstrakcyjna klasa subject"""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer):
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event_type: str, data: Any = None):
        for observer in self._observers:
            try:
                observer.update(self, event_type, data)
            except Exception as e:
                logging.error(f"Error notifying observer: {e}")


class DataObserver(Observer):
    """Prosty observer do reagowania na zmiany danych"""
    
    def __init__(self, name: str, callback=None):
        self.name = name
        self.callback = callback
    
    def update(self, subject: Subject, event_type: str, data: Any):
        logging.info(f"{self.name} received {event_type}")
        
        if self.callback:
            try:
                self.callback(event_type, data)
            except Exception as e:
                logging.error(f"Error in callback: {e}")


class DataManager(Subject):
    """Główny manager danych - implementuje Subject"""
    
    def __init__(self):
        super().__init__()
        self.env_data: List[CountryData] = []
        self.tran_data: List[RegionData] = []
        self.year_range: tuple = (2018, 2022)
        self.selected_countries: List[str] = []
        self.selected_regions: List[str] = []
        self.data_filter: Dict[str, Any] = {}
    
    def load_environmental_data(self, data: List[CountryData]):
        self.env_data = data
        self.notify('env_data_loaded', {'count': len(data)})
    
    def load_transport_data(self, data: List[RegionData]):
        self.tran_data = data
        countries = set(r.country_code for r in data)
        self.notify('tran_data_loaded', {'count': len(data), 'countries': len(countries)})
    
    def set_year_range(self, year_range: tuple):
        old_range = self.year_range
        self.year_range = year_range
        self.notify('year_range_changed', {'old_range': old_range, 'new_range': year_range})
    
    def set_selected_countries(self, countries: List[str]):
        old_selection = self.selected_countries.copy()
        self.selected_countries = countries
        self.notify('countries_selected', {'old_selection': old_selection, 'new_selection': countries})
    
    def set_selected_regions(self, regions: List[str]):
        old_selection = self.selected_regions.copy()
        self.selected_regions = regions
        self.notify('regions_selected', {'old_selection': old_selection, 'new_selection': regions})
    
    def apply_filter(self, filter_criteria: Dict[str, Any]):
        old_filter = self.data_filter.copy()
        self.data_filter.update(filter_criteria)
        self.notify('filter_applied', {'old_filter': old_filter, 'new_filter': self.data_filter})
    
    def clear_filters(self):
        old_filter = self.data_filter.copy()
        self.data_filter = {}
        self.notify('filters_cleared', {'old_filter': old_filter})
    
    def get_filtered_env_data(self) -> List[CountryData]:
        filtered_data = self.env_data
        if self.selected_countries:
            filtered_data = [c for c in filtered_data if c.country_name in self.selected_countries]
        return filtered_data
    
    def get_filtered_tran_data(self) -> List[RegionData]:
        filtered_data = self.tran_data
        
        if self.selected_regions:
            filtered_data = [r for r in filtered_data if r.region_name in self.selected_regions]
        
        if 'country_code' in self.data_filter:
            country_code = self.data_filter['country_code'].upper()
            filtered_data = [r for r in filtered_data if r.country_code == country_code]
        
        if 'nuts_level' in self.data_filter:
            nuts_level = self.data_filter['nuts_level']
            filtered_data = [r for r in filtered_data if r.nuts_level == nuts_level]
        
        return filtered_data
    
    def get_summary_stats(self) -> Dict[str, Any]:
        env_filtered = self.get_filtered_env_data()
        tran_filtered = self.get_filtered_tran_data()
        
        return {
            'env_countries_total': len(self.env_data),
            'env_countries_filtered': len(env_filtered),
            'tran_regions_total': len(self.tran_data),
            'tran_regions_filtered': len(tran_filtered),
            'year_range': self.year_range,
            'selected_countries': self.selected_countries,
            'selected_regions': self.selected_regions,
            'active_filters': self.data_filter
        }


class StreamlitObserverBridge:
    """Prosta klasa do integracji Observer Pattern ze Streamlit"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.component_observers = {}
    
    def register_component(self, component_name: str, refresh_callback=None):
        observer = DataObserver(component_name, refresh_callback)
        self.data_manager.attach(observer)
        self.component_observers[component_name] = observer
        return observer
    
    def unregister_component(self, component_name: str):
        if component_name in self.component_observers:
            observer = self.component_observers[component_name]
            self.data_manager.detach(observer)
            del self.component_observers[component_name]
