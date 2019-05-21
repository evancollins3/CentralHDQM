# Central Historic DQM application for CMS detector


## How to update?

The code is running on a `vocms0231` machine. Bellow are the update instructions:

* Navigate to `/data/hdqm/`
* Run `update.sh`
* Code from the master branch of this repository will be fetched and started to be served.

## Where does the data come from?

Data is not present in this repository but code expects to find it under `/data/hdqm/data/` directory. `update.sh` will make sure that previous data is used for the updated version. In order to update the data, it has to be regenerated an placed in the directory mentioned above. 
