import logging
import datetime
import csv

__author__ = "Mark Ruys"
__copyright__ = "Copyright 2017, Mark Ruys"
__license__ = "MIT"
__email__ = "mark@paracas.nl"

class GoodWeCSV:

    def __init__(self, filename):
        self.filename = filename.replace('DATE', datetime.date.today().isoformat())

    def append(self, data):
        ''' Append a row to the CSV file. '''
        try:
            with open(self.filename, 'x', newline='') as csvfile:
                csvfile.write('\ufeff') # Add UTF-8 BOM header
                csvwriter = csv.writer(csvfile, dialect='excel', delimiter=',')
                csvwriter.writerow([self.label(field) for field in self.order()])
        except:
            pass

        with open(self.filename, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, dialect='excel', delimiter=',')
            csvwriter.writerow([data[field] for field in self.order()])

    def format_field(self, value):
        ''' Format values while respecting the locale, so Excel opens the CSV properly. '''
        if type(value) is float:
            return "{:n}".format(value)
        if type(value) is list:
            return "/".join([self.format_field(v) for v in value])
        return value

    def label(self, field):
        return {
            'date': 'date',
            'eday_kwh': 'eday_kwh',
            'pgrid_w': 'pgrid_w',
            'energy_used': 'energy_used',
            'load': 'load',
            'temperature': 'temp',
            'grid_voltage': 'voltage',
        }[field]

    def order(self):
        return [
            'date',
            'eday_kwh',
            'pgrid_w',
            'energy_used',
            'load',
            'temperature',
            'grid_voltage',
        ]
