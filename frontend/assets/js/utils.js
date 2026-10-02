/**
 * CyberShield 360 - Utility Functions
 */

function showLoading() {
  let overlay = document.getElementById('loading-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="text-center"><div class="spinner-cyber mx-auto mb-3"></div><p class="text-secondary">Analyzing threat...</p></div>';
    document.body.appendChild(overlay);
  }
  overlay.style.display = 'flex';
}

function goBack() {
  if (window.history.length > 1 && document.referrer && document.referrer.startsWith(window.location.origin)) {
    window.history.back();
  } else {
    window.location.href = '/pages/dashboard.html';
  }
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.style.display = 'none';
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function getThreatBadge(level) {
  const icons = { safe: 'fa-check-circle', warning: 'fa-exclamation-triangle', danger: 'fa-skull-crossbones' };
  const icon = icons[level] || 'fa-question-circle';
  return `<span class="threat-badge ${level}"><i class="fas ${icon}"></i> ${(level || 'unknown').toUpperCase()}</span>`;
}

function getThreatColor(level) {
  return { safe: '#00C853', warning: '#FFC107', danger: '#E63946' }[level] || '#C9D1D9';
}

function renderScanResult(containerId, result) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const level = result.threat_level || 'unknown';
  const confidence = result.confidence || 0;
  const color = getThreatColor(level);

  let html = `
    <div class="scan-result" data-aos="fade-up">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h4><i class="fas fa-shield-alt me-2"></i>Scan Result</h4>
        ${getThreatBadge(level)}
      </div>
      <div class="row g-4">
        <div class="col-md-6">
          <div class="mb-3">
            <label class="text-secondary small">Confidence Score</label>
            <div class="d-flex align-items-center gap-3">
              <div class="confidence-bar flex-grow-1">
                <div class="confidence-fill" style="width:${confidence * 100}%; background:${color}"></div>
              </div>
              <strong style="color:${color}">${(confidence * 100).toFixed(1)}%</strong>
            </div>
          </div>
          <div class="mb-3">
            <label class="text-secondary small">Threat Type</label>
            <p class="mb-0">${result.threat_type || 'None'}</p>
          </div>
          ${result.model ? `<div class="mb-3"><label class="text-secondary small">Model</label><p class="mb-0 small">${result.model}</p></div>` : ''}
        </div>
        <div class="col-md-6">
          <div class="mb-3">
            <label class="text-secondary small">Analysis</label>
            <ul class="mb-0 ps-3">
              ${(result.reasons || []).map(r => `<li class="small">${r}</li>`).join('')}
            </ul>
          </div>
        </div>
      </div>
      <div class="mt-3 p-3 rounded" style="background:rgba(41,182,246,0.1); border-left:3px solid var(--info)">
        <strong><i class="fas fa-lightbulb me-2"></i>Recommendation</strong>
        <p class="mb-0 mt-1 small">${result.recommendation || 'Stay vigilant'}</p>
      </div>
      <div class="mt-3 d-flex gap-2">
        <button class="btn-cyber btn-sm" onclick="downloadReport('${result.report_id || ''}')"><i class="fas fa-download me-1"></i>Download PDF</button>
      </div>
    </div>`;

  container.innerHTML = html;
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


function animateCounter(element, target, duration = 2000) {
  const start = 0;
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.floor(start + (target - start) * eased).toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = Array.from({ length: 80 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5,
    size: Math.random() * 2 + 1
  }));

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((p, i) => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(193,18,31,0.4)';
      ctx.fill();

      particles.slice(i + 1).forEach(p2 => {
        const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(193,18,31,${0.15 * (1 - dist / 120)})`;
          ctx.stroke();
        }
      });
    });
    requestAnimationFrame(draw);
  }
  draw();

  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });
}

function setupFileUpload(zoneId, inputId, onFile) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  if (!zone || !input) return;

  const triggerFile = file => {
    if (!file) return;
    if (typeof FileList !== 'undefined' && file instanceof File) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
    }
    onFile(file);
  };

  zone.addEventListener('click', e => {
    if (e.target === input) return;
    input.click();
  });
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    if (e.dataTransfer?.files?.length) {
      triggerFile(e.dataTransfer.files[0]);
    }
  });
  input.addEventListener('change', () => {
    if (input.files?.length) {
      triggerFile(input.files[0]);
    }
  });
}

function previewImage(file, previewId) {
  const preview = document.getElementById(previewId);
  if (!preview || !file) return;
  const reader = new FileReader();
  reader.onload = e => {
    preview.innerHTML = `<img src="${e.target.result}" class="img-fluid rounded" style="max-height:300px" alt="Preview">`;
    preview.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

function toggleSidebar() {
  document.querySelector('.sidebar')?.classList.toggle('open');
}

function getCategoryIcon(category) {
  const icons = {
    'Ransomware': 'fa-lock', 'Scam': 'fa-mask', 'Government': 'fa-landmark',
    'Malware': 'fa-bug', 'Data Breach': 'fa-database', 'Cyber Attack': 'fa-crosshairs'
  };
  return icons[category] || 'fa-newspaper';
}

async function downloadReport(reportId) {
  if (!reportId) return;
  showLoading();
  const token = localStorage.getItem('access_token');
  const url = `${API_BASE}/reports/${encodeURIComponent(reportId)}/pdf`;
  try {
    const res = await fetch(url, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    if (!res.ok) throw new Error('Could not generate PDF report');
    if (!res.headers.get('content-type')?.includes('application/pdf')) {
      throw new Error('The server did not return a PDF file');
    }
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `cybershield_threat_report_${reportId.slice(0, 8)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
  } catch (e) {
    console.error('PDF download error:', e);
    Swal.fire({ icon: 'error', title: 'Download Failed', text: 'Unable to download PDF. Please try again.', background: '#141A26', color: '#fff' });
  } finally {
    hideLoading();
  }
}
