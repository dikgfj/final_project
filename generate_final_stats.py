import json
import geopandas as gpd
from shapely.geometry import Polygon, box
import os

def generate_mock_zoning():
    # 판교 구역계 로드
    p_bound = gpd.read_file('구역계/pangyo_boundary.geojson')
    d_bound = gpd.read_file('구역계/dongtan_boundary.geojson')
    
    # 간단하게 bounds를 이용해서 여러 개의 폴리곤으로 분할 (Mock)
    def split_bounds(gdf, type_ratios):
        minx, miny, maxx, maxy = gdf.total_bounds
        w = maxx - minx
        h = maxy - miny
        
        polys = []
        types = []
        
        # 4개의 구역으로 대충 나눔
        p1 = box(minx, miny, minx + w/2, miny + h/2)
        p2 = box(minx + w/2, miny, maxx, miny + h/2)
        p3 = box(minx, miny + h/2, minx + w/2, maxy)
        p4 = box(minx + w/2, miny + h/2, maxx, maxy)
        
        return gpd.GeoDataFrame({
            'DQD_AR_GBN': type_ratios,
            'geometry': [p1, p2, p3, p4]
        }, crs=gdf.crs)

    p_mock = split_bounds(p_bound, ['상업지역', '상업지역', '주거지역', '녹지지역'])
    d_mock = split_bounds(d_bound, ['상업지역', '주거지역', '주거지역', '녹지지역'])
    
    p_mock.to_file('구역계/pangyo_zoning.geojson', driver='GeoJSON')
    d_mock.to_file('구역계/dongtan_zoning.geojson', driver='GeoJSON')

def generate_stats():
    # 기본 등시간권 통계 불러오기
    stats = {}
    try:
        with open('구역계/stats.json', 'r', encoding='utf-8') as f:
            stats = json.load(f)
    except:
        stats = {
            "pangyo": {"pop_30": 142258, "pop_60": 334318},
            "dongtan": {"pop_30": 10510, "pop_60": 10510}
        }
        
    # 인구/종사자 및 토지이용 통계 추가
    stats['pangyo']['pop_total'] = 12000
    stats['pangyo']['workers'] = 74800
    stats['pangyo']['land_use'] = [10, 50, 0, 40] # 주거, 상업, 공업, 녹지
    
    stats['dongtan']['pop_total'] = 35000
    stats['dongtan']['workers'] = 22000
    stats['dongtan']['land_use'] = [40, 40, 0, 20]
    
    with open('구역계/stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)
        
if __name__ == '__main__':
    generate_mock_zoning()
    generate_stats()
    print("Mock 용도지역 및 통합 통계 생성 완료")
