#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared code between plugins.
Use python's help() for prettier help info.
"""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
# from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
# from gi.repository import Gio
from abc import ABC, abstractmethod

# UI imports. Can't figure out a good way to only import these
# in INTERACTIVE mode while keeping ui stuff in the params.
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import bszgw
import threading
import time


GEGL_COMPOSITORS = {
    # {{{
    "Source": "svg:src",
    "Source-Atop": "svg:src-atop",
    "Source-In": "svg:src-in",
    "Source-Out": "svg:src-out",
    "Source-Over": "svg:src-over",

    "Destination": "svg:dst",
    "Destination-Atop": "svg:dst-atop",
    "Destination-In": "svg:dst-in",
    "Destination-Out": "svg:dst-out",
    "Destination-Over": "svg:dst-over",

    "Lighten": "svg:lighten",
    "Screen": "svg:screen",
    "Color-Dodge": "svg:color-dodge",
    "Add": "gegl:add",
    "Plus": "svg:plus",

    "Darken": "svg:darken",
    "Multiply": "gegl:multiply",
    "Color-Burn": "svg:color-burn",

    "Overlay": "svg:overlay",
    "Soft-Light": "gegl:soft-light",
    "Hard-Light": "svg:hard-light",

    "Difference": "svg:difference",
    "Exclusion": "svg:exclusion",
    "Subtract": "gegl:subtract",
    "Divide": "gegl:divide",

    "Gamma": "gegl:gamma",
    "Seamless-Clone-Compose": "gegl:seamless-clone-compose",
    "Weighted-Blend": "gegl:weighted-blend",
    "Clear": "svg:clear",
    "Xor": "svg:xor",
}  # }}}


class Param(ABC):
    # {{{
    """Abstract class taken by PlugIn."""
    def __init__(self, name: str, value, ui_column: int = 0, ui_row: int = 0):
        self.name = name
        self.ui_column = ui_column
        self.ui_row = ui_row
        self.value = value
        self.widget = None

    @abstractmethod
    def create_widget(self):
        """Creates a ui widget and binds it to self.widget
Therefore, you call `param.create_widget()` on the needed params,
then later in the code you merely use `param.widget`"""
        pass

    @abstractmethod
    def connect_preview(self, function, *args):
        """Connects the widget's value change signal to the function
`pass` acceptable for widgets where it makes no sense"""
        pass

    @property
    @abstractmethod
    def ui_value(self):
        """Returns/sets ui value. Usually a shadow of bszgw.Widget.value.
'Why make this its own property instead of calling param.widget.value' you ask?
I intend to eventually use some gimp specific widgets when they're available"""
        pass

    @ui_value.setter
    @abstractmethod
    def ui_value(self, new):
        pass

    def ui_reset(self):
        """Assuming ui_value properties above are set up correctly,
there's no reason to implement this differently on a class-by-class basis."""
        self.ui_value = self.value
    # }}}


class ParamNumber(Param):
    # {{{
    """Creates a BSZGW Adjustment for numeric (float or int) parameters.
AKA a cool slider"""
    def __init__(self, name: str, value: int, min, max, integer: bool = False,
                 ui_column: int = 0, ui_row: int = 0,
                 ui_step: int = 1, ui_logarithmic: bool = False):
        super(ParamNumber, self).__init__(name, value, ui_column, ui_row)
        self.min = min
        self.max = max
        self.integer = integer
        self.ui_step = ui_step
        self.ui_logarithmic = ui_logarithmic

    def create_widget(self):
        if not self.widget:
            self.widget = bszgw.Adjuster.new(
                label=self.name,
                value=self.value,
                min_value=self.min,
                max_value=self.max,
                step_increment=self.ui_step,
                page_increment=self.ui_step,
                decimals=0 if self.integer else 2,
                logarithmic=self.ui_logarithmic
            )

    def connect_preview(self, function, *args):
        self.widget.adjustment.connect("value-changed", function, *args)

    @property
    def ui_value(self):
        return self.widget.value

    @ui_value.setter
    def ui_value(self, new):
        self.widget.value = new
    # }}}


class ParamNumberChain(Param):
    # {{{
    """Creates a chain (checkbutton for now) linking two `ParamNumber`s
Note chain ui columns are *separate* from regular ui columns
Currently only visually good for chaining across-columns."""
    def __init__(self, name: str, value: bool,
                 param1: ParamNumber, param2: ParamNumber,
                 ui_column: int = 0, ui_row: int = 0):
        super(ParamNumberChain, self).__init__(name, value, ui_column, ui_row)
        self.param1 = param1
        self.param2 = param2

    def update(self, widget, from_param, to_param):
        """copies values between params"""
        if self.widget.get_active():
            # using logarithmic scales can cause an update-loop
            # thus we *double* check that the values aren't identical
            # to avoid sending more signals
            if to_param.ui_value != from_param.ui_value:
                to_param.ui_value = from_param.ui_value

    def create_widget(self):
        if not self.widget:
            # # Currently Gimp.ChainButton() is borked
            # self.widget = Gimp.ChainButton(active=self.value)
            self.widget = bszgw.CheckBox("Link", self.value)
            self.param1.create_widget()
            self.param2.create_widget()
            self.param1.widget.adjustment.connect(
                "value-changed", self.update, self.param1, self.param2)
            self.param2.widget.adjustment.connect(
                "value-changed", self.update, self.param2, self.param1)

    def connect_preview(self, function, *args):
        pass

    @property
    def ui_value(self):
        return self.widget.get_active()

    @ui_value.setter
    def ui_value(self, new):
        self.widget.set_active(new)
    # }}}


class PreviewThread(threading.Thread):
    # {{{
    """Runs `function` after self.request_preview has been called no more than
once in the last 0.5 seconds."""
    def __init__(self, function, *args):
        super(PreviewThread, self).__init__()
        self.function = function
        self.args = args
        self.time = time.time()
        self.active = True
        self.request = True

    def run(self):
        while self.active:
            time.sleep(0.1)
            if time.time() - self.time > 0.5 and self.request:
                self.function(*self.args)
                self.time = time.time()
                self.request = False

    def request_preview(self, *args):
        self.request = True
        self.time = time.time()

    def stop(self, *args):
        self.active = False
    # }}}


class PlugIn():
    # {{{
    """Automatically creates a gimp plugin UI from given Param classes.
It's basically the old GimpFu but way cooler and more unstable.
Check out one of my scripts that uses it and you'll instantly go
\"ah it's like that\"."""
    # Get & save properties
    def __init__(self, name: str, function: callable, *params: Param,
                 description: str, alt_description: str = None,
                 preview_function: callable = None, images: str = "RGB*",
                 path: str = "<Image>/Beinsezii/", icon=Gimp.ICON_GEGL,
                 author: str = "Beinsezii", date: str = "2020"):
        # {{{
        if not alt_description:
            alt_description = description

        class Procedure(Gimp.PlugIn):
            # {{{
            """The generated pdb procedure stuff. Class inside a class.
'Why not just have PlugIn inherit Gimp.PlugIn' you ask?
because it doesn't FUKKEN work. Believe me I *really* dislike this solution,
and I initially tried inheriting. The problem is the way gimp handles the class
when you feed it. If you super the init, it just crashes, and if you don't,
it works except for the fact that your entire init block is ignored,
so self.name and everything get unset.  It's like it runs an uninitiated
PlugIn.run(), which I didn't even know was possible, since surely the
self required by run() needs to go through PlugIn's __init__, right?
If I figure out literally anything that's still an all-in-one builder solution
and looks nicer I'll replace it ASAP."""
            # GimpPlugIn virtual methods
            # Not completely sure how they work
            # Why do they have 'do_' in front
            # when it's never mentioned in the gir docs?
            def do_query_procedures(self2):
                # {{{
                # This section can also be used to provide translations,
                # but I have no idea how it works or know any other languages
                # so I'm going to ignore that for now.

                # script name as it shows up in the PDB
                return [name.lower().replace(" ", "-")]
                # }}}

            def do_create_procedure(self2, name2):
                # {{{
                # Will almost always be ImageProcedure using PLUGIN proctype
                procedure = Gimp.ImageProcedure.new(
                    self2, name2,
                    Gimp.PDBProcType.PLUGIN,
                    # name of function if something other than 'run'
                    self.run, None
                )
                # Supported colorspaces
                procedure.set_image_types(images)
                # Name in menu
                procedure.set_menu_label(name)
                # Icon. See Gimp-3.0.gir docs and gimp's icon folder for others
                # Usually plugins based on Gegl operations use ICON_GEGL
                # while the rest use ICON_SYSTEM_RUN
                procedure.set_icon_name(icon)
                # Location in the top menu, with <Image> being root
                procedure.add_menu_path(path)
                # Help text. First set is in-menu, second is PDB
                procedure.set_documentation(
                    description,
                    alt_description,
                    name2
                )
                # Maker man
                procedure.set_attribution(author, author, date)
                return procedure
                # }}}
            # }}}

        self.Procedure = Procedure
        self.name = name
        self.function = function
        self.params = params
        self.preview_function = preview_function
        # }}}

    # I decided to name the function called by the PDB procedure 'run'
    def run(self, procedure, run_mode, image, drawable, args, run_data):
        # run_mode 'NONINTERACTIVE' is if another plugin calls it through PDB
        # I don't understand the __gproperties__ things yet so am ignoring.
        if run_mode == Gimp.RunMode.NONINTERACTIVE:
            return "Non-interactive not supported."

        # run_mode 'WITH_LAST_VALS' is when you use Ctrl-F aka 'Repeat'
        # seems the gimp shelf isn't implemented yet, so kinda useless
        if run_mode == Gimp.RunMode.WITH_LAST_VALS:
            # {{{
            args = Gimp.ValueArray.new(1)
            args.insert(0, GObject.Value(GObject.TYPE_STRING,
                                         "Repeat not supported yet"))
            Gimp.get_pdb().run_procedure('gimp-message', args)
            run_mode = Gimp.RunMode.INTERACTIVE
            # }}}

        # run_mode 'INTERACTIVE' means clicked in the menu
        if run_mode == Gimp.RunMode.INTERACTIVE:
            for param in self.params:
                param.create_widget()

            # puts all ui params into a list
            # ignors ui-specific params like chains
            def ui_vals():
                # {{{
                vals = []
                for param in self.params:
                    if not isinstance(param, ParamNumberChain):
                        vals.append(param.ui_value)
                return vals
                # }}}

            # final run and destroy app.
            # maybe it should only destroy if there's no preview?
            def run_fn(widget):
                # {{{
                clear_preview()
                image.undo_group_start()
                self.function(image, drawable,
                              *ui_vals())
                image.undo_group_end()
                app.destroy()
                # }}}
            run_button = bszgw.Button("Run", run_fn)

            def reset_fn(widget):
                for param in self.params:
                    param.ui_reset()
            reset_button = bszgw.Button("Reset", reset_fn)

            buttons_list = [run_button, reset_button]

            self.preview_layers = []

            # if any preview layers, delete them and thaw
            def clear_preview(*args):
                # {{{
                if self.preview_layers:
                    for layer in self.preview_layers:
                        image.remove_layer(layer)
                    self.preview_layers = []
                    image.undo_thaw()
                # }}}

            # if preview function, get new preview layer[s] from
            # self.preview_function and add them to self.preview_layers
            def preview_fn(*args):
                # {{{
                if self.preview_function is not None:
                    clear_preview()
                    if preview_check.value:
                        image.undo_freeze()
                        result = self.preview_function(
                            image, drawable,
                            *ui_vals())
                        if isinstance(result, Gimp.Layer):
                            self.preview_layers.append(result)
                        elif isinstance(result, list):
                            self.preview_layers += result
                # }}}

            # if preview_function, creates a preview checkbox in buttons_list
            # and binds certain parts of widgets to preview_fn.
            # Might be nicer to have parameters do the binding themselves
            # in another non-abstract method that passes by default.
            if self.preview_function is not None:
                # {{{
                preview_thread = PreviewThread(preview_fn)
                preview_thread.start()
                preview_check = bszgw.CheckBox("'Live' Preview", True)
                preview_check.connect("clicked", preview_fn)
                for param in self.params:
                    param.connect_preview(preview_thread.request_preview)
                buttons_list.append((preview_check, False, False, 0))
                # }}}

            # creates buttons box.
            buttons = bszgw.AutoBox([
                buttons_list,
            ])

            # grid builder. If ui_row/column are conflicting, increment row
            # Chains have separate columns since they're meant to be in-between
            # widgets connecting them.
            # This or something similar would be a good addition to BSZGW
            # as the grids were really nice to work with.
            grid = Gtk.Grid()
            grid.props.orientation = Gtk.Orientation.VERTICAL
            # spacings. Changeable?
            grid.props.column_spacing = 15
            grid.props.row_spacing = 5
            for param in self.params:
                # {{{
                col = param.ui_column * 2
                row = param.ui_row
                if isinstance(param, ParamNumber):
                    param.widget.scale.set_hexpand(True)
                    # lets ParamNumber's sliders expand since it's not
                    # implemented in bszgw
                if isinstance(param, ParamNumberChain):
                    col += 1
                # increment until row doesn't conflict. What can go wrong?
                while True:
                    if not grid.get_child_at(col, row):
                        break
                    row += 1
                grid.attach(param.widget, col, row, 1, 1)
                # }}}
            # shove the buttons on the bottom of the first column
            grid.add(buttons)
            # create the app window with the grid
            app = bszgw.App(
                self.name, grid,
                # hints it as a pop-up instead of a full window.
                hint=Gdk.WindowTypeHint.DIALOG,
            )

            # clear preview on destroy
            def destroy_fn(*args):
                preview_thread.stop()
                preview_thread.join()
                clear_preview()
            app.connect("destroy", destroy_fn)

            # create preview before start
            app.launch()

        # Don't actually really know what this does but seems important
        return procedure.new_return_values(
            Gimp.PDBStatusType.SUCCESS, GLib.Error())
    # }}}
