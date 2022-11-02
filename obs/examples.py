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


def GetPosition(matches = []):
    """
    Reads replay files and extracts position data for each player across a match using
    the clarity parser : https://github.com/skadistats/clarity

    :param matches:
    :return:
    """

    # TODO : implement ability to parse selected files.
    if not obs.utils.CheckJava():
        return
    obs.utils.CheckClarity()
    replayFiles = obs.utils.CheckDems()
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
    ## TODO : Parallelize this
    for file in replayFiles[1:]:
      # if ctr > 5:
        #     break
        print("Parsing file {}/{}..".format(ctr,len(replayFiles[1:])))
        # if os.path.getsize(file) == 0:
        #     print('File {} is empty'.format(file))
        #     continue
        curDir = "{}/{}".format(subprocess.run("pwd", capture_output=True).stdout.decode("utf-8").replace(" ","\ ").strip(),file)
        #print(curDir)
        p = subprocess.Popen("java -jar target/position.one-jar.jar '{}'".format(shlex.quote(curDir)), shell = True,cwd = './clarity-examples', stdout=subprocess.PIPE)
        #p = subprocess.check_output(["java", "-jar", "target/position.one-jar.jar", curDir], cwd='./clarity-examples')
        output, err = p.communicate()
        positionDict[file.split('.')[0]] = output.decode('utf-8').split('\n')
        #print(type(output))
        p_status = p.wait()
        ctr+=1
    results = {}
    print()
    print("Done")
    ctr = 1
    # TODO : Parallelize this
    for matchId in positionDict.keys():
        try:
            # skip the first 10 rows which gives player assignments, not location
            # TODO : Implement change so that dynamically determines last position entry
            print("Building dataframes {}/{}..".format(ctr, len(positionDict.keys())))
            series = pd.Series(positionDict[matchId])
            firstPos = series.str.contains('_').idxmax()
            series = series[firstPos:].reset_index(drop = True)
            df = series.str.split(',', expand=True)
            df = df.rename(columns={0: "Player", 1: "X", 2: "Y", 3: "Z", 4: "Time"})
            # skip the last row which gives info about how long the parsing took
            results[matchId] = df.iloc[0:-2]
            ctr += 1
        except:
            print(matchId, series)
            ctr += 1
            continue
    print()
    print("Done")
    matchDict = {}
    matchCtr = 1
    for match in results:
        print("Sampling match {}/{}".format(matchCtr, len(results)))
        results[match]['Time'] = pd.to_numeric(results[match]['Time'])
        firstTs = abs(results[match].iloc[0]['Time'])
        # convert each recording to milliseconds
        results[match]['Time'] = (results[match]['Time'] + firstTs) * 1000
        tEnd = results[match].iloc[-1]['Time']
        # number of 200 ms invervals
        ints = int(np.ceil(tEnd / 200))
        # equally spaced (200 ms intervals) values from 0 to tEnd
        timeArray = [i * 200 for i in range(1, ints + 1)]
        timeIndex = np.zeros(ints)
        playerDict = {}
        for i in range(10):
            player = 'Player_0{}'.format(i)
            playerDf = results[match][results[match]['Player'] == player].reset_index()
            arrayCtr = 0;
            startTime = 0;
            for i in range(1, len(playerDf)):
                if (round(playerDf['Time'].iloc[i], 3) >= startTime):
                    timeIndex[arrayCtr] = playerDf['index'][i - 1]
                    startTime += 200
                    arrayCtr += 1
            df = playerDf[playerDf['index'].isin(timeIndex[:arrayCtr + 1])].drop(columns="index").reset_index(drop=True)
            df = pd.concat([df, df.iloc[[-1] * (len(timeArray) - len(df))]])
            df['Time'] = timeArray
            playerDict[player] = df
        matchCtr += 1
        matchDict[match] = playerDict
    print()
    return matchDict
    # This makes the wait possible
    # p_status = p.wait()
    # print(type(output))

#matchData = GetODotaMatchData([6212505052,6522221361])
#DownloadReplays(matchData)
#print(GetPosition([6212505052, 6522221361]).keys())
