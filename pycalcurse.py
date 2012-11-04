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
import signal

import curses
import datetime
from icalendar import Calendar, Event

from constants import DAY_DICT, MONTH_DICT, \
    INPUT_COLOR_DICT, COLOR_DICT_REVERSE, COLOR_DICT
from widgets import MultiCheckboxWidget, InfoBoxWidget, InputBoxWidget, \
    KeyInputWidget
from curses_windows import CalendarWindow, RessourceWindow, EventWindow, \
    InfoWindow
from ressources import CalRessource
from utils import term_size, centralized_pos


class PyCalCurse(object):

    def __init__(self):
        self.today = datetime.date.today()
        self.active_day = self.today
        self.screen = None
        self.calendar_window = None
        self.event_window = None
        self.info_window = None
        self.ressource_window = None
        self.linenumber_of_calwidget = 0
        self.calendar_ressources = {}
        self.term_size = term_size()
        signal.signal(signal.SIGWINCH, self._repaint_after_term_size_change)

    def input_loop(self):
        x = 0
        while x != ord('q'):
            self.init_main_screen()
            self.build_ressource_window()
            self.build_calendar_window()
            self.build_event_window()
            self.build_info_window()
            self.calendar_window._actualise_calendar_window(
                self.active_day, self.calendar_ressources
            )
            self.event_window._actualise_event_window(
                self.active_day, self.calendar_ressources
            )
            if self.active_day == self.today:
                self._today()
            x = self.screen.getch()
            if x == curses.KEY_RIGHT or x == ord('l'):
                self.active_day = self.active_day + datetime.timedelta(1)
                self.event_window._actualise_event_window(
                    self.active_day, self.calendar_ressources
                )
            if x == curses.KEY_LEFT or x == ord('h'):
                self.active_day = self.active_day - datetime.timedelta(1)
                self.event_window._actualise_event_window(
                    self.active_day, self.calendar_ressources
                )
            if x == curses.KEY_UP or x == ord('k'):
                self.active_day = self.active_day - datetime.timedelta(7)
                self.event_window._actualise_event_window(
                    self.active_day, self.calendar_ressources
                )
            if x == curses.KEY_DOWN or x == ord('j'):
                self.active_day = self.active_day + datetime.timedelta(7)
                self.event_window._actualise_event_window(
                    self.active_day, self.calendar_ressources
                )
            if x == ord('t'):
                self.active_day = self.today
            if x == ord('m'):
                self.info_window._key_infos += 1
                self.info_window._generate_key_infos()
            if x == ord('a'):
                self._add_event()
            if x == ord('r'):
                self._add_ressource()
            if x == ord('e'):
                self._edit_ressource_or_event()
            if x == ord('i'):
                self._show_license_box()
        self._write_to_info_line("PyCalCurse beenden? [j/n]")
        self.info_window.refresh()
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
            curses.resize_term(self.term_size[0], self.term_size[1])
            self.screen.clear()
            self.screen.refresh()
        else:
            self.screen.refresh()

    def build_calendar_window(self):
        if not self.calendar_window:
            self.calendar_window = CalendarWindow(self.term_size)
            self.calendar_window.refresh()
        else:
            self.calendar_window.refresh()

    def build_event_window(self):
        if not self.event_window:
            self.event_window = EventWindow(self.term_size)
            #self.event_window = curses.newwin(19, 56, 0, 0)
            #self.event_window.border()
            self.event_window.refresh()
        else:
            self.event_window.refresh()

    def build_info_window(self):
        if not self.info_window:
            self.info_window = InfoWindow(self.term_size)
            self.info_window.refresh()
            self.info_window._generate_key_infos()
        else:
            self.info_window.refresh()

    def build_ressource_window(self):
        if not self.ressource_window:
            self.ressource_window = RessourceWindow(self.term_size)
            self._load_ressources()
            self.ressource_window.fill_ressource_window(
                self.calendar_ressources
            )
            self.ressource_window.refresh()
        else:
            self.ressource_window.refresh()

    def _add_event(self):
        if self.calendar_ressources.keys() == []:
            InfoBoxWidget(4, 70, 10, 5,
                "Noch keine Ressource vorhanden!", "Bitte legen sie zuerst eine Ressource an."
            )
            self._refresh_after_popup()
            return
        name = ''
        while name == '':
            name = InputBoxWidget(4, 70, 10, 5, "Bezeichnung des Events").getstr()

            if name == '':
                InfoBoxWidget(4, 70, 10, 5, "Fehler!", "Der Name der Ressource darf nicht leer sein.")

        start_time = ''
        end_time = ''
        while start_time == '' and end_time == '':
            while start_time == '':
                time_string = InputBoxWidget(4, 70, 10, 5, "Beginn des Termines (HH:MM)").getstr()
                start_time = self._time_input(time_string)

            while end_time == '':
                time_string = InputBoxWidget(4, 70, 10, 5, "Ende des Termines (HH:MM)").getstr()
                end_time = self._time_input(time_string)

            if end_time < start_time:
                InfoBoxWidget(4, 70, 10, 5, "Fehlerhafte eingabe!", "Endzeit darf nicht vor Startzeit liegen")
                start_time = ''
                end_time = ''

        line_pos = 2
        checkbox_information = {}
        for ressource in self.calendar_ressources:
            if self.calendar_ressources[ressource].ressource_type == 'local':
                checkbox_information[line_pos] = [
                    self.calendar_ressources[ressource],
                    self.calendar_ressources[ressource].name
                ]
                line_pos += 1

        if checkbox_information.keys() == []:
            InfoBoxWidget(4, 70, 10, 5, "Fehler!", "Es wurde bisher keine lokale Ressource angelegt.")
            self._refresh_after_popup()
            return

        multi_widget = MultiCheckboxWidget(
            self.screen,
            3 + len(self.calendar_ressources), 70, 10, 5,
            "In welche Kalender speichern?",
            checkbox_information
        )

        new_event = Event()
        new_event.add('summary', name)
        new_event.add('dtstart', start_time)
        new_event.add('dtend', end_time)
        choosen_ressources = []
        for pos in multi_widget.checkboxes.keys():
            if multi_widget.checkboxes[pos][0].active:
                choosen_ressources.append(multi_widget.checkboxes[pos][1])
        for ressource in choosen_ressources:
            ressource.ical.add_component(new_event)
            ressource.save()
        self.calendar_window = None
        self.event_window = None
        self.info_window = None
        self.ressource_window = None

    def _add_ressource(self):
        name = ''
        while name == '':
            name = InputBoxWidget(4, 70, 10, 5, "Namen der Ressource eingeben.").getstr()
            if name == '':
                InfoBoxWidget(4, 70, 10, 5, "Fehler!", "Der Name der Ressource darf nicht leer sein.")

        local_or_remote_win = KeyInputWidget(4, 70, 10, 5,
            "Eine Locale oder eine Webressource anlegen?", "l = locale Ressource, w = webbasierte Ressource")
        x = 0
        while not x in [ord('l'), ord('w')]:
            x = local_or_remote_win.getch()
        if x == ord('l'):
            ressource_type = "local"
        elif x == ord('w'):
            ressource_type = "webressource"
        self._refresh_after_popup()

        color_win = KeyInputWidget(5, 70, 10, 5,
            "In welcher Farbe sollen die Einträge dargestellt werden?",
            ["0 = Normal, 1 = Schwarz, 2 = Blau, 3 = Cyan, 4 = Gruen, 5 = Magenta",
            "6 = Rot, 7 = Weiss, 8 = Gelb"]
        )
        x = 0
        while not x in [ord(str(num)) for num in range(9)]:
            x = color_win.getch()
        color = INPUT_COLOR_DICT[x]

        new_ressource = Calendar()
        new_ressource.add('prodid', '-//My calendar product//mxm.dk//')
        new_ressource.add('version', '2.0')
        if ressource_type == 'local':
            new_cal_path = os.path.expanduser("~/.config/pycalcurse/%s.ics" % (name.lower()))
        elif ressource_type == 'webressource':
            self._refresh_after_popup()
            new_cal_path = ''
            while new_cal_path == '':
                url_win = InputBoxWidget(4, 70, 10, 5, "Wie lautet die URL der Webressource?")
                new_cal_path = url_win.getstr()
                if new_cal_path == '':
                    InfoBoxWidget(4, 70, 10, 5, "Fehler!", "Die Url darf nicht leer sein.")
        if os.path.exists(new_cal_path):
            self._refresh_after_popup()
            InfoBoxWidget(4, 70, 10, 5, "Fehler!", "Der Kalender existiert bereits.")
        if ressource_type == 'local':
            with open(new_cal_path, 'w') as ressource_file:
                ressource_file.write(new_ressource.to_ical())
        config_file_path = os.path.expanduser(
            '~/.config/pycalcurse/ressources.csv'
        )
        with open(config_file_path, 'a') as config_file:
            config_string = "%s,%s,%s,%s\n" % (name, ressource_type, new_cal_path, color)
            config_file.write(config_string)
        self.calendar_window = None
        self.event_window = None
        self.info_window = None
        self.ressource_window = None

    def _edit_ressource_or_event(self):
        key_win = KeyInputWidget(4, 70, 10, 5,
            "Ein Event oder eine Ressource bearbeiten?",
            "a = Event, r = Ressource")
        x = 0
        while not x in [ord('a'), ord('r')]:
            x = key_win.getch()
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
            InfoBoxWidget(4, 70, 10, 5, "Fehler!", "An diesem Tag gibt es keine Einträge.")
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
                self.event_window.addstr(
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
                self.event_window.addstr(line, 1, "      |       |")
                line += 1
            self.event_window.refresh()
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
                        self.info_window = None
                        self.event_window = None
                        self.calendar_window = None
                        self.ressource_window = None
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
                        self.info_window = None
                        self.event_window = None
                        self.calendar_window = None
                        self.ressource_window = None
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
                            self.info_window = None
                            self.event_window = None
                            self.calendar_window = None
                            self.ressource_window = None
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
        self.ressource_window.touchwin()
        min_line = active_line = 3
        max_line = (len(self.calendar_ressources.keys()) + 2)
        x = 0
        while x != 10:  # use 10 for 'Enter', because curses.KEY_ENTER is 343
                        # but getch get 10 from the key
            line = 3
            for ressource in self.calendar_ressources.keys():
                if line == active_line:
                    self.ressource_window.addstr(
                        line,
                        1,
                        ressource,
                        curses.A_REVERSE
                    )
                    line += 1
                else:
                    self.ressource_window.addstr(
                        line,
                        1,
                        ressource,
                        curses.color_pair(self.calendar_ressources[ressource].color)
                    )
                    line += 1
            self.ressource_window.refresh()
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
            self.ressource_window = None
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
            self.calendar_window = None
            self.event_window = None
            self.info_window = None
            self.ressource_window = None
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
            self.calendar_window = None
            self.event_window = None
            self.info_window = None
            self.ressource_window = None
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
                if self.calendar_ressources[choosen_ressource].ressource_type == 'local':
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
                self.calendar_window = None
                self.event_window = None
                self.info_window = None
                self.ressource_window = None
                self.calendar_ressources = {}
                curses.noecho()
                return
        self.ressource_window.refresh()

    def _time_input(self, time_string):
        try:
            start_time_hour, start_time_min = time_string.split(":")
            time = datetime.datetime(
                self.active_day.year,
                self.active_day.month,
                self.active_day.day,
                int(start_time_hour),
                int(start_time_min)
            )
        except:
            InfoBoxWidget(
                4, 70, 10, 5,
                "Fehler!",
                "Falsches Eingabeformat oder Feld ist leer."
            )
            time = ''
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
            centralized_pos(69, version),
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

    def _today(self):
        # Set the actual Day in the Infobar
        self.info_window.window.addstr(1, 1, \
            "Heute ist %s der %s. %s %s" % (
                DAY_DICT[self.today.weekday()][0], \
                self.today.day, \
                MONTH_DICT[self.today.month][0], \
                self.today.year
            ),
            curses.A_REVERSE
        )
        self.info_window.refresh()
        self.calendar_window._actualise_calendar_window(
            self.active_day, self.calendar_ressources
        )

    def _write_to_info_line(self, message):
        self.info_window.window.addstr(
            1,
            1,
            (" " * (self.info_window.window.width - 2)),
            curses.A_REVERSE)
        self.info_window.refresh()
        self.info_window.window.addstr(1, 1, message, curses.A_REVERSE)
        self.info_window.refresh()

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
        self.ressource_window.touchwin()
        self.ressource_window.refresh()
        self.calendar_window.touchwin()
        self.calendar_window.refresh()
        self.info_window.touchwin()
        self.info_window.refresh()
        self.event_window.touchwin()
        self.event_window.refresh()

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

    def _repaint_after_term_size_change(self, signum, frame):
        self.term_size = term_size()
        height = self.term_size[0]
        if height < 24:
            height = 24
        width = self.term_size[1]
        if width < 80:
            width = 80
        curses.resize_term(height, width)
        self.screen.resize(height, width)
        self.screen.clear()
        self.screen.refresh()
        self.calendar_window = None
        self.ressource_window = None
        self.event_window = None
        self.info_window = None
        self.build_calendar_window()
        self.build_ressource_window()
        self.build_event_window()
        self.build_info_window()


if __name__ == '__main__':
    try:
        scr = PyCalCurse()
        signal.signal(signal.SIGWINCH, scr._repaint_after_term_size_change)
        scr.input_loop()
    finally:
        curses.endwin()
        os.system("clear")
