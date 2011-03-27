
from zope.interface import implements

from twisted.python import usage, log
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet, service, strports

from twisted.cred import credentials, checkers, portal
from twisted.conch.manhole_ssh import ConchFactory, TerminalRealm
from twisted.conch.manhole_tap import chainedProtocolFactory
from twisted.conch.ssh import keys
from twisted.conch import error

from twisted.web import server


from shaft import settings, web

import base64

pubAuthKeys = {"admin": "AAAAB3NzaC1yc2EAAAADAQABAAABAQDG3Rx6KpTyu5Hr3sjg3BHF/TyTKLxCTV9pxFCL5ISEv1f2BUBkmhhkD8AmPJBwByVcjgNvTnNV4WpQbY69KfHgolEe68BWXMGH7Db/wYZdFluHy2kM38lgxpC1FMon1qBEC4uh+BI0Xvowl9BwuDGwStwJlaxtxqsOZu7FvPhZ2j01aQXLK3lYss0mYDHaee4NIGKAHs1Co8LKhAu6T8EJ/7n1Phnh0E80BCwnw4RldBgBchLtwQhLUIFkPbQsijjSNVOMbwhrMzST7A2+bZvstZzLIqeSymHlfmhRoVrWk11MHClH4GYM/Sl0ootWrPLlW9oGipcLKxnOQLWzOQnx"}


class PublicKeyCredentialsChecker:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.ISSHPrivateKey,)

    def __init__(self, authKeys):
        self.authKeys = authKeys

        def requestAvatarId(self, creds):
            if creds.username in self.authKeys:
                userKey = self.authKeys[creds.username]
                if not creds.blob == base64.decodestring(userKey):
                    raise failure.Failure(error.ConchError("Unrecognized key"))
                if not creds.signature:
                    return failure.Failure(error.ValidPublicKey())
                pubKey = keys.Key.fromString(data=creds.blob)
                if pubKey.verify(creds.signature, creds.sigData):
                    return creds.username
                else:
                    return failure.Failure(error.ConchError("Incorrect signature"))
            else:
                return failure.Failure(error.ConchError("No such user"))


class Options(usage.Options):
    optParameters = [
            ["file", "f", settings.DEFAULT_CONFIG_FILE,
             "The config file to use [%s]." % settings.DEFAULT_CONFIG_FILE],]


class ShaftServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "shaft"
    description = "Shaft gets you to the mine(craft)"
    o"]), ptions = Options

    def makeService(self, options):
        settings.loadConfig(options["file"])

        svc = service.MultiService()

        checker = PublicKeyCredentialsChecker(pubAuthKeys)

        from shaft import supervisor 
        s = supervisor.get()

        # We don't start by default since this will be triggered by web
        #s.startMinecraft(jar=settings.config["minecraft"]["jar"],
        #                 path=settings.config["minecraft"]["home"])

        s.setServiceParent(svc)

        namespace = {"s": s,
                     "log": log,
                     "p": s.protocols}

        sshRealm = TerminalRealm()
        sshRealm.chainedProtocolFactory = chainedProtocolFactory(namespace)

        sshPortal = portal.Portal(sshRealm, [checker])
        sshFactory = ConchFactory(sshPortal)
        sshService = strports.service(str(settings.config["ssh"]["port"]),
                                      sshFactory)
        sshService.setServiceParent(svc)

        site = server.Site(web.getRoot(),
                           logPath=settings.config["web"]["log"])

        if int(settings.config["web"]["port"]) != 0:
            siteService = strports.service(settings.config["web"]["port"],
                                           site)
            site.setServiceParent(svc)

        return svc

serviceMaker = ShaftServiceMaker()

