#!/bin/usr/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 03 01:41 BRT 2020
Modified on Fri Apr 03 23:52 BRT 2020
Author: guilhermepassos@outlook.com | twitter: @gpass0s

This module inserts contact's prediction in HubSpot database
"""
import requests
import os

from isales.redis_cli import RedisConnectionManager, RedisReader, try_again
from isales.logger import logger


class HubSpotWriter:
    def __init__(self):
        self.redis_client = RedisConnectionManager().get_client()
        self.redis_reader = RedisReader(
            os.environ["CONTATCS_FOR_UPDATE_QUEUE"], os.environ["MAX_BUFFER_SENDER"]
        )
        self.contact_post_api_url = os.environ["CONTACT_POST_API_URL"]
        self.payload = []

    def __call__(self):
        contacts_for_update = self.redis_reader()
        self.payload.clear()
        self._build_payload(contacts_for_update)
        self._update()
        self.redis_reader.remove_items()

    def _build_payload(self, contacts_for_update):

        for contact in contacts_for_update:
            contact_payload = {
                "vid": contact["contact_id"],
                "properties": [{"property": "ML", "value": contact["prediction"]}],
            }
            self.payload.append(contact_payload)

    @try_again
    def _update(self):
        """Sends a http request to HubSpot"""
        access_token = self.redis_client.get("access_token").decode("utf-8")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            url=self.contact_post_api_url, headers=headers, data=self.payload
        )
        if response.status_code == 202:
            logger.info(msg=f"{len(self.payload)} contacts were updated in Hubspot.")
