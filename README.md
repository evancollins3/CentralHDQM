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

The folllowing instruction are completely copy-pastable. This will start a complete HDQM stack on your local (lxplus) environment:

``` bash
# You have to change the username. From this point, all instruction can be copy pasted without modifications.
ssh -L 8000:localhost:8000 -L 8080:localhost:5000 akirilov@lxplus7.cern.ch
mkdir -p /tmp/$USER/hdqm
cd /tmp/$USER/hdqm/

git clone --branch backend-development https://github.com/andrius-k/CentralHDQM
cd CentralHDQM/

cd backend/
# This will give us a CMSSW environment
source cmsenv

# Add python dependencies
python3 -m pip install -r requirements.txt -t .python_packages

cd extractor/

# Extract few DQM histograms. Using only one process because we are on SQLite
./hdqmextract.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 324999 325000 325001 -j 1

# Calculate HDQM values from DQM histograms stored in the DB
./calculate.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 324999 325000 325001 -j 1

cd ../api/
# Run the API
./run.sh &>/dev/null &

cd ../../frontend/
# Use local API instead of the production one
sed -i 's/vocms0231.cern.ch/localhost/g' js/config.js
# Run the static file server
python3 -m http.server 8000 &>/dev/null &

# Run this to find pids of running servers to kill them:
# ps awwx | grep python
```

That's it! Now visit http://localhost:8000/ on your browser.

**VERY IMPORTANT:**
OMS data will not yet be present because authentication certificate is required! All features of the entire tool work properly nevertheless.

## How to install locally

If nginx colmplains that it can't bind to port, make sure to request the ports to be opened in puppet:
https://gitlab.cern.ch/ai/it-puppet-hostgroup-vocms/merge_requests/72
And open them using SELinux: `sudo semanage port -m -t http_port_t -p tcp 8081`
Also important:
`sudo firewall-cmd --zone=public --add-port=81/tcp --permanent`
`sudo firewall-cmd --reload`
Make sure to make root directory accessible in SELinux:
`chcon -Rt httpd_sys_content_t /data/hdqmTest/CentralHDQM/frontend/`

