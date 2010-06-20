#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copyright (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.

import sys
import os.path

from argproc.error import *
from argproc.plyparse import Parser


class Rule(object):

    def __init__(self, left, direction, right, mandatory, tags):
        self.left = left
        self.left.side = 'left'
        self.direction = direction
        self.right = right
        self.right.side = 'right'
        self.mandatory = mandatory
        self.tags = tags

    def tostring(self):
        left = self.left.tostring()
        right = self.right.tostring()
        if left == right and self.direction == '<=>':
            s = left
        else:
            s = '%s %s %s' % (left, self.direction, right)
        if self.mandatory:
            s += ' *'
        if self.tags:
            s += ' [%s]' % (','.join((tag.tostring() for tag in self.tags)))
        return s


class Node(object):
    """A parsed node in our AST."""

    def __init__(self, *args):
        children = []
        for arg in args:
            if isinstance(arg, list):
                children += arg
            elif isinstance(arg, tuple):
                children += list(arg)
            else:
                children.append(arg)
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

    def _eval_error(self, err):
        """Raise an EvalError."""
        m = 'Caught %s when evaluating %s: %s' % \
                (err.__class__.__name__, self.__class__.__name__, str(err))
        raise EvalError, m

    def tostring(self):
        """Stringify this node."""
        raise NotImplementedError

    @staticmethod
    def formatter(format):
        """Return a formatter for this Node."""
        def format_func(self):
            return format % tuple(map(self, lambda x: x.tostring()))
        return format_func

    def assigned_fields(self):
        """All fields that are (recursively) assigned by this node."""
        fields = (child.assigned_fields() for child in self)
        return reduce(list.__add__, fields, [])

    def referenced_fields(self):
        """All fields that are (recursively) referenced by this node."""
        fields = (child.referenced_fields() for child in self)
        return reduce(list.__add__, fields, [])

    def show_tree(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(c.show_tree() for c in self))


class Literal(Node):

    def __init__(self, value):
        super(Literal, self).__init__()
        self.value = value

    def eval(self, args, globals):
        return self.value

    def tostring(self):
        return repr(self.value)

    show_tree = tostring


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


class Dict(Node):

    def __init__(self, elements):
        super(Dict, self).__init__(elements)

    def eval(self, args, globals):
        items = ((n[0].eval(args, globals), n[1].eval(args, globals))
                 for n in self)
        return dict(items)

    def tostring(self):
        items = ((n[0].tostring(), n[1].tostring()) for n in self)
        items = ', '.join(('%s: %s' % (it[0], it[1]) for it in items))
        return '{%s}' % items


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


class FunctionCall(Node):

    def __init__(self, function, arguments):
        super(FunctionCall, self).__init__(function, arguments)

    def eval(self, args, globals):
        arguments = []
        for arg in self[1:]:
            arguments.append(arg.eval(args, globals))
        function = self[0].eval(args, globals)
        value = function(*arguments)
        return value

    def tostring(self):
        arguments = ', '.join((arg.tostring() for arg in self[1:]))
        return '%s(%s)' % (self[0].tostring(), arguments)


class AttributeReference(Node):

    def __init__(self, object, attribute):
        super(AttributeReference, self).__init__([object])
        self.attribute = attribute

    def eval(self, args, globals):
        object = self[0].eval(args, globals)
        attribute = self.attribute
        try:
            return getattr(object, attribute)
        except Exception, e:
            self._eval_error(e)

    tostring = Node.formatter('%s.%s')


class Subscription(Node):

    def __init__(self, object, element):
        super(Subscription, self).__init__(object, element)

    def eval(self, args, globals):
        object = self[0].eval(args, globals)
        element = self[1].eval(args, globals)
        try:
            return object[element]
        except Exception, e:
            m = '%s when subscribing object <%s>: %s' % \
                    (e.__class__.__name__, repr(object), str(e))
            raise EvalError, m

    tostring = Node.formatter('%s[%s]')


class Slicing(Node):

    def __init__(self, object, low, high):
        super(Slicing, self).__init__(object, low, high)

    def eval(self, args, globals):
        object = self[0].eval(args, globals)
        low = self[1].eval(args, globals)
        high = self[2].eval(args, globals)
        try:
            return object[low:high]
        except Exception, e:
            self._eval_error(e)

    tostring = Node.formatter('%s[%s:%s]')


class Validation(Node):

    def __init__(self, field, validator):
        super(Validation, self).__init__(field, validator)

    def _validation_error(self, field, reason, fields=None):
        m = 'Could not validate field "%s": %s'  % (field, reason)
        error = ValidationError(m)
        error.fields = fields
        raise error

    def eval(self, args, globals):
        field = self[0].tostring()
        value = self[0].eval(args, globals)
        validator = self[1].eval(args, globals)
        if callable(validator):
            try:
                validator(value)
            except ValueError, err:
                self._validation_error(field, str(err), fields=[field])
        elif hasattr(validator, '__contains__') and not \
                    isinstance(validator, basestring):
            if value not in validator:
                self._validation_error(field, 'value not in %s' \
                                       % self[1].tostring(), fields=[field])
        else:
            if value != validator:
                self._validation_error(field, 'value not equal to %s' \
                                       % self[1].tostring(), fields=[field])
        return value

    def assigned_fields(self):
        return self[0].assigned_fields()

    tostring = Node.formatter('%s:%s')


class Tag(object):

    def __init__(self, name, negated):
        self.name = name
        self.negated = negated

    def tostring(self):
        s = '@'
        if self.negated:
            s += '!'
        s += self.name
        return s


class RuleParser(Parser):
    """A parser for our validation rule syntax."""

    exception = ParseError

    tokens = ('NAME', 'FIELD', 'ARROW', 'LARROW', 'RARROW', 'INTEGER',
              'FLOAT', 'STRING', 'TRUE', 'FALSE', 'NONE')
    literals = ('(', ')', '[', ']', ',', ':', '*', '!', '{', '}', '.', '@')

    t_NAME = '[a-zA-Z_][a-zA-Z0-9_]*'
    t_FIELD = r'\$!?[a-zA-Z_][a-zA-Z0-9_]*'
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
        """rule : expression mandatory tags
                | expression direction expression mandatory tags"""

        if len(p) == 4:
            p[0] = Rule(p[1], '<=>', p[1], p[2], p[3])
        else:
            p[0] = Rule(p[1], p[2], p[3], p[4], p[5])

    def p_expresssion(self, p):
        """expression : literal
                      | tuple
                      | list
                      | dict
                      | name
                      | field
                      | function_call
                      | attribute_reference
                      | subscription
                      | slicing
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

    def p_argument_list(self, p):
        """argument_list : expression
                         | argument_list ',' expression
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_list(self, p):
        """list : '[' argument_list ']'"""
        p[0] = List(p[2])

    def p_dict(self, p):
        """dict : '{' key_value_list '}'"""
        p[0] = Dict(p[2])

    def p_key_value_list(self, p):
        """key_value_list : key_value
                          | key_value_list ',' key_value
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_key_value(self, p):
        """key_value : literal ':' expression"""
        p[0] = Node((p[1], p[3]))

    def p_name(self, p):
        """name : NAME"""
        p[0] = Name(p[1])

    def p_field(self, p):
        """field : FIELD"""
        p[0] = Field(p[1])

    def p_function_call(self, p):
        """function_call : expression '(' ')'
                         | expression '(' argument_list ')'"""
        if len(p) == 4:
            p[0] = FunctionCall(p[1], [])
        else:
            p[0] = FunctionCall(p[1], p[3])

    def p_attribute_reference(self, p):
        """attribute_reference : expression '.' NAME"""
        p[0] = AttributeReference(p[1], p[3])

    def p_subscription(self, p):
        """subscription : expression '[' expression ']'"""
        p[0] = Subscription(p[1], p[3])

    def p_slicing(self, p):
        """slicing : expression '[' expression ':' expression ']'"""
        p[0] = Slicing(p[1], p[3], p[5])

    def p_validation(self, p):
        """validation : field ':' expression"""
        p[0] = Validation(p[1], p[3])

    def p_direction(self, p):
        """direction : ARROW
                     | LARROW
                     | RARROW
        """
        p[0] = p[1]

    def p_mandatory(self, p):
        """mandatory : '*'
                     | empty
        """
        p[0] = p[1] == '*'

    def p_empty(self, p):
        """empty : """
        p[0] = None

    def p_tags(self, p):
        """tags : tag_list
                | empty
        """
        if len(p) == 2:
            p[0] = p[1]

    def p_tag_list(self, p):
        """tag_list : tag
                    | tag_list ',' tag"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_tag(self, p):
        """tag : '@' NAME
               | '@' '!' NAME
        """
        if len(p) == 3:
            p[0] = Tag(p[2], False)
        else:
            p[0] = Tag(p[3], True)
