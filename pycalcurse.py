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

import os

import curses
import datetime
import calendar
from icalendar import Calendar, Event

from constants import DAY_DICT, MONTH_DICT, CALENDAR_DAY_POSITION, INPUT_COLOR_DICT, \
    COLOR_DICT_REVERSE, COLOR_DICT
from widgets import CheckboxWidget
from ressources import CalRessource


class PyCalCurse(object):

    def __init__(self):
        self.today = datetime.date.today()
        self.active_day = self.today
        self.screen = None
        self.calendar_widget = None
        self.event_widget = None
        self.info_widget = None
        self.included_cal_widget = None
        self.linenumber_of_calwidget = 0
        self.calendar_ressources = {}
        self._key_infos = 1

    def input_loop(self):
        x = 0
        while x != ord('q'):
            self.init_main_screen()
            self.build_included_cal_widget()
            self.build_calendar_widget()
            self.build_event_widget()
            self.build_info_widget()
            self._actualise_calendar_widget()
            self._actualise_event_widget()
            if self.active_day == self.today:
                self._today()
            x = self.screen.getch()
            if x == curses.KEY_RIGHT or x == ord('l'):
                self.active_day = self.active_day + datetime.timedelta(1)
            self._actualise_event_widget()
            if x == curses.KEY_LEFT or x == ord('h'):
                self.active_day = self.active_day - datetime.timedelta(1)
                self._actualise_event_widget()
            if x == curses.KEY_UP or x == ord('k'):
                self.active_day = self.active_day - datetime.timedelta(7)
                self._actualise_event_widget()
            if x == curses.KEY_DOWN or x == ord('j'):
                self.active_day = self.active_day + datetime.timedelta(7)
                self._actualise_event_widget()
            if x == ord('t'):
                self.active_day = self.today
            if x == ord('m'):
                self._key_infos += 1
                self._generate_key_infos()
            if x == ord('a'):
                self._add_event()
            if x == ord('r'):
                self._add_ressource()
            if x == ord('e'):
                self._edit_ressource_or_event()
            if x == ord('i'):
                self._show_license_box()
        self._write_to_info_line("PyCalCurse beenden? [j/n]")
        self.info_widget.refresh()
        x = self.screen.getch()
        if x == ord('j') or x == ord('y'):
            curses.endwin()
        else:
            curses.endwin()
            self.input_loop()

    def init_main_screen(self):
        if not self.screen:
            self.screen = curses.initscr()
            self._init_colors()
            self.screen.keypad(1)
            curses.noecho()
            curses.curs_set(0)
            curses.resize_term(24, 80)
            self.screen.clear()
            self.screen.refresh()
        else:
            self.screen.refresh()

    def build_calendar_widget(self):
        if not self.calendar_widget:
            self.calendar_widget = curses.newwin(12, 24, 0, 56)
            self.calendar_widget.border()
            self.calendar_widget.addstr(
                1,
                self._centralized_pos(24, "Kalender"),
                "Kalender"
            )
            self.calendar_widget.addstr(2, 1, "----------------------")
            self.calendar_widget.refresh()
        else:
            self.calendar_widget.refresh()

    def build_event_widget(self):
        if not self.event_widget:
            self.event_widget = curses.newwin(19, 56, 0, 0)
            self.event_widget.border()
            self.event_widget.refresh()
        else:
            self.event_widget.refresh()

    def build_info_widget(self):
        if not self.info_widget:
            self.info_widget = curses.newwin(5, 56, 19, 0)
            self.info_widget.addstr(1,
                1,
                (" " * 54),
                curses.A_REVERSE)
            self.info_widget.border()
            self.info_widget.refresh()
            self._generate_key_infos()
        else:
            self.info_widget.refresh()

    def _add_event(self):
        input_win = curses.newwin(4, 70, 10, 5)
        input_win.border()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        if self.calendar_ressources.keys() == []:
            input_win.addstr(1, 1, "Noch keine Ressource vorhanden!", curses.A_REVERSE)
            input_win.addstr(2, 1, "Bitte legen sie zuerst eine Ressource an.")
            input_win.getch()
            self._refresh_after_popup()
            return
        input_win.addstr(1, 1, "Bezeichnung des Events", curses.A_REVERSE)
        input_win.touchwin()
        curses.echo()
        input_win.move(2, 1)
        input_win.refresh()
        name = input_win.getstr()
        if name == '':
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Fehler!", curses.A_REVERSE)
            input_win.addstr(2, 1, "Der Name der Ressource darf nicht leer sein.")
            input_win.getch()
            self._refresh_after_popup()
            return
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.addstr(1, 1, "Beginn des Termines (HH:MM)", curses.A_REVERSE)
        input_win.move(2, 1)
        start_time = self._time_input(input_win)
        if not start_time:
            self._refresh_after_popup()
            return
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.addstr(1, 1, "Ende des Termines (HH:MM)", curses.A_REVERSE)
        input_win.move(2, 1)
        end_time = self._time_input(input_win)
        if not end_time:
            self._refresh_after_popup()
            return

        if end_time < start_time:
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Fehlerhafte eingabe!", curses.A_REVERSE)
            input_win.addstr(2, 1, "Endzeit darf nicht vor Startzeit liegen")
            input_win.getch()
            self._refresh_after_popup()
            return
        input_win.clear()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.resize((3 + len(self.calendar_ressources)), 70)
        input_win.border()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.addstr(1, 1, "In welche Kalender speichern?", curses.A_REVERSE)
        curses.noecho()
        line_pos = 2
        checkbox_pos = {}
        for ressource in self.calendar_ressources:
            if self.calendar_ressources[ressource].ressource_type == 'local':
                ressource_checkbox = CheckboxWidget(
                    input_win,
                    line_pos,
                    1,
                    ressource
                )
                checkbox_pos[line_pos] = [ressource_checkbox,
                    self.calendar_ressources[ressource]
                ]
                line_pos += 1
        if checkbox_pos.keys() == []:
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Fehler!", curses.A_REVERSE)
            input_win.addstr(2, 1, "Es wurde bisher keine lokale Ressource angelegt.")
            input_win.getch()
            self._refresh_after_popup()
            return
        first_pos = min(checkbox_pos.keys())
        last_pos = max(checkbox_pos.keys())
        curent_pos = first_pos
        input_win.move(curent_pos, 2)
        input_win.refresh()
        curses.curs_set(2)
        x = 0
        while x != 10:  # use 10 for 'Enter', because curses.KEY_ENTER is 343
                        # but getch get 10 from the key
            x = self.screen.getch()
            if x == 32:  # use 32 for 'Space', because there is no KEY_SPACE
                checkbox_pos[curent_pos][0].toggle()
                input_win.move(curent_pos, 2)
                input_win.refresh()
            if x == curses.KEY_UP:
                if curent_pos != first_pos:
                    curent_pos -= 1
                    input_win.move(curent_pos, 2)
                    input_win.refresh()
            if x == curses.KEY_DOWN:
                if curent_pos != last_pos:
                    curent_pos += 1
                    input_win.move(curent_pos, 2)
                    input_win.refresh()
        curses.curs_set(0)

        new_event = Event()
        new_event.add('summary', name)
        new_event.add('dtstart', start_time)
        new_event.add('dtend', end_time)
        choosen_ressources = []
        for pos in checkbox_pos.keys():
            if checkbox_pos[pos][0].active:
                choosen_ressources.append(checkbox_pos[pos][1])
        for ressource in choosen_ressources:
            ressource.ical.add_component(new_event)
            ressource.save()
        self.calendar_widget = None
        self.event_widget = None
        self.info_widget = None
        self.included_cal_widget = None

    def _add_ressource(self):
        input_win = curses.newwin(4, 70, 10, 5)
        input_win.border()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(1, 1, "Namen der Ressource eingeben.", curses.A_REVERSE)
        input_win.touchwin()
        curses.echo()
        input_win.move(2, 1)
        input_win.refresh()
        name = input_win.getstr()
        if name == '':
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Fehler!", curses.A_REVERSE)
            input_win.addstr(2, 1, "Der Name der Ressource darf nicht leer sein.")
            input_win.getch()
            self._refresh_after_popup()
            return
        curses.noecho()

        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.addstr(
            1,
            1,
            "Eine Locale oder eine Webressource anlegen?",
            curses.A_REVERSE
        )
        input_win.addstr(2, 1, "l = locale Ressource, w = webbasierte Ressource")
        input_win.refresh()
        x = 0
        while not x in [ord('l'), ord('w')]:
            x = input_win.getch()
        if x == ord('l'):
            ressource_type = "local"
        elif x == ord('w'):
            ressource_type = "webressource"

        input_win.resize(5, 70)
        input_win.border()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.addstr(3, 1, (" " * 68))
        input_win.addstr(
            1,
            1,
            "In welcher Farbe sollen die Einträge dargestellt werden?",
            curses.A_REVERSE
        )
        input_win.addstr(2, 1, "0 = Normal, 1 = Schwarz, 2 = Blau, 3 = Cyan, 4 = Gruen, 5 = Magenta")
        input_win.addstr(3, 1, "6 = Rot, 7 = Weiss, 8 = Gelb")
        input_win.refresh()
        x = 0
        while not x in [ord(str(num)) for num in range(9)]:
            x = input_win.getch()
        color = INPUT_COLOR_DICT[x]

        new_ressource = Calendar()
        new_ressource.add('prodid', '-//My calendar product//mxm.dk//')
        new_ressource.add('version', '2.0')
        if ressource_type == 'local':
            new_cal_path = os.path.expanduser("~/.config/pycalcurse/%s.ics" % (name.lower()))
        elif ressource_type == 'webressource':
            self._refresh_after_popup()
            input_win.resize(4, 70)
            input_win.border()
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Wie lautet die URL der Webressource?", curses.A_REVERSE)
            input_win.touchwin()
            curses.echo()
            input_win.move(2, 1)
            input_win.refresh()
            new_cal_path = input_win.getstr()
            curses.noecho()
        if os.path.exists(new_cal_path):
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Fehler!", curses.A_REVERSE)
            input_win.addstr(2, 1, "Der Kalender existiert bereits.")
            input_win.getch()
            self._refresh_after_popup()
            return
        if ressource_type == 'local':
            with open(new_cal_path, 'w') as ressource_file:
                ressource_file.write(new_ressource.to_ical())
        config_file_path = os.path.expanduser(
            '~/.config/pycalcurse/ressources.csv'
        )
        with open(config_file_path, 'a') as config_file:
            config_string = "%s,%s,%s,%s\n" % (name, ressource_type, new_cal_path, color)
            config_file.write(config_string)
        self.calendar_widget = None
        self.event_widget = None
        self.info_widget = None
        self.included_cal_widget = None

    def _edit_ressource_or_event(self):
        input_win = curses.newwin(4, 70, 10, 5)
        input_win.border()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(1, 1, "Ein Event oder eine Ressource bearbeiten?", curses.A_REVERSE)
        input_win.addstr(2, 1, "a = Event, r = Ressource")
        input_win.touchwin()
        input_win.refresh()
        x = 0
        while not x in [ord('a'), ord('r')]:
            x = input_win.getch()
        if x == ord('a'):
            self._refresh_after_popup()
            self._edit_event()
        elif x == ord('r'):
            self._refresh_after_popup()
            self._edit_ressource()

    def _edit_event(self):
        events_of_active_day = []
        for ressource_name in self.calendar_ressources.keys():
            ressource = self.calendar_ressources[ressource_name]
            if self.active_day.isoformat() in ressource.keys():
                [events_of_active_day.append([event, ressource.color]) for event in \
                    ressource[self.active_day.isoformat()]]
        if events_of_active_day == []:
            input_win = curses.newwin(4, 70, 10, 5)
            input_win.border()
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Fehler!", curses.A_REVERSE)
            input_win.addstr(2, 1, "An diesem Tag gibt es keine Einträge.")
            input_win.getch()
            self._refresh_after_popup()
            return
        events_of_active_day.sort(key=lambda a: a[0]['DTSTART'].dt)
        min_line = active_line = 3
        max_line = (2 + len(events_of_active_day))
        x = 0
        while x != 10:  # use 10 for 'Enter', because curses.KEY_ENTER is 343
                        # but getch get 10 from the key
            line = 3
            for event_pair in events_of_active_day:
                event = event_pair[0]
                ressource_color = event_pair[1]
                start_time = event['DTSTART'].dt
                if 'DURATION' in event.keys():
                    end_time = start_time + event['DURATION'].dt
                elif 'DTEND' in event.keys():
                    end_time = event['DTEND'].dt
                if line == active_line:
                    coloring = curses.A_REVERSE
                else:
                    coloring = curses.color_pair(ressource_color)
                self.event_widget.addstr(
                    line,
                    1,
                    "%s | %s | %s" % (
                        start_time.strftime("%H:%M"),
                        end_time.strftime("%H:%M"),
                        event['SUMMARY'].title(),
                    ),
                    coloring
                )
                line += 1
            while line < 18:
                self.event_widget.addstr(line, 1, "      |       |")
                line += 1
            self.event_widget.refresh()
            x = self.screen.getch()
            if x == curses.KEY_UP:
                if active_line == min_line:
                    pass
                else:
                    active_line -= 1
            elif x == curses.KEY_DOWN:
                if active_line == max_line:
                    pass
                else:
                    active_line += 1
        choosen_event = events_of_active_day[active_line - 3][0]  # Subtract the staringline
        input_win = curses.newwin(4, 70, 10, 5)
        input_win.border()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.addstr(1, 1, "Was bearbeiten?", curses.A_REVERSE)
        input_win.addstr(2, 1, "1 = Name, 2 = Zeit, 3 = Loeschen, 0 = Abbrechen")
        x = 0
        while not x in [ord(str(y)) for y in range(5)]:
            x = input_win.getch()
        if x == ord('0'):  # Abbrechen
            self._refresh_after_popup()
        elif x == ord('1'):  # Name
            curses.echo()
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Neuer Name des Termines (HH:MM)", curses.A_REVERSE)
            input_win.move(2, 1)
            name = input_win.getstr()
            for ressource_name in self.calendar_ressources:
                ressource = self.calendar_ressources[ressource_name]
                for subcomponent in ressource.ical.subcomponents:
                    if subcomponent == choosen_event:
                        index_of_ressource = ressource.ical.subcomponents.index(subcomponent)
                        ressource.ical.subcomponents[index_of_ressource].set('SUMMARY', name)
                        ressource.save()
                        self.info_widget = None
                        self.event_widget = None
                        self.calendar_widget = None
                        self.included_cal_widget = None
                        return
            curses.noecho()
            pass
        elif x == ord('2'):  # Zeit
            curses.echo()
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Beginn des Termines (HH:MM)", curses.A_REVERSE)
            input_win.move(2, 1)
            start_time = self._time_input(input_win)
            if not start_time:
                curses.noecho()
                self._refresh_after_popup()
                return
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Ende des Termines (HH:MM)", curses.A_REVERSE)
            input_win.move(2, 1)
            end_time = self._time_input(input_win)
            curses.noecho()
            if not end_time:
                self._refresh_after_popup()
                return
            if end_time < start_time:
                input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
                input_win.addstr(2, 1, (" " * 68))
                input_win.addstr(1, 1, "Fehlerhafte eingabe!", curses.A_REVERSE)
                input_win.addstr(2, 1, "Endzeit darf nicht vor Startzeit liegen")
                input_win.getch()
                self._refresh_after_popup()
                return
            for ressource_name in self.calendar_ressources:
                ressource = self.calendar_ressources[ressource_name]
                for subcomponent in ressource.ical.subcomponents:
                    if subcomponent == choosen_event:
                        index_of_ressource = ressource.ical.subcomponents.index(subcomponent)
                        ressource.ical.subcomponents[index_of_ressource].set('DTSTART', start_time)
                        ressource.ical.subcomponents[index_of_ressource].set('DTEND', end_time)
                        ressource.save()
                        self.info_widget = None
                        self.event_widget = None
                        self.calendar_widget = None
                        self.included_cal_widget = None
                        return
        elif x == ord('3'):  # Loeschen
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(
                1,
                1,
                "Den Termin %s wirklich loeschen?" % (choosen_event.get('SUMMARY')),
                curses.A_REVERSE
            )
            input_win.addstr(2, 1, "[j/n]")
            while x not in [ord('y'), ord('j'), ord('n')]:
                x = input_win.getch()
            if x == ord('n'):
                self._refresh_after_popup()
                return
            elif x in [ord('y'), ord('j')]:
                for ressource_name in self.calendar_ressources:
                    ressource = self.calendar_ressources[ressource_name]
                    for subcomponent in ressource.ical.subcomponents:
                        if subcomponent == choosen_event:
                            index_of_ressource = ressource.ical.subcomponents.index(subcomponent)
                            del ressource.ical.subcomponents[index_of_ressource]
                            ressource.save()
                            self.info_widget = None
                            self.event_widget = None
                            self.calendar_widget = None
                            self.included_cal_widget = None
                            return

    def _edit_ressource(self):
        if self.calendar_ressources.keys() == []:
            input_win = curses.newwin(4, 70, 10, 5)
            input_win.border()
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Fehler!", curses.A_REVERSE)
            input_win.addstr(2, 1, "Es existiert noch keine Ressource.")
            input_win.getch()
            self._refresh_after_popup()
            return
        self.included_cal_widget.touchwin()
        min_line = active_line = 3
        max_line = (len(self.calendar_ressources.keys()) + 2)
        x = 0
        while x != 10:  # use 10 for 'Enter', because curses.KEY_ENTER is 343
                        # but getch get 10 from the key
            line = 3
            for ressource in self.calendar_ressources.keys():
                if line == active_line:
                    self.included_cal_widget.addstr(
                        line,
                        1,
                        ressource,
                        curses.A_REVERSE
                    )
                    line += 1
                else:
                    self.included_cal_widget.addstr(
                        line,
                        1,
                        ressource,
                        curses.color_pair(self.calendar_ressources[ressource].color)
                    )
                    line += 1
            self.included_cal_widget.refresh()
            x = self.screen.getch()
            if x == curses.KEY_UP:
                if active_line == min_line:
                    pass
                else:
                    active_line -= 1
            elif x == curses.KEY_DOWN:
                if active_line == max_line:
                    pass
                else:
                    active_line += 1
        choosen_ressource = self.calendar_ressources.keys()[active_line - 3]  # Subtract the staringline
        input_win = curses.newwin(4, 70, 10, 5)
        input_win.border()
        input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
        input_win.addstr(2, 1, (" " * 68))
        input_win.addstr(1, 1, "Was bearbeiten?", curses.A_REVERSE)
        input_win.addstr(2, 1, "1 = Name, 2 = Farbe, 3 = Loeschen, 0 = Abbrechen")
        x = 0
        while not x in [ord(str(y)) for y in range(4)]:
            x = input_win.getch()
        if x == ord('0'):  # Exit
            self._refresh_after_popup()
            self.included_cal_widget = None
            return
        elif x == ord('1'):  # Change name
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(1, 1, "Bitte geben sie den neuen Namen ein.", curses.A_REVERSE)
            curses.echo()
            input_win.move(2, 1)
            new_name = input_win.getstr()
            old_calendar = self.calendar_ressources[choosen_ressource]
            ical = old_calendar.ical
            color = old_calendar.color
            new_cal_path = os.path.expanduser("~/.config/pycalcurse/%s.ical" % (new_name.lower()))
            with open(new_cal_path, 'w') as ressource_file:
                ressource_file.write(ical.to_ical())
            new_calendar = CalRessource(new_name, new_cal_path, color=COLOR_DICT_REVERSE[color])
            del self.calendar_ressources[choosen_ressource]
            self.calendar_ressources[new_name] = new_calendar
            config_file_path = os.path.expanduser(
                '~/.config/pycalcurse/ressources.csv'
            )
            config_file = open(config_file_path, 'w')
            config_string_list = []
            for ressource in [self.calendar_ressources[ressource_name] for \
                ressource_name in self.calendar_ressources.keys()]:
                config_string_list.append("%s,%s,%s,%s\n" % (
                        ressource.name,
                        ressource.ressource_type,
                        ressource.ressouce_path,
                        COLOR_DICT_REVERSE[ressource.color]
                    )
                )
            config_file.write(''.join(config_string_list))
            config_file.close()
            self.calendar_widget = None
            self.event_widget = None
            self.info_widget = None
            self.included_cal_widget = None
            self.calendar_ressources = {}
            curses.noecho()
            return
        elif x == ord('2'):  # Change color
            input_win.resize(5, 70)
            input_win.border()
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(3, 1, (" " * 68))
            input_win.addstr(
                1,
                1,
                "In welcher Farbe sollen die Einträge dargestellt werden?",
                curses.A_REVERSE
            )
            input_win.addstr(2, 1, "0 = Normal, 1 = Schwarz, 2 = Blau, 3 = Cyan, 4 = Gruen, 5 = Magenta")
            input_win.addstr(3, 1, "6 = Rot, 7 = Weiss, 8 = Gelb")
            input_win.refresh()
            x = 0
            while not x in [ord(str(num)) for num in range(9)]:
                x = input_win.getch()
            self.calendar_ressources[choosen_ressource].color = COLOR_DICT[INPUT_COLOR_DICT[x]]
            config_file_path = os.path.expanduser(
                '~/.config/pycalcurse/ressources.csv'
            )
            config_file = open(config_file_path, 'w')
            config_string_list = []
            for ressource in [self.calendar_ressources[ressource_name] for \
                ressource_name in self.calendar_ressources.keys()]:
                config_string_list.append("%s,%s,%s,%s\n" % (
                        ressource.name,
                        ressource.ressource_type,
                        ressource.ressouce_path,
                        COLOR_DICT_REVERSE[ressource.color]
                    )
                )
            config_file.write(''.join(config_string_list))
            config_file.close()
            self.calendar_widget = None
            self.event_widget = None
            self.info_widget = None
            self.included_cal_widget = None
            self.calendar_ressources = {}
            curses.noecho()
            return
        elif x == ord('3'):  # Delete ressource
            input_win.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            input_win.addstr(2, 1, (" " * 68))
            input_win.addstr(
                1,
                1,
                "Soll die Ressource %s wirklich geloescht werden?." % (choosen_ressource),
                curses.A_REVERSE)
            input_win.addstr(2, 1, "[j/n]")
            x = 0
            while x not in [ord('y'), ord('j'), ord('n')]:
                x = input_win.getch()
            if x == ord('n'):
                self._refresh_after_popup()
                return
            elif x in [ord('y'), ord('j')]:
                if self.calendar_ressources[choosen_ressource].ressource_type == 'webressource':
                    os.remove(self.calendar_ressources[choosen_ressource].ressouce_path)
                del self.calendar_ressources[choosen_ressource]
                config_file_path = os.path.expanduser(
                    '~/.config/pycalcurse/ressources.csv'
                )
                config_file = open(config_file_path, 'w')
                config_string_list = []
                for ressource in [self.calendar_ressources[ressource_name] for \
                    ressource_name in self.calendar_ressources.keys()]:
                    config_string_list.append("%s,%s,%s,%s\n" % (
                            ressource.name,
                            ressource.ressource_type,
                            ressource.ressouce_path,
                            COLOR_DICT_REVERSE[ressource.color]
                        )
                    )
                    config_file.write(''.join(config_string_list))
                config_file.close()
                self.calendar_widget = None
                self.event_widget = None
                self.info_widget = None
                self.included_cal_widget = None
                self.calendar_ressources = {}
                curses.noecho()
                return
        self.included_cal_widget.refresh()

    def _time_input(self, window):
        try:
            start_time_hour, start_time_min = window.getstr().split(":")
            time = datetime.datetime(
                self.active_day.year,
                self.active_day.month,
                self.active_day.day,
                int(start_time_hour),
                int(start_time_min)
            )
        except:
            window.addstr(1, 1, (" " * 68), curses.A_REVERSE)
            window.addstr(2, 1, (" " * 68))
            window.addstr(1, 1, "Fehlerhafte Eingabe!", curses.A_REVERSE)
            window.addstr(2, 1, "falsches Eingabeformat")
            window.getch()
            return None
        return time

    def _show_license_box(self):
        info_box = curses.newwin(22, 71, 1, 5)
        info_box.border()
        version = "unknown"
        try:
            with open('versions.txt', 'r') as version_file:
                version = version_file.read()
        except IOError:
            pass
        info_box.addstr(1,
            1,
            "%sVersion%s" % (
                (' ' * 30),
                (' ' * 32)
            ),
            curses.A_REVERSE
        )
        info_box.addstr(3,
            self._centralized_pos(69, version),
            version
        )
        info_box.addstr(6,
            1,
            "%sLizenztext%s" % (
                (' ' * 29),
                (' ' * 30)
            ),
            curses.A_REVERSE
        )
        info_box.addstr(8,
            1,
            "            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE ",
            curses.A_BOLD
        )
        info_box.addstr(9,
            1,
            "                    Version 2, December 2004",
            curses.A_BOLD
        )
        info_box.addstr(11,
            1,
            " Copyright (C) 2012 Max Brauer <max.brauer@inqbus.de> ",
            curses.A_BOLD
        )
        info_box.addstr(13,
            1,
            " Everyone is permitted to copy and distribute verbatim " \
            "or modified",
            curses.A_BOLD
        )
        info_box.addstr(14,
            1,
            " copies of this license document, and changing it is " \
            "allowed as long",
            curses.A_BOLD
        )
        info_box.addstr(15,
            1,
            " as the name is changed.",
            curses.A_BOLD
        )
        info_box.addstr(17,
            1,
            "            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE ",
            curses.A_BOLD
        )
        info_box.addstr(18,
            1,
            "   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND " \
            "MODIFICATION ",
            curses.A_BOLD
        )
        info_box.addstr(20,
            1,
            "  0. You just DO WHAT THE FUCK YOU WANT TO. ",
            curses.A_BOLD
        )
        info_box.refresh()
        info_box.touchwin()
        info_box.getch()
        del info_box
        self._refresh_after_popup()

    def _generate_key_infos(self):
        if self._key_infos >= 4:
            self._key_infos = 1
        if self._key_infos == 1:
            self.info_widget.addstr(2, 1, (" " * 50))
            self.info_widget.addstr(3, 1, (" " * 50))
            self.info_widget.addstr(2, 1, ">/l", curses.A_BOLD)
            self.info_widget.addstr(2, 5, "naechster Tag")
            self.info_widget.addstr(3, 1, "</h", curses.A_BOLD)
            self.info_widget.addstr(3, 5, "vorheriger Tag")
            self.info_widget.addstr(2, 21, "^/k", curses.A_BOLD)
            self.info_widget.addstr(2, 25, "eine Woche zurueck")
            self.info_widget.addstr(3, 21, "v/j", curses.A_BOLD)
            self.info_widget.addstr(3, 25, "eine Woche vor")
            self.info_widget.addstr(2, 45, "q", curses.A_BOLD)
            self.info_widget.addstr(2, 47, "Beenden")
            self.info_widget.addstr(3, 45, "m", curses.A_BOLD)
            self.info_widget.addstr(3, 47, "mehr...")
            self.info_widget.refresh()
        elif self._key_infos == 2:
            self.info_widget.addstr(2, 1, (" " * 54))
            self.info_widget.addstr(3, 1, (" " * 54))
            self.info_widget.addstr(2, 1, "a", curses.A_BOLD)
            self.info_widget.addstr(2, 3, "Termin anlegen")
            self.info_widget.addstr(3, 1, "e", curses.A_BOLD)
            self.info_widget.addstr(3, 3, "Termin/Ressource bearbeiten")
            self.info_widget.addstr(2, 32, "r", curses.A_BOLD)
            self.info_widget.addstr(2, 34, "Ressource anlegen")
            self.info_widget.addstr(3, 32, "m", curses.A_BOLD)
            self.info_widget.addstr(3, 34, "mehr...")
            self.info_widget.refresh()
        elif self._key_infos == 3:
            self.info_widget.addstr(2, 1, (" " * 54))
            self.info_widget.addstr(3, 1, (" " * 54))
            self.info_widget.addstr(2, 1, "t", curses.A_BOLD)
            self.info_widget.addstr(2, 3, "zum heutigen Tag springen")
            self.info_widget.addstr(3, 1, "m", curses.A_BOLD)
            self.info_widget.addstr(3, 3, "mehr...")
            self.info_widget.addstr(2, 30, "i", curses.A_BOLD)
            self.info_widget.addstr(2, 32, "Lizenstext")
            self.info_widget.refresh()

    def build_included_cal_widget(self):
        if not self.included_cal_widget:
            self.included_cal_widget = curses.newwin(12, 24, 12, 56)
            self.included_cal_widget.border()
            self.included_cal_widget.addstr(1, 7, "Ressourcen")
            self.included_cal_widget.addstr(2, 1, "----------------------")
            self._load_ressources()
            line = 3
            for ressource in self.calendar_ressources.keys():

                self.included_cal_widget.addstr(
                    line,
                    1,
                    ressource,
                    curses.color_pair(self.calendar_ressources[ressource].color))
                line += 1
            self.included_cal_widget.refresh()
        else:
            self.included_cal_widget.refresh()

    def _today(self):
        # Set the actual Day in the Infobar
        self.info_widget.addstr(1, 1, \
            "Heute ist %s der %s. %s %s" % (
                DAY_DICT[self.today.weekday()][0], \
                self.today.day, \
                MONTH_DICT[self.today.month][0], \
                self.today.year
            ),
            curses.A_REVERSE
        )
        self.info_widget.refresh()
        self._actualise_calendar_widget()
        # Set the calendar to the actual date

    def _actualise_calendar_widget(self):
        for line_to_clear in [5, 6, 7, 8, 9, 10]:
            self.calendar_widget.addstr(line_to_clear, 1, (" " * 21))
        self.calendar_widget.addstr(
            3,
            8,
            "%s %s" % (
                MONTH_DICT[self.active_day.month][1],
                self.active_day.year
            )
        )
        self.calendar_widget.addstr(4, 1, " MO DI MI DO FR SA SO ")
        days_of_the_month = calendar.monthrange(
            self.active_day.year, self.active_day.month
        )[1]
        self.linenumber_of_calwidget = 5
        for day_number in range(1, days_of_the_month + 1):
            day = datetime.date(self.active_day.year, self.active_day.month, day_number)
            if day == self.active_day:
                format = curses.A_REVERSE
            elif self._event_on_day(day):
                format = curses.A_BOLD
            else:
                format = curses.A_NORMAL
            self.calendar_widget.addstr(
                self.linenumber_of_calwidget,
                CALENDAR_DAY_POSITION[day.weekday()],
                self._day_len_check(day.day),
                format
            )
            if day.weekday() == 6:
                self.linenumber_of_calwidget += 1
        self.calendar_widget.refresh()

    def _actualise_event_widget(self):
        self.event_widget.clear()
        self.event_widget.border()
        self.event_widget.addstr(1, 1, "Von   | Bis   | Termin")
        self.event_widget.addstr(2, 1, ("-" * 54))
        line = 3
        events = []
        for ressource_name in self.calendar_ressources.keys():
            ressource = self.calendar_ressources[ressource_name]
            if self.active_day.isoformat() in ressource.keys():
                [events.append([event, ressource.color]) for event in \
                    ressource[self.active_day.isoformat()]]
        events.sort(key=lambda a: a[0]['DTSTART'].dt)
        for event_pair in events:
            event = event_pair[0]
            ressource_color = event_pair[1]
            start_time = event['DTSTART'].dt
            if 'DURATION' in event.keys():
                end_time = start_time + event['DURATION'].dt
            elif 'DTEND' in event.keys():
                end_time = event['DTEND'].dt
            self.event_widget.addstr(
                line,
                1,
                "%s | %s | %s" % (
                    start_time.strftime("%H:%M"),
                    end_time.strftime("%H:%M"),
                    event['SUMMARY'].title(),
                ),
                curses.color_pair(ressource_color)
            )
            line += 1
        while line < 18:
            self.event_widget.addstr(line, 1, "      |       |")
            line += 1
        self.event_widget.refresh()

    def _write_to_info_line(self, message):
        self.info_widget.addstr(1, 1, (" " * 54), curses.A_REVERSE)
        self.info_widget.refresh()
        self.info_widget.addstr(1, 1, message, curses.A_REVERSE)
        self.info_widget.refresh()

    def _event_on_day(self, day):
        for ressource in self.calendar_ressources.keys():
            if day.isoformat() in self.calendar_ressources[ressource].keys():
                return True

    def _day_len_check(self, day):
        if len(str(day)) == 1:
            return "0%s" % (str(day))
        else:
            return str(day)

    def _load_ressources(self):
        with self._load_config_or_create() as config_file:
            for line in config_file.read().split('\n'):
                if line != '':
                    name, cal_type, ressource_path, color = line.split(',')
                    self.calendar_ressources[name] = CalRessource(
                        name,
                        ressource_path,
                        color,
                        ressource_type=cal_type
                    )

    def _load_config_or_create(self):
        config_path = os.path.expanduser('~/.config/pycalcurse/')
        config_file_path = os.path.expanduser(
            '~/.config/pycalcurse/ressources.csv'
        )
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        if not os.path.exists(config_file_path):
            open(config_file_path, 'w').close()
        return open(config_file_path, 'r')

    def _refresh_after_popup(self):
        self.included_cal_widget.touchwin()
        self.included_cal_widget.refresh()
        self.calendar_widget.touchwin()
        self.calendar_widget.refresh()
        self.info_widget.touchwin()
        self.info_widget.refresh()
        self.event_widget.touchwin()
        self.event_widget.refresh()

    def _centralized_pos(self, width_or_hight, input_text):
        return ((width_or_hight - len(input_text)) / 2)

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(curses.COLOR_BLACK, curses.COLOR_BLACK, -1)
        curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, -1)
        curses.init_pair(curses.COLOR_CYAN, curses.COLOR_CYAN, -1)
        curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, -1)
        curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, -1)
        curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, -1)
        curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, -1)


if __name__ == '__main__':
    try:
        scr = PyCalCurse()
        scr.input_loop()
    finally:
        curses.endwin()
