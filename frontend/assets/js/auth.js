/**
 * CyberShield 360 - Authentication Module
 */

function saveAuth(data) {
  if (data.access_token) localStorage.setItem('access_token', data.access_token);
  if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
  if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
}

function getUser() {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}

function isLoggedIn() {
  return !!localStorage.getItem('access_token');
}

function isAdmin() {
  const user = getUser();
  return user && user.role === 'admin';
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = '/pages/login.html';
}

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = '/pages/login.html';
    return false;
  }
  return true;
}

function requireAdmin() {
  if (!requireAuth()) return false;
  if (!isAdmin()) {
    Swal.fire({ icon: 'error', title: 'Access Denied', text: 'Admin privileges required.', background: '#141A26', color: '#fff' });
    window.location.href = '/pages/dashboard.html';
    return false;
  }
  return true;
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  showLoading();
  const result = await apiPost(ENDPOINTS.LOGIN, { email, password });
  hideLoading();

  if (result.success) {
    saveAuth(result.data);
    Swal.fire({ icon: 'success', title: 'Welcome!', text: result.message, timer: 1500, showConfirmButton: false, background: '#141A26', color: '#fff' });
    setTimeout(() => window.location.href = '/pages/dashboard.html', 1500);
  } else {
    Swal.fire({ icon: 'error', title: 'Login Failed', text: result.message, background: '#141A26', color: '#fff' });
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const confirm = document.getElementById('confirm_password').value;

  if (password !== confirm) {
    Swal.fire({ icon: 'error', title: 'Error', text: 'Passwords do not match', background: '#141A26', color: '#fff' });
    return;
  }

  showLoading();
  const result = await apiPost(ENDPOINTS.REGISTER, { name, email, password });
  hideLoading();

  if (result.success) {
    saveAuth(result.data);
    Swal.fire({ icon: 'success', title: 'Account Created!', text: 'Welcome to CyberShield 360', timer: 2000, showConfirmButton: false, background: '#141A26', color: '#fff' });
    setTimeout(() => window.location.href = '/pages/dashboard.html', 2000);
  } else {
    Swal.fire({ icon: 'error', title: 'Registration Failed', text: result.message, background: '#141A26', color: '#fff' });
  }
}

async function handleForgotPassword(e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  showLoading();
  const result = await apiPost(ENDPOINTS.FORGOT_PASSWORD, { email });
  hideLoading();

  if (result.success) {
    sessionStorage.setItem('reset_email', email);
    Swal.fire({ icon: 'success', title: 'OTP Sent', text: 'Check your email for the OTP', background: '#141A26', color: '#fff' });
    setTimeout(() => window.location.href = '/pages/otp.html', 1500);
  } else {
    Swal.fire({ icon: 'error', title: 'Error', text: result.message, background: '#141A26', color: '#fff' });
  }
}

async function handleVerifyOtp(e) {
  e.preventDefault();
  const email = sessionStorage.getItem('reset_email');
  const otp = document.getElementById('otp').value;
  const password = document.getElementById('password').value;
  const confirm = document.getElementById('confirm_password').value;

  if (password !== confirm) {
    Swal.fire({ icon: 'error', title: 'Error', text: 'Passwords do not match', background: '#141A26', color: '#fff' });
    return;
  }

  showLoading();
  const verifyResult = await apiPost(ENDPOINTS.VERIFY_OTP, { email, otp });
  if (!verifyResult.success) {
    hideLoading();
    Swal.fire({ icon: 'error', title: 'Invalid OTP', text: verifyResult.message, background: '#141A26', color: '#fff' });
    return;
  }

  const resetResult = await apiPost(ENDPOINTS.RESET_PASSWORD, { email, otp, password });
  hideLoading();

  if (resetResult.success) {
    sessionStorage.removeItem('reset_email');
    Swal.fire({ icon: 'success', title: 'Password Reset!', text: 'You can now login with your new password', background: '#141A26', color: '#fff' });
    setTimeout(() => window.location.href = '/pages/login.html', 2000);
  } else {
    Swal.fire({ icon: 'error', title: 'Error', text: resetResult.message, background: '#141A26', color: '#fff' });
  }
}

async function handleAdminLogin(e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  showLoading();
  const result = await apiPost(ENDPOINTS.ADMIN_LOGIN, { email, password });
  hideLoading();

  if (result.success) {
    saveAuth(result.data);
    Swal.fire({ icon: 'success', title: 'Admin Access Granted', timer: 1500, showConfirmButton: false, background: '#141A26', color: '#fff' });
    setTimeout(() => window.location.href = '/pages/admin/dashboard.html', 1500);
  } else {
    Swal.fire({ icon: 'error', title: 'Access Denied', text: result.message, background: '#141A26', color: '#fff' });
  }
}
