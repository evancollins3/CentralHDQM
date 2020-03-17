# HDQM tutorial for PPD workshop

During this tutorial we will cover the following topics:

1. Setting up a local deployment of the full HDQM stack on lxplus
2. Adding adding new plot configurations
3. Writing our own custom metrics for the new plots
4. Configuring display groups to show multiple trends in one plot

## Deploying HDQM locally

First, please follow local setup instructions that are available here: https://github.com/cms-DQM/CentralHDQM#how-to-run-locally

This will deploy a full stack of HDQM locally, in lxplus.

### If OMS and/or RR doesn't work

Consult this section in case either OMS or RR APIs are not functioning at this moment.

``` bash
cd backend/
sqlite3 hdqm.db
```

``` sql
-- If RR is down, set all to true:
UPDATE oms_data_cache SET significant = 1, is_dcs = 1;

-- If OMS is down, create all rows
INSERT INTO "oms_data_cache" VALUES(1,325098,0,'2018-10-22 21:45:12.000000','2018-10-22 21:48:47.000000',3.8,6499.0,4.880754,1.819496,1.959637,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',51852.51,1805.181,215,7333,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(2,325097,0,'2018-10-22 21:03:27.000000','2018-10-22 21:41:46.000000',3.8,6499.0,27.650654,1.753344,18.793686,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',44400.125,1470.831,2299,7333,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(3,324999,0,'2018-10-21 07:46:04.000000','2018-10-21 08:01:42.000000',3.8,6499.0,12.823047,1.263898,3.850594,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',80672.055,1125.588,938,7324,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(4,324998,0,'2018-10-21 05:22:15.000000','2018-10-21 07:43:31.000000',3.8,6499.0,124.040188,1.294307,114.588043,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',85375.43,1293.284,8476,7324,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(5,325000,0,'2018-10-21 08:03:09.000000','2018-10-21 10:27:58.000000',3.8,6499.0,99.478719,1.026495,95.161531,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',79609.52,1047.821,8689,7324,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(6,325057,0,'2018-10-22 13:50:57.000000','2018-10-22 16:24:00.000000',3.8,6499.0,128.329852,1.481395,121.566727,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',74043.78,1711.889,9183,7331,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(7,325001,0,'2018-10-21 10:28:55.000000','2018-10-21 14:23:33.000000',3.8,6499.0,125.970563,0.786782,121.399453,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',77849.375,843.698,14078,7324,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(8,324997,0,'2018-10-21 04:23:27.000000','2018-10-21 05:19:41.000000',3.8,6499.0,49.37966,1.577752,42.214555,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',59324.92,1787.391,3374,7324,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(9,325099,0,'2018-10-22 21:49:49.000000','2018-10-23 00:21:28.000000',3.8,6499.0,148.647938,1.443952,139.547121,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',87238.12,1782.806,9099,7333,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
INSERT INTO "oms_data_cache" VALUES(10,325022,0,'2018-10-21 20:52:50.000000','2018-10-22 07:16:34.000000',3.8,6499.0,452.509125,0.834237,437.270188,'l1_trg_collisions2018/v70','/cdaq/physics/Run2018/2e34/v3.6.1/HLT/V2',62756.434,1358.919,37424,7328,'25ns_2556b_2544_2215_2332_144bpi_20injV3','2018D','Collisions18',1,1);
```

## Add new plots

Now go to the root directory of the project: `cd /tmp/$USER/hdqm/CentralHDQM/`

### Add configuration files

``` bash
vim backend/extractor/cfg/Muons/workshopTrends.ini
```

``` ini
[plot:Mean_GlbGlbMuon_HM]
metric = workshop.Mean()
relativePath = Muons/diMuonHistograms/GlbGlbMuon_HM
yTitle = GeV/c<sup>2</sup>
plotTitle = Invariant mass of the 2 muons in the event (&sum; 3<sup>2</sup> 5<sub>-1</sub>)

[plot:Mean_MeanDistr_Phi]
metric = workshop.Mean()
relativePath = DT/02-Segments/00-MeanRes/MeanDistr_Phi
yTitle = CM
plotTitle = Mean value of the residuals phi LS
```

``` bash
vim backend/extractor/cfg/RPC/workshopTrends.ini
```

``` ini
[plot:Mean_ClusterSize_Barrel]
metric = workshop.Mean()
relativePath = RPC/Muon/SummaryHistograms/ClusterSize_Barrel
yTitle = Number of Barrel strips
plotTitle = Number of contiguous Barrel strips associated with the hit
```

``` bash
mkdir backend/extractor/cfg/Ecal/
vim backend/extractor/cfg/Ecal/workshopTrends.ini
```

``` ini
[plot:Mean_TrigPrimClient_EB_number_of_TTs_with_TTF4_set]
metric = workshop.Mean()
relativePath = Ecal/Trends/TrigPrimClient EB number of TTs with TTF4 set
yTitle = Number of TTs with TTF4 set
plotTitle = TrigPrimClient Number of TTs with TTF4 set
```

`plotTitle` and `yTitle` support HTML code! List of math symbols, if necessary, can be found here: https://www.w3schools.com/charsets/ref_utf_math.asp

`plotTitle` is a new parameter! A lot of current configs are not using it, therefore I invite everyone to take advantage of it and make your plots more beautiful.

`metric` value is essentially a constructor call to a metric python class. Next we will look at how to add new, custom metric.

### Add new metric

``` bash
vim backend/extractor/metrics/workshop.py
```

``` py
from basic import BaseMetric

class Mean(BaseMetric):
    def calculate(self, histo):
        return (histo.GetMean(), histo.GetMeanError())
```

More info about adding new metrics: https://github.com/cms-DQM/CentralHDQM#adding-new-metrics

### Add new metric to calculation script:

``` bash
vim backend/extractor/calculate.py
```

Import it:

``` python
from metrics import workshop
```

And add the new metric to the METRICS_MAP:

``` python
METRICS_MAP = {'fits': fits, 'basic': basic, 'L1T_metrics': L1T_metrics, 'muon_metrics': muon_metrics, 'workshop': workshop}
```

### Run the extraction and calculation again

``` bash
cd backend/extractor/

./hdqmextract.py -c cfg/Muons/workshopTrends.ini cfg/Ecal/workshopTrends.ini cfg/RPC/workshopTrends.ini cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 324997 324998 324999 325000 325001 325022 325057 325097 325098 325099 -j 1

./calculate.py -c cfg/Muons/workshopTrends.ini cfg/Ecal/workshopTrends.ini cfg/RPC/workshopTrends.ini cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 324997 324998 324999 325000 325001 325022 325057 325097 325098 325099 -j 1
```

If runs are the same as before, you no longer need to run OMS and RR extraction. Otherwise:

``` bash
./oms_extractor.py
./rr_extractor.py
```

## Add superimposed plots

Let's configure the frontend to show two, otherwise separate, trends in one plot.

``` bash
vim ../../frontend/js/displayConfig.js
```

``` js
// Workshop configuration
{
    name: "BPix_FPix_number_of_tracks",
    plot_title: "BPix and FPix number of tracks",
    y_title: "Number of tracks",
    subsystem: "PixelPhase1",
    correlation: false,
    series: ["Ntracks_BPix", "Ntracks_FPix"],
},
```

## Final remarks

* Whenever new DQM monitor elements are added to backend configuration (`.ini` files), both `hdqmextract.py` and `calculate.py` has to be executed.

* Whenever backend configuration (`.ini` files) is changed but no new DQM monitor elements are added, only `calculate.py` has to be executed.

* Whenever new runs get extracted, `oms_extractor.py` and `rr_extractor.py` has to be executed.
  * Keep in mind that cookies for OMS and RR extraction are valid only for only ~10h.
  * Once they expire and you want to extract new runs, you have to rerun the `cern-get-sso-cookie` commands
  * **Run this command before running `cmsenv`!!!**

* If you want to keep working on the same deployment of the full HDQM stack after disconnecting, please follow these (shortened) instructions: https://github.com/cms-DQM/CentralHDQM#new-ssh-connection

* In case the local database gets contaminated in any way (you extracted too many things for a small test, for example), the easies way to start from scratch is by deleting the db file. Continue using the tool normally, the database will be recreated automatically.
  * `rm backend/hdqm.db`
