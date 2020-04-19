#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Does that "coding:" thing actually do anything?

# Uncomment as needed.
# I don't actually know if it's faster to not import some of the gi repo stuff
# since it probably gets imported later anyway ...right?
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
# from gi.repository import Gegl
# from gi.repository import GObject
from gi.repository import GLib
# from gi.repository import Gio
import sys
import bszgw


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
        procedure.set_image_types("*")
        # Name in menu
        procedure.set_menu_label("Template")
        # Icon. See Gimp-3.0.gir docs and gimp's icon folder for others
        # Historically plugins that use the new Gegl operations use ICON_GEGL
        # while the rest use ICON_SYSTEM_RUN
        procedure.set_icon_name(Gimp.ICON_SYSTEM_RUN)
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

    # just a function to do stuff.
    def execute(self, adjuster, adjuster2, check, combo, radio, text):
        bszgw.Message(f"""Test Adjuster = {adjuster}
Test Adjuster2 = {adjuster2}
Test Check = {check}
Test Drop Down = {combo}
Test Radio Buttons = {radio}
Test Text Box = '''{text}'''
""")

    # I decided to name the function called by the PDB 'main'
    def main(self, procedure, run_mode, image, drawable, args, run_data):
        # If actually clicked in the menu
        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk

            test_adjuster = bszgw.Adjuster("Test Adjuster", 30, 0, 100, 5, 10)
            test_adjuster2 = bszgw.Adjuster(
                "Test Adjuster2", 30, 0, 100, 5, 10,
                decimals=1, slider=False
            )
            test_check = bszgw.CheckBox("Test Check Box", True)
            test_drop_down = bszgw.DropDown(
                "Test Drop Down",
                [["Choice A", "A"], ["Choice B", "B"], ["Choice C", "C"]], "A",
                enums=True
            )
            test_radio = bszgw.RadioButtons(
                "Test Radio Buttons",
                ["Choice A", "Choice B", "Choice C"], 0
            )
            test_text_box = bszgw.TextBox("Test Text Box", "Test Text\nLine 2")

            # don't call self.widget.value directly in execute so you can run
            # the program without a UI.
            def exec_button_fn(widget):
                self.execute(
                    test_adjuster.value,
                    test_adjuster2.value,
                    test_check.value,
                    test_drop_down.value,
                    test_radio.value,
                    test_text_box.value
                )

            exec_button = bszgw.Button("Execute", exec_button_fn)

            adjuster2_dropdown = bszgw.AutoBox([
                test_adjuster2,
                test_drop_down
            ])

            left_side = bszgw.AutoBox([
                test_adjuster,
                [adjuster2_dropdown, test_radio]
            ])

            right_side = bszgw.AutoBox([
                test_text_box,
                [test_check, exec_button]
            ])

            final_box = bszgw.AutoBox(
                [left_side, right_side],
                orientation=Gtk.Orientation.HORIZONTAL
            )

            test_app = bszgw.App(
                "Test App", final_box, hint=Gdk.WindowTypeHint.DIALOG
            )

            test_app.launch()

        # Don't actually really know what this does
        return procedure.new_return_values(
            Gimp.PDBStatusType.SUCCESS, GLib.Error()
        )


# have gimp load the plugin. should it be in a `if __name__ == '__main__':` ?
Gimp.main(Test.__gtype__, sys.argv)
