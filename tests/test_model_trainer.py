#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 12 14:44 BRT 2020

author: guilherme passos | twitter: @gpass0s

This module tests model trainer module methods
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from isales import model_trainer
from isales.model_trainer import ModelTrainer


@pytest.fixture
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
@patch.object(model_trainer, "pd")
@patch.object(model_trainer, "xgb")
def model_trainer_object(mocked_xgb, mocked_pd):
    trainer = ModelTrainer()
    return trainer


def test_prepare_data(model_trainer_object):
    # arrange
    exchange_duration = ["Ainda não sei", "8 Semanas", "7 Semanas", "1 Semana"]
    ages = [-1, 91, 20, None]
    test_dataframe = pd.DataFrame(
        {"Qual a duração do seu intercâmbio?": exchange_duration, "Idade": ages}
    )
    expected_dataframe = pd.DataFrame(
        {
            "Qual a duração do seu intercâmbio?": [np.nan, 8, 7, 1],
            "Idade": [20.0, 20.0, 20.0, 20.0],
        }
    )
    model_trainer_object.dataframe = test_dataframe
    # act
    model_trainer_object._prepare_data()
    # assert

    assert model_trainer_object.dataframe.equals(expected_dataframe)


def test_convert_strings_to_int(model_trainer_object):
    # arrange
    countries = ["EUA", "Canadá", "Malta", "Austrália"]
    test_dataframe = pd.DataFrame({"countries": countries})
    expected_result = {"countries": {"Austrália": 0, "Canadá": 1, "EUA": 2, "Malta": 3}}
    model_trainer_object.dataframe = test_dataframe
    # act
    model_trainer_object._convert_strings_to_int()
    # assert

    assert model_trainer_object.reference_dicts == expected_result
