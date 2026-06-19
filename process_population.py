import pandas as pd
import geopandas as gpd
import json
import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def process_population():
    print("집계구 및 인구 데이터 로드 중...")
    try:
        oa_shp = gpd.read_file('집계구/bnd_oa_00_2025_2Q.shp', encoding='euc-kr')
    except Exception as e:
        print("집계구 로드 에러:", e)
        return
        
    pop_df = pd.read_csv('인구/2025년기준_2024년_인구총괄(총인구).csv', encoding='euc-kr', header=None, names=['year', 'tot_oa_cd', 'category', 'value'])
    
    # Merge
    oa_shp['TOT_OA_CD'] = oa_shp['TOT_OA_CD'].astype(str)
    pop_df['tot_oa_cd'] = pop_df['tot_oa_cd'].astype(str)
    oa_pop = oa_shp.merge(pop_df, left_on='TOT_OA_CD', right_on='tot_oa_cd', how='left')
    
    # Clean population values
    def clean_val(x):
        try:
            return float(x)
        except:
            return 0.0
            
    oa_pop['value'] = oa_pop['value'].apply(clean_val)
    
    print("등시간권 로드 중...")
    p_30 = gpd.read_file('data/pangyo_iso30.geojson')
    p_60 = gpd.read_file('data/pangyo_iso60.geojson')
    d_30 = gpd.read_file('data/dongtan_iso30.geojson')
    d_60 = gpd.read_file('data/dongtan_iso60.geojson')
    
    if oa_pop.crs is None: oa_pop.set_crs('epsg:5179', inplace=True)
    oa_pop = oa_pop.to_crs('epsg:5179')
    
    p_30_5179 = p_30.to_crs('epsg:5179')
    p_60_5179 = p_60.to_crs('epsg:5179')
    d_30_5179 = d_30.to_crs('epsg:5179')
    d_60_5179 = d_60.to_crs('epsg:5179')
    
    print("공간 결합 연산 중...")
    oa_centroids = oa_pop.copy()
    oa_centroids['geometry'] = oa_centroids.geometry.centroid
    
    def calc_pop(centroids, poly):
        joined = gpd.sjoin(centroids, poly, how='inner', predicate='within')
        joined = joined.drop_duplicates(subset=['TOT_OA_CD'])
        return joined['value'].sum()
        
    p_30_pop = calc_pop(oa_centroids, p_30_5179)
    p_60_pop = calc_pop(oa_centroids, p_60_5179)
    d_30_pop = calc_pop(oa_centroids, d_30_5179)
    d_60_pop = calc_pop(oa_centroids, d_60_5179)
    
    import os
    stats_file = 'data/stats.json'
    
    if os.path.exists(stats_file):
        with open(stats_file, 'r', encoding='utf-8') as f:
            try:
                stats = json.load(f)
            except json.JSONDecodeError:
                stats = {}
    else:
        stats = {}
        
    if 'pangyo' not in stats:
        stats['pangyo'] = {'pop_total': 12000, 'workers': 74800, 'land_use': [10, 50, 0, 40]}
    if 'dongtan' not in stats:
        stats['dongtan'] = {'pop_total': 35000, 'workers': 22000, 'land_use': [40, 40, 0, 20]}
        
    stats['pangyo']['pop_30'] = int(p_30_pop)
    stats['pangyo']['pop_60'] = int(p_60_pop)
    stats['dongtan']['pop_30'] = int(d_30_pop)
    stats['dongtan']['pop_60'] = int(d_60_pop)
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)
        
    print(f"통계 결과 업데이트 완료: {stats}")

if __name__ == '__main__':
    process_population()
