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

from ctypes import c_ushort, sizeof, Structure
import fcntl
import sys
import termios


class WinSize(Structure):
    """To get the terminal size information via the UNIX systemcall 'ioctl()'.
    This is needed cause the control sequence '\033[18t' only work proper in
    xterm-like terminals but not without running X-Server.

    The 'WinSize.from_file()'-method returns the result of 'ioctl()' and is
    wrapped by 'window_size()'. Use this function instead.

    Thanks to 'BlackJack' and 'python-forum.de' and '@mutetella' from Twitter
    for this piece of code!
    """
    _fields_ = [
        ('rows', c_ushort),
        ('columns', c_ushort),
        ('x_pixels', c_ushort),  # Unused.
        ('y_pixels', c_ushort),  # Unused.
    ]

    @classmethod
    def from_file(cls, tty_file):
        result = fcntl.ioctl(tty_file,
                             termios.TIOCGWINSZ, '\0' * sizeof(cls))
        return cls.from_buffer_copy(result)


def term_size():
    """term_size() -> (rows, columns)

    In contrast to graphical frameworks which not working with chars but with
    pixels as unit the result of this function begins with (1, 1) that means
    the upper left corner.
    """
    size = WinSize.from_file(sys.stdout)
    return size.rows, size.columns


def centralized_pos(width_or_hight, input_text):
    return ((width_or_hight - len(input_text)) / 2)
