from ConfigParser import SafeConfigParser

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

## This is not async do not modify or call these funcitons after startup
DEFAULT_CONFIG_FILE = "/etc/shaft.conf"
DEFAULT_CONFIG = """
[web]
port = 6969
log = /var/log/shaft_web.log
user = ababa
sesame = taugepeeph4ChuteilooshohmienoQu4Ajul4JohNge1ahfa5haiqui

[ssh]
port = 2222

[minecraft]
jar = /home/minecraft/minecraft_server.jar
path = /home/minecraft
"""

__config = SafeConfigParser()
__config.readfp(StringIO(DEFAULT_CONFIG))

config = __config._sections

def loadConfig(file=DEFAULT_CONFIG_FILE):
    __config.read(file)

