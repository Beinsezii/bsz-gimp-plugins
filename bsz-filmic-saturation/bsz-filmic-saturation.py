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
from bsz_gimp_lib import PlugIn, ParamNumber, ParamNumberChain

import struct
import time


# Main function.
def filmic_saturation(image, drawable):
    # {{{
    # Fairly certain mask_intersect() is the current selection mask
    intersect, x, y, width, height = drawable.mask_intersect()
    if intersect:
        t = time.perf_counter()

        # start Gegl
        Gegl.init(None)
        # fetch main buffer
        buff = drawable.get_buffer()

        # fetch shadow aka "temp" buffer
        shadow = drawable.get_shadow_buffer()

        rect = Gegl.Rectangle.new(x, y, width, height)

        pixels = buff.get(rect, 1.0, "CIE LCH(ab) alpha double",
                          Gegl.AbyssPolicy.CLAMP)
        pixels_iter = (pixels[x:x + 32] for x in range(0, len(pixels), 32))
        new_pixels = bytearray()

        for pixel in pixels_iter:
            l, c, h, a = struct.unpack('dddd', pixel)
            c = c - (l * c) / 100
            new_pixels += struct.pack('dddd', l, c, h, a)

        shadow.set(rect, "CIE LCH(ab) alpha double", bytes(new_pixels))

        # # create a new node tree/graph
        # tree = Gegl.Node()

        # # Input buffer node using main buffer
        # Input = tree.create_child("gegl:buffer-source")
        # Input.set_property("buffer", buff)

        # Invert = tree.create_child("gegl:invert")

        # # Output buffer node using temp buffer
        # Output = tree.create_child("gegl:write-buffer")
        # Output.set_property("buffer", shadow)

        # Input.link(Invert)

        # Invert.link(Output)

        # # Run the node tree
        # Output.process()

        # Flush shadow buffer and combine it with main drawable
        shadow.flush()
        drawable.merge_shadow(True)

        # Update everything.
        drawable.update(x, y, width, height)
        Gimp.displays_flush()

        print(time.perf_counter() - t)
        # }}}


# Preview function. Just runs the same thing on a copy
def filmic_saturation_preview(image, drawable, *args):
    # {{{
    preview_layer = drawable.copy()
    image.insert_layer(preview_layer, None, 0)
    filmic_saturation(image, preview_layer, *args)
    return preview_layer
    # }}}


# Parameters from bsz_gimp_lib
# {{{

# }}}

# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Filmic Saturation",  # name
    filmic_saturation,    # function
    # ,     # *params
    description="WIP",
    alt_description="Alt Desc WIP",
    images="RGB*",
    # preview_function=dual_bloom_2_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
