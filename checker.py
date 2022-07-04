#!/usr/bin/env python3
version = '1.0.0'

import asyncio
import aiohttp
import aiohttp_proxy
import urllib3
import optparse
import json
import time
import threading
import signal
import sys

import itertools
i_counter = itertools.count()

import logging
def create_logger():
    # Create logger for App
    logger = logging.getLogger('steam_checker')
    logger.setLevel(logging.DEBUG)

    # Create file handler with logs even debug messages
    fh = logging.FileHandler('steam-checker.log', mode='w')
    fh.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s] %(levelname)8s --- %(message)s ' + '(%(filename)s:%(lineno)s)',datefmt='%Y-%m-%d %H:%M:%S')

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

logger = create_logger()

timestr = time.strftime('%Y%m%d-%H%M%S')
parser = optparse.OptionParser(usage='usage: %prog [options] arg', version=version)
http = urllib3.PoolManager() # Instance to make requests

proxylist = []
steamaccounts = []

def GetProxyFromFile(proxyfile_abspath):
    with open(proxyfile_abspath, 'r') as f:
        _proxylist = f.read().split('\n')
        f.close()
    return _proxylist

proxy_list_updater_thread_alive = True
def ProxyListUpdater(proxylist_abspath):
    global proxylist
    while(proxy_list_updater_thread_alive):
        proxylist = GetProxyFromFile(proxylist_abspath)
        time.sleep(1)

def GetSteamAccounts(steamaccounts_abspath):
    with open(steamaccounts_abspath, 'r') as f:
        steamaccounts = list(filter(bool, f.read().split('\n')))
        f.close()
    return steamaccounts

main_thread_alive = True
def Main():
    while main_thread_alive:
        print(len(proxylist))
        print(len(steamaccounts))
        time.sleep(1)

parser.add_option(
    '-p', '--proxy',
    action='store',
    help='abspath to proxy list txt file',
    type='string',
    dest='proxylist_abspath'
)

parser.add_option(
    '-s', '--steamaccounts',
    action='store',
    help='abspath to steam accounts txt file',
    type='string',
    dest='steamaccounts_abspath'
)

options, args = parser.parse_args()

if options.proxylist_abspath == None or options.steamaccounts_abspath == None:
    logger.info('Please put valid arguments')
else:
    # Get a list of all Steam accounts from a file
    logger.info('Reading Steam accounts from file')
    steamaccounts = GetSteamAccounts(options.steamaccounts_abspath)
    logger.info(f'Steam accounts successfully read from the file, their count: {len(steamaccounts)}')
    
    # Start a thread to pick up new proxy servers
    proxy_list_updater_thread = threading.Thread(target=ProxyListUpdater, args=[options.proxylist_abspath])
    proxy_list_updater_thread.start()
    logger.info('The stream to update proxy servers is running')

    # Wait until the proxylist variable is empty
    logger.info('Wait until the proxylist variable is empty...')
    while(not proxylist):
        time.sleep(1)
    logger.info(f'The first proxies were discovered, their count: {len(proxylist)}')

    logger.info('Preparation is over, checking of accounts has begun')
    main_thread = threading.Thread(target=Main, args=())
    main_thread.start()

# Check User Input for stop app
logging.info("For exit program use Ctrl+C\n")

def signal_handler(sig, frame):
    logging.info('\nTerminating all threads.\n')

    global proxy_list_updater_thread_alive
    proxy_list_updater_thread_alive = False
    logging.info('Wait for the ProxyListUpdater thread to finish working')
    proxy_list_updater_thread.join()
    logging.info('The ProxyListUpdater thread has completed its work')

    global main_thread_alive
    main_thread_alive = False
    logging.info('Wait for the Main thread to finish working')
    main_thread.join()
    logging.info('The Main thread has completed its work')

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.pause()