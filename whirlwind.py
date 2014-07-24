#!/usr/bin/env python
from argparse import ArgumentParser
import logging
import os
import random
import sys
import time

from jujuclient import Environment
import yaml

log = logging.getLogger('whirlwind')

class Worker(object):
    def __init__(self, config):
        self.config = self.prepare_config(config)
        self.env = None

    def start(self):
        self.env = self.connect_state_server()
        if not self.env:
            return False

        while True:
            try:
                if self.perform_change():
                    time.sleep(self.config.change_interval)
                else:
                    time.sleep(self.config.change_retry_interval)
            except KeyboardInterrupt:
                return
            except:
                log.exception('Error occured during proactive change')
                return

    def connect_state_server(self):
        while True:
            try:
                log.debug('Connecting to state server for environment: %s', self.config.environment)
                return Environment.connect(self.config.environment)
            except:
                log.exception('Could not connect to state server')

            log.debug('Retrying connection in 30 seconds')
            time.sleep(30)

    def perform_change(self):
        services = self.config.services.keys()
        random.shuffle(services)

        for service in services:
            if self.try_change_service(service):
                return True

            log.debug('Service not ready for change: %s', service)

        log.warn('No services ready for proactive change')

    def try_change_service(self, service):
        started_units = self.fetch_units(service)
        if not started_units:
            return

        log.debug('Performing proactive change for service: %s', service)

        log.debug('Adding unit to service')
        self.env.add_unit(service)

        while True:
            if len(self.fetch_units(service)) > len(started_units):
                break

            log.debug('Waiting 30 seconds for unit to be added')
            time.sleep(30)

        unit_to_remove = random.choice(started_units.keys())

        log.debug('Removing unit: %s', unit_to_remove)
        self.env.remove_units([unit_to_remove])

        while True:
            if unit_to_remove not in self.fetch_units(service, started=False):
                break

            log.debug('Waiting 15 seconds for unit to be removed')
            time.sleep(15)

        if self.config.remove_machines:
            machine = started_units[unit_to_remove]['Machine']

            log.debug('Removing machine: %s', machine)
            self.env.destroy_machines([machine])

        log.debug('Proactive change successful')
        return True

    def fetch_units(self, service, started=True):
        status = self.env.status()

        if service not in status['Services']:
            return

        if not started:
            return status['Services'][service]['Units']

        return dict((k, v) for k, v in status['Services'][service]['Units'].iteritems() if v['AgentState'] == 'started')

    def prepare_config(self, config):
        config = normalize_structure(config)

        for k, v in config.services.items():
            config.services[k] = normalize_structure(v)

        return config

def normalize_structure(val, recursive=False):
    if isinstance(val, dict):
        s = Structure()

        for k, v in val.iteritems():
            if recursive:
                v = normalize_config(v, True)
            setattr(s, k, v)

        return s
    elif recursive and isinstance(val, list):
        return [normalize_structure(v, True) for v in val]

    return val

class Structure(object):
    pass

def main():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--config-file', default='config.yml')

    args = parser.parse_args()

    configure_logger(args.verbose)

    if not os.path.isfile(args.config_file):
        log.error('Could not open config file: %s', args.config_file)
        sys.exit(1)

    with open(args.config_file, 'r') as fp:
        config = yaml.load(fp)

    worker = Worker(config)
    if not worker.start():
        sys.exit(1)

def configure_logger(verbose):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    log.addHandler(handler)

    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARN)

if __name__ == '__main__':
    main()
