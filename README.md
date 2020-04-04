==================================
## Insight Sales | HubSpot Project
==================================

This project aims to create an automated and near real time service that predicts HubSpot contact's probability to buy exchange program packages. In its main core, this project uses a XGboost model that was 
trained with more than 10 thousands HubSpot records of leads buying pattern. 

In order to receive data from Hubspot, this project uses a Google Cloud Function which works
as a producer sending data to a Redis queue. The GCP function is subscribed to HubSpot through a 
webhook service that triggers this function everytime a contact is created or modified. 
Then, this project's <a href=https://github.com/gPass0s/isales/blob/master/isales/collector.py>collector</a> module reads the Redis queue, fetches contacts main information in HS database and sends all this data to the <a href=https://github.com/gPass0s/isales/blob/master/isales/preprocessor.py> preprocessor</a> module. Next,the preprocessor module enhances the fetched data for the prediction stage. After all that, the 
<a href=https://github.com/gPass0s/isales/blob/master/isales/model.py>model</a>module predicts lead's
propability to buy an exchange program by using a Xgboost machine learning model. 

Finally, predictions generated by the ML model are sent to Hubspot database by the <a href=https://github.com/gPass0s/isales/blob/master/isales/sender.py>sender</a> module.
At the end of the day, these predicitons help sellers to decide which contacts they should invest their time. 
