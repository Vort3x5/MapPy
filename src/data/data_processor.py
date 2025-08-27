from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from .models import CountryData, RegionData


class DataProcessingStrategy(ABC):
    
    @abstractmethod
    def process(self, data: List[Union[CountryData, RegionData]], 
                year_range: tuple, **kwargs) -> Dict[str, Any]:
        pass


class CountryAggregationStrategy(DataProcessingStrategy):
    
    def process(self, data: List[CountryData], year_range: tuple, 
                **kwargs) -> Dict[str, Any]:
        start_year, end_year = year_range
        result = {
            'countries': [],
            'values': [],
            'years': list(range(start_year, end_year + 1)),
            'totals': [],
            'averages': []
        }
        
        for country in data:
            country_values = []
            for year in result['years']:
                value = country.get_value_for_year(year)
                country_values.append(value if value is not None else 0)
            
            if any(v > 0 for v in country_values):
                result['countries'].append(country.country_name)
                result['values'].append(country_values)
                result['totals'].append(sum(country_values))
                result['averages'].append(sum(country_values) / len([v for v in country_values if v > 0]) 
                                        if any(v > 0 for v in country_values) else 0)
        
        return result


class RegionAggregationStrategy(DataProcessingStrategy):
    
    def process(self, data: List[RegionData], year_range: tuple,
                country_filter: str = None, nuts_level: int = None, **kwargs) -> Dict[str, Any]:
        start_year, end_year = year_range
        filtered_data = data
        
        if country_filter:
            filtered_data = [r for r in filtered_data if r.country_code == country_filter.upper()]
        
        if nuts_level is not None:
            filtered_data = [r for r in filtered_data if r.nuts_level == nuts_level]
        
        result = {
            'regions': [],
            'values': [],
            'years': list(range(start_year, end_year + 1)),
            'country_codes': [],
            'nuts_levels': [],
            'totals': [],
            'averages': []
        }
        
        for region in filtered_data:
            region_values = []
            for year in result['years']:
                value = region.get_value_for_year(year)
                region_values.append(value if value is not None else 0)
            
            if any(v > 0 for v in region_values):
                result['regions'].append(region.region_name)
                result['values'].append(region_values)
                result['country_codes'].append(region.country_code)
                result['nuts_levels'].append(region.nuts_level)
                result['totals'].append(sum(region_values))
                result['averages'].append(sum(region_values) / len([v for v in region_values if v > 0]) 
                                        if any(v > 0 for v in region_values) else 0)
        
        return result


class DataProcessor:
    
    def __init__(self, strategy: DataProcessingStrategy):
        self.strategy = strategy
    
    def set_strategy(self, strategy: DataProcessingStrategy):
        self.strategy = strategy
    
    def process_data(self, data: List[Union[CountryData, RegionData]], 
                    year_range: tuple, **kwargs) -> Dict[str, Any]:
        return self.strategy.process(data, year_range, **kwargs)
