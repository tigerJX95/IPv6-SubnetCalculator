"""V0.3 前缀分析及常用前缀专项测试。"""
import unittest
from ipv6_core import calculate, common_target_prefixes, prefix_analysis, subnet_count_description


class PrefixAnalysisTest(unittest.TestCase):
    def test_original_example(self):
        result = calculate('2026:1015:abcd::/48', '64', preview_limit=0)
        self.assertEqual(prefix_analysis(result), 16)

    def test_56_to_64(self):
        result = calculate('2026:1015:abcd:ac00::/56', '64', preview_limit=0)
        self.assertEqual(prefix_analysis(result), 8)

    def test_same_prefix(self):
        result = calculate('2026:1015:abcd::/48', '48', preview_limit=0)
        self.assertEqual(prefix_analysis(result), 0)

    def test_128_bit_boundary(self):
        result = calculate('2026:1015:abcd::/128', '128', preview_limit=0)
        self.assertEqual(prefix_analysis(result), 0)

    def test_128_cannot_split(self):
        result = calculate('2026:1015:abcd::/128', '128', preview_limit=0)
        self.assertIn('无法继续划分子网', subnet_count_description(result))
        self.assertEqual(result.subnet_count, 1)

    def test_127_can_split_into_two_128s(self):
        result = calculate('2026:1015:abcd::/127', '128', preview_limit=0)
        self.assertEqual(result.subnet_count, 2)
        self.assertEqual(subnet_count_description(result), '2')

    def test_same_prefix_keeps_original_network(self):
        result = calculate('2026:1015:abcd::/64', '64', preview_limit=0)
        self.assertIn('未进一步划分', subnet_count_description(result))

    def test_common_prefixes_from_48(self):
        self.assertEqual(common_target_prefixes(48), (48, 56, 60, 64, 127, 128))

    def test_common_prefixes_from_56(self):
        self.assertEqual(common_target_prefixes(56), (56, 60, 64, 127, 128))

    def test_common_prefixes_from_65(self):
        self.assertEqual(common_target_prefixes(65), (127, 128))

    def test_common_prefixes_from_128(self):
        self.assertEqual(common_target_prefixes(128), (128,))

    def test_common_prefixes_from_zero(self):
        self.assertEqual(common_target_prefixes(0), (48, 56, 60, 64, 127, 128))

    def test_invalid_prefixes(self):
        for bad in (-1, 129, True, '64'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                common_target_prefixes(bad)
