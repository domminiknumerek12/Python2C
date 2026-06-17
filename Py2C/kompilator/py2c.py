
import sys
import traceback
from backend.transpilator import transpiluj
from backend.errors import CompilationError

def main():
    if len(sys.argv) < 2:
        print("Użycie: py2c.py input.py [output.c]")
        sys.exit(1)
    
    plik_wej = sys.argv[1]
    plik_wyj = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Wczytanie pliku źródłowego
        try:
            with open(plik_wej, 'r', encoding='utf-8') as f:
                kod = f.read()
        except FileNotFoundError:
            print(f"BŁĄD: Plik '{plik_wej}' nie znaleziony.")
            sys.exit(1)
        except IOError as e:
            print(f"BŁĄD: Nie można czytać pliku '{plik_wej}': {e}")
            sys.exit(1)
        
        if not kod.strip():
            print(f"BŁĄD: Plik '{plik_wej}' jest pusty.")
            sys.exit(1)
        
        # Transpilacja
        try:
            kod_c = transpiluj(kod)
        except CompilationError as e:
            print(f"BŁĄD KOMPILACJI: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"BŁĄD WEWNĘTRZNY: {e}")
            traceback.print_exc()
            sys.exit(1)
        
        # Zapisanie resultu
        if plik_wyj:
            try:
                with open(plik_wyj, 'w', encoding='utf-8') as f:
                    f.write(kod_c)
                print(f'✓ Kompilacja powodzenia. Zapisano: {plik_wyj}')
            except IOError as e:
                print(f"BŁĄD: Nie można zapisać do pliku '{plik_wyj}': {e}")
                sys.exit(1)
        else:
            print(kod_c)
    
    except KeyboardInterrupt:
        print("\nKompilacja przerwana przez użytkownika.")
        sys.exit(130)
    except Exception as e:
        print(f"NIEZNANY BŁĄD: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()