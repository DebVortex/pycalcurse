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

import curses

from utils import centralized_pos


class CalendarWindow(object):
    """
    """

    def __init__(self, term_size):
        xpos = term_size[1] - 24
        self.window = self.build_window(12, 24, 0, xpos)

    def build_window(self, height, width, ypos, xpos):
        """
        """
        calendar_window = curses.newwin(height, width, ypos, xpos)
        calendar_window.border()
        calendar_window.addstr(
            1,
            centralized_pos(24, "Kalender"),
            "Kalender"
        )
        calendar_window.addstr(2, 1, "----------------------")
        return calendar_window

    def refresh(self):
        self.window.refresh()
