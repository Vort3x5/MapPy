from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
import pandas as pd
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


class TopNStrategy(DataProcessingStrategy):
    
    def __init__(self, n: int = 10, sort_by: str = 'total'):
        self.n = n
        self.sort_by = sort_by  # 'total', 'average', 'latest'
    
    def process(self, data: List[Union[CountryData, RegionData]], 
                year_range: tuple, **kwargs) -> Dict[str, Any]:
        start_year, end_year = year_range
        
        items_with_metrics = []
        
        for item in data:
            values = []
            for year in range(start_year, end_year + 1):
                value = item.get_value_for_year(year)
                if value is not None and value > 0:
                    values.append(value)
            
            if values:
                total = sum(values)
                average = total / len(values)
                latest = item.get_value_for_year(end_year) or 0
                
                items_with_metrics.append({
                    'item': item,
                    'total': total,
                    'average': average,
                    'latest': latest,
                    'values': values
                })
        
        sorted_items = sorted(items_with_metrics, 
                            key=lambda x: x[self.sort_by], 
                            reverse=True)[:self.n]
        
        result = {
            'items': [],
            'names': [],
            'values': [],
            'years': list(range(start_year, end_year + 1)),
            'totals': [],
            'averages': [],
            'sort_criterion': self.sort_by
        }
        
        for item_data in sorted_items:
            item = item_data['item']
            name = item.country_name if isinstance(item, CountryData) else item.region_name
            
            full_values = []
            for year in result['years']:
                value = item.get_value_for_year(year)
                full_values.append(value if value is not None else 0)
            
            result['items'].append(item)
            result['names'].append(name)
            result['values'].append(full_values)
            result['totals'].append(item_data['total'])
            result['averages'].append(item_data['average'])
        
        return result


class DataProcessor:
    
    def __init__(self, strategy: DataProcessingStrategy):
        self.strategy = strategy
    
    def set_strategy(self, strategy: DataProcessingStrategy):
        self.strategy = strategy
    
    def process_data(self, data: List[Union[CountryData, RegionData]], 
                    year_range: tuple, **kwargs) -> Dict[str, Any]:
        return self.strategy.process(data, year_range, **kwargs)


class DataAggregator:
    
    @staticmethod
    def aggregate_by_country(regions: List[RegionData], year_range: tuple) -> Dict[str, Any]:
        start_year, end_year = year_range
        country_totals = {}
        
        for region in regions:
            country = region.country_code
            if country not in country_totals:
                country_totals[country] = {
                    'name': country,
                    'values_by_year': {year: 0 for year in range(start_year, end_year + 1)},
                    'regions_count': 0
                }
            
            country_totals[country]['regions_count'] += 1
            
            for year in range(start_year, end_year + 1):
                value = region.get_value_for_year(year)
                if value is not None:
                    country_totals[country]['values_by_year'][year] += value
        
        result = {
            'countries': [],
            'values': [],
            'years': list(range(start_year, end_year + 1)),
            'regions_count': []
        }
        
        for country_code, data in country_totals.items():
            result['countries'].append(country_code)
            result['regions_count'].append(data['regions_count'])
            
            country_values = [data['values_by_year'][year] for year in result['years']]
            result['values'].append(country_values)
        
        return result
    
    @staticmethod
    def get_time_series_data(items: List[Union[CountryData, RegionData]], 
                           year_range: tuple) -> pd.DataFrame:
        start_year, end_year = year_range
        years = list(range(start_year, end_year + 1))
        
        # Przygotuj dane w formacie long
        data_rows = []
        
        for item in items:
            name = item.country_name if isinstance(item, CountryData) else item.region_name
            
            for year in years:
                value = item.get_value_for_year(year)
                if value is not None and value > 0:
                    data_rows.append({
                        'name': name,
                        'year': year,
                        'value': value,
                        'type': 'country' if isinstance(item, CountryData) else 'region'
                    })
        
        return pd.DataFrame(data_rows)
