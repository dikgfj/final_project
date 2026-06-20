import osmnx as ox
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import requests
import os
import time

VWORLD_API_KEY = "35B4E604-0390-3CC4-B937-9D67255B61DE"

def vworld_geocode(address, addr_type="parcel"):
    """
    VWorld 오픈 API를 사용하여 주소를 좌표로 변환
    addr_type: 'parcel' (지번주소) 또는 'road' (도로명주소)
    """
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "epsg:4326",
        "address": address,
        "refine": "true",
        "simple": "false",
        "format": "json",
        "type": addr_type,
        "key": VWORLD_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['response']['status'] == 'OK':
                result = data['response']['result']['point']
                return (float(result['y']), float(result['x'])) # lat, lon
    except Exception as e:
        print(f"API Error for {address}: {e}")
    return None

def clean_address(addr):
    if not isinstance(addr, str):
        return ""
    # 건축물대장에 포함된 가상의 '동탄구' 등 불필요한 단어 제거 (정확한 지오코딩을 위함)
    addr = addr.replace("동탄구 ", "")
    addr = addr.replace("번지", "")
    # "경기도 성남시 삼평동 621" 형태로 정제
    addr = addr.replace("분당구 ", "") # 분당구 삼평동 -> 삼평동 (때론 구가 방해됨, 하지만 VWorld는 구를 넣는 것이 좋을 수도 있음. 일단 동탄구는 가짜행정구역이므로 제거 필수)
    return addr.strip()

def main():
    print("1. VWorld API를 이용한 대용량 주소 지오코딩 시작...")
    df = pd.read_csv('건축물대장.csv', encoding='utf-8-sig')
    
    # 캐싱용 딕셔너리
    geocode_cache = {}
    
    points = []
    valid_indices = []
    
    for idx, row in df.iterrows():
        # 우선 지번 주소(대지위치) 시도
        jibun_addr = clean_address(row['대지위치'])
        
        # 캐시 확인
        if jibun_addr in geocode_cache:
            coords = geocode_cache[jibun_addr]
        else:
            coords = vworld_geocode(jibun_addr, "parcel")
            # 실패 시 도로명 주소(도로명대지위치)로 재시도
            if not coords and pd.notna(row['도로명대지위치']):
                road_addr = clean_address(row['도로명대지위치'])
                coords = vworld_geocode(road_addr, "road")
                
            geocode_cache[jibun_addr] = coords
            
        if coords:
            points.append(Point(coords[1], coords[0])) # lon, lat
            valid_indices.append(idx)
        else:
            print(f"지오코딩 실패: {jibun_addr} / {row['도로명대지위치']}")

    df_valid = df.loc[valid_indices].copy()
    gdf_points = gpd.GeoDataFrame(df_valid, geometry=points, crs="EPSG:4326")
    print(f"지오코딩 성공률: {len(gdf_points)} / {len(df)}")

    print("2. OSM 건축물 폴리곤 (실제 형태) 다운로드 중...")
    try:
        p_bound = gpd.read_file('data/pangyo_boundary.geojson')
        d_bound = gpd.read_file('data/dongtan_boundary.geojson')
    except:
        print("구역계 파일 로드 실패. 폴더를 확인하세요.")
        return

    p_poly = p_bound.geometry.iloc[0]
    d_poly = d_bound.geometry.iloc[0]
    
    tags = {'building': True}
    print(" -> 판교 건축물 폴리곤 다운로드")
    try:
        p_buildings = ox.features_from_polygon(p_poly, tags)
        p_buildings = p_buildings[p_buildings.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    except Exception as e:
        print(f"판교 건물 다운로드 실패: {e}")
        p_buildings = gpd.GeoDataFrame(crs="EPSG:4326", geometry=[])
        
    print(" -> 동탄 건축물 폴리곤 다운로드")
    try:
        d_buildings = ox.features_from_polygon(d_poly, tags)
        d_buildings = d_buildings[d_buildings.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    except Exception as e:
        print(f"동탄 건물 다운로드 실패: {e}")
        d_buildings = gpd.GeoDataFrame(crs="EPSG:4326", geometry=[])

    print("3. 공간 조인 (Spatial Join) 수행...")
    
    def process_and_save(buildings_gdf, points_gdf, filename):
        if not buildings_gdf.empty and not points_gdf.empty:
            joined = gpd.sjoin(buildings_gdf, points_gdf, how='left', predicate='intersects')
            # 중복 제거 (여러 건물이 한 폴리곤에 들어갈 경우 첫 번째 데이터만 사용)
            if 'osmid' in joined.columns:
                joined = joined.drop_duplicates(subset=['osmid'])
            else:
                joined = joined[~joined.index.duplicated(keep='first')]
                
            final_gdf = joined[['geometry', '주용도코드명', '용적률(%)', '연면적(㎡)']].copy()
            final_gdf.rename(columns={'주용도코드명': 'DQD_AR_GBN', '용적률(%)': 'far', '연면적(㎡)': 'gross_area'}, inplace=True)
            
            final_gdf['DQD_AR_GBN'] = final_gdf['DQD_AR_GBN'].fillna('기타')
            final_gdf['far'] = final_gdf['far'].fillna(0)
            final_gdf['gross_area'] = final_gdf['gross_area'].fillna(0)
            
            os.makedirs('data', exist_ok=True)
            final_gdf.to_file(f'data/{filename}', driver='GeoJSON')
            print(f" -> 성공: data/{filename} 생성 완료 (총 {len(final_gdf)}개 폴리곤)")
        else:
            print(f" -> {filename} 생성 실패 (건물 데이터가 없거나 교차점 없음)")

    process_and_save(p_buildings, gdf_points, 'pangyo_buildings.geojson')
    process_and_save(d_buildings, gdf_points, 'dongtan_buildings.geojson')

    print("모든 VWorld 전처리 파이프라인이 완료되었습니다!")

if __name__ == '__main__':
    main()
