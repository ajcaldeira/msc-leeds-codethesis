## This file is used to gather the dataset
## It will contain many functions that are only meant to be executed once for the initial API pull.
## Due to the large size of the data, almost everything is written to file to avoid doing large data pulls every day.
import random
import time
from api_pull import GetStartingData, Get_match_data, Pull_100_match_id,GetSummIdFromPuuid,GetPlayerRankedInfo, writeToFile
from parse_json import JoinMatchAndTimeline, Parse_match, Parse_Timeline
import dedupe
import json
import pandas as pd
import glob

## Simply writes to file
def WriteToFile(puuidList,rank, mode, newline=True):
    textfile = open(f"ranks/{rank}.txt", mode)
    for item in puuidList:
        if newline:
            textfile.write(item + "\n")
        else: 
            textfile.write(item)
    textfile.close()

# LIMITS: 
# 20 requests every 1 seconds(s)
# 100 requests every 2 minutes(s)

## USERNAMES HAVE BEEN REDACTED FOR PRIVACY
## Dictionary used for seed users | key:value = rank:username
seed_users1 = {'Iron':'REDACTED USERNAME',
              'Bronze':'REDACTED USERNAME',
              'Silver':'REDACTED USERNAME',
              'Gold':'REDACTED USERNAME',
              'Plat':'REDACTED USERNAME',
              'Diamond':'REDACTED USERNAME',
              'Master':'REDACTED USERNAME',
              'GM & Challenger':'REDACTED USERNAME'}
seed_users2 = {'Iron':'REDACTED USERNAME',
              'Bronze':'REDACTED USERNAME',
              'Silver':'REDACTED USERNAME',
              'Gold':'REDACTED USERNAME',
              'Plat':'REDACTED USERNAME',
              'Diamond':'REDACTED USERNAME',
              'Master':'REDACTED USERNAME',
              'GM & Challenger':'REDACTED USERNAME'}

## Call the API and get a list of each users matches
## Download the json timeline and match data
def GetUserListFromDict(seed_users):

    for rank in seed_users: ## Feor each rank in the dict
        matchIDs = GetStartingData(seed_users[rank]) ##
        puuidList = []

        counter = 0
        for matchId in matchIDs: ## Loop through match IDs for current user
            if counter == 50:
                time.sleep(120)
                counter = 0
            print(f'Doing match {matchId} for {seed_users[rank]}')
            matchData, matchTimelineData = Get_match_data(matchId) ## Get timeline and match data
            for i in range(10):
                curentParticipant = matchData['metadata']['participants'][i]
                puuidList.append(curentParticipant)
            time.sleep(1)
            counter+=1

        WriteToFile(puuidList, rank, 'a')
        puuidList.clear()

## Takes in the path to the text file with the compiled list, returns list of puuids
## Simply reads from file
def ReadFromFile(pathToFile):
    userList = []
    with open(pathToFile, 'r') as f:
        lines = f.readlines()
        userList.extend(lines)

    ## Debugging purposes to ensure the right data is being read
    # for puuid in userList:
    #     summID = GetSummIdFromPuuid(puuid.strip()) # returns the summID
    #     playerRankedInfo = GetPlayerRankedInfo(summID) # returns an array of json responses

    return userList
        

def GatherAllMatchIdsFromPuuid(userList,start,end):
    matchIDs = []
    counter = 0 #used for rate limiting
    limit = 40
    #loop through the list
    for user in userList[start:end]:
        if counter == limit:
            counter = 0 #reset counter
            WriteToFile(matchIDs,"matchIDList", 'a') #write to file because its huge amounts of data
            matchIDs.clear() #clear the list
            time.sleep(140) #wait 2 mins (API limit)
        matchIDs.extend(Pull_100_match_id(user.strip())) #pull as many match ids for the user (ranked)
        counter+=1
        time.sleep(1.5) #wait 1 second, rate limit
        print(f'completed: {user}')
    WriteToFile(matchIDs,"matchIDList", 'a')
    return matchIDs
        
def GatherAllMatchDataFromFile(pathToFile,outputDir,start,end):

    ## FIX THIS WHOLE FUNCTION
    matchList = ReadFromFile(pathToFile)
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

        matchData, matchTimelineData = Get_match_data(matchId)
        
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
        writeToFile(f'{outputDir}{matchId}_match', matchData) ## write to file
        writeToFile(f'{outputDir}{matchId}_timeline', matchTimelineData) ## write to file

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
    matchList = ReadFromFile(pathToFile)        
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
        writeToFile(f'{outputDir}{gameId}_{playerCounter}', summInfo) ## write to file
        counter+=1
        playerCounter+=1
        time.sleep(1.5)


if __name__ == '__main__':

    #################################################################################
    ## THE METHODS ONLY NEEDED TO BE RUN ONCE FOR API CALLS!!!!                    ##
    #################################################################################

    ## Pull User List
    GetUserListFromDict(seed_users1) #this is to gather a list of users
    userList = ReadFromFile("ranks/CompleteList.txt") #gathers user info

    ## shuffle the list to be able to reduce the size without cutting out any specific rank
    random.shuffle(userList)

    ## write to file because its huge amounts of data
    WriteToFile(userList,"CompleteListShuffled", 'a', newline=False) 
    
    userList = ReadFromFile("ranks/CompleteListShuffled.txt")
    

    ## The following 3 lines of code are repeated incrementally since API calls may 
    ## take a long time. I did them in increments of 100.
    ## The numerical values that remain (the final 2 in the parameters) are the positions it left off
    ## and the position to finish at. Eg. GatherAllMatchIdsFromPuuid() starts at 3000 and ends at 4000
    # pull match IDs
    matchIdList = GatherAllMatchIdsFromPuuid(userList,3000,4000) #needs a range START, END
    GatherAllMatchDataFromFile("matchList/matchListFinal.txt","match json files/",1400,2000) #DONE

    #path to match list ## officially 0,2000
    ParseMatchDataIntoSpreadsheet("matchList/matchListFinal.txt","joined_TESTONLY.csv",0,2000) #DONE

    # API PULL:
    # params: path to csv match data, output path for each json (without .json ext)
    # writes rank jsons to file
    ## Get the summoner IDs of players from the csv file and call the api to get the json file downloaded
    GetPlayerRanks("joined.csv","rank json files/") 

