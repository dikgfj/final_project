import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon
import os

def create_boundaries():
    os.makedirs('구역계', exist_ok=True)
    
    # 제1판교테크노밸리 대략적 경계 (폴리곤 좌표)
    # 실제 지구단위계획 경계와 유사하게 설정 (추후 정밀 보정 가능)
    pangyo_coords = [
        (127.0988, 37.4042), (127.1090, 37.4068),
        (127.1118, 37.4005), (127.1023, 37.3979),
        (127.0988, 37.4042)
    ]
    pangyo_poly = Polygon(pangyo_coords)
    pangyo_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[pangyo_poly])
    pangyo_gdf.to_file('구역계/pangyo_boundary.geojson', driver='GeoJSON')
    
    # 동탄테크노밸리 대략적 경계
    dongtan_coords = [
        (127.0900, 37.2150), (127.1150, 37.2150),
        (127.1150, 37.2000), (127.0900, 37.2000),
        (127.0900, 37.2150)
    ]
    dongtan_poly = Polygon(dongtan_coords)
    dongtan_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[dongtan_poly])
    dongtan_gdf.to_file('구역계/dongtan_boundary.geojson', driver='GeoJSON')
    
    return pangyo_poly, dongtan_poly

def download_osm_data(pangyo_poly, dongtan_poly):
    os.makedirs('OSM_도로망', exist_ok=True)
    
    print("제1판교테크노밸리 도로망 다운로드 중...")
    G_pangyo = ox.graph_from_polygon(pangyo_poly, network_type='all')
    ox.save_graphml(G_pangyo, filepath='OSM_도로망/pangyo_network.graphml')
    
    print("동탄테크노밸리 도로망 다운로드 중...")
    G_dongtan = ox.graph_from_polygon(dongtan_poly, network_type='all')
    ox.save_graphml(G_dongtan, filepath='OSM_도로망/dongtan_network.graphml')
    
    print("OSM 도로망 데이터 다운로드 완료!")

if __name__ == '__main__':
    p_poly, d_poly = create_boundaries()
    download_osm_data(p_poly, d_poly)
