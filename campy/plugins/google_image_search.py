import traceback
import re
import simplejson
import httplib2

from plugin import CampyPlugin
import settings

class GoogleImage(CampyPlugin):
    def handle_message(self, campfire, room, message):
        body = message['body']
        if not body:
            return

        if not body.startswith(settings.CAMPFIRE_BOT_NAME):
            return

        m = re.match('%s: gis (?P<search_string>\w+)$' % settings.CAMPFIRE_BOT_NAME, body)
        if m:
            try:
                headers, content = httplib2.Http().request(
                    "https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=%s" %
                    m.group('search_string'))
                json = simplejson.loads(content)
                self.speak_image_url(room, json['responseData']['results'][0]['unescapedUrl'])
            except (KeyError,):
                print traceback.format_exc()


    def speak_image_url(self, room, url):
        room.speak(unicode(url))
