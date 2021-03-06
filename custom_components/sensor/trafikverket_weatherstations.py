"""
Showing weather information for air and road temperature provided by Trafikverket in Sweden.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.trafikverket_weatherstations/

EXAMPLE
-------
sensor:
  - platform: trafikverket_weatherstations
    name: Trafikverket WeatherStation Lanna
    api: eXXcbXXXacXXXXc39XX3aXXX4aXX46XX
    station: Lanna
    type: road
"""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Data provided by Trafikverket API"

CONF_API = 'api'
CONF_STATION = 'station'
CONF_TYPE = 'type'

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_API): cv.string,
    vol.Required(CONF_STATION): cv.string,
    vol.Required(CONF_TYPE): vol.In(['air', 'road']),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    sensor_name = config.get(CONF_NAME)
    sensor_api = config.get(CONF_API)
    sensor_station = config.get(CONF_STATION)
    sensor_type = config.get(CONF_TYPE)

    add_devices([TrafikverketWeatherStation(sensor_name, sensor_api, sensor_station, sensor_type)])

class TrafikverketWeatherStation(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_name, sensor_api, sensor_station, sensor_type):
        """Initialize the sensor."""
        self._name = sensor_name
        self._api = sensor_api
        self._station = sensor_station
        self._type = sensor_type
        self._state = None
        self._attributes = {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        import requests
        import json

        url = 'http://api.trafikinfo.trafikverket.se/v1.3/data.json' # Set destination URL here
        
        if self._type == 'air':
            xml = """
            <REQUEST>
                  <LOGIN authenticationkey='""" + self._api + """' />
                  <QUERY objecttype="WeatherStation">
                        <FILTER>
                              <EQ name="Name" value='""" + self._station + """' />
                        </FILTER>
                        <INCLUDE>Measurement.Air.Temp</INCLUDE>
                  </QUERY>
            </REQUEST>"""
        else:
            xml = """
            <REQUEST>
                  <LOGIN authenticationkey='""" + self._api + """' />
                  <QUERY objecttype="WeatherStation">
                        <FILTER>
                              <EQ name="Name" value='""" + self._station + """' />
                        </FILTER>
                        <INCLUDE>Measurement.Road.Temp</INCLUDE>
                  </QUERY>
            </REQUEST>"""

        post = requests.post(url, data=xml.encode('utf-8'))
        loaded_json = json.loads(post.text)

        if self._type == 'air':
            result = loaded_json["RESPONSE"]["RESULT"][0]["WeatherStation"][0]["Measurement"]["Air"]["Temp"]
        else:
            result = loaded_json["RESPONSE"]["RESULT"][0]["WeatherStation"][0]["Measurement"]["Road"]["Temp"]
        
        self._state = result