import argparse

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
import metis
from collections import defaultdict

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="data directory for raw and intermediate datasets")
    parser.add_argument("--nb_polygons", type=int, default=23)
    args = parser.parse_args()
    nb_polygons = args.nb_polygons    
    DATA_DIR = args.data_dir
    df = gpd.read_file(f'{DATA_DIR}/gdf_sa2_package_map.geojson')
    #nb_polygons = df.CF.unique().shape[0]

    adjlist = joblib.load(f'{DATA_DIR}/adjlist.joblib')
    nodew = joblib.dump(f'{DATA_DIR}/nodew.joblib')

    metis_graph = metis.adjlist_to_metis(adjlist, nodew=nodew)
    edgecuts, parts = metis.part_graph(metis_graph, nb_polygons)
    nb_parts = len(set(parts))
    print('# of generated polygons = ', nb_parts)

    my_polygon_list = defaultdict(list)
    my_address_list = defaultdict(int)
    for idx, (gname, df_sa2) in enumerate(df.groupby('SA2_CODE21')):
        part_id = parts[idx]
        my_polygon_list[part_id].append(df_sa2.geometry.values[0])
        my_address_list[part_id] += df_sa2.geometry.shape[0]
    
    final_polygon_list = []
    for k, v in my_polygon_list.items():
        s = gpd.GeoSeries(v)
        final_polygon_list.append(s.unary_union)
    

    dict = {'geometry': final_polygon_list}
    df_output = pd.DataFrame(dict)
    df_output_geo = gpd.GeoDataFrame(df_output, geometry='geometry')
    df_output_geo.to_file(f'{DATA_DIR}/gdf_sol_polygons.geojson', driver='GeoJSON', index=False)

    ax = None
    color_list = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', 
              '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', 
              '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000']
    for i in range(df_output_geo.shape[0] - 1):
        ax = df_output_geo.iloc[i:i + 1].geometry.plot(alpha=0.5, lw=1, color=color_list[i % len(color_list)], label=f'Pol {i}', ax=ax)

    plt.scatter(df.LONGITUDE, df.LATITUDE, color='black', s=0.15, alpha=0.6, label='Address')
    plt.legend(fontsize=5, loc='best')
    plt.savefig('new_polygon.pdf')
