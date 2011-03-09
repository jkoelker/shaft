from twisted.python import log
from twisted.runner import procmon
from twisted.internet import defer, error, task, reactor as _reactor

from shaft import minecraft

class Supervisor(procmon.ProcessMonitor):
    restartTime = 5

    def __init__(self, reactor=_reactor):
        procmon.ProcessMonitor.__init__(self, reactor)
        self.minecrafts = {}

    # Override the startProcess command so we can use our custom
    # protocol and path

    def startProcess(self, name):
        log.msg("Starting Process: %s" % name)
        if name in self.protocols:
            log.msg("Already have protocol for %s" % name)
            return

        args, uid, gid, env, path = self.processes[name]

        proto = minecraft.MinecraftServerProtocol()
        proto.service = self
        proto.name = name
        self.protocols[name] = proto
        self.timeStarted[name] = self._reactor.seconds()
        return defer.maybeDeferred(self._reactor.spawnProcess, proto,
                                   args[0], args, uid=uid,
                                   gid=gid, env=env, path=path)

    # Set the doc of the function to the overridden doc
    startProcess.__doc__ = procmon.ProcessMonitor.startProcess.__doc__

    # Override addProcess so we store the path as well   
    def addProcess(self, name, args, uid=None, gid=None, env={},
                   path=None):
        if name in self.processes:
            raise KeyError("remove %s first" % (name,))
        self.processes[name] = args, uid, gid, env, path
        self.delay[name] = self.minRestartDelay
        if self.running:
            return self.startProcess(name)

    # Ghetto splice in our new params to the doc
    addProcess.__doc__ = procmon.ProcessMonitor.addProcess.__doc__ + \
                         "@param path: The path to start the launched " + \
                            "process in.  If C{None} the current " + \
                            "directory is used." + \
                         "@type path: C{str}\n"

    def _forceStopProcess(self, proc, name):
        try:
            proc.signalProcess('KILL')
            del self.murder[name]
        except error.ProcessExitedAlready:
            pass

    def _stopProcess(self, result, name):
        success = result.get('success', False)
        proto = self.protocols.get(name, None)

        if not success and proto is not None:
            stopDeferred = proto.stopServer()
            stopDeferred.addCallback(self._stopProcess, name)
            return

        if proto is not None:
            proc = proto.transport
            try:
                proc.signalProcess('TERM')
            except error.ProcessExitedAlready:
                pass
            else:
                self.murder[name] = self._reactor.callLater(
                                            self.killTime,
                                            self._forceStopProcess,
                                            proc, name)
            if name in self.processes:
                del self.processes[name]

            if name in self.protocols:
                del self.protocols[name]

        return result

    def stopProcess(self, name):
        if name not in self.processes:
            raise KeyError("Unrecognized process name: %s" % (name,))

        proto = self.protocols.get(name, None)

        if proto is not None:
            stopDeferred = proto.stopServer()
            stopDeferred.addCallback(self._stopProcess, name)
            return stopDeferred
        
        d = defer.Deferred()
        d.callback({'success': False})
        return d
        

    # Set the doc of the function to the overridden doc
    stopProcess.__doc__ = procmon.ProcessMonitor.stopProcess.__doc__

    def startMinecraft(self, jar, java="java", name='minecraft',
                       uid=None, gid=None, env={}, path=None):
        """
        Starts a new minecraft server instance in the L{Supervisor}.

        @raises: C{KeyError} if the supervisor already has an
            instance already running with the same name
        """
        self.minecrafts[name] = jar, java, uid, gid, env, path
        args = [java, "-jar", jar, "nogui"]
        return defer.maybeDeferred(self.addProcess, name=name, args=args,
                                   uid=uid, gid=gid, env=env, path=path)

    def restartMinecraft(self, name='minecraft'):
        if name not in self.minecrafts:
            raise KeyError("start %s first" % name)

        def start():
            jar, java, uid, gid, env, path = self.minecrafts[name]
            return task.deferLater(self._reactor, self.restartTime,
                                   self.startMinecraft, jar, java,
                                   name, uid, gid, env, path)
        
        if name in self.processes:
            stopDeferred = self.stopProcess(name)
            stopDeferred.addCallback(lambda _: start())
            return stopDeferred

        else:
            return start()

    def stopMinecraft(self, name='minecraft'):
        return self.stopProcess(name)


