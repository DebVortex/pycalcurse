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

import locale
locale.setlocale(locale.LC_ALL, "")

import curses

from fields import CheckboxField


class AbstractBoxWidget(object):
    """
    """

    def __init__(self, height, width, x_pos, y_pos, label):
        box = curses.newwin(height, width, x_pos, y_pos)
        box.border()
        box.addstr(1, 1, "".join([" " for x in range(width - 2)]), curses.A_REVERSE)
        box.addstr(1, 1, label, curses.A_REVERSE)
        return box


class InfoBoxWidget(AbstractBoxWidget):
    """
    """

    def __init__(self, height, width, x_pos, y_pos, label, text):
        info_win = AbstractBoxWidget.__init__(self, height, width, x_pos, y_pos, label)
        info_win.addstr(2, 1, text)
        info_win.getch()
        del self


class KeyInputWidget(AbstractBoxWidget):
    """
    """

    def __init__(self, height, width, x_pos, y_pos, label, text):
        self.key_input_win = AbstractBoxWidget.__init__(self, height, width, x_pos, y_pos, label)
        if type(text) == list:
            line = 2
            for text_line in text:
                self.key_input_win.addstr(line, 1, text_line)
                line += 1
        else:
            self.key_input_win.addstr(2, 1, text)

    def getch(self):
        return self.key_input_win.getch()


class InputBoxWidget(AbstractBoxWidget):
    """
    """

    def __init__(self, height, width, x_pos, y_pos, label, input_start_line=2, input_start_col=1):
        self.input_win = AbstractBoxWidget.__init__(self, height, width, x_pos, y_pos, label)
        self.input_win.touchwin()
        self.input_win.move(input_start_line, input_start_col)

    def getstr(self):
        self.input_win.refresh()
        curses.echo()
        input_text = self.input_win.getstr()
        curses.noecho()
        return input_text


class MultiCheckboxWidget(AbstractBoxWidget):
    """
    """

    def __init__(self, curses_scr, height, width, x_pos, y_pos, label, checkbox_information):
        """
        """
        self.curses_scr = curses_scr
        self.input_win = AbstractBoxWidget.__init__(self, height, width, x_pos, y_pos, label)
        self.checkboxes = self._build_checkboxes(checkbox_information)
        self._navigate_and_toggle()

    def _build_checkboxes(self, checkbox_information):
        """
        """
        checkboxes = {}
        for pos in checkbox_information:
            checkbox = CheckboxField(
                self.input_win,
                pos,
                1,
                checkbox_information[pos][1]
            )
            checkboxes[pos] = [checkbox, checkbox_information[pos][0]]
        return checkboxes

    def _navigate_and_toggle(self):
        first_pos = min(self.checkboxes.keys())
        last_pos = max(self.checkboxes.keys())
        curent_pos = first_pos
        self.input_win.move(curent_pos, 2)
        self.input_win.refresh()
        curses.curs_set(2)
        x = 0
        while x != 10:  # use 10 for 'Enter', because curses.KEY_ENTER is 343
                        # but getch get 10 from the key
            x = self.curses_scr.getch()
            if x == 32:  # use 32 for 'Space', because there is no curses.KEY_SPACE
                self.checkboxes[curent_pos][0].toggle()
                self.input_win.move(curent_pos, 2)
                self.input_win.refresh()
            if x == curses.KEY_UP:
                if curent_pos != first_pos:
                    curent_pos -= 1
                    self.input_win.move(curent_pos, 2)
                    self.input_win.refresh()
            if x == curses.KEY_DOWN:
                if curent_pos != last_pos:
                    curent_pos += 1
                    self.input_win.move(curent_pos, 2)
                    self.input_win.refresh()
        curses.curs_set(0)
