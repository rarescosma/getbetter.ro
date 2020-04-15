#!/usr/bin/env python3

import re
from collections import defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Pattern

from flask import Flask, redirect, request, send_from_directory
from mkdocs.config import load_config

SITE_DIR: str = "site"
LOC_PATTERN: Pattern = re.compile("<loc>([^<]+)</loc>")
SIMILARITY_THRESHOLD: float = 0.65
SIMILARITY_RATIO_THRESHOLD: float = 1.4

app = Flask(__name__, static_url_path=f"/{SITE_DIR}")


@lru_cache(maxsize=1)
def _sitemap_paths(sitemap_file: Path = Path(SITE_DIR) / "sitemap.xml"):
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

    max_similarity = max(sim_map.keys())
    if max_similarity >= SIMILARITY_THRESHOLD:
        return sim_map[max_similarity].pop()
    else:
        next_best = max(set(sim_map.keys()) - {max_similarity})
        if max_similarity / next_best >= SIMILARITY_RATIO_THRESHOLD:
            return sim_map[max_similarity].pop()
    return None


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def handle_static(path):
    if not path:
        return send_from_directory(SITE_DIR, "index.html")
    if Path(path).suffix == "":
        if not path.endswith("/"):
            return redirect(f"{path}/", code=302)
        return send_from_directory(SITE_DIR, path + "/index.html")
    return send_from_directory(SITE_DIR, path)


@app.errorhandler(404)
def handle_not_found(_):
    similar_url = _find_similar(request.path, known_paths=_sitemap_paths())
    if similar_url is not None:
        return redirect(f"/{similar_url}/", code=301)
    return "Nope.", 404


if __name__ == "__main__":
    app.run()
