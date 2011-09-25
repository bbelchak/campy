#
# Copyright (c) 2011 Zac Bowling <zac@zacbowling.com>
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


import urllib2, re
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup
import sys, traceback, textwrap

if __name__ == "__main__":
    sys.path.append("../")
    sys.path.append("./")
    
from plugins import CampyPlugin
from campy import settings


class ZeroCater(CampyPlugin):
    def __init__(self, *args):
        pass
    
    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        if not body:
            return

        if not body.startswith(settings.CAMPFIRE_BOT_NAME):
            return
        
        m = re.match('%s: (?P<mode>zc|zcd)$' % settings.CAMPFIRE_BOT_NAME, body)
        if m:
            try:
                detail = True
                if m.group('mode') == "zc":
                    detail = False
                room.paste(pull_zc(settings.ZERO_CATER_URL,detail))
            except Exception, e:
                speak_text = u"%s: error parsing ZeroCater output." % speaker['user']['name']
                room.speak(speak_text)
                room.paste(traceback.format_exc())
                
                

    def send_help(self, campfire, room, message, speaker):
        help_text = """%s: Here is your help for the ZeroCater plugin:
        zc - display the zerocater menu
        zcd - display the zerocater menu with item details and descriptions
        """ % speaker['user']['name']
        room.paste(help_text)
        
#thar be horrible looking python below!
def pull_zc(pullurl,show_details=True):
    page = urllib2.urlopen(pullurl)
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
            paste_text.append(u"  %s @ %s - %s %s %s" % (meal_date_text.strip(), timetag_text.strip(), food_text.strip(), restaurant_text.strip(), people_text.strip()))
            
            if show_details:
                order_items = meal_name.find("ul",{"class":"order-summary"})
            
                for order_item in order_items.findAll("li"):
                    order_item_text = str(order_item.contents[0]).decode("UTF-8")
                    paste_text.append(u"    * %s" % order_item_text.strip())
                    #paste_text.append(repr(order_item.contents).decode("UTF-8"))
                    #print repr(order_item)
                    order_item_description = order_item.find("div",{"class":"item-description"})
                    if (order_item_description is not None):
                        order_item_description = str(BeautifulStoneSoup(order_item_description.string,convertEntities=BeautifulStoneSoup.HTML_ENTITIES)).decode("UTF-8")
                        order_item_description = textwrap.TextWrapper(initial_indent="      ",subsequent_indent="      ", width=65).fill(order_item_description)
                        paste_text.append(order_item_description)
                if (order_items is not None):
                    paste_text.append("") #add a new line after the item list for asthetics
            
            
            
    paste_text.append(u"\nMenu and voting: %s" % pullurl)
    return ('\n'.join(paste_text))
    
if __name__ == "__main__":
    print pull_zc("http://www.zerocater.com/seatme",show_details=True)