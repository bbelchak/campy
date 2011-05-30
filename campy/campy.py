from pinder.campfire import Campfire
import settings
from twisted.internet import reactor

class Campy(object):
    def __init__(self):
        self.client = Campfire(settings.CAMPFIRE_SUBDOMAIN,
                                settings.CAMPFIRE_API_KEY, ssl=True)

        self.rooms = []
        self.since_message_id = None

        for room in settings.CAMPFIRE_ROOMS:
            room = self.client.find_room_by_name(room)
            if room:
                self.rooms.append(room)
                room.join()


    def listen(self):
        def callback(message):
            for plugin in settings.REGISTERED_PLUGINS:
                plugin.handle_message(self.client, self.client.room(message['room_id']),
                                      message)

        def errback(message):
            print message

        for room in self.rooms:
            room.listen(callback, errback)


if __name__ == "__main__":
    running = True
    campy = Campy()
    campy.listen()
    reactor.run()
