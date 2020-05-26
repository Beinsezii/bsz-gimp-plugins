#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared code between plugins.
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
from gi.repository import Gtk  # noqa: F401
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import bszgw
import threading
import time


def PDB(procedure: str, *args):
    # {{{
    argsv = Gimp.ValueArray.new(len(args))
    for num, arg in enumerate(args):
        if isinstance(arg, str):
            gtype = GObject.TYPE_STRING
        else:
            raise ValueError("PDB Type not supported")

        argsv.insert(num, GObject.Value(gtype, arg))
    return Gimp.get_pdb().run_procedure(procedure, argsv)
    # }}}


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
    def __init__(self, name: str, value,
                 description: str = "",
                 ui_column: int = 0, ui_row: int = 0,
                 ui_width: int = 1, ui_height: int = 1):
        self.name = name
        if not description:
            self.description = name
        else:
            self.description = description
        self.ui_column = ui_column
        self.ui_row = ui_row
        self.ui_width = ui_width
        self.ui_height = ui_height
        self.value = value
        self.__widget = None

    @abstractmethod
    def connect_preview(self, function, *args):
        """Connects the widget's value change signal to the function
`pass` acceptable for widgets where it makes no sense"""
        pass

    @abstractmethod
    def create_widget(self):
        """Returns a new widget for param.
Mostly used internally for widget property."""
        pass

    def ui_reset(self):
        """Assuming ui_value properties are set up correctly,
there's no reason to implement this differently on a class-by-class basis."""
        self.ui_value = self.value

    @property
    @abstractmethod
    def gproperty(self):
        """Returns a dictionary containing the gproperty for the parameter."""
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

    @property
    def widget(self):
        """Readonly property containing the ui widget.
Will create the widget on first read."""
        if self.__widget is None:
            self.__widget = self.create_widget()
        return self.__widget
    # }}}


class ParamBool(Param):
    # {{{
    """Creates a BSZGW CheckButton for booleans"""
    def __init__(self, name: str, value: bool,
                 description: str = "",
                 ui_column: int = 0, ui_row: int = 0,
                 ui_width: int = 1, ui_height: int = 1):
        super(ParamBool, self).__init__(name, value,
                                        description,
                                        ui_column, ui_row,
                                        ui_width, ui_height)

    def connect_preview(self, function, *args):
        self.widget.connect("clicked", function, *args)

    def create_widget(self):
        return bszgw.CheckButton(self.name, self.value,
                                 tooltip=self.description)

    @property
    def gproperty(self):
        return {self.name.lower().replace(' ', '-'):
                (bool,
                 self.name,
                 self.description,
                 self.value,
                 GObject.ParamFlags.READWRITE)
                }

    @property
    def ui_value(self):
        return self.widget.value

    @ui_value.setter
    def ui_value(self, new):
        self.widget.value = new
    # }}}


class ParamCombo(Param):
    # {{{
    """Creates a BSZGW ComboBox from a dictionary"""
    def __init__(self, name: str, dictionary: dict, value,
                 description: str = "",
                 ui_column: int = 0, ui_row: int = 0,
                 ui_width: int = 1, ui_height: int = 1):
        super(ParamCombo, self).__init__(name, value,
                                         description,
                                         ui_column, ui_row,
                                         ui_width, ui_height)
        self.dictionary = dictionary

    def connect_preview(self, function, *args):
        self.widget.connect("changed", function, *args)

    def create_widget(self):
        return bszgw.ComboBox.new(
            self.dictionary,
            self.value,
            tooltip=self.description,
            show_ids=False,
        )

    @property
    def gproperty(self):
        return {self.name.lower().replace(' ', '-'):
                (str,
                 self.name,
                 self.description,
                 self.value,
                 GObject.ParamFlags.READWRITE)
                }

    @property
    def ui_value(self):
        return self.widget.value

    @ui_value.setter
    def ui_value(self, new):
        self.widget.value = new
    # }}}


class ParamNumber(Param):
    # {{{
    """Creates a BSZGW Adjustment for numeric (float or int) parameters.
AKA a cool slider"""
    def __init__(self, name: str, value: int, min, max,
                 description: str = "",
                 ui_column: int = 0, ui_row: int = 0,
                 ui_width: int = 1, ui_height: int = 1,
                 integer: bool = False,
                 ui_step: int = 1, ui_logarithmic: bool = False):
        super(ParamNumber, self).__init__(name, value,
                                          description,
                                          ui_column, ui_row,
                                          ui_width, ui_height)
        self.min = min
        self.max = max
        self.integer = integer
        self.ui_step = ui_step
        self.ui_logarithmic = ui_logarithmic

    def connect_preview(self, function, *args):
        self.widget.adjustment.connect("value-changed", function, *args)

    def create_widget(self):
        return bszgw.Adjuster.new(
            label=self.name,
            value=self.value,
            tooltip=self.description,
            min_value=self.min,
            max_value=self.max,
            step_increment=self.ui_step,
            page_increment=self.ui_step,
            decimals=0 if self.integer else 2,
            logarithmic=self.ui_logarithmic
        )

    @property
    def gproperty(self):
        return {self.name.lower().replace(' ', '-'):
                (int if self.integer else float,
                 self.name,
                 self.description,
                 self.min, self.max, self.value,
                 GObject.ParamFlags.READWRITE)
                }

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
                 description: str = "",
                 ui_column: int = 0, ui_row: int = 0,
                 ui_width: int = 1, ui_height: int = 1):
        super(ParamNumberChain, self).__init__(name, value,
                                               description,
                                               ui_column, ui_row,
                                               ui_width, ui_height)
        self.param1 = param1
        self.param2 = param2

    def create_widget(self):
        self.param1.widget.adjustment.connect(
            "value-changed", self.update, self.param1, self.param2)
        self.param2.widget.adjustment.connect(
            "value-changed", self.update, self.param2, self.param1)
        return bszgw.CheckButton("Link", self.value,
                                 tooltip=self.description)
        # # Currently Gimp.ChainButton() is borked
        # return Gimp.ChainButton(active=self.value)

    def connect_preview(self, function, *args):
        pass

    def update(self, widget, from_param, to_param):
        """copies values between params"""
        if self.widget.get_active():
            # using logarithmic scales can cause an update-loop
            # thus we *double* check that the values aren't identical
            # to avoid sending more signals
            if to_param.ui_value != from_param.ui_value:
                to_param.ui_value = from_param.ui_value

    @property
    def gproperty(self):
        return None

    @property
    def ui_value(self):
        return self.widget.get_active()

    @ui_value.setter
    def ui_value(self, new):
        self.widget.set_active(new)
    # }}}


class ParamString(Param):
    # {{{
    """Creates a BSZGW Entry for inputting text."""
    def __init__(self, name: str, value: str,
                 description: str = "",
                 ui_column: int = 0, ui_row: int = 0,
                 ui_width: int = 1, ui_height: int = 1,
                 ui_multiline: bool = False,
                 ui_min_width: int = 300, ui_min_height: int = 100):
        super(ParamString, self).__init__(name, value,
                                          description,
                                          ui_column, ui_row,
                                          ui_width, ui_height)
        self.ui_multiline = ui_multiline
        self.ui_min_width = ui_min_width
        self.ui_min_height = ui_min_height

    def connect_preview(self, function, *args):
        pass
        # self.widget.connect("value-changed", function, *args)

    def create_widget(self):
        return bszgw.Entry(
            label=self.name,
            value=self.value,
            # tooltip=self.description,  # TODO not implemented
            multi_line=self.ui_multiline,
            min_width=self.ui_min_width,
            min_height=self.ui_min_height
        )

    @property
    def gproperty(self):
        return {self.name.lower().replace(' ', '-'):
                (str,
                 self.name,
                 self.name,  # desc?
                 self.value,
                 GObject.ParamFlags.READWRITE)
                }

    @property
    def ui_value(self):
        return self.widget.value

    @ui_value.setter
    def ui_value(self, new):
        self.widget.value = new
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
                 preview_function: callable = None,
                 procedure_name: str = None, images: str = "RGB*",
                 path: str = "<Image>/Beinsezii/", icon=Gimp.ICON_GEGL,
                 authors: str = "Beinsezii", copyright: str = None,
                 date: str = "2020"):
        # {{{
        if not procedure_name:
            procedure_name = name.lower().replace(" ", "-")
        if not alt_description:
            alt_description = description
        if not copyright:
            copyright = authors
        gproperties = {}
        for param in params:
            gproperty = param.gproperty
            if gproperty:
                gproperties.update(gproperty)

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

            # basically create a dict of parameters the plugin takes
            __gproperties__ = gproperties

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
                return [procedure_name]
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
                procedure.set_attribution(authors, copyright, date)

                # add the gproperties to the procedures
                for key in gproperties:
                    procedure.add_argument_from_property(self2, key)

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
    def run(self, procedure, run_mode, image, drawable, argsv, run_data):
        # convert the ValueArray into a regular list
        args = [argsv.index(x) for x in range(argsv.length())]

        # if no params and therefore no widgets always run non-interactive
        if self.params == ():
            run_mode = Gimp.RunMode.NONINTERACTIVE

        # run_mode 'NONINTERACTIVE' is if another plugin calls it through PDB
        if run_mode == Gimp.RunMode.NONINTERACTIVE:
            self.function(image, drawable, *args)

        # run_mode 'WITH_LAST_VALS' is when you use Ctrl-F aka 'Repeat'
        # seems the gimp shelf isn't implemented yet?
        if run_mode == Gimp.RunMode.WITH_LAST_VALS:
            # {{{
            PDB("gimp-message", "Repeate not supported yet")
            run_mode = Gimp.RunMode.INTERACTIVE
            # }}}

        # run_mode 'INTERACTIVE' means clicked in the menu
        if run_mode == Gimp.RunMode.INTERACTIVE:
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

            self.preview_layers = []

            # if any preview layers, delete them and thaw
            # TODO: hide base layers when preview is up
            def clear_preview(*args):
                # {{{
                if self.preview_layers:
                    for layer in self.preview_layers:
                        image.remove_layer(layer)
                    self.preview_layers = []
                    while not image.undo_is_enabled():
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

            # creates preview_check, starts the live preview thread,
            # and has the widgets connect to function
            if self.preview_function is not None:
                # {{{
                preview_thread = PreviewThread(preview_fn)
                preview_thread.start()
                preview_check = bszgw.CheckButton("'Live' Preview", True)
                preview_check.connect("clicked", preview_fn)
                for param in self.params:
                    param.connect_preview(preview_thread.request_preview)
                # }}}
            else:
                preview_check = None

            # creates buttons box to avoid attaching buttons directly.
            # reduces buggery with grid attach widths.
            buttons = bszgw.AutoBox([
                [run_button, reset_button]
            ])

            # Creates the main grid using attach_all for collision detection.
            # Chains have separate columns since they're meant to be in-between
            # widgets connecting them.
            grid = bszgw.Grid()
            GC = bszgw.GridChild
            children = []
            for param in self.params:
                col = param.ui_column * 2
                if isinstance(param, ParamNumberChain):
                    col += 1
                children.append(GC(param.widget,
                                   col_off=col, row_off=param.ui_row,
                                   width=param.ui_width,
                                   height=param.ui_height))
            grid.attach_all(*children, preview_check, buttons)
            grid.props.margin = 10

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
