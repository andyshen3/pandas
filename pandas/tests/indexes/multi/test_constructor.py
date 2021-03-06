# -*- coding: utf-8 -*-

import re

import numpy as np
import pytest

from pandas._libs.tslib import Timestamp
from pandas.compat import lrange, range

from pandas.core.dtypes.cast import construct_1d_object_array_from_listlike

import pandas as pd
from pandas import Index, MultiIndex, date_range
import pandas.util.testing as tm


def test_constructor_single_level():
    result = MultiIndex(levels=[['foo', 'bar', 'baz', 'qux']],
                        labels=[[0, 1, 2, 3]], names=['first'])
    assert isinstance(result, MultiIndex)
    expected = Index(['foo', 'bar', 'baz', 'qux'], name='first')
    tm.assert_index_equal(result.levels[0], expected)
    assert result.names == ['first']


def test_constructor_no_levels():
    msg = "non-zero number of levels/labels"
    with pytest.raises(ValueError, match=msg):
        MultiIndex(levels=[], labels=[])

    both_re = re.compile('Must pass both levels and labels')
    with pytest.raises(TypeError, match=both_re):
        MultiIndex(levels=[])
    with pytest.raises(TypeError, match=both_re):
        MultiIndex(labels=[])


def test_constructor_nonhashable_names():
    # GH 20527
    levels = [[1, 2], [u'one', u'two']]
    labels = [[0, 0, 1, 1], [0, 1, 0, 1]]
    names = (['foo'], ['bar'])
    message = "MultiIndex.name must be a hashable type"
    with pytest.raises(TypeError, match=message):
        MultiIndex(levels=levels, labels=labels, names=names)

    # With .rename()
    mi = MultiIndex(levels=[[1, 2], [u'one', u'two']],
                    labels=[[0, 0, 1, 1], [0, 1, 0, 1]],
                    names=('foo', 'bar'))
    renamed = [['foor'], ['barr']]
    with pytest.raises(TypeError, match=message):
        mi.rename(names=renamed)

    # With .set_names()
    with pytest.raises(TypeError, match=message):
        mi.set_names(names=renamed)


def test_constructor_mismatched_label_levels(idx):
    labels = [np.array([1]), np.array([2]), np.array([3])]
    levels = ["a"]

    msg = "Length of levels and labels must be the same"
    with pytest.raises(ValueError, match=msg):
        MultiIndex(levels=levels, labels=labels)

    length_error = re.compile('>= length of level')
    label_error = re.compile(r'Unequal label lengths: \[4, 2\]')

    # important to check that it's looking at the right thing.
    with pytest.raises(ValueError, match=length_error):
        MultiIndex(levels=[['a'], ['b']],
                   labels=[[0, 1, 2, 3], [0, 3, 4, 1]])

    with pytest.raises(ValueError, match=label_error):
        MultiIndex(levels=[['a'], ['b']], labels=[[0, 0, 0, 0], [0, 0]])

    # external API
    with pytest.raises(ValueError, match=length_error):
        idx.copy().set_levels([['a'], ['b']])

    with pytest.raises(ValueError, match=label_error):
        idx.copy().set_labels([[0, 0, 0, 0], [0, 0]])


def test_copy_in_constructor():
    levels = np.array(["a", "b", "c"])
    labels = np.array([1, 1, 2, 0, 0, 1, 1])
    val = labels[0]
    mi = MultiIndex(levels=[levels, levels], labels=[labels, labels],
                    copy=True)
    assert mi.labels[0][0] == val
    labels[0] = 15
    assert mi.labels[0][0] == val
    val = levels[0]
    levels[0] = "PANDA"
    assert mi.levels[0][0] == val


def test_from_arrays(idx):
    arrays = [np.asarray(lev).take(lab)
              for lev, lab in zip(idx.levels, idx.labels)]

    # list of arrays as input
    result = MultiIndex.from_arrays(arrays, names=idx.names)
    tm.assert_index_equal(result, idx)

    # infer correctly
    result = MultiIndex.from_arrays([[pd.NaT, Timestamp('20130101')],
                                     ['a', 'b']])
    assert result.levels[0].equals(Index([Timestamp('20130101')]))
    assert result.levels[1].equals(Index(['a', 'b']))


def test_from_arrays_iterator(idx):
    # GH 18434
    arrays = [np.asarray(lev).take(lab)
              for lev, lab in zip(idx.levels, idx.labels)]

    # iterator as input
    result = MultiIndex.from_arrays(iter(arrays), names=idx.names)
    tm.assert_index_equal(result, idx)

    # invalid iterator input
    msg = "Input must be a list / sequence of array-likes."
    with pytest.raises(TypeError, match=msg):
        MultiIndex.from_arrays(0)


def test_from_arrays_index_series_datetimetz():
    idx1 = pd.date_range('2015-01-01 10:00', freq='D', periods=3,
                         tz='US/Eastern')
    idx2 = pd.date_range('2015-01-01 10:00', freq='H', periods=3,
                         tz='Asia/Tokyo')
    result = pd.MultiIndex.from_arrays([idx1, idx2])
    tm.assert_index_equal(result.get_level_values(0), idx1)
    tm.assert_index_equal(result.get_level_values(1), idx2)

    result2 = pd.MultiIndex.from_arrays([pd.Series(idx1), pd.Series(idx2)])
    tm.assert_index_equal(result2.get_level_values(0), idx1)
    tm.assert_index_equal(result2.get_level_values(1), idx2)

    tm.assert_index_equal(result, result2)


def test_from_arrays_index_series_timedelta():
    idx1 = pd.timedelta_range('1 days', freq='D', periods=3)
    idx2 = pd.timedelta_range('2 hours', freq='H', periods=3)
    result = pd.MultiIndex.from_arrays([idx1, idx2])
    tm.assert_index_equal(result.get_level_values(0), idx1)
    tm.assert_index_equal(result.get_level_values(1), idx2)

    result2 = pd.MultiIndex.from_arrays([pd.Series(idx1), pd.Series(idx2)])
    tm.assert_index_equal(result2.get_level_values(0), idx1)
    tm.assert_index_equal(result2.get_level_values(1), idx2)

    tm.assert_index_equal(result, result2)


def test_from_arrays_index_series_period():
    idx1 = pd.period_range('2011-01-01', freq='D', periods=3)
    idx2 = pd.period_range('2015-01-01', freq='H', periods=3)
    result = pd.MultiIndex.from_arrays([idx1, idx2])
    tm.assert_index_equal(result.get_level_values(0), idx1)
    tm.assert_index_equal(result.get_level_values(1), idx2)

    result2 = pd.MultiIndex.from_arrays([pd.Series(idx1), pd.Series(idx2)])
    tm.assert_index_equal(result2.get_level_values(0), idx1)
    tm.assert_index_equal(result2.get_level_values(1), idx2)

    tm.assert_index_equal(result, result2)


def test_from_arrays_index_datetimelike_mixed():
    idx1 = pd.date_range('2015-01-01 10:00', freq='D', periods=3,
                         tz='US/Eastern')
    idx2 = pd.date_range('2015-01-01 10:00', freq='H', periods=3)
    idx3 = pd.timedelta_range('1 days', freq='D', periods=3)
    idx4 = pd.period_range('2011-01-01', freq='D', periods=3)

    result = pd.MultiIndex.from_arrays([idx1, idx2, idx3, idx4])
    tm.assert_index_equal(result.get_level_values(0), idx1)
    tm.assert_index_equal(result.get_level_values(1), idx2)
    tm.assert_index_equal(result.get_level_values(2), idx3)
    tm.assert_index_equal(result.get_level_values(3), idx4)

    result2 = pd.MultiIndex.from_arrays([pd.Series(idx1),
                                         pd.Series(idx2),
                                         pd.Series(idx3),
                                         pd.Series(idx4)])
    tm.assert_index_equal(result2.get_level_values(0), idx1)
    tm.assert_index_equal(result2.get_level_values(1), idx2)
    tm.assert_index_equal(result2.get_level_values(2), idx3)
    tm.assert_index_equal(result2.get_level_values(3), idx4)

    tm.assert_index_equal(result, result2)


def test_from_arrays_index_series_categorical():
    # GH13743
    idx1 = pd.CategoricalIndex(list("abcaab"), categories=list("bac"),
                               ordered=False)
    idx2 = pd.CategoricalIndex(list("abcaab"), categories=list("bac"),
                               ordered=True)

    result = pd.MultiIndex.from_arrays([idx1, idx2])
    tm.assert_index_equal(result.get_level_values(0), idx1)
    tm.assert_index_equal(result.get_level_values(1), idx2)

    result2 = pd.MultiIndex.from_arrays([pd.Series(idx1), pd.Series(idx2)])
    tm.assert_index_equal(result2.get_level_values(0), idx1)
    tm.assert_index_equal(result2.get_level_values(1), idx2)

    result3 = pd.MultiIndex.from_arrays([idx1.values, idx2.values])
    tm.assert_index_equal(result3.get_level_values(0), idx1)
    tm.assert_index_equal(result3.get_level_values(1), idx2)


def test_from_arrays_empty():
    # 0 levels
    msg = "Must pass non-zero number of levels/labels"
    with pytest.raises(ValueError, match=msg):
        MultiIndex.from_arrays(arrays=[])

    # 1 level
    result = MultiIndex.from_arrays(arrays=[[]], names=['A'])
    assert isinstance(result, MultiIndex)
    expected = Index([], name='A')
    tm.assert_index_equal(result.levels[0], expected)

    # N levels
    for N in [2, 3]:
        arrays = [[]] * N
        names = list('ABC')[:N]
        result = MultiIndex.from_arrays(arrays=arrays, names=names)
        expected = MultiIndex(levels=[[]] * N, labels=[[]] * N,
                              names=names)
        tm.assert_index_equal(result, expected)


@pytest.mark.parametrize('invalid_array', [
    (1),
    ([1]),
    ([1, 2]),
    ([[1], 2]),
    ('a'),
    (['a']),
    (['a', 'b']),
    ([['a'], 'b']),
])
def test_from_arrays_invalid_input(invalid_array):
    invalid_inputs = [1, [1], [1, 2], [[1], 2],
                      'a', ['a'], ['a', 'b'], [['a'], 'b']]
    for i in invalid_inputs:
        pytest.raises(TypeError, MultiIndex.from_arrays, arrays=i)


@pytest.mark.parametrize('idx1, idx2', [
    ([1, 2, 3], ['a', 'b']),
    ([], ['a', 'b']),
    ([1, 2, 3], [])
])
def test_from_arrays_different_lengths(idx1, idx2):
    # see gh-13599
    msg = '^all arrays must be same length$'
    with pytest.raises(ValueError, match=msg):
        MultiIndex.from_arrays([idx1, idx2])


def test_from_tuples():
    msg = 'Cannot infer number of levels from empty list'
    with pytest.raises(TypeError, match=msg):
        MultiIndex.from_tuples([])

    expected = MultiIndex(levels=[[1, 3], [2, 4]],
                          labels=[[0, 1], [0, 1]],
                          names=['a', 'b'])

    # input tuples
    result = MultiIndex.from_tuples(((1, 2), (3, 4)), names=['a', 'b'])
    tm.assert_index_equal(result, expected)


def test_from_tuples_iterator():
    # GH 18434
    # input iterator for tuples
    expected = MultiIndex(levels=[[1, 3], [2, 4]],
                          labels=[[0, 1], [0, 1]],
                          names=['a', 'b'])

    result = MultiIndex.from_tuples(zip([1, 3], [2, 4]), names=['a', 'b'])
    tm.assert_index_equal(result, expected)

    # input non-iterables
    msg = 'Input must be a list / sequence of tuple-likes.'
    with pytest.raises(TypeError, match=msg):
        MultiIndex.from_tuples(0)


def test_from_tuples_empty():
    # GH 16777
    result = MultiIndex.from_tuples([], names=['a', 'b'])
    expected = MultiIndex.from_arrays(arrays=[[], []],
                                      names=['a', 'b'])
    tm.assert_index_equal(result, expected)


def test_from_tuples_index_values(idx):
    result = MultiIndex.from_tuples(idx)
    assert (result.values == idx.values).all()


def test_from_product_empty_zero_levels():
    # 0 levels
    msg = "Must pass non-zero number of levels/labels"
    with pytest.raises(ValueError, match=msg):
        MultiIndex.from_product([])


def test_from_product_empty_one_level():
    result = MultiIndex.from_product([[]], names=['A'])
    expected = pd.Index([], name='A')
    tm.assert_index_equal(result.levels[0], expected)


@pytest.mark.parametrize('first, second', [
    ([], []),
    (['foo', 'bar', 'baz'], []),
    ([], ['a', 'b', 'c']),
])
def test_from_product_empty_two_levels(first, second):
    names = ['A', 'B']
    result = MultiIndex.from_product([first, second], names=names)
    expected = MultiIndex(levels=[first, second],
                          labels=[[], []], names=names)
    tm.assert_index_equal(result, expected)


@pytest.mark.parametrize('N', list(range(4)))
def test_from_product_empty_three_levels(N):
    # GH12258
    names = ['A', 'B', 'C']
    lvl2 = lrange(N)
    result = MultiIndex.from_product([[], lvl2, []], names=names)
    expected = MultiIndex(levels=[[], lvl2, []],
                          labels=[[], [], []], names=names)
    tm.assert_index_equal(result, expected)


@pytest.mark.parametrize('invalid_input', [
    1,
    [1],
    [1, 2],
    [[1], 2],
    'a',
    ['a'],
    ['a', 'b'],
    [['a'], 'b'],
])
def test_from_product_invalid_input(invalid_input):
    pytest.raises(TypeError, MultiIndex.from_product, iterables=invalid_input)


def test_from_product_datetimeindex():
    dt_index = date_range('2000-01-01', periods=2)
    mi = pd.MultiIndex.from_product([[1, 2], dt_index])
    etalon = construct_1d_object_array_from_listlike([
        (1, pd.Timestamp('2000-01-01')),
        (1, pd.Timestamp('2000-01-02')),
        (2, pd.Timestamp('2000-01-01')),
        (2, pd.Timestamp('2000-01-02')),
    ])
    tm.assert_numpy_array_equal(mi.values, etalon)


@pytest.mark.parametrize('ordered', [False, True])
@pytest.mark.parametrize('f', [
    lambda x: x,
    lambda x: pd.Series(x),
    lambda x: x.values
])
def test_from_product_index_series_categorical(ordered, f):
    # GH13743
    first = ['foo', 'bar']

    idx = pd.CategoricalIndex(list("abcaab"), categories=list("bac"),
                              ordered=ordered)
    expected = pd.CategoricalIndex(list("abcaab") + list("abcaab"),
                                   categories=list("bac"),
                                   ordered=ordered)

    result = pd.MultiIndex.from_product([first, f(idx)])
    tm.assert_index_equal(result.get_level_values(1), expected)


def test_from_product():

    first = ['foo', 'bar', 'buz']
    second = ['a', 'b', 'c']
    names = ['first', 'second']
    result = MultiIndex.from_product([first, second], names=names)

    tuples = [('foo', 'a'), ('foo', 'b'), ('foo', 'c'), ('bar', 'a'),
              ('bar', 'b'), ('bar', 'c'), ('buz', 'a'), ('buz', 'b'),
              ('buz', 'c')]
    expected = MultiIndex.from_tuples(tuples, names=names)

    tm.assert_index_equal(result, expected)


def test_from_product_iterator():
    # GH 18434
    first = ['foo', 'bar', 'buz']
    second = ['a', 'b', 'c']
    names = ['first', 'second']
    tuples = [('foo', 'a'), ('foo', 'b'), ('foo', 'c'), ('bar', 'a'),
              ('bar', 'b'), ('bar', 'c'), ('buz', 'a'), ('buz', 'b'),
              ('buz', 'c')]
    expected = MultiIndex.from_tuples(tuples, names=names)

    # iterator as input
    result = MultiIndex.from_product(iter([first, second]), names=names)
    tm.assert_index_equal(result, expected)

    # Invalid non-iterable input
    msg = "Input must be a list / sequence of iterables."
    with pytest.raises(TypeError, match=msg):
        MultiIndex.from_product(0)


def test_create_index_existing_name(idx):

    # GH11193, when an existing index is passed, and a new name is not
    # specified, the new index should inherit the previous object name
    index = idx
    index.names = ['foo', 'bar']
    result = pd.Index(index)
    expected = Index(
        Index([
            ('foo', 'one'), ('foo', 'two'),
            ('bar', 'one'), ('baz', 'two'),
            ('qux', 'one'), ('qux', 'two')],
            dtype='object'
        ),
        names=['foo', 'bar']
    )
    tm.assert_index_equal(result, expected)

    result = pd.Index(index, names=['A', 'B'])
    expected = Index(
        Index([
            ('foo', 'one'), ('foo', 'two'),
            ('bar', 'one'), ('baz', 'two'),
            ('qux', 'one'), ('qux', 'two')],
            dtype='object'
        ),
        names=['A', 'B']
    )
    tm.assert_index_equal(result, expected)


def test_tuples_with_name_string():
    # GH 15110 and GH 14848

    li = [(0, 0, 1), (0, 1, 0), (1, 0, 0)]
    with pytest.raises(ValueError):
        pd.Index(li, name='abc')
    with pytest.raises(ValueError):
        pd.Index(li, name='a')


def test_from_tuples_with_tuple_label():
    # GH 15457
    expected = pd.DataFrame([[2, 1, 2], [4, (1, 2), 3]],
                            columns=['a', 'b', 'c']).set_index(['a', 'b'])
    idx = pd.MultiIndex.from_tuples([(2, 1), (4, (1, 2))], names=('a', 'b'))
    result = pd.DataFrame([2, 3], columns=['c'], index=idx)
    tm.assert_frame_equal(expected, result)
