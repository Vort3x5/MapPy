# src/utils/consts.py
"""Minimalna konfiguracja systemu"""

# Konfiguracja Excel
EXCEL_CONFIG = {
    'HEADER_ROW': 8,
    'DATA_START_ROW': 10
}

# Konfiguracja map
MAP_CONFIG = {
    'EUROPE_CENTER': [54.5, 15.2],
    'POLAND_CENTER': [52.0, 19.5],  # Bardziej precyzyjne centrum Polski
    'EUROPE_ZOOM': 4,
    'POLAND_ZOOM': 7,  # Większy zoom dla Polski
    'COLOR_SCALE': 'YlOrRd'
}

# Konfiguracja wykresów
CHART_CONFIG = {
    'WIDTH': 800,
    'HEIGHT': 600,
    'COLORS': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
    'FONT_SIZE': 12
}

# Współrzędne krajów europejskich i regionów polskich
# Źródło: Natural Earth Data (https://www.naturalearthdata.com/)
COUNTRY_COORDINATES = {
    'poland': (52.0, 19.0),
    'germany': (51.0, 9.0),
    'france': (46.0, 2.0),
    'spain': (40.0, -4.0),
    'italy': (42.0, 13.0),
    'belgium': (50.8, 4.4),
    'netherlands': (52.5, 5.8),
    'austria': (47.0, 13.0),
    'denmark': (56.0, 10.0),
    'sweden': (59.0, 18.0),
    'finland': (64.0, 26.0),
    'norway': (62.0, 10.0),
    'czechia': (49.8, 15.5),
    'czech republic': (49.8, 15.5),
    'slovakia': (48.7, 19.7),
    'hungary': (47.5, 19.0),
    'slovenia': (46.0, 15.0),
    'croatia': (45.0, 16.0),
    'romania': (46.0, 25.0),
    'bulgaria': (43.0, 25.0),
    'lithuania': (55.0, 24.0),
    'latvia': (57.0, 24.0),
    'estonia': (59.0, 26.0),
    'portugal': (39.5, -8.0),
    'greece': (39.0, 22.0),
    'ireland': (53.0, -8.0),
    'mazowieckie': (52.2, 21.0),
    'śląskie': (50.3, 19.2),
    'wielkopolskie': (52.4, 17.0),
    'małopolskie': (50.1, 20.1),
    'dolnośląskie': (51.1, 16.3),
    'łódzkie': (51.8, 19.5),
    'zachodniopomorskie': (53.4, 15.6),
    'pomorskie': (54.2, 18.6),
    'warmińsko-mazurskie': (54.0, 20.5),
    'kujawsko-pomorskie': (53.0, 18.6),
    'podlaskie': (53.1, 23.2),
    'lubelskie': (51.2, 22.9),
    'podkarpackie': (49.6, 22.0),
    'świętokrzyskie': (50.6, 20.6),
    'lubuskie': (52.0, 15.2),
    'opolskie': (50.5, 17.9)
}
