from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CountryData:
    country_code: str
    country_name: str
    data_by_year: Dict[int, float]
    data_type: str = 'environmental'
    
    def get_value_for_year(self, year: int) -> Optional[float]:
        return self.data_by_year.get(year)
    
    def get_year_range(self) -> tuple:
        if not self.data_by_year:
            return (None, None)
        years = list(self.data_by_year.keys())
        return (min(years), max(years))
    
    def get_total_for_period(self, start_year: int, end_year: int) -> float:
        total = 0.0
        for year in range(start_year, end_year + 1):
            value = self.get_value_for_year(year)
            if value is not None:
                total += value
        return total


@dataclass
class RegionData:
    region_code: str
    region_name: str
    country_code: str
    nuts_level: int
    data_by_year: Dict[int, float]
    
    def get_value_for_year(self, year: int) -> Optional[float]:
        return self.data_by_year.get(year)
    
    def is_country_level(self) -> bool:
        return self.nuts_level == 0
    
    def get_year_range(self) -> tuple:
        if not self.data_by_year:
            return (None, None)
        years = list(self.data_by_year.keys())
        return (min(years), max(years))
