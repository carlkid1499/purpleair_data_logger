#!/usr/bin/env python3

"""
    A python class designed to use the PurpleAirAPI for sensor data.
    For best practice from PurpleAir:
    "The data from individual sensors will update no less than every 30 seconds.
    As a courtesy, we ask that you limit the number of requests to no more than
    once every 1 to 10 minutes, assuming you are only using the API to obtain data
    from sensors. If retrieving data from multiple sensors at once, please send a
    single request rather than individual requests in succession."
"""

from PurpleAirAPI import PurpleAirAPI
from PurpleAirDataLoggerPSQLStatements import *
import pg8000
import argparse
from time import sleep


class PurpleAirDataLogger():
    """
        The logger class. For now we will ingest data into a TimeScaleDB PostgreSQL
        database. Then we will use Grafana to visualize said data.
    """

    def __init__(self, PurpleAirAPIReadKey, psql_db_conn):
        """
            :param str PurpleAirAPIReadKey: A valid PurpleAirAPI Read key
            :param object psql_db_conn: A valid PG8000 database connection
        """

        # Make one instance of our PurpleAirAPI class
        self.__paa_obj = PurpleAirAPI(PurpleAirAPIReadKey)

        # Store the dict/json keys to access data fields.
        # These keys are derived from the PurpleAir documentation: https://api.purpleair.com/#api-sensors-get-sensor-data
        self.__accepted_field_names_list = [
            # Station information and status fields:
            "name", "icon", "model", "hardware", "location_type", "private", "latitude", "longitude", "altitude", "position_rating", "led_brightness", "firmware_version", "firmware_upgrade", "rssi", "uptime", "pa_latency", "memory", "last_seen", "last_modified", "date_created", "channel_state", "channel_flags", "channel_flags_manual", "channel_flags_auto", "confidence", "confidence_manual", "confidence_auto",

            # Environmental fields:
            "humidity", "humidity_a", "humidity_b", "temperature", "temperature_a", "temperature_b", "pressure", "pressure_a", "pressure_b",

            # Miscellaneous fields:
            "voc", "voc_a", "voc_b", "ozone1", "analog_input",

            # PM1.0 fields:
            "pm1.0", "pm1.0_a", "pm1.0_b", "pm1.0_atm", "pm1.0_atm_a", "pm1.0_atm_b", "pm1.0_cf_1", "pm1.0_cf_1_a",
            "pm1.0_cf_1_b",

            # PM2.5 fields:
            "pm2.5_alt", "pm2.5_alt_a", "pm2.5_alt_b", "pm2.5", "pm2.5_a", "pm2.5_b", "pm2.5_atm", "pm2.5_atm_a", "pm2.5_atm_b", "pm2.5_cf_1", "pm2.5_cf_1_a", "pm2.5_cf_1_b",

            # PM2.5 pseudo (simple running) average fields:
            # Note: These are inside the return json as json["sensor"]["stats"]. They are averages of the two sensors.
            # sensor 'a' and 'b' sensor be. Each sensors data is inside json["sensor"]["stats_a"] and json["sensor"]["stats_b"]
            "pm2.5_10minute", "pm2.5_10minute_a", "pm2.5_10minute_b", "pm2.5_30minute", "pm2.5_30minute_a", "pm2.5_30minute_b", "pm2.5_60minute", "pm2.5_60minute_a", "pm2.5_60minute_b", "pm2.5_6hour", "pm2.5_6hour_a", "pm2.5_6hour_b",
            "pm2.5_24hour", "pm2.5_24hour_a", "pm2.5_24hour_b", "pm2.5_1week", "pm2.5_1week_a", "pm2.5_1week_b",

            # PM10.0 fields:
            "pm10.0", "pm10.0_a", "pm10.0_b", "pm10.0_atm", "pm10.0_atm_a", "pm10.0_atm_b", "pm10.0_cf_1", "pm10.0_cf_1_a", "pm10.0_cf_1_b",

            # Particle count fields:
            "0.3_um_count", "0.3_um_count_a", "0.3_um_count_b", "0.5_um_count", "0.5_um_count_a", "0.5_um_count_b", "1.0_um_count", "1.0_um_count_a", "1.0_um_count_b", "2.5_um_count", "2.5_um_count_a", "2.5_um_count_b", "5.0_um_count", "5.0_um_count_a", "5.0_um_count_b", "10.0_um_count", "10.0_um_count_a", "10.0_um_count_b",

            # ThingSpeak fields, used to retrieve data from api.thingspeak.com:
            "primary_id_a", "primary_key_a", "secondary_id_a", "secondary_key_a", "primary_id_b", "primary_key_b", "secondary_id_b", "secondary_key_b"
        ]
        # Make our psql database connection
        self.__db_conn = psql_db_conn

        # Make our PSQL Tables
        self.__create_psql_db_tables()

        # Convert our PSQL tables to hyper tables
        self.__convert_psql_tables_to_hyper_tables()

        # Commit then set auto commit to true
        self.__db_conn.commit()
        the_psql_db_conn.autocommit = True

    def __create_psql_db_tables(self):
        """
            Create the PSQL database tables if they don't exist already
        """

        # We will create one table for different data groups. Simply following the
        # offical PurpleAir documentaiton. Think Station information and status fields,
        # Environmental fields, etc. See website for more informaiton.
        # https://api.purpleair.com/#api-sensors-get-sensor-data

        self.__db_conn.run(CREATE_STATION_INFORMATION_AND_STATUS_FIELDS_TABLE)
        self.__db_conn.run(CREATE_ENVIRONMENTAL_FIELDS_TABLE)
        self.__db_conn.run(CREATE_MISCELLANEOUS_FIELDS)
        self.__db_conn.run(CREATE_PM1_0_FIELDS)
        self.__db_conn.run(CREATE_PM2_5_FIELDS)
        self.__db_conn.run(CREATE_PM2_5_PSEUDO_AVERAGE_FIELDS)
        self.__db_conn.run(CREATE_PM10_0_FIELDS)
        self.__db_conn.run(CREATE_PARTICLE_COUNT_FIELDS)
        self.__db_conn.run(CREATE_THINGSPEAK_FIELDS)

    def __convert_psql_tables_to_hyper_tables(self):
        """
            A method to convert our PSQL tables to TimeScaleDB hyper tables.
        """

        self.__db_conn.run(
            """SELECT create_hypertable('station_information_and_status_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('environmental_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('miscellaneous_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('pm1_0_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('pm2_5_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('pm2_5_pseudo_average_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('pm10_0_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('particle_count_fields', 'data_time_stamp', if_not_exists => TRUE)""")
        self.__db_conn.run(
            """SELECT create_hypertable('thingspeak_fields', 'data_time_stamp', if_not_exists => TRUE)""")

    def get_accepted_field_names_list(self):
        """
            Get the accepted field data names (keys) in a string list.
        """

        return self.__accepted_field_names_list

    def get_sensor_data(self, sensor_index, read_key=None, fields=None):
        """
            Request data from a single sensor.

            :param int sensor_index: A valid PurpleAirAPI sensor index.

            :param str read_key: A valid PurpleAirAPI private read key.

            :param str fields: A comma delmited string of valid field names.

            :return A python dictionary with data.
        """

        return self.__paa_obj.request_sensor_data(sensor_index, read_key, fields)

    def store_sensor_data(self, single_sensor_data_dict):
        """
            Insert the sensor data into the database.

            :param dict single_sensor_data_dict: A python dictionary containing all fields
                                                 for insertion. If a sensor doesn't support
                                                 a certain field make sure it is NULL and part
                                                 of the dictionary. This method does no type
                                                 or error checking. That is upto the caller.
        """

        # Run the queries
        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_STATION_INFORMATION_AND_STATUS_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            name=single_sensor_data_dict["name"],
            icon=single_sensor_data_dict["icon"],
            model=single_sensor_data_dict["model"],
            hardware=single_sensor_data_dict["hardware"],
            location_type=single_sensor_data_dict["location_type"],
            private=single_sensor_data_dict["private"],
            latitude=single_sensor_data_dict["latitude"],
            longitude=single_sensor_data_dict["longitude"],
            altitude=single_sensor_data_dict["altitude"],
            position_rating=single_sensor_data_dict["position_rating"],
            led_brightness=single_sensor_data_dict["led_brightness"],
            firmware_version=single_sensor_data_dict["firmware_version"],
            firmware_upgrade=single_sensor_data_dict["firmware_upgrade"],
            rssi=single_sensor_data_dict["rssi"],
            uptime=single_sensor_data_dict["uptime"],
            pa_latency=single_sensor_data_dict["pa_latency"],
            memory=single_sensor_data_dict["memory"],
            last_seen=single_sensor_data_dict["last_seen"],
            last_modified=single_sensor_data_dict["last_modified"],
            date_created=single_sensor_data_dict["date_created"],
            channel_state=single_sensor_data_dict["channel_state"],
            channel_flags=single_sensor_data_dict["channel_flags"],
            channel_flags_manual=single_sensor_data_dict["channel_flags_manual"],
            channel_flags_auto=single_sensor_data_dict["channel_flags_auto"],
            confidence=single_sensor_data_dict["confidence"],
            confidence_manual=single_sensor_data_dict["confidence_manual"],
            confidence_auto=single_sensor_data_dict["confidence_auto"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_ENVIRONMENTAL_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            humidity=single_sensor_data_dict["humidity"],
            humidity_a=single_sensor_data_dict["humidity_a"],
            humidity_b=single_sensor_data_dict["humidity_b"],
            temperature=single_sensor_data_dict["temperature"],
            temperature_a=single_sensor_data_dict["temperature_a"],
            temperature_b=single_sensor_data_dict["temperature_b"],
            pressure=single_sensor_data_dict["pressure"],
            pressure_a=single_sensor_data_dict["pressure_a"],
            pressure_b=single_sensor_data_dict["pressure_b"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_MISCELLANEOUS_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            voc=single_sensor_data_dict["voc"],
            voc_a=single_sensor_data_dict["voc_a"],
            voc_b=single_sensor_data_dict["voc_b"],
            ozone1=single_sensor_data_dict["ozone1"],
            analog_input=single_sensor_data_dict["analog_input"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_PM1_0_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            pm1_0=single_sensor_data_dict["pm1_0"],
            pm1_0_a=single_sensor_data_dict["pm1_0_a"],
            pm1_0_b=single_sensor_data_dict["pm1_0_b"],
            pm1_0_atm=single_sensor_data_dict["pm1_0_atm"],
            pm1_0_atm_a=single_sensor_data_dict["pm1_0_atm_a"],
            pm1_0_atm_b=single_sensor_data_dict["pm1_0_atm_b"],
            pm1_0_cf_1=single_sensor_data_dict["pm1_0_cf_1"],
            pm1_0_cf_1_a=single_sensor_data_dict["pm1_0_cf_1_a"],
            pm1_0_cf_1_b=single_sensor_data_dict["pm1_0_cf_1_b"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_PM2_5_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            pm2_5_alt=single_sensor_data_dict["pm2_5_alt"],
            pm2_5_alt_a=single_sensor_data_dict["pm2_5_alt_a"],
            pm2_5_alt_b=single_sensor_data_dict["pm2_5_alt_b"],
            pm2_5=single_sensor_data_dict["pm2_5"],
            pm2_5_a=single_sensor_data_dict["pm2_5_a"],
            pm2_5_b=single_sensor_data_dict["pm2_5_b"],
            pm2_5_atm=single_sensor_data_dict["pm2_5_atm"],
            pm2_5_atm_a=single_sensor_data_dict["pm2_5_atm_a"],
            pm2_5_atm_b=single_sensor_data_dict["pm2_5_atm_b"],
            pm2_5_cf_1=single_sensor_data_dict["pm2_5_cf_1"],
            pm2_5_cf_1_a=single_sensor_data_dict["pm2_5_cf_1_a"],
            pm2_5_cf_1_b=single_sensor_data_dict["pm2_5_cf_1_b"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_PM2_5_PSEUDO_AVERAGE_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            pm2_5_10minute=single_sensor_data_dict["pm2_5_10minute"],
            pm2_5_10minute_a=single_sensor_data_dict["pm2_5_10minute_a"],
            pm2_5_10minute_b=single_sensor_data_dict["pm2_5_10minute_b"],
            pm2_5_30minute=single_sensor_data_dict["pm2_5_30minute"],
            pm2_5_30minute_a=single_sensor_data_dict["pm2_5_30minute_a"],
            pm2_5_30minute_b=single_sensor_data_dict["pm2_5_30minute_b"],
            pm2_5_60minute=single_sensor_data_dict["pm2_5_60minute"],
            pm2_5_60minute_a=single_sensor_data_dict["pm2_5_60minute_a"],
            pm2_5_60minute_b=single_sensor_data_dict["pm2_5_60minute_b"],
            pm2_5_6hour=single_sensor_data_dict["pm2_5_6hour"],
            pm2_5_6hour_a=single_sensor_data_dict["pm2_5_6hour_a"],
            pm2_5_6hour_b=single_sensor_data_dict["pm2_5_6hour_b"],
            pm2_5_24hour=single_sensor_data_dict["pm2_5_24hour"],
            pm2_5_24hour_a=single_sensor_data_dict["pm2_5_24hour_a"],
            pm2_5_24hour_b=single_sensor_data_dict["pm2_5_24hour_b"],
            pm2_5_1week=single_sensor_data_dict["pm2_5_1week"],
            pm2_5_1week_a=single_sensor_data_dict["pm2_5_1week_a"],
            pm2_5_1week_b=single_sensor_data_dict["pm2_5_1week_b"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_PM10_0_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            pm10_0=single_sensor_data_dict["pm10_0"],
            pm10_0_a=single_sensor_data_dict["pm10_0_a"],
            pm10_0_b=single_sensor_data_dict["pm10_0_b"],
            pm10_0_atm=single_sensor_data_dict["pm10_0_atm"],
            pm10_0_atm_a=single_sensor_data_dict["pm10_0_atm_a"],
            pm10_0_atm_b=single_sensor_data_dict["pm10_0_atm_b"],
            pm10_0_cf_1=single_sensor_data_dict["pm10_0_cf_1"],
            pm10_0_cf_1_a=single_sensor_data_dict["pm10_0_cf_1_a"],
            pm10_0_cf_1_b=single_sensor_data_dict["pm10_0_cf_1_b"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_PARTICLE_COUNT_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            um_count_0_3=single_sensor_data_dict["0.3_um_count"],
            um_count_a_0_3=single_sensor_data_dict["0.3_um_count_a"],
            um_count_b_0_3=single_sensor_data_dict["0.3_um_count_b"],
            um_count_0_5=single_sensor_data_dict["0.5_um_count"],
            um_count_a_0_5=single_sensor_data_dict["0.5_um_count_a"],
            um_count_b_0_5=single_sensor_data_dict["0.5_um_count_b"],
            um_count_1_0=single_sensor_data_dict["1.0_um_count"],
            um_count_a_1_0=single_sensor_data_dict["1.0_um_count_a"],
            um_count_b_1_0=single_sensor_data_dict["1.0_um_count_b"],
            um_count_2_5=single_sensor_data_dict["2.5_um_count"],
            um_count_a_2_5=single_sensor_data_dict["2.5_um_count_a"],
            um_count_b_2_5=single_sensor_data_dict["2.5_um_count_b"],
            um_count_5_0=single_sensor_data_dict["5.0_um_count"],
            um_count_a_5_0=single_sensor_data_dict["5.0_um_count_a"],
            um_count_b_5_0=single_sensor_data_dict["5.0_um_count_b"],
            um_count_10_0=single_sensor_data_dict["10.0_um_count"],
            um_count_a_10_0=single_sensor_data_dict["10.0_um_count_a"],
            um_count_b_10_0=single_sensor_data_dict["10.0_um_count_b"]
        )

        self.__db_conn.run(
            PSQL_INSERT_STATEMENT_THINGSPEAK_FIELDS,
            data_time_stamp=single_sensor_data_dict["data_time_stamp"],
            sensor_index=single_sensor_data_dict["sensor_index"],
            primary_id_a=single_sensor_data_dict["primary_id_a"],
            primary_key_a=single_sensor_data_dict["primary_key_a"],
            secondary_id_a=single_sensor_data_dict["secondary_id_a"],
            secondary_key_a=single_sensor_data_dict["secondary_key_a"],
            primary_id_b=single_sensor_data_dict["primary_id_b"],
            primary_key_b=single_sensor_data_dict["primary_key_b"],
            secondary_id_b=single_sensor_data_dict["secondary_id_b"],
            secondary_key_b=single_sensor_data_dict["secondary_key_b"]
        )

    def get_multiple_sensors_data(self, fields, location_type=None, read_keys=None, show_only=None, modified_since=None, max_age=None, nwlng=None, nwlat=None, selng=None, selat=None):
        """
            Request data from a multiple sensors. Uses the same parameters as
            PurpleAirAPI.request_multiple_sensors_data()

            :return A python dictionary with data.
        """

        return self.__paa_obj.request_multiple_sensors_data(self, fields, location_type, read_keys, show_only, modified_since, max_age, nwlng, nwlat, selng, selat)

    def store_multiple_sensors_data(self):
        """
            Insert the multiple sensors data into the database.
        """
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect data from PurpleAir sensors and insert into a database!")
    parser.add_argument("-db_usr",  required=True, dest="db_usr",
                        type=str, help="The PSQL database user")
    parser.add_argument("-db_host", required=False, default="localhost",
                        dest="db_host", type=str, help="The PSQL database host")
    parser.add_argument("-db", required=True, dest="db",
                        type=str, help="The PSQL database name")
    parser.add_argument("-db_port", required=False, default=5432,
                        dest="db_port", type=str, help="The PSQL database port number")
    parser.add_argument("-db_pwd",  required=False, default=None,
                        dest="db_pwd", type=str, help="The PSQL database password")
    parser.add_argument("-paa_read_key",  required=True,
                        dest="paa_read_key", type=str, help="The PurpleAirAPI Read key")
    parser.add_argument("-paa_sensor_index",  required=True,
                        dest="paa_sensor_index", type=int, help="The PurpleAirAPI sensor index")

    args = parser.parse_args()

    # Make the PSQL DB connection with CML args
    the_psql_db_conn = pg8000.connect(
        user=args.db_usr,
        host=args.db_host,
        database=args.db,
        port=args.db_port,
        password=args.db_pwd)

    # Make an instance our our data logger
    the_paa_data_logger = PurpleAirDataLogger(
        args.paa_read_key, the_psql_db_conn)

    while True:
        # We will request data once every 65 seconds.
        print("Requesting new data...")
        sensor_data = the_paa_data_logger.get_sensor_data(
            args.paa_sensor_index)

        # Do some validation work.
        field_names_list = the_paa_data_logger.get_accepted_field_names_list()

        # Let's make it easier on ourselves by making the sensor data one level deep.
        # Instead of json["sensor"]["KEYS..."] and json["sensor"]["stats_a"]["KEYS..."] etc
        # We turn it into just json["KEYS..."].
        the_modified_sensor_data = {}
        the_modified_sensor_data["data_time_stamp"] = sensor_data["data_time_stamp"]
        for key, val in sensor_data["sensor"].items():
            if key == "stats":
                # For now name this one stats_pm2.5 until I understand the difference
                # between sensor_data["stats"]["pm2.5"] and sensor_data["pm2.5"]
                the_modified_sensor_data["stats_pm2.5"] = val["pm2.5"]
                the_modified_sensor_data["pm2.5_10minute"] = val["pm2.5_10minute"]
                the_modified_sensor_data["pm2.5_30minute"] = val["pm2.5_30minute"]
                the_modified_sensor_data["pm2.5_60minute"] = val["pm2.5_60minute"]
                the_modified_sensor_data["pm2.5_6hour"] = val["pm2.5_6hour"]
                the_modified_sensor_data["pm2.5_24hour"] = val["pm2.5_24hour"]
                the_modified_sensor_data["pm2.5_1week"] = val["pm2.5_1week"]
                the_modified_sensor_data["pm2.5_time_stamp"] = val["time_stamp"]

            elif key in ["stats_a", "stats_b"]:
                the_modified_sensor_data["stats_a_pm2.5"] = val["pm2.5"]
                the_modified_sensor_data[f"pm2.5_10minute_{key[-1]}"] = val["pm2.5_10minute"]
                the_modified_sensor_data[f"pm2.5_30minute_{key[-1]}"] = val["pm2.5_30minute"]
                the_modified_sensor_data[f"pm2.5_60minute_{key[-1]}"] = val["pm2.5_60minute"]
                the_modified_sensor_data[f"pm2.5_6hour_{key[-1]}"] = val["pm2.5_6hour"]
                the_modified_sensor_data[f"pm2.5_24hour_{key[-1]}"] = val["pm2.5_24hour"]
                the_modified_sensor_data[f"pm2.5_1week_{key[-1]}"] = val["pm2.5_1week"]

            else:
                the_modified_sensor_data[key] = val

        # Not all sensors support all field names, so we check that the keys exist
        # in the sensor data. If not we add it in with a NULL equivalent. i.e 0, "", etc.
        for key_str in field_names_list:
            if key_str not in the_modified_sensor_data.keys():
                if key_str == "firmware_upgrade":
                    # Add it to our data dict, but make it an empty string since its a TEXT psql type.
                    the_modified_sensor_data[key_str] = ""

                elif key_str in ["voc", "voc_a", "voc_b", "ozone1"]:
                    # Add it to our data dict, but make it an 0.0 since its a FLOAT psql type.
                    the_modified_sensor_data[key_str] = 0.0

        print("Waiting 65 seconds before requesting new data again...")
        sleep(65)
