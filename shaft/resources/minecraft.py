from twisted.internet import defer
from twisted.web import resource, server

from shaft import backup, minecraft, settings, supervisor

import simplejson as json

import os

class Minecraft(resource.Resource):
    def render_POST(self, request):

        def started(result):
            request.finish()

        def stopped(result):
            request.finish()

        data = json.loads(request.content.getvalue())
        action = data.get("action", None)

        s = supervisor.get()

        if action is None:
             return resource.ErrorPage(http.BAD_REQUEST,
                                       http.RESPONSES[http.BAD_REQUEST],
                                       "action required")

        elif action.lower() == "start":
            d = s.startMinecraft(jar=settings.config["minecraft"]["jar"],
                                 path=settings.config["minecraft"]["home"])
            d.addCallback(started)

        elif action.lower() == "stop":
            d = s.stopMinecraft()
            d.addCallback(stopped)

        return server.NOT_DONE_YET

