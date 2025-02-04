import requests
from collections import defaultdict
import time
import numpy as np
from sklearn.cluster import KMeans
#url = "https://api.wmata.com/Bus.svc/json/jBusPositions[?RouteID][&Lat][&Lon][&Radius]"
regular_url = "https://api.wmata.com/Bus.svc/json/"
#url = "https://api.wmata.com/Bus.svc/json/jBusPositions"
#38.894762, -77.022825
#params = {"Lat": 38.894762, "Lon":-77.022825, "Radius":1000}
headers= {"api_key":"a00bebb0819a42deae5c457f06b7c1f4"}
#response = requests.get(url=url, params=params, headers=headers)
#print(response.json())
from classNode import Node
from geopy.distance import vincenty
import dill as pk
import pickle

def buses_radius(**kwargs):
    try:
        params = {}
        if "Lat" in kwargs and "Lon" in kwargs:
            params["Lat"] = kwargs["Lat"]
            params["Lon"] = kwargs["Lon"]
            params["Radius"] = kwargs["Radius"]
        url = regular_url + "jBusPositions"
        response = requests.get(url=url, params=params, headers=headers)
        return response.json()
    except:
        raise Exception("Invalid keyword arguments for buses_radius!")

def stops_radius(**kwargs):
    try:
        params = {}
        if "Lat" in kwargs and "Lon" in kwargs:
            params["Lat"] = kwargs["Lat"]
            params["Lon"] = kwargs["Lon"]
            params["Radius"] = kwargs["Radius"]
        url = regular_url + "jStops"
        response = requests.get(url=url, params=params, headers=headers)
        print(response.json())
        return response.json()
    except:
        raise Exception("Invalid keyword arguments for stops_radius!")

def path_details(Route_ID):
    #https://api.wmata.com/Bus.svc/json/jRouteDetails?RouteID=29K&Date=2019-11-9
    params = {"RouteID": Route_ID}
    url = regular_url + "jRouteDetails"
    return requests.get(url=url, params=params, headers=headers).json()

def get_all_paths():
    #https://api.wmata.com/Bus.svc/json/jRoutes
    url = regular_url + "jRoutes"
    return requests.get(url=url, headers=headers).json()

def create_nodes():
    nodes_dict = defaultdict(int)
    parent_dict = defaultdict(lambda: defaultdict(int))
    for path in get_all_paths()["Routes"]:
        path_detail = path_details(path["RouteID"])
        try:
            prev = None
            for stop in path_detail["Direction0"]["Stops"]:
                newNode = Node(**stop)
                nodes_dict[stop["StopID"]] = newNode
                if prev != None:
                    parent_dict[prev.stopID][newNode.stopID] = vincenty((prev.lat, prev.lon), (newNode.lat, newNode.lon))
                    #prev.set_child(newNode)
                prev = newNode
        except:
            print("Exception" + str(path_detail))
            continue
        try:
            prev = None
            for stop in path_detail["Direction1"]["Stops"]:
                newNode = Node(**stop)
                print(newNode)
                nodes_dict[stop["StopID"]] = newNode
                if prev != None:
                    parent_dict[prev.stopID][newNode.stopID] = vincenty((prev.lat, prev.lon), (newNode.lat, newNode.lon))
                    #prev.set_child(newNode)
                prev = newNode
        except:
            print("Exception" + str(path_detail))
            print("Parents Dict" + str(parent_dict))
            print("Nodes Dict" + str(nodes_dict))
            continue
        # try:
        # print(path_detail)
        time.sleep(0.1)




if __name__ == "__main__":
    create_nodes()
    with open("allstops.pk", "rb") as nodes_file:
        nodes_dict = pk.load(nodes_file)
    with open("crime.pk", "rb") as file:
        xl = pickle.load(file)
        xl = xl[xl["year"] == 2017]
        xl.dropna()
        X = xl.as_matrix(columns=['YBLOCK', 'XBLOCK'])
        dbscan = KMeans(n_clusters=8, random_state=0).fit(X)
        for latitude, longitude in dbscan.cluster_centers_:
            stops = stops_radius(**{"Lat": latitude, "Lon": longitude, "Radius": 5000})["Stops"]
            for stop in stops:
                update_node = nodes_dict[stop["StopID"]]
                if type(update_node) != int:
                    update_node.update_safety(vincenty((latitude, longitude), (update_node.lat, update_node.lon)).km/5)
        print(nodes_dict)
        with open("allstops.pk", "wb") as file:
            pk.dump(nodes_dict, file)
    # with open("parentstops.pk", "wb") as file:
    #     pk.dump(parent_dict, file)