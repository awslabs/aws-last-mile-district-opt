import argparse

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from tqdm import tqdm
import joblib

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="data directory for raw and intermediate datasets")
    parser.add_argument("--time_matrix_fn", help="e.g. data/ret_time_1653986430_4968.npy", required=True)
    args = parser.parse_args()
    tm_matrix_fn = args.time_matrix_fn        
    DATA_DIR = args.data_dir

    df_all_stops = pd.read_csv(f'{DATA_DIR}/stops_all.csv')
    df = gpd.read_file(f'{DATA_DIR}/gdf_sa2_package_map.geojson')
    dist_matrix = np.load(tm_matrix_fn)

    sa2_list = []
    for gname, df_sa2 in df.groupby('SA2_CODE21'):
        sa2_list.append((gname, list(df_sa2.ADDRESS_DEFAULT_GEOCODE_PID), df_sa2.geometry.values[0]))
    nb_sa2 = len(sa2_list)
    sa2_matrix = np.ones((nb_sa2, nb_sa2))

    for i, from_sa2 in enumerate(sa2_list):
        for j, to_sa2 in enumerate(sa2_list):
            #print(from_sa2)
            if i == j:
                new_val = 0
                
            elif from_sa2[-1].intersects(to_sa2[-1]):
                new_val = 0
            else:
                row_slice = df_all_stops[df_all_stops.address_id.isin(from_sa2[1])].index
                col_slice = df_all_stops[df_all_stops.address_id.isin(to_sa2[1])].index
                ixgrid = np.ix_(row_slice, col_slice)
                partial_matrix = dist_matrix[ixgrid]
                new_val = int(partial_matrix.sum() / (len(row_slice) * len(col_slice)))
                
                
            sa2_matrix[i][j] = new_val
    
    # make it symmetric by taking the max of the pair
    sa2_matrix = np.maximum(sa2_matrix, sa2_matrix.transpose())
    tm_arr = sa2_matrix
    max_dist = tm_arr.max()
    tm_arr_inverse = max_dist - tm_arr
    tm_arr_inverse = tm_arr_inverse.astype(np.int32)

    nb_nodes = tm_arr_inverse.shape[0]
    scale_factor = 1000
    pc = np.percentile(tm_arr_inverse, 99.5)
    adjlist = []
    nodew = []
    for i in tqdm(range(nb_nodes)):
        row = tm_arr_inverse[i]
        sorted_index = reversed(np.argsort(row))
        selected_idx = []
        for sidx in sorted_index:
            if sidx == i: # itself
                continue
            weight = row[sidx]
            if weight < pc:
                break
            selected_idx.append((sidx, int(weight))) # add index and weight
        adjlist.append(selected_idx)
        nodew.append(len(sa2_list[i][1]))
    
    #assert len(nodew) == len(adjlist)
    joblib.dump(adjlist, f'{DATA_DIR}/adjlist.joblib')
    joblib.dump(nodew, f'{DATA_DIR}/nodew.joblib')
