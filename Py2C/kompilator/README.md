# Python → C Transpiler

## Struktura projektu

```
kompilator/
├── py2c.py                  # Główny punkt wejścia transpilera
├── test.py                  # Pliki testowe
├── program                  # Przykładowy program Python do przetłumaczenia
├── output.c                 # Wygenerowany kod C
├── README.md                # Dokumentacja
│
└── backend/                 # Komponenty transpilera
    ├── typy.py              # Definicje typów (int, float, str, bool)
    ├── symbole.py           # Tablica symboli - przechowuje zmienne
    ├── parser.py            # Parser - czyta kod Python
    ├── grammar.lark         # Gramatyka języka Python
    ├── typowanie.py         # Wnioskowanie typów - określa typy zmiennych
    ├── gen_kod.py           # Generowanie kodu C
    └── transpilator.py      # Główny transpiler - łączy wszystkie części
```

## Użycie

python py2c test.py output.c

## Obsługiwane języki Python

- **Typy**: `int`, `float`, `str`, `bool` (True/False, None)
- **Instrukcje**: `if`/`elif`/`else`, `while`, `for range()`, `def`, `return`, `break`, `continue`, `pass`
- **Wyrażenia**: `+`, `-`, `*`, `/`, `//`, `%`, `**`, operatory porównania, logiczne
- **Funkcje wbudowane**: `print()`, `input()`, `int()`, `float()`, `abs()`, `len()`, `min()`, `max()`
- **Funkcje matematyczne**: `sqrt()`, `sin()`, `cos()`, `tan()`, `log()`, `exp()`, `pow()`, itp.
- **Listy**: jako tablice C (stały rozmiar)
- **Operatory**: `+=`, `-=`, `*=`, `/=`, `%=`