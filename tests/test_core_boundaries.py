# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
#
# This file is part of IPv6SubnetCalculator.
# IPv6SubnetCalculator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IPv6SubnetCalculator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IPv6SubnetCalculator. If not, see <https://www.gnu.org/licenses/>.

"""以标准库和边界组合交叉验证计算，不枚举巨量子网。"""
import itertools
import random
import tempfile
import unittest
from ipaddress import IPv4Network, IPv6Address, IPv6Network
from pathlib import Path
from unittest.mock import patch
from core.ipv6_core import calculate, locate_subnet, subnet_at_index
from core.subnet_export import subnet_at, page_subnets, export_all
from core.subnet_tools import subnet_range_text, resolve_locator_range, LOCATOR_MODES
from core.export_estimate import estimate_export_range


class CoreBoundaryTests(unittest.TestCase):
    def test_all_8385_prefix_pairs_against_standard_library(self):
        for source in range(129):
            network = IPv6Network(('2026:1015:abcd:1234:5678:90ab:cdef:1234', source), strict=False)
            for target in range(source, 129):
                with self.subTest(source=source, target=target):
                    result = calculate(str(network), str(target), preview_limit=0)
                    self.assertEqual(result.subnet_count * result.addresses_per_subnet, network.num_addresses)
                    expected = list(itertools.islice(network.subnets(new_prefix=target), 3))
                    actual = [subnet_at_index(network, target, i+1) for i in range(len(expected))]
                    self.assertEqual(actual, expected)
                    last = subnet_at_index(network, target, result.subnet_count)
                    self.assertEqual(last, IPv6Network((network[-1], target), strict=False))
                    self.assertEqual(locate_subnet(network, target, str(last[-1])), result.subnet_count)

    def test_seeded_host_input_and_small_complete_partitions(self):
        rng = random.Random(20261017)
        for _ in range(300):
            source = rng.randrange(129)
            target = rng.randrange(source, min(128, source+7)+1)
            address = IPv6Address(rng.getrandbits(128))
            result = calculate(f'{address}/{source}', str(target), preview_limit=0)
            expected = list(result.network.subnets(new_prefix=target))
            actual = [subnet_at_index(result.network, target, i+1) for i in range(len(expected))]
            self.assertEqual(actual, expected)
            self.assertEqual(result.normalized, address != result.network[0])
            for i, subnet in enumerate(actual, 1):
                self.assertEqual(locate_subnet(result.network, target, str(subnet[0])), i)
                self.assertEqual(locate_subnet(result.network, target, str(subnet[-1])), i)

    def test_public_entry_points_reject_invalid_prefix_before_writing(self):
        network = IPv6Network('2026:1015:abcd::/48')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'out.txt'
            for prefix in (True, False, 47, -1, 129, 64.5, '64', None):
                calls = (lambda: subnet_at_index(network, prefix, 1),
                    lambda: subnet_at(network, prefix, 0),
                    lambda: page_subnets(network, prefix, 1, 100),
                    lambda: locate_subnet(network, prefix, str(network[0])),
                    lambda: resolve_locator_range(LOCATOR_MODES[1], '1', network, prefix),
                    lambda: subnet_range_text(network, prefix, 1, 1),
                    lambda: estimate_export_range(network, prefix, 'txt', 1),
                    lambda: export_all(path, network, prefix, 'txt', end=1))
                for call in calls:
                    with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                        call()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_ipv4_network_is_rejected(self):
        network = IPv4Network('192.0.2.0/24')
        with self.assertRaises(ValueError):
            subnet_at_index(network, 64, 1)
        with self.assertRaises(ValueError):
            page_subnets(network, 64, 1, 25)

    def test_boolean_and_fractional_indices_are_rejected(self):
        network = IPv6Network('::/0')
        for value in (True, False, 1.5, '1'):
            with self.subTest(value=value):
                with self.assertRaises(IndexError):
                    subnet_at(network, 128, value)
                with self.assertRaises(ValueError):
                    subnet_at_index(network, 128, value)
                with self.assertRaises(ValueError):
                    page_subnets(network, 128, value, 25)
                with self.assertRaises(ValueError):
                    subnet_range_text(network, 128, value, 3)

    def test_estimator_rejects_invalid_window(self):
        network = IPv6Network('::/126')
        for count, start in ((True, 0), (1, True), (1.5, 0), (0, 0), (1, -1), (4, 1)):
            with self.subTest(count=count, start=start), self.assertRaises(ValueError):
                estimate_export_range(network, 128, 'txt', count, start)

    def test_replace_failure_preserves_original_and_removes_temporary_file(self):
        for fmt in ('txt', 'xlsx'):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/('existing.'+fmt)
                path.write_bytes(b'original')
                with patch('core.subnet_export.os.replace', side_effect=PermissionError('file in use')):
                    with self.assertRaises(PermissionError):
                        export_all(path, IPv6Network('::/120'), 128, fmt, end=20)
                self.assertEqual(path.read_bytes(), b'original')
                self.assertEqual([p.name for p in Path(directory).iterdir()], [path.name])

    def test_mid_write_failure_preserves_original(self):
        for fmt in ('txt', 'xlsx'):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/('existing.'+fmt)
                path.write_bytes(b'original')
                def fail(_done, _total):
                    raise OSError('simulated disk write failure')
                with self.assertRaises(OSError):
                    export_all(path, IPv6Network('::/112'), 128, fmt, end=2048, progress=fail)
                self.assertEqual(path.read_bytes(), b'original')
                self.assertEqual([p.name for p in Path(directory).iterdir()], [path.name])
