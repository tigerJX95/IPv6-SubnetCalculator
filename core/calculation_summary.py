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

"""计算结果摘要的纯文本格式，不依赖界面、剪贴板或逐条子网生成。"""
from core.localized_text import text as tx, join_text as jt
from core.address_usage import describe_network
from core.ipv6_core import SubnetResult, prefix_analysis


def format_calculation_summary(result: SubnetResult) -> str:
    """将一次成功计算的不可变快照转换为可粘贴到规划文档的摘要。"""
    usage = describe_network(result.network)
    return jt('\n', (tx('IPv6 子网计算摘要'), tx('网络地址：{0}', result.network), tx('源网络前缀：/{0}', result.network.prefixlen), tx('目标子网前缀：/{0}', result.target_prefix), tx('网络起始地址：{0}', result.start_address), tx('网络结束地址：{0}', result.end_address), tx('网络地址总量：{0:,}', result.network.num_addresses), tx('可划分子网数：{0:,}', result.subnet_count), tx('每个子网地址数：{0:,}', result.addresses_per_subnet), tx('新增子网位数：{0} 位', prefix_analysis(result)), '', tx('地址类型：{0}', usage.name), tx('部署提示：{0}', usage.guidance), tx('规范参考：{0}', usage.reference), '', tx('说明：IPv6 没有广播地址；结束地址表示网段最大地址。'), tx('地址总量为数学容量，不代表实际可分配主机数量。')))
