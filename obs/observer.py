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

    :param matches : list of match ids to parse as integers
    :return: a double dictionary of match ids, player ids, and dataframes of position data
    """
    isint = lambda x: all(isinstance(item, int) for item in x)
    if not isint(matches):
        print("Error : Matches must be a list of integers")
        return
    if not obs.utils.CheckJava():
        return
    obs.utils.CheckClarity()
    if len(matches) == 0:
        replayFiles = obs.utils.CheckDems()
        print("{} replays found.".format(len(replayFiles)))
    else:
        replayFiles = [ str(match)+".dem"for match in matches]
        files_in_dir = os.listdir()
        if not all(elem in files_in_dir for elem in replayFiles):
            print("Specified replay files not found. Downloading replays.")
            obs.utils.DownloadReplays(matches)
    positionDict = ParseFiles(replayFiles)
    results = BuildDataFrames(positionDict)
    sampledResults = SampleFromMatches(results)
    return sampledResults
def ParseFiles(replayFiles : list):

    """
    Parses replay files and extracts position data for each player across a match using
    the clarity parser

    :param replayFiles : list of replay files to parse
    :return: a double dictionary of match ids, player ids, and dataframes of position data
    """
    positionDict = {}
    ctr = 1
    for file in replayFiles:
        print("Parsing file {}/{}..".format(ctr,len(replayFiles)))
        curDir = "{}/{}".format(subprocess.run("pwd", capture_output=True).stdout.decode("utf-8").replace(" ","\ ").strip(),file)
        p = subprocess.Popen("java -jar target/position.one-jar.jar '{}'".format(shlex.quote(curDir)), shell = True,cwd = './clarity-examples', stdout=subprocess.PIPE)
        output, err = p.communicate()
        #print("Output : {}".format(output.decode("utf-8")))
        if output.decode("utf-8") == "":
            print("Java Runtime Error. Please make sure a Java Runtime Environment is installed, path is defined, etc.")
            return
        positionDict[file.split('.')[0]] = output.decode('utf-8').split('\n')
        p_status = p.wait()
        ctr+=1
    print()
    print("Done")
    return positionDict

def BuildDataFrames(positionDict : dict):
    """
    builds dataframes from the position data extracted from the replay files
    :param positionDict:
    :return: a double dictionary of match ids, player ids, and dataframes of position data
    """
    results = {}
    ctr = 1
    # TODO : Parallelize this
    for matchId in positionDict.keys():
        try:
            # skip the first 10 rows which gives player assignments, not location
            # TODO : Implement change so that dynamically determines last position entry
            print("Building dataframes {}/{}..".format(ctr, len(positionDict.keys())))
            series = pd.Series(positionDict[matchId])
            firstPos = series.str.contains('_').idxmax()
            series = series[firstPos:].reset_index(drop=True)
            df = series.str.split(',', expand=True)
            df = df.rename(columns={0: "player", 1: "x", 2: "y", 3: "z", 4: "time", 5: "mana", 6: "mana_regen",
                                    7: "max_mana", 8: "hp", 9: "hp_regen", 10: "max_hp", 11: "xp", 12: "level",
                                    13: "str", 14: "int", 15: "agi"})
            # skip the last row which gives info about how long the parsing took
            results[matchId] = df.iloc[0:-2]
            ctr += 1
        except:
            print("Error parsing match {}".format(matchId))
            ctr += 1
            continue
    print()
    print("Done")
    return results

def SampleFromMatches(results : dict):
    """
    Samples at 200ms for each player in each match
    :param
    :param results:
    :return:  a double dictionary of match ids, player ids, and dataframes of position data
    """
    matchDict = {}
    matchCtr = 1
    for match in results:
        print("Sampling match {}/{}".format(matchCtr, len(results)))
        try:
            results[match]['time'] = pd.to_numeric(results[match]['time'])
            firstTs = abs(results[match].iloc[0]['time'])
            # convert each recording to milliseconds
            results[match]['time'] = (results[match]['time'] + firstTs) * 1000
            tEnd = results[match].iloc[-1]['time']
            # number of 200 ms invervals
            ints = int(np.ceil(tEnd / 200))
            # equally spaced (200 ms intervals) values from 0 to tEnd
            timeArray = [i * 200 for i in range(1, ints + 1)]
            timeIndex = np.zeros(ints)
            playerDict = {}
            for i in range(10):
                player = 'Player_0{}'.format(i)
                playerDf = results[match][results[match]['player'] == player].reset_index()
                arrayCtr = 0;
                startTime = 0;
                for i in range(1, len(playerDf)):
                    if (round(playerDf['time'].iloc[i], 3) >= startTime):
                        timeIndex[arrayCtr] = playerDf['index'][i - 1]
                        startTime += 200
                        arrayCtr += 1
                df = playerDf[playerDf['index'].isin(timeIndex[:arrayCtr + 1])].drop(columns="index").reset_index(drop=True)
                df = pd.concat([df, df.iloc[[-1] * (len(timeArray) - len(df))]])
                df['time'] = timeArray
                playerDict[player] = df
            matchCtr += 1
            matchDict[match] = playerDict
        except:
            print("Error sampling match {}. Dataframe of length {}".format(match, len(results[match])))
            matchCtr += 1
            continue
    print("Done.")
    return matchDict
