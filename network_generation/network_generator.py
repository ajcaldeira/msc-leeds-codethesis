import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import pandasql
# import laplacian_test
from sklearn.preprocessing import MinMaxScaler

def ScaleWeights(weights,newMax,newMin):
    oldMax = max(weights)
    oldMin = min(weights)
    currRange = (oldMax - oldMin)  
    newRange = (newMax - newMin)
    newWeights = []
    for weight in weights:
        newWeight = (((weight - oldMin) * newRange) / currRange) + newMin
        newWeights.append(newWeight)
    return newWeights


def GetGraphClustering(G):
    A = nx.to_scipy_sparse_matrix(G)
    return A.todense()

def CalcNodeSize(dfNodeSizes,uid):
    sql = f'SELECT scaledNodeSize from dfNodeSizes WHERE tid = "{uid}"'
    dfFinal = pandasql.sqldf(sql, locals())
    dfFinal['scaledNodeSize'] = dfFinal['scaledNodeSize'] * 1500
    
    return dfFinal['scaledNodeSize'].tolist()

def DrawGraph(G,gameData,dfNodeSizes):
    ## convert the weights
    weights = [i['scaledWeights'] for i in dict(G.edges).values()]

    ## labels are the participants ids
    labels = [i for i in dict(G.nodes).keys()]
    labels = {i:i for i in dict(G.nodes).keys()}

    NodeSizelist = CalcNodeSize(dfNodeSizes,gameData['uid'][0])
    fig, ax = plt.subplots(figsize=(7,7))
    pos = nx.circular_layout(G)

    ## Develop the graph
    nx.draw_networkx_nodes(G, pos, ax = ax, label=True,node_size=NodeSizelist, alpha=0.4)
    nx.draw_networkx_edges(G, pos, width=weights, ax=ax,node_size=NodeSizelist,connectionstyle="arc3,rad=0.1")
    ## Start preparing the figure for output
    ax.set_title(gameData['uid'][0], pad=30)
    ax.set_xlabel(f'''WIN: {gameData['win'][0]} | GPM: {round(gameData['GPM'][0])} | Performance: {round(gameData['nf1'][0],2)}, {round(gameData['nf2'][0],2)}, {round(gameData['nf3'][0],2)} \n InCent: {gameData['IndegreeCent'][0]} | OutCent: {gameData['OutdegreeCent'][0]} | CW: {gameData['WeightCentralisation'][0]} \n RANK: {gameData['avgrank'][0]} | RESISTANCE: {gameData['resistance'][0]}''',fontsize=16,labelpad=10)
    nx.draw_networkx_labels(G, pos, ax=ax)
    plt.gcf().subplots_adjust(bottom=0.15)
    ## Save the plot to file
    plt.savefig(f'NetworkImages/{gameData["uid"][0]}.jpeg')
    plt.close(fig)


def GetGameData(uid,df):
    
    sql = f'''
    SELECT uid,GPM,WeightCentralisation,OutdegreeCent,IndegreeCent,win,avgrank,nf1,nf2,nf3,resistance
    FROM df
    WHERE uid = '{uid}'
    '''
    dfFinal = pandasql.sqldf(sql, locals())
    return dfFinal.to_dict('list')

## Read the team level game data
dfGameata = pd.read_csv('PATH_TO_TEAM_DATA.csv')

## Read the file with weights
dfWeightfile = pd.read_csv('PATH_TO_WEIGHTFILE.csv')

## Scale all weights equally
newWeights = ScaleWeights(dfWeightfile['weight'].tolist(),10,0)
dfWeightfile['scaledWeights'] = newWeights

## Get node sizes by performance factor
dfNodeSizes = pd.read_csv('PATH_TO_FILE_OF_PERFORMANCE_FACTOR_1.csv')
## Filter out bad cols:
sql = '''select * from dfNodeSizes where filter = 1 '''
dfNodeSizes = pandasql.sqldf(sql, locals())
nodeSizes = dfNodeSizes['ZIPF_TESTER'].tolist()
nodeSizesFloat = [float(i) for i in nodeSizes]
dfNodeSizes['scaledNodeSize'] = ScaleWeights(nodeSizesFloat,0.1,3) ## use this function but with 0.5 and 1.5 as the range
uidList = dfNodeSizes['tid'].tolist()

## Use this for generating specific graphs
# uidList = ['EUW1_XXXXXXXXXX_XXX'] 

for uid in uidList: ## loop through each team id
    gameData = GetGameData(uid,dfGameata)
    
    ## pick only the specified UID from the weightlist
    sql = f'''SELECT * FROM dfWeightfile WHERE team = "{uid}"'''
    dfCurrentTeamWeights = pandasql.sqldf(sql, locals())
    ## Generate graph
    G = nx.from_pandas_edgelist(dfCurrentTeamWeights,'frm','to_player', edge_attr='scaledWeights',create_using=nx.MultiDiGraph(directed=True))
    weightsAll = nx.get_edge_attributes(G,'scaledWeights')
    G.remove_edges_from((e for e, w in weightsAll.items() if w == 0))
    ## Draw it to screen
    DrawGraph(G,gameData,dfNodeSizes)
    


