#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copyright (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.

import sys
import os.path

from argproc.error import Error
from argproc.plyparse import Parser


class Rule(object):

    def __init__(self, left, direction, right, tags):
        self.left = left
        self.left.side = 'left'
        self.direction = direction
        self.right = right
        self.right.side = 'right'
        self.tags = tags

    def tostring(self):
        left = self.left.tostring()
        right = self.right.tostring()
        if left == right and self.direction == '<=>':
            s = left
        else:
            s = '%s %s %s' % (left, self.direction, right)
        if self.tags:
            s += ' [%s]' % (','.join((tag.tostring() for tag in self.tags)))
        return s


class Tag(object):

    def __init__(self, name, negated):
        self.name = name
        self.negated = negated

    def tostring(self):
        if self.negated:
            s = '!%s' % self.name
        else:
            s = self.name
        return s


class Node(object):
    """A parsed node in our AST."""

    def __init__(self, children=[]):
        self.children = children

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __getitem__(self, i):
        return self.children[i]

    def append(self, el):
        self.children.append(el)

    def eval(self, args, globals):
        """(Recursively) evaluate the value of this node."""
        raise NotImplementedError

    def tostring(self):
        """(Recursively) stringify the this node."""
        return ''.join((str(child) for child in self))

    def assigned_fields(self):
        """All fields that are (recursively) assigned by this node."""
        return sum((child.assigned_fields() for child in self), [])

    def referenced_fields(self):
        """All fields that are (recursively) referenced by this node."""
        return sum((child.referenced_fields() for child in self), [])


class FieldSpec(Node):

    def __init__(self, expression, mandatory):
        super(FieldSpec, self).__init__([expression])
        self.mandatory = mandatory

    def eval(self, args, globals):
        return self.children[0].eval(args, globals)

    def tostring(self):
        s = self.children[0].tostring()
        if self.mandatory:
            s += ' *'
        return s


class Name(Node):

    def __init__(self, name):
        super(Name, self).__init__()
        self.name = name

    def eval(self, args, globals):
        value = eval(self.name, globals, args)
        return value

    def tostring(self):
        return self.name


class Field(Node):

    def __init__(self, name):
        super(Field, self).__init__()
        self.name = name[1:]

    def eval(self, args, globals):
        return args[self.name]

    def referenced_fields(self):
        return [self.name]

    def assigned_fields(self):
        return [self.name]

    def tostring(self):
        return '$%s' % self.name


class Validation(Node):

    def __init__(self, name, validators):
        super(Validation, self).__init__([name])
        self.children += validators

    def eval(self, args, globals):
        name = self[0].tostring()
        value = self[0].eval(args, globals)
        for val in self[1:]:
            validator = val.eval(args, globals)
            if callable(validator):
                try:
                    validator(value)
                except ValueError, err:
                    raise Error('Could not validate field "%s" (%s)' %
                                (name, str(err)), fields=[name])
            elif hasattr(validator, '__contains__') and not \
                        isinstance(validator, basestring):
                if value not in validator:
                    raise Error('Could not validate field "%s" (value not in '
                                'reference values)' % name, fields=[name])
            else:
                if value != validator:
                    raise Error('Could not validate field "%s" (not equal to '
                                'reference value)'% name, fields=[name])
        return value

    def assigned_fields(self):
        return self[0].assigned_fields()

    def tostring(self):
        name = self[0].tostring()
        validators = ','.join((ch.tostring() for ch in self.children[1:]))
        return '%s:%s' % (name, validators)


class FunctionCall(Node):

    def __init__(self, function, arguments):
        super(FunctionCall, self).__init__(arguments)
        self.function = function

    def eval(self, args, globals):
        arguments = []
        for arg in self:
            arguments.append(arg.eval(args, globals))
        function = self.function.eval(args, globals)
        value = function(*arguments)
        return value

    def tostring(self):
        arguments = ', '.join((arg.tostring() for arg in self))
        return '%s(%s)' % (self.function.tostring(), arguments)


class Literal(Node):

    def __init__(self, value):
        super(Literal, self).__init__()
        self.value = value

    def eval(self, args, globals):
        return self.value

    def tostring(self):
        return repr(self.value)


class Tuple(Node):

    def __init__(self, elements):
        super(Tuple, self).__init__(elements)

    def eval(self, args, globals):
        value = tuple(el.eval(args, globals) for el in self)
        return value

    def tostring(self):
        elements = ','.join((el.tostring() for el in self))
        if len(self) == 1:
            elements += ','
        return '(%s)' % elements


class List(Node):

    def __init__(self, elements):
        super(List, self).__init__(elements)

    def eval(self, args, globals):
        value = list(el.eval(args, globals) for el in self)
        return value

    def tostring(self):
        elements = ', '.join((el.tostring() for el in self))
        return '[%s]' % elements


class ParseError(Exception):
    """Parse error."""


class RuleParser(Parser):
    """A parser for our validation rule syntax."""

    exception = ParseError

    tokens = ('NAME', 'FIELD', 'ARROW', 'LARROW', 'RARROW', 'INTEGER',
              'FLOAT', 'STRING', 'TRUE', 'FALSE', 'NONE')
    literals = ('(', ')', '[', ']', ',', ':', '*', '!')

    t_NAME = '[a-zA-Z_][a-zA-Z0-9_]*'
    t_FIELD = r'\$[a-zA-Z_][a-zA-Z0-9_]*'
    t_INTEGER = '-?[0-9]+'
    t_FLOAT = r'-?[0-9]+\.[0-9]+'
    t_STRING = '\'[^\']+\'|"[^"]+"'
    t_ARROW = '<=>'
    t_LARROW = '<='
    t_RARROW = '=>'
    t_TRUE = 'True'
    t_FALSE = 'False'
    t_NONE = 'None'
    t_ignore = ' \t\n'

    def t_COMMENT(self, t):
        r'\#.*'
        pass
 
    def p_main(self, p):
        """main : rule
                | main rule
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_rule(self, p):
        """rule : fieldspec tags
                | fieldspec direction fieldspec tags"""

        if len(p) == 3:
            p[0] = Rule(p[1], '<=>', p[1], p[2])
        else:
            p[0] = Rule(p[1], p[2], p[3], p[4])

    def p_fieldspec(self, p):
        """fieldspec : expression
                     | expression '*'
        """
        p[0] = FieldSpec(p[1], len(p) == 3)

    def p_expression(self, p):
        """expression : field
                      | validation
                      | function_call
        """
        p[0] = p[1]

    def p_name(self, p):
        """name : NAME"""
        p[0] = Name(p[1])

    def p_field(self, p):
        """field : FIELD"""
        p[0] = Field(p[1])

    def p_validation(self, p):
        """validation : field ':' validator_list"""
        p[0] = Validation(p[1], p[3])

    def p_function_call(self, p):
        """function_call : name '(' argument_list ')'"""
        p[0] = FunctionCall(p[1], p[3])

    def p_validator_list(self, p):
        """validator_list : validator
                          | validator_list ',' validator
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_argument_list(self, p):
        """argument_list : argument
                         | argument_list ',' argument
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_validator(self, p):
        """validator : name
                     | field
                     | literal
                     | tuple
                     | list
                     | function_call
        """
        p[0] = p[1]

    def p_argument(self, p):
        """argument : name
                    | field
                    | literal
                    | tuple
                    | list
                    | function_call
                    | validation
        """
        p[0] = p[1]

    def p_literal(self, p):
        """literal : INTEGER
                   | FLOAT
                   | STRING
                   | TRUE
                   | FALSE
                   | NONE
        """
        p[0] = Literal(eval(p[1]))

    def p_tuple(self, p):
        """tuple : '(' argument_list ')'
                 | '(' argument_list ',' ')'
        """
        # grammar not completely correct: (1,2,) would match
        p[0] = Tuple(p[2])

    def p_list(self, p):
        """list : '[' argument_list ']'"""
        p[0] = List(p[2])

    def p_direction(self, p):
        """direction : ARROW
                     | LARROW
                     | RARROW
        """
        p[0] = p[1]

    def p_tags(self, p):
        """tags : '[' tag_list ']'
                | empty
        """
        if len(p) == 4:
            p[0] = p[2]

    def p_tag_list(self, p):
        """tag_list : tag
                    | tag_list ',' tag"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_tag(self, p):
        """tag : NAME
               | '!' NAME
        """
        if len(p) == 2:
            p[0] = Tag(p[1], False)
        else:
            p[0] = Tag(p[2], True)

    def p_empty(self, p):
        """empty : """
        p[0] = None
