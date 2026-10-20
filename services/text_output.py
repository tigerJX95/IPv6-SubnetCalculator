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

"""将已经确定的 UTF-8 文本写入临时文件，成功后原子替换目标。"""
import os
import tempfile
from pathlib import Path


def save_text_atomic(destination, text):
    path=Path(destination)
    data=text.encode('utf-8')
    fd,temporary=tempfile.mkstemp(prefix='.ipv6-text-',suffix='.tmp',dir=str(path.parent))
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    return path
