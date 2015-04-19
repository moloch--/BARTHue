#!/usr/bin/env python
'''

This program adjusts your Hue lights based on the BART schedule

'''

import time
import pyhue
import logging
import argparse

from datetime import timedelta
from rgb import Converter
from BARTpy import BART

HUE_USERNAME = 'newdeveloper'
BART_API_KEY = 'ZJVD-UYTM-IKBQ-DT35'

# RGB Color Tuples
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


def get_color_for_etd(etd):
    '''
    Return a color for the EDT, the idea is to return
    more reddish colors the lower the time.
    '''
    colors = Converter()
    if timedelta(minutes=10) <= etd:
        return colors.rgbToCIE1931(*GREEN)
    elif timedelta(minutes=6) <= etd:
        return colors.rgbToCIE1931(*BLUE)
    else:
        return colors.rgbToCIE1931(*RED)


def bart_hue_loop(bart, station_name, destination, light, poll_interval):
    ''' Main loop forever, and ever '''
    while True:
        try:
            departure = bart[station_name][destination]
            if departure is not None and 0 < len(departure.trains):
                light.on = True
                light.xy = get_color_for_etd(departure.trains[0].minutes)
            else:
                light.on = False
            logging.info("Succesfully updated state")
        except KeyboardInterrupt:
            raise
        except:
            logging.exception("Error while updating state")
        finally:
            time.sleep(float(poll_interval))


def bart_hue(station_name, destination, bridge_ip,
             light_name, poll_interval=30.0):
    ''' Grab all the objects we need and start the loop '''
    logging.info("BARTHue is starting up ...")
    bart = BART(BART_API_KEY)
    bridge = pyhue.Bridge(bridge_ip, HUE_USERNAME)
    light = next(light for light in bridge.lights if light.name == light_name)
    bart_hue_loop(bart, station_name, destination, light, poll_interval)


if __name__ == '__main__':

    logging.basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s",
                        level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description='Changes your Hue light(s) based on the BART schedule',
    )
    parser.add_argument('--station', '-s',
                        help='the station to pull information about',
                        dest='station_name',
                        required=True)
    parser.add_argument('--train-line', '-t',
                        help='the train line to monitor (destination)',
                        dest='destination',
                        required=True)
    parser.add_argument('--bridge-ip', '-b',
                        help='the hue bridge ip address',
                        dest='bridge_ip',
                        required=True)
    parser.add_argument('--light-name', '-l',
                        help='the name of the light to change',
                        dest='light_name',
                        required=True)
    parser.add_argument('--poll', '-p',
                        help='the polling interval',
                        dest='poll_interval',
                        default=30.0,
                        type=float)
    try:
        bart_hue(**vars(parser.parse_args()))
    except KeyboardInterrupt:
        print("User stop, have a nice day!")
