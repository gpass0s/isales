#!/bin/usr/python3
# --*-- coding: utf-8 --*--
"""
Created on Tue Mar 31 15:11 BRT 2020
Last modified on
Author: guilhermepassos@outlook.com | twitter: @gpass0s

This module tests splitter module's methods
"""

from unittest.mock import call, patch

from isales import splitter
from isales.splitter import Splitter

_PREDICTABLE_CONTACTS = [
    {
        "383216495": {
            "vid": 383216495,
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
            "vid": 383216724,
            "properties": {
                "num_unique_conversion_events": {"value": "2"},
                "program_duration": {"value": "Semanas"},
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


@patch.dict("os.environ", {"TO_PREDICT_QUEUE": "TO_PREDICT"})
@patch.dict("os.environ", {"TO_GO_QUEUE": "TO_GO"})
@patch.object(splitter, "RedisConnectionManager", autospec=True)
@patch.object(Splitter, "_insert_to_redis")
def test_format_contacts_for_prediction(
    mocked_insert_to_redis, mocked_redis_connection_manager
):

    splitter = Splitter()
    splitter._format_contacts_for_prediction(_PREDICTABLE_CONTACTS)

    calls = [
        call(
            "TO_PREDICT",
            {
                "contact_id": 383216495,
                "País de interesse": "EUA",
                "Qual a duração do seu intercâmbio?": "Ainda não sei",
                "Idade": 24,
                "Associated Deals": 1,
                "Number of times contacted": 1,
                "Number of Sales Activities": 1,
                "Number of Unique Forms Submitted": 1,
                "Number of Form Submissions": 2,
            },
        ),
        call(
            "TO_PREDICT",
            {
                "contact_id": 383216724,
                "País de interesse": "UK",
                "Qual a duração do seu intercâmbio?": "Semanas",
                "Idade": 21,
                "Associated Deals": 1,
                "Number of times contacted": 2,
                "Number of Sales Activities": 3,
                "Number of Unique Forms Submitted": 2,
                "Number of Form Submissions": 2,
            },
        ),
    ]

    mocked_insert_to_redis.assert_has_calls(calls, any_order=False)


@patch.dict("os.environ", {"TO_PREDICT_QUEUE": "TO_PREDICT"})
@patch.dict("os.environ", {"TO_GO_QUEUE": "TO_GO"})
@patch.object(splitter, "RedisConnectionManager", autospec=True)
@patch.object(Splitter, "_insert_to_redis")
def test_format_contacts_for_prediction_avoiding_missing_data(
    mocked_insert_to_redis, mocked_redis_connection_manager,
):

    splitter = Splitter()
    _predictable_contacts = _PREDICTABLE_CONTACTS[0]
    del _predictable_contacts["383216495"]["properties"]["program_duration"]
    splitter._format_contacts_for_prediction([_predictable_contacts])

    calls = [
        call(
            "TO_PREDICT",
            {
                "contact_id": 383216724,
                "País de interesse": "UK",
                "Qual a duração do seu intercâmbio?": "Semanas",
                "Idade": 21,
                "Associated Deals": 1,
                "Number of times contacted": 2,
                "Number of Sales Activities": 3,
                "Number of Unique Forms Submitted": 2,
                "Number of Form Submissions": 2,
            },
        )
    ]
    mocked_insert_to_redis.assert_has_calls(calls, any_order=False)


@patch.dict("os.environ", {"TO_PREDICT_QUEUE": "TO_PREDICT"})
@patch.dict("os.environ", {"TO_GO_QUEUE": "TO_GO"})
@patch.object(splitter, "RedisConnectionManager", autospec=True)
@patch.object(Splitter, "_insert_to_redis")
def test_format_contacts_for_prediction_avoid_missing_data(
    mocked_insert_to_redis, mocked_redis_connection_manager,
):

    splitter = Splitter()
    splitter._format_new_contacts_for_update(_NON_PREDICTABLE_CONTACTS)

    calls = [
        call("TO_GO", {"contact_id": 383611195, "predction": "No deal associated"}),
        call("TO_GO", {"contact_id": 383216724, "predction": "No deal associated"}),
    ]

    mocked_insert_to_redis.assert_has_calls(calls, any_order=False)
