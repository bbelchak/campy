#
# Copyright (c) 2011 Mark Wong <markwkm@gmail.com>
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

from random import shuffle


class BlackJack(CampyPlugin):
    def __init__(self):
        self.table = BlackJackTable(settings.BLACKJACK_DECKS)
        self.table.shuffle()

    def send_help(self, campfire, room, message, speaker):
        help_text = """%s: Here is your help for the BlackJack plugin:
hit -- Hit me!
join -- Join the game.
leave -- Leave the game.
show -- What is on the table?
stand -- End your turn.
start -- Start a round.

Example: bj join
        """ % speaker['user']['name']
        room.paste(help_text)

    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        if not body:
            return

        if not body.startswith(settings.CAMPFIRE_BOT_NAME):
            return

        m = re.match('%s: bj (?P<cmd>.*)$' % settings.CAMPFIRE_BOT_NAME, body)
        if m:
            try:
                cmd = m.group('cmd')
                if cmd == 'hit':
                    if self.table.hit(speaker['user']['name'], room):
                        room.paste(self.table.show_table())
                    else:
                        room.speak('%s: It\'s not your turn.' % \
                                speaker['user']['name'])
                elif cmd == 'join':
                    seat = self.table.add_player(speaker['user']['name'])
                    if seat == -1:
                        room.speak('%s: You are already in the game.' % \
                                speaker['user']['name'])
                    else:
                        room.speak('%s: You are in position %d.' % \
                                (speaker['user']['name'], seat))
                elif cmd == 'leave':
                    if self.table.remove_player(speaker['user']['name']):
                        room.speak('%s: You have left the table.' % \
                                speaker['user']['name'])
                    else:
                        room.speak('%s: You are not in the game.' % \
                                speaker['user']['name'])
                elif cmd == 'show':
                    room.paste(self.table.show_table())
                elif cmd == 'stand':
                    if self.table.stand(speaker['user']['name'], room):
                        room.paste(self.table.show_table())
                    else:
                        room.speak('%s: It\'s not your turn.' % \
                                speaker['user']['name'])
                elif cmd == 'start':
                    if self.table.deal(speaker['user']['name']):
                        room.paste(self.table.show_table())
                        room.speak('%s: It\'s your turn.' % \
                                self.table[game.position].get_name())
                    else:
                        room.speak('%s: You cannot start the game if you ' \
                                'are not playing.' % \
                                speaker['user']['name'])
                else:
                    room.speak('I don\'t recognize the command "%s"' % cmd)
            except (KeyError,):
                room.speak(traceback.format_exc())


class Card:
    def __init__(self, suit, value, card_value=None, sort_value=None):
        self.suit = suit
        self.value = value

        if sort_value is None:
            self.sort_value = value
        else:
            self.sort_value = sort_value

        if card_value is None:
            self.card_value = value
        else:
            self.card_value = card_value

    def face(self):
        return '%s%s' % (self.suit, self.value)

    def val(self):
        return self.card_value


class Deck:
    def __init__(self, definition):
        self.cards = []
        for c in definition:
            if 'sort_value' in c:
                sort_value = c['sort_value']
            else:
                sort_value = None

            if 'card_value' in c:
                card_value = c['card_value']
            else:
                card_value = None

            self.insert(Card(c['suit'], c['value'],
                    card_value=card_value, sort_value=sort_value))

    def count(self):
        return len(self.cards)

    def deal(self):
        return self.cards.pop(0)

    def insert(self, card):
        self.cards.append(card)

    def show(self):
        cards = []
        for card in self.cards:
            cards.append(card.face())
        return cards

    def shuffle(self):
        shuffle(self.cards)


class BlackJackPlayer:
    def __init__(self, name):
        self.name = name

        self.box = []

    def card_total(self):
        # TODO: Calculate all possible values when aces are involved.
        value = 0
        for card in self.box:
            value += card.val()
        return value

    def deal(self, card):
        self.box.append(card)

    def get_name(self):
        return self.name

    def return_cards(self):
        tmp = []
        tmp.extend(self.box)
        self.box = []
        return tmp


class BlackJackTable:
    MAX_POSITIONS = 9 # Not including dealer.
    DEALER_NAME = 'Dealer'

    def __init__(self, decks):
        self.number_of_decks = decks
        single_deck = [{'suit': 'S', 'value': 2},
                {'suit': 'S', 'value': 3},
                {'suit': 'S', 'value': 4},
                {'suit': 'S', 'value': 5},
                {'suit': 'S', 'value': 6},
                {'suit': 'S', 'value': 7},
                {'suit': 'S', 'value': 8},
                {'suit': 'S', 'value': 9},
                {'suit': 'S', 'value': 10},
                {'suit': 'S', 'value': 'J', 'card_value': 10,
                        'sort_value': 11},
                {'suit': 'S', 'value': 'Q', 'card_value': 10,
                        'sort_value': 12},
                {'suit': 'S', 'value': 'K', 'card_value': 10,
                        'sort_value': 13},
                {'suit': 'S', 'value': 'A', 'card_value': 11,
                        'sort_value': 14},
                {'suit': 'H', 'value': 2},
                {'suit': 'H', 'value': 3},
                {'suit': 'H', 'value': 4},
                {'suit': 'H', 'value': 5},
                {'suit': 'H', 'value': 6},
                {'suit': 'H', 'value': 7},
                {'suit': 'H', 'value': 8},
                {'suit': 'H', 'value': 9},
                {'suit': 'H', 'value': 10},
                {'suit': 'H', 'value': 'J', 'card_value': 10,
                        'sort_value': 11},
                {'suit': 'H', 'value': 'Q', 'card_value': 10,
                        'sort_value': 12},
                {'suit': 'H', 'value': 'K', 'card_value': 10,
                        'sort_value': 13},
                {'suit': 'H', 'value': 'A', 'card_value': 11,
                        'sort_value': 14},
                {'suit': 'C', 'value': 2},
                {'suit': 'C', 'value': 3},
                {'suit': 'C', 'value': 4},
                {'suit': 'C', 'value': 5},
                {'suit': 'C', 'value': 6},
                {'suit': 'C', 'value': 7},
                {'suit': 'C', 'value': 8},
                {'suit': 'C', 'value': 9},
                {'suit': 'C', 'value': 10},
                {'suit': 'C', 'value': 'J', 'card_value': 10,
                        'sort_value': 11},
                {'suit': 'C', 'value': 'Q', 'card_value': 10,
                        'sort_value': 12},
                {'suit': 'C', 'value': 'K', 'card_value': 10,
                        'sort_value': 13},
                {'suit': 'C', 'value': 'A', 'card_value': 11,
                        'sort_value': 14},
                {'suit': 'D', 'value': 2},
                {'suit': 'D', 'value': 3},
                {'suit': 'D', 'value': 4},
                {'suit': 'D', 'value': 5},
                {'suit': 'D', 'value': 6},
                {'suit': 'D', 'value': 7},
                {'suit': 'D', 'value': 8},
                {'suit': 'D', 'value': 9},
                {'suit': 'D', 'value': 10},
                {'suit': 'D', 'value': 'J', 'card_value': 10,
                        'sort_value': 11},
                {'suit': 'D', 'value': 'Q', 'card_value': 10,
                        'sort_value': 12},
                {'suit': 'D', 'value': 'K', 'card_value': 10,
                        'sort_value': 13},
                {'suit': 'D', 'value': 'A', 'card_value': 11,
                        'sort_value': 14}]

        definition = []
        for i in range(decks):
            definition.extend(single_deck)

        self.deck = Deck(definition)

        self.dealer = BlackJackPlayer("Dealer")
        self.table = [self.dealer]
        for i in range(BlackJackTable.MAX_POSITIONS):
            self.table.append(None)

        self.position = 0

        self.round_started = False

    def add_player(self, name, seat=None):
        # Don't let two people with the same name join twice.
        for i in range(BlackJackTable.MAX_POSITIONS):
            if self.table[i] is None:
                continue
            if self.table[i].get_name() == name:
                return -1

        if self.player_count() >= BlackJackTable.MAX_POSITIONS:
            raise Exception('table is full')

        player = BlackJackPlayer(name)

        if seat is None:
            for i in range(BlackJackTable.MAX_POSITIONS):
                if self.table[i + 1] is None:
                    self.table[i + 1] = player
                    return i + 1
        else:
            if self.table[i + 1] is None:
                self.table[i + 1] = player
                return i + 1
            else:
                raise Exception('seat is already taken')

    def count(self):
        return self.deck.count()

    def deal(self, name):
        # Don't let someone not in the game start it.
        start = False
        for i in range(BlackJackTable.MAX_POSITIONS):
            if self.table[i] is None:
                continue
            if self.table[i].get_name() == name:
                start = True
                break

        if start == False:
            return False

        for i in range(2):
            # Deal to the dealer last.
            order = range(1, BlackJackTable.MAX_POSITIONS)
            order.append(0)
            for i in order:
                if self.table[i] is not None:
                    self.table[i].deal(self.deck.deal())

        for i in range(BlackJackTable.MAX_POSITIONS):
            if self.table[i + 1] is not None:
                self.position = i + 1
                self.round_started = True
                return True

    def dealer_turn(self):
        score_to_beat = 0
        self.round_started = False
        for i in range(BlackJackTable.MAX_POSITIONS):
            if self.table[i] is None:
                continue

            if self.table[i].card_total() > 21:
                # Don't need to beat any busted players.
                continue

            tmp_value = self.table[i].card_total()
            if tmp_value > score_to_beat:
                score_to_beat = tmp_value

        while self.dealer.card_total() < score_to_beat:
            self.hit(BlackJackTable.DEALER_NAME)
            if self.dealer.card_total() > 21:
                # Dealer busts.
                return

    def hit(self, name, room=None):
        if self.table[self.position].get_name() != name:
            return False

        self.table[self.position].deal(self.deck.deal())
        # Automatically move to next player if bust.
        if self.table[self.position].card_total() > 21:
            if room is not None:
                room.speak('%s: You busted!' % name)
            # If the current turn is on the dealer, don't need to stand when
            # done.
            if self.position != 0:
                self.stand(name, room)
        return True

    def player_count(self):
        count = 0
        for i in range(BlackJackTable.MAX_POSITIONS):
            if self.table[i + 1] is not None:
                count += 1
        return count

    def remove_player(self, name):
        for i in range(BlackJackTable.MAX_POSITIONS):
            if self.table[i + 1] is None:
                continue
            if self.table[i + 1].get_name() == name:
                self.table[i + 1] = None
                return True
        return False

    def retrieve_cards(self):
        for i in range(BlackJackTable.MAX_POSITIONS + 1):
            if self.table[i] is not None:
                for card in self.table[i].return_cards():
                    self.deck.insert(card)

    def show_table(self):
        # Determine if a game is in progress by the number of cards in the
        # dealer's hand.
        if len(self.dealer.box) != 0:
            msg = 'Current turn: %s\n' % self.table[self.position].get_name()
        else:
            msg = ''
        msg += 'Number of decks: %d\n' % self.number_of_decks
        if self.position == 0:
            start_position = 0
        else:
            start_position = 1
            msg += '0 %s' % self.table[0].get_name()
            if len(self.dealer.box) > 0:
                msg += ': %s **' % self.dealer.box[0].face()
            msg += '\n'
        for i in range(start_position, BlackJackTable.MAX_POSITIONS + 1):
            if self.table[i] is not None:
                msg += '%d %s' % (i, self.table[i].get_name())
                if len(self.table[i].box) > 0:
                    msg += ': '
                for card in self.table[i].box:
                    msg += '%s ' % card.face()
                if len(self.table[i].box) > 0:
                    msg += '= %d' % self.table[i].card_total()
                msg += '\n'

        if self.round_started == False and len(self.dealer.box) > 0:
            # Assume the game has ended and show the results if there are cards
            # on the table.

            # Use dealer_value to determine whether a player beat the dealer.
            if self.dealer.card_total() > 21:
                dealer_value = 0
            else:
                dealer_value = self.dealer.card_total()

            max_hand = 0
            for i in range(BlackJackTable.MAX_POSITIONS + 1):
                if self.table[i] is not None:
                    val = self.table[i].card_total()
                    if val > max_hand and val <= 21:
                        max_hand = val

            winners = []
            if dealer_value >= max_hand:
                winnders.append(self.dealer.get_name())

            # Determine how many people beat the dealer.
            for i in range(1, BlackJackTable.MAX_POSITIONS + 1):
                if self.table[i] is not None:
                    if self.table[i].card_total() >= dealer_value:
                        winners.append(self.table[i].get_name())

            if len(winners) > 1:
                msg += '\nWinners' 
            else:
                msg += '\nWinner' 
            msg += ': %s ' % ', '.join(winners)

            busted = []
            for i in range(1, BlackJackTable.MAX_POSITIONS + 1):
                if self.table[i] is not None:
                    if self.table[i].card_total() > 21:
                        busted.append(self.table[i].get_name())
            msg += 'Busted: %s ' % ', '.join(busted)

            # Round over, collect cards.
            self.retrieve_cards()

        return msg

    def stand(self, name, room=None):
        if self.table[self.position].get_name() != name:
            return False

        while True:
            self.position = (self.position + 1) % \
                    (BlackJackTable.MAX_POSITIONS + 1)
            if self.position == 0:
                self.dealer_turn()
                break
            if self.table[self.position] is not None:
                room.speak('%s: It\'s your turn.' % self.table[self.position])
                break
        return True

    def shuffle(self):
        self.deck.shuffle()
