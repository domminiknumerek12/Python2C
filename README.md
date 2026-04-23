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
	  statement: 
		  	| instruction
			  | block_statement
			
	  instruction:
	  		| assignment
	  		| expression
	  		| BREAK
	  		| CONTINUE
	  		| return
	  
	  assignment: variable ASGN rhs
	  
	  variable: 
	      | NAME
	      | call
	      | container
	      
	  rhs:
	      | literal
	      | NAME
	      | call
	      | container
	      
	  block_statement:
	  		| while_statement
	  		| for_statement
	  		| if_statement
	  
	  block: NEWLINE INDENT statement+
	  
	  while_statement: while_header block
	  
	  for_statement: for_header block
	  
	  while_header: WHILE condition COLON
	  
	  for_header: FOR target IN expression COLON
	  
	  if_statement: IF condition COLON block [ELSE block]
	  
	  container:
	  		| list
	  		| tuple
	  		| dictionary
	  
	  condition:
	  		| compare
	  		| call
	  		| TRUE
	  		| FALSE
	  
	  expression: NAME LPAREN callable* RPAREN
	  
	  callable:
	  		| container
	  		| literal
	  		| expression
	  		| NAME
	  
	  compare: item comp_op item
	  
	  comp_op: EQ | GE | LE
	  
	  list: LPAREN item? (COMMA item)* RPAREN
	  
	  tuple: LNO (item COMMA)* PNO
	  
	  dictionary: LK dict_item? (COMMA dict_item)*  PK
	  
	  dict_item: item COLON item
	  
	  item:
	  	| literal
	  	| container
	  	| expression
	  
	  literal:
	  	| NUMBER
	  	| STRING
	  	| NONE
	  	| TRUE
	  	| FALSE
