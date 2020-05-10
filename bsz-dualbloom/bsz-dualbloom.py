#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use this for reference on gegl operations and their properties/inputs/outputs.
http://www.gegl.org/operations/

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
from bsz_gimp_lib import GEGL_COMPOSITORS, ParamNumber, ParamNumberChain, \
    ParamCombo, PlugIn


# Main function.
def dual_bloom(self, drawable, thresh_high, thresh_low,
               size_high, size_low, opacity_high, opacity_low,
               composite_high="gegl:overlay", composite_low="gegl:overlay"):
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

        # Filter nodes for high threshold. See gegl.org/operations
        Threshold_High = tree.create_child("gegl:threshold")
        Threshold_High.set_property("value", thresh_high)
        CTA_High = tree.create_child("gegl:color-to-alpha")
        # hex was the only string I could get to work.
        CTA_High.set_property("color", Gegl.Color.new("#000000"))
        Blur_High = tree.create_child("gegl:gaussian-blur")
        Blur_High.set_property("std-dev-x", size_high)
        Blur_High.set_property("std-dev-y", size_high)
        Opacity_High = tree.create_child("gegl:opacity")
        Opacity_High.set_property("value", opacity_high)
        Comp_High = tree.create_child(composite_high)

        # Filter nodes for low threshold
        Threshold_Low = tree.create_child("gegl:threshold")
        Threshold_Low.set_property("value", thresh_low)
        CTA_Low = tree.create_child("gegl:color-to-alpha")
        CTA_Low.set_property("color", Gegl.Color.new("#ffffff"))
        Blur_Low = tree.create_child("gegl:gaussian-blur")
        Blur_Low.set_property("std-dev-x", size_low)
        Blur_Low.set_property("std-dev-y", size_low)
        Opacity_Low = tree.create_child("gegl:opacity")
        Opacity_Low.set_property("value", opacity_low)
        Comp_Low = tree.create_child(composite_low)

        # Output buffer node using temp buffer
        Output = tree.create_child("gegl:write-buffer")
        Output.set_property("buffer", shadow)

        # base image linked to the thresholds and Comp_Low
        Input.link(Threshold_High)
        Input.link(Threshold_Low)
        Input.link(Comp_Low)

        # connect the low nodes to each other and Comp_High
        Threshold_Low.link(CTA_Low)
        CTA_Low.link(Blur_Low)
        Blur_Low.link(Opacity_Low)
        # Seems like `.link(node)` is shorthand for
        # `.connect_to("output", node, "input")`
        Opacity_Low.connect_to("output", Comp_Low, "aux")
        Comp_Low.link(Comp_High)

        # connect the high nodes to each other and Output
        Threshold_High.link(CTA_High)
        CTA_High.link(Blur_High)
        Blur_High.link(Opacity_High)
        Opacity_High.connect_to("output", Comp_High, "aux")
        Comp_High.link(Output)

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
def dual_bloom_preview(image, drawable, *args):
    # {{{
    preview_layer = drawable.copy()
    image.insert_layer(preview_layer, None, 0)
    dual_bloom(image, preview_layer, *args)
    return preview_layer
    # }}}


# Parameters from bsz_gimp_lib
# {{{
thresh_high = ParamNumber("Threshold High", 0.80, 0, 1,
                          ui_step=0.1)
thresh_low = ParamNumber("Threshold Low", 0.30, 0, 1,
                         ui_step=0.1, ui_column=1)

size_high = ParamNumber("Blur Size High", 10, 0, 1500,
                        ui_logarithmic=True)
size_low = ParamNumber("Blur Size Low", 10, 0, 1500,
                       ui_logarithmic=True, ui_column=1)
size_chain = ParamNumberChain("Link Blurs", True, size_high, size_low,
                              ui_row=1)

opacity_high = ParamNumber("Opacity High", 0.2, -10, 10)
opacity_low = ParamNumber("Opacity Low", 0.1, -10, 10,
                          ui_column=1)

composite_high = ParamCombo("Composite High", GEGL_COMPOSITORS, "svg:overlay")
composite_low = ParamCombo("Composite Low", GEGL_COMPOSITORS, "svg:overlay",
                           ui_column=1)
# }}}


# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Dual Bloom",  # name
    dual_bloom,    # function
    thresh_high,   # *params
    thresh_low,
    size_high,
    size_low,
    opacity_high,
    opacity_low,
    composite_high,
    composite_low,
    size_chain,
    description="Provides light and dark bloom using thresholds.",
    alt_description="Provides light and dark bloom using thresholds.",
    images="RGB*, GRAY*",
    preview_function=dual_bloom_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
