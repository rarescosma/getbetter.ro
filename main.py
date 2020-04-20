import logging
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__file__)

YOUTUBE_TPL = """
<div class="videobox">
    <iframe
        src="https://www.youtube.com/embed/{video_id}"
        frameborder="0"
        webkitAllowFullScreen="true"
        mozallowfullscreen="true"
        allowFullScreen="true">
    </iframe>
</div>
"""

MAPS_TPL = """
<div class="videobox">
    <iframe src="https://www.google.com/maps/d/u/0/embed?mid={map_id}"></iframe>
</div>
"""

IMAGE_TEMPLATE = """<a href="/{url}" title="{title}"><img src="/{thumb}"></a>"""

CONTENT_DIR = Path(__file__).parent.resolve() / "content"
PHOTOS_DIR = CONTENT_DIR / "photos"


def youtube(video_id: str) -> str:
    """ Renders a YouTube videobox.
    """
    return YOUTUBE_TPL.format(video_id=video_id.strip())


def mymaps(map_id: str) -> str:
    """ Renders an embedded map from google mymaps.
    """
    return MAPS_TPL.format(map_id=map_id.strip())


def photos(gallery_id: str) -> str:
    """ Renders a photo gallery.
    """
    photos_dir = PHOTOS_DIR / gallery_id

    if not photos_dir.exists() or not photos_dir.is_dir():
        LOG.warning(f"Gallery directory {photos_dir} is invalid.")
        return ""

    image_paths = sorted(
        [
            _.relative_to(CONTENT_DIR)
            for _ in photos_dir.glob("*.jpg")
            if _thumb_path(_).exists()
        ]
    )
    image_markup = "\n".join(
        IMAGE_TEMPLATE.format(url=_, title=_.name, thumb=_thumb_path(_))
        for _ in image_paths
    )
    return f'<div class="gallery">{image_markup}</div>'


def _thumb_path(img_path: Path) -> Path:
    """ image.jpg -> imaget.jpg
    """
    return Path(str(img_path).replace(img_path.suffix, f"t{img_path.suffix}"))


def define_env(env: Any):
    """ Hook for declaring variables, macros and filters.
    """
    env.macro(youtube, "yt")
    env.macro(mymaps)
    env.macro(photos)
