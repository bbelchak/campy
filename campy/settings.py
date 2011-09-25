#
# Copyright (c) 2011 Ben Belchak <ben@belchak.com>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
CAMPFIRE_SUBDOMAIN = '' # Subdomain you use for campfire
CAMPFIRE_BOT_NAME = 'r' # Campfire name of the bot that matches the API_KEY
CAMPFIRE_API_KEY = '' # Campfire API key for your bot's user
CAMPFIRE_ROOMS = []  # Tuple of strings that match your room names

# Google Image search settings
GOOGLE_IMAGE_SAFE = "active" # active, moderate, off

# Pivotal Tracker settings
PT_USERNAME = '' # Pivotal Tracker username
PT_PASSWORD = '' # Pivotal Tracker password
PT_ROOM_TO_PROJECT_MAP = {} # dict that maps CAMPFIRE_ROOMS to their corresponding project ids

# Tuple of full package paths to the plugins you'd like to register.
REGISTERED_PLUGINS = []

SAY_GOODBYE = False
LEAVE_ON_EXIT = False
RSS_REFRESH_TIME = 10 # seconds between rss feed refreshes

ZERO_CATER_URL = "http://www.zerocater.com/seatme" #default URL

try:
    import simplejson as json
except ImportError:
    import json


import os
import sys

# Load settings from the local_settings.py file
try:
    from local_settings import *
except ImportError:
    pass

def load_from_file(filename):
    print "Loading settings from %s" % filename
    if os.path.exists(filename):
        with open(filename) as f:
            attrs = json.loads(f.read())
            for k,v in attrs.iteritems():
                setattr(sys.modules[__name__], k, v)

# Load settings from a list of json config files:
import_list = [
    '/etc/campyrc',
    '%s/.campyrc' % os.environ['HOME']
]

for filename in import_list:
    load_from_file(filename)
