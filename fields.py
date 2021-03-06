#!/usr/bin/env python
# ~ encoding: utf-8 ~
#
# Copyright (C) 2012 Max Brauer <max.brauer@inqbus.de>
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.


class CheckboxField(object):
    """
    """

    possile_modes = {
        'square': '[ ]',
        'round': '( )',
        'curly': '{ }'
    }

    def __init__(self, window, x_pos, y_pos, label, mode="square", symbol="X"):
        """ Initialize the CheckboxWidget.

        label = the text behind the checkbox

        mode = defines how the checkbox look like.
        Possible values are:
        * 'square' for [ ]
        * 'round' for ( )
        * 'curly' for { }

        symbol = a char to represent if the box is checked or not
        """
        self.window = window
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.label = label
        self.mode = self.possile_modes.get(mode, '( )')
        self.symbol = symbol
        self.active = False
        self._place_widget_in_window()

    def curly(self):
        """ Change mode to curly {}
        """
        self.mode = self.possile_modes['curly']

    def round(self):
        """ Change mode to round ()
        """
        self.mode = self.possile_modes['round']

    def square(self):
        """ Change mode to square []
        """
        self.mode = self.possile_modes['square']

    def toggle(self):
        """ Toggle active state.

        If active, set to inactive. If inactive, set to active.
        """
        self.active = not self.active
        self._place_widget_in_window()

    def _place_widget_in_window(self):
        """ Generate the String for the widget.
        """
        self.window.addstr(
            self.x_pos,
            self.y_pos,
            "%s %s" % (self.mode, self.label)
        )
        if self.active:
            self.window.addstr(
                self.x_pos,
                self.y_pos + 1,
                self.symbol
            )
        self.window.refresh()
