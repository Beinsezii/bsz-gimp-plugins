#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use these for reference on gegl operations and their properties/inputs/outputs.
http://www.gegl.org/operations/
https://gitlab.gnome.org/GNOME/gegl/-/tree/master/operations

Also build the .gir files using g-ir-doc-tool for additional insight.
If the docs don't have a description on something like class methods,
run python's help() on it to view it in the terminal.
Requires having a debug term open in gimp obvs
"""

# Uncomment as needed.
# I don't actually know if it's faster to not import some of the gi repo stuff
# since it probably gets imported later anyway ...right?
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
# gi.require_version('Babl', '0.1')
# from gi.repository import Babl
# from gi.repository import GObject
# from gi.repository import GLib
# from gi.repository import Gio
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
# import bszgw
from bsz_gimp_lib import PlugIn, ParamString, PDB

import numpy


# Main function.
def pixel_math(image, drawable, babl_format, code,):
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

        rect = Gegl.Rectangle.new(x, y, width, height)

        try:
            array = bytearray(buff.get(rect, 1.0, babl_format,
                              Gegl.AbyssPolicy.CLAMP))

            pixels = numpy.frombuffer(array)
            try:
                exec(code, globals(), locals())
            except Exception as e:
                PDB('gimp-message', str(e))

            shadow.set(rect, babl_format, bytes(array))

        # seems if babl crashes it nukes the program out of the try/except
        # will leaves this here for now to remind myself to find a better
        # solution
        except Exception as e:
            PDB('gimp-message', str(e))

        # Flush shadow buffer and combine it with main drawable
        shadow.flush()
        drawable.merge_shadow(True)

        # Update everything.
        drawable.update(x, y, width, height)
        Gimp.displays_flush()
        # }}}


# Preview function. Just runs the same thing on a copy
def pixel_math_preview(image, drawable, *args):
    # {{{
    preview_layer = drawable.copy()
    image.insert_layer(preview_layer, None, 0)
    pixel_math(image, preview_layer, *args)
    return preview_layer
    # }}}


# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Pixel Math",  # name
    pixel_math,    # function
    ParamString('BABL Format',
                value="HSLA double"),
    ParamString('Python Code',
                value="pixels[2::4] = 1 - pixels[2::4]",
                ui_multiline=True,
                ui_min_size="400x100"),
    description="Enter custom algorithms for pixel math.\n"
    "Pixels stored in NumPy array 'pixels'.",
    images="RGB*",
    preview_function=pixel_math_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
