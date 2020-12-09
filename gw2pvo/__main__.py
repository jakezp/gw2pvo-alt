#!/usr/bin/env python3

import sys, os
if sys.version_info < (3,6):
    sys.exit('Sorry, you need at least Python 3.6 for Astral 2')

import logging
import argparse
import locale
import time
import telegram

from datetime import datetime
from configparser import ConfigParser
from astral import LocationInfo
from astral.geocoder import lookup, database
from astral.location import Location

from gw2pvo import ds_api
from gw2pvo import ow_api
from gw2pvo import gw_api
from gw2pvo import mqtt
from gw2pvo import netatmo_api
from gw2pvo import gw_csv
from gw2pvo import pvo_api
from gw2pvo import __version__

__author__ = "Mark Ruys"
__copyright__ = "Copyright 2017-2020, Mark Ruys"
__license__ = "MIT"
__email__ = "mark@paracas.nl"
__doc__ = "Upload GoodWe power inverter data to PVOutput.org"

last_eday_kwh = 0
last_energy_used = 0

# Telegram
def telegram_notify(telegram_token, telegram_chatid, message):
    token = telegram_token
    chat_id = telegram_chatid
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)

def get_temperature(settings, latitude, longitude):
    if settings.darksky_api_key:
        ds = ds_api.DarkSkyApi(settings.darksky_api_key)
        return ds.get_temperature(latitude, longitude)
    elif settings.openweather_api_key:
        ow = ow_api.OpenWeatherApi(settings.openweather_api_key)
        return ow.get_temperature(latitude, longitude)
    return None

def run_once(settings, city):
    global last_eday_kwh
    global last_energy_used

    # Check if we only want to run during daylight
    if city:
        now = datetime.time(datetime.now())
    #    if now < city.dawn().time() or now > city.dusk().time():
    #        logging.debug("Skipped upload as it's night")
    #        return

    if settings.mqtt_host:
        if settings.gw_station_id:
            logging.error("Bad configuration options. Choose either Goodwe or MQTT as source for inverter data. Both cannot be used simultaniously.")
            sys.exit(1)
    # Fetch the latest reading from MQTT broker
        mqtt_broker = mqtt.MQTT(settings.telegram_token, settings.telegram_chatid, settings.mqtt_host, settings.mqtt_port, settings.mqtt_user, settings.mqtt_password, settings.mqtt_topic)
        data = mqtt_broker.getCurrentReadings()
    elif settings.gw_station_id:
    # Fetch the last reading from GoodWe
        goodwe = gw_api.GoodWeApi(settings.gw_station_id, settings.gw_account, settings.gw_password)
        data = goodwe.getCurrentReadings()

    # Check if we want to abort when offline
    if settings.skip_offline:
        if data['status'] == 'Offline':
            logging.debug("Skipped upload as the inverter is offline")
            return

    # Append reading to CSV file
    if settings.csv:
        if data['status'] == 'Offline':
            logging.debug("Don't append offline data to CSV file")
        else:
            locale.setlocale(locale.LC_ALL, locale.getlocale())
            csv = gw_csv.GoodWeCSV(settings.csv)
            csv.append(data)

    # Submit reading to PVOutput, if they differ from the previous set
    eday_kwh = data['eday_kwh']
    energy_used = data['energy_used']

    if data['pgrid_w'] == 0 and abs(eday_kwh - last_eday_kwh) < 0.001:
        logging.debug("Ignore unchanged eday_kwh reading")
    else:
        last_eday_kwh = eday_kwh

    if data['load'] == 0 and abs(energy_used - last_energy_used) < 0.001:
        logging.debug("Ignore unchanged energy_used reading")
    else:
        last_energy_used = energy_used

    # Get the temperature if pulling data from GoodWe
    if settings.gw_station_id:
        temperature = get_temperature(settings, data['latitude'], data['longitude'])
        if temperature:
            data['temperature'] = temperature

    voltage = data['grid_voltage']
    if settings.pv_voltage:
        voltage=data['pv_voltage']

    if settings.pvo_system_id and settings.pvo_api_key:
        pvo = pvo_api.PVOutputApi(settings.telegram_token, settings.telegram_chatid, settings.pvo_system_id, settings.pvo_api_key)
        pvo.add_status(data['pgrid_w'], last_eday_kwh, data.get('temperature'), voltage, data['energy_used'], data['load'])
    else:
        logging.debug(str(data))
        logging.warning("Missing PVO id and/or key")

# Get historic data from GoodWe and publish to PVOutput
def copy(settings):
    # Confirm that MQTT config is not used for historic data
    if settings.mqtt_host:
        logging.error("Bad configuration options. MQTT cannot be used for backfilling historic data. Remove MQTT options from configuration and specify Goodwe (SEMS Portal details).")
        sys.exit(1)

    # Fetch readings from GoodWe
    date = datetime.strptime(settings.date, "%Y-%m-%d")
    goodwe = gw_api.GoodWeApi(settings.gw_station_id, settings.gw_account, settings.gw_password)
    data = goodwe.getDayReadings(date)

    if settings.pvo_system_id and settings.pvo_api_key:
        if settings.darksky_api_key:
            ds = ds_api.DarkSkyApi(settings.darksky_api_key)
            temperatures = ds.get_temperature_for_day(data['latitude'], data['longitude'], date)
        elif settings.openweather_api_key:
            ow = ow_api.OpenWeatherApi(settings.openweather_api_key)
            temperatures = ow.get_temperature_for_day(data['latitude'], data['longitude'], date)
        else:
            temperatures = None

        # Submit readings to PVOutput
        pvo = pvo_api.PVOutputApi(settings.telegram_token, settings.telegram_chatid, settings.pvo_system_id, settings.pvo_api_key)
        pvo.add_day(data['entries'], temperatures)
    else:
        for entry in data['entries']:
            logging.info("{}: {:6.0f} W {:6.2f} kWh".format(
                entry['dt'],
                entry['pgrid_w'],
                entry['eday_kwh'],
            ))
        logging.warning("Missing PVO id and/or key")

def copy_csv(settings):
    pvo = pvo_api.PVOutputApi(settings.telegram_token, settings.telegram_chatid, settings.pvo_system_id, settings.pvo_api_key)
    pvo.add_day_csv(settings.upload_csv)
    sys.exit(0)

def run():
    defaults = {
        'log': "info"
    }

    # Parse any config file specification. We make this parser with add_help=False so
    # that it doesn't parse -h and print help.
    conf_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    conf_parser.add_argument("--config", help="Specify config file", metavar='FILE')
    args, remaining_argv = conf_parser.parse_known_args()
    
    # Read configuration file and add it to the defaults hash.
    if args.config:
        config = ConfigParser()
        config.read(args.config)
        if "Defaults" in config:
            defaults.update(dict(config.items("Defaults")))
        else:
            logging.error("Bad config file, missing Defaults section")
            sys.exit(1)

    # Parse rest of arguments
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[conf_parser],
    )
    parser.set_defaults(**defaults)
    parser.add_argument("--gw-station-id", help="GoodWe station ID", metavar='ID')
    parser.add_argument("--gw-account", help="GoodWe account", metavar='ACCOUNT')
    parser.add_argument("--gw-password", help="GoodWe password", metavar='PASSWORD')
    parser.add_argument("--mqtt-host", help="MQTT hostname", metavar='MQTT_HOST')
    parser.add_argument("--mqtt-port", help="MQTT port", metavar='MQTT_USER')
    parser.add_argument("--mqtt-user", help="MQTT username", metavar='MQTT_USER')
    parser.add_argument("--mqtt-password", help="MQTT password", metavar='MQTT_PASS')
    parser.add_argument("--mqtt-topic", help="MQTT topic", metavar='MQTT_TOPIC')
    parser.add_argument("--pvo-system-id", help="PVOutput system ID", metavar='ID')
    parser.add_argument("--pvo-api-key", help="PVOutput API key", metavar='KEY')
    parser.add_argument("--pvo-interval", help="PVOutput interval in minutes", type=int, choices=[5, 10, 15])
    parser.add_argument("--telegram-token", help="Telegram bot token", metavar='TELEGRAM_TOKEN')
    parser.add_argument("--telegram-chatid", help="Telegram chat id", metavar='TELEGRAM_CHATID')
    parser.add_argument("--darksky-api-key", help="Dark Sky Weather API key")
    parser.add_argument("--openweather-api-key", help="Open Weather API key")
    parser.add_argument("--log", help="Set log level (default info)", choices=['debug', 'info', 'warning', 'critical'])
    parser.add_argument("--date", help="Copy all readings (max 14/90 days ago)", metavar='YYYY-MM-DD')
    parser.add_argument("--upload-csv", help="Upload all readings from csv file (max 14/90 days ago)")
    parser.add_argument("--pv-voltage", help="Send pv voltage instead of grid voltage", action='store_true')
    parser.add_argument("--skip-offline", help="Skip uploads when inverter is offline", action='store_true')
    parser.add_argument("--city", help="Sets timezone and skip uploads from dusk till dawn")
    parser.add_argument('--csv', help="Append readings to a Excel compatible CSV file, DATE in the name will be replaced by the current date")
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    args = parser.parse_args()

    # Configure the logging
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(levelname)-8s %(message)s', level=numeric_level)

    logging.debug("gw2pvo version " + __version__)

    if isinstance(args.skip_offline, str):
        args.skip_offline = args.skip_offline.lower() in ['true', 'yes', 'on', '1']

    if args.upload_csv is None:
        if args.gw_station_id is None or args.gw_account is None or args.gw_password is None:
            if args.mqtt_host is None or args.mqtt_topic is None:
                logging.error("Missing configuation. Either MQTT configuration or Goodwe (SEMS Portal) credentails need to be provided.\nPlease add either --gw-station-id, --gw-account and --gw-password OR add --mqtt-host and --mqtt-topic (at a minimum). Alternatively, one of these options can also be configured in a configuration file.")
                sys.exit(1)

    if args.city:
        city = Location(lookup(args.city, database()))
        os.environ['TZ'] = city.timezone
        time.tzset()
    else:
        city = None
    logging.debug("Timezone {}".format(datetime.now().astimezone().tzinfo))

    # Check if we want to copy old data
    if args.date:
        try:
            copy(args)
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as exp:
            logging.error(exp)
        sys.exit()
    elif args.upload_csv:
        try: 
            copy_csv(args)
        except Exception as exp:
            logging.error(exp)
            sys.exit(1)

    startTime = datetime.now()

    while True:
        currentTime = datetime.now()
        try:
            run_once(args, city)
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as exp:
            errorMsg = ("Failed to publish data PVOutput - " + str(exp))
            logging.error(str(currentTime) + " - " + str(errorMsg))
            try:
                telegram_notify(args.telegram_token, args.telegram_chatid, errorMsg)
            except Exception as exp:
                logging.error(str(currentTime) + " - Failed to send telegram notification - " + str(exp))

        if args.pvo_interval is None:
            break

        interval = args.pvo_interval * 60
        time.sleep(interval - (datetime.now() - startTime).seconds % interval)

if __name__ == "__main__":
    run()
