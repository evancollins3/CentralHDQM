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

# Get an SSO to access OMS and RR APIs. This has to be done before cmsenv script
# First check if we are the owner of the folder where we'll be puting the cookie
if [ $(ls -ld /tmp/$USER/hdqm/CentralHDQM/backend/api/etc | awk '{ print $3 }') == $USER ]; then 
    cern-get-sso-cookie -u https://cmsoms.cern.ch/agg/api/v1/runs -o backend/api/etc/oms_sso_cookie.txt
    cern-get-sso-cookie -u https://cmsrunregistry.web.cern.ch/api/json_creation/generate -o backend/api/etc/rr_sso_cookie.txt
fi

cd backend/
# This will give us a CMSSW environment
source cmsenv

# Add python dependencies
python3 -m pip install -r requirements.txt -t .python_packages

cd extractor/

# Extract few DQM histograms. Using only one process because we are on SQLite
./hdqmextract.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 325117 325159 325168 325169 325170 325172 325175 325308 325309 325310 -j 1

# Calculate HDQM values from DQM histograms stored in the DB
./calculate.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 325117 325159 325168 325169 325170 325172 325175 325308 325309 325310 -j 1

# Get the OMS and RR data about the runs
./oms_extractor.py
./rr_extractor.py

cd ../api/
# Run the API
./run.sh &>/dev/null &

cd ../../frontend/
# Use local API instead of the production one
sed -i 's/\/api/http:\/\/localhost:8080\/api/g' js/config.js
# Run the static file server
python3 -m http.server 8000 &>/dev/null &

# Run this to find pids of running servers to kill them:
# ps awwx | grep python
```

That's it! Now visit http://localhost:8000/ on your browser.

## How to install locally

If nginx complains that it can't bind to port, make sure to request the ports to be opened in puppet:  
https://gitlab.cern.ch/ai/it-puppet-hostgroup-vocms/merge_requests/72  

And open them using SELinux: `sudo semanage port -m -t http_port_t -p tcp 8081`  
Also important:  
`sudo firewall-cmd --zone=public --add-port=81/tcp --permanent`  
`sudo firewall-cmd --reload`  
Make sure to make root directory accessible in SELinux:  
`chcon -Rt httpd_sys_content_t /data/hdqmTest/CentralHDQM/frontend/`  

## How to add new plots

In order to add new plots to HDQM, you have to provide two layers of configuration:  
1. backend configuration
2. frontend configuration

### Backend configuration

Backend is configured with `.cfg` files that describe what monitor elements should be taken from the DQM `.root` files and how the value from the should be extracted for plotting.  
These files are placed here, in a corresponding subsystem directory: `backend/extractor/cfg/<subsystem>`. This directory structure has to be preserved in order for the tool to work. 

Let's take a look at an example:

``` ini
1  [plot:Ntracks_Pixel]
2  metric = basic.BinCount(2)
3  relativePath = PixelPhase1/Tracks/ntracks
4  plotTitle = Pixel number of tracks
5  yTitle = Number of Tracks in Pixel
```

That's all it takes to tell HDQM how to plot a DQM quantity over time. Let's break this down line by line.

* The first line describes an ID of a plot that is unique per subsystem. This ID will be used to refer to this plot later on. *This field is required*.
* **metric** property tells the tool what function needs to be called to reduce a DQM histogram to a single value that will be plotted. Think of this as of a constructor call of a Python class. Classes that can be used are defined here: `backend/extractor/metrics/`. If necessary, new python classes could be added. new classes have to provide a constructor with as many arguments as it's required to be referred to from the configuration and a `calculate(self, histo)` method that will be called by the backend. This function has to return a tuple of two values `(value, error)`. *This field is required*.
* **relativePath** is a path of a monitor element in a legacy DQM root file that a metric should be applied to. In case a path of a monitor element changed, you can provide multiple, space separated paths here. ME that is found the first will be used. *This field is required*.
* **plotTitle** is a title of a plot that will be displayed in a web application. This value can contain spaces as it only has to be human readable. If this field is not provided, yTitle will be used instead. *This field is not required*.
* **yTitle** is a title of y axis. It is usually used to display the units used in a plot. *This field is required*.

Those were the main properties, however there are other less common ones:

``` ini
1  histo1Path = PixelPhase1/Phase1_MechanicalView/PXBarrel/num_clusters_PXLayer_2
2  histo2Path = PixelPhase1/Phase1_MechanicalView/PXBarrel/size_PXLayer_2
3  threshold = 50
```

* Sometimes, a value of a point in a trend depends on more than one DQM histogram. In such cases **histo1Path** and **histo2Path** could be used to define the paths of the other histograms. *These fields are not required*.
* **threshold** was used previously to define a minimum number of entries for a histogram to be taken into a trend. Now, this is no longer used, however this value can be wired in your custom Python extraction class. *This field is not required*.

### Frontend configuration

In a frontend configuration you can define what is called **display groups**. Display groups define a list of related plots that will be displayed together in a web application, as an overlay.  
The configuration is located here: `frontend/js/displayConfig.js`

Let's take a look at an example:

``` js
{
	name: "an_id_of_a_display_group",
	plot_title: "Nice title of a group",
	y_title: "Units of all plots in a group",
	subsystem: "<Subsystem>",
	correlation: false,
	series: ["plot1_ID", "plot2_ID"],
}
```

