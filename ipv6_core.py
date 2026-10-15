"""Pure IPv6 subnet calculations. No GUI dependencies."""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv6Address, IPv6Network, AddressValueError, NetmaskValueError
import re

MAX_PREVIEW = 100


class InputError(ValueError):
    """User-facing validation error."""


@dataclass(frozen=True)
class SubnetResult:
    network: IPv6Network
    target_prefix: int
    normalized: bool
    subnet_count: int
    addresses_per_subnet: int
    preview: tuple[IPv6Network, ...]

    @property
    def start_address(self) -> IPv6Address:
        return self.network.network_address

    @property
    def end_address(self) -> IPv6Address:
        return IPv6Address(int(self.network.network_address) + self.network.num_addresses - 1)


def calculate(network_text: str, target_text: str, *, preview_limit: int = MAX_PREVIEW) -> SubnetResult:
    """Validate CIDR then compute subnet details; never enumerate entire IPv6 space."""
    source = network_text.strip()
    target = target_text.strip()
    if not source:
        raise InputError("请输入 IPv6 网络地址及前缀，例如 2001:db8::/32。")
    if source.count("/") != 1:
        raise InputError("网络地址必须包含一个 CIDR 前缀，例如 2001:db8::/32。")
    addr, prefix = (part.strip() for part in source.split("/"))
    if not addr or not prefix or not re.fullmatch(r"[0-9]{1,3}", prefix):
        raise InputError("原始网络前缀必须为 0～128 的整数。")
    original_prefix = int(prefix)
    if not 0 <= original_prefix <= 128:
        raise InputError("原始网络前缀必须为 0～128 的整数。")
    if not target or not re.fullmatch(r"[0-9]{1,3}", target):
        raise InputError("目标子网前缀必须为 0～128 的整数（不需要输入 /）。")
    target_prefix = int(target)
    if not 0 <= target_prefix <= 128:
        raise InputError("目标子网前缀必须为 0～128 的整数。")
    if target_prefix < original_prefix:
        raise InputError("目标子网前缀不能小于原始网络前缀。")
    try:
        ip = IPv6Address(addr)
        net = IPv6Network((ip, original_prefix), strict=False)
    except (AddressValueError, NetmaskValueError, ValueError) as exc:
        raise InputError("IPv6 地址格式不正确，请检查地址字符和冒号位置。") from exc
    if isinstance(preview_limit, bool) or not isinstance(preview_limit, int) or not 0 <= preview_limit <= MAX_PREVIEW:
        raise ValueError(f"preview_limit must be an integer from 0 to {MAX_PREVIEW}")
    count = 1 << (target_prefix - original_prefix)
    step = 1 << (128 - target_prefix)
    first = int(net.network_address)
    preview = tuple(IPv6Network((IPv6Address(first + i * step), target_prefix)) for i in range(min(count, preview_limit)))
    return SubnetResult(net, target_prefix, ip != net.network_address, count, step, preview)
