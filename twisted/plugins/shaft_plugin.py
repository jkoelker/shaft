
from zope.interface import implements

from twisted.python import usage, log
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet, service, strports

from twisted.cred import checkers, portal
from twisted.conch.manhole import ColoredManhole
from twisted.conch.manhole_ssh import ConchFactory, TerminalRealm
from twisted.conch.manhole_tap import chainedProtocolFactory

creds = {"admin": "p"}
jarFile = "/home/jkoelker/Downloads/test/minecraft_server.jar"
workingPath = "/home/jkoelker/Downloads/test"

class Options(usage.Options):
    optParameters = [["ssh", "s", 2222, "The port number for ssh shell."]]

class ShaftServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "shaft"
    description = "Shaft gets you to the mine(craft)"
    options = Options

    def makeService(self, options):
        svc = service.MultiService()

        checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(**creds)

        from shaft import supervisor 
        s = supervisor.Supervisor()
        s.startMinecraft(jar=jarFile, path=workingPath)
        s.setServiceParent(svc)

        namespace = {"s": s,
                     "log": log,
                     "p": s.protocols}

        sshRealm = TerminalRealm()
        sshRealm.chainedProtocolFactory = chainedProtocolFactory(namespace)

        sshPortal = portal.Portal(sshRealm, [checker])
        sshFactory = ConchFactory(sshPortal)
        sshService = strports.service(str(options["ssh"]), sshFactory)
        sshService.setServiceParent(svc)

        return svc

serviceMaker = ShaftServiceMaker()

