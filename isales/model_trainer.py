#!/usr/bin/python3
# -*- encoding: utf-8 -*-
"""
Created on Sun on Sun 12 12:24 BRT 2020
Last modified on Mon 13 11:33 BRT 2020
author: guilherme passos | twitter: @gpass0s
"""

import ast
import os
import re

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

from isales.logger import logger


class ModelTrainer:
    def __init__(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        self.relevant_columns = ast.literal_eval(
            ast.literal_eval(os.environ["DATA_TRAIN_COLUMNS"])
        )
        self.dataframe = pd.read_csv(f"{dirname}/src/data_train.csv")
        self.dataframe_sold = self.dataframe["Sold"]
        self.model = xgb.XGBClassifier(max_depth=5, n_estimators=500, learning_rate=0.1)
        self.label_encoder = LabelEncoder()
        self.reference_dicts = {}

    def __call__(self):
        self.dataframe = self.dataframe[self.relevant_columns]
        self._prepare_data()
        self._convert_strings_to_int()
        self.dataframe = ModelTrainer.fill_empty_fields(self.dataframe)
        self._fit_model()
        return {"model": self.model, "reference_dicts": self.reference_dicts}

    def _prepare_data(self):

        self.dataframe["Qual a duração do seu intercâmbio?"] = self.dataframe[
            "Qual a duração do seu intercâmbio?"
        ].replace("Ainda não sei", np.nan)
        self.dataframe["Qual a duração do seu intercâmbio?"] = self.dataframe.loc[
            self.dataframe["Qual a duração do seu intercâmbio?"].apply(
                lambda x: isinstance(x, str)
            )
            == True,
            "Qual a duração do seu intercâmbio?",
        ].apply(lambda x: int(re.findall(r"\d+", x)[0]))

        self.dataframe.loc[self.dataframe.Idade < 0, "Idade"] = np.nan
        self.dataframe.loc[self.dataframe.Idade > 90, "Idade"] = np.nan
        self.dataframe["Idade"].fillna(self.dataframe["Idade"].mean(), inplace=True)
        logger.info(msg="Preparing data for training")

    def _convert_strings_to_int(self):

        for column in self.dataframe.columns:
            if (
                len(
                    self.dataframe.loc[
                        self.dataframe[column].apply(lambda x: isinstance(x, str))
                        == True
                    ]
                )
                > 0
            ):
                self.reference_dicts[column] = {}
                self._make_word_dict(column)
                self.dataframe.loc[:, column] = self.label_encoder.fit_transform(
                    self.dataframe[column].astype("str")
                )
        logger.info(msg="Strings were converted to int")

    def _make_word_dict(self, column):

        labels = self.dataframe[column].array
        codes = self.label_encoder.fit_transform(self.dataframe[column].astype("str"))

        for label, code in zip(labels, codes):
            try:
                self.reference_dicts[column][label]
            except KeyError:
                self.reference_dicts[column][label] = code

    @staticmethod
    def fill_empty_fields(dataframe):

        imp = IterativeImputer(max_iter=100, random_state=0)
        imp.fit(dataframe)
        dataframe = imp.transform(dataframe)

        return dataframe

    def _fit_model(self):

        self.model.fit(self.dataframe, self.dataframe_sold)
        logger.info(msg="Model was trained")
