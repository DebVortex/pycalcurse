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

DAY_DICT = {
    0: ['Montag', 'Mo'],
    1: ['Dienstag', 'Di'],
    2: ['Mittwoch', 'Mi'],
    3: ['Donnerstag', 'Do'],
    4: ['Freitag', 'Fr'],
    5: ['Sonnabend', 'Sa'],
    6: ['Sonntag', 'So'],
}

MONTH_DICT = {
    1: ['Januar', 'Jan'],
    2: ['Februar', 'Feb'],
    3: ['März', 'Mrz'],
    4: ['April', 'Apr'],
    5: ['Mai', 'Mai'],
    6: ['Juni', 'Jun'],
    7: ['Juli', 'Jul'],
    8: ['August', 'Aug'],
    9: ['September', 'Sep'],
    10: ['Oktober', 'Okt'],
    11: ['November', 'Nov'],
    12: ['Dezember', 'Dez'],
}

CALENDAR_DAY_POSITION = {
    0: 2,
    1: 5,
    2: 8,
    3: 11,
    4: 14,
    5: 17,
    6: 20
}

COLOR_DICT = {
 'black': curses.COLOR_BLACK,
 'blue': curses.COLOR_BLUE,
 'cyan': curses.COLOR_CYAN,
 'green': curses.COLOR_GREEN,
 'magenta': curses.COLOR_MAGENTA,
 'red': curses.COLOR_RED,
 'white': curses.COLOR_WHITE,
 'yellow': curses.COLOR_YELLOW,
 'normal': curses.A_NORMAL
}

COLOR_DICT_REVERSE = {
    curses.COLOR_BLACK: "black",
    curses.COLOR_BLUE: "blue",
    curses.COLOR_CYAN: "cyan",
    curses.COLOR_GREEN: "green",
    curses.COLOR_MAGENTA: "magenta",
    curses.COLOR_RED: "red",
    curses.COLOR_WHITE: "white",
    curses.COLOR_YELLOW: "yellow",
    curses.A_NORMAL: "normal"
}

INPUT_COLOR_DICT = {
 ord("0"): 'normal',
 ord("1"): 'black',
 ord("2"): 'blue',
 ord("3"): 'cyan',
 ord("4"): 'green',
 ord("5"): 'magenta',
 ord("6"): 'red',
 ord("7"): 'white',
 ord("8"): 'yellow',
}
