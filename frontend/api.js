const API_BASE = "https://127.0.0.1:5000";

async function apiRequest(path, method = "GET", body = null, isFormData = false) {
  const options = {
    method: method,
    credentials: "include"
  };

  if (body !== null) {
    if (isFormData) {
      options.body = body;
    } else {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }
  }

  const response = await fetch(API_BASE + path, options);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong");
  }

  return data;
}


// AUTH
function apiLogin(username, password) {
  return apiRequest("/api/auth/login", "POST", { username, password });
}
function apiLogout() {
  return apiRequest("/api/auth/logout", "POST");
}
function apiMe() {
  return apiRequest("/api/auth/me", "GET");
}

// ADMIN ENDPOINTS
function apiAdminDashboard() {
  return apiRequest("/api/admin/dashboard", "GET");
}
function apiAdminListHospitals() {
  return apiRequest("/api/admin/hospitals", "GET");
}
function apiAdminAddHospital(hospitalData) {
  return apiRequest("/api/admin/hospitals", "POST", hospitalData);
}
function apiAdminListDoctors() {
  return apiRequest("/api/admin/doctors", "GET");
}
function apiAdminAddDoctor(doctorData) {
  return apiRequest("/api/admin/doctors", "POST", doctorData);
}
function apiAdminListPatients(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiRequest(`/api/admin/patients${query}`, "GET");
}
function apiAdminImportCsv(file, hospitalId) {
  const formData = new FormData();
  formData.append("file", file);
  if (hospitalId !== null && hospitalId !== "") {
    formData.append("hospital_id", hospitalId);
  }
  return apiRequest("/api/admin/patients/import-csv", "POST", formData, true);
}

// SHARED UI HELPERS
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  if (!t) return;
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  t.className = 'toast t-' + type + ' show';
  document.getElementById('toast-icon').textContent = icons[type] || '✅';
  document.getElementById('toast-msg').textContent = msg;
  clearTimeout(t._tid);
  t._tid = setTimeout(() => t.classList.remove('show'), 3800);
}


function openOverlay(id) {
  document.getElementById(id).classList.add('open');
}

function closeOverlay(id) {
  document.getElementById(id).classList.remove('open');
}

// HOSPITAL ENDPOINTS
function apiHospitalDashboard() {
  return apiRequest("/api/hospital/dashboard", "GET");
}

function apiHospitalListPatients(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiRequest(`/api/hospital/patients${query}`, "GET");
}

function apiHospitalRegisterPatient(patientData) {
  return apiRequest("/api/hospital/patients", "POST", patientData);
}

function apiHospitalGetPatient(patientId) {
  return apiRequest(`/api/hospital/patients/${patientId}`, "GET");
}

function apiHospitalSearchDoctors(search = "", specialization = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (specialization) params.set("specialization", specialization);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest(`/api/hospital/doctors${query}`, "GET");
}


// DOCTOR ENDPOINTS 
function apiDoctorListHospitals() {
  return apiRequest("/api/doctor/hospitals", "GET");
}

function apiDoctorSearchPatients(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiRequest(`/api/doctor/patients${query}`, "GET");
}

function apiDoctorGetPatient(patientId) {
  return apiRequest(`/api/doctor/patients/${patientId}`, "GET");
}

function apiDoctorAddPrescription(prescriptionData) {
  return apiRequest("/api/doctor/prescriptions", "POST", prescriptionData);
}

function apiDoctorListMyPrescriptions() {
  return apiRequest("/api/doctor/prescriptions", "GET");
}

// OTP
function apiVerifyOtp(otp) {
  return apiRequest("/api/auth/verify-otp", "POST", { otp });
}

// manual Google Drive backup
function apiAdminBackup() {
  return apiRequest("/api/admin/backup", "POST");
}

// List previous backups from Google Drive
function apiAdminListBackups() {
  return apiRequest("/api/admin/backup/list", "GET");
}