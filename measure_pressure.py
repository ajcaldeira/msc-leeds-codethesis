## This file calculates the pressure metric
import pandas as pd
import json
import csv
## Check radius
from math import sqrt
import numpy as np

## Checks if a player is in the specified radius of the kill site
def CheckRadius(killX,killY,playerX,playerY):

    a = killX - playerX
    b = killY - playerY
    radius = 2000 ## constant
    c = sqrt(a * a  +  b * b)
    if (c < radius):
        ## Inside
        return True
    else:
        ## Outside
        return False


## Takes in: RAW Json Formatted file for the high level match data
## This is a very complex function:
## 1. It loops through every event that occured during the game, looking for kills
## 2. Once a kill is found, it notes the position of each player NOT involved in the kill
## 3. and uses CheckRadius() to see if they are within the specified radius
## 4. It notes those that were in the radius and creates a record in a new dataframe for them
def ParseTimelinePressure(match_timeline):
    
    ## Get the participant ID by puuid
    matchFrames = match_timeline['info']['frames']

    ## Init 2 dictionaries to store the killer and who assisted the killer
    killPressureDict = {} # killer (key) and assisting participants (value)
    finalPressureDict = {} # participants (key) and who they assisted (value)

    for i in range(1,11):
        killPressureDict[str(i)] = []
        finalPressureDict[str(i)] = []

    t1 = [1,2,3,4,5]
    t2 = [6,7,8,9,10]
    playersTakenPartInKill = []
    ## Loop through each frame of the game (1 minute intervals)
    for frame in matchFrames:
        currentEventList = frame['events']
        ## Loop through each event in the time frame
        for event in currentEventList:
            ## Looking for the type of event
            playersTakenPartInKill = []
            if event['type'] == 'CHAMPION_KILL':
                try: #trying incase there was no assisting participant
                    # add killer to list of participants int he kill
                    playersTakenPartInKill.append(event['killerId'])
                    killX = event['position']['x']
                    killY = event['position']['y']
                    try:
                        for assistingParticipant in event['assistingParticipantIds']:
                            playersTakenPartInKill.append(assistingParticipant)
                    except:

                        pass ## was a solo kill or execute so all 4 players will be added to the list
                    notInKill = [] ## define the list first incase there are no pressure assists in the game
                    # get players that were not part of the kill
                    if event['killerId'] < 6 and event['killerId'] > 0:
                        notInKill = list(np.setdiff1d(t1,playersTakenPartInKill)) # Team 1
                    elif event['killerId'] > 5 and event['killerId'] > 0:
                        notInKill = list(np.setdiff1d(t2,playersTakenPartInKill)) # Team 2

                    pressureList = []
                    for pid in notInKill:# here are the players that were not part of the kill
                        ## get their positions in that interval of time
                        playerX = frame['participantFrames'][str(pid)]['position']['x']
                        playerY = frame['participantFrames'][str(pid)]['position']['y']
                        ## Check if they were within the kill radius
                        if CheckRadius(killX,killY,playerX,playerY):
                            killPressureDict[str(event['killerId'])].append(pid)


                except Exception as e:
                    print('broken', e)
                    print(event['timestamp'])
                    print(match_timeline['metadata']['matchId'])
 
    for i in range(1,11):
        for pid in killPressureDict[str(i)]:
            if pid > 0:
                finalPressureDict[str(pid)].append(i)

    for i in range(1,11):
        finalPressureDict[str(i)] = str(finalPressureDict[str(i)])

    dfPressure = pd.DataFrame.from_dict(finalPressureDict, orient='index', columns=['participantsAssistedWithPressure'])
    dfPressure.index.name = 'participant'

    return dfPressure


## This file should only be called directly for development, testing or debuging purposes
if __name__ == '__main__':
    ## Load test data 
    f = open('EUW1_5417501902_match.json',)
    g = open('EUW1_5417501902_timeline.json',)
    
    # returns JSON object as a dictionary
    matchData = json.load(f)
    timelineData = json.load(g)

    ParseTimelinePressure(timelineData)