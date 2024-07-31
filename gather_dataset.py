## This file is used to gather the dataset
## It will contain many functions that are only meant to be executed once for the initial API pull.
## Due to the large size of the data, almost everything is written to file to avoid doing large data pulls every day.
import random
import time
from api_pull import getMatchListFromSummonerName, getMatchDataByMatchId, getMatchTimelineByMatchID, GetPlayerRankedInfo, getMatchesForASummonerPUUID, writeToJSONFile
from parse_json import JoinMatchAndTimeline, Parse_match, Parse_Timeline
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
    
## Helper functions to read from files
def readFromFile(pathToFile):
    userList = []
    with open(pathToFile, 'r') as f:
        lines = f.readlines()
        userList.extend(lines)

    return userList

def ReadJsonMatchAndTimelineData(pathToJson):
    f = open(f'{pathToJson}.json','r')
    data = json.load(f)
    return data

#Takes:
# path to text file containing match IDs, 
# output directory of the csv (without.csv ext), 
# start and end index of the list
def ParseMatchDataIntoSpreadsheet(pathToFile,outputDir,start,end):
    #Read the match ID list to use as an index
    matchList = readFromFile(pathToFile)        
    matchList.sort()
    firstRecord = False
    if start == 0:
        firstRecord = True
    for matchId in matchList[start:end]:
        matchId = matchId.strip()
        #does not need .json at the end, just the dir and filename
        matchData = ReadJsonMatchAndTimelineData(f"match json files/{matchId}_match")
        matchTimelineData = ReadJsonMatchAndTimelineData(f"match json files/{matchId}_timeline")
        # Parse data 
        joinedDF = JoinMatchAndTimeline(Parse_match(matchData),Parse_Timeline(matchTimelineData))
        if firstRecord:
            joinedDF.to_csv(f'{outputDir}',index=False, mode='a') ## Write to csv (append)
            firstRecord = False
        else:
            joinedDF.to_csv(f'{outputDir}',index=False, mode='a', header=False) ## Write to csv (append)

def GetPlayerRanks(dirToData,outputDir):

    ## Read the csv using pandas
    df = pd.read_csv(dirToData)
    ## Write the summID col into a list
    summIDs = df['summonerId'].values.tolist()
    gameIDs = df['gameId'].values.tolist()

    ## read from the list 
    counter = 0
    playerCounter = 1
    limit = 40
    for uid,gameId in zip(summIDs[12000:],gameIDs[12000:]): #MAX 15380
        if counter == limit: #api limits coming close
            # time.sleep(60) #wait 2 mins
            counter = 0
        if playerCounter == 11: #done all players for the previous game
            playerCounter = 1 #so reset the player counter for the new game
        region = gameId[0:4].lower()
        summInfo = GetPlayerRankedInfo(uid, region) ## Get the ranked info of the players account
        writeToJSONFile(f'{outputDir}{gameId}_{playerCounter}', summInfo) ## write to file
        counter+=1
        playerCounter+=1
        time.sleep(1.5)



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
    fetchInitialDataUsingSeednames(seed_summonernames, 100)

    ## fetch additional set of matches after randomly shuffling data in the set
    print('####################################')
    print('####################################')
    print("##### Fetching additional data #####")
    print('####################################')
    print('####################################')
    additionalFetchOfMatches()
    

    #path to match list ## officially 0,2000
    # ParseMatchDataIntoSpreadsheet("matchList/matchListFinal.txt","joined_TESTONLY.csv",0,2000) #DONE

    # API PULL:
    # params: path to csv match data, output path for each json (without .json ext)
    # writes rank jsons to file
    ## Get the summoner IDs of players from the csv file and call the api to get the json file downloaded
    # GetPlayerRanks("joined.csv","rank json files/") 

    endTime = time.time()
    elapsedTime = endTime - startTime
    print(f"Time taken: {elapsedTime} seconds")