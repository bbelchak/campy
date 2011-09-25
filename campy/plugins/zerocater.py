import urllib2, re
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup

from plugins import CampyPlugin
from campy import settings
import sys, traceback

class ZeroCater(CampyPlugin):
    def __init__(self, *args):
        pass
    
    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        if not body:
            return

        if not body.startswith(settings.CAMPFIRE_BOT_NAME):
            return
        
        m = re.match('%s: zc$' % settings.CAMPFIRE_BOT_NAME, body)
        if m:
            try:
                #thar be horrible looking python below!
                page = urllib2.urlopen(settings.ZERO_CATER_URL)
                soup = BeautifulSoup(page)
                paste_text = []
                for week_box in soup.html.body.findAll("div",{"class":"week_box"}):
                    paste_text.append(str(week_box.findPrevious("h2").renderContents()))
                    meal_dates = week_box.findAll("div",{"class":"meal_date"})
                    for meal_date in meal_dates: 
                        meal_date_text = meal_date.getText().decode("UTF-8")
                        meal_name = meal_date.findNext("div",{"class":"meal_name collapser-container"})
                        time_name_size = meal_name.find("div",{"class":"grid_6 alpha"}).find("span")
                        timetag = time_name_size.find("span",{"class":"collapser-controller"})
                        timetag_text = str(timetag.find("span",{"class":"collapser-state "}).findNextSibling(text = True)).decode("UTF-8")
                        food = timetag.findNextSibling(text = True)
                        food_text = str(BeautifulStoneSoup(food.string,convertEntities=BeautifulStoneSoup.HTML_ENTITIES)).decode("UTF-8")
                        restaurant = food.findNextSibling("a")
                        restaurant_text = str(BeautifulStoneSoup(restaurant.string,convertEntities=BeautifulStoneSoup.HTML_ENTITIES)).decode("UTF-8").strip()
                        people = restaurant.findNextSibling(text = True)
                        people_text = str(BeautifulStoneSoup(people.string,convertEntities=BeautifulStoneSoup.HTML_ENTITIES)).decode("UTF-8")
                        paste_text.append(u"\t %s @ %s - %s %s %s" % (meal_date_text.strip(), timetag_text.strip(), food_text.strip(), restaurant_text.strip(), people_text.strip()))
                paste_text.append(u"\nMenu and voting: %s" % settings.ZERO_CATER_URL)
                text = ('\n'.join(paste_text))
                room.paste(text)
            except Exception, e:
                speak_text = u"%s: error parsing ZeroCater output." % speaker['user']['name']
                room.speak(speak_text)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                room.paste(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                
                

    def send_help(self, campfire, room, message, speaker):
        help_text = """%s: Here is your help for the ZeroCater plugin:
        zc - display the zerocater menu
        """ % speaker['user']['name']
        room.paste(help_text)