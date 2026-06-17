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

    def emit(self, tekst=''):
        if tekst:
            self.linie.append(self.WCIĘCIE * self.poziom_wc + tekst)
        else:
            self.linie.append('')

    def raw_out(self, tekst):
        self.linie.append(tekst)

    def result(self):
        return '\n'.join(self.linie)

    def enter(self, zakres=None):
        if zakres:
            self.zakres = zakres
        self.zadeklarowane.append(set())

    def leave(self, zakres=None):
        self.zadeklarowane.pop()
        if zakres:
            self.zakres = zakres

    def czy_zadeklarowana(self, nazwa):
        return any(nazwa in d for d in self.zadeklarowane)

    def oznacz(self, nazwa):
        self.zadeklarowane[-1].add(nazwa)

    def typ_zmiennej(self, nazwa):
        return self.zakres.typ_zmiennej(nazwa) or CAŁKOWITY

    def wnioskuj_typ(self, node):
        if isinstance(node, Token):
            return CAŁKOWITY
        dane = node.data
        if dane == 'number':
            tekst = str(node.children[0])
            return ZMIENNOPRZECINKOWY if ('.' in tekst or 'e' in tekst.lower()) else CAŁKOWITY
        if dane == 'string':
            return TEKST
        if dane in ('true_lit', 'false_lit', 'none_lit'):
            return CAŁKOWITY
        if dane == 'name':
            nazwa = str(node.children[0])
            return self.zakres.typ_zmiennej(nazwa) or CAŁKOWITY
        if dane == 'binop':
            typy = [self.wnioskuj_typ(d) for d in node.children if isinstance(d, Tree)]
            result = CAŁKOWITY
            for typ in typy:
                result = typ_szerszy(result, typ)
            return result
        if dane in ('compare', 'or_op', 'and_op', 'not_op'):
            return CAŁKOWITY
        if dane == 'unary_op':
            return self.wnioskuj_typ(node.children[1])
        if dane == 'power_op':
            return ZMIENNOPRZECINKOWY
        if dane == 'subscript':
            nazwa = str(node.children[0])
            return self.zakres.typ_zmiennej(nazwa) or CAŁKOWITY
        if dane == 'call':
            nazwa_func = str(node.children[0])
            MAT = {'sqrt', 'pow', 'sin', 'cos', 'tan', 'log', 'log2', 'log10', 'exp', 'ceil', 'floor', 'fabs'}
            if nazwa_func in MAT or nazwa_func == 'float':
                return ZMIENNOPRZECINKOWY
            if nazwa_func in ('int', 'len'):
                return CAŁKOWITY
            if nazwa_func in ('input',):
                return TEKST
            if nazwa_func in ('abs', 'max', 'min'):
                arg_węzły = next(
                    (d for d in node.children[1:] if isinstance(d, Tree) and d.data == 'args'), None
                )
                typy_arg = [self.wnioskuj_typ(d) for d in arg_węzły.children if isinstance(d, Tree)] if arg_węzły else []
                return ZMIENNOPRZECINKOWY if ZMIENNOPRZECINKOWY in typy_arg else CAŁKOWITY
            return self.ts.funkcje.get(nazwa_func, {}).get('zwraca', CAŁKOWITY)
        return CAŁKOWITY

    def generuj(self, drzewo):
        for nagłówek in sorted(self.ts.nagłówki):
            self.raw_out(f'#include {nagłówek}')
        self.raw_out('')

        if self.ts.użyj_bufora_wej:
            self.raw_out('static char __inbuf[256];')
            self.raw_out('')

        for nazwa_func, info_func in self.ts.funkcje.items():
            params = ', '.join(
                deklaracja_c(p_typ, p_nazwa) for p_nazwa, p_typ in info_func['parametry']
            )
            self.raw_out(f'{typ_c(info_func["zwraca"])} {nazwa_func}({params or "void"});')
        if self.ts.funkcje:
            self.raw_out('')

        for node in drzewo.children:
            wew = self.rozpakuj(node)
            if isinstance(wew, Tree) and wew.data == 'func_def':
                self.gen(wew)
                self.raw_out('')

        self.raw_out('int main(void) {')
        self.poziom_wc = 1
        self.enter(self.ts.glob)
        for node in drzewo.children:
            wew = self.rozpakuj(node)
            if isinstance(wew, Tree) and wew.data == 'func_def':
                continue
            self.gen(node)
        self.emit('return 0;')
        self.poziom_wc = 0
        self.leave()
        self.raw_out('}')

        return self.result()

    def rozpakuj(self, node):
        if not isinstance(node, Tree):
            return node
        while node.data in ('stmt', 'simple_stmt') and node.children:
            dziecko = node.children[0]
            if isinstance(dziecko, Tree):
                node = dziecko
            else:
                break
        return node

    def gen(self, node):
        if isinstance(node, Token):
            return str(node)
        if not isinstance(node, Tree):
            return ''
        return getattr(self, 'gen_' + node.data, self.gen_domyślnie)(node)

    def gen_domyślnie(self, node):
        for dziecko in node.children:
            if isinstance(dziecko, Tree):
                self.gen(dziecko)
        return ''

    def gen_stmt(self, node):
        return self.gen(self.rozpakuj(node))

    def gen_simple_stmt(self, node):
        return self.gen(node.children[0])

    def gen_suite(self, node):
        for dziecko in node.children:
            self.gen(dziecko)
        return ''

    def gen_assign(self, node):
        try:
            if not node.children or len(node.children) < 2:
                raise CompilerRuntimeError("Instrukcja przypisania musi mieć nazwę zmiennej i wartość.")
            
            nazwa = str(node.children[0])
            if not nazwa or not isinstance(nazwa, str) or len(nazwa) == 0:
                raise CompilerRuntimeError(f"Nazwa zmiennej nieprawidłowa: '{nazwa}'")
            
            rhs = node.children[1]
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
                    self.emit(f'{typ_c(elem_typ)} {nazwa}[{rozmiar}] = {expr};')
                elif typ == TEKST:
                    self.emit(f'char {nazwa}[256];')
                    self.emit(f'strcpy({nazwa}, {expr});')
                else:
                    self.emit(f'{typ} {nazwa} = {expr};')
            else:
                self.emit(f'strcpy({nazwa}, {expr});' if typ == TEKST else f'{nazwa} = {expr};')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania przypisania: {e}")

    def gen_aug_assign(self, node):
        self.emit(f'{node.children[0]} {node.children[1]} {self.gen(node.children[2])};')

    def gen_return_stmt(self, node):
        if node.children:
            self.emit(f'return {self.gen(node.children[0])};')
        else:
            self.emit('return;')

    def gen_expr_stmt(self, node):
        tekst = self.gen(node.children[0])
        if tekst:
            self.emit(f'{tekst};')

    def gen_pass_stmt(self, node):
        self.emit('/* pass */')

    def gen_break_stmt(self, node):
        self.emit('break;')

    def gen_continue_stmt(self, node):
        self.emit('continue;')

    def gen_if_stmt(self, node):
        dzieci = [d for d in node.children if isinstance(d, Tree)]
        i, pierwszy = 0, True
        while i < len(dzieci):
            dziecko = dzieci[i]
            if dziecko.data == 'suite':
                self.emit('} else {')
                self.poziom_wc += 1
                self.enter()
                for instrukcja in dziecko.children:
                    self.gen(instrukcja)
                self.leave()
                self.poziom_wc -= 1
                i += 1
            else:
                słowo_kluczowe = 'if' if pierwszy else '} else if'
                self.emit(f'{słowo_kluczowe} ({self.gen(dziecko)}) {{')
                self.poziom_wc += 1
                self.enter()
                i += 1
                if i < len(dzieci) and dzieci[i].data == 'suite':
                    for instrukcja in dzieci[i].children:
                        self.gen(instrukcja)
                    i += 1
                self.leave()
                self.poziom_wc -= 1
                pierwszy = False
        self.emit('}')

    def gen_while_stmt(self, node):
        try:
            if not node.children or len(node.children) < 2:
                raise CompilerRuntimeError("Pętla while musi mieć warunek i ciało.")
            
            warunek = self.gen(node.children[0])
            if not warunek:
                raise CompilerRuntimeError("Nie można wygenerować warunku pętli while")
            
            self.emit(f'while ({warunek}) {{')
            self.poziom_wc += 1
            self.enter()
            
            suite = node.children[1]
            if isinstance(suite, Tree) and suite.data == 'suite':
                for dziecko in suite.children:
                    self.gen(dziecko)
            else:
                self.gen(suite)
            
            self.leave()
            self.poziom_wc -= 1
            self.emit('}')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania pętli while: {e}")

    def gen_for_stmt(self, node):
        try:
            if not node.children or len(node.children) < 3:
                raise CompilerRuntimeError("Pętla for musi mieć zmienną, zakres i ciało.")
            
            zmienna = str(node.children[0])
            if not zmienna:
                raise CompilerRuntimeError("Nazwa zmiennej pętli for nie może być pusta")
            
            args_zakresu = node.children[1]
            suite = node.children[2]
            
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
                
                node_kroku = args_zakresu.children[2]
                krok = self.gen(node_kroku)
                if not krok:
                    raise CompilerRuntimeError("Nie można wygenerować kroku pętli for")
                
                ujemny = isinstance(node_kroku, Tree) and node_kroku.data == 'unary_op' and str(node_kroku.children[0]) == '-'
                if not ujemny:
                    try:
                        ujemny = float(krok) < 0
                    except ValueError:
                        pass
                operator = '>' if ujemny else '<'
                nagłówek = f'int {zmienna} = {start_gen}; {zmienna} {operator} {koniec_gen}; {zmienna} += {krok}'

            self.emit(f'for ({nagłówek}) {{')
            self.poziom_wc += 1
            self.enter()
            self.oznacz(zmienna)
            
            if isinstance(suite, Tree) and suite.data == 'suite':
                for dziecko in suite.children:
                    self.gen(dziecko)
            else:
                self.gen(suite)
            
            self.leave()
            self.poziom_wc -= 1
            self.emit('}')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania pętli for: {e}")

    def gen_func_def(self, node):
        try:
            if not node.children:
                raise CompilerRuntimeError("Definicja funkcji musi mieć nazwę.")
            
            nazwa_func = str(node.children[0])
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
            
            self.raw_out(f'{typ_c(info_func["zwraca"])} {nazwa_func}({params or "void"}) {{')
            self.poziom_wc = 1
            zewnętrzny_zakres = self.zakres
            self.enter(info_func['zakres'])
            
            for p_nazwa, _ in info_func['parametry']:
                self.oznacz(p_nazwa)
            
            suite = next((d for d in node.children if isinstance(d, Tree) and d.data == 'suite'), None)
            if suite:
                for dziecko in suite.children:
                    self.gen(dziecko)
            else:
                if len(node.children) > 1:
                    raise CompilerRuntimeError(f"Ciało funkcji '{nazwa_func}' nie znalezione")
            
            self.leave(zewnętrzny_zakres)
            self.poziom_wc = 0
            self.raw_out('}')
        except CompilerRuntimeError:
            raise
        except Exception as e:
            raise CompilerRuntimeError(f"Błąd podczas generowania definicji funkcji: {e}")

    def gen_number(self, node):
        return str(node.children[0])

    def gen_string(self, node):
        return str(node.children[0])

    def gen_true_lit(self, node):
        return '1'

    def gen_false_lit(self, node):
        return '0'

    def gen_none_lit(self, node):
        return 'NULL'

    def gen_name(self, node):
        return str(node.children[0])

    def gen_binop(self, node):
        części = [str(d) if isinstance(d, Token) else self.gen(d) for d in node.children]
        result = części[0]
        i = 1
        while i < len(części) - 1:
            operator = '/' if części[i] == '//' else części[i]
            result = f'({result} {operator} {części[i + 1]})'
            i += 2
        return result

    def gen_compare(self, node):
        części = [self.gen(d) if isinstance(d, Tree) else str(d) for d in node.children]
        if len(części) == 3:
            return f'({części[0]} {części[1]} {części[2]})'
        klauzule = [f'({części[i]} {części[i + 1]} {części[i + 2]})' for i in range(0, len(części) - 2, 2)]
        return '(' + ' && '.join(klauzule) + ')'

    def gen_or_op(self, node):
        return '(' + ' || '.join(self.gen(d) for d in node.children if isinstance(d, Tree)) + ')'

    def gen_and_op(self, node):
        return '(' + ' && '.join(self.gen(d) for d in node.children if isinstance(d, Tree)) + ')'

    def gen_not_op(self, node):
        return f'(!{self.gen(node.children[0])})'

    def gen_unary_op(self, node):
        operator = str(node.children[0])
        expr = self.gen(node.children[1])
        return f'({operator}{expr})'

    def gen_power_op(self, node):
        return f'pow({self.gen(node.children[0])}, {self.gen(node.children[1])})'

    def gen_subscript(self, node):
        return f'{node.children[0]}[{self.gen(node.children[1])}]'

    def gen_list_lit(self, node):
        return '{' + ', '.join(self.gen(d) for d in node.children if isinstance(d, Tree)) + '}'

    def gen_call(self, node):
        try:
            if not node.children:
                raise CompilerRuntimeError("Wywołanie funkcji musi mieć nazwę funkcji")
            
            nazwa_func = str(node.children[0])
            if not nazwa_func:
                raise CompilerRuntimeError("Nazwa funkcji nie może być pusta")
            
            arg_węzły = next(
                (d for d in node.children[1:] if isinstance(d, Tree) and d.data == 'args'), None
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
