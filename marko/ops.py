from typing import Iterable
from marko.elements.block import Document
from itertools import chain


def merge(documents: Iterable[Document]) -> Document:
    link_ref_defs: dict[str, tuple[str, str]] = {}

    for document in documents:
        for label, dest_and_title in document.link_ref_defs.items():
            if (label in link_ref_defs) and (link_ref_defs[label] != dest_and_title):
                raise ValueError(f"{label} occurs twice with different definition")
            link_ref_defs[label] = dest_and_title

    return Document(
        children=list(chain(*[document.children for document in documents])),
        link_ref_defs=link_ref_defs,
    )
