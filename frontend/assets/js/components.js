/**
 * CyberShield 360 - Reusable UI Components
 */

function renderNavbar(isDashboard = false) {
  const user = getUser();
  const admin = user && user.role === 'admin';
  const homeHref = admin ? '/pages/admin/dashboard.html' : (isDashboard ? '/pages/dashboard.html' : '/');
  return `
  <nav class="navbar-cyber">
    <div class="d-flex align-items-center gap-2">
      <button class="btn btn-outline-cyber btn-sm px-2 py-1 me-2" onclick="goBack()" title="Go Back"><i class="fas fa-arrow-left me-1"></i>Back</button>
      <a href="${homeHref}" class="navbar-brand">
      <div class="shield-icon"><i class="fas fa-shield-alt"></i></div>
      <div>
        <span>CYBERSHIELD 360</span>
        <div class="tagline" style="font-size:0.6rem;letter-spacing:2px">Protect • Detect • Educate</div>
      </div>
    </a>
    ${isDashboard ? `
      <button class="btn btn-link text-white d-lg-none" onclick="toggleSidebar()"><i class="fas fa-bars fa-lg"></i></button>
    ` : `
      <ul class="nav-links d-none d-lg-flex">
        <li><a href="/#features">Features</a></li>
        <li><a href="/#about">About</a></li>
        <li><a href="/pages/news.html">News</a></li>
        <li><a href="/pages/learning.html">Learn</a></li>
      </ul>
    `}
    <div class="d-flex align-items-center gap-3">
      ${user ? `
        ${admin ? '' : `<a href="/pages/notifications.html" class="text-secondary position-relative">
          <i class="fas fa-bell fa-lg"></i>
          <span class="notif-dot" id="notif-badge" style="display:none"></span>
        </a>`}
        <div class="dropdown">
          <button class="btn btn-link text-white dropdown-toggle" data-bs-toggle="dropdown">
            <i class="fas fa-user-circle fa-lg"></i> ${user.name}
          </button>
          <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end">
            ${admin
              ? '<li><a class="dropdown-item" href="/pages/admin/dashboard.html"><i class="fas fa-graduation-cap me-2"></i>Education Admin</a></li>'
              : '<li><a class="dropdown-item" href="/pages/profile.html"><i class="fas fa-user me-2"></i>Profile</a></li><li><a class="dropdown-item" href="/pages/dashboard.html"><i class="fas fa-chart-line me-2"></i>Dashboard</a></li>'}
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item text-danger" href="#" onclick="logout()"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
          </ul>
        </div>
      ` : `
        <a href="/pages/login.html" class="btn-outline-cyber btn-sm">Login</a>
        <a href="/pages/register.html" class="btn-cyber btn-sm">Get Started</a>
      `}
    </div>
  </nav>`;
}

function renderSidebar(activePage = '') {
  const menuItems = isAdmin() ? [
    { section: 'Administration' },
    { href: '/pages/admin/dashboard.html', icon: 'fa-chart-line', label: 'User Progress', id: 'admin-dashboard' },
    { section: 'Education' },
    { href: '/pages/news.html', icon: 'fa-newspaper', label: 'Cyber News', id: 'news' },
    { href: '/pages/cyber-law.html', icon: 'fa-gavel', label: 'Cyber Law', id: 'cyber-law' },
    { href: '/pages/learning.html', icon: 'fa-graduation-cap', label: 'Learning Center', id: 'learning' },
    { href: '/pages/quiz.html', icon: 'fa-question-circle', label: 'Quiz', id: 'quiz' },
  ] : [
    { section: 'Main' },
    { href: '/pages/dashboard.html', icon: 'fa-chart-line', label: 'Dashboard', id: 'dashboard' },
    { href: '/pages/profile.html', icon: 'fa-user', label: 'Profile', id: 'profile' },
    { section: 'Scanners' },
    { href: '/pages/image-scanner.html', icon: 'fa-image', label: 'Image Scanner', id: 'image-scanner' },
    { href: '/pages/qr-scanner.html', icon: 'fa-qrcode', label: 'QR Scanner', id: 'qr-scanner' },
    { href: '/pages/url-scanner.html', icon: 'fa-link', label: 'URL Checker', id: 'url-scanner' },
    { href: '/pages/email-scanner.html', icon: 'fa-envelope', label: 'Email Scanner', id: 'email-scanner' },
    { href: '/pages/sms-scanner.html', icon: 'fa-sms', label: 'SMS Scanner', id: 'sms-scanner' },
    { href: '/pages/ocr-scanner.html', icon: 'fa-file-alt', label: 'OCR Scanner', id: 'ocr-scanner' },
    { href: '/pages/fake-image.html', icon: 'fa-eye-slash', label: 'Fake Image Detection', id: 'fake-image' },
    { section: 'Education' },
    { href: '/pages/news.html', icon: 'fa-newspaper', label: 'Cyber News', id: 'news' },
    { href: '/pages/cyber-law.html', icon: 'fa-gavel', label: 'Cyber Law', id: 'cyber-law' },
    { href: '/pages/learning.html', icon: 'fa-graduation-cap', label: 'Learning Center', id: 'learning' },
    { href: '/pages/quiz.html', icon: 'fa-question-circle', label: 'Quiz', id: 'quiz' },
    { section: 'Reports' },
    { href: '/pages/reports.html', icon: 'fa-file-pdf', label: 'Threat Reports', id: 'reports' },
    { href: '/pages/notifications.html', icon: 'fa-bell', label: 'Notifications', id: 'notifications' },
  ];

  let html = '<aside class="sidebar"><ul class="sidebar-menu">';
  menuItems.forEach(item => {
    if (item.section) {
      html += `<li class="sidebar-section">${item.section}</li>`;
    } else {
      const active = activePage === item.id ? 'active' : '';
      html += `<li><a href="${item.href}" class="${active}"><i class="fas ${item.icon}"></i> ${item.label}</a></li>`;
    }
  });
  html += '</ul></aside>';
  return html;
}

function renderFooter() {
  return `
  <footer class="footer-cyber">
    <div class="container">
      <div class="row g-4">
        <div class="col-lg-4">
          <div class="footer-brand mb-3"><i class="fas fa-shield-alt text-danger me-2"></i>CYBERSHIELD 360</div>
          <p class="text-secondary small">AI-powered cybersecurity awareness and threat detection platform. Protect • Detect • Educate</p>
        </div>
        <div class="col-lg-2 col-6">
          <h6 class="mb-3">Scanners</h6>
          <ul class="list-unstyled small">
            <li class="mb-2"><a href="/pages/url-scanner.html" class="text-secondary">URL Checker</a></li>
            <li class="mb-2"><a href="/pages/email-scanner.html" class="text-secondary">Email Scanner</a></li>
            <li class="mb-2"><a href="/pages/image-scanner.html" class="text-secondary">Image Scanner</a></li>
            <li class="mb-2"><a href="/pages/qr-scanner.html" class="text-secondary">QR Scanner</a></li>
          </ul>
        </div>
        <div class="col-lg-2 col-6">
          <h6 class="mb-3">Learn</h6>
          <ul class="list-unstyled small">
            <li class="mb-2"><a href="/pages/learning.html" class="text-secondary">Learning Center</a></li>
            <li class="mb-2"><a href="/pages/quiz.html" class="text-secondary">Quiz</a></li>
            <li class="mb-2"><a href="/pages/cyber-law.html" class="text-secondary">Cyber Law</a></li>
            <li class="mb-2"><a href="/pages/news.html" class="text-secondary">Cyber News</a></li>
          </ul>
        </div>
        <div class="col-lg-2 col-6">
          <h6 class="mb-3">Account</h6>
          <ul class="list-unstyled small">
            <li class="mb-2"><a href="/pages/login.html" class="text-secondary">Login</a></li>
            <li class="mb-2"><a href="/pages/register.html" class="text-secondary">Register</a></li>
            <li class="mb-2"><a href="/pages/dashboard.html" class="text-secondary">Dashboard</a></li>
          </ul>
        </div>
        <div class="col-lg-2 col-6">
          <h6 class="mb-3">Connect</h6>
          <div class="d-flex gap-3">
            <a href="#" class="text-secondary"><i class="fab fa-twitter fa-lg"></i></a>
            <a href="#" class="text-secondary"><i class="fab fa-linkedin fa-lg"></i></a>
            <a href="#" class="text-secondary"><i class="fab fa-github fa-lg"></i></a>
          </div>
        </div>
      </div>
      <hr class="border-secondary my-4" style="opacity:0.2">
      <p class="text-center text-secondary small mb-0">&copy; 2026 CyberShield 360. All rights reserved.</p>
    </div>
  </footer>`;
}

function renderDashboardLayout(activePage, content) {
  document.body.innerHTML = `
    ${renderNavbar(true)}
    ${renderSidebar(activePage)}
    <main class="main-content">${content}</main>
  `;
}

async function loadNotificationBadge() {
  if (!isLoggedIn()) return;
  const result = await apiGet(ENDPOINTS.NOTIFICATIONS + '?page=1');
  if (result.success && result.data.unread_count > 0) {
    const badge = document.getElementById('notif-badge');
    if (badge) badge.style.display = 'block';
  }
}

function initPage() {
  if (window.AOS && typeof window.AOS.init === 'function') {
    window.AOS.init({ duration: 800, once: true });
  }
  loadNotificationBadge();
}
