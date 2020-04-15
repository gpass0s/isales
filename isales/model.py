#!/usr/bin/python3
# -*- encoding: utf-8 -*-
"""
Created on Sun on Fri 04 15:34 BRT 2020
Last modified on Fri 12 12:24 BRT 2020
author: guilherme passos | twitter: @gpass0s
"""
import ast
import os
import numpy as np
import pandas as pd

from isales.model_trainer import ModelTrainer
from isales.redis_cli import RedisReader, RedisWriter
from isales.logger import logger


class Predictor:
    def __init__(self):

        self.queue_to_read = os.environ["CONTATCS_FOR_PREDICTION_QUEUE"]
        self.contacts_for_update = os.environ["CONTATCS_FOR_UPDATE_QUEUE"]
        self.redis_reader = RedisReader(
            self.queue_to_read, os.environ["MAX_BUFFER_MODEL"]
        )
        self.redis_writer = RedisWriter()
        self.relevant_columns = ast.literal_eval(
            ast.literal_eval(os.environ["DATA_TRAIN_COLUMNS"])
        )
        train_objects = ModelTrainer()()
        self.model = train_objects["model"]
        self.reference_dicts = train_objects["reference_dicts"]
        self.contacts = {self.contacts_for_update: []}
        self.dataframe = pd.DataFrame()

    def __call__(self):
        self.contacts_for_prediction = self.redis_reader()
        if self.contacts_for_prediction:
            logger.info(msg="Data extracted from redis")
            self.dataframe = pd.DataFrame(self.contacts_for_prediction)

            if self._convert_strings_to_int() is None:
                self._build_contacts_for_update()
            else:
                self._check_for_strings_in_dataframe()
                predictions = self._generate_predictions()
                self._build_contacts_for_update(predictions=predictions)

            self.redis_writer(self.contacts)
            self.redis_reader.remove_items()
            self.contacts[self.contacts_for_update].clear()

    def _convert_estunidos_to_eua(self):

        self.dataframe.loc[
            self.dataframe.loc[
                self.dataframe["País de interesse"] == "Estados Unidos"
            ].index,
            "País de interesse",
        ] = "EUA"

    def _convert_strings_to_int(self):

        try:
            for column in self.reference_dicts.keys():
                for label in self.reference_dicts[column].keys():
                    self.dataframe.loc[
                        self.dataframe.loc[self.dataframe[column] == label].index,
                        column,
                    ] = self.reference_dicts[column][label]

            return True
        except KeyError as err:
            logger.error(
                msg="Unknown column. It's not possible to generate predictions",
                extra={"Full msg error": err},
            )
            return None

    def _check_for_strings_in_dataframe(self):

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

                try:
                    highest_code = self._find_highest_code(self.reference_dicts[column])
                    self.dataframe.loc[
                        self.dataframe[column].apply(lambda x: isinstance(x, str))
                        == True,
                        column,
                    ] = highest_code
                except KeyError:
                    logger.info(msg=f"Column {column} not found in the references")

    def _find_highest_code(self, reference_dict):

        highest_code = 0
        for label in reference_dict.keys():
            if reference_dict[label] > highest_code:
                highest_code = reference_dict[label]

        return highest_code + 1

    def _generate_predictions(self):
        self.dataframe.loc[
            self.dataframe["Qual a duração do seu intercâmbio?"] == "Ainda não sei",
            "Qual a duração do seu intercâmbio?",
        ] = np.nan
        dataframe_for_predicttion = self.dataframe.loc[:, self.relevant_columns]
        dataframe_for_predicttion = ModelTrainer.fill_empty_fields(
            dataframe_for_predicttion
        )
        predictions = self.model.predict_proba(dataframe_for_predicttion) * 100
        logger.info(msg="Predicitions generated")
        return predictions

    def _build_contacts_for_update(self, predictions=None):
        contacts_id = self.dataframe["contact_id"]
        i = 0
        for contact_id in contacts_id:
            if predictions is None:
                contact = {"contact_id": contact_id, "prediciton": "400"}
            else:
                predicton = str(round(predictions[i][0], 2))
                contact = {"contact_id": contact_id, "prediction": predicton}
            self.contacts[self.contacts_for_update].append(contact)
            i += 1
