#!/usr/bin/python3
# -*- encoding: utf-8 -*-
"""
Created on Sun Mar 29 08:25 BRT 2020
Last modified on Tue Mar 30 20:19 BRT 2020
author: guilherme passos | twitter: @gpass0s

This module reads the new events that are arriving in the redis queue and fetches these events
information in HubSpot database.
"""
import ast
import json
import os
import requests

from isales.logger import logger
from isales.redis_connector import RedisConnectionManager


class RedisReader:
    def __init__(self, queue_to_read=None):
        self.redis_client = RedisConnectionManager()
        self._max_buffer = os.environ["MAX_BUFFER"]
        if queue_to_read:
            self.queue_to_read = queue_to_read
        else:
            self.queue_to_read = os.environ["QUEUE_TO_READ"]

    def __call__(self):
        return self._read_from_redis()

    def _read_from_redis(self):
        """Reads nested data from redis queue and formats this data into a list of dictonaries"""
        subscription_items = []
        items = self.redis_client.lrange(self.queue_to_read, 0, self._max_buffer)

        for item in items:
            parsed_item = ast.literal_eval(item.decode("utf-8"))
            subscription_items = subscription_items + parsed_item

        logger.info(msg="")
        return subscription_items

    def remove_items(self):
        """Removes data from Redis"""
        self.redis_client.lrem(self.queue_to_read, 0, self._max_buffer)


class HubSpotFetcher:
    def __init__(self):
        self.redis_client = RedisConnectionManager()
        self._deal_api_url = os.environ["DEAL_API_URL"]
        self._contact_api_url = os.environ["CONTACT_API_URL"]
        self._contact_creation_subscription = os.environ["CONTACT_CREATION_SUBSCRIPTION"]

    def __call__(self, deal_items):
        return self._fetch_from_hubspot(deal_items)

    def _fetch_from_hubspot(self, subscription_items):
        """Fetches deal and associated contact information from HubSpot database"""
        fetched_data = {"predictable_contacts": [], "non_predictable_contacts": []}
        for item in subscription_items:
            if item["subscriptionType"] == self._contact_creation_subscription:
                fetched_data["non_predictable_contacts"].append(item)
            else:
                url = self._build_url(self._deal_api_url, item["objectId"])
                deal = self._request(url)
                if deal:
                    try:
                        contacts_id = deal["associations"]["associatedVids"]
                        if contacts_id:
                            url = self._build_url(self._contact_api_url, *contacts_id)
                            contacts = self._request(url)
                            if contacts:
                                fetched_data["predictable_contacts"].append(contacts)
                        else:
                            logger.error(msg="Deal with no contact associated")
                    except (KeyError, TypeError) as err:
                        logger.error(
                            msg="Deal with no contact associated",
                            extra={"full_msg_error": err},
                        )

        return fetched_data

    def _request(self, url):
        """Requests data from HubSport Database"""
        access_token = self.redis_client.get("acces_token").decode("utf-8")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        if response.staus_code == 200:
            return json.loads(response.text)
        return None

    @staticmethod
    def _build_url(base_url, *ids_to_fetch):
        """ Builds urls to fetch both deal and contact information"""
        iterable = iter(ids_to_fetch)
        url = f"{base_url}{next(iterable)}"
        if len(ids_to_fetch) > 1:
            for id in iterable:
                url = f"{url}&vid={id}"
        return url
