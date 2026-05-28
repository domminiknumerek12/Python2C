
import sys
from backend.transpilator import transpiluj

if len(sys.argv) < 2:
    print("użycie: py2c.py input.py [output.c]")
    sys.exit(1)
    
plik_wej = sys.argv[1]
plik_wyj = sys.argv[2] if len(sys.argv) > 2 else None
    
with open(plik_wej) as f:
    kod = f.read()
    
kod_c = transpiluj(kod)
    
if plik_wyj:
    with open(plik_wyj, 'w') as f:
        f.write(kod_c)
    print(f'Zapisano: {plik_wyj}')
else:
    print(kod_c)