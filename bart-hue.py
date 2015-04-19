#!/usr/bin/env python
'''

This program adjusts your Hue lights based on the BART schedule

'''

import time
import pyhue
import argparse

from datetime import timedelta
from rgb import Converter
from BARTpy import BART

HUE_USERNAME = 'newdeveloper'

# RGB Color Tuples
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)


def get_color_for_etd(etd):
    '''
    Return a color for the EDT, the idea is to return
    more reddish colors the lower the time.
    '''
    colors = Converter()
    if timedelta(minutes=10) <= etd:
        return colors.rgbToCIE1931(*GREEN)
    elif timedelta(minutes=7) <= etd:
        return colors.rgbToCIE1931(*BLUE)
    else:
        return colors.rgbToCIE1931(*RED)


def bart_hue(station_name, destination, bridge_ip,
             light_name, poll_interval=30.0):
    ''' Adjusts a Hue light based on a train schedule '''
    print("BARTHue is starting up ...")
    bart = BART()
    bridge = pyhue.Bridge(bridge_ip, HUE_USERNAME)
    light = next(light for light in bridge.lights if light.name == light_name)
    while True:
        departure = bart[station_name][destination]
        if departure is not None and 0 < len(departure.trains):
            light.on = True
            light.xy = get_color_for_etd(departure.trains[0].minutes)
        else:
            light.on = False
        print("Updated state, sleeping...")
        time.sleep(float(poll_interval))


if __name__ == '__main__':
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
