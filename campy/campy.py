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
from pinder.exc import HTTPNotFoundException
import re

import settings
from pinder.campfire import Campfire
from twisted.internet import reactor

class Campy(object):
    def __init__(self):
        self.client = Campfire(settings.CAMPFIRE_SUBDOMAIN,
                                settings.CAMPFIRE_API_KEY, ssl=True)

        self.rooms = []
        self.since_message_id = None

        self.plugins = []
        for plugin in settings.REGISTERED_PLUGINS:
            path = plugin.split('.')
            klass = path.pop()
            plugin_obj = getattr(__import__('.'.join(path), globals(), locals(), [klass], -1), klass)
            self.plugins.append(plugin_obj())

        for room in settings.CAMPFIRE_ROOMS:
            print "Joining %s" % room
            room = self.client.find_room_by_name(room)
            if room:
                self.rooms.append(room)
                room.join()


    def listen(self):
        def callback(message):
            for plugin in self.plugins:
                try:
                    speaker = self.client.user(message['user_id'])
                    if not message['body']:
                        return

                    if re.match('%s: help' % settings.CAMPFIRE_BOT_NAME, message['body']):
                        try:
                            plugin.send_help(self.client, self.client.room(message['room_id']),
                                        message, speaker)
                        except NotImplementedError:
                            pass
                    else:
                        plugin.handle_message(self.client, self.client.room(message['room_id']),
                                          message, speaker)
                except HTTPNotFoundException:
                    pass

        def errback(message):
            print message

            
        for room in self.rooms:
            room.listen(callback, errback)

    def die(self):
        for room in self.rooms:
            if settings.SAY_GOODBYE:
                room.speak("Goodbye!")
            if settings.LEAVE_ON_EXIT:
                room.leave()


if __name__ == "__main__":
    campy = Campy()
    campy.listen()
    reactor.run()
    campy.die()
