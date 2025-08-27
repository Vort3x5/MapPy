from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import plotly.graph_objects as go
import io
from PIL import Image as PILImage
from datetime import datetime
import os
from typing import List, Dict, Any, Optional


class PDFExporter:
    
    def __init__(self):
        self.output_dir = "output/reports"
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
    
    def export_chart(self, figure: go.Figure, countries: List[str], 
                    data_source: str, year_range: tuple, 
                    additional_data: Optional[Dict] = None) -> str:
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raport_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []
        
        title_text = f"Raport: {data_source}"
        title = Paragraph(title_text, self.styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        info_text = f"""
        Zakres lat: {year_range[0]} - {year_range[1]}<br/>
        Kraje/regiony: {', '.join(countries[:5]) if countries else 'wszystkie'}<br/>
        Data generowania: {datetime.now().strftime("%d.%m.%Y %H:%M")}
        """
        info = Paragraph(info_text, self.styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 30))
        
        chart_image = self._convert_plotly_to_image(figure)
        if chart_image:
            elements.append(chart_image)
        
        doc.build(elements)
        return filepath
    
    def _convert_plotly_to_image(self, figure: go.Figure) -> Optional[Image]:
        try:
            img_bytes = figure.to_image(format="png", width=700, height=500)
            pil_image = PILImage.open(io.BytesIO(img_bytes))
            
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return Image(img_buffer, width=6*inch, height=4*inch)
            
        except Exception as e:
            print(f"Błąd konwersji wykresu: {e}")
            return None
