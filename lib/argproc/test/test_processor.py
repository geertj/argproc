#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copy$right (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.

from nose.tools import assert_raises

from argproc import ArgumentProcessor as ArgProc
from argproc import Error


class TestProcessor(object):

    def test_simple(self):
        proc = ArgProc()
        proc.rule('$left <=> $right')
        assert proc.process({'left': 10}) == { 'right': 10 }
        assert proc.process({'right': 10}) == {}
        assert proc.reverse({'right': 10}) == { 'left': 10 }
        assert proc.reverse({'left': 10}) == {}

    def test_reverse(self):
        proc = ArgProc()
        proc.rule('$left <=> $right')
        assert proc.reverse({'right': 10}) == { 'left': 10 }

    def test_mandatory(self):
        proc = ArgProc()
        proc.rule('$left <=> $right *')
        assert_raises(Error, proc.process, {})

    def test_optional(self):
        proc = ArgProc()
        proc.rule('$left <=> $right')
        assert proc.process({}) == {}

    def test_multiple_rules(self):
        proc = ArgProc()
        proc.rules("""
            $left1 <=> $right1
            $left2 <=> $right2
            """)
        right = proc.process({'left1': 1, 'left2': 2})
        assert right== {'right1': 1, 'right2': 2}

    def test_unidirectional(self):
        proc = ArgProc()
        proc.rule('$left => $right')
        assert proc.process({'left': 10}) == {'right': 10}
        assert proc.reverse({'right': 10}) == {}
        proc = ArgProc()
        proc.rule('$left <= $right')
        assert proc.process({'left': 10}) == {}
        assert proc.reverse({'right': 10}) == {'left': 10}

    def test_bidrectional(self):
        proc = ArgProc()
        proc.rule('$left <=> $right')
        assert proc.process({'left': 10}) == {'right': 10}
        assert proc.reverse({'right': 10}) == {'left': 10}

    def test_none(self):
        proc = ArgProc()
        proc.rule('None => $right')
        assert proc.process({}) == {'right': None}

    def test_true(self):
        proc = ArgProc()
        proc.rule('True => $right')
        assert proc.process({}) == {'right': True}

    def test_false(self):
        proc = ArgProc()
        proc.rule('False => $right')
        assert proc.process({}) == {'right': False}

    def test_int(self):
        proc = ArgProc()
        proc.rule('10 => $right')
        assert proc.process({}) == {'right': 10}

    def test_float(self):
        proc = ArgProc()
        proc.rule('3.14 => $right')
        assert proc.process({}) == {'right': 3.14}

    def test_str_single_quoted(self):
        proc = ArgProc()
        proc.rule('\'test\' => $right')
        assert proc.process({}) == {'right': 'test'}

    def test_str_double_quoted(self):
        proc = ArgProc()
        proc.rule('"test" => $right')
        assert proc.process({}) == {'right': 'test'}

    def test_tuple(self):
        proc = ArgProc()
        proc.rule('(1,2,3) => $right')
        assert proc.process({}) == {'right': (1,2,3)}
        
    def test_tuple_with_one_entry(self):
        proc = ArgProc()
        proc.rule('(1,) => $right')
        assert proc.process({}) == {'right': (1,)}

    def test_list(self):
        proc = ArgProc()
        proc.rule('[1,2,3] => $right')
        assert proc.process({}) == {'right': [1,2,3]}

    def test_dict(self):
        proc = ArgProc()
        proc.rule('{1:2, 3:4} => $right')
        assert proc.process({}) == {'right': {1:2, 3:4}}

    def test_function_call(self):
        proc = ArgProc()
        proc.rule('int($left) => $right')
        assert proc.process({'left': '10'}) == {'right': 10}

    def test_function_call_with_multiple_arguments(self):
        proc = ArgProc()
        proc.rule('max($left, 2) => $right')
        assert proc.process({'left': 1}) == {'right': 2}

    def test_attribute_reference(self):
        proc = ArgProc()
        proc.rule('int.__class__ => $right')
        assert proc.process({}) == {'right': type}

    def test_subscription(self):
        proc = ArgProc()
        proc.rule('[1,2,3][1] => $right')
        assert proc.process({}) == {'right': 2}

    def test_slicing(self):
        proc = ArgProc()
        proc.rule('[1,2,3][1:2] => $right')
        assert proc.process({}) == {'right': [2]}

    def test_validator_callable(self):
        proc = ArgProc()
        proc.rule('$left:int => $right')
        assert proc.process({'left': 10}) == {'right': 10}
        assert_raises(Error, proc.process, {'left': '10a'})

    def test_validator_literal(self):
        proc = ArgProc()
        proc.rule('$left:"value" => $right')
        assert proc.process({'left': 'value'}) == {'right': 'value'}
        assert_raises(Error, proc.process, {'left': 'val'})

    def test_validator_tuple(self):
        proc = ArgProc()
        proc.rule('$left:(1,2,3) => $right')
        assert proc.process({'left': 2}) == {'right': 2}
        assert_raises(Error, proc.process, {'left': 4})

    def test_validator_list(self):
        proc = ArgProc()
        proc.rule('$left:[1,2,3] => $right')
        assert proc.process({'left': 2}) == {'right': 2}
        assert_raises(Error, proc.process, {'left': 4})

    def test_validator_function_call(self):
        proc = ArgProc()
        proc.rule('$left:set((1,2)) => $right')
        assert proc.process({'left': 1}) == {'right': 1}
        assert_raises(Error, proc.process, {'left': 3})

    def test_function_with_validator(self):
        proc = ArgProc()
        proc.rule('int($left:int) => $right')
        assert proc.process({'left': 1}) == {'right': 1}

    def test_local_name(self):
        verify = 'test'
        proc = ArgProc()
        proc.rule('$left:verify => $right *')
        assert proc.process({'left': 'test'}) == {'right': 'test'}
        assert_raises(Error, proc.process, {'left': 'value'})

    def test_global_name(self):
        global verify
        verify = 'test'
        proc = ArgProc()
        proc.rule('$left:verify => $right *')
        assert proc.process({'left': 'test'}) == {'right': 'test'}
        assert_raises(Error, proc.process, {'left': 'value'})

    def test_tags(self):
        proc = ArgProc(tags=['tag'])
        proc.rule('$left => $right @tag')
        assert proc.process({'left': 10}) == {'right': 10}
        proc = ArgProc(tags=[])
        proc.rule('$left => $right @tag')
        assert proc.process({'left': 10}) == {}
        proc = ArgProc()
        proc.rule('$left => $right @tag')
        assert proc.process({'left': 10}) == {'right': 10}

    def test_multiple_tags(self):
        proc = ArgProc(tags=['tag2'])
        proc.rule('$left => $right @tag1,@tag2')
        assert proc.process({'left': 10}) == {'right': 10}
        proc = ArgProc(tags=[])
        proc.rule('$left => $right @tag1,@tag2')
        assert proc.process({'left': 10}) == {}
        proc = ArgProc()
        proc.rule('$left => $right @tag1,@tag2')
        assert proc.process({'left': 10}) == {'right': 10}

    def test_negated_tag(self):
        proc = ArgProc()
        proc.rule('$left => $right @!tag')
        assert proc.process({'left': 10}) == {'right': 10}
        proc = ArgProc(tags=['tg'])
        proc.rule('$left => $right @!tag')
        assert proc.process({'left': 10}) == {'right': 10}
        proc = ArgProc(tags=['tag'])
        proc.rule('$left => $right @!tag')
        assert proc.process({'left': 10}) == {}

    def test_comment(self):
        proc = ArgProc()
        proc.rules("""
                $left1 => $right1  # comment
                #$left2 => $right2
        """)
        assert proc.process({'left1': 10}) == {'right1': 10}
        assert proc.process({'left2': 20}) == {}
