## This file contains all the API calls needed for the project
import requests
import json
import os
import env
## BASE INFO
API_KEY = os.getenv('RIOT_API_KEY')
PREFIX_1 = os.getenv('RIOT_API_SERVER_ALIAS1')
PREFIX_2 = os.getenv('RIOT_API_SERVER_ALIAS2')
PREFIX_3 = os.getenv('RIOT_API_SERVER_ALIAS3') ## Has a placeholder in the value


## Get PUUID from Summoner Name
def Pull_username(summonerName):   
    
    summInfox = requests.get(f'{PREFIX_1}/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={API_KEY}')
    summInfo = json.loads(summInfox.text)
    return summInfo['accountId']

## Use PUUID to get last 100 games 
def Pull_100_match_id(puuid):

    payload = {'start': '0', 'totalGames': '100','api_key': API_KEY} #CAN PULL MAX 100 FOR A SINGLE PARTICIPANT
    matchIdInfox = requests.get(f'{PREFIX_2}/lol/match/v4/matchlists/by-account/{puuid}', params=payload)
    matchIdInfo = json.loads(matchIdInfox.text)

    return matchIdInfo

## Get the high level match data for a specific match ID
def GetMatchDataByID(match_id):
    payload = {'api_key': API_KEY}
    matchGameInfox = requests.get(f'{PREFIX_2}/lol/match/v4/matches/{match_id}', params=payload)
    matchGameInfo = json.loads(matchGameInfox.text)
    return matchGameInfo

## Get the match timeline data for a specific match ID
def GetMatchTimelineByID(match_id):
    payload = {'api_key': API_KEY}
    matchGameInfox = requests.get(f'{PREFIX_2}/lol/match/v4/timelines/by-match/{match_id}', params=payload)
    matchTimelineInfo = json.loads(matchGameInfox.text)
    return matchTimelineInfo

def writeToFile(type, gameData):
    with open(f'{type}.json', 'w') as outfile:
        json.dump(gameData, outfile)

def GetPlayerRankedInfo(summonerId,region):
    summInfox = requests.get(f'{PREFIX_3.replace("REPLACE",region)}/lol/league/v4/entries/by-summoner/{summonerId}?api_key={API_KEY}')
    summInfo = json.loads(summInfox.text)
    return summInfo

def writeToFile(type, gameData):
    with open(f'{type}.json', 'w') as outfile:
        json.dump(gameData, outfile)

## This is the function called by other files to start the pull by the players Summoner Name
def GetStartingData(summName):
    summonerPuuid = Pull_username(summName) ## Get PUUID from Summoner Name
    matchIDs = Pull_100_match_id(summonerPuuid) ## Use PUUID to get last 100 games
    return matchIDs

def Get_match_data(matchID=0):
   
    matchGameInfo = GetMatchDataByID(matchID) ## Get the match data for a specific match ID
    matchTimelineInfo = GetMatchTimelineByID(matchID) ## Get the match timeline data for a specific match ID
    
    ## Used for debugging
    # writeToFile('match', matchGameInfo) ## write to file
    # writeToFile('timeline', matchTimelineInfo) ## write to file
    # exit()

    return matchGameInfo, matchTimelineInfo

    
