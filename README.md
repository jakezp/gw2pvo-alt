
# gw2pvo-alt

gw2pvo-alt is a command line tool to upload solar data from a GoodWe power inverter to the PVOutput.org website. gw2pvo-alt is 100% based on the awesome [gw2pvo](https://github.com/markruys/gw2pvo) work done by [Mark Ruys](https://github.com/markruys), modified for my own requirements. Some of the additions done include: 
* Added weather support for OpenWeather
* Include consumption data to be uploaded to PVOutput.org
* Added support to read data from MQTT instead of SEMS Portal

## Installation

You need to have Python 3 and pip installed. Then:

```shell
sudo pip3 install --upgrade https://github.com/jakezp/gw2pvo-alt/raw/main/dist/gw2pvo-1.4.1-alt.tar.gz
```

### Source data

Source data can be collected from either SEMS Portal or MQTT. *Configure only one of these options, not both!*

#### SEMS Portal
Determine the Station ID from the GoodWe site as follows. Open the [Sems Portal](https://www.semsportal.com). The Plant Status will reveal the Station ID in the URL. Example:

    https://www.semsportal.com/powerstation/powerstatussnmin/9a6415bf-cdcc-46af-b393-2b442fa89a7f

So the Station ID is `9a6415bf-cdcc-46af-b393-2b442fa89a7f`.

#### MQTT Broker

In order to get the Goodwe inverter to log data to MQTT, I've hacked together [gw2matt](https://github.com/jakezp/gw2mqtt). Alternative options include:
* [GoodWe Solar inverter logger based on ESP8266](https://github.com/jantenhove/GoodWeLogger)
* [mqtt-pvoutput-bridge](https://github.com/jkairys/mqtt-pvoutput-bridge)

**I have not used either of these options, but the mqtt collector used in gw2pvo-alt has been inspired and partly based on [mqtt-pvoutput-bridge](https://github.com/jkairys/mqtt-pvoutput-bridge)* 

### Temperature
Configure one of the following methods to include temperature data. Please note, that currently, if you use MQTT as your source data, these methods to add temperature will not work, since I've not implemented it yet. I'm including temperature as part of my MQTT dataset. I may still implement this at a later stage, but at the moment, I am calling OpenWeatherAPI from Home Assistant, so it will be pointless to call it from Home Assistant and call it here, where I can just post the temperature data from Home Assistant to MQTT broker to be included. Make sense?

#### Netatmo

In case you have some Netatmo weather station nearby, you can use it to fetch the local temperature. First you need to create an (free) account at [developers portal](https://dev.netatmo.com/). Next create an app. This gives you a username, password, client_id, and a client_secret, which you need to supply to `gw2pvo`.

You have the option to either let `gw2pvo` find the nearest public weather station, or to select one yourself.

#### Open Weather

Optionally, for actual weather information you can get a (free) [OpenWeather API](https://openweathermap.org/api) account. Register and get 1,000 free calls per day. Use Open Weather as an alternative to Dark Sky that will be shutting down it's API in 2021.

#### Dark Sky

If you currently have a [Dark Sky API](https://darksky.net) account, you can still use it until the API will be [shut down](https://blog.darksky.net/dark-sky-has-a-new-home/) in 2021. Note that Dark Sky does not accept new signups anymore.

### PVOutput
Furthermore, you need a (free) [PVOutput](PVOutput.org) account. Register a device and enable the API. From PVOutput you need:

  1. The API Key
  2. The System Id of your device

## Usage
```usage: gw2pvo [-h] [--config FILE] [--gw-station-id ID] 
                 [--gw-account ACCOUNT] [--gw-password PASSWORD] 
                 [--mqtt-host MQTT_HOST] [--mqtt-user MQTT_USER] [--mqtt-password MQTT_PASS] [--mqtt-topic MQTT_TOPIC] 
                 [--pvo-system-id ID] [--pvo-api-key KEY] [--pvo-interval {5,10,15}] 
                 [--darksky-api-key DARKSKY_API_KEY] [--openweather-api-key OPENWEATHER_API_KEY] 
                 [--netatmo-username NETATMO_USERNAME] [--netatmo-password NETATMO_PASSWORD]
                 [--netatmo-client-id NETATMO_CLIENT_ID] [--netatmo-client-secret NETATMO_CLIENT_SECRET] [--netatmo-device-id NETATMO_DEVICE_ID] 
                 [--log {debug,info,warning,critical}] [--date YYYY-MM-DD] [--pv-voltage] [--skip-offline]
                 [--city CITY] [--csv CSV] [--version]

Upload GoodWe power inverter data to PVOutput.org

optional arguments:
  -h, --help            show this help message and exit
  --config FILE         Specify config file
  --gw-station-id ID    GoodWe station ID
  --gw-account ACCOUNT  GoodWe account
  --gw-password PASSWORD
                        GoodWe password
  --mqtt-host MQTT_HOST
                        MQTT hostname
  --mqtt-user MQTT_USER
                        MQTT username
  --mqtt-password MQTT_PASS
                        MQTT password
  --mqtt-topic MQTT_TOPIC
                        MQTT topic
  --pvo-system-id ID    PVOutput system ID
  --pvo-api-key KEY     PVOutput API key
  --pvo-interval {5,10,15}
                        PVOutput interval in minutes
  --darksky-api-key DARKSKY_API_KEY
                        Dark Sky Weather API key
  --openweather-api-key OPENWEATHER_API_KEY
                        Open Weather API key
  --netatmo-username NETATMO_USERNAME
                        Netatmo username
  --netatmo-password NETATMO_PASSWORD
                        Netatmo password
  --netatmo-client-id NETATMO_CLIENT_ID
                        Netatmo OAuth client id
  --netatmo-client-secret NETATMO_CLIENT_SECRET
                        Netatmo OAuth client secret
  --netatmo-device-id NETATMO_DEVICE_ID
                        Netatmo device id
  --log {debug,info,warning,critical}
                        Set log level (default info)
  --date YYYY-MM-DD     Copy all readings (max 14/90 days ago)
  --pv-voltage          Send pv voltage instead of grid voltage
  --skip-offline        Skip uploads when inverter is offline
  --city CITY           Sets timezone and skip uploads from dusk till dawn
  --csv CSV             Append readings to a Excel compatible CSV file, DATE in the name will be replaced by the current date
  --version             show program's version number and exit
```

The list of allowed cities can be found in the [Astral documentation](https://astral.readthedocs.io/en/stable/index.html#cities).

### Examples

#### SEMS Portal
```shell
gw2pvo --gw-station-id GWID --gw-account ACCOUNT --gw-password PASSWORD --pvo-system-id PVOID --pvo-api-key KEY --log info
```

If you want to save readings in a daily CSV file:

```shell
gw2pvo --gw-station-id GWID --gw-account ACCOUNT --gw-password PASSWORD --pvo-system-id PVOID --pvo-api-key KEY --csv "Solar DATE.csv"
```

Replace GWID, ACCOUNT, PVOID, PASSWORD, and KEY by the proper values. DATE is a template and will be automatically substituted by the current date.

##### Config file

It is more secure to define credentials in a config file instead of adding it to the command line. E.g. if you created `gw2pvo.cfg` as follows:

```ini
[Defaults]
gw_station_id = ...
gw_account = ...
gw_password = ...

pvo_api_key = ...
pvo_system_id = ...

openweather-api-key = ...

city = ...
```

Then this will also upload your inverter data to PVOutput:

```shell
gw2pvo --config gw2pvo.cfg --log debug
```

You can add any argument setting to the config file as you like.

#### MQTT Broker
```shell
gw2pvo --mqtt-host MQTT_HOST --mqtt-user MQTT_USER --mqtt-password MQTT_PASS --mqtt-topic MQTT_TOPIC --pvo-system-id PVOID --pvo-api-key KEY --log info
```
Replace MQTT_HOST, MQTT_USER, MQTT_PASS, MQTT_TOPIC PVOID, PASSWORD, and KEY by the proper values. 

##### Config file

It is more secure to define credentials in a config file instead of adding it to the command line. E.g. if you created `gw2pvo.cfg` as follows:

```ini
[Defaults]
mqtt-host = ...
mqtt-user = ...
mqtt-password = ...
mqtt-topic = ...

pvo_api_key = ...
pvo_system_id = ...

city = ...
```

Then this will also upload your inverter data to PVOutput:

```shell
gw2pvo --config gw2pvo.cfg --log info
```

You can add any argument setting to the config file as you like.


## Automatic uploads

The power graph on PVOutput is not based on the power reading from GoodWe, but on the amount of energy produced this day. This has the advantage that it does not matter if you skip one or more readings.

PVOutput gives you the option to choose to upload each 5, 10, or 15 minutes. Make sure you upload at the same rate as configured at PVOutput.

### Systemd service

If you run gw2pvo on a Systemd based Linux, you could install the script as a service, like:

```ini
[Unit]
Description=Read GoodWe inverter and upload data to PVOutput.org

[Service]
WorkingDirectory=/home/gw2pvo
ExecStart=/usr/local/bin/gw2pvo --config /etc/gw2pvo.cfg --pvo-interval 5 --skip-offline
Restart=always
RestartSec=300
User=gw2pvo

[Install]
WantedBy=multi-user.target
```

Store the file as ``/etc/systemd/system/gw2pvo.service`` and run:

```shell
sudo useradd -m gw2pvo
sudo systemctl enable gw2pvo
sudo systemctl start gw2pvo
sudo systemctl status gw2pvo
sudo journalctl -u gw2pvo -f
```

## Docker

You can use the [Dockerfile](https://raw.githubusercontent.com/jakezp/gw2pvo-alt/main/Dockerfile) to run a Docker container as follows:

```shell
docker build --tag gw2pvo-alt .
```

Add all settings to config file named `gw2pvo.cfg` like:

```ini
[Defaults]
mqtt-host = ...
mqtt-user = ...
mqtt-password = ...
mqtt-topic = ...

pvo_api_key = ...
pvo_system_id = ...

city = Cape Town
```

Do set `city` to a [valid value](https://astral.readthedocs.io/en/stable/index.html#cities) otherwise the container will use the UTC timezone. Then start the container like:

```shell
docker run --rm -v $(pwd)/gw2pvo.cfg:/gw2pvo.cfg gw2pvo
```

## Recover missed data

You can copy a day of readings from GoodWe to PVOutput. Interval will be 5 minutes as this is what the API provides. Syntax:

```shell
gw2pvo --gw-station-id GWID --gw-account ACCOUNT --gw-password PASSWORD --pvo-system-id PVOID --pvo-api-key KEY --log info --date YYYY-MM-DD
```

Beware that the date parameter must be not be older than 14 days from the current date. In donation mode, not more than 90 days.

**Ensure you use the the *SEMS Portal* details to backfil historic data, since MQTT does not contain historic data**. Be careful mixing MQTT and SEMS data, since the data does not match 100%. The assumption is that this is due to some sort of averaging or rounding being done when data is being uploaded to SEMS Portal.

## Disclaimer and warranty

*In addition to what is stated below, please see the [Disclaimer and warranty](https://github.com/markruys/gw2pvo#disclaimer-and-warrenty) section from the original [gw2pvo](https://github.com/markruys/gw2pvo).*

gw2pvo-alt is *not* an offical fork of the original [gw2pvo](https://github.com/markruys/gw2pvo), *nor* is it official software from GoodWe/Sems and it is not endorsed or supported by me. In fact, I **STRONGLY** discourage the usge of gw2pvo-alt, since it is being modified for **MY** personal use and stored on github as a source to to automate my docker build. It will most probably **NOT** work for anyone else without some sort of additional modifications. If you do however want to give it a try, imrove or adapt it further, feel free to do so.

GoodWe API access is based on the Chinese Sems Swagger documentation: [global](http://globalapi.sems.com.cn:82/swagger/ui/index), [Europe](http://eu.semsportal.com:82/swagger/ui/index#). It could be very well that at a certain point GoodWe decides to alter or disable the API.

The software is provided "as is", without **ANY** warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.

