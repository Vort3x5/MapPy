# src/visual/chart.py
"""Interaktywne wykresy z Plotly - poprawione etykiety"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Union
from data.models import CountryData, RegionData
from utils.consts import CHART_CONFIG


class ChartVisualizer:
    """Klasa do tworzenia wykresów z czytelnymi etykietami"""
    
    def __init__(self):
        self.color_palette = CHART_CONFIG['COLORS']
        self.width = CHART_CONFIG['WIDTH']
        self.height = CHART_CONFIG['HEIGHT']
        self.font_size = CHART_CONFIG['FONT_SIZE']
    
    def create_bar_chart(self, data: Dict[str, Any], data_source: str) -> go.Figure:
        """Wykres słupkowy z czytelnymi etykietami"""
        
        fig = go.Figure()
        
        countries = data.get('countries', data.get('regions', data.get('names', [])))
        years = data.get('years', [])
        values = data.get('values', [])
        
        if not countries or not years or not values:
            return self._create_empty_chart("Brak danych do wyświetlenia")
        
        # Stwórz wykres grupowany
        for i, country in enumerate(countries):
            country_values = values[i] if i < len(values) else []
            color = self.color_palette[i % len(self.color_palette)]
            
            fig.add_trace(go.Bar(
                name=country,
                x=years,
                y=country_values,
                marker_color=color,
                hovertemplate=(
                    '<b>%{fullData.name}</b><br>'
                    'Rok: %{x}<br>'
                    'Wartość: %{y:,.0f}<br>'
                    '<extra></extra>'
                ),
                text=[f'{v:,.0f}' if v > 0 else '' for v in country_values],
                textposition='auto',
                textfont=dict(color='black', size=10)
            ))
        
        # Layout z czytelnymi etykietami
        title = f"Porównanie: {data_source}"
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black', 'family': 'Arial'}
            },
            xaxis_title='Rok',
            yaxis_title=self._get_y_axis_label(data_source),
            barmode='group',
            width=self.width,
            height=self.height,
            font={'size': self.font_size, 'color': 'black', 'family': 'Arial'},
            hovermode='x unified',
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'color': 'black'}
            },
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Osie z ciemnymi etykietami
        fig.update_xaxes(
            showgrid=True, 
            gridcolor='lightgray',
            showline=True, 
            linecolor='black',
            title_font=dict(size=14, color='black', family='Arial'),
            tickfont=dict(size=12, color='black', family='Arial'),
            linewidth=2
        )
        fig.update_yaxes(
            showgrid=True, 
            gridcolor='lightgray',
            showline=True, 
            linecolor='black',
            tickformat=',.0f',
            title_font=dict(size=14, color='black', family='Arial'),
            tickfont=dict(size=12, color='black', family='Arial'),
            linewidth=2
        )
        
        return fig
    
    def create_line_chart(self, data: Dict[str, Any], data_source: str) -> go.Figure:
        """Wykres liniowy z czytelnymi etykietami"""
        
        fig = go.Figure()
        
        countries = data.get('countries', data.get('regions', data.get('names', [])))
        years = data.get('years', [])
        values = data.get('values', [])
        
        if not countries or not years or not values:
            return self._create_empty_chart("Brak danych do wyświetlenia")
        
        for i, country in enumerate(countries):
            country_values = values[i] if i < len(values) else []
            color = self.color_palette[i % len(self.color_palette)]
            
            fig.add_trace(go.Scatter(
                name=country,
                x=years,
                y=country_values,
                mode='lines+markers',
                line=dict(color=color, width=3),
                marker=dict(size=8, color=color),
                hovertemplate=(
                    '<b>%{fullData.name}</b><br>'
                    'Rok: %{x}<br>'
                    'Wartość: %{y:,.0f}<br>'
                    '<extra></extra>'
                )
            ))
        
        # Layout
        title = f"Trendy czasowe: {data_source}"
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black', 'family': 'Arial'}
            },
            xaxis_title='Rok',
            yaxis_title=self._get_y_axis_label(data_source),
            width=self.width,
            height=self.height,
            font={'size': self.font_size, 'color': 'black', 'family': 'Arial'},
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend={'font': {'color': 'black'}}
        )
        
        fig.update_xaxes(
            showgrid=True, 
            gridcolor='lightgray',
            title_font=dict(size=14, color='black', family='Arial'),
            tickfont=dict(size=12, color='black', family='Arial'),
            linecolor='black',
            linewidth=2
        )
        fig.update_yaxes(
            showgrid=True, 
            gridcolor='lightgray', 
            tickformat=',.0f',
            title_font=dict(size=14, color='black', family='Arial'),
            tickfont=dict(size=12, color='black', family='Arial'),
            linecolor='black',
            linewidth=2
        )
        
        return fig
    
    def create_pie_chart(self, data: Dict[str, Any], data_source: str, year: int) -> go.Figure:
        """Wykres kołowy z czytelnymi etykietami"""
        
        countries = data.get('countries', data.get('regions', data.get('names', [])))
        values = data.get('values', [])
        years = data.get('years', [])
        
        if not countries or not values or year not in years:
            return self._create_empty_chart(f"Brak danych dla roku {year}")
        
        year_index = years.index(year)
        year_values = [vals[year_index] if year_index < len(vals) else 0 for vals in values]
        
        # Filtruj tylko pozytywne wartości
        filtered_data = [(country, value) for country, value in zip(countries, year_values) if value > 0]
        
        if not filtered_data:
            return self._create_empty_chart(f"Brak danych dla roku {year}")
        
        countries_filtered, values_filtered = zip(*filtered_data)
        
        # Ogranicz do top 10
        if len(countries_filtered) > 10:
            sorted_data = sorted(zip(countries_filtered, values_filtered), 
                               key=lambda x: x[1], reverse=True)
            countries_filtered, values_filtered = zip(*sorted_data[:10])
        
        fig = go.Figure(data=[go.Pie(
            labels=countries_filtered,
            values=values_filtered,
            hole=0.3,
            textinfo='label+percent',
            textposition='auto',
            marker=dict(colors=self.color_palette[:len(countries_filtered)]),
            hovertemplate='<b>%{label}</b><br>Wartość: %{value:,.0f}<br>Udział: %{percent}<extra></extra>',
            textfont=dict(size=12, color='black', family='Arial')
        )])
        
        title = f"{data_source} - {year}"
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black', 'family': 'Arial'}
            },
            width=self.width,
            height=self.height,
            font={'size': self.font_size, 'color': 'black', 'family': 'Arial'},
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01,
                font=dict(color='black')
            )
        )
        
        return fig
    
    def create_comparison_chart(self, data: Dict[str, Any], data_source: str) -> go.Figure:
        """Wykres porównawczy (subplot dla 2 krajów)"""
        
        countries = data.get('countries', data.get('regions', data.get('names', [])))
        years = data.get('years', [])
        values = data.get('values', [])
        
        if len(countries) != 2:
            return self.create_bar_chart(data, data_source)
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=countries,
            shared_yaxes=True,
            horizontal_spacing=0.1
        )
        
        for i, country in enumerate(countries):
            country_values = values[i] if i < len(values) else []
            color = self.color_palette[i]
            
            fig.add_trace(
                go.Bar(
                    x=years,
                    y=country_values,
                    name=country,
                    marker_color=color,
                    showlegend=False,
                    text=[f'{v:,.0f}' if v > 0 else '' for v in country_values],
                    textposition='auto',
                    hovertemplate=f'<b>{country}</b><br>Rok: %{{x}}<br>Wartość: %{{y:,.0f}}<extra></extra>',
                    textfont=dict(color='black', size=10)
                ),
                row=1, col=i+1
            )
        
        fig.update_layout(
            title={
                'text': f"Porównanie: {data_source}",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black', 'family': 'Arial'}
            },
            width=self.width,
            height=self.height,
            font={'size': self.font_size, 'color': 'black', 'family': 'Arial'},
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        fig.update_xaxes(
            title_text="Rok", 
            showgrid=True, 
            gridcolor='lightgray',
            title_font=dict(color='black', family='Arial'),
            tickfont=dict(color='black', family='Arial')
        )
        fig.update_yaxes(
            title_text=self._get_y_axis_label(data_source), 
            showgrid=True, 
            gridcolor='lightgray', 
            tickformat=',.0f',
            title_font=dict(color='black', family='Arial'),
            tickfont=dict(color='black', family='Arial')
        )
        
        return fig
    
    def create_top_n_chart(self, data: Dict[str, Any], data_source: str) -> go.Figure:
        """Wykres top N krajów/regionów"""
        
        names = data.get('names', [])
        totals = data.get('totals', [])
        
        if not names or not totals:
            return self._create_empty_chart("Brak danych do wyświetlenia")
        
        # Sortuj i ogranicz jeśli potrzeba
        sorted_data = sorted(zip(names, totals), key=lambda x: x[1], reverse=True)
        if len(sorted_data) > 15:  # Maksymalnie 15 dla czytelności
            sorted_data = sorted_data[:15]
        
        names_sorted, totals_sorted = zip(*sorted_data)
        
        colors = [self.color_palette[i % len(self.color_palette)] for i in range(len(names_sorted))]
        
        fig = go.Figure(data=[
            go.Bar(
                x=names_sorted,
                y=totals_sorted,
                marker_color=colors,
                text=[f'{v:,.0f}' for v in totals_sorted],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Wartość: %{y:,.0f}<extra></extra>',
                textfont=dict(color='black', size=10)
            )
        ])
        
        fig.update_layout(
            title={
                'text': f"Top {len(names_sorted)} - {data_source}",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black', 'family': 'Arial'}
            },
            xaxis_title="Element",
            yaxis_title=self._get_y_axis_label(data_source),
            width=self.width,
            height=self.height,
            font={'size': self.font_size, 'color': 'black', 'family': 'Arial'},
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        fig.update_xaxes(
            showgrid=True, 
            gridcolor='lightgray', 
            tickangle=45,
            title_font=dict(color='black', family='Arial'),
            tickfont=dict(color='black', family='Arial'),
            linecolor='black',
            linewidth=2
        )
        fig.update_yaxes(
            showgrid=True, 
            gridcolor='lightgray', 
            tickformat=',.0f',
            title_font=dict(color='black', family='Arial'),
            tickfont=dict(color='black', family='Arial'),
            linecolor='black',
            linewidth=2
        )
        
        return fig
    
    def create_regional_breakdown_chart(self, regions: List[RegionData], 
                                      country_code: str, year: int) -> go.Figure:
        """Wykres rozkładu regionalnego w kraju"""
        
        # Filtruj regiony dla konkretnego kraju i roku
        country_regions = [r for r in regions if r.country_code == country_code.upper()]
        
        region_names = []
        region_values = []
        
        for region in country_regions:
            value = region.get_value_for_year(year)
            if value is not None and value > 0:
                region_names.append(region.region_name)
                region_values.append(value)
        
        if not region_names:
            return self._create_empty_chart(f"Brak danych regionalnych dla {country_code} w {year}")
        
        # Sortuj malejąco
        sorted_data = sorted(zip(region_names, region_values), 
                           key=lambda x: x[1], reverse=True)
        region_names, region_values = zip(*sorted_data)
        
        # Ogranicz do top 12 dla czytelności
        if len(region_names) > 12:
            region_names = region_names[:12]
            region_values = region_values[:12]
        
        # Jednolity kolor dla regionów
        color = '#2E86AB'
        
        fig = go.Figure(data=[
            go.Bar(
                y=region_names,
                x=region_values,
                orientation='h',
                marker_color=color,
                text=[f'{v:,.0f}' for v in region_values],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Wartość: %{x:,.0f}<extra></extra>',
                textfont=dict(color='white', size=11)
            )
        ])
        
        fig.update_layout(
            title={
                'text': f"Regiony - {country_code.upper()} ({year})",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black', 'family': 'Arial'}
            },
            xaxis_title="Liczba pojazdów",
            yaxis_title="Region",
            width=self.width,
            height=max(400, len(region_names) * 30),
            font={'size': 11, 'color': 'black', 'family': 'Arial'},
            margin=dict(l=200, r=50, t=80, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        fig.update_xaxes(
            showgrid=True, 
            gridcolor='lightgray', 
            tickformat=',.0f',
            title_font=dict(color='black', family='Arial'),
            tickfont=dict(color='black', family='Arial')
        )
        fig.update_yaxes(
            showgrid=False,
            title_font=dict(color='black', family='Arial'),
            tickfont=dict(color='black', family='Arial')
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Stwórz pusty wykres z wiadomością"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color="gray", family='Arial'),
            showarrow=False
        )
        
        fig.update_layout(
            width=self.width,
            height=self.height,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            font={'family': 'Arial'}
        )
        
        return fig
    
    def _get_y_axis_label(self, data_source: str) -> str:
        """Pobierz etykietę osi Y"""
        if "zutylizowane" in data_source.lower() or "environmental" in data_source.lower():
            return "Liczba zutylizowanych pojazdów"
        else:
            return "Liczba pojazdów elektrycznych"
