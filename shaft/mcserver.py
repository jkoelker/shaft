
from twisted.internet import defer, protocol

from datetime import datetime

import re

MESSAGE = "MESSAGE"
LOGIN = "LOGIN"
DISCONNECT = "DISCONNECT"
KICK = "KICK"
UNKNOWN = "UNKNOWN"

successKick = re.compile("CONSOLE: Kicking (.+)")
noUserKick = re.compile("Can't find user (.+)\. No kick.")


def isKick(text):
    if successKick.match(text) is not None:
        return True
    elif noUserKick.match(text) is not None:
        return True

    return False

class MCServerProtocol(protocol.ProcessProtocol):
    __obuf = ''
    __ebuf = ''
    
    delimiter = '\n'

    def __init__(self, *args, **kwargs):
        self.__obuf = ''
        self.__ebuf = ''
        self.__ds = {KICK: {},
                     }

    def connectionMade(self):
        pass

    def outRecieved(self, data):
        self.__obuf = self.__obuf + data

        while True:
            try:
                line, self.__obuf = self.__obuf.split(self.delimiter, 1)
            except ValueError:
                break
            
            out = self.parseOutput(line)
            self.handleOutput(out)

    def errRecieved(self, data):
        self.__ebuf = self.__ebuf + data

        while True:
            try:
                line, self.__ebuf = self.__ebuf.split(self.delimiter, 1)
            except ValueError:
                break
            
            err = self.parseError(line)
            self.handleError(err)

    def inConnectionLost(self):
        pass

    def outConnectionLost(self):
        pass

    def errConnectionlost(self):
        pass

    def processExited(self, reason):
        pass

    def processEnded(self, reason):
        pass

    def parseError(self, line):
        pass

    def handleError(self, err):
        pass

    def parseOutput(self, line):
        """
        Takes a line from the server such as:

        2011-03-06 17:21:23 [INFO] Starting minecraft server version Beta

        Returns an output dict of 

        {'datetime': datetime.datetime(2011, 3, 6, 17, 21, 23),
         'level': 'INFO',
         'text': 'Starting minecraft server version Beta',
         'type': 'MESSAGE',
         'action': None}
        """
        parts = line.split(' ')
        
        dt = ' '.join(parts[0:2])
        level = parts[2][1:-1]
        text = ' '.join(parts[3:])

        type = self.checkType(text)
        
        return {'datetime': datetime.strptime(dt, "%Y-%m-%d %H:%M:%S"),
                'level': level,
                'text' : text,
                'type': type}


    def checkType(self, text):
        """
        Known Types:

        MESSAGE
        LOGIN
        DISCONNECT
        KICK
        UNKNOWN

        """

        if isKick(text):
            return KICK

        return UNKNOWN

    def handleOutput(self, out):
        type = out["type"]
        text = out["text"]

        if type == UNKNOWN:
            self.handleUnknown(text)

        elif type == KICK:
            self.handleKick(text)

    def handleKick(self, text):
        user = None
        success = False

        m = successKick.match(text)
        if m is not None:
            user = m.group(1)
            success = True

        m = noUserKick.match(text)
        if m is not None:
            user = m.group(1)
            success = False

        if user in self.__kickds:
            d = self.__kickds[KICK][user]
            if success:
                d.callback(text)

            else:
                d.errback(text)

    def handleUnknown(self, text):
        pass

    def kickUser(self, username):
        d = defer.Deferred()
        self.transport.write("kick %s\n" % username)
        self.__ds[KICK][username] = d
        return d

