from .typy import CAŁKOWITY

class Zakres:
    def __init__(self, rodzic=None):
        self.rodzic = rodzic
        self.zmienne = {}
        self.tablice = {}

    def def_zmienna(self, nazwa, typ):
        self.zmienne[nazwa] = typ

    def def_tablica(self, nazwa, typ, rozmiar):
        self.tablice[nazwa] = (typ, rozmiar)

    def typ_zmiennej(self, nazwa):
        if nazwa in self.zmienne:
            return self.zmienne[nazwa]
        if nazwa in self.tablice:
            return self.tablice[nazwa][0]
        return self.rodzic.typ_zmiennej(nazwa) if self.rodzic else None

    def info_tablicy(self, nazwa):
        if nazwa in self.tablice:
            return self.tablice[nazwa]
        return self.rodzic.info_tablicy(nazwa) if self.rodzic else (CAŁKOWITY, 0)

    def czy_tablica(self, nazwa):
        return nazwa in self.tablice or (self.rodzic.czy_tablica(nazwa) if self.rodzic else False)

    def ma_lokalne(self, nazwa):
        return nazwa in self.zmienne or nazwa in self.tablice

class TablicaSymboli:
    def __init__(self):
        self.glob = Zakres()
        self.aktualny = self.glob
        self.funkcje = {}
        self.nagłówki = {'<stdio.h>'}
        self.użyj_bufora_wej = False

    def wejdź(self):
        self.aktualny = Zakres(self.aktualny)
        return self.aktualny

    def wyjdź(self):
        self.aktualny = self.aktualny.rodzic
