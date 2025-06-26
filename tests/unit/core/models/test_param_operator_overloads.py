# ~/clientfactory/tests/unit/core/models/test_param_operator_overloads.py
# ~/clientfactory/tests/unit/core/models/test_param_operator_overloads.py

import pytest
from clientfactory.core.models.request import Param


class TestParamOperatorOverloads:
    """Test >> and << operators for Param merging."""

    def test_rshift_basic_merge(self):
        """Test basic >> merge where left takes priority."""
        p1 = Param(name='p1', source='src1', target='tgt1')
        p2 = Param(name='p2', source='src2', target='tgt2')

        result = p1 >> p2
        assert result.name == 'p1'
        assert result.source == 'src1'
        assert result.target == 'tgt1'

    def test_lshift_basic_merge(self):
        """Test basic << merge where right takes priority."""
        p1 = Param(name='p1', source='src1', target='tgt1')
        p2 = Param(name='p2', source='src2', target='tgt2')

        result = p1 << p2
        assert result.name == 'p2'
        assert result.source == 'src2'
        assert result.target == 'tgt2'

    def test_rshift_partial_merge(self):
        """Test >> merge with non-overlapping attributes."""
        p1 = Param(name='p1', choices=['a', 'b'])
        p2 = Param(mapping={'x': 1, 'y': 2})

        result = p1 >> p2
        assert result.name == 'p1'
        assert result.choices == ['a', 'b']
        assert result.mapping == {'x': 1, 'y': 2}

    def test_lshift_partial_merge(self):
        """Test << merge with non-overlapping attributes."""
        p1 = Param(name='p1', choices=['a', 'b'])
        p2 = Param(mapping={'x': 1, 'y': 2})

        result = p1 << p2
        assert result.name == 'p1'  # p2 has no name
        assert result.choices == ['a', 'b']
        assert result.mapping == {'x': 1, 'y': 2}

    def test_chained_operations(self):
        """Test chaining >> and << operations."""
        p1 = Param(name='p1', source='src1')
        p2 = Param(target='tgt2', required=True)
        p3 = Param(default='default3')

        result = (p1 >> p2) << p3
        assert result.name == 'p1'
        assert result.source == 'src1'
        assert result.target == 'tgt2'
        assert result.required is True
        assert result.default == 'default3'

    def test_class_based_merge(self):
        """Test merging with class-based params."""
        class QueryParam(Param):
            source = 'query_source'
            choices = ['a', 'b', 'c']

        q1 = QueryParam(name='q1')
        p2 = Param(name='p2', choices=['x', 'y'])

        result = q1 >> p2
        assert result.name == 'q1'
        assert result.source == 'query_source'
        assert result.choices == ['a', 'b', 'c']

    def test_allownone_preserved(self):
        """Test that allownone attribute is preserved."""
        p1 = Param(name='p1', allownone=False)
        p2 = Param(name='p2', allownone=True)

        result1 = p1 >> p2
        assert result1.allownone is False

        result2 = p1 << p2
        assert result2.allownone is True
