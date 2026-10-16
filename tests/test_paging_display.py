"""超大分页统计的紧凑显示专项测试。"""
import unittest
from main import compact_count

class PagingDisplayTests(unittest.TestCase):
    def test_normal_count_is_exact(self):
        self.assertEqual(compact_count(656), '656')
        self.assertEqual(compact_count(12345), '12,345')

    def test_large_count_is_compact(self):
        self.assertEqual(compact_count(123456789), '1.23亿')
        self.assertEqual(compact_count(180143985094820), '180.14万亿')
        self.assertEqual(compact_count(18014398509481984), '1.80京')

    def test_extreme_ipv6_number_uses_scientific(self):
        summary = compact_count(2**128)
        self.assertIn('×10^38', summary)
        self.assertLess(len(summary), 16)

if __name__ == '__main__':
    unittest.main()
