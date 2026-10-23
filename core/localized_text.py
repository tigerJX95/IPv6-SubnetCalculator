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

"""无 Qt 依赖的展示文本：保留原文、参数与组合，计算及序列化始终使用原文。"""
from functools import lru_cache
from string import Formatter


@lru_cache(maxsize=2048)
def format_signature(template):
    """Preserve fields, conversions and nested format specs while permitting reordering."""
    fields = []
    def collect(value, depth=0):
        if depth > 10:
            raise ValueError('Format specification nesting is too deep')
        for _, field, spec, conversion in Formatter().parse(value):
            if field is not None:
                fields.append((field, spec, conversion or ''))
                if spec:
                    collect(spec, depth+1)
    collect(template)
    return tuple(sorted(fields))


def exception_text(exc):
    """Keep a structured localized message instead of flattening exception arguments."""
    if len(exc.args) == 1 and isinstance(exc.args[0], Text):
        return exc.args[0]
    return str(exc)


class Text(str):
    def __new__(cls, source, args=(), *, parts=None, replacement=None):
        canonical = source.format(*args) if args else source
        if parts is not None:
            canonical=''.join(str(x) for x in parts)
        obj=super().__new__(cls,canonical)
        obj.source=source
        obj.arguments=tuple(args)
        obj.parts=tuple(parts) if parts is not None else None
        obj.replacement=replacement
        obj.section=None
        return obj

    def __str__(self):
        return self

    def __add__(self, other):
        if not isinstance(other,str):return NotImplemented
        return Text('',parts=(self,other))

    def __radd__(self, other):
        if not isinstance(other,str):return NotImplemented
        return Text('',parts=(other,self))

    def replace(self, old, new, count=-1):
        obj=Text(str.replace(self,old,new,count))
        obj.replacement=(self,old,new,count)
        return obj

    def line(self,index=0):
        obj=Text(str.split(self,"\n")[index])
        obj.section=(self,index)
        return obj

    def render(self, translate):
        if self.section is not None:
            value,index=self.section
            lines=render(value,translate).split("\n")
            return lines[index] if -len(lines)<=index<len(lines) else str(value).split("\n")[index]
        if self.replacement is not None:
            value,old,new,count=self.replacement
            return render(value,translate).replace(old,new,count)
        if self.parts is not None:
            return ''.join(render(p,translate) for p in self.parts)
        source=translate(self.source)
        try:
            if (not isinstance(source, str) or self.source.strip() and not source.strip()
                    or format_signature(source) != format_signature(self.source)):
                source=self.source
        except (ValueError, TypeError):
            source=self.source
        values=[]
        for argument in self.arguments:
            if isinstance(argument,BaseException):argument=exception_text(argument)
            values.append(render(argument,translate) if isinstance(argument,Text) else argument)
        try:
            return source.format(*values) if self.arguments else source
        except (ValueError, KeyError, IndexError, AttributeError, TypeError):
            if source == self.source:
                raise
            return self.source.format(*values) if self.arguments else self.source


def text(source,*args):
    return Text(source,args)


def join_text(separator, values):
    parts=[]
    for value in values:
        if not isinstance(value,str):raise TypeError('join_text requires strings')
        if parts:parts.append(separator)
        parts.append(value)
    return Text('',parts=parts)


def render(value,translate):
    return value.render(translate) if isinstance(value,Text) else str(value)
