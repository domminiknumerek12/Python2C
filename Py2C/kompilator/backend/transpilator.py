from .parser import PARSER
from .symbole import TablicaSymboli
from .typowanie import PrzebiegTypów
from .gen_kod import GeneratorKodu

def transpiluj(kod_źródłowy):
    if not kod_źródłowy.endswith('\n'):
        kod_źródłowy += '\n'
    
    drzewo = PARSER.parse(kod_źródłowy)
    
    tablica_symboli = TablicaSymboli()
    PrzebiegTypów(tablica_symboli).wykonaj(drzewo)
    return GeneratorKodu(tablica_symboli).generuj(drzewo)
