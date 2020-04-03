#!/usr/bin/python3
# -*- encoding: utf-8 -*-
"""
Created on Sun Mar 29 08:25 BRT 2020
Last modified on Fri 03 18:41 BRT 2020
author: guilherme passos | twitter: @gpass0s

This module reads the new events that are arriving in a redis subscription queue, fetches these
events information from HubSpot database and writes the fetched data in another redis queue.
"""
import json
import os
import requests

from isales.logger import logger
from isales.redis_cli import RedisConnectionManager, RedisReader, RedisWriter, try_again


class HubSpotFetcher:
    """Fetches deals and contact information in Hubspot"""

    def __init__(self, queue_to_read=None):
        self.redis_client = RedisConnectionManager().get_client()
        self.deal_api_url = os.environ["DEAL_API_URL"]
        self.contact_api_url = os.environ["CONTACT_GET_API_URL"]
        self.contact_creation_subscription = os.environ["CONTACT_CREATION_SUBSCRIPTION"]
        self.predictable_contacts = os.environ["PREDICTABLE_CONTACTS_QUEUE"]
        self.contacts_for_update_queue = os.environ["CONTATCS_FOR_UPDATE_QUEUE"]

        max_buffer = os.environ["MAX_BUFFER"]
        if queue_to_read is None:
            self.redis_reader = RedisReader(os.environ["QUEUE_TO_READ"], max_buffer)
        else:
            self.redis_reader = RedisReader(queue_to_read, max_buffer)

        self.redis_writer = RedisWriter()
        self.contacts_id_to_fetch = []
        self.contacts = {
            self.predictable_contacts: [],
            self.contacts_for_update_queue: [],
        }

    def __call__(self):
        subscription_items = self.redis_reader()
        self.contacts[self.predictable_contacts].clear()
        self.contacts[self.contacts_for_update_queue].clear()
        self._fetch_from_hubspot(subscription_items)
        if self.contacts_id_to_fetch:
            self._fetch_contact_info()

        self.redis_writer(self.contacts)
        self.redis_reader.remove_items()

    def _fetch_from_hubspot(self, subscription_items):
        """Fetches deals and contacts information from HubSpot database"""
        self.contacts_id_to_fetch.clear()
        processed_items = {}
        for item in subscription_items:
            subscription_type = item["subscriptionType"]
            object_name = item["subscriptionType"].split(".")[0]

            # better ask for forgiveness than permission
            try:
                processed_items[item["objectId"]]
            except KeyError:
                if subscription_type == self.contact_creation_subscription:
                    self._format_new_contact(item["objectId"])
                elif object_name == "deal":
                    self._fetch_deal_info(item["objectId"])
                elif object_name == "contact":
                    self.contacts_id_to_fetch.append(item["objectId"])

                if len(self.contacts_id_to_fetch) > 99:
                    self._fetch_contact_info()

                processed_items[item["objectId"]] = True

    def _format_new_contact(self, contact_id):
        """Assigns prediction equals to 0 in contacts recently created"""
        new_contact = {"contact_id": contact_id, "prediction": "0"}
        self.contacts[self.contacts_for_update_queue].append(new_contact)

    def _fetch_deal_info(self, deal_id):
        """ Fetches a deal information from Hubspot database"""
        url = self._build_url(self.deal_api_url, deal_id)
        deal = self._request(url)
        try:
            contacts_id = deal["associations"]["associatedVids"]
            if contacts_id:
                self.contacts_id_to_fetch = self.contacts_id_to_fetch + contacts_id
        except (KeyError, TypeError) as err:
            logger.error(
                msg="Deal with no contact associated", extra={"full_msg_error": err},
            )

    def _fetch_contact_info(self):
        """Fetches a contact information from Hubspot database"""
        url = self._build_url(self.contact_api_url, *self.contacts_id_to_fetch)
        contacts_fetched = self._request(url)
        if contacts_fetched:
            self.contacts[self.predictable_contacts].append(contacts_fetched)
            self.contacts_id_to_fetch.clear()
            logger.info(msg=f"Fetched {len(self.contacts_id_to_fetch)} contact's info")

    @try_again
    def _request(self, url):
        """Sends a http request to HubSpot"""
        access_token = self.redis_client.get("access_token").decode("utf-8")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
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
