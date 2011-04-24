from twisted.web import resource

from shaft.resources import minecraft, world

def getRoot():
    root = resource.Resource()
    root.putChild("minecraft", minecraft.Minecraft())
    root.putChild("world", world.World())

    return root
