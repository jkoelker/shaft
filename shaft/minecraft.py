from twisted.python import log
from twisted.internet import error, defer, protocol, reactor as _reactor
from twisted.protocols import basic
from twisted.runner.procmon import transport as dummyTransport

from zope.interface import implements, Interface, Attribute

import re
from datetime import datetime

MESSAGE = "MESSAGE"
LOGIN = "LOGIN"
KICK = "KICK"
STOP = "STOP"
CHAT = "CHAT"
BAN = "BAN"
PARDON = "PARDON"
BANIP = "BANIP"
PARDONIP = "PARDONIP"
OP = "OP"
DEOP = "DEOP"
TP = "TP"
GIVE = "GIVE"
TELL = "TELL"
SAVEALL = "SAVEALL"
SAVEOFF = "SAVEOFF"
SAVEON = "SAVEON"
LIST = "LIST"
SAY = "SAY"
TIME = "TIME"
WHITELIST = "WHITELIST"
UNKNOWN = "UNKNOWN"

logLine = re.compile("(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) \[(\w+)\] (.*)")

successKick = re.compile("(.+): Kicking (.+)")
noUserKick = re.compile("Can't find user (.+)\. No kick.")
kickRegexes = (successKick, noUserKick,)

stoppingConsole = re.compile("(.+): Stopping the server..")
stoppingServer = re.compile("Stopping server")
stoppingChunks = re.compile("Saving chunks")
stoppingRegexes = (stoppingConsole, stoppingServer, stoppingChunks,)

chatMessage = re.compile("<(.+)> (.+)")
chatRegexes = (chatMessage,)

banUser = re.compile("(.+): Banning (.+)")
banRegexes = (banUser,)

pardonUser = re.compile("(.+): Pardoning (.+)")
pardonRegexes = (pardonUser,)

banIP= re.compile("(.+): Banning ip (.+)")
banIPRegexes = (banIP,)

pardonIP= re.compile("(.+): Pardoning ip (.+)")
pardonIPRegexes = (pardonIP,)

opUser = re.compile("(.+): Opping (.+)")
opRegexes = (opUser,)

deopUser = re.compile("(.+): De-Opping (.+)")
deopRegexes = (deopUser,)

tpUser = re.compile("(.+): Teleporting (.+) to (.+)\.")
tpRegexes = (tpUser,)

tellUser = re.compile(".7(.+) whispers (.+) to (.+)")
tellConsole = re.compile("\[(.+)->(.+)\] (.+)")
tellRegexes = (tellUser, tellConsole,)

giveUser = re.compile("(.+): Giving (.+) some (\d+)")
giveRegexes = (giveUser,)

sayMsg = re.compile("\[(.+)\] (.+)")
sayRegexes = (sayMsg,)

timeAdd = re.compile("(.+): (Added) (\d+) to time")
timeSet = re.compile("(.+): (Set) time to (\d+)")
timeRegexes = (timeAdd, timeSet,)

saveForce = re.compile("(.+): (Forcing) save..")
saveComplete = re.compile("(.+): Save (complete).")
saveAllRegexes = (saveForce, saveComplete,)

saveOn = re.compile("(.+): (Enabling) level saving..")
saveOnRegexes = (saveOn,)

saveOff = re.compile("(.+): (Disabling) level saving..")
saveOffRegexes = (saveOff,)

connectedUsers = re.compile("Connected players: (.*)")
listRegexes = (connectedUsers, )

whiteListOn = re.compile("(.+): Turned (on) white-listing")
whiteListOff = re.compile("(.+): Turned (off) white-listing")
whiteListList = re.compile("(White-listed) (players): (.*)")
whiteListAdd = re.compile("(.+): (Added) (.+) to white-list")
whiteListRemove = re.compile("(.+): (Removed) (.+) from white-list")
whiteListReload = re.compile("(.+): (Reloaded) white-list from file")
whiteListRegexes = (whiteListOn, whiteListOff, whiteListList,
                    whiteListAdd, whiteListRemove, whiteListReload,
                    whiteListRegexes,)


def isType(regexes, text):
    for r in regexes:
        m = r.match(text)
        if m is not None:
            return m
    return None

def isWhiteList(text):
    return isType(whiteListRegexes, text)

def isOp(text):
    return isType(opRegexes, text)

def isDeOp(text):
    return isType(deopRegexes, text)

def isTp(text):
    return isType(tpRegexes, text)

def isGive(text):
    return isType(giveRegexes, text)

def isTell(text):
    return isType(tellRegexes, text)

def isSaveAll(text):
    return isType(saveAllRegexes, text)

def isSaveOff(text):
    return isType(saveOffRegexes, text)

def isSaveOn(text):
    return isType(saveOnRegexes, text)

def isList(text):
    return isType(listRegexes, text)

def isSay(text):
    return isType(sayRegexes, text)

def isTime(text):
    return isType(timeRegexes, text)

def isBanIP(text):
    return isType(banIPRegexes, text)

def isPardonIP(text):
    return isType(pardonIPRegexes, text)

def isPardon(text):
    return isType(pardonRegexes, text)

def isBan(text):
    return isType(banRegexes, text)

def isKick(text):
    return isType(kickRegexes, text)

def isStop(text):
    return isType(stoppingRegexes, text)

def isChat(text):
    return isType(chatRegexes, text)

def checkType(text):
    if isKick(text) is not None:
        return KICK
    elif isStop(text) is not None:
        return STOP
    elif isChat(text) is not None:
        return CHAT
    elif isWhiteList(text) is not None:
        return WHITELIST
    elif isOp(text) is not None:
        return OP
    elif isDeOp(text) is not None:
        return DEOP
    elif isTp(text) is not None:
        return TP
    elif isGive(text) is not None:
        return GIVE
    elif isSaveAll(text) is not None:
        return SAVEALL
    elif isSaveOff(text) is not None:
        return SAVEOFF
    elif isSaveOn(text) is not None:
        return SAVEON
    elif isList(text) is not None:
        return LIST
    elif isTime(text) is not None:
        return TIME
    # Tell must be before Say because the regexes are greedy
    elif isTell(text) is not None:
        return TELL
    elif isSay(text) is not None:
        return SAY
    # BanIP and PardonIP must be before Ban and Pardon because the regexes
    # are greedy
    elif isBanIP(text) is not None:
        return BANIP
    elif isPardonIP(text) is not None:
        return PARDONIP
    elif isBan(text) is not None:
        return BAN
    elif isPardon(text) is not None:
        return PARDON
    return UNKNOWN


def maybeCallback(d, result, key=None, delKey=True):
    if d is None:
        return

    if isinstance(d, dict) and key is not None and key in d:
        d[key].callback(result)
        if delKey:
            del d[key]
    else:
        d.callback(result)


class ILineHandler(Interface):
    type = Attribute("A C{str} specifying the type of message the "
                     "Handler handles")
    def handle(self, line):
        """
        Handles a Line of text
        """


class BaseHandler(object):
    implements(ILineHandler)

    type = UNKNOWN
    handler = None

    def __init__(self, handler):
        self.handler = handler 

    def log(self, line):
        m = logLine.match(line)
        if m is not None:
            dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            level = m.group(2)
            text = m.group(3)
            type = checkType(text)
            log.msg("\ntype: %s\nlevel: %s\ntext: %s" % (type, level, text))
            return

        log.msg("%s: %s" % (self.type, line))

    def handle(self, line):
        self.log(line)


whiteListDeferreds = {}
whiteListManager = None
class WhiteListHandler(BaseHandler):
    type = WHITELIST

    def handle(self, line):
        global whiteListManager

        m = isWhiteList(line)
        op = m.group(1)
        action = m.group(2).lower()

        result = {'action': WHITELIST,
                  'op': op,
                  'type': action,
                  'success': True}

        if action == "reloaded":
            maybeCallback(whiteListDeferreds, result, key=action)

        elif action == "players":
            users = m.group(3).strip().split(' ')
            result['users'] = users
            maybeCallback(whiteListDeferreds, result, key=action)

        elif action in ("off", "on"):
            whiteListManager = maybeCallback(whiteListManager, result)
            maybeCallback(whiteListDeferreds, result, key=action)

        elif action in ("removed", "added"):
            user = m.group(3)
            result['user'] = user
            maybeCallback(whiteListDeferreds, result, key=(action, user))

listDeferred = None
class ListHandler(BaseHandler):
    type = LIST

    def handle(self, line):
        global listDeferred

        m = isList(line)
        users = m.group(1).strip().split(' ')

        listDeferred = maybeCallback(listDeferred, {'action': LIST,
                                                    'users': users,
                                                    'success': True})


saveDeferred = None
saving = False
class SaveAllHandler(BaseHandler):
    type = SAVEALL

    def handle(self, line):
        global saveDeferred
        global saving

        m = isSaveAll(line)
        op = m.group(1)
        status = m.group(2).lower()

        if status == "forcing":
            saving = True
            return

        saveDeferred = maybeCallback(saveDeverred, {'action': SAVEALL,
                                                    'op': op,
                                                    'success': True})
        saving = False


saveOnDeferred = None
class saveOnHandler(BaseHandler):
    type = SAVEON

    def handle(self, line):
        global saveOnDeferred

        m = isSaveOn(line)
        op = m.group(1)

        saveOnDeferred = maybeCallback(saveOnDeferred, {'action': SAVEON,
                                                        'op': op,
                                                        'success': True})


saveOffDeferred = None
class saveOffHandler(BaseHandler):
    type = SAVEOFF

    def handle(self, line):
        global saveOffDeferred

        m = isSaveOff(line)
        op = m.group(1)

        saveOffDeferred = maybeCallback(saveOffDeferred, 
                                        {'action': SAVEOFF,
                                         'op': op,
                                         'success': True})


timeDeferreds = {}
class TimeHandler(BaseHandler):
    type = TIME

    def handle(self, line):
        m = isTime(line)
        op = m.group(1)
        type = m.group(2).lower()
        amount = m.group(3)

        result = {'action': TIME,
                  'op': op,
                  'type': type,
                  'amount': amount,
                  'success': True}

        maybeCallback(timeDeferreds, result, key=(type, amount)) 


sayDeferreds = {}
class SayHandler(BaseHandler):
    type = SAY

    def handle(self, line):
        m = isSay(line)
        op = m.group(1)
        message = m.group(2)

        result = {'action': SAY,
                  'op': op,
                  'message': message,
                  'success': True}

        maybeCallback(sayDeferreds, result, key=message)


giveDeferreds = {}
class GiveHandler(BaseHandler):
    type = GIVE

    def handle(self, line):
        m = isGive(line)
        op = m.group(1)
        user = m.group(2)
        item = m.group(3)

        result = {'action': GIVE,
                  'op': op,
                  'user': user,
                  'item': item,
                  'success': True}

        maybeCallback(giveDeferreds, result, key=(user, item))


tpDeferreds = {}
class TpHandler(BaseHandler):
    type = TP

    def handle(self, line):
        m = isTp(line)
        op = m.group(1)
        user1 = m.group(2)
        user2 = m.group(3)

        result = {'action': TP,
                  'user1': user1,
                  'user2': user2,
                  'success': True}

        maybeCallback(tpDeferreds, result, key=(user1, user2))


tellDeferreds = {}
class TellHandler(BaseHandler):
    type = TELL

    def handle(self, line):
        m = isTell(line)
        user1 = m.group(1)

        if m.group(0)[0] == '[':
            user2 = m.group(2)
            message = m.group(3)

        else:
            message = m.group(2)
            user2 = m.group(3)

        result = {'action': TELL,
                  'user1': user1,
                  'user2': user2,
                  'success': True}

        maybeCallback(tellDeferreds, result, key=(user2, what))


class ChatHandler(BaseHandler):
    type = CHAT

    def handle(self, line):
        m = isChat(line)
        user = m.group(1)
        message = m.group(2)

        # Put callback up here for chat bridge
        log.msg("CHAT:\nUser: %s\nMsg: %s" % (user, message))


pardonIPDeferreds = {}
class PardonIPHandler(BaseHandler):
    type = PARDONIP 

    def handle(self, line):
        m = isPardonIP(line)
        op = group(1)
        user = group(2)

        result = {'action': PARDONIP,
                  'op': op,
                  'user': user,
                  'success': True}

        maybeCallback(pardonIPDeferreds, result, key=user)


banIPDeferreds = {}
class BanHandler(BaseHandler):
    type = BANIP

    def handle(self, line):
        m = isBanIP(line)
        op = group(1)
        user = group(2)

        result = {'action': BANIP,
                  'op': op,
                  'user': user,
                  'success': True}

        maybeCallback(banIPDeferreds, result, key=user)


pardonDeferreds = {}
class PardonHandler(BaseHandler):
    type = PARDON 

    def handle(self, line):
        m = isPardon(line)
        op = group(1)
        user = group(2)

        result = {'action': PARDON,
                  'op': op,
                  'user': user,
                  'success': True}

        maybeCallback(pardonDeferreds, result, key=user)


banDeferreds = {}
class BanHandler(BaseHandler):
    type = BAN

    def handle(self, line):
        m = isBan(line)
        op = group(1)
        user = group(2)

        result = {'action': BAN,
                  'op': op,
                  'user': user,
                  'success': True}

        maybeCallback(banDeferreds, result, key=user)


opDeferreds = {}
class OpHandler(BaseHandler):
    type = OP

    def handle(self, line):
        m = isOp(line)
        op = group(1)
        user = group(2)

        result = {'action': OP,
                  'op': op,
                  'user': user,
                  'success': True}

        maybeCallback(opDeferreds, result, key=user)


deopDeferreds = {}
class DeOpHandler(BaseHandler):
    type = DEOP

    def handle(self, line):
        m = isDeOp(line)
        op = group(1)
        user = group(2)

        result = {'action': DEOP,
                  'op': op,
                  'user': user,
                  'success': True}

        maybeCallback(deopDeferreds, result, key=user)


kickDeferreds = {}
class KickHandler(BaseHandler):
    type = KICK

    def handle(self, line):
        m = isKick(line)
        op = m.group(1)
        
        if len(m.groups()) == 2:
            user = m.group(2)
            success = True
            log.msg("User %s was kicked" % user)
        else:
            user = m.group(1)
            success = False
            log.msg("User %s not connected" % user)

        result = {'action': KICK,
                  'op': op,
                  'user': user,
                  'success': success})

        maybeCallback(kickDeferreds, result, key=user)


stopDeferred = None
stopRequested = False
class StopHandler(BaseHandler):
    type = STOP

    def handle(self, line):
        global stopDeferred
        global stopRequested

        m = stoppingConsole.match(line)
        if m is not None:
            log.msg("User %s requested server to stop" % m.group(1))
            stopRequested = True
            return

        m = stoppingServer.match(line)
        if m is not None:
            log.msg("Server is stopping")

            stopDeferred = maybeCallback(stopDeferred, {'action': STOP,
                                                        'success': True})
            return

        m = stoppingChunks.match(line)
        if m is not None:
            log.msg("Server Stopped")



# Not sure I like this (it seems too "clever")
HANDLER_MAP = dict([(globals()[x].type,
                     globals()[x]) for x in dir() if hasattr(globals()[x],
                                                             "type")])


class MinecraftLineHandler(basic.LineReceiver):
    delimiter = '\n'
    protocol = None

    def __init__(self, service):
        self.protocol = protocol 

    def lineReceived(self, line):
        dt = datetime.now()
        level = UNKNOWN
        type = UNKNOWN
        text = line

        m = logLine.match(line)
        
        if m is not None:
            dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            level = m.group(2)
            text = m.group(3)
            type = checkType(text)

        handler = HANDLER_MAP[type](self)
        handler.handle(text)


class MinecraftServerProtocol(protocol.ProcessProtocol):
    service = None
    empty = True
    name = None

    def connectionMade(self):
        log.msg("Connected to instance %s" % self.name)
        self.output = MinecraftLineHandler(self)
        self.output.makeConnection(dummyTransport)

    def outRecieved(self, data):
        self.output.dataReceived(data)
        self.empty = data[-1] == '\n'

    errReceived = outRecieved

    def processEnded(self, reason):
        if not self.empty:
            self.output.dataReceived('\n')
        if not stopRequested:
            self.service.connectionLost(self.name)

    def _sendCommand(self, *args):
        cmd = ' '.join(args)
        self.transport.write(cmd + '\n')

    def kickUser(self, username):
        log.msg("Kicking user: %s" % username)
        kickDeferreds[username] = defer.Deferred()
        self._sendCommand("kick", username)
        return kickDeferreds[username]

    def stopServer(self):
        global stopDeferred
        log.msg("Stopping server")
        stopDeferred = defer.Deferred()
        self._sendCommand("stop")
        return stopDeferred
        
    def banUser(self, username):
        log.msg("Banning user: %s" % username)
        banDeferreds[username] = defer.Deferred()
        self._sendCommand("ban", username)
        return banDeferreds[username]

    def pardonUser(self, username):
        log.msg("Pardoning user: %s" % username)
        pardonDeferreds[username] = defer.Deferred()
        self._sendCommand("pardon", username)
        return pardonDeferreds[username]

    def banIP(self, ip):
        log.msg("Banning ip: %s" % ip)
        banIPDeferreds[ip] = defer.Deferred()
        self._sendCommand("ban", "ip", ip)
        return banIPDeferreds[ip]

    def pardonIP(self, ip):
        log.msg("Pardoning ip: %s" % ip)
        pardonIPDeferreds[ip] = defer.Deferred()
        self._sendCommand("pardon", "ip", ip)
        return pardonIPDeferreds[ip]

    def opUser(self, username):
        log.msg("Opping user: %s" % username)
        opDeferreds[username] = defer.Deferred()
        self._sendCommand("op", username)
        return opDeferreds[username]

    def deopUser(self, username):
        log.msg("De-opping user: %s" % username)
        deopDeferreds[username] = defer.Deferred()
        self._sendCommand("deop", username)
        return deopDeferreds[username]

    def tellUser(self, username, what):
        log.msg("Telling %s: %s" % (username, what))
        tellDeferreds[(username, what)] = defer.Deferred()
        self._sendCommand("tell", username, what)
        return tellDeferreds[(username, what)]

    def tpUser(self, username1, username2):
        log.msg("Teleporting: %s->%s" % (username1, username2))
        tpDeferreds[(username1, username2)] = defer.Deferred()
        self._sendCommand("tp", username1, username2)
        return tpDeferreds[(username1, username2)]

    def giveUser(self, username, item, quantity=1):
        log.msg("Giving: %s %s (%s)" % (username, item, quantity))
        giveDeferreds[(username, item)] = new defer.Deferred()
        self._sendCommand("give", username, item, quantity)
        return giveDeferreds[(username, item)]

    def say(self, what):
        log.msg("Saying: %s" % what)
        sayDeferreds[what] = defer.Deferred()
        self._sendCommand("say", what)
        return tellDeferreds[what]

    def time(self, type, amount):
        log.msg("Time: %s %s" % (type, amount))
        timeDeferreds[(type, amount)] = defer.Deferred()
        self._sendCommand("time", type, amount)
        return timeDeferreds[(type, amount)]

    def saveAll(self):
        global saveDeferred

        if saving:
            d = defer.Deferred()
            d.callback({'action': SAVEALL,
                        'reason': "save already in progress",
                        'success': False})
            return d

        log.msg("Saving")
        saveDeferred = defer.Deferred()
        self._sendCommand("save-all")
        return saveDeferred

    def saveOn(self):
        global saveOnDeferred

        log.msg("Enabling saves")
        saveOnDeferred = defer.Deferred()
        self._sendCommand("save-on")
        return saveOnDeferred

    def saveOff(self):
        global saveOffDeferred

        log.msg("Disabling saves")
        saveOffDeferred = defer.Deferred()
        self._sendCommand("save-off")
        return saveOffDeferred

    def list(self):
        global listDeferred
        
        log.msg("Listing connected users")
        listDeferred = defer.Deferred()
        self._sendCommand("list")
        return listDeferred

    def whiteListOff(self):
        log.msg("Turning off whitelist")
        action = "off"
        whiteListDeferreds[action] = defer.Deferred()
        self._sendCommand("whitelist", action)
        return whiteListDeferreds[action]

    def whiteListOn(self):
        log.msg("Turning on whitelist")
        action = "on"
        whiteListDeferreds[action] = defer.Deferred()
        self._sendCommand("whitelist", action)
        return whiteListDeferreds[action]

    def whiteListReload(self):
        log.msg("Reloading whitelist")
        action = "reloaded"
        whiteListDeferreds[action] = defer.Deferred()
        self._sendCommand("whitelist", "reload")
        return whiteListDeferreds[action]

    def whiteListList(self):
        log.msg("Listing whitelist")
        action = "players"
        whiteListDeferreds[action] = defer.Deferred()
        self._sendCommand("whitelist", "list")
        return whiteListDeferreds[action]

    def whiteListUser(self, username):
        log.msg("Whitelisting user: %s" % username)
        action = "added"
        whiteListDeferreds[(action, username)] = defer.Deferred()
        self._sendCommand("whitelist", "add", username)
        return whiteListDeferreds[(action, username)]

    def unWhiteListUser(self, username):
        log.msg("Unwhitelisting user: %s" % username)
        action = "removed"
        whiteListDeferreds[(action, username)] = defer.Deferred()
        self._sendCommand("whitelist", "remove", username)
        return whiteListDeferreds[(action, username)]

    def setWhiteListManager(self, f):
        global whiteListManager

        def resetListener(_):
            global whiteListManager

            log.msg("Setting whitelist manager to %s" % f.__name__)
            whiteListManager = defer.Deferred()
            whiteListManager.addCallback(f)
            whiteListManager.addCallback(resetListener)

        resetListener(None)


