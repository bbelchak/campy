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
import base64
from twisted.internet import reactor, protocol, ssl
from twisted.protocols import basic
import logging
try:
    import json
except ImportError:
    import simplejson as json

log = logging.getLogger(__name__)

class StreamingParser(basic.LineReceiver):
    delimiter = '\r'

    def __init__(self):
        self.in_header = True
        self.header_data = []
        self.status_data = ""
        self.status_size = None

    def connectionMade(self):
        self.transport.write(self.factory.header)
        self.factory.consumer._registerProtocol(self)

    def lineReceived(self, line):
        while self.in_header:
            if line:
                self.header_data.append(line)
            else:
                http, status, message = self.header_data[0].split(" ", 2)
                status = int(status)
                if status == 200:
                    self.factory.consumer.connectionMade()
                else:
                    self.factory.continueTrying = 0
                    self.transport.loseConnection()
                    self.factory.consumer.connectionFailed(RuntimeError(status, message))

                self.in_header = False
            break

        try:
            if line:
                message = json.loads(line)
                if message['type'] == 'KickMessage':
                    self.transport.loseConnection()
                    self.factory.connector.connect()
        except:
            pass
        else:
            if line:
                if isinstance(message, dict):
                    self.factory.consumer.messageReceived(message)


class MessageReceiver(object):
    def connectionMade(self):
        pass

    def connectionFailed(self, why):
        pass

    def messageReceived(self, message):
        raise NotImplementedError

    def _registerProtocol(self, protocol):
        self._streamProtocol = protocol

    def disconnect(self):
        if hasattr(self, "_streamProtocol"):
            self._streamProtocol.factory.continueTrying = 0
            self._streamProtocol.transport.loseConnection()
        else:
            raise RuntimeError("not connected")


class StreamFactory(protocol.ReconnectingClientFactory):
    maxDelay = 120
    initialDelay = 3
    protocol = StreamingParser
    noisy = True

    def __init__(self, consumer, room):
        self.room = room
        if isinstance(consumer, MessageReceiver):
            self.consumer = consumer
        else:
            raise TypeError("consumer should be an instance of MessageReceiver")

    def startedConnecting(self, connector):
        log.debug("Started connecting to room %s." % self.room.name)

    def clientConnectionLost(self, connector, reason):
        log.debug("Lost connection. Reason: %s", reason)
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.debug("Connection failed. Reason: %s", reason)
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def make_header(self, username, password, method, uri, postdata=""):
        auth_header = 'Basic ' + base64.b64encode("%s:%s" % (username, password)).strip()
        header = [
            "%s %s HTTP/1.1" % (method, uri),
            "Authorization: %s" % auth_header,
            "User-Agent: campy bot (https://github.com/bbelchak/campy/)",
            "Host: streaming.campfirenow.com",
        ]

        if method == "GET":
            self.header = "\r\n".join(header) + "\r\n\r\n"
        elif method == "POST":
            header += [
                "Content-Type: application/x-www-form-urlencoded",
                "Content-Length: %d" % len(postdata)
            ]
            self.header = "\r\n".join(header) + "\r\n\r\n" + postdata

def start(username, password, room, consumer):
    client = StreamFactory(consumer, room)
    client.make_header(username, password, "GET", "/room/%s/live.json" % room.id)
    reactor.connectSSL("streaming.campfirenow.com", 443, client, ssl.ClientContextFactory())
