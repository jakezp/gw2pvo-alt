import paho.mqtt.client as mqtt
import time
import logging
from datetime import datetime

__author__ = "Jacqueco Peenz"
__copyright__ = "Copyright 2020, Jacqueco Peenz"
__license__ = "MIT"
__email__ = "jakezp@gmail.com"
__credit__ = "https://github.com/jkairys/mqtt-pvoutput-bridge"

class MQTT:

    def __init__(self, mqtt_host, mqtt_user, mqtt_password, mqtt_topic):
        self.mqtt_host = mqtt_host
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.mqtt_topic = mqtt_topic
        self.raw_data = {}

    def mqtt_server_connection(self, mqtt_host, mqtt_user, mqtt_password, mqtt_topic):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.username_pw_set(username=self.mqtt_user, password=self.mqtt_password)
        client.connect(self.mqtt_host)
        client.loop_start()
        time.sleep(10)
        raw_data = self.raw_data
        client.loop_stop()

        return self.raw_data

    def on_connect(self, client, userdata, flags, rc):
        currentTime = datetime.now()
        #logging.info(str(currentTime) + " - Connected to MQTT broker with result code " + str(rc))
        logging.info(str(currentTime) + " - Grabbing latest inverter data from topic: " + str(self.mqtt_topic))
        client.subscribe(str(self.mqtt_topic)+"/#")

    def on_message(self, client, userdata, msg):
        payload = str(msg.payload.decode('utf-8'))
        path = msg.topic.split("/")

        if(path[0] == self.mqtt_topic):
            reading = path[2]
            self.raw_data[reading] = payload

    def getCurrentReadings(self):
        data = self.mqtt_server_connection(self.mqtt_host, self.mqtt_user, self.mqtt_password, self.mqtt_topic)
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
            'temperature' : 0
        }

        result['status'] = data['work_mode_label']
        result['pgrid_w'] = float(data['ppv'])
        result['grid_voltage'] = float(data['vgrid'])
        result['pv_voltage'] = float(data['vpv1'])
        result['load'] = float(data['house_consumption'])
        result['eday_kwh'] = float(data['v1'])
        result['etotal_kwh'] = float(data['e_total'])
        result['soc'] = data['battery_soc']
        result['energy_used'] = float(data['v3'])
        result['temperature'] = data['v5']

        message = "Status: {status}, Temperature is {temperature} degrees, Current PV power: {pgrid_w} W, Current consumption: {load} kW, Current grid voltage: {grid_voltage} V, Current PV voltage: {pv_voltage} V, Total PV power generated today: {eday_kwh} kWh, Total consumption today: {energy_used} kWh, Current battery SOC: {soc} %, All time total generation: {etotal_kwh} kWh".format(**result)

        logging.info(message)
        logging.info("**Done***\n")
        return result

