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
import threading
import re
import sys
import signal
import time
from twisted.internet.defer import Deferred
import streaming
import Queue

import settings
from pinder.campfire import Campfire
from twisted.internet import reactor

class PluginThread(threading.Thread):
    def __init__(self, plugins, client):
        threading.Thread.__init__(self)
        self.plugins = plugins
        self.client = client
        self.kill_received = False

    def run(self):
        while not self.kill_received:
            try:
                message = message_pool.get_nowait()
            except Queue.Empty:
                time.sleep(1)
                continue

            print "%s: Handling %s" % (self.getName(), message)
            if message:
                for plugin in self.plugins:
                    try:
                        # TODO: Add a speaker cache so that we don't have to hit the API every time
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
                    except Exception:
                        pass
        print "%s shutting down!" % self.getName()


class CampyStreamConsumer(streaming.MessageReceiver):
    def __init__(self, plugins, cf_client):
        self.plugins = plugins
        self.client = cf_client
        super(CampyStreamConsumer, self).__init__()
        
    def connectionFailed(self, why):
        print "Couldn't connect:", why
        reactor.stop()

    def messageReceived(self, message):
        message_pool.put(message)


class Campy(object):
    def __init__(self):
        self.client = Campfire(settings.CAMPFIRE_SUBDOMAIN,
                                settings.CAMPFIRE_API_KEY)

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
        for room in self.rooms:
            username, password = room._connector.get_credentials()
            streaming.start(username, password, room.id,
                            CampyStreamConsumer(self.plugins, self.client))
        reactor.addSystemEventTrigger('before', 'shutdown', self.die)
        reactor.run()


    def die(self):
        for room in self.rooms:
            if settings.SAY_GOODBYE:
                room.speak("Goodbye!")
            if settings.LEAVE_ON_EXIT:
                room.leave()


if __name__ == "__main__":
    message_pool = Queue.Queue()
    campy = Campy()
    threads = []
    campy_started = False
    for x in xrange(settings.NUM_THREADS):
        thread = PluginThread(campy.plugins, campy.client)
        threads.append(thread)
        thread.daemon = True
        # I had to add this sleep statement here to get the
        # process to shut down. I'm open to better suggestions!
        time.sleep(.05)
        thread.start()

    while len(threads) > 0:
        try:
            threads = [t.join(1) for t in threads if t is not None and t.isAlive()]
            if not campy_started:
                campy_started = True
                print "Campy has started!"
                campy.listen()
                print "Shutting down..."
        except KeyboardInterrupt:
            print threads
            for t in threads:
                t.kill_received = True

