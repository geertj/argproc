# parser_lex.py. This file automatically created by PLY (version 3.3). Don't edit!
_tabversion   = '3.3'
_lextokens    = {'NONE': 1, 'FALSE': 1, 'NAME': 1, 'LARROW': 1, 'FLOAT': 1, 'RARROW': 1, 'FIELD': 1, 'ARROW': 1, 'INTEGER': 1, 'TRUE': 1, 'STRING': 1}
_lexreflags   = 0
_lexliterals  = '()[],:*!{}.@'
_lexstateinfo = {'INITIAL': 'inclusive'}
_lexstatere   = {'INITIAL': [('(?P<t_COMMENT>\\#.*)|(?P<t_FIELD>\\$!?[a-zA-Z_][a-zA-Z0-9_]*)|(?P<t_NAME>[a-zA-Z_][a-zA-Z0-9_]*)|(?P<t_FLOAT>-?[0-9]+\\.[0-9]+)|(?P<t_STRING>\'[^\']+\'|"[^"]+")|(?P<t_INTEGER>-?[0-9]+)|(?P<t_FALSE>False)|(?P<t_NONE>None)|(?P<t_TRUE>True)|(?P<t_ARROW><=>)|(?P<t_LARROW><=)|(?P<t_RARROW>=>)', [None, ('t_COMMENT', 'COMMENT'), (None, 'FIELD'), (None, 'NAME'), (None, 'FLOAT'), (None, 'STRING'), (None, 'INTEGER'), (None, 'FALSE'), (None, 'NONE'), (None, 'TRUE'), (None, 'ARROW'), (None, 'LARROW'), (None, 'RARROW')])]}
_lexstateignore = {'INITIAL': ' \t\n'}
_lexstateerrorf = {'INITIAL': 't_ANY_error'}
