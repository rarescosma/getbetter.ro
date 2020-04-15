import json
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
GALLERY_DIR = CONTENT_DIR / "galleries"


def youtube(video_id: str) -> str:
    return YOUTUBE_TPL.format(video_id=video_id.strip())


def gb_mymaps(map_id: str) -> str:
    return MAPS_TPL.format(map_id=map_id.strip())


def gb_gallery(gallery_id: str) -> str:
    gallery_dir = GALLERY_DIR / gallery_id

    if not gallery_dir.exists() or not gallery_dir.is_dir():
        LOG.warning(f"Gallery directory {gallery_dir} is invalid.")
        return ""

    image_paths = sorted(
        [
            _.relative_to(CONTENT_DIR)
            for _ in gallery_dir.glob("*.jpg")
            if _thumb_path(_).exists()
        ]
    )
    image_markup = "\n".join(
        IMAGE_TEMPLATE.format(url=_, title=_.name, thumb=_thumb_path(_))
        for _ in image_paths
    )
    return f'<div class="gallery">{image_markup}</div>'


def _thumb_path(img_path: Path) -> Path:
    return Path(str(img_path).replace(img_path.suffix, f"t{img_path.suffix}"))


def define_env(env: Any):
    """
    This is the hook for declaring variables, macros and filters (new form)
    """
    env.macro(youtube, "yt")
    env.macro(gb_mymaps, "gb_mymaps")
    env.macro(gb_gallery)
