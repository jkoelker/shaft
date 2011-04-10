from twisted.web import resource

from shaft.resources import minecraft

def getRoot():
    root = resource.Resource()
    root.putChild("minecraft", minecraft.Minecraft())

    return root
