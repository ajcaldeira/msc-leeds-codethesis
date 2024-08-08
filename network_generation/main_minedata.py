## File with all formulae to calculate the metrics 
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from operator import itemgetter

## List of all nodes
def GetListOfNodes(G):
    return list(G.nodes())

## List of all edges
def GetListOfEdges(G):
    return list(G.edges(data = True))

## Number of Nodes within a single step from each node
def GetNumberNodesSingleStepFremEachNode(G):
    lst_nodes = GetListOfNodes(G)
    dict_single_step = {}
    for node in lst_nodes:
        dict_single_step[node] = len(list(G.neighbors(node)))

    return dict(sorted(dict_single_step.items()))

## Dict of degree for each node
def GetDegreeEachNode(G):
    return dict(G.degree())

## Float avg degree of network
def GetAverageDegreeNetwork(G):
    degree_dict = GetDegreeEachNode(G)
    total = 0
    for key in degree_dict:
        total +=degree_dict[key]
    avg = (total/len(degree_dict))
    return avg

## Dict betweeness centrality for each node
def GetBetweenessCentrality(G):
    # Get betweenness centrality
    btwn_centr_dict = nx.betweenness_centrality(G) 
    # Assign each to an attribute in your network
    nx.set_node_attributes(G, btwn_centr_dict, 'betweenness')
    sorted_btwn_centr = sorted(btwn_centr_dict.items(), key=itemgetter(1), reverse=True)
    return dict(sorted_btwn_centr)

## Dict Eigenvector Centrality for each node
def GetEigenvectorCentrality(G):
    # Get betweenness centrality
    eigen_centr_dict = nx.eigenvector_centrality(G) 
    # Assign each to an attribute in your network
    nx.set_node_attributes(G, eigen_centr_dict, 'eigenvector')
    sorted_eigen_centr = sorted(eigen_centr_dict.items(), key=itemgetter(1), reverse=True)
    return dict(sorted_eigen_centr)

## Integer number of edges in
def GetNumberOfEdges(G):
    return int(G.number_of_edges())

## Float density of network
def GetDensity(G):
    return nx.density(G)

def GetGraphClustering():
    A = nx.to_scipy_sparse_matrix(G)
    return A.todense()

def DrawGraph(G):
    weights = [i['weight'] for i in dict(G.edges).values()]
    labels = [i for i in dict(G.nodes).keys()]
    labels = {i:i for i in dict(G.nodes).keys()}


    fig, ax = plt.subplots(figsize=(5,5))
    pos = nx.circular_layout(G)
    nx.draw_networkx_nodes(G, pos, ax = ax, label=True,node_size=1500, alpha=0.4)
    nx.draw_networkx_edges(G, pos, width=weights, ax=ax,node_size=1500,connectionstyle="arc3,rad=0.1")
    nx.draw_networkx_labels(G, pos, ax=ax)

    plt.show()

def WriteToCsv(start_idx,currentLine):
    if start_idx == 0: ## first item, so write header, and overwrite file
        with open('graph_measure.csv', 'w') as f:
            f.write(f"density,noEdges,avgDegree,goldpm\n")
            f.write(f"{currentLine}")
    else:
        with open('graph_measure.csv', 'a') as f:
            f.write(f"{currentLine}")

## Takes in the graph 
def CalculateMetrics(G, start_idx, exclude=[]):
    currentLine = f"{round(GetDensity(G),3)},{int(GetNumberOfEdges(G))},{round(GetAverageDegreeNetwork(G),1)}"
    return currentLine
    
## This groups the players and gives out data per game
if __name__ == "__main__":

    ## Read CSV to dataframe
    df = pd.read_csv('weightfile.csv')

    ## Divide the dataframe by each game
    start_idx = 0
    end_idx = 0
    currentParticipant = 0
    previousParticipant = 0
    totalGold = 0
    for index,row in df.iterrows():
        currentParticipant = row['from']
        if previousParticipant != currentParticipant and previousParticipant < currentParticipant:
            totalGold += row['gold'] #total gold
            
        if previousParticipant > currentParticipant: ## We have hit the first id of the next team
            previousParticipant = 0
            currentParticipant = 0
            ##Generate graph
            G = nx.from_pandas_edgelist(df[start_idx:end_idx],'from','to', edge_attr='weight',create_using=nx.DiGraph(directed=True))

            currentLine = CalculateMetrics(G,start_idx)
            ##add additional details

            finalLine = f"{currentLine},{round(totalGold/df['dur'][end_idx-1],2)}\n"

            WriteToCsv(start_idx,finalLine)

            start_idx = end_idx
            totalGold = 0

        else: ## We are still on the same team
            previousParticipant = currentParticipant
            end_idx = index+1


##### DEFINITONS #####

## https://programminghistorian.org/en/lessons/exploring-and-analyzing-network-data-with-python#centrality

## Degree
# Degree is the simplest and the most common way of finding important nodes. 
# A node’s degree is the sum of its edges. If a node has three lines extending from it to other nodes, its degree is three.
# Degree can tell you about the biggest hubs, but it can’t tell you that much about the rest of the nodes. 

## Betweenness Centrality
# Betweenness centrality doesn’t care about the number of edges any one node or set of nodes has. 
# Betweenness centrality looks at all the shortest paths that pass through a particular node.

## Eigenvector centrality
# Eigenvector centrality is a kind of extension of degree — it looks at a combination of a node’s edges and the edges of that node’s neighbors. 
# Eigenvector centrality cares if you are a hub, but it also cares how many hubs you are connected to. 
# If you’re the only thing connecting two clusters, every communication between those clusters has to pass through you. 
# In contrast to a hub, this sort of node is often referred to as a broker. 

## Community / modularity - not sure if relevant
# what the subgroups or communities are within the larger social structure. 
# Is your network one big, happy family where everyone knows everyone else? 
# Or is it a collection of smaller subgroups that are only connected by one or two intermediaries?


# GetListOfNodes(G)
# GetListOfEdges(G)
# GetNumberNodesSingleStepFremEachNode(G)
# GetDegreeEachNode(G)
# GetAverageDegreeNetwork(G)
# GetBetweenessCentrality(G)
# GetNumberOfEdges(G)
# GetDensity(G)
# DrawGraph(G)