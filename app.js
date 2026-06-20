// Initialize Map
const map = L.map('map').setView([37.40, 127.10], 15); // Default to Pangyo

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

let currentRegion = 'pangyo';
window.statsData = null; // Store stats globally

// Charts Initialization
let landUseChart = new Chart(document.getElementById('landuseChart').getContext('2d'), {
    type: 'bar',
    data: {
        labels: ['주거지역', '상업지역', '공업지역', '녹지지역'],
        datasets: [{
            label: '판교테크노밸리',
            data: [0, 0, 0, 0],
            backgroundColor: '#1a4f8b'
        }, {
            label: '동탄테크노밸리',
            data: [0, 0, 0, 0],
            backgroundColor: '#ca0020'
        }]
    }
});

let demoChart = new Chart(document.getElementById('demographicsChart').getContext('2d'), {
    type: 'bar',
    data: {
        labels: ['총인구 수', '종사자 수'],
        datasets: [{
            label: '판교테크노밸리',
            data: [0, 0],
            backgroundColor: '#1a4f8b'
        }, {
            label: '동탄테크노밸리',
            data: [0, 0],
            backgroundColor: '#ca0020'
        }]
    }
});

let industryChart = new Chart(document.getElementById('industryChart').getContext('2d'), {
    type: 'bar',
    data: {
        labels: ['IT/지식첨단', '상업/서비스', '제조업', '기타'],
        datasets: [{
            label: '판교테크노밸리',
            data: [0, 0, 0, 0],
            backgroundColor: '#1a4f8b'
        }, {
            label: '동탄테크노밸리',
            data: [0, 0, 0, 0],
            backgroundColor: '#ca0020'
        }]
    }
});

// Update population text based on checkbox states
function updatePopulationText() {
    if (!window.statsData) return;
    
    let popKey = 'pop_30';
    let workKey = 'workers_30';
    let timeText = '(30분)';
    const is30 = document.getElementById('iso30').checked;
    const is60 = document.getElementById('iso60').checked;
    
    if (is60) {
        popKey = 'pop_60';
        workKey = 'workers_60';
        timeText = '(60분)';
    } else if (is30) {
        popKey = 'pop_30';
        workKey = 'workers_30';
        timeText = '(30분)';
    }
    
    if (window.statsData.pangyo) {
        document.getElementById('pangyo-label').innerHTML = `판교 도달인구${timeText}: <span id="pangyo-pop">${window.statsData.pangyo[popKey].toLocaleString()}</span> 명 (종사자: <span id="pangyo-work">${window.statsData.pangyo[workKey].toLocaleString()}</span> 명)`;
    }
    if (window.statsData.dongtan) {
        document.getElementById('dongtan-label').innerHTML = `동탄 도달인구${timeText}: <span id="dongtan-pop">${window.statsData.dongtan[popKey].toLocaleString()}</span> 명 (종사자: <span id="dongtan-work">${window.statsData.dongtan[workKey].toLocaleString()}</span> 명)`;
    }
}

function updateCharts() {
    if (!window.statsData) return;
    const pStats = window.statsData.pangyo || {};
    const dStats = window.statsData.dongtan || {};
    
    // Update Land Use Chart
    landUseChart.data.datasets[0].data = pStats.land_use || [0,0,0,0];
    landUseChart.data.datasets[1].data = dStats.land_use || [0,0,0,0];
    landUseChart.update();
    
    // Update LUM and FAR text
    document.getElementById('pangyo-lum').innerText = pStats.lum ? pStats.lum.toFixed(2) : '0';
    document.getElementById('dongtan-lum').innerText = dStats.lum ? dStats.lum.toFixed(2) : '0';
    document.getElementById('pangyo-far').innerText = pStats.far || '0';
    document.getElementById('dongtan-far').innerText = dStats.far || '0';
    
    // Update Road Density text
    document.getElementById('pangyo-road').innerText = pStats.road_density || '0';
    document.getElementById('dongtan-road').innerText = dStats.road_density || '0';
    
    // Update Demographics Chart
    demoChart.data.datasets[0].data = [pStats.pop_total || 0, pStats.workers || 0];
    demoChart.data.datasets[1].data = [dStats.pop_total || 0, dStats.workers || 0];
    demoChart.update();
    
    // Update Industry Chart
    industryChart.data.datasets[0].data = pStats.industry_mix || [0,0,0,0];
    industryChart.data.datasets[1].data = dStats.industry_mix || [0,0,0,0];
    industryChart.update();
    
    updatePopulationText();
}

let iso30Layer = null;
let iso60Layer = null;
let zoningLayer = null;
let boundaryLayer = null;

function getZoningColor(d) {
    return d === '주거지역' ? '#f4a582' :
           d === '상업지역' ? '#ca0020' :
           d === '공업지역' ? '#92c5de' :
           d === '녹지지역' ? '#0571b0' :
                              '#ffffff';
}

function styleZoning(feature) {
    return {
        fillColor: getZoningColor(feature.properties.DQD_AR_GBN),
        weight: 1,
        opacity: 1,
        color: '#666',
        dashArray: '3',
        fillOpacity: 0.6
    };
}

function onEachZoningFeature(feature, layer) {
    if (feature.properties) {
        const usage = feature.properties.DQD_AR_GBN || '정보 없음';
        const far = feature.properties.far || 0;
        const area = feature.properties.gross_area || 0;
        
        let popupContent = `<div style="font-family:'Malgun Gothic', sans-serif;">
                            <h4 style="margin:0 0 5px 0; border-bottom:1px solid #ccc; padding-bottom:3px;">건축물 실제 속성 정보</h4>
                            <b>주용도:</b> ${usage}<br/>
                            <b>용적률:</b> ${parseFloat(far).toFixed(1)}%<br/>
                            <b>연면적:</b> ${parseFloat(area).toLocaleString()} m²
                            </div>`;
        layer.bindPopup(popupContent);
    }
}

// 에러를 화면에 직접 표시하는 함수 (alert 차단 대비)
function displayErrorOnScreen(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = "position:fixed; top:20px; left:50%; transform:translateX(-50%); background:rgba(255,0,0,0.9); color:white; padding:15px 30px; z-index:9999; border-radius:5px; font-weight:bold;";
    errorDiv.innerText = message;
    document.body.appendChild(errorDiv);
}

async function loadIsochrone(region) {
    // 기존 레이어 제거 및 체크박스 초기화
    if (iso30Layer) map.removeLayer(iso30Layer);
    if (iso60Layer) map.removeLayer(iso60Layer);
    if (zoningLayer) map.removeLayer(zoningLayer);
    if (boundaryLayer) map.removeLayer(boundaryLayer);
    
    document.getElementById('iso30').checked = false;
    document.getElementById('iso60').checked = false;
    updatePopulationText();

    // Promise.all을 활용한 병렬 데이터 로드 및 강력한 에러 핸들링
    try {
        const [res30, res60, resZoning, resBoundary] = await Promise.all([
            fetch(`data/${region}_iso30.geojson`).catch(e => e),
            fetch(`data/${region}_iso60.geojson`).catch(e => e),
            fetch(`data/${region}_buildings.geojson`).catch(e => e),
            fetch(`data/${region}_boundary.geojson`).catch(e => e)
        ]);

        if (resBoundary && resBoundary.ok) {
            const dataBoundary = await resBoundary.json();
            boundaryLayer = L.geoJSON(dataBoundary, {
                style: {color: '#000', weight: 4, fillOpacity: 0}
            }).addTo(map);
        }

        if (resZoning && resZoning.ok) {
            const dataZoning = await resZoning.json();
            zoningLayer = L.geoJSON(dataZoning, {
                style: styleZoning,
                onEachFeature: onEachZoningFeature
            });
            const chk = document.getElementById('layerZoning');
            if (!chk || chk.checked) {
                zoningLayer.addTo(map);
            }
        }

        if (res30 && res30.ok) {
            const data30 = await res30.json();
            iso30Layer = L.geoJSON(data30, {
                style: {color: '#ff7800', weight: 2, fillOpacity: 0.2, dashArray: '5, 5'}
            });
        } else {
            console.warn(`30분 데이터가 없습니다: data/${region}_iso30.geojson`);
            iso30Layer = null;
        }

        if (res60 && res60.ok) {
            const data60 = await res60.json();
            iso60Layer = L.geoJSON(data60, {
                style: {color: '#3388ff', weight: 2, fillOpacity: 0.1, dashArray: '5, 5'}
            });
        } else {
            console.warn(`60분 데이터가 없습니다: data/${region}_iso60.geojson`);
            iso60Layer = null;
        }
    } catch (e) {
        console.error('Error loading Isochrones (Promise.all failed):', e);
        displayErrorOnScreen(`[등시간권 로드 오류] ${e.message}`);
        iso30Layer = null;
        iso60Layer = null;
    }
}

document.getElementById('iso30').addEventListener('change', (e) => {
    if (e.target.checked && iso30Layer) iso30Layer.addTo(map);
    else if (iso30Layer) map.removeLayer(iso30Layer);
    updatePopulationText();
});

document.getElementById('iso60').addEventListener('change', (e) => {
    if (e.target.checked && iso60Layer) iso60Layer.addTo(map);
    else if (iso60Layer) map.removeLayer(iso60Layer);
    updatePopulationText();
});

const layerZoningElem = document.getElementById('layerZoning');
if (layerZoningElem) {
    layerZoningElem.addEventListener('change', (e) => {
        if (e.target.checked && zoningLayer) zoningLayer.addTo(map);
        else if (zoningLayer) map.removeLayer(zoningLayer);
    });
}

window.toggleLayer = function(region) {
    currentRegion = region;
    
    // 지도를 하드코딩된 고정 좌표로 줌인
    if (region === 'pangyo') {
        map.setView([37.40, 127.10], 15);
    } else if (region === 'dongtan') {
        map.setView([37.21, 127.09], 15);
    }
    
    // 통계 차트 업데이트 (사이드바 연동) - 항상 두 지역 모두 비교
    updateCharts();
    
    // 등시간권 데이터 백그라운드 로드
    loadIsochrone(region);
};

// Load initial stats and trigger map load
async function loadStats() {
    try {
        const response = await fetch(`data/stats.json`);
        if (!response.ok) {
            throw new Error(`HTTP 상태 코드: ${response.status} (stats.json 파일을 찾을 수 없습니다)`);
        }
        window.statsData = await response.json();
        toggleLayer('pangyo');
    } catch (e) {
        console.error('Error loading stats:', e);
        
        // 텍스트를 '계산 중...'에서 '오류 발생'으로 변경
        document.getElementById('pangyo-pop').innerText = '오류 발생';
        document.getElementById('dongtan-pop').innerText = '오류 발생';
        
        displayErrorOnScreen(`[데이터 로드 치명적 오류] ${e.message}\ndata 폴더 경로 설정이나 파일 누락을 확인하세요.`);
    }
}

// 초기 실행
loadStats();
