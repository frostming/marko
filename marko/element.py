from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable, Sequence
from typing import overload

from .helpers import camel_to_snake_case


class _SourceMap(Sequence[int]):
    """A compact mapping from parsed-text offsets to source offsets."""

    def __init__(self, runs: Iterable[tuple[int, int]]) -> None:
        self._runs: list[tuple[int, int, int]] = []
        self._run_starts: list[int] = []
        length = 0
        for source_start, run_length in runs:
            if run_length <= 0:
                continue
            self._run_starts.append(length)
            self._runs.append((length, length + run_length, source_start))
            length += run_length
        self._length = length

    @classmethod
    def from_positions(cls, positions: Iterable[int]) -> _SourceMap:
        runs: list[tuple[int, int]] = []
        run_start: int | None = None
        previous: int | None = None
        run_length = 0
        for position in positions:
            if previous is None or position != previous + 1:
                if run_start is not None:
                    runs.append((run_start, run_length))
                run_start = position
                run_length = 1
            else:
                run_length += 1
            previous = position
        if run_start is not None:
            runs.append((run_start, run_length))
        return cls(runs)

    def __len__(self) -> int:
        return self._length

    @overload
    def __getitem__(self, index: int) -> int: ...

    @overload
    def __getitem__(self, index: slice) -> _SourceMap: ...

    def __getitem__(self, index: int | slice) -> int | _SourceMap:
        if isinstance(index, slice):
            start, stop, step = index.indices(self._length)
            if step != 1:
                return self.from_positions(self[i] for i in range(start, stop, step))
            runs: list[tuple[int, int]] = []
            for body_start, body_end, source_start in self._runs:
                overlap_start = max(start, body_start)
                overlap_end = min(stop, body_end)
                if overlap_start < overlap_end:
                    runs.append(
                        (
                            source_start + overlap_start - body_start,
                            overlap_end - overlap_start,
                        )
                    )
            return type(self)(runs)

        if index < 0:
            index += self._length
        if index < 0 or index >= self._length:
            raise IndexError("source map index out of range")
        run_index = bisect_right(self._run_starts, index) - 1
        body_start, _, source_start = self._runs[run_index]
        return source_start + index - body_start


def _translate_span(
    positions: Sequence[int] | None, start: int, end: int
) -> tuple[int, int] | None:
    """Translate a span ``[start, end)`` in a parsed text to the corresponding
    span in the source text, or return None if not possible.
    """
    if positions is None or start < 0 or end <= start or end > len(positions):
        return None
    return (positions[start], positions[end - 1] + 1)


class Element:
    """This class holds attributes common to both the BlockElement and
    InlineElement classes.
    This class should not be subclassed by any other classes beside these.
    """

    override: bool

    #: The span of the source text that this element corresponds to,
    #: as a ``(start, end)`` tuple of indices into the normalized source text.
    #: ``None`` if the position is not available.
    #:
    #: .. note:: The positions are indices into the source text after
    #:     normalization (line terminators are normalized to ``\n``), so they
    #:     may differ from the original text when it contains ``\r\n`` or ``\r``.
    source_span: tuple[int, int] | None = None

    #: A list of ``(start, end)`` spans of the source text that contain
    #: only syntax characters (e.g. ``**`` of emphasis, brackets of a link),
    #: or ``None`` if not available. Content spans are covered by children.
    syntax_spans: list[tuple[int, int]] | None = None

    #: Internal: parallel mapping of the indices of :attr:`inline_body` to
    #: the positions in the source text. Only set on elements whose inline
    #: body is parsed, and cleared after the inline parsing is done.
    _inline_positions: Sequence[int] | None = None

    @property
    def start_pos(self) -> int | None:
        """The start index of the element in the source text, or None."""
        if self.source_span:
            return self.source_span[0]
        return None

    @property
    def end_pos(self) -> int | None:
        """The end index of the element in the source text, or None."""
        if self.source_span:
            return self.source_span[1]
        return None

    @classmethod
    def get_type(cls, snake_case: bool = False) -> str:
        """
        Return the Markdown element type that the object represents.

        :param snake_case: Return the element type name in snake case if True
        """

        # Prevent override of BlockElement and InlineElement
        if (
            cls.override
            and cls.__base__
            and cls.__base__ not in Element.__subclasses__()
        ):
            name = cls.__base__.__name__
        else:
            name = cls.__name__
        return camel_to_snake_case(name) if snake_case else name

    def __repr__(self) -> str:
        try:
            from objprint import objstr
        except ImportError:
            from pprint import pformat

            if hasattr(self, "children"):
                children = f" children={pformat(self.children)}"
            else:
                children = ""

            return f"<{self.__class__.__name__}{children}>"
        else:
            return objstr(self, honor_existing=False, include=["children"])
