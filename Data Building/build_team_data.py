## Generates the aggregated data for teams
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
    teamIdList = []
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
            teamIdList.append(f'{gameIds[index]}_{teamIds[index]}')
            gameIdList.append(gameIds[index])
            weightList.append(value)
            toList.append(key)
            fromList.append(participantIds[index])

    with open('teamCSVs/assists.csv', 'w') as f:
        f.write(f"gid,team,frm,to_player,weight\n")
        for gid,team,frm,to,weight in zip(gameIdList,teamIdList,fromList,toList,weightList):
            f.write(f"{gid},{team},{frm},{to},{weight}\n")

def CalculateIndegree(df):
    # Number of assists the player has received
    # for each player, count the number of times the current player has been assisted

    sql = '''
    SELECT gid, team, to_player as player, sum(weight) as assistedIndegree
    FROM df
    GROUP BY gid, to_player
    '''
    dfNew = pandasql.sqldf(sql, locals()) ## this has outdegree for every player now
    print(f"Shape of dfNew ind: {dfNew.shape}")
    dfNew.to_csv("teamCSVs/assistedIndegree.csv",index=False)

## reads in assists.csv
def CalculateOutdegree(df):
    sql = '''
    SELECT gid, team, frm as player, sum(weight) as assistedOutdegree
    FROM df
    GROUP BY gid, frm
    '''
    dfNew = pandasql.sqldf(sql, locals()) ## this has outdegree for every player now
    print(f"Shape of dfNew: {dfNew.shape}")
    dfNew.to_csv("teamCSVs/assistedOutdegree.csv",index=False)

def CalculateIndegreeCentrality():
    ## Formula = sum(maxIndegree - CID(playeri)) / 4 * number of assists
    df = pd.read_csv("teamCSVs/assistedIndegree.csv")
    
    ## Gather the variables needed
    sql = '''
    SELECT team,
    max(assistedIndegree) as maxIndegree,
    sum(assistedIndegree) as totalAssists
    FROM df 
    GROUP BY team
    '''
    ## contains max indegree, total assists
    dfTeamIdMax = pandasql.sqldf(sql, locals()) ## all unique game ids here

    ## For each team
    in_dict = {}
    for index, row in dfTeamIdMax.iterrows():
        maxIndeg = row['maxIndegree']
        sumIndeg = row['totalAssists']
        currentTeam = row['team']
        dfTemp = df.loc[df['team'] == str(currentTeam)]
        numerator = 0
        denominator = 4*sumIndeg
        for idx, r in dfTemp.iterrows():
            numerator += (maxIndeg - r['assistedIndegree'])
        in_dict[row['team']] = round(numerator / denominator,4)

    dfIn = pd.DataFrame(in_dict.items(), columns=['Team', 'IndegreeCent'])
    dfIn.to_csv("teamCSVs/indegreeCentrality.csv",index=False)
    
def CalculateOutdegreeCentrality():
    ## Formula = sum(maxIndegree - CID(playeri)) / 4 * number of assists
    df = pd.read_csv("teamCSVs/assistedOutdegree.csv")
    
    ## Gather the variables needed
    sql = '''
    SELECT team, 
    max(assistedOutdegree) as maxOutdegree,
    sum(assistedOutdegree) as totalAssists
    FROM df 
    GROUP BY team
    '''
    ## contains max indegree, total assists
    dfTeamIdMax = pandasql.sqldf(sql, locals()) ## all unique game ids here
    
    sql ='''
    SELECT dfTeamIdMax.team,
    sum(dfTeamIdMax.maxOutdegree) as maxOutdegree,
    dfTeamIdMax.totalAssists,
    sum(df.assistedOutdegree) as assistedOutdegree
    FROM dfTeamIdMax
    INNER JOIN df
    ON dfTeamIdMax.team = df.team
    GROUP BY dfTeamIdMax.team
    ORDER BY dfTeamIdMax.team
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    out_dict = {}
    for index, row in dfFinal.iterrows():
        numerator = row['maxOutdegree'] - row['assistedOutdegree'] ## sum(maxIndegree - CID(playeri))
        denom = 4 * row['assistedOutdegree'] ##4 * number of assists
        out_dict[row['team']] = round(numerator / denom,4)
    dfOut = pd.DataFrame(out_dict.items(), columns=['Team', 'OutdegreeCent'])
    dfOut.to_csv("teamCSVs/outdegreeCentrality.csv",index=False)

def CalculatePerMinMetrics():
    df = pd.read_csv("PATH_TO_FINAL_DATA_FILE.csv")
    
    sql = '''
    SELECT 
    gameId, 
    teamId, 
    sum(kills) as kills, 
    sum(assists) as assists, 
    sum(goldEarned) as gold, 
    sum(visionScore) as visionScore, 
    sum(champExperience) as champExperience, 
    sum(totalMinionsKilled) as totalMinionsKilled, 
    gameDuration
    FROM df
    GROUP BY gameId, teamId
    '''
    dfGrp = pandasql.sqldf(sql, locals()) ## all unique game ids here

    sql = '''
    SELECT 
    gameId, teamId,
    ROUND((kills/gameDuration),4) as KPM, 
    ROUND((assists/gameDuration),4) as AsPM, 
    ROUND((gold/gameDuration),4) as GPM,
    ROUND((visionScore/gameDuration),4) as visionScorePM,
    ROUND((champExperience/gameDuration),4) as champExperiencePM,
    ROUND((totalMinionsKilled/gameDuration),4) as minionsKilledPM
    FROM dfGrp
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    dfFinal["uid"] = dfFinal["gameId"].astype(str) + "_" + dfFinal["teamId"].astype(str)
    dfFinal.drop(['gameId','teamId'], axis=1,inplace=True)
    # print(dfFinal)
    dfFinal.to_csv("teamCSVs/perMinMetrics.csv",index=False)

## Intensity calculation 
def CalculateIntensity():

    dfComplete = pd.read_csv("PATH_TO_FINAL_DATA_FILE.csv")
    dfOutdeg = pd.read_csv("teamCSVs/assistedOutdegree.csv")

    ## Add unique id for each team to dfComplete
    dfComplete["uid"] = dfComplete["gameId"].astype(str) + "_" + dfComplete["teamId"].astype(str)

    ## Reduce the assistedOutdegree for team metrics
    sql = '''
    SELECT team, sum(assistedOutdegree) as assists
    FROM dfOutdeg
    GROUP BY team
    '''
    dfAssists = pandasql.sqldf(sql, locals()) ## all unique game ids here

    sql = '''
    SELECT gameId, teamId, uid,
    sum(kills) as kills, 
    sum(turretKills) as turretKills,
    sum(epicMonsterKills) as epicMonsterKills,
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
    dfFinal.to_csv("teamCSVs/intensity.csv",index=False)

## Calculate Weight Centralisation
def CalculateWeightCentralisation():
    
    ## Formula = /(5^2 - 5 - 1)A

    df = pd.read_csv("teamCSVs/assists.csv")

    fromList = df['frm'].tolist() ## this is i
    teamList = df['team'].tolist()
    uniqueTeams = list(dict.fromkeys(teamList))

    toList = df['to_player'].tolist() ## this is j
    weightList = df['weight'].tolist() ## this is w

    currentFrmLst = []
    currentWeightLst = []
    weightCentDict = {}
    startIdx = 0
    ctr = 0
    idx = 0 ##using a manual index
    lastGame = False
    for uidTeam in uniqueTeams: # for every unique team
        for team in teamList[startIdx:]: ## limit it so it doesnt have to loop the entire list
            if team == uidTeam:
                currentFrmLst.append(fromList[idx])
                currentWeightLst.append(weightList[idx])
                idx += 1
            
            if team != uidTeam or idx == len(teamList) :
                ctr+=1
                startIdx = idx
                ## Do the maths
                maxWeight = max(currentWeightLst)
                totalAssists = sum(currentWeightLst)
                recSum = 0
                ## sum( sum(maxWeight - weight(i to j++)); i++ )
                for index,frm in enumerate(currentFrmLst):
                    weight = currentWeightLst[index]
                    recSum += (maxWeight - weight)
                weightCent = round(recSum /(((5**2) - 5 - 1) * totalAssists),4)
                weightCentDict[uidTeam] = weightCent
                # Maths is done! Clear the temporary lists and continue
                currentFrmLst.clear()
                currentWeightLst.clear()

                break
            

    ## Write dict to file:
    dfOut = pd.DataFrame(weightCentDict.items(), columns=['Team', 'WeightCentralisation'])
    dfOut.to_csv("teamCSVs/weightCentralisation.csv",index=False)

## calculate the total wins
def CalculateTotalWins():

    df = pd.read_csv("PATH_TO_FINAL_DATA_FILE.csv")

    sql = '''
    SELECT gameId, teamId, avg(win) as win, avg(avgrank) as avgrank
    FROM df
    GROUP BY gameId,teamId
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    dfFinal["uid"] = dfFinal["gameId"].astype(str) + "_" + dfFinal["teamId"].astype(str)
    dfFinal.drop(columns=['gameId','teamId'],inplace=True)
    dfFinal.to_csv("teamCSVs/gameWins.csv",index=False)

## join all needed metrics from all files into a single csv
def JoinMetricsTogether():
    ## read each csv
    dfPerMin = pd.read_csv("teamCSVs/perMinMetrics.csv")
    dfOutdeg = pd.read_csv("teamCSVs/outdegreeCentrality.csv")
    dfIndeg = pd.read_csv("teamCSVs/indegreeCentrality.csv")
    dfAsRatio = pd.read_csv("teamCSVs/intensity.csv")
    dfWeightCent = pd.read_csv("teamCSVs/weightCentralisation.csv")
    dfWins = pd.read_csv("teamCSVs/gameWins.csv")
    dfResistance = pd.read_csv("teamCSVs/resistance.csv")
    ## Joins all metrics into a single DF
    sql = '''
    SELECT 
    dfPerMin.uid, dfWeightCent.WeightCentralisation, dfPerMin.KPM, dfPerMin.AsPM, dfPerMin.GPM,
    dfPerMin.visionScorePM, dfPerMin.champExperiencePM, dfPerMin.minionsKilledPM,
    dfOutdeg.OutdegreeCent, dfIndeg.IndegreeCent, dfWins.win, dfWins.avgrank ,
    dfAsRatio.insensity, dfResistance.resistance
    FROM dfPerMin
    INNER JOIN dfOutdeg
        ON dfPerMin.uid = dfOutdeg.Team
    INNER JOIN dfIndeg
        ON dfPerMin.uid = dfIndeg.Team
    INNER JOIN dfAsRatio
        ON dfPerMin.uid = dfAsRatio.uid
    INNER JOIN dfWeightCent
        ON dfPerMin.uid = dfWeightCent.Team
    INNER JOIN dfWins
        ON dfPerMin.uid = dfWins.uid
    INNER JOIN dfResistance
        ON dfPerMin.uid = dfResistance.team
    '''
    dfFinal = pandasql.sqldf(sql, locals()) ## all unique game ids here
    dfFinal.to_csv("teamCSVs/CombinedMeasurements.csv",index=False)
    

## Generate the assists csv
df = pd.read_csv("PATH_TO_FINAL_DATA_FILE.csv")
GenerateAssistsCsv(df,10760) ## limit officially 10760 ## calc weightlist
df2 = pd.read_csv("PATH_TO_ASSISTS_FILE.csv")

# these 2 are required for CalculateIndegreeCentrality & CalculateOutdegreeCentrality
CalculateOutdegree(df2) ## calc. outdegree
CalculateIndegree(df2) ## calc. indegree

CalculateIndegreeCentrality() ## Works out inCentrality for the team
CalculateOutdegreeCentrality() ## Works out outCentrality for the team
CalculatePerMinMetrics() ## converts into per-minute metrics
CalculateIntensity() ## calculate intensity 
CalculateWeightCentralisation() ## calculate weight centralisation
CalculateTotalWins() ## calc. total wins
JoinMetricsTogether() ## join all metrics