import subprocess

import requests
import json
import os
import pandas as pd
import time
import urllib.request
import numpy as np
import csv
import glob
from io import StringIO
from datetime import datetime
from collections import defaultdict
import shlex
import obs.utils


def GetPosition(matches: list):
    """
    Reads replay files and extracts position data for each player across a match using
    the clarity parser : https://github.com/skadistats/clarity

    :param matches:
    :return:
    """
    if not obs.utils.CheckJava():
        return
    obs.utils.CheckClarity()
    replayFiles = obs.utils.CheckDems()
    print("Checking for replays in current directory..")
    if not replayFiles[0]:
        return
    print("{} replays found.".format(len(replayFiles[1:])))
    print("Building package...")
    #subprocess.Popen(, shell=True, cwd='./clarity-examples')
    p = subprocess.Popen('mvn -P position package', stdout=subprocess.PIPE, shell=True, cwd='./clarity-examples')
    (output, err) = p.communicate()
    # This makes the wait possible
    p_status = p.wait()
    ctr = 1;
    positionDict = {}
    #print("test")
    for file in replayFiles[1:]:
        print("Parsing file {}/{}..".format(ctr,len(replayFiles[1:])))
        curDir = "{}/{}".format(subprocess.run("pwd", capture_output=True).stdout.decode("utf-8").replace(" ","\ ").strip(),file)
        #print(curDir)
        p = subprocess.Popen("java -jar target/position.one-jar.jar '{}'".format(shlex.quote(curDir)), shell = True,cwd = './clarity-examples', stdout=subprocess.PIPE)
        #p = subprocess.check_output(["java", "-jar", "target/position.one-jar.jar", curDir], cwd='./clarity-examples')
        output, err = p.communicate()
        positionDict[file.split('.')[0]] = output.decode('utf-8').split('\n')
        #print(type(output))
        p_status = p.wait()
        ctr+=1
    matchCoordsDict = {}
    for matchId in positionDict.keys():
        # skip the first 10 rows which gives player assignments, not location
        series = pd.Series(positionDict[matchId][10:])
        df = series.str.split(',', expand=True)
        df = df.rename(columns={0: "Player", 1: "X", 2: "Y", 3: "Z", 4: "Time"})
        # skip the last 2 rows which gives info about how long the parsing took
        matchCoordsDict[matchId] = df.iloc[0:-2]
    return matchCoordsDict

    # This makes the wait possible
    # p_status = p.wait()
    # print(type(output))

#matchData = GetODotaMatchData([6212505052,6522221361])
#DownloadReplays(matchData)
#print(GetPosition([6212505052, 6522221361]).keys())
