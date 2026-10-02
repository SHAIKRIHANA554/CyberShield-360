/**
 * CyberShield 360 - API Configuration
 */
const localFrontendHosts = ['localhost:5173', '127.0.0.1:5173'];
const API_BASE = localFrontendHosts.includes(window.location.host)
  ? 'http://127.0.0.1:5000/api'
  : `${window.location.origin}/api`;

const ENDPOINTS = {
  // Auth
  REGISTER: '/auth/register',
  LOGIN: '/auth/login',
  ADMIN_LOGIN: '/auth/admin/login',
  FORGOT_PASSWORD: '/auth/forgot-password',
  VERIFY_OTP: '/auth/verify-otp',
  RESET_PASSWORD: '/auth/reset-password',
  PROFILE: '/auth/profile',
  CHANGE_PASSWORD: '/auth/change-password',
  REFRESH: '/auth/refresh',

  // Dashboard
  STATS: '/dashboard/stats',
  GLOBAL_STATS: '/dashboard/global-stats',
  ACTIVITIES: '/dashboard/activities',

  // Scanners
  SCAN_URL: '/scanner/url',
  SCAN_EMAIL: '/scanner/email',
  SCAN_SMS: '/scanner/sms',
  SCAN_IMAGE: '/scanner/image',
  SCAN_QR: '/scanner/qr',
  SCAN_OCR: '/scanner/ocr',
  SCAN_FAKE_IMAGE: '/scanner/fake-image',

  // Content
  NEWS: '/news',
  CYBER_LAW: '/cyber-law',
  LEARNING: '/learning',
  QUIZ: '/quiz',
  QUIZ_SUBMIT: '/quiz',
  LEADERBOARD: '/quiz/leaderboard',

  // Notifications & Reports
  NOTIFICATIONS: '/notifications',
  REPORTS: '/reports',
  REPORT_PDF: '/reports/generate/pdf',
  REPORT_EXCEL: '/reports/generate/excel',

  // Admin
  ADMIN_DASHBOARD: '/admin/dashboard',
  ADMIN_USERS: '/admin/users',
  ADMIN_NEWS: '/admin/news',
  ADMIN_LEARNING: '/admin/learning',
  ADMIN_QUIZ: '/admin/quiz',
  ADMIN_NOTIFICATIONS: '/admin/notifications',

  HEALTH: '/health'
};
