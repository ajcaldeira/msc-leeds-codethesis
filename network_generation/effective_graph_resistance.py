import networkx as nx
from networkx import linalg
import pandas as pd
import numpy as np
from scipy.sparse.csgraph import laplacian
import pandasql

## Return resistance value
def CalcResistance(eigenvalues,N=5):
    ## Round all values:

    eigval = eigenvalues.tolist()
    # print(eigval)
    roundedEigval = [round(val, 2) for val in eigval]
    roundedEigval = [i for i in roundedEigval if i != 0]

    summ = 0
    for e in roundedEigval:
        summ = summ + (1/e)
    R = 5 * summ
    return R


def GetGameIDs():
    dfGames = pd.read_csv('../stats notes/spss_02_sept_full.csv') ## has unique ids, could use any file with them
    return dfGames['uid'].tolist()

def GenerateResistances():
    uidList = GetGameIDs()
    dfWeights = pd.read_csv('../analysis_demos/teamCSVs/assists.csv')
    resistanceDict = {}
    counter = 0
    for uid in uidList:
        sql = f'''SELECT * FROM dfWeights WHERE team = "{uid}"'''
        dfCurrentTeamWeights = pandasql.sqldf(sql, locals())

        G = nx.from_pandas_edgelist(dfCurrentTeamWeights,'frm','to_player', edge_attr='weight',create_using=nx.MultiGraph(directed=True))

        W = nx.adjacency_matrix(G)
        D = np.diag(np.sum(np.array(W.todense()), axis=1))

        L = D - W
        e, v = np.linalg.eig(L)

        resistanceValue = CalcResistance(e)
        resistanceDict[uid] = round(resistanceValue,4)
        counter+=1
        if counter % 100 == 0:
            print(f'Completed: {counter}/{len(uidList)}')
        

    dfIn = pd.DataFrame(resistanceDict.items(), columns=['team', 'resistance'])
    dfIn.to_csv("../analysis_demos/teamCSVs/resistance.csv",index=False)


GenerateResistances()