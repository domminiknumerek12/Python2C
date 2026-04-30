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
|NAME|`[_a-zA-Z][_a-zA-Z0-9]*`|nazwa obiektu|
|NUMBER|`[0-9]+(.[0-9]+)?`|liczba rzecywista|
|STRING|`^".*"$`|napis|
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
|TIMES|`*`|mnożenie|
|DIV|`/`|dzielenie|
|POWER|`**`|potęgowanie|
|DIV_INT|`//`|dzielenie całkowite|
|MODULO|`%`|modulo|
|AND|`&`|koniunkcja|
|OR|`|`|alternatywa|
|XOR|`^`|alternatywa wykluczająca|
|LSHIFT|`<<`|przesunięcie bitowe w lewo|
|RSHIFT|`>>`|przesunięcie bitowe w prawo|
# Porównania
|Token|Wzorzec|Opis|
|-----|-------|----|
|EQ|`==`|równosć|
|GE|`>=`|większe bądź równe od|
|LE|`<=`|mniejsze bądź równe od|
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
	%declare INDENT DEDENT
	
	program: statement+ EOF
	  
	statement: instruction
	| block_statement
	| ignore
	| PASS
	
	instruction: expressions
	  		| assignment
			| exception
	  		| return
			| raise
			| delete
			| assert
	  		| BREAK
	  		| CONTINUE
			| PASS
	
	block_statement: if_conditional
			| match_conditional
			| for_loop
			| while_loop
			| function
			| class
	
	ignore: import
		| yield
		| error_handling
		| variable_scope
		| context

	assignment: simple_asgn
			| extended_asgn

	simple_asgn: unit [COMMA unit]? ASGN expression

	extended_asgn: unit operator ASGN expression

	operator: PLUS
			| MINUS
			| TIMES
			| DIV
			| MODULO
			| DIV_INT
			| POWER
			| AND
			| OR
			| XOR
			| LSHIFT
			| RSHIFT
	
	if_conditional: IF if_condition COLON block [elif_conditional]* [else_conditional]
	   
	elif_conditional: ELIF if_condition COLON block
	
	else_conditional: ELSE COLON block

	if_condition: expression compare expression
	compare: OR_KW
			| AND_KW
			| OR
			| AND
			| EQ
			| LE
			| GE
			| IN
	
	match_conditional: MATCH name_expr COLON NEWLINE INDENT match_case
	
	match_case: CASE (NAME|constant) COLON block [match_case]
	
	for_loop: FOR for_iter COLON block
	
	while_loop: WHILE while_condition COLON block
	
	function: DEF NAME LPAREN (NAME (COLON NAME)*)? RPAREN COLON block
	
	class:  CLASS NAME (LPAREN NAME RPAREN)? COLON block 
	
	import: IMPORT .*$
	
	yield: YIELD .*$
	
	error_handling: TRY COLON block [EXCEPT COLON block] [FINALLY COLON block]
	
	variable_scope: GLOBAL .*$
			| NONLOCAL .*$
	
	context: WITH .*$
	 
	block: NEWLINE INDENT statement+ DEDENT
	
	expression: LPAREN expression RPAREN
			| expression OR_KW expression
			| expression AND_KW expression
			| NOT expression
			| expression OR expression
			| expression AND expression
			| expression XOR expression
			| expression LSHIFT expression
			| expression RSHIFT expression
			| expression PLUS expression
			| expression MINUS expression
			| expression TIMES expression
			| expression DIV expression
			| expression DIV_INT expression
			| expression MODULO expression
			| expression POWER expression
			| unit
	 
	unit: unit DOT NAME
		| unit LPAREN args RPAREN 
		| unit LBRACKET indices RBRACKET
		| NAME
		| constant
		| collection

	indices: expression [COLON expression]

	args: [arg (COMMA arg)*]

	arg: expression
		| NAME ASGN expression
	
	collection: list | tuple | dict
	
	constant: TRUE
		| FALSE
		| NONE
		| literal
		
	literal: integer
		| float
		| string

	integer: pos_int | neg_int
		
	float: pos_fl | neg_fl
	
	pos_int: NUMBER
	neg_int: MINUS NUMBER
	
	pos_fl: NUMBER
	neg_fl: MINUS NUMBER
	
	list: LBRACKET expression? (COMMA expression)* RBRACKET
	  
	tuple: LPAREN expression COMMA RPAREN
		| LPAREN expression (COMMA expression)+ RPAREN
	  
	dictionary: LBRACE dict_item? (COMMA dict_item)*  RBRACe
	  
	dict_item: expression COLON expression


	PASS: "pass"
	IF: "if"
	ELIF: "elif"
	ELSE: "else"
	MATCH: "match"
	CASE: "case"
	FOR: "for"
	WHILE: "while"
	IN: "in"
	IS: "is"
	RAISE: "raise"
	ASSERT: "assert"
	DEF: "def"
	CLASS: "class"
	TRY: "try"
	EXCEPT: "except"
	FINALLY: "finally"
	WITH: "with"
	YIELD: "yield"
	GLOBAL: "global"
	NONLOCAL: "nonlocal"
	
	OR_KW: "or"
	AND_KW: "and"
	NOT: "not"
	AND: '&'
	OR: '|'
	XOR: '^'
	LSHIFT: '<<'
	RSHIFT: '>>'
	PLUS: '+'
	MINUS: '-'
	TIMES: '*'
	DIV: '/'
	POWER: '**'
	DIV_INT: '//'
	MODULO: '%'
	
	EQ: '=='
	GE: '>='
	LE: '<='
	
	ASGN: '='
	
	LPAREN: '('
	RPAREN: ')'
	LBRACKET: '['
	RBRACKET: ']'
	LBRACE: '{'
	RBRACE: '}'
	
	COMMA: ','
	COLON: ':'
	DOT: '.'
	
	TRUE: "True"
	FALSE: "False"
	NONE: "None"
	
	COMMENT: #.*$
	
	NAME: [_a-zA-Z][_a-zA-Z0-9]*
	
	INT: '0'|[1-9][0-9]*
	FLOAT: ['0'|[1-9][0-9]*](.[0-9]*)?
	STRING: []
	
	WHITESPACE: [ \t\r]+
	NEWLINE: \n
	EOF: EOF

