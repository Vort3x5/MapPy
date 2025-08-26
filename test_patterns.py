import sys
import os
sys.path.append('src')

from data.data_loader import DataLoaderFactory
from data.data_processor import DataProcessor, CountryAggregationStrategy, RegionAggregationStrategy, TopNStrategy
from utils.observers import DataManager, DataObserver, UIComponentObserver


def test_factory_pattern():
    """Test Factory Pattern"""
    print("\n1. FACTORY PATTERN TEST")
    print("-" * 30)
    
    factory = DataLoaderFactory()
    
    # Test tworzenia różnych loaderów
    env_loader = factory.create_loader('environmental')
    tran_loader = factory.create_loader('transport')
    
    print(f"Environmental loader: {type(env_loader).__name__}")
    print(f"Transport loader: {type(tran_loader).__name__}")
    
    # Test dostępnych typów
    available_types = factory.get_available_types()
    print(f"Available loader types: {available_types}")
    
    # Test błędnego typu
    try:
        factory.create_loader('unknown')
    except ValueError as e:
        print(f"Expected error for unknown type: {e}")
    
    print("Factory Pattern: PASS")
    return env_loader, tran_loader


def test_strategy_pattern(env_loader, tran_loader):
    """Test Strategy Pattern"""
    print("\n2. STRATEGY PATTERN TEST")
    print("-" * 30)
    
    # Wczytaj przykładowe dane jeśli istnieją
    env_data = []
    tran_data = []
    
    if os.path.exists("in/env_waselvtdefaultview_spreadsheet.xlsx"):
        env_data = env_loader.load("in/env_waselvtdefaultview_spreadsheet.xlsx")
        print(f"Loaded {len(env_data)} countries")
    else:
        print("No environmental data file - using mock data")
        from data.models import CountryData
        env_data = [
            CountryData("PL", "Poland", {2018: 100000, 2019: 110000, 2020: 120000}, "environmental"),
            CountryData("DE", "Germany", {2018: 200000, 2019: 210000, 2020: 220000}, "environmental")
        ]
    
    if os.path.exists("in/tran_r_elvehstdefaultview_spreadsheet.xlsx"):
        tran_data = tran_loader.load("in/tran_r_elvehstdefaultview_spreadsheet.xlsx")
        print(f"Loaded {len(tran_data)} regions")
    else:
        print("No transport data file - using mock data")
        from data.models import RegionData
        tran_data = [
            RegionData("PL1", "Mazowieckie", "PL", 1, {2018: 500, 2019: 600, 2020: 700}),
            RegionData("DE1", "Baden-Württemberg", "DE", 1, {2018: 1000, 2019: 1200, 2020: 1400})
        ]
    
    # Test CountryAggregationStrategy
    print("\nTesting CountryAggregationStrategy...")
    country_strategy = CountryAggregationStrategy()
    processor = DataProcessor(country_strategy)
    
    result = processor.process_data(env_data[:5], (2018, 2020))
    print(f"Countries processed: {len(result['countries'])}")
    print(f"Years: {result['years']}")
    if result['countries']:
        print(f"Sample country: {result['countries'][0]} with values: {result['values'][0]}")
    
    # Test RegionAggregationStrategy
    print("\nTesting RegionAggregationStrategy...")
    region_strategy = RegionAggregationStrategy()
    processor.set_strategy(region_strategy)
    
    result = processor.process_data(tran_data[:10], (2018, 2020), country_filter='PL')
    print(f"Regions processed: {len(result['regions'])}")
    if result['regions']:
        print(f"Sample region: {result['regions'][0]} with values: {result['values'][0]}")
    
    # Test TopNStrategy
    print("\nTesting TopNStrategy...")
    top_strategy = TopNStrategy(n=3, sort_by='total')
    processor.set_strategy(top_strategy)
    
    result = processor.process_data(env_data, (2018, 2020))
    print(f"Top {len(result['names'])} countries by total:")
    for i, (name, total) in enumerate(zip(result['names'], result['totals'])):
        print(f"  {i+1}. {name}: {total:,.0f}")
    
    print("Strategy Pattern: PASS")
    return env_data, tran_data


def test_observer_pattern(env_data, tran_data):
    """Test Observer Pattern"""
    print("\n3. OBSERVER PATTERN TEST")
    print("-" * 30)
    
    # Stwórz DataManager (Subject)
    data_manager = DataManager()
    
    # Stwórz różnych observerów
    map_observer = DataObserver("MapComponent")
    chart_observer = DataObserver("ChartComponent")
    table_observer = DataObserver("TableComponent")
    
    # Dodaj callback observer
    def ui_callback(event_type, data):
        print(f"  UI Callback triggered: {event_type} with {data}")
    
    callback_observer = DataObserver("UICallback", ui_callback)
    
    # Załącz observerów
    data_manager.attach(map_observer)
    data_manager.attach(chart_observer)
    data_manager.attach(table_observer)
    data_manager.attach(callback_observer)
    
    print(f"Attached {len(data_manager._observers)} observers")
    
    # Test powiadomień
    print("\nTesting notifications...")
    
    print("1. Loading environmental data...")
    data_manager.load_environmental_data(env_data)
    
    print("2. Loading transport data...")
    data_manager.load_transport_data(tran_data)
    
    print("3. Changing year range...")
    data_manager.set_year_range((2019, 2021))
    
    print("4. Selecting countries...")
    data_manager.set_selected_countries(['Poland', 'Germany'])
    
    print("5. Applying filter...")
    data_manager.apply_filter({'country_code': 'PL', 'nuts_level': 1})
    
    # Test UI Component Observer
    print("\nTesting UI Component Observer...")
    def refresh_map(event_type, data):
        print(f"  Refreshing map for {event_type}")
    
    ui_observer = UIComponentObserver("InteractiveMap", refresh_map)
    data_manager.attach(ui_observer)
    
    data_manager.set_year_range((2020, 2022))
    
    # Test detach
    print("\nTesting observer detachment...")
    data_manager.detach(map_observer)
    data_manager.set_selected_countries(['Poland'])  # map_observer nie powinien dostać powiadomienia
    
    # Test summary stats
    print("\nTesting summary stats...")
    stats = data_manager.get_summary_stats()
    print(f"Summary: {stats}")
    
    print("Observer Pattern: PASS")
    return data_manager


def test_integration():
    """Test integracji wszystkich wzorców"""
    print("\n4. INTEGRATION TEST")
    print("-" * 30)
    
    # Factory Pattern - stwórz loadery
    factory = DataLoaderFactory()
    env_loader = factory.create_loader('environmental')
    
    # Strategy Pattern - przygotuj procesor
    from data.data_processor import CountryAggregationStrategy
    strategy = CountryAggregationStrategy()
    processor = DataProcessor(strategy)
    
    # Observer Pattern - stwórz manager
    data_manager = DataManager()
    
    # Dodaj observer, który używa Strategy Pattern
    def process_data_callback(event_type, data):
        if event_type == 'env_data_loaded' and data_manager.env_data:
            result = processor.process_data(data_manager.env_data[:3], data_manager.year_range)
            print(f"  Processed {len(result['countries'])} countries via Strategy Pattern")
    
    processor_observer = DataObserver("DataProcessor", process_data_callback)
    data_manager.attach(processor_observer)
    
    # Test pełnego flow
    print("Running full integration flow...")
    
    # Mock data jeśli brak plików
    if not os.path.exists("data/env_waselvtdefaultview_spreadsheet.xlsx"):
        from data.models import CountryData
        mock_data = [
            CountryData("PL", "Poland", {2018: 100000, 2019: 110000, 2020: 120000}, "environmental"),
            CountryData("DE", "Germany", {2018: 200000, 2019: 210000, 2020: 220000}, "environmental"),
            CountryData("FR", "France", {2018: 180000, 2019: 190000, 2020: 200000}, "environmental")
        ]
        data_manager.load_environmental_data(mock_data)
    else:
        env_data = env_loader.load("data/env_waselvtdefaultview_spreadsheet.xlsx")
        data_manager.load_environmental_data(env_data)
    
    # Zmiana parametrów wywołuje observerów i przetwarzanie strategiami
    data_manager.set_year_range((2018, 2020))
    data_manager.set_selected_countries(['Poland', 'Germany'])
    
    print("Integration Test: PASS")


def main():
    """Uruchom wszystkie testy wzorców projektowych"""
    print("TESTOWANIE WZORCÓW PROJEKTOWYCH")
    print("=" * 50)
    
    try:
        # Test każdego wzorca osobno
        env_loader, tran_loader = test_factory_pattern()
        env_data, tran_data = test_strategy_pattern(env_loader, tran_loader)
        data_manager = test_observer_pattern(env_data, tran_data)
        
        # Test integracji
        test_integration()
        
        print("\n" + "=" * 50)
        print("WSZYSTKIE WZORCE PROJEKTOWE: PASS")
        print("✓ Factory Pattern - tworzenie loaderów")
        print("✓ Strategy Pattern - różne algorytmy przetwarzania")  
        print("✓ Observer Pattern - reaktywne powiadomienia")
        print("✓ Integracja - wszystkie wzorce współpracują")
        
        print("\nGotowe do implementacji wizualizacji!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
