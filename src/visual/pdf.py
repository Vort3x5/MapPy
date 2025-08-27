"""Export wykresów i danych do PDF"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import plotly.graph_objects as go
import io
import base64
from PIL import Image as PILImage
from datetime import datetime
import os
from typing import List, Dict, Any, Optional
from utils.consts import PDF_CONFIG


class PDFExporter:
    """Klasa do eksportu wykresów i raportów do PDF"""
    
    def __init__(self):
        self.output_dir = PDF_CONFIG['OUTPUT_DIR']
        self.page_width, self.page_height = A4
        self.margin = PDF_CONFIG['MARGIN']
        
        # Upewnij się że katalog wyjściowy istnieje
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup stylów
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Stwórz niestandardowe style"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=20,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=12,
            fontName='Helvetica'
        )
        
        self.small_style = ParagraphStyle(
            'CustomSmall',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            spaceAfter=6,
            fontName='Helvetica',
            textColor=colors.grey
        )
    
    def export_chart(self, figure: go.Figure, countries: List[str], 
                    data_source: str, year_range: tuple, 
                    additional_data: Optional[Dict] = None) -> str:
        """Eksportuj wykres do PDF z metadanymi"""
        
        # Generuj nazwę pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        country_str = "_".join([c.replace(" ", "") for c in countries[:3]])  # Max 3 kraje w nazwie
        data_type = "env" if "zutylizowane" in data_source.lower() else "tran"
        filename = f"raport_{data_type}_{country_str}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Stwórz dokument PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Zbierz elementy do PDF
        elements = []
        
        # Strona tytułowa
        elements.extend(self._create_title_page(countries, data_source, year_range))
        
        # Metadane raportu
        elements.extend(self._create_metadata_section(countries, data_source, year_range, additional_data))
        
        # Wykres
        chart_image = self._convert_plotly_to_image(figure)
        if chart_image:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Wykres główny", self.subtitle_style))
            elements.append(Spacer(1, 10))
            elements.append(chart_image)
        
        # Tabela z danymi
        if additional_data:
            data_table = self._create_data_table(additional_data, data_source)
            if data_table:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("Szczegółowe dane", self.subtitle_style))
                elements.append(Spacer(1, 10))
                elements.append(data_table)
        
        # Stopka raportu
        elements.extend(self._create_footer())
        
        # Zbuduj PDF
        try:
            doc.build(elements)
            return filepath
        except Exception as e:
            raise Exception(f"Błąd tworzenia PDF: {str(e)}")
    
    def export_summary_report(self, env_data: List, tran_data: List, 
                             year_range: tuple) -> str:
        """Eksportuj pełny raport podsumowujący"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raport_podsumowujacy_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        elements = []
        
        # Strona tytułowa
        elements.extend(self._create_summary_title_page(year_range))
        
        # Sekcja danych środowiskowych
        if env_data:
            elements.append(PageBreak())
            elements.append(Paragraph("Dane środowiskowe - Pojazdy zutylizowane", self.subtitle_style))
            elements.extend(self._create_data_summary(env_data, "environmental", year_range))
        
        # Sekcja danych transportowych
        if tran_data:
            elements.append(PageBreak())
            elements.append(Paragraph("Dane transportowe - Pojazdy elektryczne", self.subtitle_style))
            elements.extend(self._create_data_summary(tran_data, "transport", year_range))
        
        # Podsumowanie
        elements.extend(self._create_summary_conclusions(env_data, tran_data, year_range))
        
        # Stopka
        elements.extend(self._create_footer())
        
        try:
            doc.build(elements)
            return filepath
        except Exception as e:
            raise Exception(f"Błąd tworzenia raportu: {str(e)}")
    
    def _create_title_page(self, countries: List[str], data_source: str, 
                          year_range: tuple) -> List:
        """Stwórz stronę tytułową"""
        elements = []
        
        # Główny tytuł
        if "zutylizowane" in data_source.lower():
            main_title = "Analiza Danych o Pojazdach Zutylizowanych"
        else:
            main_title = "Analiza Danych o Pojazdach Elektrycznych"
        
        elements.append(Paragraph(main_title, self.title_style))
        elements.append(Spacer(1, 20))
        
        # Podtytuł z krajami
        if len(countries) == 1:
            subtitle = f"Raport dla: {countries[0]}"
        elif len(countries) <= 5:
            subtitle = f"Porównanie krajów: {', '.join(countries)}"
        else:
            subtitle = f"Analiza {len(countries)} krajów/regionów"
        
        elements.append(Paragraph(subtitle, self.subtitle_style))
        elements.append(Spacer(1, 30))
        
        # Informacje o raporcie
        info_text = f"""
        <b>Okres analizy:</b> {year_range[0]} - {year_range[1]}<br/>
        <b>Źródło danych:</b> Eurostat (Europejski Urząd Statystyczny)<br/>
        <b>Data generowania:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}<br/>
        <b>Typ analizy:</b> {data_source}
        """
        
        elements.append(Paragraph(info_text, self.body_style))
        elements.append(Spacer(1, 50))
        
        # Logo/branding (opcjonalne)
        elements.append(Paragraph("Eurostat Vehicle Data Analyzer", self.body_style))
        elements.append(Paragraph("System analizy danych o pojazdach w Europie", self.small_style))
        
        elements.append(PageBreak())
        
        return elements
    
    def _create_metadata_section(self, countries: List[str], data_source: str, 
                                year_range: tuple, additional_data: Optional[Dict]) -> List:
        """Stwórz sekcję metadanych"""
        elements = []
        
        elements.append(Paragraph("Informacje o raporcie", self.subtitle_style))
        
        # Tabela metadanych
        metadata = [
            ['Parametr', 'Wartość'],
            ['Źródło danych', 'Eurostat - European Statistical Office'],
            ['Typ danych', data_source],
            ['Zakres czasowy', f'{year_range[0]} - {year_range[1]}'],
            ['Liczba krajów/regionów', str(len(countries))],
            ['Data generowania', datetime.now().strftime("%d.%m.%Y %H:%M:%S")],
        ]
        
        if additional_data:
            if 'total_values' in additional_data:
                metadata.append(['Suma wszystkich wartości', f"{additional_data['total_values']:,.0f}"])
            if 'average_value' in additional_data:
                metadata.append(['Średnia wartość', f"{additional_data['average_value']:,.0f}"])
        
        metadata_table = Table(metadata, colWidths=[3*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 20))
        
        # Lista krajów
        if countries:
            elements.append(Paragraph("Analizowane kraje/regiony:", self.subtitle_style))
            countries_text = "<br/>".join([f"• {country}" for country in countries])
            elements.append(Paragraph(countries_text, self.body_style))
        
        return elements
    
    def _convert_plotly_to_image(self, figure: go.Figure) -> Optional[Image]:
        """Konwertuj wykres Plotly do obrazu dla PDF"""
        try:
            # Konwertuj na PNG z wysoką rozdzielczością
            img_bytes = figure.to_image(
                format="png", 
                width=800, 
                height=600,
                scale=2  # Wyższa jakość
            )
            
            # Stwórz obraz PIL
            pil_image = PILImage.open(io.BytesIO(img_bytes))
            
            # Zapisz do bufora
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Oblicz rozmiary dla PDF (zachowaj proporcje)
            available_width = self.page_width - 2 * self.margin
            available_height = (self.page_height - 4 * self.margin) * 0.6  # 60% wysokości strony
            
            img_width, img_height = pil_image.size
            width_scale = available_width / img_width
            height_scale = available_height / img_height
            scale = min(width_scale, height_scale, 1.0)  # Nie powiększaj
            
            final_width = img_width * scale * 0.75  # Konwersja do punktów
            final_height = img_height * scale * 0.75
            
            return Image(img_buffer, width=final_width, height=final_height)
            
        except Exception as e:
            print(f"Błąd konwersji wykresu: {e}")
            return None
    
    def _create_data_table(self, data: Dict[str, Any], data_source: str) -> Optional[Table]:
        """Stwórz tabelę z danymi"""
        try:
            countries = data.get('countries', data.get('regions', data.get('names', [])))
            years = data.get('years', [])
            values = data.get('values', [])
            totals = data.get('totals', [])
            
            if not countries or not years or not values:
                return None
            
            # Nagłówki tabeli
            headers = ['Kraj/Region'] + [str(year) for year in years] + ['Suma']
            
            # Dane
            table_data = [headers]
            for i, country in enumerate(countries):
                row = [country]
                country_values = values[i] if i < len(values) else []
                
                # Dodaj wartości dla każdego roku
                for j, year in enumerate(years):
                    value = country_values[j] if j < len(country_values) else 0
                    row.append(f"{value:,.0f}" if value > 0 else "-")
                
                # Dodaj sumę
                total = totals[i] if i < len(totals) else sum(country_values)
                row.append(f"{total:,.0f}")
                
                table_data.append(row)
            
            # Ogranicz liczbę wierszy jeśli za dużo
            if len(table_data) > 21:  # 1 nagłówek + 20 wierszy max
                table_data = table_data[:21]
                table_data.append(['...'] * len(headers))
            
            # Stwórz tabelę
            col_widths = [2.5*inch] + [0.8*inch] * len(years) + [1*inch]
            table = Table(table_data, colWidths=col_widths)
            
            # Stylizuj tabelę
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Wyróżnij kolumnę sum
                ('BACKGROUND', (-1, 1), (-1, -1), colors.lightyellow),
                ('FONTNAME', (-1, 1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            return table
            
        except Exception as e:
            print(f"Błąd tworzenia tabeli: {e}")
            return None
    
    def _create_footer(self) -> List:
        """Stwórz stopkę raportu"""
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Informacje dodatkowe", self.subtitle_style))
        
        footer_text = """
        <b>Źródło danych:</b> Ten raport został wygenerowany na podstawie danych z Eurostatu, 
        oficjalnego urzędu statystycznego Unii Europejskiej. Dane dotyczą zarządzania pojazdami 
        wycofanymi z eksploatacji oraz adopcji pojazdów elektrycznych w krajach i regionach europejskich.<br/><br/>
        
        <b>Metodologia:</b> Wartości przedstawiają roczne sumy zagregowane w wybranym okresie. 
        Dane regionalne są klasyfikowane według NUTS (Nomenklatura Jednostek Terytorialnych do Celów Statystycznych).<br/><br/>
        
        <b>Zastrzeżenia:</b> Dane mogą zawierać braki dla niektórych krajów/regionów w określonych latach. 
        Wartości zerowe lub brakujące są oznaczane jako "-" w tabelach. Wszystkie wartości są wyrażone w liczbach bezwzględnych.<br/><br/>
        """
        
        elements.append(Paragraph(footer_text, self.body_style))
        
        # Informacje o systemie
        system_info = f"""
        <i>Raport wygenerowany przez: Eurostat Vehicle Data Analyzer v1.0<br/>
        Data i czas: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}<br/>
        Projekt: System Analizy Danych Pojazdów w Europie</i>
        """
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(system_info, self.small_style))
        
        return elements
    
    def _create_summary_title_page(self, year_range: tuple) -> List:
        """Strona tytułowa dla raportu podsumowującego"""
        elements = []
        
        elements.append(Paragraph("Raport Podsumowujący", self.title_style))
        elements.append(Paragraph("Analiza Danych Pojazdów w Europie", self.subtitle_style))
        elements.append(Spacer(1, 50))
        
        summary_info = f"""
        <b>Zakres czasowy:</b> {year_range[0]} - {year_range[1]}<br/>
        <b>Źródła danych:</b> env_waselvt (pojazdy zutylizowane), tran_r_elvehst (pojazdy elektryczne)<br/>
        <b>Data generowania:</b> {datetime.now().strftime("%d.%m.%Y %H:%M")}<br/>
        <b>Typ raportu:</b> Kompleksowa analiza porównawcza
        """
        
        elements.append(Paragraph(summary_info, self.body_style))
        elements.append(PageBreak())
        
        return elements
    
    def _create_data_summary(self, data: List, data_type: str, year_range: tuple) -> List:
        """Stwórz podsumowanie danych"""
        elements = []
        
        # Podstawowe statystyki
        total_items = len(data)
        
        elements.append(Paragraph(f"Liczba pozycji: {total_items}", self.body_style))
        
        if data_type == "environmental":
            countries = set(item.country_name for item in data)
            elements.append(Paragraph(f"Liczba krajów: {len(countries)}", self.body_style))
        else:
            countries = set(item.country_code for item in data)
            nuts_levels = set(item.nuts_level for item in data)
            elements.append(Paragraph(f"Liczba krajów: {len(countries)}", self.body_style))
            elements.append(Paragraph(f"Poziomy NUTS: {sorted(list(nuts_levels))}", self.body_style))
        
        return elements
    
    def _create_summary_conclusions(self, env_data: List, tran_data: List, year_range: tuple) -> List:
        """Stwórz sekcję podsumowującą wnioski"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Podsumowanie i wnioski", self.subtitle_style))
        
        conclusions_text = f"""
        Analiza danych z okresu {year_range[0]}-{year_range[1]} obejmuje:
        <br/><br/>
        • Dane środowiskowe: {len(env_data) if env_data else 0} krajów z danymi o utylizacji pojazdów
        <br/>
        • Dane transportowe: {len(tran_data) if tran_data else 0} regionów z danymi o pojazdach elektrycznych
        <br/><br/>
        Ten raport dostarcza kompleksowego przeglądu stanu zarządzania pojazdami wycofanymi 
        z eksploatacji oraz adopcji pojazdów elektrycznych w krajach europejskich.
        """
        
        elements.append(Paragraph(conclusions_text, self.body_style))
        
        return elements
