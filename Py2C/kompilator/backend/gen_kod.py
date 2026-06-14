from lark import Tree, Token
from .typy import CAŁKOWITY, ZMIENNOPRZECINKOWY, TEKST, NIETYP, typ_szerszy, typ_c, format_printf, deklaracja_c
from .errors import RuntimeError as CompilerRuntimeError

class GeneratorKodu:
    WCIĘCIE = '    '

    def __init__(self, tablica_symboli):
        if not tablica_symboli:
            raise CompilerRuntimeError("Tablica symboli nie może być pusta.")
        self.ts = tablica_symboli
        self.linie = []
        self.poziom_wc = 0
        self.zakres = tablica_symboli.glob
        self.zadeklarowane = [set()]

    def emituj(self, tekst=''):
        if tekst:
            self.linie.append(self.WCIĘCIE * self.poziom_wc + tekst)
        else:
            self.linie.append('')

    def surowo(self, tekst):
        self.linie.append(tekst)

    def wynik(self):
        return '\n'.join(self.linie)

    def wejdź(self, zakres=None):
        if zakres:
            self.zakres = zakres
        self.zadeklarowane.append(set())

    def wyjdź(self, zakres=None):
        self.zadeklarowane.pop()
        if zakres:
            self.zakres = zakres

    def czy_zadeklarowana(self, nazwa):
        return any(nazwa in d for d in self.zadeklarowane)

    def oznacz(self, nazwa):
        self.zadeklarowane[-1].add(nazwa)

    def typ_zmiennej(self, nazwa):
        return self.zakres.typ_zmiennej(nazwa) or CAŁKOWITY

    def wnioskuj_typ(self, węzeł):
        if isinstance(węzeł, Token):
            return CAŁKOWITY
        dane = węzeł.data
        if dane == 'number':
            tekst = str(węzeł.children[0])
            return ZMIENNOPRZECINKOWY if ('.' in tekst or 'e' in tekst.lower()) else CAŁKOWITY
        if dane == 'string':
            return TEKST
        if dane in ('true_lit', 'false_lit', 'none_lit'):
            return CAŁKOWITY
        if dane == 'name':
            nazwa = str(węzeł.children[0])
            return self.zakres.typ_zmiennej(nazwa) or CAŁKOWITY
        if dane == 'binop':
            typy = [self.wnioskuj_typ(d) for d in węzeł.children if isinstance(d, Tree)]
            wynik = CAŁKOWITY
            for typ in typy:
                wynik = typ_szerszy(wynik, typ)
            return wynik
        if dane in ('compare', 'or_op', 'and_op', 'not_op'):
            return CAŁKOWITY
        if dane == 'unary_op':
            return self.wnioskuj_typ(węzeł.children[1])
        if dane == 'power_op':
            return ZMIENNOPRZECINKOWY
        if dane == 'subscript':
            nazwa = str(węzeł.children[0])
            return self.zakres.typ_zmiennej(nazwa) or CAŁKOWITY
        if dane == 'call':
            nazwa_func = str(węzeł.children[0])
            MAT = {'sqrt', 'pow', 'sin', 'cos', 'tan', 'log', 'log2', 'log10', 'exp', 'ceil', 'floor', 'fabs'}
            if nazwa_func in MAT or nazwa_func == 'float':
                return ZMIENNOPRZECINKOWY
            if nazwa_func in ('int', 'len'):
                return CAŁKOWITY
            if nazwa_func in ('input',):
                return TEKST
            if nazwa_func in ('abs', 'max', 'min'):
                arg_węzły = next(
                    (d for d in węzeł.children[1:] if isinstance(d, Tree) and d.data == 'args'), None
                )
                typy_arg = [self.wnioskuj_typ(d) for d in arg_węzły.children if isinstance(d, Tree)] if arg_węzły else []
                return ZMIENNOPRZECINKOWY if ZMIENNOPRZECINKOWY in typy_arg else CAŁKOWITY
            return self.ts.funkcje.get(nazwa_func, {}).get('zwraca', CAŁKOWITY)
        return CAŁKOWITY

    def generuj(self, drzewo):
        for nagłówek in sorted(self.ts.nagłówki):
            self.surowo(f'#include {nagłówek}')
        self.surowo('')

        if self.ts.użyj_bufora_wej:
            self.surowo('static char __inbuf[256];')
            self.surowo('')

        for nazwa_func, info_func in self.ts.funkcje.items():
            params = ', '.join(
                deklaracja_c(p_typ, p_nazwa) for p_nazwa, p_typ in info_func['parametry']
            )
            self.surowo(f'{typ_c(info_func["zwraca"])} {nazwa_func}({params or "void"});')
        if self.ts.funkcje:
            self.surowo('')

        for węzeł in drzewo.children:
            wew = self.rozpakuj(węzeł)
            if isinstance(wew, Tree) and wew.data == 'func_def':
                self.gen(wew)
                self.surowo('')

        self.surowo('int main(void) {')
        self.poziom_wc = 1
        self.wejdź(self.ts.glob)
        for węzeł in drzewo.children:
            wew = self.rozpakuj(węzeł)
            if isinstance(wew, Tree) and wew.data == 'func_def':
                continue
            self.gen(węzeł)
        self.emituj('return 0;')
        self.poziom_wc = 0
        self.wyjdź()
        self.surowo('}')

        return self.wynik()

    def rozpakuj(self, węzeł):
        if not isinstance(węzeł, Tree):
            return węzeł
        while węzeł.data in ('stmt', 'simple_stmt') and węzeł.children:
            dziecko = węzeł.children[0]
            if isinstance(dziecko, Tree):
                węzeł = dziecko
            else:
                break
        return węzeł

    def gen(self, węzeł):
        if isinstance(węzeł, Token):
            return str(węzeł)
        if not isinstance(węzeł, Tree):
            return ''
        return getattr(self, 'gen_' + węzeł.data, self.gen_domyślnie)(węzeł)

    def gen_domyślnie(self, węzeł):
        for dziecko in węzeł.children:
            if isinstance(dziecko, Tree):
                self.gen(dziecko)
        return ''

    def gen_stmt(self, węzeł):
        return self.gen(self.rozpakuj(węzeł))

    def gen_simple_stmt(self, węzeł):
        return self.gen(węzeł.children[0])

    def gen_suite(self, węzeł):
        for dziecko in węzeł.children:
            self.gen(dziecko)
        return ''

    def gen_assign(self, węzeł):
        try:
            if not węzeł.children or len(węzeł.children) < 2:
                raise CompilerRuntimeError("Instrukcja przypisania musi mieć nazwę zmiennej i wartość.")
            
            nazwa = str(węzeł.children[0])
            if not nazwa or not isinstance(nazwa, str) or len(nazwa) == 0:
                raise CompilerRuntimeError(f"Nazwa zmiennej nieprawidłowa: '{nazwa}'")
            
            rhs = węzeł.children[1]
            typ = self.typ_zmiennej(nazwa)
            expr = self.gen(rhs)
            
            if not expr:
                raise CompilerRuntimeError(f"Nie można wygenerować wyrażenia dla przypisania zmiennej '{nazwa}'")
            
            if not self.czy_zadeklarowana(nazwa):
                self.oznacz(nazwa)
                if self.zakres.czy_tablica(nazwa):
                    elem_typ, rozmiar = self.zakres.info_tablicy(nazwa)
                    if rozmiar is None or rozmiar <= 0:
                        raise CompilerRuntimeError(f"Nieprawidłowy rozmiar tablicy '{nazwa}'")
                    self.emituj(f'{typ_c(elem_typ)} {nazwa}[{rozmiar}] = {expr};')
                elif typ == TEKST:
                    self.emituj(f'char {nazwa}[256];')
                    self.emituj(f'strcpy({nazwa}, {expr});')
                else:
                    self.emituj(f'{typ} {nazwa} = {expr};')
            else:
                self.emituj(f'strcpy({nazwa}, {expr});' if typ == TEKST else f'{nazwa} = {expr};')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania przypisania: {e}")

    def gen_aug_assign(self, węzeł):
        self.emituj(f'{węzeł.children[0]} {węzeł.children[1]} {self.gen(węzeł.children[2])};')

    def gen_return_stmt(self, węzeł):
        if węzeł.children:
            self.emituj(f'return {self.gen(węzeł.children[0])};')
        else:
            self.emituj('return;')

    def gen_expr_stmt(self, węzeł):
        tekst = self.gen(węzeł.children[0])
        if tekst:
            self.emituj(f'{tekst};')

    def gen_pass_stmt(self, węzeł):
        self.emituj('/* pass */')

    def gen_break_stmt(self, węzeł):
        self.emituj('break;')

    def gen_continue_stmt(self, węzeł):
        self.emituj('continue;')

    def gen_if_stmt(self, węzeł):
        dzieci = [d for d in węzeł.children if isinstance(d, Tree)]
        i, pierwszy = 0, True
        while i < len(dzieci):
            dziecko = dzieci[i]
            if dziecko.data == 'suite':
                self.emituj('} else {')
                self.poziom_wc += 1
                self.wejdź()
                for instrukcja in dziecko.children:
                    self.gen(instrukcja)
                self.wyjdź()
                self.poziom_wc -= 1
                i += 1
            else:
                słowo_kluczowe = 'if' if pierwszy else '} else if'
                self.emituj(f'{słowo_kluczowe} ({self.gen(dziecko)}) {{')
                self.poziom_wc += 1
                self.wejdź()
                i += 1
                if i < len(dzieci) and dzieci[i].data == 'suite':
                    for instrukcja in dzieci[i].children:
                        self.gen(instrukcja)
                    i += 1
                self.wyjdź()
                self.poziom_wc -= 1
                pierwszy = False
        self.emituj('}')

    def gen_while_stmt(self, węzeł):
        try:
            if not węzeł.children or len(węzeł.children) < 2:
                raise CompilerRuntimeError("Pętla while musi mieć warunek i ciało.")
            
            warunek = self.gen(węzeł.children[0])
            if not warunek:
                raise CompilerRuntimeError("Nie można wygenerować warunku pętli while")
            
            self.emituj(f'while ({warunek}) {{')
            self.poziom_wc += 1
            self.wejdź()
            
            suite = węzeł.children[1]
            if isinstance(suite, Tree) and suite.data == 'suite':
                for dziecko in suite.children:
                    self.gen(dziecko)
            else:
                self.gen(suite)
            
            self.wyjdź()
            self.poziom_wc -= 1
            self.emituj('}')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania pętli while: {e}")

    def gen_for_stmt(self, węzeł):
        try:
            if not węzeł.children or len(węzeł.children) < 3:
                raise CompilerRuntimeError("Pętla for musi mieć zmienną, zakres i ciało.")
            
            zmienna = str(węzeł.children[0])
            if not zmienna:
                raise CompilerRuntimeError("Nazwa zmiennej pętli for nie może być pusta")
            
            args_zakresu = węzeł.children[1]
            suite = węzeł.children[2]
            
            if not isinstance(args_zakresu, Tree):
                raise CompilerRuntimeError("Zakres pętli for musi być węzłem drzewa")

            if args_zakresu.data == 'range1':
                koniec_gen = self.gen(args_zakresu.children[0])
                if not koniec_gen:
                    raise CompilerRuntimeError("Nie można wygenerować końca zakresu pętli for")
                nagłówek = f'int {zmienna} = 0; {zmienna} < {koniec_gen}; {zmienna}++'
            elif args_zakresu.data == 'range2':
                start_gen = self.gen(args_zakresu.children[0])
                koniec_gen = self.gen(args_zakresu.children[1])
                if not start_gen or not koniec_gen:
                    raise CompilerRuntimeError("Nie można wygenerować zakresu pętli for")
                nagłówek = f'int {zmienna} = {start_gen}; {zmienna} < {koniec_gen}; {zmienna}++'
            else:
                start_gen = self.gen(args_zakresu.children[0])
                koniec_gen = self.gen(args_zakresu.children[1])
                if not start_gen or not koniec_gen:
                    raise CompilerRuntimeError("Nie można wygenerować zakresu pętli for")
                
                węzeł_kroku = args_zakresu.children[2]
                krok = self.gen(węzeł_kroku)
                if not krok:
                    raise CompilerRuntimeError("Nie można wygenerować kroku pętli for")
                
                ujemny = isinstance(węzeł_kroku, Tree) and węzeł_kroku.data == 'unary_op' and str(węzeł_kroku.children[0]) == '-'
                if not ujemny:
                    try:
                        ujemny = float(krok) < 0
                    except ValueError:
                        pass
                operator = '>' if ujemny else '<'
                nagłówek = f'int {zmienna} = {start_gen}; {zmienna} {operator} {koniec_gen}; {zmienna} += {krok}'

            self.emituj(f'for ({nagłówek}) {{')
            self.poziom_wc += 1
            self.wejdź()
            self.oznacz(zmienna)
            
            if isinstance(suite, Tree) and suite.data == 'suite':
                for dziecko in suite.children:
                    self.gen(dziecko)
            else:
                self.gen(suite)
            
            self.wyjdź()
            self.poziom_wc -= 1
            self.emituj('}')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania pętli for: {e}")

    def gen_func_def(self, węzeł):
        try:
            if not węzeł.children:
                raise CompilerRuntimeError("Definicja funkcji musi mieć nazwę.")
            
            nazwa_func = str(węzeł.children[0])
            if not nazwa_func:
                raise CompilerRuntimeError("Nazwa funkcji nie może być pusta")
            
            info_func = self.ts.funkcje.get(nazwa_func, {
                'zwraca': NIETYP,
                'parametry': [],
                'zakres': self.ts.glob
            })
            
            params = ', '.join(
                deklaracja_c(p_typ, p_nazwa) for p_nazwa, p_typ in info_func['parametry']
            )
            
            self.surowo(f'{typ_c(info_func["zwraca"])} {nazwa_func}({params or "void"}) {{')
            self.poziom_wc = 1
            zewnętrzny_zakres = self.zakres
            self.wejdź(info_func['zakres'])
            
            for p_nazwa, _ in info_func['parametry']:
                self.oznacz(p_nazwa)
            
            suite = next((d for d in węzeł.children if isinstance(d, Tree) and d.data == 'suite'), None)
            if suite:
                for dziecko in suite.children:
                    self.gen(dziecko)
            else:
                if len(węzeł.children) > 1:
                    raise CompilerRuntimeError(f"Ciało funkcji '{nazwa_func}' nie znalezione")
            
            self.wyjdź(zewnętrzny_zakres)
            self.poziom_wc = 0
            self.surowo('}')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania definicji funkcji: {e}")

    def gen_number(self, węzeł):
        return str(węzeł.children[0])

    def gen_string(self, węzeł):
        return str(węzeł.children[0])

    def gen_true_lit(self, węzeł):
        return '1'

    def gen_false_lit(self, węzeł):
        return '0'

    def gen_none_lit(self, węzeł):
        return 'NULL'

    def gen_name(self, węzeł):
        return str(węzeł.children[0])

    def gen_binop(self, węzeł):
        części = [str(d) if isinstance(d, Token) else self.gen(d) for d in węzeł.children]
        wynik = części[0]
        i = 1
        while i < len(części) - 1:
            operator = '/' if części[i] == '//' else części[i]
            wynik = f'({wynik} {operator} {części[i + 1]})'
            i += 2
        return wynik

    def gen_compare(self, węzeł):
        części = [self.gen(d) if isinstance(d, Tree) else str(d) for d in węzeł.children]
        if len(części) == 3:
            return f'({części[0]} {części[1]} {części[2]})'
        klauzule = [f'({części[i]} {części[i + 1]} {części[i + 2]})' for i in range(0, len(części) - 2, 2)]
        return '(' + ' && '.join(klauzule) + ')'

    def gen_or_op(self, węzeł):
        return '(' + ' || '.join(self.gen(d) for d in węzeł.children if isinstance(d, Tree)) + ')'

    def gen_and_op(self, węzeł):
        return '(' + ' && '.join(self.gen(d) for d in węzeł.children if isinstance(d, Tree)) + ')'

    def gen_not_op(self, węzeł):
        return f'(!{self.gen(węzeł.children[0])})'

    def gen_unary_op(self, węzeł):
        operator = str(węzeł.children[0])
        expr = self.gen(węzeł.children[1])
        return f'({operator}{expr})'

    def gen_power_op(self, węzeł):
        return f'pow({self.gen(węzeł.children[0])}, {self.gen(węzeł.children[1])})'

    def gen_subscript(self, węzeł):
        return f'{węzeł.children[0]}[{self.gen(węzeł.children[1])}]'

    def gen_list_lit(self, węzeł):
        return '{' + ', '.join(self.gen(d) for d in węzeł.children if isinstance(d, Tree)) + '}'

    def gen_call(self, węzeł):
        try:
            if not węzeł.children:
                raise CompilerRuntimeError("Wywołanie funkcji musi mieć nazwę funkcji")
            
            nazwa_func = str(węzeł.children[0])
            if not nazwa_func:
                raise CompilerRuntimeError("Nazwa funkcji nie może być pusta")
            
            arg_węzły = next(
                (d for d in węzeł.children[1:] if isinstance(d, Tree) and d.data == 'args'), None
            )
            węzły_arg = [d for d in arg_węzły.children if isinstance(d, Tree)] if arg_węzły else []
            argumenty = [self.gen(d) for d in węzły_arg]
            
            # Sprawdzenie czy wszystkie argumenty zostały wygenerowane
            for i, arg in enumerate(argumenty):
                if not arg:
                    raise CompilerRuntimeError(f"Nie można wygenerować argumentu {i+1} funkcji '{nazwa_func}'")
            
            wbudowana = self.wbudowana(nazwa_func, argumenty, węzły_arg)
            if wbudowana:
                return wbudowana
            
            return f'{nazwa_func}({", ".join(argumenty)})'
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania wywołania funkcji '{nazwa_func}': {e}")

    def wbudowana(self, nazwa_func, argumenty, węzły_arg):
        try:
            if nazwa_func == 'print':
                if not argumenty:
                    return 'printf("\\n")'
                formaty = ' '.join(format_printf(self.wnioskuj_typ(w)) for w in węzły_arg)
                return f'printf("{formaty}\\n", {", ".join(argumenty)})'

            if nazwa_func == 'input':
                prompt = argumenty[0] if argumenty else '""'
                return (f'(printf({prompt}), fflush(stdout), fgets(__inbuf, 256, stdin), '
                        f'(__inbuf[strlen(__inbuf)-1]==\'\\n\'?(__inbuf[strlen(__inbuf)-1]=\'\\0\'):0), '
                        f'__inbuf)')

            if nazwa_func == 'int':
                if not argumenty:
                    return '0'
                return (f'atoi({argumenty[0]})'
                        if węzły_arg and self.wnioskuj_typ(węzły_arg[0]) == TEKST
                        else f'((int)({argumenty[0]}))')

            if nazwa_func == 'float':
                if not argumenty:
                    return '0.0'
                return (f'atof({argumenty[0]})'
                        if węzły_arg and self.wnioskuj_typ(węzły_arg[0]) == TEKST
                        else f'((double)({argumenty[0]}))')

            if nazwa_func == 'abs':
                if not argumenty:
                    return '0'
                return (f'fabs({argumenty[0]})'
                        if węzły_arg and self.wnioskuj_typ(węzły_arg[0]) == ZMIENNOPRZECINKOWY
                        else f'abs({argumenty[0]})')

            if nazwa_func == 'len':
                if not argumenty:
                    return '0'
                if węzły_arg and węzły_arg[0].data == 'name':
                    nazwa_zmiennej = str(węzły_arg[0].children[0])
                    rozmiar = self.zakres.info_tablicy(nazwa_zmiennej)[1]
                    if rozmiar:
                        return str(rozmiar)
                return f'strlen({argumenty[0]})'

            if nazwa_func == 'max' and len(argumenty) == 2:
                a, b = argumenty
                return f'(({a})>({b})?({a}):({b}))'
            
            if nazwa_func == 'min' and len(argumenty) == 2:
                a, b = argumenty
                return f'(({a})<({b})?({a}):({b}))'

            MAT = {'sqrt', 'sin', 'cos', 'tan', 'log', 'log2', 'log10', 'exp', 'ceil', 'floor', 'fabs', 'pow'}
            if nazwa_func in MAT:
                return f'{nazwa_func}({", ".join(argumenty)})'

            return None
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd w wbudowanej funkcji '{nazwa_func}': {e}")
