import os
import sys
sys.path.append('src')

from data.data_loader import DataLoaderFactory


def main():
    print("TESTOWANIE PARSOWANIA DANYCH EUROSTATU")
    print("=" * 50)
    
    print("\n1. Test Factory Pattern...")
    factory = DataLoaderFactory()
    
    try:
        env_loader = factory.create_loader('environmental')
        print("Environmental loader created")
        
        tran_loader = factory.create_loader('transport')  
        print("Transport loader created")
        
    except Exception as e:
        print(f"Factory error: {e}")
        return
    
    # Test Environmental Data
    print("\n2. Test Environmental Data Loading...")
    env_file = "in/env_waselvtdefaultview_spreadsheet.xlsx"
    
    if os.path.exists(env_file):
        env_data = env_loader.load(env_file)
        
        if env_data:
            print(f"\nWYNIKI ENV ({len(env_data)} krajów):")
            for country in env_data[:5]:  # Pokaż pierwsze 5
                years_range = country.get_year_range()
                total_2018_2022 = country.get_total_for_period(2018, 2022)
                print(f"  {country.country_name} ({country.country_code})")
                print(f"      Lata: {years_range[0]}-{years_range[1]}")
                print(f"      Suma 2018-2022: {total_2018_2022:,.0f}")
        else:
            print("Brak danych środowiskowych")
    else:
        print(f"Brak pliku: {env_file}")
    
    # Test Transport Data
    print("\n3. Test Transport Data Loading...")
    tran_file = "in/tran_r_elvehstdefaultview_spreadsheet.xlsx"
    
    if os.path.exists(tran_file):
        tran_data = tran_loader.load(tran_file)
        
        if tran_data:
            # Pokaż statystyki
            countries = set(r.country_code for r in tran_data)
            poland_regions = [r for r in tran_data if r.country_code == 'PL']
            
            print(f"\nWYNIKI TRAN ({len(tran_data)} regionów):")
            print(f"  Kraje: {len(countries)} ({', '.join(sorted(list(countries))[:10])}...)")
            print(f"  Regiony polskie: {len(poland_regions)}")
            
            # Przykłady polskich regionów
            for region in poland_regions[:3]:
                print(f"  {region.region_name} (NUTS {region.nuts_level})")
                print(f"      2022: {region.get_value_for_year(2022) or 'brak'}")
        else:
            print("Brak danych transportowych")
    else:
        print(f"Brak pliku: {tran_file}")
    
    print(f"\nTest zakończony! Przejdź do: streamlit run app.py")


if __name__ == "__main__":
    main()
