## Generates the data for individuals
import pandas as pd
import pandasql
import ast
import csv

def JoinAssistLists(assistedKillIds,assistedTowerIds,assistedMonsterIds,assistedPressureIds):
    weightList = []
    for index,item in enumerate(assistedKillIds):
        killSub = ast.literal_eval(assistedKillIds[index]) #read the string as a literal list
        towerSub = ast.literal_eval(assistedTowerIds[index]) #read the string as a literal list
        monsterSub = ast.literal_eval(assistedMonsterIds[index]) #read the string as a literal list
        pressureSub = ast.literal_eval(assistedPressureIds[index]) #read the string as a literal list
        weightList.append(str(killSub + towerSub + monsterSub + pressureSub))
    return weightList

def GenerateAssistsCsv(df,limit):
    gameIds = df['gameId'].tolist()
    participantIds = df['participantId'].tolist()
    assistedKillIds = df['participantsAssisted'].tolist()
    assistedTowerIds = df['towerKillsAssisted'].tolist()
    assistedMonsterIds = df['monsterKillsAssisted'].tolist()
    assistedPressureIds = df['participantsAssistedWithPressure'].tolist()
    assistedIds = JoinAssistLists(assistedKillIds,assistedTowerIds,assistedMonsterIds,assistedPressureIds)
    teamIds = df['teamId'].tolist()
    kills = df['kills'].tolist()
    teamIdList = [] ## used for team+player id ## not changing name cuz it will mess things up!
    tidList = [] ## Used for team id
    gameIdList = []
    fromList = []
    toList = []
    currentToList = [] ## a list that is emptied every iteration to make sure data is consistant
    weightList = []
    current_game = ""
    prev_game = ""
    firstloop = True
    for index,assist in enumerate(assistedIds[0:limit]):      

        current_game = gameIds[index]
        assist = ast.literal_eval(assist) #read the string as a literal list
        if len(assist) < 1: ##Player has assisted 0 people
            assist.append(participantIds[index])
            my_dict = {j:0 for j in assist}
        else:
            my_dict = {j:assist.count(j) for j in assist} ## count the number of times the assister is repeated

        ## if the player has no kills that game, then mark it as 0
        if kills[index] == 0: ## player got no kills
            my_dict[participantIds[index]] = 0
        
        ## if there is someone the participant hasnt assistsed, add them to the list and mark it as 0
        if participantIds[index] < 6: ## is team 1
            for i in range(1,6):
                if i not in my_dict:
                    my_dict[i] = 0
        else: ## is team 2
            for i in range(6,11):
                if i not in my_dict:
                    my_dict[i] = 0
    

        ## Add all the people participantIds[index] assisted to the lists
        for key, value in my_dict.items():
            ## Make sure the participant hasnt assisted someone on the opposite team
            if (participantIds[index] < 6 and key > 5) or (participantIds[index] > 5 and key < 6):
                continue
            teamIdList.append(f'{gameIds[index]}_{teamIds[index]}_{participantIds[index]}')
            tidList.append(f'{gameIds[index]}_{teamIds[index]}')
            gameIdList.append(gameIds[index])
            weightList.append(value)
            toList.append(key)
            fromList.append(participantIds[index])

    with open('individualCSVs/assists.csv', 'w') as f:
        f.write(f"gid,tid,team,frm,to_player,weight\n")
        for gid,tid,team,frm,to,weight in zip(gameIdList,tidList,teamIdList,fromList,toList,weightList):
            f.write(f"{gid},{tid},{team},{frm},{to},{weight}\n")

## TEST
def StandardiseAssistsCSV(dfComplete,dfAssists):
    sql = '''
    SELECT gameId, teamId, sum(kills) as kills
    FROM dfComplete
    GROUP BY gameId,teamId
    '''
    dfKillByTeam = pandasql.sqldf(sql, locals()) ## all kill for each team
    dfKillByTeam['team'] = dfKillByTeam['gameId'].astype(str) + "_" + dfKillByTeam['teamId'].astype(str)
    dfKillByTeam.drop(['gameId','teamId'],axis=1,inplace=True)
    # print(dfKillByTeam.head(5))

    sql = '''
    SELECT gid,tid,dfAssists.team,frm,to_player,weight,kills
    FROM dfAssists
    INNER JOIN dfKillByTeam
        ON dfAssists.tid = dfKillByTeam.team
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all kill for each team

    dfFinal['StdWeight'] = dfFinal.apply(lambda row: row.weight / row.kills, axis = 1)
    dfFinal.drop(['kills'],axis=1,inplace=True)
    dfFinal.rename(columns={'weight': 'unstdWeight'},inplace=True)
    dfFinal.rename(columns={'StdWeight': 'weight'},inplace=True)
    return dfFinal
   
def CalculateIndegree(df):
    # Number of assists the player has received
    # for each player, count the number of times the current player has been assisted
    df['receivedTid'] = df["tid"].astype(str) + "_" + df["to_player"].astype(str)
    df.drop(['team'], axis=1, inplace=True)

    sql = '''
    SELECT gid, receivedTid as team, to_player as player, sum(unstdWeight) as unstdWeight, sum(weight) as assistedIndegree
    FROM df
    GROUP BY gid, receivedTid, to_player
    '''
    dfNew = pandasql.sqldf(sql, locals()) ## this has outdegree for every player now
    print(f"Shape of dfNew ind: {dfNew.shape}")
    dfNew.to_csv("individualCSVs/indivAssistedIndegree.csv",index=False)

## reads in assists.csv
def CalculateOutdegree(df):
    sql = '''
    SELECT gid, team, frm as player, sum(unstdWeight) as unstdWeight, sum(weight) as assistedOutdegree
    FROM df
    GROUP BY gid, frm
    '''
    dfNew = pandasql.sqldf(sql, locals()) ## this has outdegree for every player now
    print(f"Shape of dfNew: {dfNew.shape}")
    dfNew.to_csv("individualCSVs/indivAssistedOutdegree.csv",index=False)

def CalculatePerMinMetrics():
    df = pd.read_csv("../complete.csv")
    
    sql = '''
    SELECT 
    gameId, 
    teamId,
    participantId,
    kills, 
    assists, 
    goldEarned AS gold, 
    visionScore, 
    champExperience, 
    totalMinionsKilled, 
    gameDuration
    FROM df
    GROUP BY gameId, teamId, participantId
    '''
    dfGrp = pandasql.sqldf(sql, locals()) ## all unique game ids here

    sql = '''
    SELECT 
    gameId, teamId, participantId,
    ROUND((kills/gameDuration),4) as KPM, 
    ROUND((assists/gameDuration),4) as AsPM, 
    ROUND((gold/gameDuration),4) as GPM,
    ROUND((visionScore/gameDuration),4) as visionScorePM,
    ROUND((champExperience/gameDuration),4) as champExperiencePM,
    ROUND((totalMinionsKilled/gameDuration),4) as minionsKilledPM
    FROM dfGrp
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    dfFinal["uid"] = dfFinal["gameId"].astype(str) + "_" + dfFinal["teamId"].astype(str) + "_" + dfFinal["participantId"].astype(str) 
    dfFinal.drop(['gameId','teamId','participantId'], axis=1,inplace=True)
    # print(dfFinal)
    dfFinal.to_csv("individualCSVs/indivPerMinMetrics.csv",index=False)

def CalculateAssistRatio():
    df = pd.read_csv("../complete.csv")

    sql = '''
    SELECT gameId, teamId, sum(assists) assists, sum(kills) as kills
    FROM df
    GROUP BY gameId, teamId
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    
    dfFinal["AsRatio"] = dfFinal["assists"] / dfFinal["kills"]
    dfFinal["uid"] = dfFinal["gameId"].astype(str) + "_" + dfFinal["teamId"].astype(str)
    dfFinal.drop(['assists','kills','gameId','teamId'], axis=1,inplace=True)

    dfFinal.to_csv("assistRatio.csv",index=False)

## Similar to assist ratio but taking all assists (found in outdegreecentrality csv) by all kills 
def CalculateIntensity():

    dfComplete = pd.read_csv("../complete.csv")
    dfOutdeg = pd.read_csv("individualCSVs/indivAssistedOutdegree.csv")

    ## Add unique id for each individual to dfComplete
    dfComplete["uid"] = dfComplete["gameId"].astype(str) + "_" + dfComplete["teamId"].astype(str) + "_" + dfComplete["participantId"].astype(str)

    ## Reduce the assistedOutdegree for individual metrics
    sql = '''
    SELECT team, sum(unstdWeight) as assists
    FROM dfOutdeg
    GROUP BY team
    '''
    dfAssists = pandasql.sqldf(sql, locals()) ## all unique game ids here

    sql = '''
    SELECT gameId, teamId, uid,
    kills, 
    turretKills,
    epicMonsterKills,
    dfAssists.assists as assists
    FROM dfComplete
    INNER JOIN dfAssists
        ON dfComplete.uid = dfAssists.team
    GROUP BY gameId, uid, teamId, dfAssists.assists
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    
    ## Sum the total kills
    dfFinal["totalKills"] = dfFinal[['kills','turretKills','epicMonsterKills']].sum(axis=1)
    
    ## Assists / Kills
    dfFinal["insensity"] = dfFinal["assists"] / dfFinal["totalKills"]
    dfFinal.drop(['assists','totalKills','gameId','teamId','epicMonsterKills','turretKills','kills'], axis=1,inplace=True)
    dfFinal.to_csv("individualCSVs/intensity.csv",index=False)
  
def CalculateTotalWins():

    df = pd.read_csv("../complete.csv")

    sql = '''
    SELECT gameId, teamId, participantId, win, avgrank
    FROM df
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    dfFinal["uid"] = dfFinal["gameId"].astype(str) + "_" + dfFinal["teamId"].astype(str) + "_" + dfFinal["participantId"].astype(str)
    dfFinal.drop(columns=['gameId','teamId','participantId'],inplace=True)
    dfFinal.to_csv("individualCSVs/gameWins.csv",index=False)

def JoinMetricsTogether():
    dfPerMin = pd.read_csv("individualCSVs/indivPerMinMetrics.csv")
    dfOutdeg = pd.read_csv("individualCSVs/indivAssistedOutdegree.csv")
    dfIndeg = pd.read_csv("individualCSVs/indivAssistedIndegree.csv")
    dfAsRatio = pd.read_csv("individualCSVs/intensity.csv")
    dfWins = pd.read_csv("individualCSVs/gameWins.csv")

    sql = '''
    SELECT 
    dfPerMin.uid, dfPerMin.KPM, dfPerMin.AsPM, dfPerMin.GPM,
    dfPerMin.visionScorePM, dfPerMin.champExperiencePM, dfPerMin.minionsKilledPM,
    dfOutdeg.assistedOutdegree, dfIndeg.assistedIndegree, dfWins.win, dfWins.avgrank ,dfAsRatio.insensity
    FROM dfPerMin
    INNER JOIN dfOutdeg
        ON dfPerMin.uid = dfOutdeg.team
    INNER JOIN dfIndeg
        ON dfPerMin.uid = dfIndeg.team
    INNER JOIN dfAsRatio
        ON dfPerMin.uid = dfAsRatio.uid
    INNER JOIN dfWins
        ON dfPerMin.uid = dfWins.uid
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    dfFinal.to_csv("individualCSVs/CombinedMeasurements.csv",index=False)
    

## Generate the assists csv
df = pd.read_csv("../complete.csv")
GenerateAssistsCsv(df,10760) ## limit officially 10760 ## COmmented out since the csv already exists
df2 = pd.read_csv("individualCSVs/assists.csv")
df3 = StandardiseAssistsCSV(df,df2)
## function names self explanatory
CalculateOutdegree(df3) 
CalculateIndegree(df3)
CalculatePerMinMetrics()
CalculateIntensity()
CalculateTotalWins()
JoinMetricsTogether() ## joins all needed variables from all csvs generatud until this point
