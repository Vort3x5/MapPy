from abc import ABC, abstractmethod
from typing import List, Any, Dict, Union
import logging
from data.models import CountryData, RegionData


class Observer(ABC):
    """Abstrakcyjna klasa observera - Observer Pattern"""
    
    @abstractmethod
    def update(self, subject: 'Subject', event_type: str, data: Any):
        """Reakcja na zmianę w subject"""
        pass


class Subject(ABC):
    """Abstrakcyjna klasa subject - Observer Pattern"""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer):
        """Dodaj observer do listy"""
        if observer not in self._observers:
            self._observers.append(observer)
            logging.debug(f"Observer {observer} attached")
    
    def detach(self, observer: Observer):
        """Usuń observer z listy"""
        if observer in self._observers:
            self._observers.remove(observer)
            logging.debug(f"Observer {observer} detached")
    
    def notify(self, event_type: str, data: Any = None):
        """Powiadom wszystkich observerów o zmianie"""
        logging.debug(f"Notifying {len(self._observers)} observers about {event_type}")
        for observer in self._observers:
            try:
                observer.update(self, event_type, data)
            except Exception as e:
                logging.error(f"Error notifying observer {observer}: {e}")


class DataObserver(Observer):
    """Konkretny observer do reagowania na zmiany danych"""
    
    def __init__(self, name: str, callback=None):
        self.name = name
        self.callback = callback  # Opcjonalna funkcja callback
    
    def update(self, subject: Subject, event_type: str, data: Any):
        """Zareaguj na zmianę danych"""
        message = f"{self.name} received {event_type}"
        if data:
            message += f" with data: {data}"
        
        logging.info(message)
        
        # Wywołaj callback jeśli istnieje
        if self.callback:
            try:
                self.callback(event_type, data)
            except Exception as e:
                logging.error(f"Error in callback for {self.name}: {e}")


class UIComponentObserver(Observer):
    """Observer dla komponentów UI (mapy, wykresy, tabele)"""
    
    def __init__(self, component_name: str, refresh_function=None):
        self.component_name = component_name
        self.refresh_function = refresh_function
        self.last_update_data = None
    
    def update(self, subject: Subject, event_type: str, data: Any):
        """Odśwież komponent UI przy zmianie danych"""
        # Zapisz dane z ostatniej aktualizacji
        self.last_update_data = {
            'event_type': event_type,
            'data': data,
            'timestamp': subject.get_timestamp() if hasattr(subject, 'get_timestamp') else None
        }
        
        # Wywołaj funkcję odświeżającą jeśli istnieje
        if self.refresh_function:
            try:
                self.refresh_function(event_type, data)
            except Exception as e:
                logging.error(f"Error refreshing {self.component_name}: {e}")
        
        logging.info(f"UI component {self.component_name} updated for {event_type}")


class DataManager(Subject):
    """Główny manager danych - Subject w Observer Pattern"""
    
    def __init__(self):
        super().__init__()
        self.env_data: List[CountryData] = []
        self.tran_data: List[RegionData] = []
        self.year_range: tuple = (2018, 2022)
        self.selected_countries: List[str] = []
        self.selected_regions: List[str] = []
        self.data_filter: Dict[str, Any] = {}
        self._timestamp = None
        
    def load_environmental_data(self, data: List[CountryData]):
        """Załaduj dane środowiskowe i powiadom observerów"""
        self.env_data = data
        self._update_timestamp()
        self.notify('env_data_loaded', {
            'count': len(data),
            'countries': [c.country_name for c in data[:5]]  # Pierwsze 5 jako przykład
        })
    
    def load_transport_data(self, data: List[RegionData]):
        """Załaduj dane transportowe i powiadom observerów"""
        self.tran_data = data
        self._update_timestamp()
        
        # Przygotuj statystyki do powiadomienia
        countries = set(r.country_code for r in data)
        nuts_levels = set(r.nuts_level for r in data)
        
        self.notify('tran_data_loaded', {
            'count': len(data),
            'countries': len(countries),
            'nuts_levels': sorted(list(nuts_levels))
        })
    
    def set_year_range(self, year_range: tuple):
        """Ustaw zakres lat i powiadom observerów"""
        old_range = self.year_range
        self.year_range = year_range
        self._update_timestamp()
        
        self.notify('year_range_changed', {
            'old_range': old_range,
            'new_range': year_range,
            'span': year_range[1] - year_range[0] + 1
        })
    
    def set_selected_countries(self, countries: List[str]):
        """Ustaw wybrane kraje i powiadom observerów"""
        old_selection = self.selected_countries.copy()
        self.selected_countries = countries
        self._update_timestamp()
        
        self.notify('countries_selected', {
            'old_selection': old_selection,
            'new_selection': countries,
            'count': len(countries)
        })
    
    def set_selected_regions(self, regions: List[str]):
        """Ustaw wybrane regiony i powiadom observerów"""
        old_selection = self.selected_regions.copy()
        self.selected_regions = regions
        self._update_timestamp()
        
        self.notify('regions_selected', {
            'old_selection': old_selection,
            'new_selection': regions,
            'count': len(regions)
        })
    
    def apply_filter(self, filter_criteria: Dict[str, Any]):
        """Zastosuj filtr danych i powiadom observerów"""
        old_filter = self.data_filter.copy()
        self.data_filter.update(filter_criteria)
        self._update_timestamp()
        
        self.notify('filter_applied', {
            'old_filter': old_filter,
            'new_filter': self.data_filter,
            'criteria': filter_criteria
        })
    
    def clear_filters(self):
        """Wyczyść wszystkie filtry"""
        old_filter = self.data_filter.copy()
        self.data_filter = {}
        self._update_timestamp()
        
        self.notify('filters_cleared', {
            'old_filter': old_filter
        })
    
    def get_filtered_env_data(self) -> List[CountryData]:
        """Pobierz przefiltrowane dane środowiskowe"""
        filtered_data = self.env_data
        
        # Filtruj po wybranych krajach
        if self.selected_countries:
            filtered_data = [c for c in filtered_data if c.country_name in self.selected_countries]
        
        return filtered_data
    
    def get_filtered_tran_data(self) -> List[RegionData]:
        """Pobierz przefiltrowane dane transportowe"""
        filtered_data = self.tran_data
        
        # Filtruj po wybranych regionach
        if self.selected_regions:
            filtered_data = [r for r in filtered_data if r.region_name in self.selected_regions]
        
        # Filtruj po innych kryteriach z data_filter
        if 'country_code' in self.data_filter:
            country_code = self.data_filter['country_code'].upper()
            filtered_data = [r for r in filtered_data if r.country_code == country_code]
        
        if 'nuts_level' in self.data_filter:
            nuts_level = self.data_filter['nuts_level']
            filtered_data = [r for r in filtered_data if r.nuts_level == nuts_level]
        
        return filtered_data
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Pobierz statystyki podsumowujące"""
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
    
    def get_timestamp(self):
        """Pobierz timestamp ostatniej aktualizacji"""
        return self._timestamp
    
    def _update_timestamp(self):
        """Zaktualizuj timestamp"""
        import time
        self._timestamp = time.time()


class StreamlitObserverBridge:
    """Klasa pomocnicza do integracji Observer Pattern ze Streamlit"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.component_observers = {}
    
    def register_component(self, component_name: str, refresh_callback=None):
        """Zarejestruj komponent UI jako observer"""
        observer = UIComponentObserver(component_name, refresh_callback)
        self.data_manager.attach(observer)
        self.component_observers[component_name] = observer
        return observer
    
    def unregister_component(self, component_name: str):
        """Wyrejestruj komponent UI"""
        if component_name in self.component_observers:
            observer = self.component_observers[component_name]
            self.data_manager.detach(observer)
            del self.component_observers[component_name]
    
    def get_component_last_update(self, component_name: str):
        """Pobierz dane z ostatniej aktualizacji komponentu"""
        if component_name in self.component_observers:
            return self.component_observers[component_name].last_update_data
        return None
    
    def trigger_component_refresh(self, component_name: str, force_data=None):
        """Wymuś odświeżenie konkretnego komponentu"""
        if component_name in self.component_observers:
            observer = self.component_observers[component_name]
            observer.update(self.data_manager, 'manual_refresh', force_data)


# Przykład użycia w Streamlit
class StreamlitComponentCallbacks:
    """Przykładowe callback functions dla komponentów Streamlit"""
    
    @staticmethod
    def map_refresh_callback(event_type: str, data: Any):
        """Callback do odświeżania mapy"""
        import streamlit as st
        
        if event_type in ['year_range_changed', 'countries_selected', 'filter_applied']:
            # W rzeczywistym użyciu - tutaj byłoby odświeżanie mapy
            if hasattr(st, 'rerun'):
                # Streamlit 1.18+ 
                st.rerun()
            else:
                # Starsze wersje Streamlit
                st.experimental_rerun()
    
    @staticmethod
    def chart_refresh_callback(event_type: str, data: Any):
        """Callback do odświeżania wykresów"""
        import streamlit as st
        
        if event_type in ['year_range_changed', 'countries_selected']:
            # Podobnie - odświeżanie wykresów
            if hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.experimental_rerun()
    
    @staticmethod
    def table_refresh_callback(event_type: str, data: Any):
        """Callback do odświeżania tabel"""
        # W rzeczywistym użyciu - aktualizacja danych w tabeli
        logging.info(f"Table refresh triggered by {event_type}")
        pass
