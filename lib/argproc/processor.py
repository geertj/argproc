#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copyright (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.

import sys

from argproc.error import *
from argproc.parser import RuleParser


class ArgumentProcessor(object):
    """Rule-based arguments processor."""

    def __init__(self, namespace=None, tags=None, ignore_none=False,
                 ignore_missing=False):
        if namespace is None:
            namespace = self._get_caller_namespace(2)
        self.namespace = namespace
        self.tags = tags
        self.ignore_none = ignore_none
        self.ignore_missing = ignore_missing
        self._rules = []
        self._parser = RuleParser()

    def _get_caller_namespace(self, level):
        """INTERNAL: return a copy the global and local namespaces of the caller."""
        frame = sys._getframe()
        for i in range(level):
            frame = frame.f_back
        namespace = frame.f_globals.copy()
        namespace.update(frame.f_locals)
        return namespace

    def rules(self, rule):
        rules = self._parser.parse(rule)
        self._rules += rules

    rule = rules

    def _process_rule(self, args, ispec, ospec, rule):
        """INTERNAL: process one rule."""
        result = {}
        missing = []
        for field in ispec.referenced_fields():
            if field not in args:
                missing.append(field)
        if missing:
            if rule.mandatory and not self.ignore_missing:
                m = 'Required %s fields missing: %s' % \
                        (ispec.side, ', '.join(missing))
                raise MissingFieldError(m, fields=missing, rule=rule)
            return result
        ivalue = ispec.eval(args, self.namespace)
        if self.ignore_none and ivalue is None:
            return result
        ofields = ospec.assigned_fields()
        if len(ofields) == 1:
            result[ofields[0]] = ivalue
        else:
            if not isinstance(ivalue, tuple) and not isinstance(ivalue, list):
                m = 'Expression on %s hand size should evaluate in a tuple ' \
                    'or list in case of multiple fields on %s hand side.' % \
                        (ispec.side, ospec.side)
                raise EvalError(m, fields=ofields, rule=rule)
            if len(ofields) != len(ivalue):
                m = 'Wrong number of fields on %s hand side (%d expect %d)' % \
                        (ospec.side, len(ofields), len(ivalue))
                raise EvalError(m, fields=ofields, rule=rule)
            for i in range(len(rfields)):
                result[ofields[i]] = ivalue[i]
        return result

    def _match_tags(self, rule, tags):
        """INTERNAL: match a rule to a set of tags."""
        if tags is None or rule.tags is None:
            return True
        for tag in rule.tags:
            if tag.negated and tag.name not in tags:
                return True
            elif not tag.negated and tag.name in tags:
                return True
        return False

    def process(self, left):
        """Process the arguments in `left' and return the transformed right
        hand side."""
        right = {}
        for rule in self._rules:
            if rule.direction == '<=':
                continue
            if not self._match_tags(rule, self.tags):
                continue
            args = self._process_rule(left, rule.left, rule.right, rule)
            right.update(args)
        return right

    def process_reverse(self, right):
        """Process the arguments in `right' and return the transformed left
        hand side."""
        left = {}
        for rule in self._rules:
            if rule.direction == '=>':
                continue
            if not self._match_tags(rule, self.tags):
                continue
            args = self._process_rule(right, rule.right, rule.left, rule)
            left.update(args)
        return left

    reverse = process_reverse
