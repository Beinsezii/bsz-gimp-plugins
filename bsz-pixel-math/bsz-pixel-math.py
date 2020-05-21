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
from bsz_gimp_lib import PlugIn#, ParamString

import numpy


# Main function.
def pixel_math(image, drawable, code="pixels[1::4] *= 1 - pixels[0::4] / 100", channels="CIE LCH(ab) alpha double"):
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

        # get pixel bytes
        array = bytearray(buff.get(rect, 1.0, channels,
                          Gegl.AbyssPolicy.CLAMP))

        pixels = numpy.frombuffer(array)
        exec(code, globals(), locals())

        shadow.set(rect, channels, bytes(array))

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
    # ParamString(),
    description="Reduces/increases chroma based on intensity.\n"
    "Inspired by the 'Filmic' tonemapper in Blender.",
    images="RGB*",
    preview_function=pixel_math_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)