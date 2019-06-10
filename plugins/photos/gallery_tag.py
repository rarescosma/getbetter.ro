"""Support for displaying separate galleries via the photos plugin.

Galleries are referenced by their index using a special tag:

For example:

{% gb_gallery 0 %}

Would display the first defined gallery for the article / page.
"""
import re
from functools import partial

from pelican.contents import Content

IMAGE_TEMPLATE = """<a href="/{url}" title="{title}"><img src="/{thumb}"></a>"""
GALLERY_TEMPLATE = """
<h3>{title}</h3>
<div class="gallery">
{gallery}
</div>
"""
GALLERY_RE = re.compile(r"^.*({% gb_gallery ([0-9]+) %}).*$")


def gallery_tag(content: Content):
    """Check each content line for the gallery tag and replace."""
    lines = content._content.split("\n")
    replacer = partial(_replacer, photo_gallery=content.photo_gallery)

    for i, line in enumerate(lines):
        lines[i] = GALLERY_RE.sub(replacer, line)

    content._content = "\n".join(lines)


def _replacer(match, photo_gallery=None):
    """Access the gallery data and return the rendered gallery."""
    gallery_index = int(match.group(2))
    if gallery_index >= len(photo_gallery):
        raise IndexError("gallery index out of range")

    g_title, g_photos = photo_gallery[gallery_index]
    rendered_photos = "\n".join(
        IMAGE_TEMPLATE.format(url=p[1], title=p[0], thumb=p[2])
        for p in g_photos
    )
    return GALLERY_TEMPLATE.format(title=g_title, gallery=rendered_photos)
