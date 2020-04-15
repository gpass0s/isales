#!/usr/bin/python3
# -*- enconding: utf-8 -*-
"""
Created on Mon 13 22:22 BRT 2020

author: guilherme passos | twitter: @gass0s
"""
import pandas as pd
import pytest
from unittest.mock import patch

from isales import model
from isales.model import Predictor


@pytest.fixture
@patch.dict("os.environ", {"CONTATCS_FOR_PREDICTION_QUEUE": "CONTACTS_FOR_PREDICTION"})
@patch.dict("os.environ", {"CONTATCS_FOR_UPDATE_QUEUE": "CONTATCS_FOR_UPDATE"})
@patch.dict("os.environ", {"MAX_BUFFER_MODEL": "20"})
@patch.dict(
    "os.environ",
    {
        "DATA_TRAIN_COLUMNS": """[
        'País de interesse',
        'Qual a duração do seu intercâmbio?',
        'Idade',
        'Associated Deals',
        'Number of times contacted',
        'Number of Sales Activities',
        'Number of Unique Forms Submitted',
        'Number of Form Submissions']"""
    },
)
@patch.object(model, "ModelTrainer")
@patch.object(model, "RedisReader")
@patch.object(model, "RedisWriter")
def predictor_object(mocked_redis_writer, mocked_redis_reader, mocked_model_trainer):

    predictor = Predictor()
    return predictor


def test_convert_estunidos_to_eua(predictor_object):
    # arrange
    predictor_object.dataframe = pd.DataFrame(
        {"País de interesse": ["Malta", "Estados Unidos"]}
    )
    expected_dataframe = pd.DataFrame({"País de interesse": ["Malta", "EUA"]})

    # act
    predictor_object._convert_estunidos_to_eua()

    # assert
    assert predictor_object.dataframe.equals(expected_dataframe)


def test_convert_strings_to_int(predictor_object):
    # arrange
    predictor_object.reference_dicts = {
        "countries": {"Austrália": 0, "Canadá": 1, "EUA": 2, "Malta": 3}
    }
    predictor_object.dataframe = pd.DataFrame(
        {"countries": ["Austrália", "Canadá", "EUA", "Malta"]}
    )
    # act
    predictor_object._convert_strings_to_int()
    # assert
    assert predictor_object.dataframe.iloc[0, 0] == 0
    assert predictor_object.dataframe.iloc[1, 0] == 1
    assert predictor_object.dataframe.iloc[2, 0] == 2
    assert predictor_object.dataframe.iloc[3, 0] == 3


def test_check_for_strings_in_dataframe(predictor_object):
    # arrange
    predictor_object.reference_dicts = {
        "countries": {"Austrália": 0, "Canadá": 1, "EUA": 2, "Malta": 3}
    }
    predictor_object.dataframe = pd.DataFrame({"countries": [0, 1, 2, 3, "Chile"]})
    # act
    predictor_object._check_for_strings_in_dataframe()
    # assert
    assert predictor_object.dataframe.iloc[4, 0] == 4
