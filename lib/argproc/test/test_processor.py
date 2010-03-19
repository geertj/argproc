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
        proc.rule('$left * <=> $right')
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

    def test_function(self):
        proc = ArgProc()
        proc.rule('int($left) => $right')
        assert proc.process({'left': '10'}) == {'right': 10}

    def test_function_reverse(self):
        proc = ArgProc()
        proc.rule('$left <= int($right)')
        assert proc.reverse({'right': '10'}) == {'left': 10} 

    def test_function_bidirectional(self):
        proc = ArgProc()
        proc.rule('int($left) <=> int($right)')
        assert proc.process({'left': '10'}) == {'right': 10} 
        assert proc.reverse({'right': '10'}) == {'left': 10} 

    def test_multi_arg(self):
        proc = ArgProc()
        proc.rule('max($left, 2) => $right')
        assert proc.process({'left': 1}) == {'right': 2}

    def test_resursive_multi_arg(self):
        proc = ArgProc()
        proc.rule('max($left1, max($left2, 2)) => $right')
        right = proc.process({'left1': 1, 'left2': 1})
        assert right == {'right': 2 }

    def test_validator_callable(self):
        proc = ArgProc()
        proc.rule('$left:int => $right')
        assert proc.process({'left': 10}) == {'right': 10}
        assert_raises(Error, proc.process, {'left': '10a'})

    def test_validator_literal_string(self):
        proc = ArgProc()
        proc.rule('$left:"value" => $right')
        assert proc.process({'left': 'value'}) == {'right': 'value'}
        assert_raises(Error, proc.process, {'left': 'val'})

    def test_validator_literal_int(self):
        proc = ArgProc()
        proc.rule('$left:10 => $right')
        assert proc.process({'left': 10}) == {'right': 10}
        assert_raises(Error, proc.process, {'left': 11})

    def test_validator_literal_single_quoted_string(self):
        proc = ArgProc()
        proc.rule('$left:\'value\' => $right')
        assert proc.process({'left': 'value'}) == {'right': 'value'}
        assert_raises(Error, proc.process, {'left': 'val1'})

    def test_validator_literal_double_quoted_string(self):
        proc = ArgProc()
        proc.rule('$left:"value" => $right')
        assert proc.process({'left': 'value'}) == {'right': 'value'}
        assert_raises(Error, proc.process, {'left': 'val1'})

    def test_validator_literal_float(self):
        proc = ArgProc()
        proc.rule('$left:10.0 => $right')
        assert proc.process({'left': 10.0}) == {'right': 10.0}
        assert_raises(Error, proc.process, {'left': 10.1})

    def test_validator_tuple(self):
        proc = ArgProc()
        proc.rule('$left:(1,2,3) => $right')
        assert proc.process({'left': 2}) == {'right': 2}
        assert_raises(Error, proc.process, {'left': 4})

    def test_validator_tuple_with_one_entry(self):
        proc = ArgProc()
        proc.rule('$left:(1,) => $right')
        assert proc.process({'left': 1}) == {'right': 1}
        assert_raises(Error, proc.process, {'left': 2})

    def test_validator_list(self):
        proc = ArgProc()
        proc.rule('$left:[1,2,3] => $right')
        assert proc.process({'left': 2}) == {'right': 2}
        assert_raises(Error, proc.process, {'left': 4})

    def test_validator_constructed(self):
        proc = ArgProc()
        proc.rule('$left:set((1,2)) => $right')
        assert proc.process({'left': 1}) == {'right': 1}
        assert_raises(Error, proc.process, {'left': 3})

    def test_local_name(self):
        verify = 'test'
        proc = ArgProc()
        proc.rule('$left:verify * => $right')
        assert proc.process({'left': 'test'}) == {'right': 'test'}
        assert_raises(Error, proc.process, {'left': 'value'})

    def test_global_name(self):
        global verify
        verify = 'test'
        proc = ArgProc()
        proc.rule('$left:verify * => $right')
        assert proc.process({'left': 'test'}) == {'right': 'test'}
        assert_raises(Error, proc.process, {'left': 'value'})

    def test_tags(self):
        proc = ArgProc()
        proc.rule('$left => $right [tag]')
        assert proc.process({'left': 10}, tags=['tag']) == {'right': 10}
        assert proc.process({'left': 10}, tags=[]) == {}
        assert proc.process({'left': 10}) == {'right': 10}

    def test_multiple_tags(self):
        proc = ArgProc()
        proc.rule('$left => $right [tag1,tag2]')
        assert proc.process({'left': 10}, tags=['tag2']) == {'right': 10}
        assert proc.process({'left': 10}, tags=[]) == {}
        assert proc.process({'left': 10}) == {'right': 10}

    def test_negated_tag(self):
        proc = ArgProc()
        proc.rule('$left => $right [!tag]')
        assert proc.process({'left': 10}) == {'right': 10}
        assert proc.process({'left': 10}, tags=['tg']) == {'right': 10}
        assert proc.process({'left': 10}, tags=['tag']) == {}

    def test_comment(self):
        proc = ArgProc()
        proc.rules("""
                $left1 => $right1  # comment
                #$left2 => $right2
        """)
        assert proc.process({'left1': 10}) == {'right1': 10}
        assert proc.process({'left2': 20}) == {}
