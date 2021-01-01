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
EXTENSIONS = {"win32": ".dll", "linux": ".so"}
PM2 = ctypes.CDLL(
    os.path.dirname(os.path.realpath(__file__)) +
    "/pixel_math_2" + EXTENSIONS.get(platform)
).pixel_math_2
PM2.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]


FORMATS = {
    "RGBA": "RGBA double",
    "HSLA": "HSLA double",
    "LABA": "CIE Lab alpha double",
    "LCHA": "CIE LCH(ab) alpha double",
}


# Main function.
def pixel_math(image, drawable, babl_format, code):
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

        if babl_format == "RGBA double":
            channels = "rgba"
        elif babl_format == "HSLA double":
            channels = "hsla"
        elif babl_format == "CIE Lab alpha double":
            channels = "laba"
        elif babl_format == "CIE LCH(ab) alpha double":
            channels = "lcha"
        else:
            raise ValueError("Invalid/unsupported BABL format")

        code = code.casefold()

        for num, c in enumerate(channels):
            code = code.replace(f"{c} ", f"c{num+1} ")
            code = code.replace(f"{c}\n", f"c{num+1}\n")
            # since everything is whitespace separated in rust
            # you can just search for whitespace to avoid
            # double-replacing 'c'

        pixels = buff.get(rect, 1.0, babl_format,
                          Gegl.AbyssPolicy.CLAMP)

        PM2(code.encode('UTF-8'), pixels, len(pixels))

        shadow.set(rect, babl_format, bytes(pixels))

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
    pixel_math,    # function
    ParamCombo('Format', FORMATS, "HSLA double", "Pixel format"),

    ParamString("Operations",
                "v1 = L\n"
                "L = 1\n"
                "L - v1",
                "See description for code documentation",
                ui_multiline=True,
                ui_min_width=600, ui_min_height=200),

    description="""\
Pixel math. Code format is {channel} {operator} {value}
So c1 + 0.5 will add 0.5 to the first channel.

Available channels:
c1, c2, c3, c4 (always alpha). These are mapped to RGBA, HSLA, etc.

You may also use the channel letters themselves, such as
r, g, b, a

Supported operators are
= or ==  : set/assign
+ or +=  : add
- or -=  : subtract
* or *=  : multiply
/ or /=  : divide

In addition to channels, you can store temporary values in variables.
Available variables:
v1, v2, v3...v9
""",
    images="RGB*, GRAY*",
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
