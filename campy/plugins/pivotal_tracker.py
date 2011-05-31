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

import re
from campy import settings
from plugins import CampyPlugin

try:
    from pytracker import Tracker
    from pytracker import Story
    from pytracker import HostedTrackerAuth
except ImportError:
    raise ImportError("Requries pytracker module. http://code.google.com/p/pytracker/")

class PivotalTracker(CampyPlugin):
    def __init__(self):
        self.auth = HostedTrackerAuth(settings.PT_USERNAME, settings.PT_PASSWORD)


    def send_help(self, campfire, room, message, speaker):
        help_text = """%s: Here is your help for the PivotalTracker plugin:
        pt story create "Title" "Description" bug|feature|chore|release -- Create a story
        pt getmine started|finished|delivered|accepted|rejected|unstarted|unscheduled -- Get a list of all stories that belong to you
        pt start #story_id -- Start a particular story.
        pt start|tell next bug|feature|chore -- Start or tell the next story of a given type.
        """ % speaker['user']['name']
        room.paste(help_text)


    def handle_message(self, campfire, room, message, speaker):
        project_name = room.data['name']
        tracker = Tracker(settings.PT_ROOM_TO_PROJECT_MAP[project_name], self.auth)
        body = message['body']

        if not body:
            return

        if not body.startswith(settings.CAMPFIRE_BOT_NAME):
            return

        m = re.match('%s: pt story create "(?P<title>.*)" "(?P<description>.*)" (?P<type>.*)$' %
                        settings.CAMPFIRE_BOT_NAME, body)
        if m:
            story = Story()
            story.SetRequestedBy(speaker['user']['name'])
            story.SetName(m.group('title'))
            story.SetDescription(m.group('description'))
            story.SetStoryType(m.group('type'))
            new_story = tracker.AddNewStory(story)
            self.speak_new_story(room, new_story, speaker)
            return

        m = re.match("%s: pt getmine (?P<state>started|finished|delivered|accepted|rejected|unstarted|unscheduled)$" % settings.CAMPFIRE_BOT_NAME,
                     body)
        if m:
            stories = tracker.GetStories('owner:"%s" state:%s' % (speaker['user']['name'], m.group('state')))
            if len(stories) > 0:
                speak_text = "%s: Here are your stories:\r\n" % speaker['user']['name']
                room.speak(speak_text)
                speak_text = ''
                for story in stories:
                    speak_text += '[#%i] "%s" (%s)\r\n\r\n' % (story.GetStoryId(),
                                                               story.GetName(), story.GetUrl())
                room.paste(speak_text)
            else:
                speak_text = "%s: You have no stories matching that query." % speaker['user']['name']
                room.speak(speak_text)
            return

        m = re.match("%s: pt start #?(?P<id>\d+)$" % settings.CAMPFIRE_BOT_NAME, body)
        if m:
            story = tracker.GetStory(int(m.group('id')))
            story.SetCurrentState('started')
            story.SetOwnedBy(speaker['user']['name'])
            tracker.UpdateStory(story)
            room.speak("%s: [#%i] started by you! Get to work!" % (speaker['user']['name'],
                                                    story.GetStoryId()))
            return

        m = re.match("%s: pt (?P<command>start|tell) next (?P<story_type>\w+)" % settings.CAMPFIRE_BOT_NAME, body)
        if m:
            next = tracker.GetStories("type:%s state:unstarted" % m.group('story_type'))[0]
            if m.group('command') == 'start':
                next.SetCurrentState('started')
                next.SetOwnedBy(speaker['user']['name'])
                tracker.UpdateStory(next)
                room.speak("%s: [#%i] started by you! Get to work!" % (speaker['user']['name'],
                                                                       next.GetStoryId()))
            elif m.group('command') == 'tell':
                room.speak("%s: [#%i] %s (%s)" % (settings.CAMPFIRE_BOT_NAME, next.GetStoryId(),
                                                  next.GetName(), next.GetUrl()))
            return



    def speak_new_story(self, room, new_story, speaker):
        room.speak(unicode("%s: Your story has been created successfully." % speaker['user']['name']))

