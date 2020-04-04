#!/bin/usr/python3
# --*-- coding: utf-8 --*--
"""
Created on Tue Mar 31 15:11 BRT 2020
Last modified on
Author: guilhermepassos@outlook.com | twitter: @gpass0s

This module tests preprocessor module's methods
"""
import pytest
from unittest.mock import call, patch

from isales import preprocessor
from isales.preprocessor import Transformer

_PREDICTABLE_CONTACTS = [
    {
        "383216495": {
            "vid": "383216495",
            "properties": {
                "num_unique_conversion_events": {"value": "1"},
                "program_duration": {"value": "Ainda não sei"},
                "num_associated_deals": {"value": "1"},
                "num_conversion_events": {"value": "2"},
                "country_of_interest": {"value": "EUA"},
                "idade": {"value": "24"},
                "num_contacted_notes": {"value": "1"},
                "num_notes": {"value": "1"},
            },
        },
        "383216724": {
            "vid": "383216724",
            "properties": {
                "num_unique_conversion_events": {"value": "2"},
                "program_duration": {"value": "8 Semanas"},
                "num_associated_deals": {"value": "1"},
                "num_conversion_events": {"value": "2"},
                "country_of_interest": {"value": "UK"},
                "idade": {"value": "21"},
                "num_contacted_notes": {"value": "2"},
                "num_notes": {"value": "3"},
            },
        },
    }
]

_NON_PREDICTABLE_CONTACTS = [
    {"objectId": 383611195, "subscriptionType": "contact.creation"},
    {"objectId": 383216724, "subscriptionType": "contact.creation"},
]


@pytest.fixture
@patch.dict("os.environ", {"CONTATCS_FOR_PREDICTION_QUEUE": "CONTACTS_FOR_PREDICTION"})
@patch.dict("os.environ", {"CONTATCS_FOR_UPDATE_QUEUE": "CONTACTS_FOR_UPDATE"})
@patch.dict("os.environ", {"PREDICTABLE_CONTACTS_QUEUE": "PREDICTABLE_CONTACTS"})
@patch.dict("os.environ", {"MAX_BUFFER": "10"})
@patch.object(preprocessor, "RedisReader")
@patch.object(preprocessor, "RedisWriter")
def preprocessor_object(RedisWriter, RedisReader):
    preprocessor = Transformer()
    return preprocessor


@patch.object(Transformer, "_extract_contact_main_info")
def test_format_predictable_contacts(
    mocked_extract_contact_main_info, preprocessor_object
):

    # arrange
    mocked_extract_contact_main_info.return_value = "contact"
    calls = [
        call(
            "383216495",
            {
                "num_unique_conversion_events": {"value": "1"},
                "program_duration": {"value": "Ainda não sei"},
                "num_associated_deals": {"value": "1"},
                "num_conversion_events": {"value": "2"},
                "country_of_interest": {"value": "EUA"},
                "idade": {"value": "24"},
                "num_contacted_notes": {"value": "1"},
                "num_notes": {"value": "1"},
            },
        )
    ]
    # act
    preprocessor_object._format_predictable_contacts(_PREDICTABLE_CONTACTS)
    # assert
    mocked_extract_contact_main_info.assert_has_calls(calls)
    preprocessor_object.contacts["CONTACTS_FOR_PREDICTION"] == "contact"


@patch.object(Transformer, "_extract_contact_main_info")
def test_format_predictable_contacts_with_no_deal(
    mocked_extract_contact_main_info, preprocessor_object
):

    # arrange
    mocked_extract_contact_main_info.return_value = None
    expected_response = [
        {"contact_id": "383216495", "prediction": "404"},
        {"contact_id": "383216724", "prediction": "404"},
    ]
    # act
    preprocessor_object._format_predictable_contacts(_PREDICTABLE_CONTACTS)
    # assert
    assert preprocessor_object.contacts["CONTACTS_FOR_UPDATE"] == expected_response


def test_extract_contact_main_info(preprocessor_object):

    # arange
    expected_response = {
        "contact_id": "383216724",
        "País de interesse": "UK",
        "Qual a duração do seu intercâmbio?": 8,
        "Idade": 21,
        "Associated Deals": 1,
        "Number of times contacted": 2,
        "Number of Sales Activities": 3,
        "Number of Unique Forms Submitted": 2,
        "Number of Form Submissions": 2,
    }
    contact_properties = _PREDICTABLE_CONTACTS[0]["383216724"]["properties"]
    # act
    contact = preprocessor_object._extract_contact_main_info(
        "383216724", contact_properties
    )
    # assert
    assert contact == expected_response
