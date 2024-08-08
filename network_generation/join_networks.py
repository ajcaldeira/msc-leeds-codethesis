## An experimental file to join 2 networks onto one plot
## Not used in the thesis!! 
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('team1.csv')
df2 = pd.read_csv('team2.csv')

G = nx.from_pandas_edgelist(df,'from','to', edge_attr='weight',create_using=nx.MultiDiGraph(directed=True))
H = nx.from_pandas_edgelist(df2,'from','to', edge_attr='weight',create_using=nx.MultiDiGraph(directed=True))

Un = nx.disjoint_union(G,H)


def GetGraphClustering():
    A = nx.to_scipy_sparse_matrix(Un)
    return A.todense()

def DrawGraph(G):
    weights = [i['weight'] for i in dict(G.edges).values()]
    labels = [i for i in dict(G.nodes).keys()]
    labels = {i:i for i in dict(G.nodes).keys()}


    sizes = [11248,14528,10519,10247,8722,11248,14528,10519,10247,8722]
    scaledSizes = []

    for size in sizes:
        ## assume avgSize as the standard size
        scaledSizes.append(size/10)

    fig, ax = plt.subplots(figsize=(7,7))
    pos = nx.circular_layout(G)
    nx.draw_networkx_nodes(G, pos, ax = ax, label=True,node_size=scaledSizes, alpha=0.4)
    nx.draw_networkx_edges(G, pos, width=weights, ax=ax,node_size=scaledSizes,connectionstyle="arc3,rad=0.1")
    nx.draw_networkx_labels(G, pos, ax=ax)


    plt.show()

GetGraphClustering()