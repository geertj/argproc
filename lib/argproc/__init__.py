#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copyright (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.

"""
ArgProc is a rule-based argument processing library. It converts a set of
arguments from a "left hand side" to a "right hand side" representation, based
on a set of rules.

The rule language is designed to be human readable. Some examples below:

  $id:int <= $objectid
  $name <=> $name *
  $type:set(('test', 'blaat')) <=> $objecttype [update]
  int($value) <=> str($value)
  concat($name, $value) => $nameval
  $field:isinstance($_, FieldStorage)
  $password:$verify => $password
  concat($year:int, '-', $month:int, '-', $day:int) <=> split($date, '-')
"""

from argproc.error import Error
from argproc.processor import ArgumentProcessor
