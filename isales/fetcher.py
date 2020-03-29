#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""
Created on Sun Mar 29 08:25 BRT 2020

author: guilherme passos | twitter: @gpass0s

This module reads a redis queue and fetches an object information in HubSpot database based on its
ID.
"""
import ast
import os

from isales.redis_connector import RedisConnectionManager

class DataFetcher:

    def __init__(self, queue_to_read = None):
        self.redis_client = RedisConnectionManager()
        self.max_buffer = os.environ["MAX_BUFFER"]

        if queue_to_read:
            self.queue_to_read = queue_to_read
        else:
            self.queue_to_read = os.environ["QUEUE_TO_READ"]

    def __call__(self):
        queue_items = self._pull_from_redis()

    def _pull_from_redis(self):
        """Reads nested data from redis queue and formats this data into a list of dictonaries"""
        queue_items = []

        items = self.redis_client.lrange(self.queue_to_read, 0, self.max_buffer)

        for item in items:
            parsed_item = ast.literal_eval(item.decode("utf-8"))
            queue_items = queue_items + parsed_item
        
        return queue_items





