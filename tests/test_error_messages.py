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

"""文件访问错误保留诊断标识，中文原因不依赖系统错误语言。"""
import errno
import unittest
from core.ipv6_core import InputError, calculate
from core.network_relations import analyze_networks
from services.error_messages import describe_error


class ErrorMessageTests(unittest.TestCase):
    def test_known_os_errors_localized_with_original_path_and_code(self):
        for code,hint in ((errno.ENOENT,'找不到'),(errno.EACCES,'权限'),(errno.ENOSPC,'空间不足'),(errno.EROFS,'只读')):
            text=describe_error(OSError(code,'English system error','中文/计算方案.json'))
            self.assertIn(hint,text)
            self.assertIn('中文/计算方案.json',text)
            self.assertIn(str(code),text)
            self.assertNotIn('English system error',text)

    def test_unknown_os_error_has_chinese_fallback(self):
        self.assertIn('系统无法完成',describe_error(OSError('English only')))

    def test_windows_sharing_violation_has_specific_message(self):
        error=OSError(errno.EACCES,'sharing violation');error.winerror=32
        text=describe_error(error)
        self.assertIn('其他程序占用',text)
        self.assertIn('32',text)

    def test_application_error_text_is_preserved(self):
        error=InputError('请填写有效 CIDR。')
        self.assertEqual(describe_error(error),str(error))

    def test_structured_field_matches_failing_target_or_network(self):
        with self.assertRaises(InputError) as caught:calculate('::/64','63')
        self.assertEqual(caught.exception.field,'target')
        with self.assertRaises(InputError) as caught:analyze_networks('::/0','bad')
        self.assertEqual(caught.exception.field,'B')
