#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Does that "coding:" thing actually do anything?

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
from gi.repository import GLib
# from gi.repository import Gio
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
import bszgw
# import bsz_gimp_lib


class Test (Gimp.PlugIn):
    # GimpPlugIn virtual methods
    # Not completely sure how they work
    # Why do they have 'do_' in front when it's never mentioned in the gir docs
    def do_query_procedures(self):
        # This section can also be used to provide translations,
        # but I have no idea how it works or know any other languages
        # so I'm going to ignore that for now.
        # script name as it shows up in the PDB
        return ["bszgw-test"]

    def do_create_procedure(self, name):
        # Will almost always be ImageProcedure using PLUGIN proctype
        procedure = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            # name of function if something other than 'main'
            self.main, None
        )
        # Supported colorspaces
        procedure.set_image_types("RGB*")
        # Name in menu
        procedure.set_menu_label("Template")
        # Icon. See Gimp-3.0.gir docs and gimp's icon folder for others
        # Historically plugins that use the new Gegl operations use ICON_GEGL
        # while the rest use ICON_SYSTEM_RUN
        procedure.set_icon_name(Gimp.ICON_GEGL)
        # Location in the top menu, with <Image> being root
        procedure.add_menu_path('<Image>/Beinsezii/')
        # Main is on mouseover, additional is through PDB info
        procedure.set_documentation(
            "Main Description",
            "Additional Info",
            name
        )
        # Me
        procedure.set_attribution("Beinsezii", "Beinsezii", "2020")
        return procedure

    # Taken straight from goat-exercise-py3
    def invert(self, drawable):
        # no idea
        intersect, x, y, width, height = drawable.mask_intersect()
        if intersect:
            # new Gegl op? probably to stop simultaneous operations
            Gegl.init(None)

            # Main buffer?
            buffer = drawable.get_buffer()
            # Working (temp) buffer?
            shadow_buffer = drawable.get_shadow_buffer()

            # no idea.
            graph = Gegl.Node()
            # no idea
            input = graph.create_child("gegl:buffer-source")
            # no idea why
            input.set_property("buffer", buffer)
            # invert op. child of what?
            # Maybe "Node" is like in the Blender sense where each 'child' is a
            # step in the process. child(buffer-source) is Input, child(invert)
            # is a shader/filter, child(write-buffer) is Output
            invert = graph.create_child("gegl:invert")
            # so write to buffer is its own op
            output = graph.create_child("gegl:write-buffer")
            # same as before
            output.set_property("buffer", shadow_buffer)
            # going on node theory, these could link so
            # input (buffer source) -> invert -> output (write buffer)
            input.link(invert)
            invert.link(output)
            # execute
            output.process()

            # # Not my comment. Was the only comment in the whole code block
            # This is extremely important in bindings, since we don't
            # unref buffers. If we don't explicitly flush a buffer, we
            # may left hanging forever. This step is usually done
            # during an unref().
            shadow_buffer.flush()

            # merge the temp buffer and flush everything?
            drawable.merge_shadow(True)
            drawable.update(x, y, width, height)
            Gimp.displays_flush()

    # let's try writing my own simple one based on node theory
    def color_invert(self, drawable):
        # still not sure what a 'mask_intersect' is
        # maybe it's only the selected region in the drawable?
        # intersect, x, y, width, height = drawable.mask_intersect()
        intersect, x, y, width, height = drawable.mask_intersect()
        if intersect:
            # start Gegl, fetch buffers, create node tree
            Gegl.init(None)
            buff = drawable.get_buffer()
            shadow = drawable.get_shadow_buffer()
            tree = Gegl.Node()

            # Input node
            Input = tree.create_child("gegl:buffer-source")
            # Set input source to drawable main buffer
            Input.set_property("buffer", buff)

            # Filter nodes
            Value_Invert = tree.create_child("gegl:value-invert")
            Invert = tree.create_child("gegl:invert-gamma")

            # Output node
            Output = tree.create_child("gegl:write-buffer")
            # Set input source to drawable shadow (temp) buffer
            Output.set_property("buffer", shadow)

            # connect the dots
            Input.link(Value_Invert)
            Value_Invert.link(Invert)
            Invert.link(Output)
            # run
            Output.process()

            # Flush shadow and merge to drawable
            shadow.flush()
            drawable.merge_shadow(True)

            # Flush everything else after combining the shadow
            drawable.update(x, y, width, height)
            Gimp.displays_flush()

    # Node theory seems to be the case.
    # Now let's try branching nodes
    def pop(self, drawable, thresh_high, thresh_low,
            size, opacity_high, opacity_low):
        intersect, x, y, width, height = drawable.mask_intersect()
        if intersect:
            # start Gegl, fetch buffers, create node tree
            Gegl.init(None)
            buff = drawable.get_buffer()
            shadow = drawable.get_shadow_buffer()
            tree = Gegl.Node()

            # Get input buffer
            Input = tree.create_child("gegl:buffer-source")
            Input.set_property("buffer", buff)

            # Filter nodes
            Threshold_High = tree.create_child("gegl:threshold")
            Threshold_High.set_property("value", thresh_high)
            CTA_High = tree.create_child("gegl:color-to-alpha")
            # hex was the only string I could get to work.
            CTA_High.set_property("color", Gegl.Color.new("#000000"))
            Opacity_High = tree.create_child("gegl:opacity")
            Opacity_High.set_property("value", opacity_high)

            Threshold_Low = tree.create_child("gegl:threshold")
            Threshold_Low.set_property("value", thresh_low)
            CTA_Low = tree.create_child("gegl:color-to-alpha")
            CTA_Low.set_property("color", Gegl.Color.new("#ffffff"))
            Opacity_Low = tree.create_child("gegl:opacity")
            Opacity_Low.set_property("value", opacity_low)

            Add = tree.create_child("gegl:over")
            Blur = tree.create_child("gegl:gaussian-blur")
            Blur.set_property("std-dev-x", size)
            Blur.set_property("std-dev-y", size)
            Add2 = tree.create_child("gegl:overlay")

            # Set output buffer to shadow
            Output = tree.create_child("gegl:write-buffer")
            Output.set_property("buffer", shadow)

            # base image linked to the thresholds and Add2
            Input.link(Threshold_High)
            Input.link(Threshold_Low)
            Input.link(Add2)

            # High and low thresholds, combined in "Add" to make an image
            # of alpha, pure black (low thresh shadows),
            # and highlights (high thresh highlights)
            Threshold_High.link(CTA_High)
            # seems like `.link()` is a shorthand for
            # `.connect_to("output", foo, "input")`
            CTA_High.link(Opacity_High)
            Opacity_High.connect_to("output", Add, "aux")

            Threshold_Low.link(CTA_Low)
            CTA_Low.link(Opacity_Low)
            Opacity_Low.link(Add)

            # Blur the composited thresh images and add them back to the main
            Add.link(Blur)
            Blur.connect_to("output", Add2, "aux")
            Add2.link(Output)

            Output.process()

            # Flush shadow and merge to drawable
            shadow.flush()
            drawable.merge_shadow(True)

            # Flush everything else after combining the shadow
            drawable.update(x, y, width, height)
            Gimp.displays_flush()

    # I decided to name the function called by the PDB 'main'
    def main(self, procedure, run_mode, image, drawable, args, run_data):
        # If actually clicked in the menu
        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk  # noqa: F401
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk

            pop_label = Gtk.Label("Pop Settings")
            thresh_high = bszgw.Adjuster("High Threshold",
                                         0.80, 0, 1, 0.05, 0.1, decimals=2)
            thresh_low = bszgw.Adjuster("Low Threshold",
                                        0.35, 0, 1, 0.05, 0.1, decimals=2)
            size = bszgw.Adjuster("Blur Size",
                                  25, 0, 1500, 5, 10, decimals=2)
            opacity_high = bszgw.Adjuster("High Opacity",
                                          0.25, -10, 10, 0.05, 0.1, decimals=2)
            opacity_low = bszgw.Adjuster("Low Opacity",
                                         0.1, -10, 10, 0.05, 0.1, decimals=2)

            buttons_label = Gtk.Label(
                "[I] Example Operations.",
                tooltip_text="""Invert: Same invert from goat-exercise-py3
Color invert: Value invert then invert. Testing multiple gegl 'nodes'
Pop: Adds light and dark bloom based on thresholds"""
            )

            # don't call self.widget.value directly in execute so you can run
            # the program without a UI.
            def invert_button_fn(widget):
                self.invert(drawable)
            invert_button = bszgw.Button("Invert", invert_button_fn)

            def color_invert_fn(widget):
                self.color_invert(drawable)
            color_invert_button = bszgw.Button("Color Invert", color_invert_fn)

            def pop_w(widget):
                self.pop(drawable, thresh_high.value, thresh_low.value,
                         size.value, opacity_high.value, opacity_low.value)
            pop_button = bszgw.Button("Pop", pop_w)

            box = bszgw.AutoBox([
                pop_label,
                thresh_high,
                thresh_low,
                opacity_high,
                opacity_low,
                size,
                buttons_label,
                [invert_button, color_invert_button, pop_button]
            ])
            app = bszgw.App(
                "BSZ-Template", box, hint=Gdk.WindowTypeHint.DIALOG
            )

            app.launch()

        # Don't actually really know what this does
        return procedure.new_return_values(
            Gimp.PDBStatusType.SUCCESS, GLib.Error()
        )


# have gimp load the plugin. should it be in a `if __name__ == '__main__':` ?
Gimp.main(Test.__gtype__, sys.argv)
