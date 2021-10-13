## This file is for testing and making 1 off networks
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

def GetGraphClustering(G):
    A = nx.to_scipy_sparse_matrix(G)
    i = A.todense().ravel()

    return i

def GetGraphList():
    df = pd.read_csv('t.csv') ## weight file

    graphList = []
    currentPlayer = 0
    prevPlayer = 0
    startIdx = 0
    for index, row in df.iterrows():
        currentPlayer = row['frm']
        if prevPlayer > currentPlayer: ##prevplayer is higher than the current, means its in the next game
            # the previous game is complete, create the graph
            G = nx.from_pandas_edgelist(df[startIdx:index],'frm','to', edge_attr='weight',create_using=nx.MultiDiGraph(directed=True))
            graphList.append(GetGraphClustering(G))
            startIdx = index #reset the index back to the end of the current stint
            prevPlayer = currentPlayer
        else:
            prevPlayer = currentPlayer
            
    return graphList

GetGraphList()



def DrawGraph(G):
    weights = [i['weight'] for i in dict(G.edges).values()]
    labels = [i for i in dict(G.nodes).keys()]
    labels = {i:i for i in dict(G.nodes).keys()}

    fig, ax = plt.subplots(figsize=(7,7))
    pos = nx.circular_layout(G)
    ## Draw nodes and edges
    nx.draw_networkx_nodes(G, pos, ax = ax, label=True, node_size=1500, alpha=0.4)
    nx.draw_networkx_edges(G, pos, width=weights, ax=ax,node_size=1500, connectionstyle="arc3,rad=0.1")
    nx.draw_networkx_labels(G, pos, ax=ax)

    ## Display the image
    plt.show()

## Call these to run the file
# GetGraphClustering()
# DrawGraph(G)