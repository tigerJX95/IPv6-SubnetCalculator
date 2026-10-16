"""子网导出磁盘占用的参考区间，并非容量保证。"""
from __future__ import annotations
from ipaddress import IPv6Network
from subnet_export import subnet_at

GIB = 1024 ** 3
MIB = 1024 ** 2


def estimate_export_range(network: IPv6Network, prefix: int, fmt: str, count: int, start_index: int = 0) -> tuple[int, int]:
    """在子网序号范围内分布采样，返回近似容量区间。"""
    if count <= 0 or fmt not in ('txt', 'xlsx'):
        raise ValueError('导出估算参数无效')
    sample_count = min(128, count)
    indices = {(i * (count - 1)) // max(sample_count - 1, 1) for i in range(sample_count)}
    lengths = [len(str(subnet_at(network, prefix, start_index + i)).encode('utf-8')) + 2 for i in indices]
    average = sum(lengths) / len(lengths)
    if fmt == 'txt':
        # Windows 导出采用 UTF-8 编码和换行符，同时预留余量以应对
        # 不同地址段压缩形式造成的长度变化。
        lower = int(count * average * 0.8)
        upper = int(count * average * 1.3) + 1024
    else:
        # XLSX 使用压缩的 XML 内容，压缩比例受数据影响。
        # 采用较宽的区间，避免将压缩后容量误认为精确值。
        raw = count * (average + 105)
        lower = int(raw * 0.2)
        upper = int(raw * 1.1) + 65536
    return max(0, lower), max(lower, upper)


def format_size_range(low: int, high: int) -> str:
    unit, divisor = ('GiB', GIB) if high >= GIB else ('MiB', MIB)
    return f'{low/divisor:,.2f}～{high/divisor:,.2f} {unit}'
