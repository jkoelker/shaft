
from twisted.internet import protocol, reactor
from twisted.protocols import basic
from twisted.web2 import stream

commands = {"tar.gz": ["tar", "-c", "-z"],
            "tar.bz2": ["tar", "-c", "-j"],
            "zip": ["zip", "-r", "-"]
           } 

def isKnownType(type):
    return type in commands

def backup(path, type, callback=None, errback=None):
    """
    Sets up and returns a StreamProducer containing the compress stream for
    a backup.

    @param path: the path to backup
    @param type: one of C{tar.gz}, C{tar.bz2}, C{zip}
    @param callback: the callback for the ProcessStreamer's run deferred
    @param errback: the errback for the ProcessStreamer's run deferred

    type = (tar.gz, tar.bz2, zip) 
    """
    if not isKnownType(type):
        raise KeyError("Type %s is not implemented." % type)

    command = commands[type]
    process = stream.ProcessStreamer(stream.MemoryStream(''),
                                     command[0],
                                     command + [path])
    producer = stream.StreamProducer(process.outStream)

    d = process.run()
    if callback is not None:
        d.addCallback(callback)
    if errback is not None:
        d.addErrback(errback)

    return producer

