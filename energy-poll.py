#!/usr/bin/env python3

#import time
import datetime
import json
import argparse
import logging
import serial
from influxdb import InfluxDBClient
import paho.mqtt.client as paho

parser = argparse.ArgumentParser()
parser.add_argument('--tty', type=str, required=True, help='TTY device to read from')
parser.add_argument('--topic', type=str, required=True, help='Topic for Influx and MQTT')
parser.add_argument('--influx', type=str, default='localhost', help='Influx Database Server')
parser.add_argument('--influxport', type=int, default=8086, help='Influx Database Server Port')
parser.add_argument('--db', type=str, required=True, help='Influx Database')
parser.add_argument('--dbuser', type=str, required=True, help='Influx Database User')
parser.add_argument('--dbpass', type=str, required=True, help='Influx Database Password')
parser.add_argument('--mqtt', type=str, default='localhost', help='MQTT Broker URL')
parser.add_argument('--muser', type=str, required=True, help='MQTT User')
parser.add_argument('--mpass', type=str, required=True, help='MQTT Password')
parser.add_argument('--debug', action='store_true', help='Activate Debug')
args = parser.parse_args()

MQTT_BASE_TOPIC = f"stat/{args.topic}"
MQTT_STATE = "state"
MQTT_LWT = "lwt"

def mqtt_on_publish(client, userdata, mid, reason_code, properties):
    pass

def mqtt_on_message(client, userdata, message):
    pass

def mqtt_on_connect(client, userdata, flags, reason_code, properties):
    logging.info("Connected to MQTT broker")
    client.publish(f"{MQTT_BASE_TOPIC}/{MQTT_LWT}", payload="Online", qos=0, retain=True)

def influx_push(db, values):
    bodys = [
        {
            "measurement": args.topic,
            "fields": {
                'l1': values[0],
                'l2': values[1],
                'l3': values[2]
            }
        }
    ]
    logging.debug(f"pushing INFLUX values: {values}")
    db.write_points(bodys)

def mqtt_push_values(mqtt, topic, values):
    logging.debug(f"pushing MQTT values: {values}")
    mqtt.publish(f"{MQTT_BASE_TOPIC}/{topic}", json.dumps(values))

def mqtt_push_discovery(mqtt):
    configs = []

    # L1, L2, L3 watt
    for x in range(1, 3+1):
       text = str(f"L{str(x)}")
       configs.append({
           "~": MQTT_BASE_TOPIC,
           "name": f"Netzbezug_{text}",
           "device": {
               "model": "EnergyPoll",
               "identifiers": MQTT_BASE_TOPIC,
               "name": "Netzbezug"
           },
           "unique_id": f"Netzbezug_" + text,
           "unit_of_measurement": "W",
           "device_class": "power",
           "state_class": "measurement",
           "state_topic": f"~/{MQTT_STATE}",
           "value_template": "{{ value_json.L" + str(x) + " | float | round(2) }}"
       })

    # SUM
    configs.append({
        "~": MQTT_BASE_TOPIC,
        "name": "SUM",
        "name": f"Netzbezug_SUM",
        "device": {
            "model": "EnergyPoll",
            "identifiers": MQTT_BASE_TOPIC,
            "name": "Netzbezug"
        },
        "unique_id": f"Netzbezug_SUM",
        "unit_of_measurement": "W",
        "device_class": "power",
        "state_class": "measurement",
        "state_topic": f"~/{MQTT_STATE}",
        "value_template": "{{ value_json.SUM | float | round(2) }}"
    })

    # ENERGY
    configs.append({
        "~": MQTT_BASE_TOPIC,
        "name": f"Netzbezug_ENERGY",
        "device": {
            "model": "EnergyPoll",
            "identifiers": MQTT_BASE_TOPIC,
            "name": "Netzbezug"
        },
        "unique_id": f"Netzbezug_ENERGY",
        "unit_of_measurement": "Wh",
        "device_class": "energy",
        "state_class": "measurement",
        "state_topic": f"~/{MQTT_STATE}",
        "value_template": "{{ value_json.ENERGY | float | round(2) }}"
    })

    # ENERGY1H
    configs.append({
        "~": MQTT_BASE_TOPIC,
        "name": f"Netzbezug_ENERGY_1H",
        "device": {
            "model": "EnergyPoll",
            "identifiers": MQTT_BASE_TOPIC,
            "name": "Netzbezug"
        },
        "unique_id": f"Netzbezug_ENERGY_1H",
        "unit_of_measurement": "Wh",
        "device_class": "energy",
        "state_class": "measurement",
        "state_topic": f"~/{MQTT_STATE}",
        "value_template": "{{ value_json.ENERGY1H | float | round(2) }}"
    })
 
    # ENERGYAVG24H
    configs.append({
        "~": MQTT_BASE_TOPIC,
        "name": f"Netzbezug_ENERGY_Average_24h",
        "device": {
            "model": "EnergyPoll",
            "identifiers": MQTT_BASE_TOPIC,
            "name": "Netzbezug"
        },
        "unique_id": f"Netzbezug_ENERGY_Average_24h",
        "unit_of_measurement": "Wh",
        "device_class": "energy",
        "state_class": "measurement",
        "state_topic": f"~/{MQTT_STATE}",
        "value_template": "{{ value_json.ENERGYAVG24H | float | round(2) }}"
    })

    # pushing out dicsoveries
    for config in configs:
        mqtt.publish(f"homeassistant/sensor/{config['name']}/config", json.dumps(config))
        logging.debug(f"Pushing DISCOVERY values: {config}")


def loop(db, mqtt, tty):
    reopen_count = 0
    now = datetime.datetime.now()
    last_discovery = now - datetime.timedelta(hours=24)
    last_hour = now.hour
    energy_last_hour = 0
    energy_average_24h = 0
    while tty.isOpen():
        reopen_count += 1
        if reopen_count > 1000:
            tty.close()
            tty.open()
            reopen_count = 0
        line = tty.readline()
        (opt, p1, p2, p3) = line.decode('utf-8').split(',')
        if opt != "NOM":
            continue
        dt = datetime.datetime.now() - now
        now = datetime.datetime.now()
        p1 = max(0.0, float(p1.replace('\x00', '')) - 20.0)
        p2 = max(0.0, float(p2.replace('\x00', '')) - 20.0)
        p3 = max(0.0, float(p3.replace('\x00', '')) - 20.0)
        pS = p1 + p2 + p3
        energy = pS * dt.total_seconds() / 3600

        values = {
            "L1": p1, "L2": p2, "L3": p3 ,
            "SUM": pS,
            "ENERGY": energy,
        }

        influx_push(db, [p1, p2, p3])

        energy_last_hour += energy
        if (last_hour != now.hour):
             logging.info(f"energy_last_hour: {energy_last_hour}")
             if energy_average_24h == 0:
                 energy_average_24h = energy_last_hour
             else:
                 # TODO: this seems not correct yet, but looks not too wrong :)
                 # DBG: fixed /24 with /23 as this gave correct calculations manually
                 energy_average_24h = ((energy_average_24h - (energy_average_24h/24)) * 23 + energy_last_hour) / 23
             values["ENERGY1H"] = energy_last_hour
             values["ENERGYAVG24H"] = energy_average_24h
             energy_last_hour = 0
             last_hour = now.hour

        mqtt_push_values(mqtt, f"{MQTT_STATE}", values)

        if (now - last_discovery > datetime.timedelta(minutes=15)):
            mqtt_push_discovery(mqtt)
            last_discovery = now

    logging.error("TTY got closed, aborting execution")

def main():
    level = 'INFO'
    if args.debug:
        level = 'DEBUG'
    logging.basicConfig(level=level)
    db = InfluxDBClient(args.influx, args.influxport, database=args.db, username=args.dbuser, password=args.dbpass)
    mqtt = paho.Client(paho.CallbackAPIVersion.VERSION2)
    mqtt.on_publish = mqtt_on_publish
    mqtt.on_message = mqtt_on_message
    mqtt.on_connect = mqtt_on_connect
    mqtt.username_pw_set(args.muser, args.mpass)
    mqtt.will_set(f"{MQTT_BASE_TOPIC}/{MQTT_LWT}", payload="offline", retain=True, qos=0)
    mqtt.connect(args.mqtt, keepalive=60)

    tty = serial.Serial(args.tty, 115200, timeout=60)
    if not tty.is_open:
        logging.error(f"Unable to open {args.tty}")
        return

    logging.info("Initialization done")

    loop(db, mqtt, tty)

if __name__ == '__main__':
    main()

