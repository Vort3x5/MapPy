import plotly.graph_objects as go
from typing import Dict, Any
from utils.consts import CHART_CONFIG


class ChartVisualizer:
    
    def __init__(self):
        self.color_palette = CHART_CONFIG['COLORS']
        self.width = CHART_CONFIG['WIDTH']
        self.height = CHART_CONFIG['HEIGHT']
        self.font_size = CHART_CONFIG['FONT_SIZE']
    
    def create_bar_chart(self, data: Dict[str, Any], data_source: str) -> go.Figure:
        
        fig = go.Figure()
        
        countries = data.get('countries', data.get('regions', data.get('names', [])))
        years = data.get('years', [])
        values = data.get('values', [])
        
        if not countries or not years or not values:
            return self._create_empty_chart("Brak danych do wyświetlenia")
        
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
    
    def _create_empty_chart(self, message: str) -> go.Figure:
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
        if "zutylizowane" in data_source.lower() or "environmental" in data_source.lower():
            return "Liczba zutylizowanych pojazdów"
        else:
            return "Liczba pojazdów elektrycznych"
