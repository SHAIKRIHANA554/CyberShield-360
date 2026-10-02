/**
 * CyberShield 360 - Chart.js Helpers
 */

let chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      labels: { color: '#C9D1D9', font: { family: 'Inter' } }
    }
  },
  scales: {
    x: { ticks: { color: '#C9D1D9' }, grid: { color: 'rgba(255,255,255,0.05)' } },
    y: { ticks: { color: '#C9D1D9' }, grid: { color: 'rgba(255,255,255,0.05)' } }
  }
};

function createThreatPieChart(canvasId, distribution) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = Object.keys(distribution);
  const data = Object.values(distribution);
  const colors = labels.map(l => getThreatColor(l));

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
      datasets: [{
        data,
        backgroundColor: colors,
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: {
      ...chartDefaults,
      cutout: '65%',
      plugins: {
        ...chartDefaults.plugins,
        legend: { position: 'bottom', labels: { color: '#C9D1D9', padding: 16 } }
      }
    }
  });
}

function createScanBarChart(canvasId, dailyData) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dailyData.map(d => d.date.slice(5)),
      datasets: [{
        label: 'Scans',
        data: dailyData.map(d => d.count),
        backgroundColor: 'rgba(193,18,31,0.7)',
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      ...chartDefaults,
      plugins: { ...chartDefaults.plugins, legend: { display: false } }
    }
  });
}

function createThreatLineChart(canvasId, dailyData) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: dailyData.map(d => d.date.slice(5)),
      datasets: [{
        label: 'Daily Scans',
        data: dailyData.map(d => d.count),
        borderColor: '#FF4D4D',
        backgroundColor: 'rgba(255,77,77,0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#C1121F',
        pointRadius: 4
      }]
    },
    options: chartDefaults
  });
}

function createTypeBarChart(canvasId, typeDist) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = Object.keys(typeDist);
  const data = Object.values(typeDist);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Threats by Type',
        data,
        backgroundColor: ['#C1121F', '#FF4D4D', '#FFC107', '#29B6F6', '#00C853', '#E63946'],
        borderRadius: 6
      }]
    },
    options: {
      ...chartDefaults,
      indexAxis: 'y',
      plugins: { ...chartDefaults.plugins, legend: { display: false } }
    }
  });
}

function createSecurityGauge(canvasId, score) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const color = score >= 80 ? '#00C853' : score >= 50 ? '#FFC107' : '#E63946';

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [color, 'rgba(255,255,255,0.05)'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      cutout: '75%',
      plugins: { legend: { display: false }, tooltip: { enabled: false } }
    }
  });
}
