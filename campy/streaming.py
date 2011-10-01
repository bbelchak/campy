import base64
from twisted.internet import reactor, protocol
from twisted.protocols import basic
try:
    import json
except ImportError:
    import simplejson as json

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
    protocol = StreamingParser

    def __init__(self, consumer):
        if isinstance(consumer, MessageReceiver):
            self.consumer = consumer
        else:
            raise TypeError("consumer should be an instance of MessageReceiver")

    def make_header(self, username, password, method, uri, postdata=""):
        auth_header = 'Basic ' + base64.b64encode("%s:%s" % (username, password)).strip()
        header = [
            "%s %s HTTP/1.1" % (method, uri),
            "Authorization: %s" % auth_header,
            "User-Agent: campy bot",
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

def start(username, password, room_id, consumer):
    client = StreamFactory(consumer)
    client.make_header(username, password, "GET", "/room/%s/live.json" % room_id)
    reactor.connectTCP("streaming.campfirenow.com", 80, client)
