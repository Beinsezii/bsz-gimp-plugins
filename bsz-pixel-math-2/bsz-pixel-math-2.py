#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gegl Operation references:
http://www.gegl.org/operations/
https://gitlab.gnome.org/GNOME/gegl/-/tree/master/operations

If on Linux:
$ gegl --list-all
$ gegl --info "operation-name"

Also build the .gir files using g-ir-doc-tool for additional insight.
If the docs don't have a description on something like class methods,
run python's help() on it to view it in the terminal.
"""

# Uncomment as needed.
# I don't actually know if it's faster to not import some of the gi repo stuff
# since it probably gets imported later anyway ...right?
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
# from gi.repository import GObject
# from gi.repository import GLib
# from gi.repository import Gio
import sys
import os.path

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from bsz_gimp_lib import PlugIn, ParamCombo, ParamString

import ctypes
from sys import platform

LIBRARY = {"win32": "pixelbuster.dll", "linux": "libpixelbuster.so"}
import os.path

pixelbuster = ctypes.CDLL(
    os.path.dirname(os.path.realpath(__file__)) + "/../" +
    LIBRARY.get(platform))

pixelbuster.pb_help_ffi.restype = ctypes.c_char_p
HELP = pixelbuster.pb_help_ffi().decode('UTF-8')

pixelbuster.pixelbuster_ffi.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint,
    ctypes.c_uint
]


# Main function.
def pixel_math(image, drawable, code):
    # {{{
    # Fairly certain mask_intersect() is the current selection mask
    intersect, x, y, width, height = drawable.mask_intersect()
    if intersect:
        # start Gegl
        Gegl.init(None)
        # fetch main buffer
        buff = drawable.get_buffer()

        # fetch shadow aka "temp" buffer
        shadow = drawable.get_shadow_buffer()

        # create working rectangle area using mask intersect.
        rect = Gegl.Rectangle.new(x, y, width, height)

        pixels = buff.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.CLAMP)

        pixelbuster.pixelbuster_ffi(
            code.encode('UTF-8'),
            "srgba".encode('UTF-8'),
            pixels,
            width,
            len(pixels),
        )

        shadow.set(rect, "RGBA float", bytes(pixels))

        # Flush shadow buffer and combine it with main drawable
        shadow.flush()
        drawable.merge_shadow(True)

        # Update everything.
        drawable.update(x, y, width, height)
        Gimp.displays_flush()
        # }}}


# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Pixel Math 2",  # name
    pixel_math,  # function
    ParamString("Operations",
                "g * r",
                "See description for documentation",
                ui_multiline=True,
                ui_min_width=300,
                ui_min_height=300),
    description=HELP,
    images="*",
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
