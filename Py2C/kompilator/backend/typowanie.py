from lark import Tree, Token
from .typy import CAŁKOWITY, ZMIENNOPRZECINKOWY, TEKST, NIETYP, typ_szerszy, ADNOTACJE
from .errors import SemanticError

class PrzebiegTypów:
    def __init__(self, tablica_symboli):
        self.ts = tablica_symboli
        self._zwraca = NIETYP
        self._w_pętli = 0  # Licznik zagnieżdżenia pętli
        self._w_funkcji = False  # Czy jesteśmy wewnątrz funkcji

    def wykonaj(self, drzewo):
        self.odwiedź(drzewo)

    def _sprawdź_zmienną(self, nazwa):
        """Sprawdza czy zmienna istnieje w aktualnym zaresie."""
        if self.ts.aktualny.typ_zmiennej(nazwa) is None:
            raise SemanticError(f"Niezadeklarowana zmienna: '{nazwa}'")

    def _sprawdź_tablicę(self, nazwa):
        """Sprawdza czy tablica istnieje w aktualnym zaresie."""
        if not self.ts.aktualny.czy_tablica(nazwa):
            raise SemanticError(f"'{nazwa}' nie jest tablicą")

    def _sprawdź_funkcję(self, nazwa, liczba_argumentów=None):
        """Sprawdza czy funkcja istnieje i czy parametry się zgadzają."""
        # Wbudowane funkcje
        WBUDOWANE = {
            'print': -1,  # Zmienna liczba argumentów
            'abs': 1,
            'max': -1,
            'min': -1,
            'len': 1,
            'input': 0,
            'int': 1,
            'float': 1,
            'sqrt': 1,
            'pow': 2,
            'sin': 1, 'cos': 1, 'tan': 1,
            'log': 1, 'log2': 1, 'log10': 1,
            'exp': 1,
            'ceil': 1, 'floor': 1,
            'fabs': 1,
            'str': 1
        }
        
        if nazwa in WBUDOWANE:
            oczekiwana = WBUDOWANE[nazwa]
            if oczekiwana != -1 and liczba_argumentów is not None and liczba_argumentów != oczekiwana:
                raise SemanticError(
                    f"Funkcja '{nazwa}' oczekuje {oczekiwana} argumentu(ów), "
                    f"otrzymała {liczba_argumentów}"
                )
            return True
        
        if nazwa not in self.ts.funkcje:
            raise SemanticError(f"Niezdefiniowana funkcja: '{nazwa}'")
        
        info = self.ts.funkcje[nazwa]
        oczekiwana = len(info['parametry'])
        if liczba_argumentów is not None and liczba_argumentów != oczekiwana:
            raise SemanticError(
                f"Funkcja '{nazwa}' oczekuje {oczekiwana} parametru(ów), "
                f"otrzymała {liczba_argumentów}"
            )
        return True

    def odwiedź(self, node):
        if isinstance(node, Token):
            return CAŁKOWITY
        return getattr(self, 'odw_' + node.data, self.odw_domyślnie)(node)

    def odw_domyślnie(self, node):
        for dziecko in node.children:
            self.odwiedź(dziecko)
        return CAŁKOWITY

    def odw_start(self, node):
        for dziecko in node.children:
            self.odwiedź(dziecko)

    def odw_simple_stmt(self, node):
        return self.odwiedź(node.children[0])

    def odw_stmt(self, node):
        return self.odwiedź(node.children[0])

    def odw_suite(self, node):
        for dziecko in node.children:
            self.odwiedź(dziecko)

    def odw_assign(self, node):
        """Przypisanie zmiennej - sprawdzamy poprawność typów i zmiennych."""
        nazwa = str(node.children[0])
        if not nazwa or len(nazwa.strip()) == 0:
            raise SemanticError("Nazwa zmiennej nie może być pusta")
        
        rhs = node.children[1]
        if isinstance(rhs, Tree) and rhs.data == 'list_lit':
            elementy = [d for d in rhs.children if isinstance(d, Tree)]
            elem_typ = CAŁKOWITY
            for e in elementy:
                elem_typ = typ_szerszy(elem_typ, self.odwiedź(e))
            self.ts.aktualny.def_tablica(nazwa, elem_typ, len(elementy))
            return elem_typ
        
        typ = self.odwiedź(rhs)
        
        if self.ts.aktualny.ma_lokalne(nazwa):
            typ_stary = self.ts.aktualny.zmienne.get(nazwa)
            if typ_stary is not None:
                # Możemy zmienić typ zmiennej jeśli jest kompatybilny
                self.ts.aktualny.zmienne[nazwa] = typ_szerszy(typ_stary, typ)
            else:
                self.ts.aktualny.zmienne[nazwa] = typ
        else:
            self.ts.aktualny.def_zmienna(nazwa, typ)
        return typ

    def odw_aug_assign(self, node):
        return self.odwiedź(node.children[2])

    def odw_if_stmt(self, node):
        for dziecko in node.children:
            self.odwiedź(dziecko)

    def odw_while_stmt(self, node):
        self._w_pętli += 1
        try:
            for dziecko in node.children:
                self.odwiedź(dziecko)
        finally:
            self._w_pętli -= 1

    def odw_return_stmt(self, node):
        if not self._w_funkcji:
            raise SemanticError("'return' poza funkcją")
        typ = self.odwiedź(node.children[0]) if node.children else NIETYP
        self._zwraca = typ_szerszy(self._zwraca, typ)
        return typ

    def odw_for_stmt(self, node):
        zmienna = str(node.children[0])
        if not self.ts.aktualny.ma_lokalne(zmienna):
            self.ts.aktualny.def_zmienna(zmienna, CAŁKOWITY)
        
        self._w_pętli += 1
        try:
            for dziecko in node.children[1:]:
                self.odwiedź(dziecko)
        finally:
            self._w_pętli -= 1

    def odw_break_stmt(self, node):
        if self._w_pętli == 0:
            raise SemanticError("'break' poza pętlą")
        return NIETYP

    def odw_continue_stmt(self, node):
        if self._w_pętli == 0:
            raise SemanticError("'continue' poza pętlą")
        return NIETYP

    def odw_func_def(self, node):
        """Analiza definicji funkcji z obsługą błędów semantycznych."""
        try:
            if not node.children:
                raise SemanticError("Definicja funkcji musi mieć nazwę")
            
            nazwa_func = str(node.children[0])
            if not nazwa_func or len(nazwa_func) == 0:
                raise SemanticError("Nazwa funkcji nie może być pusta")
            
            zakres = self.ts.enter()
            parametry = []
            stary_zwraca = self._zwraca
            stara_w_funkcji = self._w_funkcji
            self._zwraca = NIETYP
            self._w_funkcji = True  # Ustawiamy że jesteśmy w funkcji
            
            for dziecko in node.children[1:]:
                if not isinstance(dziecko, Tree):
                    continue
                if dziecko.data == 'params':
                    for param in dziecko.children:
                        if not isinstance(param, Tree) or not param.children:
                            raise SemanticError(f"Nieprawidłowy parametr w funkcji '{nazwa_func}'")
                        
                        p_nazwa = str(param.children[0])
                        if not p_nazwa:
                            raise SemanticError(f"Nazwa parametru nie może być pusta w funkcji '{nazwa_func}'")
                        
                        if param.data == 'param' and len(param.children) > 1:
                            p_typ = ADNOTACJE.get(str(param.children[1]), CAŁKOWITY)
                        else:
                            p_typ = CAŁKOWITY
                        
                        zakres.def_zmienna(p_nazwa, p_typ)
                        parametry.append((p_nazwa, p_typ))
                elif dziecko.data == 'suite':
                    self.odwiedź(dziecko)
            
            typ_zwrotu = self._zwraca
            self._zwraca = stary_zwraca
            self._w_funkcji = stara_w_funkcji
            self.ts.leave()
            self.ts.funkcje[nazwa_func] = {
                'zwraca': typ_zwrotu,
                'parametry': parametry,
                'zakres': zakres
            }
            self.ts.glob.def_zmienna(nazwa_func, typ_zwrotu)
        except SemanticError:
            raise
        except Exception as e:
            raise SemanticError(f"Błąd podczas analizy definicji funkcji: {e}")

    def odw_number(self, node):
        tekst = str(node.children[0])
        return ZMIENNOPRZECINKOWY if ('.' in tekst or 'e' in tekst.lower()) else CAŁKOWITY

    def odw_string(self, node):
        self.ts.nagłówki.add('<string.h>')
        return TEKST

    def odw_true_lit(self, node):
        return CAŁKOWITY

    def odw_false_lit(self, node):
        return CAŁKOWITY

    def odw_none_lit(self, node):
        return CAŁKOWITY

    def odw_name(self, node):
        """Dostęp do zmiennej - sprawdzamy czy istnieje."""
        nazwa = str(node.children[0])
        typ = self.ts.aktualny.typ_zmiennej(nazwa)
        if typ is None:
            raise SemanticError(f"Niezadeklarowana zmienna: '{nazwa}'")
        return typ

    def odw_binop(self, node):
        typy = [self.odwiedź(d) for d in node.children if isinstance(d, Tree)]
        result = CAŁKOWITY
        for typ in typy:
            result = typ_szerszy(result, typ)
        return result

    def odw_compare(self, node):
        for dziecko in node.children:
            if isinstance(dziecko, Tree):
                self.odwiedź(dziecko)
        return CAŁKOWITY

    def odw_or_op(self, node):
        for dziecko in node.children:
            if isinstance(dziecko, Tree):
                self.odwiedź(dziecko)
        return CAŁKOWITY

    def odw_and_op(self, node):
        return self.odw_or_op(node)

    def odw_not_op(self, node):
        self.odwiedź(node.children[0])
        return CAŁKOWITY

    def odw_unary_op(self, node):
        return self.odwiedź(node.children[1])

    def odw_power_op(self, node):
        self.ts.nagłówki.add('<math.h>')
        return ZMIENNOPRZECINKOWY

    def odw_call(self, node):
        """Wywołanie funkcji - sprawdzamy czy funkcja istnieje i parametry."""
        nazwa_func = str(node.children[0])
        arg_węzły = next(
            (d for d in node.children[1:] if isinstance(d, Tree) and d.data == 'args'), None
        )
        typy_arg = [self.odwiedź(d) for d in arg_węzły.children if isinstance(d, Tree)] if arg_węzły else []
        liczba_arg = len(typy_arg)
        
        # Sprawdzamy czy funkcja istnieje
        self._sprawdź_funkcję(nazwa_func, liczba_arg)

        MAT = {'sqrt', 'pow', 'sin', 'cos', 'tan', 'log', 'log2', 'log10', 'exp', 'ceil', 'floor', 'fabs'}
        if nazwa_func in MAT:
            self.ts.nagłówki.add('<math.h>')
            return ZMIENNOPRZECINKOWY
        if nazwa_func in ('abs', 'max', 'min'):
            self.ts.nagłówki.add('<stdlib.h>')
            return ZMIENNOPRZECINKOWY if ZMIENNOPRZECINKOWY in typy_arg else CAŁKOWITY
        if nazwa_func == 'input':
            self.ts.nagłówki.update({'<string.h>', '<stdio.h>'})
            self.ts.użyj_bufora_wej = True
            return TEKST
        if nazwa_func in ('int', 'float'):
            self.ts.nagłówki.add('<stdlib.h>')
            return CAŁKOWITY if nazwa_func == 'int' else ZMIENNOPRZECINKOWY
        if nazwa_func == 'len':
            return CAŁKOWITY
        if nazwa_func == 'str':
            return TEKST
        if nazwa_func == 'print':
            return CAŁKOWITY
        return self.ts.funkcje.get(nazwa_func, {}).get('zwraca', CAŁKOWITY)

    def odw_subscript(self, node):
        """Dostęp do elementu tablicy - sprawdzamy czy tablica istnieje."""
        nazwa = str(node.children[0])
        if self.ts.aktualny.typ_zmiennej(nazwa) is None:
            raise SemanticError(f"Niezadeklarowana zmienna: '{nazwa}'")
        if not self.ts.aktualny.czy_tablica(nazwa):
            raise SemanticError(f"'{nazwa}' nie jest tablicą")
        return self.ts.aktualny.typ_zmiennej(nazwa) or CAŁKOWITY

    def odw_list_lit(self, node):
        typy = [self.odwiedź(d) for d in node.children if isinstance(d, Tree)]
        result = CAŁKOWITY
        for typ in typy:
            result = typ_szerszy(result, typ)
        return result

    def odw_expr_stmt(self, node):
        return self.odwiedź(node.children[0])

    def odw_pass_stmt(self, node):
        return NIETYP

    def odw_break_stmt(self, node):
        return NIETYP

    def odw_continue_stmt(self, node):
        return NIETYP
