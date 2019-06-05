import re
from pprint import pprint
from typing import cast

from pelican import ArticlesGenerator
from pelican.contents import Page, Content

IMAGE_TEMPLATE = """<a href="/{url}" title="{title}"><img src="/{thumb}"></a>"""
GALLERY_TEMPLATE = """
<h3>{title}</h3>
<div class="gallery">
{gallery}
</div>
"""
GALLERY_RE = re.compile(r'.+{% gb_gallery ([0-9]+) %}.+', re.DOTALL)


def my_stuff(content: Content):
    # page_gens = list(filter(lambda x: isinstance(x, ArticlesGenerator), generators))
    # if not page_gens:
    #     return

    # gen: ArticlesGenerator = page_gens[0]
    # for article in gen.articles:
    # print(content._content)
    if GALLERY_RE.match(content._content):
        print('HERER!!')
        content._content = GALLERY_RE.sub(_replacer, content._content)
    # if '{% gb_gallery' in content._content:
    #     content._content = 'bla'
    #     pprint(content.settings['SITEURL'])
    #     pprint(content.photo_gallery)
        # p._content = 'bla'
        # typed_p: Page = p
        # typed_p.content = 'bla'


def _replacer(match):
    print(match.group(1))
    return 'foo'
