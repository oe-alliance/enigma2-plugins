# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor


def sessionstart(reason, **kwargs):
    if reason != 0:
        return

    session = kwargs.get("session")
    if session is None:
        return

    try:
        from Components.Sources.MSNWeather import MSNWeather
    except ImportError:
        return

    if "MSNWeather" not in session.screen:
        session.screen["MSNWeather"] = MSNWeather()


def Plugins(**kwargs):
    return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart,)]
