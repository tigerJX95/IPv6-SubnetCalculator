"""V0.4 新增范围复制及详情相邻导航测试。"""
import unittest
from ipaddress import IPv6Network
from ipv6_core import InputError
from subnet_tools import MAX_COPY_RECORDS, adjacent_subnet_index, subnet_range_text, validate_copy_range

class ExtraFunctionsTest(unittest.TestCase):
    def setUp(self):
        self.net = IPv6Network('2026:1015:abcd::/48')

    def test_copy_single(self):
        self.assertEqual(subnet_range_text(self.net, 64, 2, 2), '2\t2026:1015:abcd:1::/64')

    def test_copy_range(self):
        self.assertEqual(subnet_range_text(self.net, 64, 1, 3).count('\n'), 2)

    def test_copy_last(self):
        self.assertIn('ffff::/64', subnet_range_text(self.net, 64, 65536, 65536))

    def test_validate_copy_range(self):
        self.assertEqual(validate_copy_range('2', '5', 65536), (2, 5))

    def test_copy_limit(self):
        with self.assertRaises(InputError):
            validate_copy_range('1', str(MAX_COPY_RECORDS + 1), 65536)

    def test_copy_invalid_bounds(self):
        for start, end in [('5','2'), ('0','1'), ('1','65537'), ('abc','2')]:
            with self.subTest(start=start, end=end), self.assertRaises(InputError):
                validate_copy_range(start, end, 65536)

    def test_no_unbounded_copy(self):
        with self.assertRaises(InputError):
            subnet_range_text(self.net, 64, 1, MAX_COPY_RECORDS + 1)

    def test_adjacent(self):
        self.assertEqual(adjacent_subnet_index(2, 10, -1), 1)
        self.assertEqual(adjacent_subnet_index(2, 10, 1), 3)

    def test_adjacent_boundaries(self):
        self.assertEqual(adjacent_subnet_index(1, 10, -1), 1)
        self.assertEqual(adjacent_subnet_index(10, 10, 1), 10)

    def test_adjacent_huge(self):
        self.assertEqual(adjacent_subnet_index(2**128-1, 2**128, 1), 2**128)

    def test_adjacent_invalid(self):
        with self.assertRaises(InputError):
            adjacent_subnet_index(1, 10, 0)
