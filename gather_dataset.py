## This file is used to gather the dataset
## It will contain many functions that are only meant to be executed once for the initial API pull.
## Due to the large size of the data, almost everything is written to file to avoid doing large data pulls every day.
import random
import time
from api_pull import getMatchListFromSummonerName, getMatchDataAndTimeline, get100MatchesOfPlayer, GetPlayerRankedInfo, writeToJSONFile
from parse_json import JoinMatchAndTimeline, Parse_match, Parse_Timeline
import dedupe
import json
import pandas as pd
import glob
import os
from dotenv import load_dotenv

load_dotenv()

## Simply writes to file
def writeToFile(listData, rank, mode, newline=True):
    textfile = open(f"ranks/{rank}.txt", mode)
    for item in listData:
        if newline:
            textfile.write(item + "\n")
        else: 
            textfile.write(item)
    textfile.close()

def writeCompleteRankList(listData):
    with open("ranks/CompleteList.txt", "w") as fp:
        for item in listData:
            fp.write(item + "\n")
    fp.close()

# LIMITS: 
# 20 requests every 1 seconds(s)
# 100 requests every 2 minutes(s)

## USERNAMES HAVE BEEN REDACTED FOR PRIVACY
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

## Call the API and get a list of each users matches
## Download the json timeline and match data
def getUsersListFromSeedNames(seed_users):
    completePuuidList = []
    
    for rank, summonerIdWithTag in seed_users.items(): ## For each rank in the dict
        summonerId, tagLine = summonerIdWithTag.split('#') # Using the hash character to split between summoner name and tagline
        matchIDs = getMatchListFromSummonerName(summonerId, tagLine) ##
        
        tierPuuidList = []
        counter = 0
        for matchId in matchIDs: ## Loop through match IDs for current user
            if counter == 50:
                print("Phew! That took a while. Let me rest for 10 seconds!")
                time.sleep(10) 
                counter = 0 # reset counter
            print(f'Doing match {matchId} for {summonerIdWithTag}')
            matchData, _ = getMatchDataAndTimeline(matchId) ## Get timeline and match data
            for i in range(len(matchData['metadata']['participants'])):
                curentParticipant = matchData['metadata']['participants'][i]
                tierPuuidList.append(str(curentParticipant))
                completePuuidList.append(str(curentParticipant))
            time.sleep(1)
            counter+=1

        tierPuuidList = list(set(tierPuuidList))
        writeToFile(tierPuuidList, rank, 'w')
        tierPuuidList.clear()
    
    completePuuidList = list(set(completePuuidList))
    writeCompleteRankList(completePuuidList)
    

## Takes in the path to the text file with the compiled list, returns list of puuids
## Simply reads from file
def readFromFile(pathToFile):
    userList = []
    with open(pathToFile, 'r') as f:
        lines = f.readlines()
        userList.extend(lines)

    return userList
        

def gatherAllMatchIdsFromPuuid(userList, start=0, end=-1):
    matchIDs = []
    counter = 0 #used for rate limiting
    limit = 40
    #loop through the list
    for user in userList[start:end]:
        if counter == limit:
            counter = 0 # reset counter
            writeToFile(matchIDs,"matchIDList", 'a') #write to file because its huge amounts of data
            matchIDs.clear() #clear the list
            time.sleep(20) #wait 2 mins (API limit)
        matchIDs.extend(get100MatchesOfPlayer(user.strip())) #pull as many match ids for the user (ranked)
        counter+=1
        time.sleep(10) #wait 1 second, rate limit
        print(f'completed: {user}')
    writeToFile(matchIDs,"matchIDList", 'a')
    return matchIDs
        
def gatherAllMatchDataFromFile(pathToFile,outputDir,start,end):

    ## FIX THIS WHOLE FUNCTION
    matchList = readFromFile(pathToFile)
    matchList.sort() #so its easy to establish where we left off
    counter = 0 #used for rate limiting
    limit = 20
    firstRecord = True
    for matchId in matchList[start:end]:
        matchId = matchId.strip()
        ## Get the data for each match ID
        if counter == limit:
            # time.sleep(120)
            counter = 0

        matchData, matchTimelineData = getMatchDataAndTimeline(matchId)
        
        try:
            ## Use this to determine if it failed, since the error wont have the 'info' key
            x=(len(matchData['info']))
            y=(len(matchTimelineData['info']))
        except Exception as e:
            print(f"Failed for: {matchId}")
            time.sleep(2)
            counter+=1
            continue
        #didnt fail, so write to file
        writeToJSONFile(f'{outputDir}{matchId}_match', matchData) ## write to file
        writeToJSONFile(f'{outputDir}{matchId}_timeline', matchTimelineData) ## write to file

        print(f'Successfully Processed Match: {matchId}')
        time.sleep(3)
        counter+=1

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


if __name__ == '__main__':

    #################################################################################
    ## THE METHODS ONLY NEEDED TO BE RUN ONCE FOR API CALLS!!!!                    ##
    #################################################################################

    ## Pull User List
    getUsersListFromSeedNames(seed_summonernames) #this is to gather a list of users
    userList = readFromFile("ranks/CompleteList.txt") #gathers user info

    ## shuffle the list to be able to reduce the size without cutting out any specific rank
    random.shuffle(userList)

    ## write to file because its huge amounts of data
    writeToFile(userList,"CompleteListShuffled.txt", 'a', newline=False) 
    
    userList = readFromFile("ranks/CompleteListShuffled.txt")
    

    ## The following 3 lines of code are repeated incrementally since API calls may 
    ## take a long time. I did them in increments of 100.
    ## The numerical values that remain (the final 2 in the parameters) are the positions it left off
    ## and the position to finish at. Eg. gatherAllMatchIdsFromPuuid() starts at 3000 and ends at 4000
    # pull match IDs
    matchIdList = gatherAllMatchIdsFromPuuid(userList) #needs a range START, END
    print("Total Match data fetched: ", len(matchIdList))
    # gatherAllMatchDataFromFile("matchList/matchListFinal.txt","match json files/",1400,2000) #DONE

    #path to match list ## officially 0,2000
    # ParseMatchDataIntoSpreadsheet("matchList/matchListFinal.txt","joined_TESTONLY.csv",0,2000) #DONE

    # API PULL:
    # params: path to csv match data, output path for each json (without .json ext)
    # writes rank jsons to file
    ## Get the summoner IDs of players from the csv file and call the api to get the json file downloaded
    # GetPlayerRanks("joined.csv","rank json files/") 