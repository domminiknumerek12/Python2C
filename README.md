# Python2C

### Zespół:
1. Dominik Mida - dmida@student.agh.edu.pl 
2. Krzysztof Sikorski - ksikorsk@student.agh.edu.pl


### Opis projektu:
Program ma za zadanie przekonwertowanie kodu napisanego w języku Python na kod w języku C.
- **Rodzaj translatora:** kompilator (transpiler źródło–źródło)
- **Planowany wynik działania programu:** kod w języku C
- **Planowany język implementacji:** Python
- **Generator parsera:** LARK

### Spis tokenów:
## Wzorce znaczeniowe
|Token|Wzorzec|Opis|
|-----|-------|----|
|NAME|`/[a-zA-Z_]\w*/`|nazwa obiektu|
|NUMBER|`/\d+(\.\d+)?([eE][+-]?\d+)?/`|liczba rzecywista|
|STRING|`/\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'/`|napis|
## Słowa kluczowe 
|Token|Wzorzec|Opis|
|-----|-------|----|
|PASS|`pass`|wypełnienie|
|IF|`if`|instrukcja "jeżeli"|
|ELIF|`elif`|instrukcja "jeśli nie, to jeżeli"|
|ELSE|`else`|instrukcja "w przeciwnym wypadku"|
|MATCH|`match`|instrukcja wyboru|
|CASE|`case`|przypadek dla dopasowanego wzorca|
|FOR|`for`|pętla for|
|WHILE|`while`|pętla while|
|IN|`in`|relacja inkluzji|
|IS|`is`|identyczność|
|RAISE|`raise`|wniesienie wyjątku|
|ASSERT|`assert`|
|DEF|`def`|definicja funkcji/klasy|
|CLASS|`class`|okreslanie definiowanego jako klasy|
|TRY|`try`|wyznaczenie sekcji krytycznej|
|EXCEPT|`except`|w wypadku błędu powiązanej sekcji krytycznej|
|FINALLY|`finally`|po wykonaniu sekcji krytycznej|
|WITH|`with`|określenie kontekstu nazwy|
|YIELD|`yield`|zwracanie generujące|
|GLOBAL|`global`|określenie zmiennej globalnej|
|NONLOCAL|`nonlocal`|deklaracja zmiennej nielokalnej|
## Stałe
|Token|Wzorzec|Opis|
|-----|-------|----|
|NONE|`None`|brak wartości|
|TRUE|`True`|prawda|
|FALSE|`False`|fałsz|
## Operatory
|Token|Wzorzec|Opis|
|-----|-------|----|
|ASGN|`=`|przypisanie|
|PLUS|`+`|dodawanie|
|MINUS|`-`|odejmowanie|
|MUL|`*`|mnożenie|
|DIV|`/`|dzielenie|
|POWER|`**`|potęgowanie|
|MOD|`%`|modulo|
# Porównania
|Token|Wzorzec|Opis|
|-----|-------|----|
|EQ|`==`|równosć|
|NE|`!=`|nierównosć|
|GE|`>=`|większe bądź równe od|
|LE|`<=`|mniejsze bądź równe od|
|GT|`>`|ściśle większe od|
|LT|`<`|ściśle mniejsze od|
# Nawiasy
|Token|Wzorzec|Opis|
|-----|-------|----|
|LPAREN|`(`|lewy nawias okrągły|
|RPAREN|`)`|prawy nawias okrągły|
|LBRACKET|`[`|lewy nawias kwadratowy|
|RBRACKET|`]`|prawy nawias kwadratowy|
|LBRACE|`{`|lewa klamra|
|RBRACE|`}`|prawa klamra|
# Interpunkcja
|Token|Wzorzec|Opis|
|-----|-------|----|
|COMMA|`,`|przecinek|
|COLON|`:`|dwukropek|
|SEMICOLON|`;`|średnik|
# Słowa kluczowe
|Token|Wzorzec|Opis|
|-----|-------|----|
|AND_KW|`and`|koniunkcja|
|OR_KW|`or`|alternatywa|
|NOT_KW|`not`|negacja|
## Znaki i tokeny strukturalne
|Token|Wzorzec|Opis|
|-----|-------|----|
|NEWLINE|`\n`|nowa linia|
|WHITESPACE|`[ ]+`|białe znaki|
|EOF|`EOF`|koniec pliku|
|INDENT|kontekstowo|wcięcie|
|DEDENT|kontekstowo|powrót do zagnieżdzenia przed wcięciem|
## Komentarz
|Token|Wzorzec|Opis|
|-----|-------|----|
|COMMENT|`#.*$`|komentarz jedno-linijkowy|

### Gramatyka:
	start: (_NEWLINE | stmt)*

    stmt: simple_stmt | if_stmt | while_stmt |        for_stmt | func_def
	simple_stmt: small_stmt _NEWLINE
	?small_stmt: assign | aug_assign | return_stmt | expr_stmt | pass_stmt | break_stmt | continue_stmt

	assign: NAME "=" expr
	aug_assign: NAME AUG_OP expr
	return_stmt: "return" expr?
	expr_stmt: expr
	pass_stmt: "pass"
	break_stmt: "break"
	continue_stmt: "continue"
	
	if_stmt: "if" expr ":" suite ("elif" expr ":" suite)* ("else" ":" suite)?
	while_stmt: "while" expr ":" suite
	for_stmt: "for" NAME "in" "range" "(" range_args ")" ":" suite
	func_def: "def" NAME "(" [params] ")" ["->" NAME] ":" suite
	
	range_args: expr -> range1 
		| expr "," expr -> range2 
		| expr "," expr "," expr -> range3
	params: param ("," param)*
	param: NAME [":" NAME]
	suite: _NEWLINE _INDENT stmt+ _DEDENT
	
	?expr: or_expr
	?or_expr: and_expr ("or" and_expr)+ -> or_op | and_expr
	?and_expr: not_expr ("and" not_expr)+ -> and_op | not_expr
	?not_expr: "not" not_expr -> not_op | cmp
	?cmp: add (COMP_OP add)+ -> compare | add
	?add: mul (ADD_OP mul)+ -> binop | mul
	?mul: pow (MUL_OP pow)+ -> binop | pow
	?pow: atom ("**" pow) -> power_op | atom
	?atom: NUMBER -> number
	     | STRING -> string
	     | "True" -> true_lit
	     | "False" -> false_lit
	     | "None" -> none_lit
	     | NAME "(" [args] ")" -> call
	     | NAME "[" expr "]" -> subscript
	     | NAME -> name
	     | ADD_OP atom -> unary_op
	     | "(" expr ")"
	     | "[" [expr ("," expr)*] "]" -> list_lit
	
	args: expr ("," expr)*
	
	AUG_OP: "+=" | "-=" | "*=" | "/=" | "%="
	COMP_OP: "==" | "!=" | "<=" | ">=" | "<" | ">"
	ADD_OP: "+" | "-"
	MUL_OP: "*" | "//" | "/" | "%"
	
	NUMBER: /\d+(\.\d+)?([eE][+-]?\d+)?/
	STRING: /\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'/
	NAME: /[a-zA-Z_]\w*/
	
	%declare _INDENT _DEDENT
	%ignore /[ \t]+/
	%ignore /\\\n/
	%ignore /#[^\n]*/
	_NEWLINE: /(\r?\n[\t ]*)+/
