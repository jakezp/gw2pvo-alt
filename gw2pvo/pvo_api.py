import sys, os
import logging
import time
import requests
import csv
import telegram

from datetime import datetime

__author__ = "Mark Ruys"
__copyright__ = "Copyright 2017, Mark Ruys"
__license__ = "MIT"
__email__ = "mark@paracas.nl"

class PVOutputApi:

    def __init__(self, telegram_token, telegram_chatid, system_id, api_key):
        self.telegram_token = telegram_token
        self.telegram_chatid = telegram_chatid
        self.m_system_id = system_id
        self.m_api_key = api_key

    # Notification
    def telegram_notify(self, telegram_token, telegram_chatid, message):
        token = self.telegram_token
        chat_id = self.telegram_chatid
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=message)

    def add_status(self, pgrid_w, eday_kwh, temperature, voltage, energy_used, load):
        t = time.localtime()
        payload = {
            'd' : "{:04}{:02}{:02}".format(t.tm_year, t.tm_mon, t.tm_mday),
            't' : "{:02}:{:02}".format(t.tm_hour, t.tm_min),
            'v1' : round(eday_kwh * 1000),
            'v2' : round(pgrid_w),
            'v3' : round(energy_used * 1000),
            'v4' : round(load)
        }

        if temperature is not None:
            payload['v5'] = temperature

        if voltage is not None:
            payload['v6'] = voltage

        self.call("https://pvoutput.org/service/r2/addstatus.jsp", payload)
        #print (payload)

    def add_day(self, data, temperatures):
        for chunk in [ data[i:i + 30] for i in range(0, len(data), 30) ]:
            readings = []
            for reading in chunk:
                dt = reading['dt']
                fields = [
                    dt.strftime('%Y%m%d'),
                    dt.strftime('%H:%M'),
                    str(round(reading['eday_kwh'] * 1000)),
                    str(reading['pgrid_w']),
                    str(round(reading['energy_used'] * 1000)),
                    str(reading['load'])
                ]
                if temperatures is not None:
                    try:
                        fields.append('')
                        fields.append('')
                        temperature = list(filter(lambda x: dt.timestamp() >= x['time'], temperatures))[-1]
                        fields.append(str(temperature['temperature']))
                    except:
                        print ()
                readings.append(",".join(fields))

            payload = {
                'data' : ";".join(readings)
            }

            self.call("https://pvoutput.org/service/r2/addbatchstatus.jsp", payload)
            #print (payload)

    def add_day_csv(self, filename):
        with open(filename, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile,delimiter=",")
            data = (list(reader))
        for chunk in [ data[i:i + 30] for i in range(0, len(data), 30) ]:
            readings = []
            for reading in chunk:
                dt = reading['date']
                fields = [
                    datetime.strptime(str(dt), '%Y-%m-%d %H:%M').strftime('%Y%m%d'),
                    datetime.strptime(str(dt), '%Y-%m-%d %H:%M').strftime('%H:%M'),
                    str(round(float(reading['eday_kwh']) * 1000)),
                    str(reading['pgrid_w']),
                    str(round(float(reading['energy_used']) * 1000)),
                    str(reading['load']),
                    str(reading['temp']),
                    str(reading['voltage'])
                ]
                readings.append(", ".join(fields))
            
            payload = { 
                'data' : ";".join(readings) 
            }

            self.call("https://pvoutput.org/service/r2/addbatchstatus.jsp", payload)
            #print(payload)

    def call(self, url, payload):
        logging.debug(payload)
        headers = {
            'X-Pvoutput-Apikey' : self.m_api_key,
            'X-Pvoutput-SystemId' : self.m_system_id,
            'X-Rate-Limit': '1'
        }

        for i in range(1, 4):
            try:
                r = requests.post(url, headers=headers, data=payload, timeout=15)
                #self.telegram_notify(self.telegram_token, self.telegram_chatid, "test")
                if 'X-Rate-Limit-Reset' in r.headers:
                    reset = round(float(r.headers['X-Rate-Limit-Reset']) - time.time())
                else:
                    reset = 0
                if 'X-Rate-Limit-Remaining' in r.headers:
                    if int(r.headers['X-Rate-Limit-Remaining']) < 10:
                        warningMsg = ("Only {} requests left, reset after {} seconds".format(
                            r.headers['X-Rate-Limit-Remaining'],
                            reset))
                        logging.warning(warningMsg)
                        telegramMsg = ("[gw2pvo-alt] " +str(warningMsg))
                        #self.telegram_notify(self.telegram_token, self.telegram_chatid, telegramMsg)
                if r.status_code == 401:
                    warningMsg = ("Unable to connect to pvoutput.org - Reason: " + r.reason)
                    logging.warning(warningMsg)
                    sys.exit(1)
                if r.status_code == 403:
                    warningMsg = ("Unable to connect to pvoutput.org - Forbidden: " + r.reason)
                    logging.warning(warningMsg)
                    time.sleep(reset + 1)
                if r.status_code == 503:
                    warningMsg = ("Unable to connect to pvoutput.org - Reason: " + r.reason)
                    logging.warning(warningMsg)
                    #self.telegram_notify(self.telegram_token, self.telegram_chatid, warningMsg)
                    time.sleep(120)
                else:
                    infoMsg = ("PVOutput.org result: " + r.reason)
                    logging.info(infoMsg)
                    r.raise_for_status()
                    break
            except requests.exceptions.RequestException as arg:
                warningMsg = (r.text or str(arg))
                logging.warning(warningMsg)
                try:
                    self.telegram_notify(self.telegram_token, self.telegram_chatid, warningMsg)
                except Exception as exp:
                    logging.error(str(currentTime) + " - Failed to send telegram notification - " + str(exp))

            time.sleep(i ** 3)
        else:
            errorMsg = ("Failed to call PVOutput API")
            logging.error(errorMsg)
            try:
                self.telegram_notify(self.telegram_token, self.telegram_chatid, errorMsg)
            except Exception as exp:
                logging.error(str(currentTime) + " - Failed to send telegram notification - " + str(exp))

