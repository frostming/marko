from tests import SpecTestSuite
from marko import Markdown
from marko.ext.gfm import gfm


class TestCommonMark(SpecTestSuite):

    @classmethod
    def setup_class(cls):
        cls.markdown = Markdown()


TestCommonMark.load_spec('commonmark')

GFM_IGNORE = [
    'autolinks_015',
    'autolinks_018',
    'autolinks_019'
]


class TestGFM(SpecTestSuite):

    @classmethod
    def setup_class(cls):
        cls.markdown = gfm

    @classmethod
    def ignore_case(cls, n):
        return n in GFM_IGNORE


TestGFM.load_spec('gfm')
