CAŁKOWITY = 'int'
ZMIENNOPRZECINKOWY = 'double'
TEKST = 'str'
NIETYP = 'void'

ADNOTACJE = {'int': CAŁKOWITY, 'float': ZMIENNOPRZECINKOWY, 'str': TEKST}

KOLEJNOŚĆ_TYPÓW = [NIETYP, CAŁKOWITY, ZMIENNOPRZECINKOWY, TEKST]

def typ_szerszy(a, b):
    try:
        return KOLEJNOŚĆ_TYPÓW[max(KOLEJNOŚĆ_TYPÓW.index(a), KOLEJNOŚĆ_TYPÓW.index(b))]
    except ValueError:
        return a or b

def format_printf(typ):
    return {'int': '%d', 'double': '%.6g', 'str': '%s'}.get(typ, '%d')

def typ_c(typ):
    mapa = {'double': 'double', 'str': 'char*', 'void': 'void'}
    return mapa.get(typ, 'int')

def deklaracja_c(typ, nazwa):
    if typ == TEKST:
        return f'char {nazwa}[256]'
    return f'{typ_c(typ)} {nazwa}'
