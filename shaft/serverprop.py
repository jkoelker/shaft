# I'd love to use configobj here but, its probably overkill, and the
# minecraft server is extremely finiky about the format

from twisted.internet import defer, threads

from datetime import datetime

def fileToDict(file):
    """
    @param file: a file-like object open for read or a string path
    @return: deferred that will contain the dict
    """

    # Since we're going to run in a thread anyway we'll parse it 
    # synchronously there
    def parseFile(file):
        convertBool = lambda x: x.lower() == "true"
        convertInt = lambda x: int(x)

        conf = {}
        lines = file.readlines()
        for line in lines():
            if line[0] == '#':
                continue
            key, value = (x.strip() for x in line.strip().split('=')[:2])
            value = [x.strip() for x in value.split('#')][0]

            if key in ("hellworld", "spawn-monsters", "monsters",
                       "online-mode", "spawn-animals", "no-animals",
                       "pvp", "white-list"):
                value = convertBool(value)

            elif key in ("max-players", "server-port"):
                value = convertInt(value)

            conf[key] = value

        file.close()
        return conf

    if isinstance(file, basestring):
        file = open(file, 'r')

    return threads.deferToThread(parseFile, file)

def confToFile(conf, file):
    """
    @param conf: config dict containing only strings, bools, or ints
    @param file: a file-like object open for write of a string path

    @return: deferred that will return None when the file is written
    """

    def writeFile(conf, file):
        convertBool = lambda x: ("%s" % x).lower()
        convertInt = lambda x: "%s" % x

        # We write out a header so we look legit ;)
        file.write("#Minecraft server properties\n")
        file.write(datetime.now().strftime("%c") + '\n')

        for key in conf:
            value = conf[key]

            if key in ("hellworld", "spawn-monsters", "monsters",
                       "online-mode", "spawn-animals", "no-animals",
                       "pvp", "white-list"):
                value = convertBool(value)

            elif key in ("max-players", "server-port"):
                value = convertInt(value)

            file.write("%s=%s\n")

        file.close()

    if isinstance(file, basestring):
        file = open(file, 'w')

    return threads.deferToThread(writeFile, conf, file)

