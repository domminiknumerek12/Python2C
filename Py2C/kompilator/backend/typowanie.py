from lark import Tree, Token
from .typy import CAŁKOWITY, ZMIENNOPRZECINKOWY, TEKST, NIETYP, typ_szerszy, ADNOTACJE

class PrzebiegTypów:
    def __init__(self, tablica_symboli):
        self.ts = tablica_symboli
        self._zwraca = NIETYP

    def wykonaj(self, drzewo):
        self.odwiedź(drzewo)

    def odwiedź(self, węzeł):
        if isinstance(węzeł, Token):
            return CAŁKOWITY
        return getattr(self, 'odw_' + węzeł.data, self.odw_domyślnie)(węzeł)

    def odw_domyślnie(self, węzeł):
        for dziecko in węzeł.children:
            self.odwiedź(dziecko)
        return CAŁKOWITY

    def odw_start(self, węzeł):
        for dziecko in węzeł.children:
            self.odwiedź(dziecko)

    def odw_simple_stmt(self, węzeł):
        return self.odwiedź(węzeł.children[0])

    def odw_stmt(self, węzeł):
        return self.odwiedź(węzeł.children[0])

    def odw_suite(self, węzeł):
        for dziecko in węzeł.children:
            self.odwiedź(dziecko)

    def odw_assign(self, węzeł):
        nazwa = str(węzeł.children[0])
        rhs = węzeł.children[1]
        if isinstance(rhs, Tree) and rhs.data == 'list_lit':
            elementy = [d for d in rhs.children if isinstance(d, Tree)]
            elem_typ = CAŁKOWITY
            for e in elementy:
                elem_typ = typ_szerszy(elem_typ, self.odwiedź(e))
            self.ts.aktualny.def_tablica(nazwa, elem_typ, len(elementy))
            return elem_typ
        typ = self.odwiedź(rhs)
        if self.ts.aktualny.ma_lokalne(nazwa):
            self.ts.aktualny.zmienne[nazwa] = typ_szerszy(
                self.ts.aktualny.zmienne.get(nazwa, typ), typ
            )
        else:
            self.ts.aktualny.def_zmienna(nazwa, typ)
        return typ

    def odw_aug_assign(self, węzeł):
        return self.odwiedź(węzeł.children[2])

    def odw_if_stmt(self, węzeł):
        for dziecko in węzeł.children:
            self.odwiedź(dziecko)

    def odw_while_stmt(self, węzeł):
        for dziecko in węzeł.children:
            self.odwiedź(dziecko)

    def odw_return_stmt(self, węzeł):
        typ = self.odwiedź(węzeł.children[0]) if węzeł.children else NIETYP
        self._zwraca = typ_szerszy(self._zwraca, typ)
        return typ

    def odw_for_stmt(self, węzeł):
        zmienna = str(węzeł.children[0])
        if not self.ts.aktualny.ma_lokalne(zmienna):
            self.ts.aktualny.def_zmienna(zmienna, CAŁKOWITY)
        for dziecko in węzeł.children[1:]:
            self.odwiedź(dziecko)

    def odw_func_def(self, węzeł):
        nazwa_func = str(węzeł.children[0])
        zakres = self.ts.wejdź()
        parametry = []
        stary_zwraca, self._zwraca = self._zwraca, NIETYP
        for dziecko in węzeł.children[1:]:
            if not isinstance(dziecko, Tree):
                continue
            if dziecko.data == 'params':
                for param in dziecko.children:
                    p_nazwa = str(param.children[0])
                    p_typ = ADNOTACJE.get(
                        str(param.children[1]), CAŁKOWITY
                    ) if len(param.children) > 1 else CAŁKOWITY
                    zakres.def_zmienna(p_nazwa, p_typ)
                    parametry.append((p_nazwa, p_typ))
            elif dziecko.data == 'suite':
                self.odwiedź(dziecko)
        typ_zwrotu = self._zwraca
        self._zwraca = stary_zwraca
        self.ts.wyjdź()
        self.ts.funkcje[nazwa_func] = {
            'zwraca': typ_zwrotu,
            'parametry': parametry,
            'zakres': zakres
        }
        self.ts.glob.def_zmienna(nazwa_func, typ_zwrotu)

    def odw_number(self, węzeł):
        tekst = str(węzeł.children[0])
        return ZMIENNOPRZECINKOWY if ('.' in tekst or 'e' in tekst.lower()) else CAŁKOWITY

    def odw_string(self, węzeł):
        self.ts.nagłówki.add('<string.h>')
        return TEKST

    def odw_true_lit(self, węzeł):
        return CAŁKOWITY

    def odw_false_lit(self, węzeł):
        return CAŁKOWITY

    def odw_none_lit(self, węzeł):
        return CAŁKOWITY

    def odw_name(self, węzeł):
        nazwa = str(węzeł.children[0])
        return self.ts.aktualny.typ_zmiennej(nazwa) or CAŁKOWITY

    def odw_binop(self, węzeł):
        typy = [self.odwiedź(d) for d in węzeł.children if isinstance(d, Tree)]
        wynik = CAŁKOWITY
        for typ in typy:
            wynik = typ_szerszy(wynik, typ)
        return wynik

    def odw_compare(self, węzeł):
        for dziecko in węzeł.children:
            if isinstance(dziecko, Tree):
                self.odwiedź(dziecko)
        return CAŁKOWITY

    def odw_or_op(self, węzeł):
        for dziecko in węzeł.children:
            if isinstance(dziecko, Tree):
                self.odwiedź(dziecko)
        return CAŁKOWITY

    def odw_and_op(self, węzeł):
        return self.odw_or_op(węzeł)

    def odw_not_op(self, węzeł):
        self.odwiedź(węzeł.children[0])
        return CAŁKOWITY

    def odw_unary_op(self, węzeł):
        return self.odwiedź(węzeł.children[1])

    def odw_power_op(self, węzeł):
        self.ts.nagłówki.add('<math.h>')
        return ZMIENNOPRZECINKOWY

    def odw_call(self, węzeł):
        nazwa_func = str(węzeł.children[0])
        arg_węzły = next(
            (d for d in węzeł.children[1:] if isinstance(d, Tree) and d.data == 'args'), None
        )
        typy_arg = [self.odwiedź(d) for d in arg_węzły.children if isinstance(d, Tree)] if arg_węzły else []

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
        return self.ts.funkcje.get(nazwa_func, {}).get('zwraca', CAŁKOWITY)

    def odw_subscript(self, węzeł):
        nazwa = str(węzeł.children[0])
        return self.ts.aktualny.typ_zmiennej(nazwa) or CAŁKOWITY

    def odw_list_lit(self, węzeł):
        typy = [self.odwiedź(d) for d in węzeł.children if isinstance(d, Tree)]
        wynik = CAŁKOWITY
        for typ in typy:
            wynik = typ_szerszy(wynik, typ)
        return wynik

    def odw_expr_stmt(self, węzeł):
        return self.odwiedź(węzeł.children[0])

    def odw_pass_stmt(self, węzeł):
        return NIETYP

    def odw_break_stmt(self, węzeł):
        return NIETYP

    def odw_continue_stmt(self, węzeł):
        return NIETYP
