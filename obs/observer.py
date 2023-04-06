import subprocess
import os
import pandas as pd
import numpy as np
import shlex
import obs.utils
import concurrent.futures


def GetPosition(matchIds = []):
    """
    Reads replay files and extracts position data for each player across a match using
    the clarity parser : https://github.com/skadistats/clarity

    :param matchIds : list of match ids to parse as integers
    :return: a double dictionary of match ids, player ids, and dataframes of position data
    """
    if not obs.utils.CheckInts(matchIds):
        return
    if not obs.utils.CheckJava():
        return
    obs.utils.CheckClarity()
    if len(matchIds) == 0:
        replayFiles = obs.utils.CheckDems()
        print("{} replays found.".format(len(replayFiles)))
    else:
        replayFiles = [str(match) +".dem" for match in matchIds]
        files_in_dir = os.listdir()
        if not all(elem in files_in_dir for elem in replayFiles):
            print("Specified replay files not found. Downloading replays.")
            print("WARNING : Files will download to current working directory.")
            answer = input("Continue? [y/n]")
            if answer == 'n':
                print("Exiting.")
                return
            obs.utils.DownloadReplays(matchIds)
    positionDict = ParseFiles(replayFiles)
    results = BuildDataFrames(positionDict)
    sampledResults = SampleFromMatches(results)
    return sampledResults

def ParseFile(file : str):
    """
    Parses one replay file using clarity
    :param  : file name of the form "<matchId>.dem"
    :return : tuple of the form (matchId, list of strings)
    """
    print(f"Parsing file {file}...")
    curDir = "{}/{}".format(subprocess.run("pwd", capture_output=True).stdout.decode("utf-8").replace(" ","\ ").strip(),file)
    p = subprocess.Popen("java -jar target/position.one-jar.jar '{}'".format(shlex.quote(curDir)), shell = True,cwd = './clarity-examples', stdout=subprocess.PIPE)
    output, err = p.communicate()
    if output.decode("utf-8") == "":
        print("Java Runtime Error. Please make sure a Java Runtime Environment is installed and can be found or the matchIDs are correct/exist")
        return f'Error {file}'
    p_status = p.wait()
    return (file.split('.')[0], output.decode('utf-8').split('\n'))
    
    
def ParseFiles(replayFiles : list):
    """
    Parses replay files and extracts position data for each player across a match using
    the clarity parser

    :param replayFiles : list of replay files to parse
    :return: a double dictionary of match ids, player ids, and dataframes of position data
    """
    positionDict = {}
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(ParseFile,replayFiles)
    print("Done")
    for result in results:
        positionDict[result[0]] = result[1]
    return positionDict

def BuildDataFrame(parsedOutput : list, matchId : str):
    """
    Gets a list of strings which is the parsed output for one replay and builds a dataframe for one match
    each row is one position reading for one player plus other metrics.

    :param parsedOutput : List of strings
    :return             : a dataframe object for one match
    """
    try:
        # skip the first 10 rows which gives player assignments, not location
        # TODO : Implement change so that dynamically determines last position entry
        print(f"Building dataframes {matchId}..")
        series = pd.Series(parsedOutput)
        firstPos = series.str.contains('_').idxmax()
        series = series[firstPos:].reset_index(drop=True)
        df = series.str.split(',', expand=True)
        df = df.rename(columns={0: "player", 1: "x", 2: "y", 3: "z", 4: "time", 5: "mana", 6: "mana_regen",
                                7: "max_mana", 8: "hp", 9: "hp_regen", 10: "max_hp", 11: "xp", 12: "level",
                                13: "str", 14: "int", 15: "agi"})
        # skip the last row which gives info about how long the parsing took
        return (matchId, df.iloc[0:-2])
    except:
        print(f"Error parsing match {matchId}")

def BuildDataFrames(positionDict : dict):
    """
    builds dataframes from the position data extracted from the replay files
    :param positionDict:
    :return: a double dictionary of match ids, player ids, and dataframes of position data
    """
    dataFrameDict = {}
    matchIds = list(positionDict.keys())
    parsedOutput = list(positionDict.values())

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(BuildDataFrame,parsedOutput,matchIds)

    for result in results:
        dataFrameDict[result[0]] = result[1]
    print("Done")
    return dataFrameDict

def SampleFromMatch(dataFrame : pd.DataFrame, matchId : str):
    """
    Takes a dataframe consisting of the position data for all 10 players in a match and samples each player's
    position every 200 ms. 

    :param dataFrame : a dataframe of position data for all 10 players in a match
    :return          : a double dictionary of match ids, player ids, and dataframes of position data
    """
    pass

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
