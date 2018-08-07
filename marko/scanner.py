# -*- coding: utf-8 -*-
# Copyright (c) 2018 by Frost Ming.
# Modification under MIT license.

# Copyright (c) 2017 by Esteban Castro Borsani.
#
# Original code by Armin Ronacher.
# Modifications under MIT licence.

# Copyright (c) 2015 by Armin Ronacher.
#
# Some rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
#     * The names of the contributors may not be used to endorse or
#       promote products derived from this software without specific
#       prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
from sre_parse import Pattern, SubPattern, parse
from sre_compile import compile as sre_compile
from sre_constants import BRANCH, SUBPATTERN

from ._compat import PY2


__all__ = ['Scanner']


class _ScanMatch:

    def __init__(self, match, rule, start, end):
        self._match = match
        self._start = start
        self._end = end
        self._rule = rule

    def __repr__(self):
        return '%s<%s>' % (
            self.__class__.__name__,
            repr(self._match.groups()))

    def __getattr__(self, name):
        return getattr(self._match, name)

    def __group_proc(self, method, group):
        if group == 0:
            return method()

        if isinstance(group, str):
            return method('%s_%s' % (self._rule, group))

        real_group = self._start + group

        if real_group > self._end:
            raise IndexError('no such group')

        return method(real_group)

    def group(self, *groups):
        if len(groups) in (0, 1):
            return self.__group_proc(
                self._match.group,
                groups and groups[0] or 0)

        return tuple(
            self.__group_proc(self._match.group, group)
            for group in groups)

    def groupdict(self, default=None):
        prefix = '%s_' % self._rule
        len_prefix = len(prefix)
        return {
            key[len_prefix:]: value
            for key, value in self._match.groupdict(default).items()
            if key.startswith(prefix)}

    def span(self, group=0):
        return self.__group_proc(self._match.span, group)

    def groups(self):
        return self._match.groups()[self._start:self._end]

    def start(self, group=0):
        return self.__group_proc(self._match.start, group)

    def end(self, group=0):
        return self.__group_proc(self._match.end, group)

    def expand(self, template):
        raise RuntimeError('Unsupported on scan matches')


class Scanner:
    """
    This is similar to re.Scanner.\
    It creates a compounded regex\
    pattern out of many patterns.
    Except it ``search`` to find matches,\
    this is so it's possible to take\
    the unmatched parts of the string.
    It prefixes groups with ``name_of_rule_``\
    to avoid group names clashes. GroupDicts\
    can still be retrieve as normal without the prefix.
    It adjusts group indexes so they work as expected,\
    instead of as per the compounded regex.
    It has a few caveats: group-index back-references\
    are relative to the compounded regex,\
    so for all practical purposes they won't work.
    """

    def __init__(self, rules, flags=0):
        pattern = Pattern()
        pattern.flags = flags

        for _ in range(len(rules)):
            pattern.opengroup()

        _og = pattern.opengroup
        pattern.opengroup = lambda n: _og(n and '%s_%s' % (name, n) or n)

        self.rules = []
        subpatterns = []
        subflags = set()

        def replace_num(match):
            return str(int(match.group()) + last_group)

        for group, (name, regex) in enumerate(rules, 1):
            # pattern.opengroup()
            last_group = pattern.groups - 1
            regex = re.sub(r'\?P=(.+?)', '?P=%s_\1' % name, regex)
            regex = re.sub(r'(?:(?<=\\)\d+|(?<=\?\()\d+(?=\)))', replace_num, regex)
            subpattern = parse(regex, flags, pattern)
            if PY2:
                bundle = (group, subpattern)
            else:
                bundle = (group, 0, 0, subpattern)
            subpatterns.append(SubPattern(pattern, [
                (SUBPATTERN, bundle),
            ]))
            pattern.closegroup(group, subpatterns[-1])
            subflags.add(subpattern.pattern.flags)
            self.rules.append((name, last_group, pattern.groups - 1))

        self._scanner = sre_compile(SubPattern(
            pattern, [(BRANCH, (None, subpatterns))])).scanner

        if len(subflags) > 1:
            raise ValueError(
                'In-pattern flags are not supported')

    def _scan(self, string):
        sc = self._scanner(string)

        for match in iter(sc.search, None):
            rule, start, end = self.rules[match.lastindex - 1]
            yield rule, _ScanMatch(match, rule, start, end)

    def scan_with_holes(self, string):
        pos = 0

        for rule, match in self._scan(string):
            hole = string[pos:match.start()]

            if hole:
                yield None, hole

            yield rule, match
            pos = match.end()

        hole = string[pos:]

        if hole:
            yield 'RawText', hole
