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
                #if not 'ppv' or not 'vgrid' or not 'vpv1' or not 'house_consumption' or not 'pv_daily' or not 'house_consumption_daily' or not 'temperature' in raw_data:      
                if not 'pv_daily' in raw_data:
                    logging.info("Failed to get 'pv_daily' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'house_consumption_daily' in raw_data:
                    logging.info("Failed to get 'house_consumption_daily' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'temperature' in raw_data:
                    logging.info("Failed to get 'temperature' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'vpv1' in raw_data:
                    logging.info("Failed to get 'vpv1' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'ppv' in raw_data:
                    logging.info("Failed to get 'ppv' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'vgrid' in raw_data:
                    logging.info("Failed to get 'vgrid' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'work_mode_label' in raw_data:
                    logging.info("Failed to get 'work_mode_label' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                elif not 'house_consumption' in raw_data:
                    logging.info("Failed to get 'house_consumption' values from mqtt broker. Retrying: " + str(i))
                    time.sleep(5)
                else:
                    break
            client.loop_stop()
            return self.raw_data
        except Exception as exp:
            errorMsg = ("Unable to connect mqtt broker - " + str(self.mqtt_host) + " - Reason: " + str(exp))
            logging.error(str(currentTime) + " - " + str(errorMsg))
            telegramMsg = ("[gw2pvo-alt] " + str(errorMsg))
            try:
                self.telegram_notify(self.telegram_token, self.telegram_chatid, telegramMsg)
            except Exception as exp:
                logging.error(str(currentTime) + " - Failed to send telegram notification - " + str(exp))
            
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
            try:
                self.telegram_notify(self.telegram_token, self.telegram_chatid, telegramMsg)
            except Exception as exp:
                logging.error(str(currentTime) + " - Failed to send telegram notification - " + str(exp))

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
            'eday_kwh' : 0,
            'pgrid_w' : 0,
            'energy_used' : 0,
            'load' : 0,
            'temperature' : 0,
            'grid_voltage' : 0,
            'pv_voltage' : 0,
            'date' : 0
        }

        result['status'] = data['work_mode_label']
        result['eday_kwh'] = float(data['pv_daily'])
        result['pgrid_w'] = float(data['ppv'])
        result['energy_used'] = float(data['house_consumption_daily'])
        result['load'] = float(data['house_consumption'])
        result['temperature'] = data['outside_temperature']
        result['grid_voltage'] = float(data['vgrid'])
        result['pv_voltage'] = float(data['vpv1'])
        result['date'] = datetime.strptime(str(data['date']), '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M')
        
        message = "Status: {status}, Current PV power: {pgrid_w}W, Total PV power generated today: {eday_kwh}kWh, Current consumption: {load}kW, Total consumption today: {energy_used}kWh, Current grid voltage: {grid_voltage}V, Current PV voltage: {pv_voltage}V, Temperature is {temperature} degrees".format(**result)

        logging.info(message)
        return result

