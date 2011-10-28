#
# Copyright (c) 2011 Mark Wong <mark.wong@myemma.com>
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

import traceback
import re

from plugins import CampyPlugin
from campy import settings

from httplib import HTTPConnection, HTTPSConnection
from urllib import quote

try:
    import json
except ImportError:
    import simplejson as json


class Twitter(CampyPlugin):

    def send_help(self, campfire, room, message, speaker):
        help_text = '%s: twitter handle' % speaker['user']['name']
        room.paste(help_text)

    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        if not body:
            return

        if not body.startswith(settings.CAMPFIRE_BOT_NAME):
            return

        m = re.match('%s: twitter (?P<handle>.*)$' % \
                settings.CAMPFIRE_BOT_NAME, body)
        if m:
            try:
                screen_name = m.group('handle')

                conn = HTTPConnection('api.twitter.com')
                conn.request('GET', '/1/users/show.json?screen_name=%s' %
                                    quote(screen_name))
                resp = conn.getresponse()
                r = resp.read()
                conn.close()
                request = json.loads(r)
                if 'status' in request:
                    room.fetch_tweet('http://twitter.com/#!/%s/status/%s' % \
                            (screen_name, request['status']['id']))
                else:
                    room.speak('I cannot find anything for @%s.' % screen_name)
            except (KeyError,):
                room.speak(traceback.format_exc())
