"""使用有限内存导出 IPv6 子网，并在成功后替换目标文件。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable, Iterator
import os
import tempfile
import zipfile
from xml.sax.saxutils import escape
from ipaddress import IPv6Address, IPv6Network

XLSX_MAX_RECORDS = 1_048_575  # 工作表总行数为 1,048,576，其中一行用于表头。
BATCH_SIZE = 1024

class ExportCancelled(Exception):
    pass

@dataclass(frozen=True)
class ExportReport:
    path: Path
    rows: int


def subnet_at(network: IPv6Network, target_prefix: int, index: int) -> IPv6Network:
    total = 1 << (target_prefix - network.prefixlen)
    if not 0 <= index < total:
        raise IndexError('子网序号超出范围')
    step = 1 << (128 - target_prefix)
    return IPv6Network((IPv6Address(int(network.network_address) + index * step), target_prefix))


def page_subnets(network: IPv6Network, target_prefix: int, page: int, page_size: int) -> list[tuple[int, str]]:
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or page_size not in (25, 50, 100, 200):
        raise ValueError('分页参数不正确')
    total = 1 << (target_prefix - network.prefixlen)
    begin = (page - 1) * page_size
    if begin >= total:
        raise ValueError('页码超出范围')
    return [(i + 1, str(subnet_at(network, target_prefix, i))) for i in range(begin, min(begin + page_size, total))]


def _iter_subnets(network: IPv6Network, target_prefix: int, total: int, stop: Event | None, start_index: int = 0) -> Iterator[str]:
    first = int(network.network_address)
    step = 1 << (128 - target_prefix)
    for i in range(total):
        if stop is not None and stop.is_set():
            raise ExportCancelled()
        yield str(IPv6Network((IPv6Address(first + (start_index + i) * step), target_prefix)))


def _write_txt(file, network, prefix, total, stop, progress, start_index=0):
    for index, address in enumerate(_iter_subnets(network, prefix, total, stop, start_index), 1):
        file.write((address + '\n').encode('utf-8'))
        if index % BATCH_SIZE == 0 or index == total:
            progress(index, total)


def _write_xlsx(file, network, prefix, total, stop, progress, start_index=0):
    if total > XLSX_MAX_RECORDS:
        raise ValueError('Excel 单工作表超出最大记录数量')
    with zipfile.ZipFile(file, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="IPv6子网" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        with z.open('xl/worksheets/sheet1.xml', 'w', force_zip64=True) as output:
            output.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><cols><col min="1" max="1" width="13" customWidth="1"/><col min="2" max="2" width="48" customWidth="1"/></cols><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>序号</t></is></c><c r="B1" t="inlineStr"><is><t>IPv6 子网</t></is></c></row>'.encode())
            for index, address in enumerate(_iter_subnets(network, prefix, total, stop, start_index), 1):
                row = index + 1
                output.write(f'<row r="{row}"><c r="A{row}"><v>{index + start_index}</v></c><c r="B{row}" t="inlineStr"><is><t>{escape(address)}</t></is></c></row>'.encode())
                if index % BATCH_SIZE == 0 or index == total:
                    progress(index, total)
            output.write(b'</sheetData></worksheet>')


def export_all(destination: str | Path, network: IPv6Network, target_prefix: int,
               format_type: str, *, stop: Event | None = None,
               progress: Callable[[int, int], None] | None = None,
               start: int = 1, end: int | None = None) -> ExportReport:
    """先写入临时文件，成功后再替换目标文件。

    调用前须在界面确认超大导出和覆盖现有文件。
    """
    full_total = 1 << (target_prefix - network.prefixlen)
    if end is None:
        end = full_total
    if (isinstance(start, bool) or isinstance(end, bool) or
        not isinstance(start, int) or not isinstance(end, int) or
        not 1 <= start <= end <= full_total):
        raise ValueError('导出范围无效，请输入有效的起始和结束序号。')
    total = end - start + 1
    if format_type not in ('txt', 'xlsx'):
        raise ValueError('不支持的导出格式')
    if format_type == 'xlsx' and total > XLSX_MAX_RECORDS:
        raise ValueError('超出 Excel 最大记录数，请使用 TXT 导出')
    path = Path(destination)
    if path.suffix.lower() != '.' + format_type:
        raise ValueError('文件扩展名与导出格式不一致')
    progress = progress or (lambda current, maximum: None)
    fd, temp = tempfile.mkstemp(prefix='.ipv6-export-', suffix='.'+format_type+'.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as out:
            if format_type == 'txt':
                _write_txt(out, network, target_prefix, total, stop, progress, start - 1)
            else:
                _write_xlsx(out, network, target_prefix, total, stop, progress, start - 1)
        if stop is not None and stop.is_set():
            raise ExportCancelled()
        os.replace(temp, path)
        return ExportReport(path, total)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
