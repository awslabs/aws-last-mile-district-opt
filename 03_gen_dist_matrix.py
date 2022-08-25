"""
Objects to connect to and retrieve data from the Valhalla API.
"""
import argparse
import json
import time
from random import sample
from timeit import default_timer as timer
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

class ValhallaAPI:
    def __init__(self, address):
        self.address = address
        self.matrix_address = "http://{}/sources_to_targets".format(
            self.address)
    
    def generate_matrix(self, points: Iterable[Dict], to_points: Iterable[Dict]=None, costing="auto", units="km") -> Iterable:
        """
        Return a matrix of times and distances from the Valhalla API.
        https://valhalla.readthedocs.io/en/latest/api/matrix/api-reference/
        Points must be provided in a list of points in the format {"lat": float, "lon": float}.
        """
        data_dict = {
            "sources": points,
            "targets": points if to_points is None else to_points,
            "costing": costing,
            "units": units
        }
        #print(urllib.parse.quote(str(data_dict)))
        r = requests.post(self.matrix_address,
            data=json.dumps(data_dict))

        # Bomb out if we didn't get a perfect result
        if r.status_code != 200:
            raise ValueError(str(r.status_code) + " - " + r.text)
        
        # Process the returned values
        # TODO: process this into preferred formats -- right now we're just returning the JSON as is
        # This may well not be the most useful format
        return r.status_code, json.loads(r.text)

if __name__ == "__main__":
    """
    json_ret['sources_to_targets'][1]
    [{'distance': 29.801, 'time': 1390, 'to_index': 0, 'from_index': 1},
    {'distance': 0.0, 'time': 0, 'to_index': 1, 'from_index': 1},
    {'distance': 58.734, 'time': 2562, 'to_index': 2, 'from_index': 1},
    {'distance': 82.363, 'time': 3507, 'to_index': 3, 'from_index': 1},
    {'distance': 57.24, 'time': 2411, 'to_index': 4, 'from_index': 1},
    {'distance': 48.533, 'time': 2174, 'to_index': 5, 'from_index': 1},
    {'distance': 81.301, 'time': 3277, 'to_index': 6, 'from_index': 1},
    {'distance': 19.647, 'time': 1168, 'to_index': 7, 'from_index': 1},
    {'distance': 58.196, 'time': 2499, 'to_index': 8, 'from_index': 1},
    {'distance': 27.502, 'time': 1235, 'to_index': 9, 'from_index': 1}]
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", 
                        help="raw data dir for routes_all.csv and stops_all.csv")
    parser.add_argument("--valhalla_address", default="localhost:8002")
    parser.add_argument("--chunk_size", default=50, type=int, help="chunk size")
    args = parser.parse_args()
    data_dir = args.data_dir
    df_stops = pd.read_csv(f'{data_dir}/stops_all.csv')
    print(df_stops.shape)
    nb_sample = df_stops.shape[0]
    session_id = int(time.time())
    df_stops.to_csv(f'df_sample_{session_id}_{nb_sample}.csv', index=False)
    points = []
    cc = 0
    for _, point in df_stops.iterrows():
        points.append({"lon": point.longitude, "lat": point.latitude})

    print('len(points) = ', len(points))
    chunk_size = args.chunk_size
    ttt = np.array_split(points, nb_sample // chunk_size)
    valhalla = ValhallaAPI(args.valhalla_address)
    ret_dist = np.ones((nb_sample, nb_sample))
    ret_time = np.ones((nb_sample, nb_sample))
    for row_ind, tt1 in tqdm(enumerate(ttt)):
        for col_ind, tt2 in enumerate(ttt):
            pts1, pts2 = list(tt1), list(tt2)
            status_code, json_ret = valhalla.generate_matrix(pts1, to_points=pts2)
            for idx, row in enumerate(json_ret['sources_to_targets']):
                g_rid = row_ind * chunk_size + idx
                for col in row:
                    g_cid = col_ind * chunk_size + col['to_index']
                    ret_dist[g_rid][g_cid] = col['distance']
                    ret_time[g_rid][g_cid] = col['time']
    
    np.save(f'{data_dir}/ret_dist_{session_id}_{nb_sample}.npy', ret_dist)
    np.save(f'{data_dir}/ret_time_{session_id}_{nb_sample}.npy', ret_time)
