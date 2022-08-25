"""
Demand Sampling and Basic Geo-Units

Data preparation

1. Download the address dataset from
https://data.gov.au/data/dataset/19432f89-dc3a-4ef3-b943-5326ef1dbecc/resource/fdce090a-b356-4afe-91bb-c78fbf88082a/download/g-naf_may22_allstates_gda2020_psv_106.zip

2. Extract the zip file and copy the file `NSW_ADDRESS_DEFAULT_GEOCODE_psv.psv` to the `data` directory

3. Download the Statistical Area 2 dataset from
https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/SA2_2021_AUST_SHP_GDA2020.zip

4. Extract the zip file and copy the entire direcotry `SA2_2021_AUST_SHP_GDA2020` to the `data` directory

As stated in our blog post, the first file includes addresses for demand sampling, 
the second file includes SA2 to form the Basic Geo-Units
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="data directory for raw and intermediate datasets")
    args = parser.parse_args()
    DATA_DIR = args.data_dir

    # define the south west Sydney region
    min_x, min_y, max_x, max_y = 150.996384, -34.096538, 151.218663, -33.822586

    # demand sampling - obtain addresses
    add_fn = f"{DATA_DIR}/NSW_ADDRESS_DEFAULT_GEOCODE_psv.psv"
    print('Reading address file....', end='', flush=True)
    df_add = pd.read_csv(add_fn, sep='|')
    print(f'df_add shape = {df_add.shape}')

    # only need addresses within the south west Sydney region
    df_add = df_add[(df_add.LONGITUDE >= min_x) & (df_add.LONGITUDE <= max_x) & (df_add.LATITUDE >= min_y) & (df_add.LATITUDE <= max_y)]
    # only need property and building addresses
    df_add_f = df_add[(df_add.GEOCODE_TYPE_CODE == 'PC') | (df_add.GEOCODE_TYPE_CODE == 'PCM') | (df_add.GEOCODE_TYPE_CODE == 'BC')]
    gdf_add = gpd.GeoDataFrame(df_add_f, geometry=gpd.points_from_xy(df_add_f.LONGITUDE, df_add_f.LATITUDE), crs='EPSG:7844')
    df_stops = gdf_add.sample(5000)

    # basic geo-unit - obtain SA2s
    df_sa2 = gpd.read_file(f'{DATA_DIR}/SA2_2021_AUST_SHP_GDA2020')
    print(f'SA2 shape = {df_sa2.shape}')
    df_sydney_sa2 = df_sa2[(df_sa2.GCC_NAME21 == 'Greater Sydney')]
    df_sa2_sw_syd = gpd.sjoin(df_sydney_sa2, df_stops, how='inner', predicate='contains')
    print('df_sa2_sw_syd.shape = ', df_sa2_sw_syd.shape)

    df_all_stops = df_stops.copy()
    df_all_stops['longitude'] = df_all_stops['LONGITUDE']
    df_all_stops['latitude'] = df_all_stops['LATITUDE']
    df_all_stops['address_id'] = df_all_stops['ADDRESS_DEFAULT_GEOCODE_PID']
    drop_columns = []
    for col_name in df_all_stops.columns:
        if col_name not in ['longitude', 'latitude', 'address_id']:
            drop_columns.append(col_name)
    
    df_all_stops.drop(columns=drop_columns, inplace=True)
    df_all_stops.to_csv(f'{DATA_DIR}/stops_all.csv', index=False)
    print('Writing SA2 as GeoJson....', end='', flush=True)
    df_sa2_sw_syd.to_file(f'{DATA_DIR}/gdf_sa2_package_map.geojson', driver='GeoJSON', index=False)
    print('Done')
