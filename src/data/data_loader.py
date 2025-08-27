import pandas as pd
import logging
from abc import ABC, abstractmethod
from typing import List, Union
from .models import CountryData, RegionData


class DataLoader(ABC):
    
    @abstractmethod
    def load(self, file_path: str) -> List[Union[CountryData, RegionData]]:
        pass
    
    @abstractmethod
    def _parse_data(self, df: pd.DataFrame) -> List[Union[CountryData, RegionData]]:
        pass


class EnvironmentalDataLoader(DataLoader):
    
    def load(self, file_path: str) -> List[CountryData]:
        try:
            df = pd.read_excel(file_path, sheet_name='Sheet 1', header=None)
            countries = self._parse_data(df)
            return countries
        
        except FileNotFoundError:
            return []
        except Exception as e:
            logging.error(f"Error loading environmental data: {e}")
            return []
    
    def _parse_data(self, df: pd.DataFrame) -> List[CountryData]:
        countries = []
        
        header_row = 8
        data_start_row = 10
        
        years = []
        for col_idx in range(1, len(df.columns), 2):
            cell_value = df.iloc[header_row, col_idx]
            if pd.notna(cell_value):
                try:
                    year = int(str(cell_value).strip())
                    if 2000 <= year <= 2030:
                        years.append(year)
                except (ValueError, TypeError):
                    continue
        
        for row_idx in range(data_start_row, len(df)):
            country_name = df.iloc[row_idx, 0]
            
            if pd.isna(country_name) or not str(country_name).strip():
                continue
                
            country_name = str(country_name).strip()
            
            data_by_year = {}
            for i, year in enumerate(years):
                value_col_idx = 1 + (i * 2)
                
                if value_col_idx < len(df.columns):
                    cell_value = df.iloc[row_idx, value_col_idx]
                    
                    if pd.notna(cell_value):
                        try:
                            value_str = str(cell_value).replace(',', '').replace(' ', '')
                            if value_str and value_str != 'i':
                                value = float(value_str)
                                if value > 0:
                                    data_by_year[year] = value
                        except (ValueError, TypeError):
                            continue
            
            if data_by_year:
                country_code = self._generate_country_code(country_name)
                country_data = CountryData(
                    country_code=country_code,
                    country_name=country_name,
                    data_by_year=data_by_year,
                    data_type='environmental'
                )
                countries.append(country_data)
        
        return countries
    
    def _generate_country_code(self, country_name: str) -> str:
        country_codes = {
            'Poland': 'PL',
            'Germany': 'DE',
            'France': 'FR', 
            'Spain': 'ES',
            'Italy': 'IT',
            'Belgium': 'BE',
            'Netherlands': 'NL',
            'Austria': 'AT',
            'Denmark': 'DK',
            'Sweden': 'SE',
            'Finland': 'FI',
            'Norway': 'NO',
            'Czech Republic': 'CZ',
            'Czechia': 'CZ',
            'Slovakia': 'SK',
            'Hungary': 'HU',
            'Slovenia': 'SI',
            'Croatia': 'HR',
            'Romania': 'RO',
            'Bulgaria': 'BG',
            'Lithuania': 'LT',
            'Latvia': 'LV',
            'Estonia': 'EE',
            'Portugal': 'PT',
            'Greece': 'GR',
            'Ireland': 'IE'
        }
        
        return country_codes.get(country_name, country_name[:2].upper())


class TransportDataLoader(DataLoader):
    
    def load(self, file_path: str) -> List[RegionData]:
        try:
            df = pd.read_excel(file_path, sheet_name='Sheet 1', header=None)
            regions = self._parse_data(df)
            return regions
        
        except FileNotFoundError:
            return []
        except Exception as e:
            logging.error(f"Error loading transport data: {e}")
            return []
    
    def _parse_data(self, df: pd.DataFrame) -> List[RegionData]:
        regions = []
        
        header_row = 8
        data_start_row = 10
        
        years = []
        for col_idx in range(2, len(df.columns), 2):
            cell_value = df.iloc[header_row, col_idx]
            if pd.notna(cell_value):
                try:
                    year = int(str(cell_value).strip())
                    if 2000 <= year <= 2030:
                        years.append(year)
                except (ValueError, TypeError):
                    continue
        
        for row_idx in range(data_start_row, len(df)):
            region_code = df.iloc[row_idx, 0]
            region_name = df.iloc[row_idx, 1]
            
            if pd.isna(region_name) or not str(region_name).strip():
                continue
                
            region_code = str(region_code).strip() if pd.notna(region_code) else 'UNKNOWN'
            region_name = str(region_name).strip()
            
            data_by_year = {}
            for i, year in enumerate(years):
                value_col_idx = 2 + (i * 2)
                
                if value_col_idx < len(df.columns):
                    cell_value = df.iloc[row_idx, value_col_idx]
                    
                    if pd.notna(cell_value):
                        try:
                            value_str = str(cell_value).replace(',', '').replace(' ', '')
                            if value_str and value_str != ':':
                                value = float(value_str)
                                if value >= 0:
                                    data_by_year[year] = value
                        except (ValueError, TypeError):
                            continue
            
            if data_by_year:
                nuts_level = self._get_nuts_level(region_code)
                country_code = self._extract_country_code(region_code)
                
                region_data = RegionData(
                    region_code=region_code,
                    region_name=region_name,
                    country_code=country_code,
                    nuts_level=nuts_level,
                    data_by_year=data_by_year
                )
                regions.append(region_data)
        
        return regions
    
    def _get_nuts_level(self, region_code: str) -> int:
        if not region_code or region_code == 'UNKNOWN':
            return 0
            
        code_len = len(region_code)
        if code_len == 2:
            return 0
        elif code_len == 3:
            return 1
        elif code_len == 4:
            return 2
        else:
            return 3
    
    def _extract_country_code(self, region_code: str) -> str:
        if not region_code or len(region_code) < 2:
            return 'XX'
        return region_code[:2].upper()


class DataLoaderFactory:
    
    @staticmethod
    def create_loader(data_type: str) -> DataLoader:
        data_type = data_type.lower().strip()
        
        if data_type in ['environmental', 'env', 'recycling', 'środowiskowy']:
            return EnvironmentalDataLoader()
        elif data_type in ['transport', 'tran', 'electric', 'transportowy']:
            return TransportDataLoader()
        else:
            raise ValueError(f"Nieznany typ danych: {data_type}")
    
    @staticmethod
    def get_available_types() -> List[str]:
        return ['environmental', 'transport']
