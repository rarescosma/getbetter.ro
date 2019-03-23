#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Rareș Cosma'
SITENAME = 'getbetter.ro'
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


# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),
         ('You can modify those links in your config file', '#'),)

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
PLUGINS = ['summary']
