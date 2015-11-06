#!/usr/bin/env python
'''

This program adjusts your Hue lights based on the BART schedule

'''

import os
import time
import pyhue
import logging
import argparse

from datetime import timedelta
from rgb import Converter
from BARTpy import BART

HUE_USERNAME = 'newdeveloper'
BART_API_KEY = 'ZJVD-UYTM-IKBQ-DT35'
MAX_ERRORS = 50

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
    logging.info("Starting main loop")
    errors = 0
    while True:
        try:
            departure = bart[station_name][destination]
            if departure is not None and 0 < len(departure.trains):
                light.on = True
                light.xy = get_color_for_etd(departure.trains[0].minutes)
            else:
                light.on = False
            logging.info("Successfully updated state")
        except KeyboardInterrupt:
            raise
        except:
            errors += 1
            logging.exception("Error #%d while updating state" % errors)
            if MAX_ERRORS <= errors:
                logging.fatal("Reached maximum error count")
                os._exit(-1)
        finally:
            time.sleep(float(poll_interval))


def bart_hue(station_name, destination, bridge_ip,
             light_name, poll_interval):
    ''' Grab all the objects we need and start the loop '''
    logging.info("BARTHue is starting up (pid: %s) ..." % os.getpid())
    bart = BART(BART_API_KEY)
    logging.info("Connecting to Hue bridge at: %s" % bridge_ip)
    bridge = pyhue.Bridge(bridge_ip, HUE_USERNAME)
    lights = filter(lambda light: light.name == light_name, bridge.lights)
    if len(lights):
        logging.info("Found light with name '%s'" % light_name)
        bart_hue_loop(bart, station_name, destination,
                      lights[0], poll_interval)
    else:
        logging.fatal("Could not find light '%s'" % light_name)
        os._exit(1)


def _main(args):
    '''
    Handles various administrivia then starts the main loop
    '''
    if args.fork:
        pid = os.fork()
        if pid:
            print("[*] Forking into background %s" % pid)
            os._exit(0)
    # Setup logging
    logging.basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s",
                        filename=args.log_filename,
                        level=logging.DEBUG)

    # Start the main loop
    bart_hue(args.station_name, args.destination, args.bridge_ip,
             args.light_name, args.poll_interval)

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
                        default=15.0,
                        type=float)
    parser.add_argument('--fork', '-f',
                        help='fork the process into the background',
                        action='store_true',
                        dest='fork')
    parser.add_argument('--log-filename', '-log',
                        help='save logging information to file',
                        dest='log_filename',
                        default="barthue.log")
    try:
        _main(parser.parse_args())
    except KeyboardInterrupt:
        print("\r[!] User stop, have a nice day!")
