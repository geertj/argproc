#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copyright (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.

import sys
import os
import os.path
import inspect

from ply import lex, yacc


class Parser(object):
    """Wrapper object for PLY lexer/parser."""

    exception = ValueError

    @classmethod
    def _parsetab_name(cls, relative=False):
        """Return the module name for PLY's parsetab file."""
        mname = inspect.getmodule(cls).__name__ + '_tab'
        if relative:
            mname = mname.split('.')[-1]
        return mname

    @classmethod
    def _write_parsetab(cls):
        """Write parser table (for distribution purposes)."""
        path = inspect.getfile(cls)
        parent = os.path.split(path)[0]
        # Need to change directories to get the file written at the right
        # location.
        cwd = os.getcwd()
        os.chdir(parent)
        tabname = cls._parsetab_name(relative=True)
        yacc.yacc(module=cls, tabmodule=tabname)
        os.chdir(cwd)

    def parse(self, input, fname=None):
        lexer = lex.lex(object=self)
        if hasattr(input, 'read'):
            input = input.read()
        lexer.input(input)
        self._input = input
        self._fname = fname
        parser = yacc.yacc(module=self, tabmodule=self._parsetab_name())
        parsed = parser.parse(lexer=lexer, tracking=True)
        return parsed

    def _position(self, o):
        if hasattr(o, 'lineno') and hasattr(o, 'lexpos'):
            lineno = o.lineno
            lexpos = o.lexpos
            pos = self._input.rfind('\n', 0, lexpos)
            column = lexpos - pos
        else:
            lineno = None
            column = None
        return lineno, column

    def t_ANY_error(self, t):
        err = self.exception()
        msg = 'illegal token'
        if self._fname:
            err.fname = self._fname
            msg += ' in file %s' % self._fname
            lineno, column = self._position(t)
            if lineno is not None and column is not None:
                msg += ' at %d:%d' % (lineno, column)
                err.lineno = lineno
                err.column = column
        err.args = (msg,)
        raise err

    def p_error(self, p):
        err = self.exception()
        msg = 'syntax error'
        if self._fname:
            err.fname = self._fname
            msg += ' in file %s' % self._fname
            lineno, column = self._position(p)
            if lineno is not None and column is not None:
                msg += ' at %d:%d' % (lineno, column)
                err.lineno = lineno
                err.column = column
        err.args = (msg,)
        raise err
