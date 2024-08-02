## This file is used to gather the dataset
## It will contain many functions that are only meant to be executed once for the initial API pull.
## Due to the large size of the data, almost everything is written to file to avoid doing large data pulls every day.
import random
import time
from api_pull import getMatchListFromSummonerName, getMatchDataByMatchId, getMatchTimelineByMatchID, getSummonerRankInfo, getMatchesForASummonerPUUID, writeToJSONFile
from parse_json import joinMatchAndTimeline, parseMatch, parseTimeline
import dedupe
import json
import pandas as pd
import glob
import os
from dotenv import load_dotenv

load_dotenv()

## Dictionary used for seed users | key:value = rank:summoner name with tagline
seed_summonernames = {
    'Iron': os.getenv('SUMMONER_NAME_IRON'),
    'Bronze': os.getenv('SUMMONER_NAME_BRONZE'),
    'Silver': os.getenv('SUMMONER_NAME_SILVER'),
    'Gold': os.getenv('SUMMONER_NAME_GOLD'),
    'Plat': os.getenv('SUMMONER_NAME_PLATINUM'),
    'Emerald': os.getenv('SUMMONER_NAME_EMERALD'),
    'Diamond': os.getenv('SUMMONER_NAME_DIAMOND'),
    'Master': os.getenv('SUMMONER_NAME_MASTER'),
    'Grandmaster': os.getenv('SUMMONER_NAME_GM'),
    'Challenger': os.getenv('SUMMONER_NAME_CHALLENGER'),
}

MATCH_AND_TIMELINE_CSV_OUTPUT = 'aggregateMatchAndTimeline.csv'
SUMMONER_RANK_INFO_CSV_OUTPUT = 'summonerRankInfo.csv'

## Helper functions to write into files
def writeFileToRanksDir(listData, rank, mode):
    try:
        with open(f"ranks/{rank}.txt", mode) as fp:
            for item in listData:
                fp.write(str(item) + '\n')
        fp.close()
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")

def writeMatchList(matchList):
    try:
        with open(f"./matchList.txt", 'a') as fp:
            preExistingMatchIds = fp.readlines()
            for item in matchList:
                if item not in preExistingMatchIds:
                    fp.write(str(item) + '\n')
                else:
                    continue
        fp.close()
        return True
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")
        return False
    

def writeMatchDataToFile(matchId, matchData):
    try:
        with open(f"./matchData/{matchId}.json", "w") as fp:
            json.dump(matchData, fp, indent=4)
        fp.close()
        return True
    except IOError as e:
        print(f"Error {e} encountered while writing to the file")
        return False
    
def writeSummonerRanksToFile(gameServerPrefix, summonerId, response):
    try:
        with open(f'./summonerRanks/{gameServerPrefix}_{summonerId}.json', 'w') as fp:
            json.dump(response, fp, indent=4)
        fp.close()
        return True
    except IOError as e:
        print(f"Error {e} encountered while writing to file")

def writeMatchTimelineToFile(matchId, matchTimeline):
    try:
        with open(f"./matchTimeline/{matchId}.json", "w") as fp:
            json.dump(matchTimeline, fp, indent=4)
        fp.close()
        return True
    except IOError as e:
        print(f"Error {e} encountered while writing to file")
        return False

def writeCompletePUUIDListOfPlayers(listData):
    try:
        with open("ranks/CompletePUUIDList.txt", "w") as fp:
            for item in listData:
                fp.write(str(item) + '\n')
        fp.close()
        return True
    except IOError as e:
        print(f"Error {e} encountered while writing to file")
        return False


# Function that processes matchData and matchTimeline JSON files, joins thems and writes
# results to a single CSV file
def parseMatchDataIntoSpreadsheet():

    matchDataPath = './matchData/'
    matchTimelinePath = './matchTimeline/'
    fileNamesMatch = 0
    validFiles = 0
    individualDFs = []
    for matchDataFile, matchTimelineFile in zip(os.listdir(matchDataPath), os.listdir(matchTimelinePath)):

        print(f"Match file name: {matchDataFile}")
        print(f"Match timeline file name : {matchTimelineFile}")

        # need both the match data and timeline data for the corresponding matches
        if (str(matchTimelineFile) == str(matchDataFile)):
            print("Files match")
            fileNamesMatch += 1
            # processing for matchDataFile
            if matchDataFile.endswith('.json'):
                matchDataFileObj = os.path.join(matchDataPath, matchDataFile)

                with open(matchDataFileObj, 'r') as matchDataFP:
                    matchData = json.load(matchDataFP)
                matchDataFP.close()

                # filtering of games of CLASSIC 5 v 5 summoners rift, because the match API also returns other games!
                if (matchData['info']['gameMode'] != "CLASSIC") or (matchData['info']['gameType'] != "MATCHED_GAME"):
                    print("Not a classic 5v5 matched game")
                    continue
                else:
                    matchDF = parseMatch(matchData)

            if matchTimelineFile.endswith('.json'):
                matchTimelineFileObj = os.path.join(matchTimelinePath, matchTimelineFile)

                with open(matchTimelineFileObj, 'r') as matchTimelineFP:
                    matchTimeline = json.load(matchTimelineFP)
                matchTimelineFP.close()

                matchTimelineDF = parseTimeline(matchTimeline)

            joinedDF = joinMatchAndTimeline(matchDF=matchDF, timelineDF=matchTimelineDF)

            if(joinedDF.shape[0] == 10):
                individualDFs.append(joinedDF)
                validFiles += 1
            print(joinedDF.shape)
    print("Valid files count : ", validFiles)
    print("Total files match: ", fileNamesMatch)

    aggregateDF = pd.concat(individualDFs, ignore_index=True)
    aggregateDF.to_csv(f'./{MATCH_AND_TIMELINE_CSV_OUTPUT}', index=False)

def processSummonerRanks():
    # This function should only be processed once we have aggregated results of the matchData and matchTimeline
    # As such perform a check to show that the CSV files generated after parsing exists or not
    # try:
    #     if os.path.isfile(f'./{MATCH_AND_TIMELINE_CSV_OUTPUT}'):
    matchAndTimeLineDF = pd.read_csv(f'./{MATCH_AND_TIMELINE_CSV_OUTPUT}')

    gameIdAndSummonerId = matchAndTimeLineDF[['gameId', 'summonerId']]
    gameIdAndSummonerId['regionPrefix'] = gameIdAndSummonerId['gameId'].str.split('_', expand=True)[0].str.lower()

    regionAndSummonerId = gameIdAndSummonerId[['regionPrefix', 'summonerId']]
    regionAndSummonerId.drop_duplicates(inplace=True)

    regionAndSummonerId.to_csv('./regionAndSummonerId.csv', index=False)

    with open('./regionAndSummonerId.csv', 'r') as fp:
        regionAndSummonerIdData = fp.readlines()[1:]
    fp.close()


    '''
    for idx, row in concernedDF.iterrows():
        summonerRankInfo = getSummonerRankInfo(gameServerId=row['regionPrefix'], summonerId=row['summonerId'])
        if summonerRankInfo:
            concernedDF.at[idx, 'queueType'] = summonerRankInfo['queueType']
            concernedDF.at[idx, 'tier'] = summonerRankInfo['tier']
            concernedDF.at[idx, 'rank'] = summonerRankInfo['rank']
            concernedDF.at[idx, 'leaguePoints'] = summonerRankInfo['leaguePoints']
            concernedDF.at[idx, 'wins'] = summonerRankInfo['wins']
            concernedDF.at[idx, 'losses'] = summonerRankInfo['losses']
    '''
    
    # write concernedDF as csv
    # concernedDF.to_csv(f'./{SUMMONER_RANK_INFO_CSV_OUTPUT}', index=False)
    # print('Summoner Rank info written to file successfully')
    # except Exception as e:
    #     print(f'Exception {e} encountered while processing!')



## Description: ----- MAIN FUNCTION TO FETCHES MATCH IDs AND MATCH DETAILS -----
# 
#       This function will fetch `num_matches` for the set of `seed_users`` that contain a rank representative summoner
#       name along with tagline defined in the .env file. For each rank representative, it fetches matchIds for `num_matches` of the representative, 
#       Using these matchIds, it then proceeds to fetch match data and timeline, which are stored locally as files. 
# 
## Input:
#       seed_users: seed of summoner names with their summoner along and taglines
#       num_matches: number of matches to fetch for each summoner
## Output: 
#       1) Inside ranks/ folder, it creates txt file containing PUUID of the players who played in the matches for the rank representative
#       2) Inside matchData/ folder, writes mutiple JSON files for matchId containing match details
#       3) Inside matchTimeline/ folder, writes multiple JSON files for matchId containing match timeline details
#       4) Creates a matchList.txt file that contains matchIds of all matches from all tier of seed players

def fetchInitialDataUsingSeednames(seed_users, num_matches):
    completePuuidList = []
    listOfMatches = []
    
    for rank, summonerIdWithTag in seed_users.items(): ## For each rank in the dict
        summonerId, tagLine = summonerIdWithTag.split('#') ## Using the hash character to split between summoner name and tagline
        matchIds = getMatchListFromSummonerName(summonerId, tagLine, num_matches) ## fetches the recent match id for a given summoner
        
        tierPuuidList = []
        counter = 0
        
        for matchId in matchIds: ## Loop through match IDs for current user
            
            # append matchId to listOfMatches
            if matchId not in listOfMatches:
                listOfMatches.append(matchId)

            if counter == 50:
                print("Phew! That took a while. Let me rest for 10 seconds!")
                time.sleep(10) 
                counter = 0 # reset counter

            print(f'Fetching match {matchId} for {summonerIdWithTag}')

            # check if the match data has been fetched before; if not fetch and write to file
            if os.path.isfile(os.path.join(f"./matchData/{matchId}.json")):
                print(f"Match data file for match ID {matchId} already exists")
                continue
            else:
                matchData = getMatchDataByMatchId(matchId)
                counter += 1
                fileWrite = writeMatchDataToFile(matchId=matchId, matchData=matchData)
                if(fileWrite):
                    print(f"Match data for match id {matchId} written successfully")

                # uses matchData to fetch additional participants; append game participants into tierPuuidList and completePuuidList
                for i in range(len(matchData['metadata']['participants'])):
                    curentParticipant = matchData['metadata']['participants'][i]
                    tierPuuidList.append(str(curentParticipant))
                    completePuuidList.append(str(curentParticipant))

            # check if the match timeline data has been fetched before; if not fetch and write to file 
            if os.path.isfile(os.path.join(f"./matchTimeline/{matchId}.json")):
                print(f"Match timeline file for match ID {matchId} already exists")
                continue
            else:
                matchTimelineData = getMatchTimelineByMatchID(matchId)
                counter += 1
                fileWrite = writeMatchTimelineToFile(matchId=matchId, matchTimeline=matchTimelineData)
                if(fileWrite):
                    print(f"Match timeline for match id {matchId} written successfully")
                

        tierPuuidList = list(set(tierPuuidList))
        tierSummonerIds = writeFileToRanksDir(tierPuuidList, rank, 'a')
        if (tierSummonerIds):
            print(f"PUUID list file for {rank} tier created successfully")
        tierPuuidList.clear()
    
    completePuuidList = list(set(completePuuidList))
    fileWrite = writeCompletePUUIDListOfPlayers(completePuuidList)
    if(fileWrite):
        print("Complete summoners PUUID list file created successfully")

    # write match list to a file
    fileWriteML = writeMatchList(listOfMatches)
    if(fileWriteML):
        print("File for match list created successfully")
    

def additionalFetchOfMatches():
    extraPerPlayerMatchCount = 1
    with open("ranks/CompletePUUIDList.txt", 'r') as fp:
        puuidList = fp.readlines()
    fp.close()

    with open("./matchList.txt", 'r') as matchListReader:
        matchList = matchListReader.readlines()
    matchListReader.close()

    newMatchesCount = 0 # variable to keep track of count of new matches added to matchList.txt
    print(f"Currently matchList file contains a record of {len(matchList)} matches")

    random.shuffle(puuidList)
    print(puuidList[0:2])

    with open("./matchList.txt", 'a') as matchListWriter:
        for puuid in puuidList:
            puuid = puuid.strip()
            print(f"Current puuid is: {puuid}")
            # fetch the additional match id for a given summoner puuid
            tempMatchList = getMatchesForASummonerPUUID(puuid, extraPerPlayerMatchCount)

            if ((newMatchesCount % 51) == 0):
                time.sleep(2)
            
            for tempMatch in tempMatchList:
                # check if the match data has been fetched before; if not fetch and write to file
                if (os.path.isfile(os.path.join(f"./matchData/{tempMatch}.json")) and (tempMatch in matchList)):
                    print(f"Match data file for match ID {tempMatch} already exists")
                else:
                    matchData = getMatchDataByMatchId(tempMatch)
                    fileWrite = writeMatchDataToFile(matchId=tempMatch, matchData=matchData)
                    if(fileWrite):
                        print(f"Match data for match id {tempMatch} written successfully")

                # check if the match timeline data has been fetched before; if not fetch and write to file 
                if (os.path.isfile(os.path.join(f"./matchTimeline/{tempMatch}.json")) and (tempMatch in matchList)):
                    print(f"Match timeline file for match ID {tempMatch} already exists")
                else:
                    matchTimelineData = getMatchTimelineByMatchID(tempMatch)
                    fileWrite = writeMatchTimelineToFile(matchId=tempMatch, matchTimeline=matchTimelineData)
                    if(fileWrite):
                        print(f"Match timeline for match id {tempMatch} written successfully")

                # writing new matches to matchList.txt
                if tempMatch not in matchList:
                    newMatchesCount += 1
                    matchListWriter.write(str(tempMatch) + '\n') # the outer matchListWriter was opened for this purpose

    print(f'Previous length of matches in matchList.txt: {len(matchList)}')
    print(f'Additionally fetched match counts: {newMatchesCount}')
    matchListWriter.close()

    print('Verifying new length of match list file')

    with open("./matchList.txt", 'r') as matchListReader:
        updatedMatchList = matchListReader.readlines()

    print(f'New length of matchList.txt file {len(updatedMatchList)}')
    matchListReader.close()


# main boilerplate code
if __name__ == '__main__':

    startTime = time.time()

    ## fetch initial data -- params: seed users names and number of matches whose data are to be fetched
    print('############################################################')
    print('############################################################')
    print("##### Fetching initial data using seed summoner names! #####")
    print('############################################################')
    print('############################################################')
    # fetchInitialDataUsingSeednames(seed_summonernames, 100)

    ## fetch additional set of matches after randomly shuffling data in the set
    print('####################################')
    print('####################################')
    print("##### Fetching additional data #####")
    print('####################################')
    print('####################################')
    # additionalFetchOfMatches()
    

    # parse match and match timeline JSON files into CSV
    print('############################################################')
    print('############################################################')
    print("##### Parsing JSON Files and Writing MATCH data to CSV #####")
    print('############################################################')
    print('############################################################')
    # parseMatchDataIntoSpreadsheet()

    # API PULL:
    # params: path to csv match data, output path for each json (without .json ext)
    # writes rank jsons to file
    ## Get the summoner IDs of players from the csv file and call the api to get the json file downloaded
    # GetPlayerRanks("joined.csv","rank json files/")
    print('############################################################')
    print('############################################################')
    print("################ Process Summoner Rank Info ################")
    print('############################################################')
    print('############################################################')
    processSummonerRanks()

    endTime = time.time()
    elapsedTime = endTime - startTime
    print(f"Time taken: {elapsedTime} seconds")