import argparse
from genericpath import exists

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
import metis
from collections import defaultdict
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="data directory for raw and intermediate datasets")
    parser.add_argument("--time_matrix_fn", help="e.g. data/ret_time_1653986430_4968.npy", required=True)
    args = parser.parse_args()
    DATA_DIR = args.data_dir
    df_all_stops = pd.read_csv(f'{DATA_DIR}/stops_all.csv')
    df_sol = gpd.read_file(f'{DATA_DIR}/gdf_sol_polygons.geojson')
    dist_matrix = np.load(args.time_matrix_fn)
    nb_polygon = df_sol.shape[0]
    df_sol['part'] = list(np.arange(nb_polygon))
    gdf_add = gpd.GeoDataFrame(df_all_stops, 
                                geometry=gpd.points_from_xy(df_all_stops.longitude, df_all_stops.latitude), 
                                crs='EPSG:4326')
    df_add_sol = gpd.sjoin(gdf_add, df_sol, predicate='within')

    
    os.makedirs(f'{DATA_DIR}/tsp_df_input/sol')
    for i in range(nb_polygon):
        df_slice = df_add_sol[df_add_sol.part == i]
        df_slice[['longitude', 'latitude']].to_csv(f'{DATA_DIR}/tsp_df_input/sol/part_{i}.csv', index=False)
    
    os.makedirs(f'{DATA_DIR}/tsp_dist_matrix/sol')
    for i in range(nb_polygon):
        slice_index = df_add_sol[df_add_sol.part == i].index
        ixgrid = np.ix_(slice_index, slice_index)
        partial_matrix = dist_matrix[ixgrid]
        np.save(f'tsp_dist_matrix/sol/part_{i}.npy', partial_matrix)


