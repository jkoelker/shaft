from twisted.internet import defer
from twisted.web import resource, server

from shaft import backup, minecraft, settings, supervisor

import os

class World(resource.Resource):
    def __init__(self, file="world.tar.gz"):
        self.file = file
        parts = file.split('.')
        self.world = parts[0]
        self.type = '.'.join(parts[1:])

    def render_GET(self, request):
        def backup():
            def done(_):
                request.finish()

            path = os.path.join(settings.config["minecraft"]["path"],
                                self.world)

            # Punt on sending the right encoding
            request.setHeader("content-type",
                              "application/octet-stream")
            request.setHeader("content-disposition",
                              "attachemnt;filename=%s" % self.file)
            backup = backup.backup(path, type, done)
            request.registerProducer(backup, True)

        def saveAll(result):
            if not result["success"]:
                requst.finish()

            backup()

        def saveOff(result):
            if not result["success"]:
                request.finish()

            d = supervisor.get().getMinecraftProto().saveAll()
            d.addCallback(saveAll)

        if not backup.isKnownType(self.type):
            return ''

        if supervisor.get().minecraftRunning():
            d = supervisor.get().getMinecraftProto().saveOff()
            d.addCallback(saveOff)
        else:
            backup()

        return server.NOT_DONE_YET



    def render_POST(self, request):
        pass


