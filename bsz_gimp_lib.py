#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared code between plugins
"""

# import gi
# gi.require_version('Gimp', '3.0')
# from gi.repository import Gimp
# gi.require_version('Gegl', '0.4')
# from gi.repository import Gegl
# from gi.repository import GObject
# from gi.repository import GLib
# from gi.repository import Gio
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
# import bszgw

# just ripped this from the html. Should change the keys
GEGL_COMPOSITORS = {
    "Source": "svg:src",
    "Source-Atop": "svg:src-atop",
    "Source-In": "svg:src-in",
    "Source-Out": "svg:src-out",
    "Source-Over": "svg:src-over",

    "Destination": "svg:dst",
    "Destination-Atop": "svg:dst-atop",
    "Destination-In": "svg:dst-in",
    "Destination-Out": "svg:dst-out",
    "Destination-Over": "svg:dst-over",

    "Lighten": "svg:lighten",
    "Screen": "svg:screen",
    "Color-Dodge": "svg:color-dodge",
    "Add": "gegl:add",
    "Plus": "svg:plus",

    "Darken": "svg:darken",
    "Multiply": "gegl:multiply",
    "Color-Burn": "svg:color-burn",

    "Overlay": "svg:overlay",
    "Soft-Light": "gegl:soft-light",
    "Hard-Light": "svg:hard-light",

    "Difference": "svg:difference",
    "Exclusion": "svg:exclusion",
    "Subtract": "gegl:subtract",
    "Divide": "gegl:divide",

    "Gamma": "gegl:gamma",
    "Seamless-Clone-Compose": "gegl:seamless-clone-compose",
    "Weighted-Blend": "gegl:weighted-blend",
    "Clear": "svg:clear",
    "Xor": "svg:xor",
}
