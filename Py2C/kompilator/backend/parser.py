from lark import Lark
from lark.indenter import PythonIndenter

with open("backend/grammar.lark") as f:
    grammar = f.read()

PARSER = Lark(grammar, parser='earley', postlex=PythonIndenter(), start='start')
