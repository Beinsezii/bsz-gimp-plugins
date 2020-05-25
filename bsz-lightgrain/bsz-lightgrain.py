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
# from gi.repository import GObject
# from gi.repository import GLib
# from gi.repository import Gio
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from bsz_gimp_lib import PlugIn, ParamNumber, ParamBool


# Main function.
def lightgrain(image, drawable, dulling, noise_l, noise_c, noise_h, invert):
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
        # create a new node tree/graph
        tree = Gegl.Node()

        # Input buffer node using main buffer
        Input = tree.create_child("gegl:buffer-source")
        Input.set_property("buffer", buff)

        # Operations
        Noise = tree.create_child("gegl:noise-cie-lch")
        Noise.set_property('holdness', dulling)
        Noise.set_property('lightness-distance', noise_l)
        Noise.set_property('chroma-distance', noise_c)
        Noise.set_property('hue-distance', noise_h)

        Opacity = tree.create_child("gegl:opacity")

        Merge = tree.create_child("svg:src-atop")

        Component = tree.create_child("gegl:component-extract")
        Component.set_property("component", 'lab-l')

        Invert = tree.create_child("gegl:invert")

        # Output buffer node using temp buffer
        Output = tree.create_child("gegl:write-buffer")
        Output.set_property("buffer", shadow)

        Input.link(Noise)
        Input.link(Merge)
        Input.link(Component)

        Noise.link(Opacity)

        # invert by default.
        if not invert:
            Component.link(Invert)
            Invert.connect_to("output", Opacity, "aux")
        # invert option is to invert the invert aka no invert
        else:
            Component.connect_to("output", Opacity, "aux")

        Opacity.connect_to("output", Merge, "aux")
        Merge.link(Output)

        # Run the node tree
        Output.process()

        # Flush shadow buffer and combine it with main drawable
        shadow.flush()
        drawable.merge_shadow(True)

        # Update everything.
        drawable.update(x, y, width, height)
        Gimp.displays_flush()

        # }}}


# Preview function. Just runs the same thing on a copy
def lightgrain_preview(image, drawable, *args):
    # {{{
    preview_layer = drawable.copy()
    image.insert_layer(preview_layer, None, 0)
    lightgrain(image, preview_layer, *args)
    return preview_layer
    # }}}


# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Lightgrain",  # name
    lightgrain,    # function
    ParamNumber("Dulling", 2, 1, 8, integer=True),
    ParamNumber("Lightness Noise", 10, 0, 100),
    ParamNumber("Chroma Noise", 5, 0, 100),
    ParamNumber("Hue Noise", 0, 0, 180),
    ParamBool("Invert", False),
    description="LCH Noise masked to Lightness.",
    images="RGB*, GRAY*",
    preview_function=lightgrain_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
