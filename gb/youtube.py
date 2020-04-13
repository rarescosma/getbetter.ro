import re
from markdown import util, Extension
from markdown.inlinepatterns import Pattern


HTML_TEMPLATE = """
<div class="videobox">
    <iframe
        src='https://www.youtube.com/embed/{video_id}'
        frameborder='0'
        webkitAllowFullScreen='true'
        mozallowfullscreen='true'
        allowFullScreen='true'>
    </iframe>
</div>
"""


class YoutubeExtension(Extension):
    def add_inline(self, md, name, pattern_class):
        pattern = r'\[(?P<prefix>%s#)(?P<video_id>[^"&?/\s]{11})\]' % name
        objPattern = pattern_class(pattern, self.config)
        objPattern.md = md
        objPattern.ext = self
        md.inlinePatterns.add(name, objPattern, "<reference")

    def extendMarkdown(self, md, md_globals):
        self.add_inline(md, "yt", YoutubePattern)


class YoutubePattern(Pattern):
    def __init__(self, pattern, config):
        Pattern.__init__(self, pattern)
        self.config = config

    def getCompiledRegExp(self):
        return re.compile(
            "^(.*?)%s(.*)$" % self.pattern,
            re.DOTALL | re.UNICODE | re.IGNORECASE,
        )

    def handleMatch(self, match):
        if match:
            video_id = match.group("video_id")
            return util.etree.fromstring(
                HTML_TEMPLATE.format(video_id=video_id)
            )
        else:
            return ""


def makeExtension(*args, **kwargs):
    return YoutubeExtension(*args, **kwargs)
