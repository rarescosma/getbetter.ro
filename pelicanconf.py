#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Rareș Cosma'
SITENAME = 'Getbetter'
SITESUBTITLE = (
   'A life journey of constant improvement in all areas of interests '
   'by Rareș Cosma'
)
SITEURL = ''
SITESRC = 'https://github.com/rarescosma/getbetter.ro'

PATH = 'content'

TIMEZONE = 'GMT'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Biography
BIO = "Senior software engineer / SRE<br/>Presently @ Klarna"
PROFILE_IMAGE = 'avatar.png'

# Social widget
SOCIAL = (('email', 'rares@getbetter.ro'),
          ('linkedin', 'https://www.linkedin.com/in/rarescosma'),
          ('github', 'https://github.com/rarescosma'))

DEFAULT_PAGINATION = 10

# URL settings
ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
PAGE_URL = 'pages/{slug}/'
PAGE_SAVE_AS = 'pages/{slug}/index.html'

# Theme
THEME = 'themes/pelican-hyde'

# Plugins
PLUGIN_PATHS = ['plugins']
PLUGINS = ['sitemap', 'summary', 'liquid_tags.getbetter', 'photos']

# Photos
PHOTO_LIBRARY = "~/src/getbetter.ro/var/galleries"
PHOTO_GALLERY = (1024, 768, 80)
PHOTO_ARTICLE = (760, 506, 80)
PHOTO_THUMB = (192, 144, 60)
PHOTO_RESIZE_JOBS = 5
PHOTO_WATERMARK = False

# Sitemap
SITEMAP = {
    'format': 'xml',
    'priorities': {
        'articles': 0.5,
        'indexes': 0.5,
        'pages': 0.75,
    },
    'changefreqs': {
        'articles': 'monthly',
        'indexes': 'daily',
        'pages': 'monthly',
    },
}

TEMPLATE_PAGES = {'wiki.html': 'wiki/index.html'}
