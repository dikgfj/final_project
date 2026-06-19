import geopandas as gpd
import os
import warnings
warnings.filterwarnings("ignore")

def process_zoning():
    print("용도지역 데이터 로드 중...")
    pangyo = gpd.read_file('구역계/pangyo_boundary.geojson')
    dongtan = gpd.read_file('구역계/dongtan_boundary.geojson')
    
    zoning_path = '용도지역/LSMD_CONT_UD210_41_202606.shp'
    zoning = gpd.read_file(zoning_path, encoding='euc-kr')
    
    print(f"원본 CRS: {zoning.crs}")
    
    p_bounds = pangyo.to_crs(zoning.crs)
    p_zoning = gpd.clip(zoning, p_bounds)
    
    # 만약 5186에서 비어있다면, 5174(Bessel)일 확률이 높음
    if p_zoning.empty:
        print("EPSG:5186 매칭 실패, EPSG:5174로 시도합니다...")
        zoning.set_crs('epsg:5174', inplace=True, allow_override=True)
        p_bounds = pangyo.to_crs('epsg:5174')
        p_zoning = gpd.clip(zoning, p_bounds)
        d_bounds = dongtan.to_crs('epsg:5174')
    else:
        d_bounds = dongtan.to_crs(zoning.crs)
        
    d_zoning = gpd.clip(zoning, d_bounds)
    
    print("판교 데이터 추출 갯수:", len(p_zoning))
    print("동탄 데이터 추출 갯수:", len(d_zoning))
    
    if not p_zoning.empty:
        p_zoning.to_crs('epsg:4326').to_file('구역계/pangyo_zoning.geojson', driver='GeoJSON')
    if not d_zoning.empty:
        d_zoning.to_crs('epsg:4326').to_file('구역계/dongtan_zoning.geojson', driver='GeoJSON')

if __name__ == '__main__':
    process_zoning()
    print("전처리 완료!")
