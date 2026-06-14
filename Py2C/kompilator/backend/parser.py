from lark import Lark, LarkError
from lark.indenter import PythonIndenter
from .errors import CompilationError
import os

def load_parser():
    """Wczytuje i konfiguruje parser z gramatyką."""
    grammar_path = "backend/grammar.lark"
    
    # Sprawdzenie istnienia pliku gramatyki
    if not os.path.exists(grammar_path):
        raise CompilationError(f"Plik gramatyki '{grammar_path}' nie znaleziony.")
    
    try:
        with open(grammar_path, 'r', encoding='utf-8') as f:
            grammar = f.read()
    except IOError as e:
        raise CompilationError(f"Błąd czytania gramatyki: {e}")
    
    if not grammar.strip():
        raise CompilationError(f"Plik gramatyki '{grammar_path}' jest pusty.")
    
    try:
        return Lark(grammar, parser='earley', postlex=PythonIndenter(), start='start')
    except LarkError as e:
        raise CompilationError(f"Błąd w gramatyce: {e}")

try:
    PARSER = load_parser()
except CompilationError as e:
    raise CompilationError(f"Nie można załadować parsera: {e}")
