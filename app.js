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
    type: 'pie',
    data: {
        labels: ['주거지역', '상업지역', '공업지역', '녹지지역'],
        datasets: [{
            data: [0, 0, 0, 0],
            backgroundColor: ['#f4a582', '#ca0020', '#92c5de', '#0571b0']
        }]
    }
});

let demoChart = new Chart(document.getElementById('demographicsChart').getContext('2d'), {
    type: 'bar',
    data: {
        labels: ['총인구 수', '종사자 수'],
        datasets: [{
            label: '인원수(명)',
            data: [0, 0],
            backgroundColor: '#1a4f8b'
        }]
    }
});

// Update population text based on checkbox states
function updatePopulationText() {
    if (!window.statsData || !window.statsData[currentRegion]) return;
    
    const pangyoPopElem = document.getElementById('pangyo-pop');
    const dongtanPopElem = document.getElementById('dongtan-pop');
    const pangyoLabelElem = document.getElementById('pangyo-label');
    const dongtanLabelElem = document.getElementById('dongtan-label');
    
    // Determine which population to show based on checkboxes
    let popKey = 'pop_30'; // default
    let timeText = '(30분)';
    const is30 = document.getElementById('iso30').checked;
    const is60 = document.getElementById('iso60').checked;
    
    if (is60) {
        popKey = 'pop_60';
        timeText = '(60분)';
    } else if (is30) {
        popKey = 'pop_30';
        timeText = '(30분)';
    } else {
        popKey = 'pop_30'; // 기본값
        timeText = '(30분)';
    }
    
    if (pangyoPopElem && window.statsData.pangyo) {
        const popStr = window.statsData.pangyo[popKey].toLocaleString() + ' 명';
        if (pangyoLabelElem) {
            pangyoLabelElem.innerHTML = `판교 도달인구${timeText}: <span id="pangyo-pop">${popStr}</span>`;
        } else {
            pangyoPopElem.innerText = popStr;
        }
    }
    if (dongtanPopElem && window.statsData.dongtan) {
        const popStr = window.statsData.dongtan[popKey].toLocaleString() + ' 명';
        if (dongtanLabelElem) {
            dongtanLabelElem.innerHTML = `동탄 도달인구${timeText}: <span id="dongtan-pop">${popStr}</span>`;
        } else {
            dongtanPopElem.innerText = popStr;
        }
    }
}

function updateCharts(region) {
    if (!window.statsData || !window.statsData[region]) return;
    const stats = window.statsData[region];
    
    // Update Land Use Chart
    landUseChart.data.datasets[0].data = stats.land_use || [0,0,0,0];
    landUseChart.update();
    
    // Update Demographics Chart
    demoChart.data.datasets[0].data = [stats.pop_total || 0, stats.workers || 0];
    demoChart.update();
    
    updatePopulationText();
}

let iso30Layer = null;
let iso60Layer = null;

async function loadIsochrone(region) {
    // 기존 레이어 제거 및 체크박스 초기화
    if (iso30Layer) map.removeLayer(iso30Layer);
    if (iso60Layer) map.removeLayer(iso60Layer);
    
    document.getElementById('iso30').checked = false;
    document.getElementById('iso60').checked = false;
    updatePopulationText();

    // 30분 등시간권 로드
    try {
        const res30 = await fetch(`./data/${region}_iso30.geojson`);
        if (res30.ok) {
            const data30 = await res30.json();
            iso30Layer = L.geoJSON(data30, {
                style: {color: '#ff7800', weight: 2, fillOpacity: 0.2, dashArray: '5, 5'}
            });
        } else {
            console.warn(`30분 데이터가 없습니다: ${region}_iso30.geojson`);
            iso30Layer = null;
        }
    } catch (e) {
        console.error('Error loading 30 min Isochrone', e);
        iso30Layer = null;
    }

    // 60분 등시간권 로드
    try {
        const res60 = await fetch(`./data/${region}_iso60.geojson`);
        if (res60.ok) {
            const data60 = await res60.json();
            iso60Layer = L.geoJSON(data60, {
                style: {color: '#3388ff', weight: 2, fillOpacity: 0.1, dashArray: '5, 5'}
            });
        } else {
            console.warn(`60분 데이터가 없습니다: ${region}_iso60.geojson`);
            iso60Layer = null;
        }
    } catch (e) {
        console.error('Error loading 60 min Isochrone', e);
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

window.toggleLayer = function(region) {
    currentRegion = region;
    
    // 지도를 하드코딩된 고정 좌표로 줌인
    if (region === 'pangyo') {
        map.setView([37.40, 127.10], 15);
    } else if (region === 'dongtan') {
        map.setView([37.21, 127.09], 15);
    }
    
    // 통계 차트 업데이트 (사이드바 연동)
    updateCharts(region);
    
    // 등시간권 데이터 백그라운드 로드
    loadIsochrone(region);
};

// Load initial stats and trigger map load
async function loadStats() {
    try {
        const response = await fetch(`./data/stats.json`);
        if (response.ok) {
            window.statsData = await response.json();
            toggleLayer('pangyo');
        } else {
            alert(`[오류] stats.json 파일을 불러오지 못했습니다. 상태 코드: ${response.status}\n\ndata 폴더가 깃허브에 제대로 업로드되었는지 확인해주세요.`);
            console.error('Error loading stats', response.status);
        }
    } catch (e) {
        alert(`[네트워크 오류] stats.json 파일을 찾는 데 실패했습니다.\n${e.message}\n\n도메인 끝에 슬래시(/)가 붙어있는지 확인하거나, 깃허브 업로드 상태를 확인하세요.`);
        console.error('Error loading stats', e);
    }
}

// 초기 실행
loadStats();
