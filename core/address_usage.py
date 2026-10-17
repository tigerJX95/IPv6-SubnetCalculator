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

"""依据特殊用途前缀识别 IPv6 网络的部署适用性；不影响数学计算。"""
from dataclasses import dataclass
from ipaddress import IPv6Network


@dataclass(frozen=True)
class AddressUsage:
    name: str
    guidance: str
    reference: str
    level: str  # 信息、注意、警告


# 更具体的前缀必须优先于其上层范围。条目保留常见且有明确部署意义的用途类别。
_ENTRIES = (
    ('::/128', '未指定地址', '不可作为普通网络接口或终端地址分配；仅用于协议规定的特殊场景。', 'RFC 4291', '警告'),
    ('::1/128', '环回地址', '仅用于本机通信，不可分配到普通网络接口进行设备互联。', 'RFC 4291', '警告'),
    ('::ffff:0:0/96', 'IPv4 映射地址', '主要用于软件接口表示 IPv4 地址，并非独立的 IPv6 网络分配前缀。', 'RFC 4291', '警告'),
    ('64:ff9b::/96', 'IPv4/IPv6 转换地址', '用于 NAT64 等 IPv4/IPv6 转换场景，不应当作普通终端公网地址池使用。', 'RFC 6052', '注意'),
    ('64:ff9b:1::/48', '本地 IPv4/IPv6 转换地址', '供特定网络中的地址转换使用，需按部署规范配置，非普通公网地址池。', 'RFC 8215', '注意'),
    ('100::/64', '丢弃专用地址', '用于丢弃流量等规定用途，不应当作普通互联地址使用。', 'RFC 6666', '警告'),
    ('100:0:0:1::/64', '虚拟示例前缀', '用于协议规定的虚拟用途，不应作为实际终端地址分配。', 'RFC 9780', '警告'),
    ('fec0::/10', '旧式站点本地地址（已废弃）', '旧式站点本地地址已由 RFC 3879 废弃，不应用于新网络部署；内部网络请优先采用按规范生成的 ULA。', 'RFC 3879 / RFC 4193', '警告'),
    ('2001::/32', 'Teredo 隧道地址', '历史 IPv6 过渡机制地址，不建议用于新建 IPv6 网络的普通地址分配。', 'RFC 4380', '注意'),
    ('2001:20::/28', 'ORCHIDv2 标识符地址', '用于特定协议的加密哈希标识符，不属于普通单播网络地址分配空间。', 'RFC 7343', '注意'),
    ('2001:2::/48', '基准测试地址', '用于性能基准测试，不应用于实际公网地址分配。', 'RFC 5180', '警告'),
    ('2001:db8::/32', '文档示例地址', '保留供文档与教学示例使用，不可用于真实公网地址部署。', 'RFC 3849', '警告'),
    ('3fff::/20', '文档示例地址', '保留供文档与教学示例使用，不可用于真实公网地址部署。', 'RFC 9637', '警告'),
    ('2002::/16', '6to4 隧道地址', '属于历史 IPv6 过渡机制；不建议作为新建 IPv6 网络的普通互联地址资源。', 'RFC 3056 / RFC 7526', '注意'),
    ('5f00::/16', 'SRv6 SID 地址', '用于段路由标识符（SID），应按相应网络架构规划，不宜作为普通地址池使用。', 'RFC 9602', '注意'),
    ('fc00::/7', '唯一本地地址空间（ULA）', '整个 ULA 范围适用于内部网络用途；其中 fd00::/8 可按 RFC 4193 生成本地前缀，fc00::/8 尚无通用本地自行分配机制；不作为普通公网地址路由。', 'RFC 4193', '注意'),
    ('fc00::/8', 'ULA 保留分配部分', '属于唯一本地地址空间，但当前没有通用的本地自行分配机制；新建内部网络通常使用 fd00::/8。', 'RFC 4193', '注意'),
    ('fd00::/8', '唯一本地地址（ULA）', '适合内部 IPv6 网络及 VPN 站点互联，不作为普通公网地址直接路由；建议随机生成 ULA /48 前缀。', 'RFC 4193', '信息'),
    ('fe80::/10', '链路本地地址', '用于单链路上的通信，不应作为跨路由器或公网互联的地址资源。', 'RFC 4291', '注意'),
    ('ff00::/8', 'IPv6 组播地址', '用于组播通信，不是普通单播终端地址，不适用于常规单播子网部署。', 'RFC 4291', '警告'),
    # IETF 协议分配范围可能包含更具体的特殊登记项；不以宽泛类别取代细项。
    ('2001::/23', 'IETF 协议专用地址空间', '用于 IETF 协议相关分配；是否可在具体网络部署须依据更具体的地址用途规范，不能直接视为普通公网地址池。', 'RFC 2928 / IANA', '注意'),
)
_REGISTERED = tuple((IPv6Network(cidr), AddressUsage(name, desc, ref, level)) for cidr,name,desc,ref,level in _ENTRIES)
_GLOBAL_UNICAST = IPv6Network('2000::/3')


def describe_network(network: IPv6Network) -> AddressUsage:
    """对整个输入前缀进行判断；跨越多个地址类别时给出混合范围提醒。"""
    if not isinstance(network, IPv6Network):
        raise TypeError('network 必须是 IPv6Network')
    specific = [(block.prefixlen, usage) for block, usage in _REGISTERED if network.subnet_of(block)]
    if specific:
        # 优先更具体的用途，不能因宽泛的 IETF 分配段覆盖 Teredo 等细分地址。
        _, selected = max(specific, key=lambda item: item[0])
        return selected
    if any(network.overlaps(block) for block, _ in _REGISTERED):
        return AddressUsage('混合地址范围',
            '该网络覆盖多个不同用途的 IPv6 地址范围，其中包含受限或特殊用途地址；不能将全部计算出的子网视为适合普通公网部署。请进一步缩小前缀分别判断。',
            'IANA IPv6 Special-Purpose Address Registry', '注意')
    # 00fd:xxxx 不是 fd00:xxxx。单独提醒易混淆的书写形式，避免误称为 ULA。
    if network.network_address.packed[0] == 0 and (int(network.network_address) >> 112) == 0xfd and network.prefixlen >= 16:
        return AddressUsage('非 ULA 地址（00fd 前缀）',
            '该地址以 00fd 开头，而 ULA 的本地分配范围以 fd00 开头；例如 fd:1000:: 实际为 00fd:1000::，并非 fd00:1000::。如用于内部网络，请核实是否输入有误；部署前可核对 IANA。',
            'RFC 4291 / RFC 4193 / IANA', '注意')
    if network.subnet_of(_GLOBAL_UNICAST):
        return AddressUsage('全球单播地址范围',
            '可进行全球单播子网规划，但实际公网互联仍取决于合法地址分配、运营商路由与网络配置；计算结果不等于已获分配或公网可达。',
            'RFC 4291 / IANA', '信息')
    return AddressUsage('其他或保留 IPv6 地址范围',
        '未归入本工具内置的常见可部署地址类别；不应据此将其当作已分配的全球单播地址。部署前请核对 IANA 和适用标准。',
        'IANA', '注意')
