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

def GetODotaMatchData(MatchIds: list):
    """
    :param MatchIds:
    :return: A dictionary containing match details retrieved from opendota.com
    """
    matchUrlDataDict = dict()
    completeMatchMetails = dict()
    ctr = 1
    for match in MatchIds:
        r = requests.get("https://api.opendota.com/api/matches/{}".format(match)).json()
        # print(r.keys())
        print('Fetching match {}/{}'.format(ctr, len(MatchIds)), end="\r", flush=True)
        completeMatchMetails[match] = r
        # OpenAPI has a max number of calls per minute
        if len(MatchIds) > 60:
            time.sleep(11)
        ctr += 1
    return (completeMatchMetails)

def DownloadReplays(matches: list):
    """
    Downloads match files in .bz2 format and extracts the files on to disk in the current working director

    :param matches: List of matchIds to download replays of
    :return: none
    """
    ctr = 1
    fileNames = [];
    print("WARNING : Files will download to current working directory.")
    answer = input("Continue? [y/n]")
    if answer == 'n':
        print("Exiting.")
        return
    for match in matches:
        extType = str(match) + ".dem.bz2"
        fileNames.append(extType)
        print("downloading replay {}/{} ...".format(ctr, len(matches)))
        urllib.request.urlretrieve(matches[match]["replay_url"], extType)
        ctr += 1
    print("Done.")
    fileCount = 1
    for file in fileNames:
        print("Decompressing file {}/{}".format(fileCount, len(fileNames)))
        if os.path.getsize(file) == 0:
            print('File {} is empty'.format(file))
        os.system("bzip2 -d {}".format(file))
        fileCount += 1

def CheckJava():
    p1 = subprocess.run('java --version', shell=True, capture_output=True)
    print("Checking if Java is installed - required for the Clarity parser..")
    if p1.returncode != 0:
        print("Java installation not found.")
        print("Please visit https://www.java.com/en/download/help/download_options.html")
        return False
    print("Java check passed.")
    return True

def CheckClarity():
    print("Checking for Clarity...")
    p1 = subprocess.run('ls', shell=True, capture_output=True)
    # print(str(p1.stdout))
    if 'clarity' not in p1.stdout.decode("utf-8"):
        print('Clarity not found.')
        toContinue = input(
            "WARNING : Clarity parser will be downloaded from Github to current directory.\nContinue? [y/n]")
        if toContinue == 'n':
            return
        print("Cloning...")
        p1 = subprocess.run('git clone https://github.com/onedeeper/clarity-examples.git', shell=True)
    print("Clarity found.")
    return True

def CheckDems():
    print("Checking for replays in current directory..")
    p1 = subprocess.run('ls', shell=True, capture_output=True)
    if '.dem' not in p1.stdout.decode("utf-8"):
        print("No .dem files found in current directory")
        print("Try using the DownloadReplays function to get some replays or place replays (.dem files) in the current directory.")
        return [False]
    files = p1.stdout.decode("utf-8").split()
    replayFiles = [True]
    for file in files:
        if '.dem' in file:
            replayFiles.append(file)
    return replayFiles