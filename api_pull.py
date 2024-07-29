## This file contains all the API calls needed for the project
import requests
import random
import time
import json
import os
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry

load_dotenv()

## Fetch environment variables
API_KEY = os.getenv('RIOT_API_KEY')
BASE_URL = os.getenv('EU_API_BASE_URL')

# Define the rate limit per second
CALLS = 100
PERIOD = 120

def exponential_backoff(attempt):
    return min(60, (2 ** attempt) + random.random())

## Get PUUID from Summoner Name
@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def getPlayerPUUID(summonerName, tagLine):
    query_params = { 'api_key': API_KEY }  
    puuid_endpoint = f'/riot/account/v1/accounts/by-riot-id/{summonerName}/{tagLine}'
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}{puuid_endpoint}', params=query_params)
            response.raise_for_status()
            summInfo = response.json()
            return summInfo['puuid']
        except requests.exceptions.RequestException as e:
            print(f'Requests exception encountered: {e}')
            wait_time = exponential_backoff(attempt)
            time.sleep(wait_time)

    

## Use PUUID to get last 100 games
@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def get100MatchesOfPlayer(puuid):
    query_params = {
        'start': '0', 
        'count': '5',
        'api_key': API_KEY
    }
    matchlist_endpoint = f'/lol/match/v5/matches/by-puuid/{puuid}/ids'

    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}{matchlist_endpoint}', params=query_params)
            response.raise_for_status()
            matchlist = response.json()
            return matchlist
        except requests.exceptions.RequestException as e:
            print(f'Exception encountered: {e}')
            wait_time = exponential_backoff(attempt)
            time.sleep(wait_time)
    

## Get the high level match data for a specific match ID
@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def getMatchDataByMatchId(match_id):
    query_params = { 'api_key': API_KEY }
    matchdata_endpoint = f'/lol/match/v5/matches/{match_id}'
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}{matchdata_endpoint}', params=query_params)
            response.raise_for_status()
            matchdata = response.json()
            return matchdata
        except requests.exceptions.RequestException as e:
            print(f'Exception encountered: {e}')
            wait_time = exponential_backoff(attempt)
            time.sleep(wait_time)

## Get the match timeline data for a specific match ID
@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def getMatchTimelineByMatchID(match_id):
    query_params = { 'api_key': API_KEY }
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}/lol/match/v5/matches/{match_id}/timeline', params=query_params)
            response.raise_for_status()
            matchTimelineData = response.json()
            return matchTimelineData
        except requests.exceptions.RequestException as e:
            print(f'Exception encountered: {e}')
            wait_time = exponential_backoff(attempt)
            time.sleep(wait_time)

def writeToJSONFile(type, gameData):
    with open(f'{type}.json', 'w') as outfile:
        json.dump(gameData, outfile)

def GetPlayerRankedInfo(summonerId):
    summInfox = requests.get(f'{BASE_URL}/lol/league/v4/entries/by-summoner/{summonerId}?api_key={API_KEY}')
    summInfo = json.loads(summInfox.text)
    return summInfo

## This is the function called by other files to start the pull by the players Summoner Name
def getMatchListFromSummonerName(summonerName, tagLine):
    summonerPuuid = getPlayerPUUID(summonerName, tagLine) ## Get PUUID from Summoner Name
    matchIDs = get100MatchesOfPlayer(summonerPuuid) ## Use PUUID to get last 100 games
    return matchIDs

def getMatchDataAndTimeline(matchID=0):
    matchGameInfo = getMatchDataByMatchId(matchID) ## Get the match data for a specific match ID
    matchTimelineInfo = getMatchTimelineByMatchID(matchID) ## Get the match timeline data for a specific match ID
    return matchGameInfo, matchTimelineInfo

