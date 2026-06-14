from .parser import PARSER
from .symbole import TablicaSymboli
from .typowanie import PrzebiegTypów
from .gen_kod import GeneratorKodu
from .errors import CompilationError, SyntaxError as CustomSyntaxError, SemanticError
from lark import LarkError

def transpiluj(kod_źródłowy):
    """Transpiluje kod Pythona na C.
    
    Args:
        kod_źródłowy: Kod Python do transpilacji
        
    Returns:
        Kod C jako string
        
    Raises:
        CompilationError: W przypadku błędu kompilacji
        CustomSyntaxError: W przypadku błędu składni
        SemanticError: W przypadku błędu semantycznego
    """
    if not kod_źródłowy or not kod_źródłowy.strip():
        raise CompilationError("Kod źródłowy jest pusty.")
    
    # Normalizacja linii
    if not kod_źródłowy.endswith('\n'):
        kod_źródłowy += '\n'
    
    # Etap 1: Parsing
    try:
        drzewo = PARSER.parse(kod_źródłowy)
    except LarkError as e:
        raise CustomSyntaxError(f"Błąd składni: {e}")
    except Exception as e:
        raise CompilationError(f"Błąd parsowania: {e}")
    
    # Etap 2: Type checking i semantic analysis
    try:
        tablica_symboli = TablicaSymboli()
        PrzebiegTypów(tablica_symboli).wykonaj(drzewo)
    except SemanticError as e:
        raise SemanticError(f"Błąd semantyczny: {e}")
    except Exception as e:
        raise CompilationError(f"Błąd podczas analizy typów: {e}")
    
    # Etap 3: Code generation
    try:
        return GeneratorKodu(tablica_symboli).generuj(drzewo)
    except Exception as e:
        raise CompilationError(f"Błąd podczas generowania kodu: {e}")
