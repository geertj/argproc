#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copyright (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.


class Error(Exception):
    """Validation error."""

    def __init__(self, error=None, fields=None, rule=None):
        self.error = error
        self.fields = fields
        self.rule = rule

    def __str__(self):
        return self.error
