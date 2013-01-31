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
import calendar
import datetime

from utils import centralized_pos
from constants import MONTH_DICT, CALENDAR_DAY_POSITION


class AbstractWindow(object):
    """
    """

    def build_window(self, height, width, ypos, xpos, name=""):
        """
        """
        self.height = height
        self.width = width
        window = curses.newwin(height, width, ypos, xpos)
        window.border()
        if name:
            window.addstr(
                1,
                centralized_pos(width, name),
                name
            )
            window.addstr(2, 1, "----------------------")
        return window

    def touchwin(self):
        self.window.touchwin()

    def refresh(self):
        self.window.refresh()

    def addstr(self, x_pos, y_pos, text, *args, **kwargs):
        self.window.addstr(x_pos, y_pos, text, *args, **kwargs)

class InfoWindow(AbstractWindow):
    """
    """

    def __init__(self, term_size):
        """
        """
        self._key_infos = 1
        width = term_size[1] - 24
        if width < 56:
            width = 56
        ypos = term_size[0] - 5
        self.window = self.build_window(5, width, ypos, 0)
        self.window.addstr(1,
            1,
            (" " * width),
            curses.A_REVERSE)
        self.window.border()

    def _generate_key_infos(self):
        if self._key_infos >= 4:
            self._key_infos = 1
        if self._key_infos == 1:
            self.window.addstr(2, 1, (" " * 50))
            self.window.addstr(3, 1, (" " * 50))
            self.window.addstr(2, 1, ">/l", curses.A_BOLD)
            self.window.addstr(2, 5, "naechster Tag")
            self.window.addstr(3, 1, "</h", curses.A_BOLD)
            self.window.addstr(3, 5, "vorheriger Tag")
            self.window.addstr(2, 21, "^/k", curses.A_BOLD)
            self.window.addstr(2, 25, "eine Woche zurueck")
            self.window.addstr(3, 21, "v/j", curses.A_BOLD)
            self.window.addstr(3, 25, "eine Woche vor")
            self.window.addstr(2, 45, "q", curses.A_BOLD)
            self.window.addstr(2, 47, "Beenden")
            self.window.addstr(3, 45, "m", curses.A_BOLD)
            self.window.addstr(3, 47, "mehr...")
            self.window.refresh()
        elif self._key_infos == 2:
            self.window.addstr(2, 1, (" " * 54))
            self.window.addstr(3, 1, (" " * 54))
            self.window.addstr(2, 1, "a", curses.A_BOLD)
            self.window.addstr(2, 3, "Termin anlegen")
            self.window.addstr(3, 1, "e", curses.A_BOLD)
            self.window.addstr(3, 3, "Termin/Ressource bearbeiten")
            self.window.addstr(2, 32, "r", curses.A_BOLD)
            self.window.addstr(2, 34, "Ressource anlegen")
            self.window.addstr(3, 32, "m", curses.A_BOLD)
            self.window.addstr(3, 34, "mehr...")
            self.window.refresh()
        elif self._key_infos == 3:
            self.window.addstr(2, 1, (" " * 54))
            self.window.addstr(3, 1, (" " * 54))
            self.window.addstr(2, 1, "t", curses.A_BOLD)
            self.window.addstr(2, 3, "zum heutigen Tag springen")
            self.window.addstr(3, 1, "m", curses.A_BOLD)
            self.window.addstr(3, 3, "mehr...")
            self.window.addstr(2, 30, "i", curses.A_BOLD)
            self.window.addstr(2, 32, "Lizenstext")
            self.window.refresh()


class RessourceWindow(AbstractWindow):
    """
    """

    def __init__(self, term_size):
        xpos = term_size[1] - 24
        height = term_size[0] - 12
        self.window = self.build_window(height, 24, 12, xpos, name="Ressourcen")

    def fill_ressource_window(self, ressources):
        """
        """
        line = 3
        for ressource in ressources.keys():
            self.window.addstr(
                line,
                1,
                ressource,
                curses.color_pair(ressources[ressource].color)
            )
            line += 1


class EventWindow(AbstractWindow):
    """
    """

    def __init__(self, term_size):
        height = term_size[0] - 5
        width = term_size[1] - 24
        if width < 56:
            width = 56
        self.window = self.build_window(height, width, 0, 0)

    def _actualise_event_window(self, active_day, ressources):
        self.window.clear()
        self.window.border()
        self.window.addstr(1, 1, "Von   | Bis   | Termin")
        self.window.addstr(2, 1, ("-" * (self.width - 2)))
        line = 3
        events = []
        for ressource_name in ressources.keys():
            ressource = ressources[ressource_name]
            if active_day.isoformat() in ressource.keys():
                [events.append([event, ressource.color]) for event in \
                    ressource[active_day.isoformat()]]
        events.sort(key=lambda a: a[0]['DTSTART'].dt)
        for event_pair in events:
            event = event_pair[0]
            ressource_color = event_pair[1]
            start_time = event['DTSTART'].dt
            if 'DURATION' in event.keys():
                end_time = start_time + event['DURATION'].dt
            elif 'DTEND' in event.keys():
                end_time = event['DTEND'].dt
            self.window.addstr(
                line,
                1,
                "%s | %s | %s" % (
                    start_time.strftime("%H:%M"),
                    end_time.strftime("%H:%M"),
                    event['SUMMARY'].title().encode(event['SUMMARY'].encoding),
                ),
                curses.color_pair(ressource_color)
            )
            line += 1
        while line < (self.height - 1):
            self.window.addstr(line, 1, "      |       |")
            line += 1
        self.window.refresh()


class CalendarWindow(AbstractWindow):
    """
    """

    def __init__(self, term_size):
        xpos = term_size[1] - 24
        self.window = self.build_window(12, 24, 0, xpos, name="Kalender")

    def _day_len_check(self, day):
        if len(str(day)) == 1:
            return "0%s" % (str(day))
        else:
            return str(day)

    def _event_on_day(self, day, ressources):
        for ressource in ressources.keys():
            if day.isoformat() in ressources[ressource].keys():
                return True

    def _actualise_calendar_window(self, active_day, ressources):
        for line_to_clear in [5, 6, 7, 8, 9, 10]:
            self.window.addstr(line_to_clear, 1, (" " * 21))
        self.window.addstr(
            3,
            8,
            "%s %s" % (
                MONTH_DICT[active_day.month][1],
                active_day.year
            )
        )
        self.window.addstr(4, 1, " MO DI MI DO FR SA SO ")
        days_of_the_month = calendar.monthrange(
            active_day.year, active_day.month
        )[1]
        self.linenumber_of_calwidget = 5
        for day_number in range(1, days_of_the_month + 1):
            day = datetime.date(active_day.year, active_day.month, day_number)
            if day == active_day:
                format = curses.A_REVERSE
            elif self._event_on_day(day, ressources):
                format = curses.A_BOLD
            else:
                format = curses.A_NORMAL
            self.window.addstr(
                self.linenumber_of_calwidget,
                CALENDAR_DAY_POSITION[day.weekday()],
                self._day_len_check(day.day),
                format
            )
            if day.weekday() == 6:
                self.linenumber_of_calwidget += 1
        self.window.refresh()
