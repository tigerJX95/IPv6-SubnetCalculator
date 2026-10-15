"""Indicative disk usage ranges for subnet exports (not guarantees)."""
from __future__ import annotations
from ipaddress import IPv6Network
from subnet_export import subnet_at

GIB = 1024 ** 3
MIB = 1024 ** 2


def estimate_export_range(network: IPv6Network, prefix: int, fmt: str, count: int) -> tuple[int, int]:
    """Sample across the subnet index space; return an approximate size interval."""
    if count <= 0 or fmt not in ('txt', 'xlsx'):
        raise ValueError('导出估算参数无效')
    sample_count = min(128, count)
    indices = {(i * (count - 1)) // max(sample_count - 1, 1) for i in range(sample_count)}
    lengths = [len(str(subnet_at(network, prefix, i)).encode('utf-8')) + 2 for i in indices]
    average = sum(lengths) / len(lengths)
    if fmt == 'txt':
        # Windows output is written as UTF-8 with LF, but margin allows for
        # variation in address compression across the address space.
        lower = int(count * average * 0.8)
        upper = int(count * average * 1.3) + 1024
    else:
        # XLSX content is compressed XML; compression ratio depends on data.
        # Broad bounds deliberately avoid claiming compressed size is exact.
        raw = count * (average + 105)
        lower = int(raw * 0.2)
        upper = int(raw * 1.1) + 65536
    return max(0, lower), max(lower, upper)


def format_size_range(low: int, high: int) -> str:
    unit, divisor = ('GiB', GIB) if high >= GIB else ('MiB', MIB)
    return f'{low/divisor:,.2f}～{high/divisor:,.2f} {unit}'
