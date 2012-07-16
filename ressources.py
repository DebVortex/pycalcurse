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

from icalendar import Calendar


class CalRessource(dict):

    def __init__(self, ressouce_path, ressource_type="local"):
        self.ressouce_path = ressouce_path
        self.ressource_type = ressource_type
        if self.ressource_type == 'webressource':
            pass
        elif self.ressource_type == 'local':
            with open(self.ressouce_path, 'rb') as cal_file:
                self.ical = Calendar.from_ical(cal_file.read())
        for component in self.ical.walk():
            if component.name == 'VEVENT':
                iso_date = component['DTSTART'].dt.isoformat().split('T')[0]
                if not iso_date in self.keys():
                    self[iso_date] = [component]
                else:
                    self[iso_date].append(component)

    def save(self):
        if not self.webresource:
            with open(self.ressouce_path, 'w') as ressource_file:
                ressource_file.write(self.ical.to_ical())
