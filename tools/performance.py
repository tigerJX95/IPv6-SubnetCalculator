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

"""可重复的性能测量；时延和吞吐仅记录，不设置机器相关的速度门槛。"""
import gc
import statistics
import tempfile
import tracemalloc
from pathlib import Path
from threading import Event
from time import perf_counter
from ipaddress import IPv6Network
from core.ipv6_core import calculate, locate_subnet
from core.address_conversion import convert_address
from core.network_relations import analyze_networks
from core.subnet_list import analyze_subnet_list
from core.subnet_export import export_all, page_subnets, ExportCancelled


def timing(function, iterations):
    samples = []
    for _ in range(5):
        started = perf_counter()
        for _ in range(iterations):
            function()
        samples.append((perf_counter()-started)*1000/iterations)
    return dict(iterations_per_sample=iterations, samples=5,
                median_ms=round(statistics.median(samples), 6),
                maximum_sample_mean_ms=round(max(samples), 6))


def measure_performance():
    network = IPv6Network('::/0')
    last_page = (2**128+199)//200
    metrics = dict(
        calculation=timing(lambda: calculate('::/0', '128', preview_limit=0), 1000),
        maximum_space_last_page=timing(lambda: page_subnets(network, 128, last_page, 200), 100),
        maximum_space_location=timing(lambda: locate_subnet(network, 128, 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'), 1000),
        address_conversion=timing(lambda: convert_address('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'), 1000),
        network_relation=timing(lambda: analyze_networks('::/0', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'), 1000),
        memory_scope='Python allocations tracked by tracemalloc; excludes native Qt allocations and process RSS',
        speed_threshold='Informational measurements; no hardware-dependent pass/fail limit')
    unique_list = '\n'.join(f'2026:1015:abcd:{index:x}::/64' for index in range(5000))
    dense_list = '\n'.join(['::/0']*5000)
    metrics['subnet_list_5000_unique'] = timing(lambda: analyze_subnet_list(unique_list), 1)
    metrics['subnet_list_5000_duplicates'] = timing(lambda: analyze_subnet_list(dense_list), 1)
    with tempfile.TemporaryDirectory(prefix='IPv6性能-') as directory:
        exports, memory = {}, {}
        for fmt, count in (('txt', 100000), ('xlsx', 20000)):
            path = Path(directory)/('子网.'+fmt)
            started = perf_counter()
            export_all(path, network, 128, fmt, end=count)
            elapsed = perf_counter()-started
            exports[fmt] = dict(rows=count, seconds=round(elapsed, 5),
                rows_per_second=round(count/max(elapsed, 1e-9)), bytes=path.stat().st_size)
            peaks = []
            for sample_count in (1000, 10000):
                gc.collect()
                tracemalloc.start()
                try:
                    export_all(path, network, 128, fmt, end=sample_count)
                    _, peak = tracemalloc.get_traced_memory()
                finally:
                    tracemalloc.stop()
                peaks.append(peak)
            memory[fmt] = dict(sample_rows=[1000, 10000], peak_python_bytes=peaks,
                               growth_bytes=peaks[1]-peaks[0])
            # A coarse regression guard detects accidental list materialization.
            if peaks[1] > 32*1024**2 or peaks[1]-peaks[0] > 4*1024**2:
                raise AssertionError(fmt+' export memory guard failed')
        stop = Event()
        original = Path(directory)/'取消.txt'
        original.write_bytes(b'original')
        started = perf_counter()
        try:
            export_all(original, network, 128, 'txt', end=2**128, stop=stop,
                       progress=lambda done, total: stop.set())
        except ExportCancelled:
            pass
        else:
            raise AssertionError('export cancellation was not observed')
        if original.read_bytes() != b'original' or list(Path(directory).glob('.ipv6-export-*')):
            raise AssertionError('cancel did not preserve original or clean up')
        metrics.update(exports=exports, export_memory=memory,
                       cancellation=dict(seconds=round(perf_counter()-started, 5),
                                         original_preserved=True, temporary_files_removed=True))
    return metrics
