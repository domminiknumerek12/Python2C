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
|Token|Wzorzec|Opis|
|-----|-------|----|
|IDENT|`_`|identacja bloku kodu|
|NAME|`[_a-zA-Z]+`|nazwa obiektu|
|NUMBER|`[0-9]+(.[0-9]+)?`|liczba całkowita/zmiennoprzecinkowa
|STRING|`^".*"$`|napis|
|PLUS|`+`|dodawanie|
|MINUS|`-`|odejmowanie|
|ASGN|`=`|przypisanie|
|EQ|`==`|równosć|
|GE|`>=`|większe bądź równe od|
|LE|`<=`|mniejsze bądź równe od|
|NONE|`None`|słowo kluczowe None|
|TRUE|`True`|słowo kluczowe True|
|FALSE|`False`|słowo kluczowe False|
|LPAREN|`(`|lewy nawias okrągły|
|RPAREN|`)`|prawy nawias okrągły|
|LBRACKET|`[`|lewy nawias kwadratowy|
|RBRACKET|`]`|prawy nawias kwadratowy|
|LBRACE|`{`|lewa klamra|
|RBRACE|`}`|prawa klamra|
|COMMA|`,`|przecinek|
|COLON|`:`|dwukropek|
|SEMICOLON|`;`|średnik|
|NEWLINE|`\n`|nowa linia|
|WHITESPACE|`[ \t\r\n]+`|białe znaki|
|EOF|`EOF`|koniec pliku|
|COMMENT|`#.*$`|komentarz|

### Gramatyka:
	program: START statement+ END
	  
	statement: instruction
	| block_statement
	| ignore
	
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
	
	if_conditional: IF if_condition COLON block [elif_conditional]* [else_conditional]
	   
	elif_conditional: ELIF if_condition COLON block
	
	else_conditional: ELSE COLON block
	
	match_conditional: MATCH name_expr COLON NEWLINE INDENT match_case
	
	match_case: CASE 
	
	for_loop: FOR for_iter COLON block
	
	while_loop: WHILE while_condition COLON block
	
	function: DEF NAME LPAREN [ COLON block
	
	class: DEF CLASS NAME (LPAREN RPAREN)? COLON block 
	
	import: IMPORT .*$
	
	yield: YIELD .*$
	
	error_handling: TRY COLON block [EXCEPT COLON block] [FINALLY COLON block]
	
	variable_scope: GLOBAL .*$
			| NONLOCAL .*$
	
	context: WITH .*$
	 
	block: NEWLINE INDENT statement+
	
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
		| literal
		| collection
	
	collection: list | tuple | dict
	
	constant: TRUE
		| FALSE
		| NONE
		| literal
		
	literal: integer
		| float
		| string
	
	list: LPAREN expression? (COMMA expression)* RPAREN
	  
	tuple: LPAREN expression COMMA RPAREN
		| LPAREN expression (COMMA expression)+ RPAREN
	  
	dictionary: LK dict_item? (COMMA dict_item)*  PK
	  
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
	
	NAME: []
	
	INT: '0'|[1-9][0-9]*
	FLOAT: ['0'|[1-9][0-9]*](.[0-9]*)?
	STRING: []
	
	WHITESPACE: [ \t\r]+
	NEWLINE: \n
	IDENT: _
	EOF: EOF

