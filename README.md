# Central Historic DQM application for CMS detector

The web application is available here: https://historicdqm.web.cern.ch

## How to update?

The code is running on a `vocms0231` machine. Bellow are the update instructions:

* Navigate to `/data/hdqm/`
* Run `update.sh`
* Code from the master branch of this repository will be fetched and started to be served.

## Where does the data come from?

Data is not present in this repository but code expects to find it under `/data/hdqm/data/` directory. `update.sh` will make sure that previous data is used for the updated version. In order to update the data, it has to be regenerated an placed in the directory mentioned above. 

## How to run locally

``` bash
ssh -L 8000:localhost:8000 -L 8080:localhost:5000 lxplus7.cern.ch
mkdir -p /tmp/$USER/hdqm
cd /tmp/$USER/hdqm/

git clone --branch backend-development https://github.com/andrius-k/CentralHDQM
cd CentralHDQM/

cd backend/extractor/
source cmsenv

# Extract few DQM histograms. Using only one process because we are on the SQLite
./hdqmextract.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 325684 325688 325698 -j 1

# Calculate HDQM values from DQM histograms stored in the DB
./calculate.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 325684 325688 325698 -j 1

cd ../api/
./run.sh &>/dev/null &

cd ../../frontend/
# Use local API instead of the production one
sed -i 's/vocms0231.cern.ch/localhost/g' js/config.js
python3 -m http.server 8000 &>/dev/null &

# Now visit http://localhost:8000/ on your browser

# Run this to find pids of running servers:
# ps awwx | grep python
```
