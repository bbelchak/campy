
class CampyPlugin(object):
    def handle_message(self, campfire, room, message):
        raise NotImplementedError

    def send_message(self, campfire, room, message):
        raise NotImplementedError