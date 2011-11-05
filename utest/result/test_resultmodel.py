import unittest
from robot.utils.asserts import assert_equal, assert_true, assert_raises

from robot.result.model import *


class TestTestSuite(unittest.TestCase):

    def setUp(self):
        self.suite = TestSuite(metadata={'M': 'V'})

    def test_modify_medatata(self):
        self.suite.metadata['m'] = 'v'
        self.suite.metadata['n'] = 'w'
        assert_equal(dict(self.suite.metadata), {'M': 'v', 'n': 'w'})

    def test_set_metadata(self):
        self.suite.metadata = {'a': '1', 'b': '1'}
        self.suite.metadata['A'] = '2'
        assert_equal(dict(self.suite.metadata), {'a': '2', 'b': '1'})

    def test_create_and_add_suite(self):
        s1 = self.suite.suites.create(name='s1')
        s2 = TestSuite(name='s2')
        self.suite.suites.append(s2)
        assert_true(s1.parent is self.suite)
        assert_true(s2.parent is self.suite)
        assert_equal(list(self.suite.suites), [s1, s2])

    def test_reset_suites(self):
        s1 = TestSuite(name='s1')
        self.suite.suites = [s1]
        s2 = self.suite.suites.create(name='s2')
        assert_true(s1.parent is self.suite)
        assert_true(s2.parent is self.suite)
        assert_equal(list(self.suite.suites), [s1, s2])

    def test_combined_suite_name(self):
        suite = TestSuite()
        assert_equal(suite.name, '')
        suite.suites.create(name='foo')
        suite.suites.create(name='bar')
        assert_equal(suite.name, 'foo & bar')
        suite.suites.create(name='zap')
        assert_equal(suite.name, 'foo & bar & zap')
        suite.name = 'new name'
        assert_equal(suite.name, 'new name')

    def test_nested_subsuites(self):
        suite = TestSuite(name='top')
        sub1 = suite.suites.create(name='sub1')
        sub2 = sub1.suites.create(name='sub2')
        assert_equal(list(suite.suites), [sub1])
        assert_equal(list(sub1.suites), [sub2])

class TestSuiteStats(unittest.TestCase):

    def test_stats(self):
        suite = self._create_suite_with_tests()
        assert_equal(suite.critical_stats.passed, 2)
        assert_equal(suite.critical_stats.failed, 1)
        assert_equal(suite.all_stats.passed, 3)
        assert_equal(suite.all_stats.failed, 2)

    def test_nested_suite_stats(self):
        suite = self._create_nested_suite_with_tests()
        assert_equal(suite.critical_stats.passed, 4)
        assert_equal(suite.critical_stats.failed, 2)
        assert_equal(suite.all_stats.passed, 6)
        assert_equal(suite.all_stats.failed, 4)

    def test_test_count(self):
        suite = self._create_nested_suite_with_tests()
        assert_equal(suite.test_count, 10)
        assert_equal(suite.suites[0].test_count, 5)
        suite.suites.append(self._create_suite_with_tests())
        assert_equal(suite.test_count, 15)
        suite.suites[-1].tests.create()
        assert_equal(suite.test_count, 16)
        assert_equal(suite.suites[-1].test_count, 6)

    def _create_nested_suite_with_tests(self):
        suite = TestSuite()
        suite.suites = [self._create_suite_with_tests(),
                        self._create_suite_with_tests()]
        return suite

    def _create_suite_with_tests(self):
        suite = TestSuite()
        suite.set_criticality([], ['nc'])
        suite.tests = [TestCase(status='PASS'),
                       TestCase(status='PASS', tags='nc'),
                       TestCase(status='PASS'),
                       TestCase(status='FAIL'),
                       TestCase(status='FAIL', tags='nc')]
        return suite


class TestSuiteStatus(unittest.TestCase):

    def test_suite_status_is_passed_by_default(self):
        assert_equal(TestSuite().status, 'PASS')

    def test_suite_status_is_failed_if_critical_failed_test(self):
        suite = TestSuite()
        suite.tests.create(status='PASS')
        assert_equal(suite.status, 'PASS')
        suite.tests.create(status='FAIL')
        assert_equal(suite.status, 'FAIL')
        suite.tests.create(status='PASS')
        assert_equal(suite.status, 'FAIL')

    def test_suite_status_is_passed_if_only_passed_tests(self):
        suite = TestSuite()
        for i in range(10):
            suite.tests.create(status='PASS')
        assert_equal(TestSuite().status, 'PASS')

    def test_suite_status_is_failed_if_failed_subsuite(self):
        suite = TestSuite()
        suite.suites.create().tests.create(status='FAIL')
        assert_equal(suite.status, 'FAIL')


class TestSuiteId(unittest.TestCase):

    def test_one_suite(self):
        assert_equal(TestSuite().id, 's1')

    def test_sub_suites(self):
        parent = TestSuite()
        for i in range(10):
            assert_equal(parent.suites.create().id, 's1-s%s' % (i+1))
        assert_equal(parent.suites[-1].suites.create().id, 's1-s10-s1')

    def test_removing_suite(self):
        suite = TestSuite()
        sub = suite.suites.create().suites.create()
        assert_equal(sub.id, 's1-s1-s1')
        suite.suites = [sub]
        assert_equal(sub.id, 's1-s1')


class TestTestCase(unittest.TestCase):

    def setUp(self):
        self.test = TestCase(tags=['t1', 't2'], name='test')

    def test_modify_tags(self):
        self.test.tags.add(['t0', 't3'])
        self.test.tags.remove('T2')
        assert_equal(list(self.test.tags), ['t0', 't1', 't3'])

    def test_set_tags(self):
        self.test.tags = ['s2', 's1']
        self.test.tags.add('s3')
        assert_equal(list(self.test.tags), ['s1', 's2', 's3'])

    def test_longname(self):
        assert_equal(self.test.longname, 'test')
        self.test.parent = TestSuite(name='suite')
        assert_equal(self.test.longname, 'suite.test')


class TestElapsedTime(unittest.TestCase):

    def test_suite_elapsed_time_when_start_and_end_given(self):
        suite = TestSuite()
        suite.starttime = '20010101 10:00:00.000'
        suite.endtime = '20010101 10:00:01.234'
        assert_equal(suite.elapsedtime, 1234)

    def test_suite_elapsed_time_is_zero_by_default(self):
        suite = TestSuite()
        assert_equal(suite.elapsedtime, 0)

    def _test_suite_elapsed_time_is_test_time(self):
        suite = TestSuite()
        suite.tests.create(starttime='19991212 12:00:00.010',
                           endtime='19991212 13:00:01.010')
        assert_equal(suite.elapsedtime, 3610000)


class TestItemLists(unittest.TestCase):

    def test_create_items(self):
        items = ItemList(str)
        item = items.create(object=1)
        assert_true(isinstance(item, str))
        assert_equal(item, '1')
        assert_equal(list(items), [item])

    def test_create_with_args_and_kwargs(self):
        class Item(object):
            def __init__(self, arg1, arg2):
                self.arg1 = arg1
                self.arg2 = arg2
        items = ItemList(Item)
        item = items.create('value 1', arg2='value 2')
        assert_equal(item.arg1, 'value 1')
        assert_equal(item.arg2, 'value 2')
        assert_equal(list(items), [item])

    def test_append_and_extend(self):
        items = ItemList(int)
        items.append(1)
        items.append(2)
        items.extend((3, 4))
        assert_equal(list(items), [1, 2, 3, 4])

    def test_only_matching_types_can_be_added(self):
        assert_raises(TypeError, ItemList(int).append, 'not integer')

    def test_parent(self):
        kw1 = Keyword()
        kw2 = Keyword()
        parent = object()
        kws = ItemList(Keyword, [kw1], parent=parent)
        kws.append(kw2)
        assert_true(kw1.parent is parent)
        assert_true(kw2.parent is parent)
        assert_equal(list(kws), [kw1, kw2])

    def test_getitem(self):
        item1 = object()
        item2 = object()
        items = ItemList(object, [item1, item2])
        assert_true(items[0] is item1)
        assert_true(items[1] is item2)
        assert_true(items[-1] is item2)

    def test_getitem_slice(self):
        items = ItemList(int, range(10))
        assert_true(isinstance(items[1:], tuple))
        assert_equal(items[:], tuple(items))
        assert_equal(items[:-1], tuple(range(9)))
        assert_equal(items[-1:1:-2], tuple(range(9, 1, -2)))

    def test_len(self):
        items = ItemList(object)
        assert_equal(len(items), 0)
        items.create()
        assert_equal(len(items), 1)

    def test_str(self):
        items = ItemList(str, ['foo', 'bar', 'quux'])
        assert_equal(str(items), '[foo, bar, quux]')

    def test_unicode(self):
        assert_equal(unicode(ItemList(int, [1, 2, 3, 4])), '[1, 2, 3, 4]')
        assert_equal(unicode(ItemList(unicode, [u'hyv\xe4\xe4', u'y\xf6t\xe4'])),
                     u'[hyv\xe4\xe4, y\xf6t\xe4]')


class TestKeywords(unittest.TestCase):

    def test_keywords_is_itemlist(self):
        assert_true(issubclass(Keywords, ItemList))

    def test_keywords_creates_keywords(self):
        assert_true(isinstance(Keywords().create(), Keyword))

    def test_setup(self):
        assert_equal(Keywords().setup, None)
        setup = Keyword(type='setup')
        assert_true(Keywords([setup, Keyword(), Keyword()]).setup is setup)

    def test_teardown(self):
        assert_equal(Keywords().teardown, None)
        teardown = Keyword(type='teardown')
        assert_true(Keywords([Keyword(), teardown]).teardown is teardown)

    def test_for_loops_are_included(self):
        kws = [Keyword(type='for'), Keyword(), Keyword(type='foritem')]
        assert_equal(list(Keywords(kws).normal), kws)
        assert_equal(list(Keywords(kws).all), kws)

    def test_iteration(self):
        kws = [Keyword(type='setup'), Keyword(), Keyword(), Keyword(type='teardown')]
        assert_equal(list(Keywords(kws)), kws)
        assert_equal(list(Keywords(kws).all), kws)
        assert_equal(list(Keywords(kws).normal), kws[1:-1])


class TestMetadata(unittest.TestCase):

    def test_normalizetion(self):
        md = Metadata([('m1', 1), ('M2', 1), ('m_3', 1), ('M1', 2), ('M 3', 2)])
        assert_equal(dict(md), {'m1': 2, 'M2': 1, 'm_3': 2})

    def test_unicode(self):
        assert_equal(unicode(Metadata()), '{}')
        d = {'a': 1, 'B': 'two', u'\xe4': u'nelj\xe4'}
        assert_equal(unicode(Metadata(d)), u'{a: 1, B: two, \xe4: nelj\xe4}')


if __name__ == '__main__':
    unittest.main()
