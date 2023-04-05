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
import concurrent.futures

def GetODotaMatchData(matchIds: list):
    """
    :param matchIds: List of matchIds to get data for
    :return: A dictionary containing match details retrieved from opendota.com
    """
    if not CheckInts(matchIds):
        return
    matchUrlDataDict = dict()
    completeMatchMetails = dict()
    ctr = 1
    print("Getting match details from opendota.com...")
    for match in matchIds:
        try:
            r = requests.get("https://api.opendota.com/api/matches/{}".format(match))
            if r.status_code == 404:
                #print('test')
                raise RuntimeError('Error : {} cannot be retrieved or does not exist '.format(match))
            print('Fetching match {}/{}'.format(ctr, len(matchIds)))
            completeMatchMetails[match] = r.json()
            # OpenAPI has a max number of calls per minute
            if len(matchIds) > 60:
                time.sleep(11)
            ctr += 1
        except Exception as e:
            print(e)
            continue
    return (completeMatchMetails)

def getReplay(url,matchId):
    extType = str(matchId) + ".dem.bz2"
    #fileNames.append(extType)
    print("downloading replay {}...".format(matchId))
    urllib.request.urlretrieve(url,extType)
    return extType

def DownloadReplays(matchIds: list):
    """
    Downloads match files in .bz2 format and extracts the files on to disk in the current working director

    :param matchIds: List of matchIds to download replays of
    :return: none
    """
    if not CheckInts(matchIds):
        return
    matchIds = GetODotaMatchData(matchIds)
    ctr = 1
    fileNames = [];
    print ("Downloading replays to current working directory..")
    urls = [matchIds[match]["replay_url"] for match in matchIds]
    matchIds = list(matchIds.keys())

    with concurrent.futures.ThreadPoolExecutor() as executor:
        fileNames = executor.map(getReplay, urls, matchIds)

    print("Done.")
    fileCount = 1
    fileNames = list(fileNames)
    for file in fileNames:
        print("Decompressing file {}/{}".format(fileCount, len(fileNames)))
        if os.path.getsize(file) == 0:
            print('File {} is empty'.format(file))
        os.system("bzip2 -d {}".format(file))
        fileCount += 1

def CheckJava():
    """
    Checks if java is installed on the system
    :return: True if java is installed, False otherwise
    """
    p1 = subprocess.run('java -version', shell=True, capture_output=True)
    print("Checking if Java is installed - required for the Clarity parser..")
    if p1.returncode != 0:
        print("Java installation not found.")
        print("Please visit https://www.java.com/en/download/help/download_options.html")
        return False
    print("Java check passed.")
    return True

def CheckClarity():
    """
    Checks if clarity exists in the current working directory
    :return: True if clarity exists, False otherwise
    """
    print("Checking for Clarity...")
    p1 = subprocess.run('ls', shell=True, capture_output=True)
    # print(str(p1.stdout))
    if 'clarity' not in p1.stdout.decode("utf-8"):
        print('Clarity not found.')
        toContinue = input(
            "WARNING : Clarity parser will be downloaded from Github to current directory.\nContinue? [y/n]")
        if toContinue == 'n':
            return False
        print("Cloning...")
        p1 = subprocess.run('git clone https://github.com/onedeeper/clarity-examples.git', shell=True)
    print("Clarity found.")
    return True

def CheckDems():
    """
    Checks if there are any .dem files in the current working directory
    :return:  Returns a list of .dem files in the current working directory
    """
    print("Checking for replays in current directory..")
    p1 = subprocess.run('ls', shell=True, capture_output=True)
    if '.dem' not in p1.stdout.decode("utf-8"):
        print("No .dem files found in current directory")
        print("Try using the DownloadReplays function to get some replays or place replays (.dem files) in the current directory.")
        return
    files = p1.stdout.decode("utf-8").split()
    replayFiles = []
    for file in files:
        if '.dem' in file:
            replayFiles.append(file)
    return replayFiles

def CheckInts(matchIds : list):
    """
    Checks if a list of integers
    :param matchIds: List of matchIds to check
    :return: True if all elements are integers, False otherwise
    """
    isint = lambda x: all(isinstance(item, int) for item in x)
    if not isint(matchIds):
        print("Error : Matches must be a list of integers")
        return False
    return True
