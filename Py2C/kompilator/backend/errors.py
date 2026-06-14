"""Moduł definiujący niestandardowe wyjątki kompilera."""

class CompilationError(Exception):
    """Ogólny błąd kompilacji."""
    pass

class SyntaxError(CompilationError):
    """Błąd składni w kodzie źródłowym."""
    pass

class SemanticError(CompilationError):
    """Błąd semantyczny (błąd typów, niezdefiniowane zmienne, itp.)."""
    pass

class RuntimeError(CompilationError):
    """Błąd czasu wykonania podczas generowania kodu."""
    pass
