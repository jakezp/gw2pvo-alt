import sys, os
import time
import logging
import telegram

import paho.mqtt.client as mqtt

from datetime import datetime

__author__ = "Jacqueco Peenz"
__copyright__ = "Copyright 2020, Jacqueco Peenz"
__license__ = "MIT"
__email__ = "jakezp@gmail.com"
__credit__ = "https://github.com/jkairys/mqtt-pvoutput-bridge"

class MQTT:

    def __init__(self, telegram_token, telegram_chatid, mqtt_host, mqtt_port, mqtt_user, mqtt_password, mqtt_topic):
        self.telegram_token = telegram_token
        self.telegram_chatid = telegram_chatid
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.mqtt_topic = mqtt_topic
        self.client = mqtt.Client()
        mqtt.Client.connected_flag = False
        mqtt.Client.bad_connection_flag = False
        self.raw_data = {}

    # notification
    def telegram_notify(self, telegram_token, telegram_chatid, message):
        token = self.telegram_token
        chat_id = self.telegram_chatid
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=message)

    def mqtt_server_connection(self, telegram_token, telegram_chatid, mqtt_host, mqtt_port, mqtt_user, mqtt_password, mqtt_topic):
        currentTime = datetime.now()
        try:
            tries = 5
            client = self.client
            client.on_connect = self.on_connect
            client.on_message = self.on_message
            client.username_pw_set(self.mqtt_user, password=self.mqtt_password)
            client.connect(self.mqtt_host, port=int(mqtt_port))
            client.loop_start()
            if not client.connected_flag and not client.bad_connection_flag:
                time.sleep(12)
            if client.bad_connection_flag:
                client.loop_stop()
                sys.exit(1)
            for i in range(tries):
                raw_data = self.raw_data
                if not 'work_mode_label' in raw_data:
                    logging.info("Failed to get all values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'ppv' in raw_data:
                    logging.info("Failed to get all values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                else:
                    break
            client.loop_stop()
            return self.raw_data
        except Exception as exp:
            errorMsg = ("Unable to connect mqtt broker - " + str(self.mqtt_host) + " - Reason: " + str(exp))
            logging.error(str(currentTime) + " - " + str(errorMsg))
            telegramMsg = ("[gw2pvo-alt] " + str(errorMsg))
            self.telegram_notify(self.telegram_token, self.telegram_chatid, telegramMsg)
            sys.exit(1)

    def on_connect(self, client, userdata, flags, rc):
        currentTime = datetime.now()
        if rc==0:
            client.connected_flag=True
            successMsg = ("Connected to mqtt broker - " + str(self.mqtt_host) + " - Result: " + str(rc))
            logging.info(str(currentTime) + " - " + str(successMsg))
            client.subscribe(str(self.mqtt_topic)+"/#")
        else:
            client.bad_connection_flag=True
            errorMsg = ("Unable to connect mqtt broker - " + str(self.mqtt_host) + " - Result: " + str(rc))
            logging.error(str(currentTime) + " - " + str(errorMsg))
            telegramMsg = ("[gw2pvo-alt] " + str(errorMsg))
            self.telegram_notify(self.telegram_token, self.telegram_chatid, telegramMsg)

    def on_message(self, client, userdata, msg):
        payload = str(msg.payload.decode('utf-8'))
        path = msg.topic.split("/")
        if(path[0] == self.mqtt_topic):
            reading = path[2]
            self.raw_data[reading] = payload
    
    def getCurrentReadings(self):
        data = self.mqtt_server_connection(self.telegram_token, self.telegram_chatid, self.mqtt_host, self.mqtt_port, self.mqtt_user, self.mqtt_password, self.mqtt_topic)
        result = {
            'status' : '',
            'pgrid_w' : 0,
            'eday_kwh' : 0,
            'etotal_kwh' : 0,
            'grid_voltage' : 0,
            'pv_voltage' : 0,
            'load' : 0,
            'soc' : 0,
            'meter' : 0,
            'energy_used' : 0,
            'temperature' : 0,
            'date' : 0
        }

        result['status'] = data['work_mode_label']
        result['pgrid_w'] = float(data['ppv'])
        result['grid_voltage'] = float(data['vgrid'])
        result['pv_voltage'] = float(data['vpv1'])
        result['load'] = float(data['house_consumption'])
        result['eday_kwh'] = float(data['pv_daily'])
        result['etotal_kwh'] = float(data['e_total'])
        result['soc'] = data['battery_soc']
        result['energy_used'] = float(data['house_consumption_daily'])
        result['temperature'] = data['outside_temperature']
        result['date'] = datetime.strptime(str(data['date']), '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M')

        message = "Status: {status}, Temperature is {temperature} degrees, Current PV power: {pgrid_w} W, Current consumption: {load} kW, Current grid voltage: {grid_voltage} V, Current PV voltage: {pv_voltage} V, Total PV power generated today: {eday_kwh} kWh, Total consumption today: {energy_used} kWh, Current battery SOC: {soc} %, All time total generation: {etotal_kwh} kWh".format(**result)

        logging.info(message)
        return result

