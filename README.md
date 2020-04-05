==================================
# Insight Sales | HubSpot Project
==================================

> This project aims to create an automated and near real time service that predicts Hubspot contact's probability to buy exchange programs. In its main core, this project uses a XGboost model which was 
trained with more than 10 thousands Hubspot records of leads buying pattern. 

> In order to receive data from Hubspot, this project relies on a Google Cloud Function which works
as a producer sending events to a redis queue. The GCP function is subscribed to HubSpot through a 
webhook service which triggers this function everytime a contact is created or modified in Hubspot. 
Then, this project's <a href=https://github.com/gPass0s/isales/blob/master/isales/collector.py>collector</a> module reads the redis subscription queue, fetches contacts main information from Hubspot database and sends all this data to the <a href=https://github.com/gPass0s/isales/blob/master/isales/preprocessor.py> preprocessor</a> module through another redis queue. Next, the preprocessor module enhances the fetched data for the prediction stage. After all that, the 
<a href=https://github.com/gPass0s/isales/blob/master/isales/model.py>model</a> module predicts contact's
propability to buy exchange programs by using a Xgboost machine learning model. 

> Finally, predictions generated by the ML model are sent to Hubspot database by the <a href=https://github.com/gPass0s/isales/blob/master/isales/sender.py>sender</a> module.
At the end of the day, these predicitons help sales representatives to decide which contacts they should invest their time.

## Project Architecture

<p align="center">
  <img src="https://i.imgur.com/IkGcNAV.png"/>
  <br/>
</p>


## Motivation

* Optimizes Hubspot sales representative's time.
* Ensures machine learning models ability of generating useful and real life insights 

## How to use it

### Requirements

* Hubspot <a href= https://developers.hubspot.com/docs/methods/webhooks/webhooks-overview>webhook API</a> subscription. 
* <a href = https://cloud.google.com/functions>Google Cloud</a> or <a href ="https://aws.amazon.com/lambda/?nc1=h_ls">AWS Lambda</a> function. The function code can be found <a href=https://github.com/gPass0s/isales/tree/master/utils/gcp_function>here</a>.
* <a href= "https://redis.io/"> Redis </a> server.
* <a href= https://github.com/gPass0s/isales/blob/master/utils/crontab>Cronjob </a>to refresh the Hupspot API token each 6 hours. 

### Usage

* Clone this repository: `$ git clone git@github.com:gPass0s/isales.git`
* Access the project root folder: `$ cd isales`
* Rename the enviroment file: `$ mv .env.template env`
* Dockerize: `$ docker build --no-cache -t isales:latest -f Dockerfile .`
* Run **collector** service: `$ docker run -d -it --name collector --network host --env-file env isales:latest python isales run collector`
* Run **preprocessor** service : `$ docker run -d -it --name collector --network host --env-file env isales:latest python isales run preprocessor`
* Run **model** service: `$ docker run -d -it --name collector --network host --env-file env isales:latest python isales run model`
* Run **sender** service: `$ docker run -d -it --name collector --network host --env-file env isales:latest python isales run model`

### Unit testing
* Activate the virtual enviroment: `$ pipenv install && pipenv shell`
* Run tests: `$ pipenv run python -m pytest --vv tests/`
