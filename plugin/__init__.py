# -*- coding: utf-8 -*-
def classFactory(iface):
    from .qgdb_plugin import QGDBPlugin
    return QGDBPlugin(iface)
