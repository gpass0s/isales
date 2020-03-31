#!/bin/usr/python3
# -*- conding: utf-8 -*-
"""
Created on Sun Mar 30 19:54 BRT 2020

author: guilherme passos | twitter: @gpass0s

This module spplits the data fecthed from Hubspot into two diffent Redis queue. They are:
Predictable contacts queue and Non-predictable contacts queue.
"""
import os

from isales.redis_connector import RedisConnectionManager
from isales.logger import logger


class Splitter:
    def __init__(self):
        self.redis_client = RedisConnectionManager()
        self._to_predict_queue = os.environ["TO_PREDICT_QUEUE"]
        self._to_go_queue = os.environ["TO_GO_QUEUE"]

    def __call__(self, fetched_data):
        self._format_contacts_for_prediction(fetched_data["predictable_contacts"])
        self._insert_new_contacts_in_redis(fetched_data["non_predictable_contacts"])

    def _format_contacts_for_prediction(self, deal_contacts):
        """Formats contacts to be predict by the Machine Learning model"""
        for contact in deal_contacts:
            for key in contact.keys():
                contact_main_info = contact[key]["properties"]
                try:
                    predictable_contact = {
                        "contact_id": int(key),
                        "País de interesse": contact_main_info["country_of_interest"][
                            "value"
                        ],
                        "Qual a duração do seu intercâmbio?": contact_main_info[
                            "program_duration"
                        ]["value"],
                        "Idade": int(contact_main_info["idade"]["value"]),
                        "Associated Deals": int(
                            contact_main_info["num_associated_deals"]["value"]
                        ),
                        "Number of times contacted": int(
                            contact_main_info["num_contacted_notes"]["value"]
                        ),
                        "Number of Sales Activities": int(
                            contact_main_info["num_notes"]["value"]
                        ),
                        "Number of Unique Forms Submitted": int(
                            contact_main_info["num_unique_conversion_events"]["value"]
                        ),
                        "Number of Form Submissions": int(
                            contact_main_info["num_conversion_events"]["value"]
                        ),
                    }
                    self._insert_to_redis(self._to_predict_queue, predictable_contact)
                except (KeyError, TypeError) as err:
                    logger.error(
                        msg="Contact is not predictable due to missing information",
                        extra={"Full msg error": err},
                    )

    def _format_new_contacts_for_update(self, new_contacts):
        """Assigns the 'No deal associated' label to the new contacts created"""
        for contact in new_contacts:
            non_predictable_contact = {
                "contact_id": int(contact["objectId"]),
                "predction": "No deal associated",
            }
            self._insert_to_redis(self._to_go_queue, non_predictable_contact)

    def _insert_to_redis(self, queue, contact):
        """Inserts contacts in Redis to be processed"""
        self.redis_client.rpush(queue, contact)
        logger.info(msg=f"Contact successfully inserted into {queue} queue.")
