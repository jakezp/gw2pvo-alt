from datetime import datetime
from datetime import timezone
import logging
import time
import requests
import json

__author__ = "Michaël Hompus"
__copyright__ = "Copyright 2018, Michaël Hompus"
__license__ = "MIT"
__email__ = "michael@hompus.nl"

class OpenWeatherApi:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_temperature(self, latitude, longitude):
        if latitude is None or longitude is None:
            return None

        payload = {
            'apiKey' : self.api_key,
            'latitude' : latitude,
            'longitude' : longitude
        }

        data = self.call("https://api.openweathermap.org/data/2.5/onecall?lat={latitude}&lon={longitude}&units=metric&exclude=minutely,hourly,daily,alerts&appid={apiKey}".format(**payload), payload)

        return data['current']['temperature']

    def get_temperature_for_day(self, latitude, longitude, date):

        # Collect 3 days weather data to ensure we have data to cover all timezones (Open Weather API provides historic hourly data per day starting at UTC 00:00)
        day_1 = int(datetime.strptime(str(date) + "+0000", "%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc).timestamp()) - 86400
        day_2 = int(datetime.strptime(str(date) + "+0000", "%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc).timestamp())
        day_3 = int(datetime.strptime(str(date) + "+0000", "%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc).timestamp()) + 86400

        now = datetime.now()
        now_ts = datetime.now().timestamp()
        now_day = datetime.strptime(str(now.strftime("%Y-%m-%d")) + " 00:00:00+0000", "%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc).timestamp()

        if day_1 > int(now_day - 432000):

            if day_3 > int(now_ts):
                day_3 = int(now_ts)

            dates = [day_1, day_2, day_3]

            result = {}
            result['hourly'] = []

            for i in dates:
                part_date = (i)
                payload = {
                    'apiKey' : self.api_key,
                    'latitude' : latitude,
                    'longitude' : longitude,
                    'date' : part_date
                }
                data = self.call("https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={latitude}&lon={longitude}&units=metric&dt={date}&appid={apiKey}".format(**payload), payload)
                data = data['hourly']
                for sample in (data):
                    time = sample['time']
                    temp = sample['temperature']
                    result['hourly'].append({
                        'time' : time,
                        'temperature' : temp
                    })
            return result['hourly']
        else:
            logging.error("Open Weather OneAPI historic data is only available for 5 days. Data upload will exclude temperature data.\n")

    def call(self, url, payload):
        for i in range(1, 4):
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                result = r.json()
                result= json.dumps(result)
                result = result.replace('dt','time')
                result = result.replace('temp','temperature')
                result = json.loads(result)
                return result
            except requests.exceptions.RequestException as arg:
                logging.warning(arg)
                time.sleep(i ** 3)
        else:
            logging.error("Failed to call Open Weather API")
