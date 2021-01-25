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
pixelbuster = ctypes.CDLL(
    os.path.dirname(os.path.realpath(__file__)) +
    "/../pixelbuster" + EXTENSIONS.get(platform)
).pixelbuster
pixelbuster.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]


FORMATS = {
    "RGBA": "RGBA double",
    "HSLA": "HSLA double",
    "XYZA": "CIE XYZ alpha double",
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
        elif babl_format == "CIE XYZ alpha double":
            channels = "xyza"
        elif babl_format == "CIE Lab alpha double":
            channels = "laba"
        elif babl_format == "CIE LCH(ab) alpha double":
            channels = "lcha"
        else:
            raise ValueError("Invalid/unsupported BABL format")

        pixels = buff.get(rect, 1.0, babl_format,
                          Gegl.AbyssPolicy.CLAMP)

        pixelbuster(code.encode('UTF-8'), channels.encode('UTF-8'), pixels, len(pixels))

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
    ParamCombo('Format', FORMATS, "HSLA double", "Pixel format", ui_preview=False),

    ParamString("Operations",
                "v = L\n"
                "L = 1\n"
                "L - v",
                "See description for code documentation",
                ui_multiline=True,
                ui_min_width=600, ui_min_height=200),

    description="""\
Pixel math. Code format is {channel} {operator} {value}
c1 + 0.5 will add 0.5 to the first channel
c1 ** 2 will raise c1 to the power of 2
c1 sqrt c1 will set c1 to the square root of itself

Everythin is case-insensitive, and *has* to be space-separated.

Available channels:
c1, c2, c3, c4. These are mapped to RGBA, HSLA, etc.

You may also use the channel letters themselves, such as
r, g, b, a

The following is a list of valid operator strings and what they translate to
"+=" | "+" | "add" => Op::Add,
"-=" | "-" | "sub" => Op::Sub,
"*=" | "*" | "mul" => Op::Mul,
"/=" | "/" | "div" => Op::Div,
"%=" | "%" | "mod" => Op::Mod,
"**" | "^" | "pow" => Op::Pow,
"=" | "set" => Op::Set,
"abs" => Op::Abs,
"acos" => Op::Acos,
"acosh" => Op::Acosh,
"asin" => Op::Asin,
"asinh" => Op::Asinh,
"atan" => Op::Atan,
"atan2" => Op::Atan2,
"atanh" => Op::Atanh,
"cbrt" => Op::Cbrt,
"ceil" => Op::Ceil,
"cos" => Op::Cos,
"cosh" => Op::Cosh,
"floor" => Op::Floor,
"log" => Op::Log,
"max" => Op::Max,
"min" => Op::Min,
"round" => Op::Round,
"sin" => Op::Sin,
"sinh" => Op::Sinh,
"sqrt" => Op::Sqrt,
"tan" => Op::Tan,
"tanh" => Op::Tanh,

In addition to channels, you can store temporary values in variables.
Available variables:
v1, v2, v3...v9
Plain 'v' is equal to v1.
Using a variable before assigning it is undefined behavior.

Finally, you have some constants:
pi => pi
e => euler's number
rand => random value from 0.0 to 1.0
""",
    images="RGBA",
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
