## This file is to join the game data csv and the ranks csv
import pandas as pd
import pandasql

games = pd.read_csv("joined.csv") ## Csv file with the bulk of the data
ranks = pd.read_csv("playerRanks.csv") ## Ranked data csv

## SQL to execute on the dataframe
sql = '''
SELECT ranks.gameId, ranks.summonerId, ranks.rank, ranks.avgrank, 
gameDuration,puuid,teamId,win,teamPosition,kills,epicMonsterKills,assists,turretKills,
visionScore,visionWardsBoughtInGame,magicDamageDealtToChampions,deaths,
totalMinionsKilled,timeCCingOthers,totalDamageTaken,totalHealsOnTeammates,
totalTimeSpentDead,goldEarned,objectivesStolen,objectivesStolenAssists,
participantId,participantsAssisted,towerKillsAssisted,monsterKillsAssisted,
participantsAssistedWithPressure,champExperience,totalMinionsKilled
FROM ranks
LEFT JOIN games
ON ranks.summonerId = games.summonerId AND ranks.gameId = games.gameId
ORDER BY ranks.gameId, participantId ASC
'''

## Write the complete csv file which holds all the data
## Some extra fields are included in the file incase there was any use later down the line
## so not all variables in the csv are used in analysis
dfFinal = pandasql.sqldf(sql, locals())
dfFinal.to_csv("complete.csv", index=False)
