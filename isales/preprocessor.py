#!/bin/usr/python3
# -*- conding: utf-8 -*-
"""
Created on Sun Mar 30 19:54 BRT 2020
Last modified on Fri 03 22:39 BRT 2020
author: guilherme passos | twitter: @gpass0s

This module prepares contacts fetched from Hubspot for prediction. Those contacts that don't enough 
information are assigned with the 404 prediction
"""
import os
import re

from isales.logger import logger
from isales.redis_cli import RedisReader, RedisWriter


class Transformer:
    def __init__(self):
        self.contacts_for_prediction = os.environ["CONTATCS_FOR_PREDICTION_QUEUE"]
        self.contacts_for_update = os.environ["CONTATCS_FOR_UPDATE_QUEUE"]
        max_buffer = int(os.environ["MAX_BUFFER"]) + 47
        self.redis_reader = RedisReader(
            os.environ["PREDICTABLE_CONTACTS_QUEUE"], max_buffer
        )
        self.redis_writer = RedisWriter()
        self.contacts = {self.contacts_for_prediction: [], self.contacts_for_update: []}

    def __call__(self):
        predictable_contacts = self.redis_reader()
        self.contacts[self.contacts_for_prediction].clear()
        self.contacts[self.contacts_for_update].clear()
        self._format_predictable_contacts(predictable_contacts)
        self.redis_writer(self.contacts)
        self.redis_reader.remove_items()

    def _format_predictable_contacts(self, predictable_contacts):
        """Formats contacts to be predict by the Machine Learning model"""
        processed_contacts = {}
        for contact in predictable_contacts:
            for key in contact.keys():
                # better ask for forgiveness than permission
                try:
                    processed_contacts[key]
                except KeyError:
                    contact_properties = contact[key]["properties"]
                    contact_info = self._extract_contact_main_info(
                        key, contact_properties
                    )
                    if contact_info:
                        self.contacts[self.contacts_for_prediction].append(contact_info)
                    else:
                        contact_info = self._format_non_predictable_contact(key)
                        self.contacts[self.contacts_for_update].append(contact_info)
                    processed_contacts[key] = True

    def _extract_contact_main_info(self, contact_id, contact_properties):

        try:
            contact = {
                "contact_id": contact_id,
                "País de interesse": contact_properties["country_of_interest"]["value"],
                "Qual a duração do seu intercâmbio?": contact_properties[
                    "program_duration"
                ]["value"],
                "Idade": int(contact_properties["idade"]["value"]),
                "Associated Deals": int(
                    contact_properties["num_associated_deals"]["value"]
                ),
                "Number of times contacted": int(
                    contact_properties["num_contacted_notes"]["value"]
                ),
                "Number of Sales Activities": int(
                    contact_properties["num_notes"]["value"]
                ),
                "Number of Unique Forms Submitted": int(
                    contact_properties["num_unique_conversion_events"]["value"]
                ),
                "Number of Form Submissions": int(
                    contact_properties["num_conversion_events"]["value"]
                ),
            }
            self._convert_program_duration_to_int(contact)
            return contact
        except (KeyError, TypeError) as err:
            logger.error(
                msg="Contact is not predictable due to misinformation",
                extra={"Full msg error": err},
            )
            return None

    @staticmethod
    def _format_non_predictable_contact(contact_id):
        """Assigns the '404' label to contacts that does not have enough information """
        non_predictable_contact = {"contact_id": contact_id, "prediction": "404"}
        return non_predictable_contact

    @staticmethod
    def _convert_program_duration_to_int(contact):
        program_duration = re.findall(
            r"\d+", contact["Qual a duração do seu intercâmbio?"]
        )
        if program_duration:
            contact["Qual a duração do seu intercâmbio?"] = int(program_duration[0])
