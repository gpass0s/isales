#!/bin/usr/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 03 01:41 BRT 2020
Last modified on Fri 04 15:34 BRT 2020
Author: guilhermepassos@outlook.com | twitter: @gpass0s

This module inserts contact's prediction in HubSpot database
"""
import json
import requests
import os

from isales.redis_cli import RedisConnectionManager, RedisReader, RedisWriter, try_again
from isales.logger import logger


class HubSpotWriter:
    def __init__(self):
        self.redis_client = RedisConnectionManager().get_client()
        self.queue_to_read = os.environ["CONTATCS_FOR_UPDATE_QUEUE"]
        self.redis_reader = RedisReader(
            self.queue_to_read, os.environ["MAX_BUFFER_SENDER"]
        )
        self.redis_writer = RedisWriter()
        self.contact_post_api_url = os.environ["CONTACT_POST_API_URL"]
        self.payload = []
        self.contacts_for_update = []

    def __call__(self):
        self.contacts_for_update = self.redis_reader()
        self.payload.clear()
        self._build_payload()

        if self.payload:
            self._update()
            self.redis_reader.remove_items()

    def _build_payload(self):
        processed_contact = {}
        for contact in self.contacts_for_update:
            # better ask for forgiveness than permission
            try:
                processed_contact[contact["contact_id"]]
            except KeyError:
                contact_payload = {
                    "vid": contact["contact_id"],
                    "properties": [{"property": "ML", "value": contact["prediction"]}],
                }
                self.payload.append(contact_payload)
                processed_contact[contact["contact_id"]] = True

    @try_again
    def _update(self):
        """Sends a http request to HubSpot"""
        access_token = self.redis_client.get("access_token").decode("utf-8")
        headers = {"Authorization": f"Bearer {access_token}"}
        data = json.dumps(self.payload)
        url = f"{self.contact_post_api_url}/batch"
        response = requests.post(url=url, headers=headers, data=data)
        if response.status_code == 202:
            logger.info(msg=f"{len(self.payload)} contacts were updated in Hubspot.")
        else:
            logger.error(
                msg=f"Error while updating contants",
                extra={"status_code": response.status_code},
            )
            logger.info(msg="Contacts will be inserted separately")
            for contact in self.contacts_for_update:
                access_token = self.redis_client.get("access_token").decode("utf-8")
                headers = {"Authorization": f"Bearer {access_token}"}
                contact_payload = json.dumps(
                    {
                        "properties": [
                            {"property": "ML", "value": contact["prediction"]}
                        ],
                    }
                )
                url = f"{self.contact_post_api_url}vid/{contact['contact_id']}/profile?"
                res = requests.post(url=url, headers=headers, data=contact_payload)
                logger.info(
                    msg=f"status_code: {res.status_code}", extra={"full_msg": res.text}
                )
                if res.status_code == 429:
                    logger.error(
                        msg="429 - Ten sencondly rolling limit reached",
                        extra={"full_msg": res.text},
                    )
                    contact_wrapper = {self.queue_to_read: [contact]}
                    self.redis_writer(contact_wrapper)
