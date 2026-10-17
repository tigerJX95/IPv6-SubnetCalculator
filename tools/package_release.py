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

"""将单文件 EXE 与项目／第三方许可证整理为 Windows 发布 ZIP。"""
import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_info import APP_VERSION

LICENSE_FILES = ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md',
                 'docs/licenses/PyQt6_GPLv3.txt', 'docs/licenses/Qt_LGPLv3.txt',
                 'docs/licenses/PyQt6_sip_LICENSE.txt')


def package_release(project_root=ROOT):
    root = Path(project_root)
    name = f'IPv6SubnetCalculator_V{APP_VERSION}'
    executable = root/'dist'/f'{name}.exe'
    inputs = [(executable, f'{name}/{executable.name}')]
    inputs.extend((root/path, f'{name}/{path}') for path in LICENSE_FILES)
    for path, _ in inputs:
        if not path.is_file():
            raise FileNotFoundError('Missing release file: '+str(path))
    destination = root/'dist'/f'{name}_Windows.zip'
    fd, temporary = tempfile.mkstemp(prefix='.ipv6-release-', suffix='.zip', dir=str(destination.parent))
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path, member in inputs:
                archive.write(path, member)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return destination


if __name__ == '__main__':
    print(package_release())
