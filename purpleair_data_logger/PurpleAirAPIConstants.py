#!/usr/bin/env python3

"""
    Copyright 2022 carlkid1499, All rights reserved.
    A python with constants with for use in PurpleAirAPI.py
"""

#: A constant to see if debug statements are enabled in the PurpleAirAPI module.
PRINT_DEBUG_MSGS = True

#: Accepted Error Codes
ERROR_CODES_LIST = [400, 403, 404, 409]

#: Success Code
SUCCESS_CODE_LIST = [200, 201, 204]

#: Store the dict/json keys to access data fields.
#: And define default empty/null values for them
#: These keys are derived from the PurpleAir documentation: https://api.purpleair.com/#api-sensors-get-sensor-data
ACCEPTED_FIELD_NAMES_DICT = {
    # Station information and status fields:
    "name": "", "icon": 0, "model": "", "hardware": "", "location_type": 0, "private": 0, "latitude": 0.0, "longitude": 0.0, "altitude": 0.0, "position_rating": 0, "led_brightness": 0, "firmware_version": "", "firmware_upgrade": "", "rssi": 0, "uptime": 0, "pa_latency": 0, "memory": 0, "last_seen": 0, "last_modified": 0, "date_created": 0, "channel_state": 0, "channel_flags": 0, "channel_flags_manual": 0, "channel_flags_auto": 0, "confidence": 0, "confidence_manual": 0, "confidence_auto": 0,

    # Environmental fields:
    "humidity": 0, "humidity_a": 0, "humidity_b": 0, "temperature": 0, "temperature_a": 0, "temperature_b": 0, "pressure": 0.0, "pressure_a": 0.0, "pressure_b": 0.0,

    # Miscellaneous fields:
    "voc": 0.0, "voc_a": 0.0, "voc_b": 0.0, "ozone1": 0.0, "analog_input": 0.0,

    # PM1.0 fields:
    "pm1.0": 0.0, "pm1.0_a": 0.0, "pm1.0_b": 0.0, "pm1.0_atm": 0.0, "pm1.0_atm_a": 0.0, "pm1.0_atm_b": 0.0, "pm1.0_cf_1": 0.0, "pm1.0_cf_1_a": 0.0,
    "pm1.0_cf_1_b": 0.0,

    # PM2.5 fields:
    "pm2.5_alt": 0.0, "pm2.5_alt_a": 0.0, "pm2.5_alt_b": 0.0, "pm2.5": 0.0, "pm2.5_a": 0.0, "pm2.5_b": 0.0, "pm2.5_atm": 0.0, "pm2.5_atm_a": 0.0, "pm2.5_atm_b": 0.0, "pm2.5_cf_1": 0.0, "pm2.5_cf_1_a": 0.0, "pm2.5_cf_1_b": 0.0,

    # PM2.5 pseudo (simple running) average fields:
    # Note: These are inside the return json as json["sensor"]["stats"]. They are averages of the two sensors.
    # sensor 'a' and 'b' sensor be. Each sensors data is inside json["sensor"]["stats_a"] and json["sensor"]["stats_b"]
    "pm2.5_10minute": 0.0, "pm2.5_10minute_a": 0.0, "pm2.5_10minute_b": 0.0, "pm2.5_30minute": 0.0, "pm2.5_30minute_a": 0.0, "pm2.5_30minute_b": 0.0, "pm2.5_60minute": 0.0, "pm2.5_60minute_a": 0.0, "pm2.5_60minute_b": 0.0, "pm2.5_6hour": 0.0, "pm2.5_6hour_a": 0.0, "pm2.5_6hour_b": 0.0,
    "pm2.5_24hour": 0.0, "pm2.5_24hour_a": 0.0, "pm2.5_24hour_b": 0.0, "pm2.5_1week": 0.0, "pm2.5_1week_a": 0.0, "pm2.5_1week_b": 0.0,

    # PM10.0 fields:
    "pm10.0": 0.0, "pm10.0_a": 0.0, "pm10.0_b": 0.0, "pm10.0_atm": 0.0, "pm10.0_atm_a": 0.0, "pm10.0_atm_b": 0.0, "pm10.0_cf_1": 0.0, "pm10.0_cf_1_a": 0.0, "pm10.0_cf_1_b": 0.0,

    # Particle count fields:
    "0.3_um_count": 0.0, "0.3_um_count_a": 0.0, "0.3_um_count_b": 0.0, "0.5_um_count": 0.0, "0.5_um_count_a": 0.0, "0.5_um_count_b": 0.0, "1.0_um_count": 0.0, "1.0_um_count_a": 0.0, "1.0_um_count_b": 0.0, "2.5_um_count": 0.0, "2.5_um_count_a": 0.0, "2.5_um_count_b": 0.0, "5.0_um_count": 0.0, "5.0_um_count_a": 0.0, "5.0_um_count_b": 0.0, "10.0_um_count": 0.0, "10.0_um_count_a": 0.0, "10.0_um_count_b": 0.0,

    # ThingSpeak fields, used to retrieve data from api.thingspeak.com:
    "primary_id_a": 0, "primary_key_a": "", "secondary_id_a": 0, "secondary_key_a": "", "primary_id_b": 0, "primary_key_b": "", "secondary_id_b": 0, "secondary_key_b": ""
}
