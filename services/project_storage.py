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

"""Planning JSON uses the same bounded reader and conflict-safe writer as plans."""
from core.localized_text import text as tx
from core.planning_project import project_from_payload, project_to_payload
from services.plan_storage import _load_document, _save_document

# JSON escaping may expand the original 1 MiB text by up to six times.
MAX_PROJECT_BYTES = 7 * 1024 * 1024


def load_project(path):
    return _load_document(path, project_from_payload, MAX_PROJECT_BYTES,
        tx('规划项目超过 7 MiB，无法打开。'))


def save_project(path, project, *, expected=None):
    return _save_document(path, project_to_payload(project), MAX_PROJECT_BYTES, expected=expected)
