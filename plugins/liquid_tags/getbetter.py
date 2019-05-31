"""
Shameless rip of the original youtube liquid tag, suited for the getbetter blog
"""
import re
from .mdx_liquid_tags import LiquidTags

YT_SYNTAX = "{% youtube id [width height] %}"
YT_RE = re.compile(r'([\S]+)(\s+([\d%]+)\s([\d%]+))?')


@LiquidTags.register('gb_youtube')
def gb_youtube(preprocessor, tag, markup):
    width = 0
    height = 0
    youtube_id = None
    hw = ""

    match = YT_RE.search(markup)
    if match:
        groups = match.groups()
        youtube_id = groups[0]
        width = groups[2] or width
        height = groups[3] or height

    if youtube_id:
        if width or height:
            hw = """
            width="{width}" height="{height}"
            """.format(width=width, height=height)
        youtube_out = """
            <div class="videobox">
                <iframe {hw}
                    src='https://www.youtube.com/embed/{youtube_id}'
                    frameborder='0' webkitAllowFullScreen mozallowfullscreen
                    allowFullScreen>
                </iframe>
            </div>
        """.format(hw=hw, youtube_id=youtube_id).strip()
    else:
        raise ValueError("Error processing input, "
                         "expected syntax: {0}".format(YT_SYNTAX))

    return youtube_out


@LiquidTags.register('gb_mymaps')
def gb_mymaps(preprocessor, tag, markup):
    map_id = markup.strip()

    out = """
        <div class="videobox">
            <iframe src="https://www.google.com/maps/d/u/0/embed?mid={map_id}"></iframe>
        </div>
    """.format(map_id=map_id).strip()

    return out

# ---------------------------------------------------
# This import allows us to be a Pelican plugin
from liquid_tags import register  # noqa
