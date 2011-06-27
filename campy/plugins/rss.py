import httplib2
import urllib
import feedparser
from twisted.internet import reactor

from plugins import CampyPlugin
from campy import settings

class RSSReader(CampyPlugin):
    def __init__(self, *args):

        self._known_entries = set()
        self._known_rooms = {}

        self.get_feed(True)

    def get_feed(self, first_run):

        d = feedparser.parse(settings.RSS_URL)
        for entry in d.entries:
            if first_run or entry.guid in self._known_entries:
                self._known_entries.add(entry.guid)
                continue

            request_info = "%s %s\n\n%s" % (
                settings.RSS_LINK_PREFIX,
                entry.title,
                entry.link)

            for room in self._known_rooms.itervalues():
                room.speak(request_info)
                self._known_entries.add(entry.guid)

        reactor.callLater(settings.RSS_REFRESH_TIME, self.get_feed, False)

    def handle_message(self, campfire, room, message, speaker):
        if room.id not in self._known_rooms:
            self._known_rooms[room.id] = room
        
