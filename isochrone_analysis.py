import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point
import json

def build_graph():
    # Try utf-8 first, if it fails try euc-kr or cp949
    try:
        nodes = pd.read_csv('network/nodes.tsv', sep='\t', encoding='utf-8')
    except UnicodeDecodeError:
        nodes = pd.read_csv('network/nodes.tsv', sep='\t', encoding='cp949')
        
    try:
        links = pd.read_csv('network/links.tsv', sep='\t', encoding='utf-8')
    except UnicodeDecodeError:
        links = pd.read_csv('network/links.tsv', sep='\t', encoding='cp949')
        
    G = nx.DiGraph()
    for _, row in links.iterrows():
        # Check actual columns
        cols = links.columns.tolist()
        if 'timeFT' in cols:
            G.add_edge(row['fromNode'], row['toNode'], weight=row['timeFT'])
            G.add_edge(row['toNode'], row['fromNode'], weight=row['timeTF'])
        elif 'wait_time' in cols and 'travel_time' in cols:
            weight = row['travel_time'] + (row['wait_time'] if pd.notna(row['wait_time']) else 0)
            G.add_edge(row['fromNode'], row['toNode'], weight=weight)
            G.add_edge(row['toNode'], row['fromNode'], weight=weight)
        elif 'time' in cols:
            weight = row['time']
            G.add_edge(row['fromNode'], row['toNode'], weight=weight)
            G.add_edge(row['toNode'], row['fromNode'], weight=weight)
        else:
            weight = row.iloc[3] # Fallback to 4th column (timeFT)
            G.add_edge(row['fromNode'], row['toNode'], weight=weight)
            G.add_edge(row['toNode'], row['fromNode'], weight=weight)
    
    return G, nodes, links

def find_station_id(nodes, station_name):
    # Find column that contains station names
    name_col = 'statnm'
    if name_col in nodes.columns:
        matches = nodes[nodes[name_col].str.contains(station_name, na=False)]
        if not matches.empty:
            return matches.iloc[0]['id']
    return None

def create_isochrone(G, nodes, links, start_id, time_limit=1800):
    # Shortest paths up to time_limit (1800s = 30min, 3600s = 60min)
    lengths = nx.single_source_dijkstra_path_length(G, start_id, cutoff=time_limit, weight='weight')
    reachable_ids = set(lengths.keys())
    
    from shapely.wkt import loads
    from shapely.geometry import Point
    geometries = []
    
    # 도달 가능한 링크 추출 및 LINESTRING 수집
    reachable_links = links[links['fromNode'].isin(reachable_ids) | links['toNode'].isin(reachable_ids)].copy()
    if 'geometry_wkt' in reachable_links.columns:
        valid_links = reachable_links[reachable_links['geometry_wkt'].notna()]
        geometries.extend(valid_links['geometry_wkt'].apply(loads).tolist())
        
    # 만약을 대비해 노드 지오메트리도 수집
    reachable_nodes = nodes[nodes['id'].isin(reachable_ids)].copy()
    if 'geometry_wkt' in reachable_nodes.columns:
        valid_nodes = reachable_nodes[reachable_nodes['geometry_wkt'].notna()]
        geometries.extend(valid_nodes['geometry_wkt'].apply(loads).tolist())
    elif 'x' in reachable_nodes.columns and 'y' in reachable_nodes.columns:
        geometries.extend([Point(xy) for xy in zip(reachable_nodes.x, reachable_nodes.y)])
        
    gdf = gpd.GeoDataFrame(geometry=geometries, crs='epsg:5179')
    
    # 점/선 객체에 모두 150m 두께의 타이트한 버퍼를 씌운 뒤 병합 (물방울 파편화 방지)
    iso_poly = gdf.geometry.buffer(150).unary_union
        
    return gpd.GeoDataFrame(index=[0], geometry=[iso_poly], crs='epsg:5179')

def process_isochrones():
    print("그래프 빌드 중...")
    G, nodes, links = build_graph()
    
    pangyo_id = find_station_id(nodes, '판교')
    dongtan_id = find_station_id(nodes, '동탄')
    
    if pangyo_id is None or dongtan_id is None:
        print("역을 찾을 수 없습니다.")
        return
        
    print(f"판교역 ID: {pangyo_id}, 동탄역 ID: {dongtan_id}")
    
    print("판교 30분/60분 등시간권 생성 중...")
    p_30 = create_isochrone(G, nodes, links, pangyo_id, 1800)
    p_60 = create_isochrone(G, nodes, links, pangyo_id, 3600)
    p_30.to_crs('epsg:4326').to_file('data/pangyo_iso30.geojson', driver='GeoJSON')
    p_60.to_crs('epsg:4326').to_file('data/pangyo_iso60.geojson', driver='GeoJSON')
    
    print("동탄 30분/60분 등시간권 생성 중...")
    d_30 = create_isochrone(G, nodes, links, dongtan_id, 1800)
    d_60 = create_isochrone(G, nodes, links, dongtan_id, 3600)
    d_30.to_crs('epsg:4326').to_file('data/dongtan_iso30.geojson', driver='GeoJSON')
    d_60.to_crs('epsg:4326').to_file('data/dongtan_iso60.geojson', driver='GeoJSON')
    
    print("등시간권 생성 완료!")

if __name__ == '__main__':
    process_isochrones()
