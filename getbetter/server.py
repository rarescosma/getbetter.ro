#!/usr/bin/env python3

import logging
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Pattern

from flask import Flask, redirect, request, send_from_directory
from mkdocs.config import load_config

WWW_DIR: str = os.getenv("WWW_DIR", "../www")
LOC_PATTERN: Pattern = re.compile("<loc>([^<]+)</loc>")
SIMILARITY_THRESHOLD: float = 0.65
SIMILARITY_RATIO_THRESHOLD: float = 1.4
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s"
)

app = Flask(__name__, static_url_path=f"/{WWW_DIR}")


@lru_cache(maxsize=1)
def _sitemap_paths(sitemap_file: Path = Path(WWW_DIR) / "sitemap.xml"):
    cfg = load_config()
    return [
        _.replace(cfg["site_url"], "").strip("/")
        for _ in LOC_PATTERN.findall(sitemap_file.read_text())
    ]


def _normalize(x: str) -> str:
    return x.lower().replace("-", "").replace("/", "").strip("/")


@lru_cache(maxsize=512)
def _similar(a: str, b: str) -> float:
    return SequenceMatcher(
        None, _normalize(a), _normalize(b), autojunk=False
    ).ratio()


def _find_similar(req_path: str, known_paths: Iterable[str]) -> Optional[str]:
    sim_map = defaultdict(list)
    for known_path in known_paths:
        sim_map[_similar(req_path, known_path)].append(known_path)

    similar, max_similarity = None, max(sim_map.keys())
    if max_similarity >= SIMILARITY_THRESHOLD:
        similar = sim_map[max_similarity].pop()
        logging.info(
            f"Max similarity {max_similarity} >= "
            f"SIMILARITY_THRESHOLD {SIMILARITY_THRESHOLD}"
        )
    else:
        next_best = max(set(sim_map.keys()) - {max_similarity})
        ratio = max_similarity / next_best
        if ratio >= SIMILARITY_RATIO_THRESHOLD:
            logging.info(
                f"Ratio between best and next best guess {ratio} >= "
                f"SIMILARITY_RATIO_THRESHOLD {SIMILARITY_RATIO_THRESHOLD}"
            )
            similar = sim_map[max_similarity].pop()
    return similar


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def handle_static(path):
    if not path:
        logging.info("Serving root /")
        return send_from_directory(WWW_DIR, "index.html")
    if Path(path).suffix == "":
        logging.info(f"Serving a dir-like URL: {path}")
        if not path.endswith("/"):
            logging.warning("Adding ending /")
            return redirect(f"{path}/", code=302)
        return send_from_directory(WWW_DIR, path + "index.html")
    logging.info(f"Serving asset: {path}")
    return send_from_directory(WWW_DIR, path)


@app.errorhandler(404)
def handle_not_found(_):
    similar_url = _find_similar(request.path, known_paths=_sitemap_paths())
    if similar_url is not None:
        logging.info(f"Redirecting '{request.path}' to '/{similar_url}/'")
        return redirect(f"/{similar_url}/", code=301)
    return "Nope.", 404


if __name__ == "__main__":
    app.run()
