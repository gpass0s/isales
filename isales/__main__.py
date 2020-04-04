#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed 01 APR 09:11 BRT 2020
Last modified on Fri 03 18:55 BRT 2020
Author: Guilherme Passos | twitter: @gpass0s
Isales package's main module and CLI
"""
import argparse
import sys

from isales import collector, preprocessor, model, sender


class CLI:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Predicts Hubspot lead's probabilities to buy",
            usage="""python3 isales run <service>

The implemented services are the following:
    collector      Collects and prepare the data that are arriving in Redis to be processed
    model          Computes leads probabilities to buy
    sender         Writes leads probabilities to buy in Hubsport database
""",
        )
        parser.add_argument("service", help="Service to run")

        if sys.argv[1:2] == ["run"]:
            args = parser.parse_args(sys.argv[2:3])
            if not hasattr(self, args.service):
                print("Unrecognized service")
                parser.print_help()
                return None
            getattr(self, args.service)()
        else:
            print("Unrecognized command")

    def collector(self):
        """Starts collector service"""
        parser = argparse.ArgumentParser(
            description="Runs collector service",
            usage="python3 isales run collector --queue <subscription_queue>",
        )
        parser.add_argument("--queue", help="[optional] Subscription queue to be read")

        queue_to_read = None
        try:
            args = parser.parse_args(sys.argv[3:])
            queue_to_read = args.queue
        except IndexError:
            queue_to_read = None
            print("Subscription queue to read wasn't define")

        hubspot_fetcher = collector.HubSpotFetcher(queue_to_read)
        while True:
            hubspot_fetcher()

    def preprocessor(self):
        """ Starts preprocessor service """
        transformer = preprocessor.Transformer()
        while True:
            transformer()

    def model(self):
        """ Starts machine learning model service """
        predictor = model.Predictor()
        while True:
            predictor()

    def sender(self):
        """ Starts sender service """
        hubspot_writer = sender.HubSpotWriter()
        while True:
            hubspot_writer()


CLI()
