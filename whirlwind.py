#!/usr/bin/env python
from argparse import ArgumentParser
import logging
import random
from subprocess import check_call, check_output
import sys
import time

import yaml

class Worker(object):
    def __init__(self, config):
        self.config = self.prepare_config(config)
        self.logger = logging.getLogger(__name__)

    def start(self):
        while True:
            try:
                if self.perform_change():
                    time.sleep(self.config.change_interval)
                else:
                    time.sleep(self.config.change_retry_interval)
            except KeyboardInterrupt:
                return
            except:
                self.logger.exception('Error occured during proactive change')
                return

    def perform_change(self):
        services = self.config.services.keys()
        random.shuffle(services)

        for service in services:
            if self.try_change_service(service):
                return True
            
            self.logger.debug('Service not ready for change: %s', service)

        self.logger.warn('No services ready for proactive change')

    def try_change_service(self, service):
        started_units = self.fetch_units(service)
        if not started_units:
            return

        self.logger.debug('Performing proactive change for service: %s', service)

        # TODO Could use juju set-constraints --service <service> <constraints>

        self.logger.debug('Adding unit to service')
        check_call(['juju', 'add-unit', service])

        while True:
            if len(self.fetch_units(service)) > len(started_units):
                break

            self.logger.debug('Waiting 15 seconds for unit to be added')
            time.sleep(15)

        unit_to_remove = random.choice(started_units.keys())

        self.logger.debug('Removing unit: %s', unit_to_remove)
        check_call(['juju', 'remove-unit', unit_to_remove])

        while True:
            if unit_to_remove not in self.fetch_units(service, started=False):
                break

            self.logger.debug('Waiting 15 seconds for unit to be removed')
            time.sleep(15)

        machine = started_units[unit_to_remove]['machine']

        if self.config.remove_machines:
            self.logger.debug('Removing machine: %s', machine)
            check_call(['juju', 'remove-machine', machine])

        self.logger.debug('Proactive change successful')
        return True

    def fetch_units(self, service, started=True):
        status = yaml.load(check_output(['juju', 'status', service]))

        if service not in status['services']:
            return

        if not started:
            return status['services'][service]['units'] 

        return dict((k, v) for k, v in status['services'][service]['units'].iteritems() if v['agent-state'] == 'started')

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

    with open(args.config_file, 'r') as fp:
        config = yaml.load(fp)

    worker = Worker(config)
    worker.start()

def configure_logger(verbose):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root = logging.getLogger()
    root.addHandler(handler)
    
    if verbose:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.WARN)

if __name__ == '__main__':
    main()
