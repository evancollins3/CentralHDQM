#!/usr/bin/env python
from __future__ import print_function

from os import remove
from sys import argv
from glob import glob
from tempfile import NamedTemporaryFile
from collections import defaultdict
from configparser import ConfigParser
from multiprocessing import Pool

import re
import json
import ROOT
import uproot

import metrics
from metrics import fits
from metrics import basic

CFGFILES = "cfg/trendPlotsTrackingCosmics.ini"
# CFGFILES = "cfg/trendPlotsRECOErrorsCosmics.ini"
# CFGFILES = 'cfg/trendPlotsStrip_aleTestCharge.ini'
# ROOTFILES = "/eos/cms/store/group/comm_dqm/DQMGUI_data/*/*/*/DQM*.root"
ROOTFILES = '/afs/cern.ch/work/a/akirilov/HDQM/CentralHDQM/CentralHDQM/backend/extractor/testData/DQM*.root'
RUNFOLDER = re.compile("Run (\d+)(;\d*)?") # pattern of the Run folder inside the TDirectory file
PDPATTERN = re.compile("DQM_V\d+_R\d+__(.+__.+__.+)[.]root") # PD inside the file name
VERSIONPATTERN = re.compile("(DQM_V)(\d+)(.+[.]root)")
DQMGUI = "https://cmsweb.cern.ch/dqm/offline/"
DQMGUI_SAMPLES = DQMGUI + "data/json/samples"
DQMGUI_JSROOT = lambda run, dataset, me: DQMGUI + "jsonfairy/archive/%d%s/%s" % (run, dataset, me)

N_JOBS = 10

def get_full_path(relativePath, run):
  parts = relativePath.split('/')
  return str('DQMData/Run %s/%s/Run summary/%s' % (run, parts[0], '/'.join(parts[1:])))

def extract_metric(tdirectory, section, run):
  metric = eval(section['metric'], {'fits': fits, 'basic': basic})

  if 'threshold' in section:
    metric.setThreshold(section['threshold'])

  if 'histo1Path' in section:
    obj = tdirectory.Get(get_full_path(section['histo1Path'], run))
    if not obj:
      raise Exception("Unable to get histo1Path '%s' from file %s'" % (section['histo1Path'], tdirectory.GetName()))
    metric.setOptionalHisto1(obj)
  if 'histo2Path' in section:
    obj = tdirectory.Get(get_full_path(section['histo2Path'], run))
    if not obj:
      raise Exception("Unable to get histo2Path '%s' from file %s'" % (section['histo2Path'], tdirectory.GetName()))
    metric.setOptionalHisto2(obj)

  fullPath = get_full_path(section['relativePath'], run)
  obj = tdirectory.Get(fullPath)
  if not obj:
    raise Exception("Unable to get relativePath '%s' from file %s'" % (section['relativePath'], tdirectory.GetName()))
  value = metric.calculate(obj)
  return value

def remove_old_versions(allFiles):
  # groups is a map: filename with version part removed -> list of all files 
  # with the same name but different version.
  groups = {}
  for fullpath in allFiles:
    filename = fullpath.split('/')[-1]
    version = 1
    mapKey = filename
    versionMatch = VERSIONPATTERN.findall(filename)
    # We should get 3 parts: DQM_V, version and the rest of the file name
    if len(versionMatch) == 1 and len(versionMatch[0]) == 3:
      version = int(versionMatch[0][1])
      # Key is everything appart from version
      mapKey = versionMatch[0][0] + versionMatch[0][2]
  
    obj = {}
    obj['fullpath'] = fullpath
    obj['filename'] = filename
    obj['version'] = version

    if mapKey not in groups.keys():
      groups[mapKey] = []
    
    groups[mapKey].append(obj)

  # Sort every group by version and select the latest one
  files = map(lambda x: sorted(groups[x], key=lambda elem: elem['version'], reverse=True)[0]['fullpath'], groups)
  
  return files

def run(runs):
  cfgFiles = glob(CFGFILES)
  plotDesc = ConfigParser()

  goodFiles = 0
  for cfgFile in cfgFiles:
    try:
      plotDesc.read(unicode(cfgFile))
      goodFiles += 1
    except:
      print("Could not read %s, skipping..." % cfgFile)
  print("Read %d configuration files." % goodFiles)

  print("Listing files on EOS, this can take a while...")
  eosFiles = glob(ROOTFILES)
  print("Done.")

  allFiles = []
  for run in runs:
    rungroup = "_R%09d_" % int(run)
    files = [file for file in eosFiles if rungroup in file]
    allFiles += files

  # Keep only the newest version of each file
  allFiles = remove_old_versions(allFiles)

  result = []
  # for filename in list(allFiles)[:1]: # TODO: don't convert to list
  for filename in allFiles:
    pdMatch = PDPATTERN.findall(filename)
    if len(pdMatch) == 0:
      dataset = ''
      pd = ''
    else:
      dataset = '/' + pdMatch[0].replace('__', '/')
      pd = pdMatch[0].split('__')[0]
    
    tdirectory = ROOT.TFile.Open(filename)

    for folder in tdirectory.Get('DQMData').GetListOfKeys():
      if not folder.GetTitle().startswith('Run '):
        continue
      run = int(folder.GetTitle().split(' ')[1])

      for section in plotDesc:
        if not section.startswith("plot:"):
          continue

        plotPath = plotDesc[section]['relativePath']
        plotFolder = '/'.join(plotDesc[section]['relativePath'].split('/')[:-1])
        guiUrl = 'https://cmsweb.cern.ch/dqm/offline/start?runnr=%s;dataset=%s;workspace=Everything;root=%s;focus=%s;zoom=yes;' % (run, dataset, plotFolder, plotPath)
        imageUrl = 'https://cmsweb.cern.ch/dqm/offline/plotfairy/archive/%s%s/%s?v=1510330581101995531;w=1906;h=933' % (run, dataset, plotPath)
        
        try:
          value = extract_metric(tdirectory, plotDesc[section], run)
          obj = {}
          obj['run'] = run
          obj['lumi'] = 0
          obj['name'] = section.split(':')[1]
          obj['pd'] = pd
          obj['dataset'] = dataset
          obj['value'] = value[0]
          obj['error'] = value[1]
          obj['file'] = filename

          obj['guiUrl'] = guiUrl
          obj['imageUrl'] = imageUrl
          result.append(obj)
        except:
          # raise
          pass
  
  with open("output.json", "w") as out:
    jsonStr = json.dumps(result, indent=2)
    out.write(jsonStr)
    print(jsonStr)

if __name__ == '__main__':
  # Select only by run number. We might update a bit too often (all PDs for each PD) but that is fine.
  runs = argv[1:]
  run(runs)
