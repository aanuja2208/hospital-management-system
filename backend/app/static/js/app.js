const API = '/api/v1';
let authToken = localStorage.getItem('token');
let refreshToken = localStorage.getItem('refreshToken');
let currentUser = null;
let currentPage = 'dashboard';
async function api(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
    const res = await fetch(`${API}${path}`, { ...opts, headers });
    if (res.status === 401 && refreshToken) {
        const r = await fetch(`${API}/auth/refresh`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (r.ok) {
            const d = await r.json();
            authToken = d.access_token; refreshToken = d.refresh_token;
            localStorage.setItem('token', authToken);
            localStorage.setItem('refreshToken', refreshToken);
            headers['Authorization'] = `Bearer ${authToken}`;
            return fetch(`${API}${path}`, { ...opts, headers }).then(r => r.ok ? r.json() : r.json().then(e => { throw e; }));
        }
        logout(); throw new Error('Session expired');
    }
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Request failed'); }
    return res.json();
}
function toast(msg, type = 'info') {
    let c = document.getElementById('toasts');
    if (!c) { c = document.createElement('div'); c.id = 'toasts'; c.className = 'toast-container'; document.body.appendChild(c); }
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span><span>${msg}</span>`;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3500);
}
function logout() {
    authToken = null; refreshToken = null; currentUser = null;
    localStorage.removeItem('token'); localStorage.removeItem('refreshToken');
    renderLogin();
}
async function handleLogin(email, password) {
    try {
        const d = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
        authToken = d.access_token; refreshToken = d.refresh_token;
        localStorage.setItem('token', authToken); localStorage.setItem('refreshToken', refreshToken);
        currentUser = await api('/auth/me');
        toast('Welcome back, ' + currentUser.first_name + '!', 'success');
        renderApp();
    } catch (e) { toast(e.message, 'error'); }
}
async function handleRegister(data) {
    try {
        const d = await api('/auth/register', { method: 'POST', body: JSON.stringify(data) });
        authToken = d.access_token; refreshToken = d.refresh_token;
        localStorage.setItem('token', authToken); localStorage.setItem('refreshToken', refreshToken);
        currentUser = await api('/auth/me');
        toast('Account created!', 'success');
        renderApp();
    } catch (e) { toast(e.message, 'error'); }
}
function renderLogin() {
    document.getElementById('app').innerHTML = `
    <div class="login-container">
        <div class="login-card">
            <div class="login-logo">
                <div class="logo-icon">🏥</div>
                <h1>MedCenter Pro</h1>
                <p>Hospital Management Platform</p>
            </div>
            <div class="login-tabs">
                <button class="login-tab active" onclick="showLoginTab('login')">Sign In</button>
                <button class="login-tab" onclick="showLoginTab('register')">Register</button>
            </div>
            <div id="loginForm">
                <div class="form-group"><label class="form-label">Email</label><input class="form-input" id="loginEmail" type="email" placeholder="admin@hospital.com"></div>
                <div class="form-group"><label class="form-label">Password</label><input class="form-input" id="loginPass" type="password" placeholder="••••••••"></div>
                <button class="btn btn-primary btn-full btn-lg" onclick="handleLogin(document.getElementById('loginEmail').value,document.getElementById('loginPass').value)">Sign In</button>
                <div class="mt-4 text-sm text-muted" style="text-align:center">
                    <p><b>Demo:</b> admin@hospital.com / admin123</p>
                    <p>sarah.johnson@hospital.com / doctor123</p>
                    <p>john.doe@email.com / patient123</p>
                </div>
            </div>
            <div id="registerForm" class="hidden">
                <div class="form-row"><div class="form-group"><label class="form-label">First Name</label><input class="form-input" id="regFirst"></div><div class="form-group"><label class="form-label">Last Name</label><input class="form-input" id="regLast"></div></div>
                <div class="form-group"><label class="form-label">Email</label><input class="form-input" id="regEmail" type="email"></div>
                <div class="form-group"><label class="form-label">Password</label><input class="form-input" id="regPass" type="password" minlength="8"></div>
                <div class="form-group"><label class="form-label">Phone</label><input class="form-input" id="regPhone"></div>
                <button class="btn btn-primary btn-full btn-lg" onclick="handleRegister({email:document.getElementById('regEmail').value,password:document.getElementById('regPass').value,first_name:document.getElementById('regFirst').value,last_name:document.getElementById('regLast').value,phone:document.getElementById('regPhone').value})">Create Account</button>
            </div>
        </div>
    </div>`;
}
function showLoginTab(tab) {
    document.querySelectorAll('.login-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
    document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');
}
function getNavItems() {
    const role = currentUser?.role;
    const items = [];
    if (role === 'ADMIN') {
        items.push(
            { id: 'dashboard', icon: '📊', label: 'Dashboard' },
            { id: 'departments', icon: '🏢', label: 'Departments' },
            { id: 'doctors', icon: '👨‍⚕️', label: 'Doctors' },
            { id: 'patients', icon: '👥', label: 'Patients' },
            { id: 'appointments', icon: '📅', label: 'Appointments' },
            { id: 'audit', icon: '📋', label: 'Audit Logs' }
        );
    } else if (role === 'DOCTOR') {
        items.push(
            { id: 'dashboard', icon: '📊', label: 'Dashboard' },
            { id: 'appointments', icon: '📅', label: 'My Appointments' },
            { id: 'schedules', icon: '🗓️', label: 'My Schedule' },
            { id: 'patients', icon: '👥', label: 'Patient Records' }
        );
    } else {
        items.push(
            { id: 'dashboard', icon: '🏠', label: 'Dashboard' },
            { id: 'book', icon: '📅', label: 'Book Appointment' },
            { id: 'appointments', icon: '📋', label: 'My Appointments' },
            { id: 'history', icon: '📂', label: 'Medical History' }
        );
    }
    return items;
}
function renderApp() {
    const nav = getNavItems();
    const initials = (currentUser.first_name[0] + currentUser.last_name[0]).toUpperCase();
    const roleClass = currentUser.role.toLowerCase();
    document.getElementById('app').innerHTML = `
    <div class="app-container">
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="logo-icon">🏥</div>
                <div><h2>MedCenter Pro</h2><small>${currentUser.role} Portal</small></div>
            </div>
            <nav class="sidebar-nav">
                <div class="nav-section">
                    <div class="nav-section-title">Navigation</div>
                    ${nav.map(n => `<a class="nav-item ${currentPage === n.id ? 'active' : ''}" onclick="navigate('${n.id}')"><span class="nav-icon">${n.icon}</span>${n.label}</a>`).join('')}
                </div>
            </nav>
            <div class="sidebar-footer">
                <div class="user-card" onclick="logout()">
                    <div class="user-avatar ${roleClass}">${initials}</div>
                    <div class="user-info"><h4>${currentUser.first_name} ${currentUser.last_name}</h4><span>${currentUser.role}</span></div>
                    <span style="margin-left:auto;color:var(--text-muted);font-size:14px" title="Sign Out">⏻</span>
                </div>
            </div>
        </aside>
        <main class="main-content">
            <header class="main-header">
                <h1 id="pageTitle">${nav.find(n => n.id === currentPage)?.label || 'Dashboard'}</h1>
                <div class="header-actions">
                    ${currentUser.role === 'ADMIN' ? '<div class="search-box"><span class="search-icon">🔍</span><input placeholder="Search patients, doctors..." id="globalSearch" onkeyup="if(event.key===\'Enter\')doGlobalSearch()"></div>' : ''}
                    <button class="btn btn-ghost" onclick="logout()" title="Logout">⏻</button>
                </div>
            </header>
            <div class="content-area" id="pageContent"><div class="loading-center"><div class="spinner"></div></div></div>
        </main>
    </div>`;
    loadPage(currentPage);
}
function navigate(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    event?.target?.closest('.nav-item')?.classList.add('active');
    document.getElementById('pageTitle').textContent = getNavItems().find(n => n.id === page)?.label || page;
    document.getElementById('pageContent').innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';
    loadPage(page);
}
async function loadPage(page) {
    try {
        switch (page) {
            case 'dashboard': await renderDashboard(); break;
            case 'departments': await renderDepartments(); break;
            case 'doctors': await renderDoctors(); break;
            case 'patients': await renderPatients(); break;
            case 'appointments': await renderAppointments(); break;
            case 'audit': await renderAuditLogs(); break;
            case 'schedules': await renderSchedules(); break;
            case 'book': await renderBooking(); break;
            case 'history': await renderHistory(); break;
            default: document.getElementById('pageContent').innerHTML = '<div class="empty-state"><div class="empty-icon">🚧</div><h3>Coming Soon</h3></div>';
        }
    } catch (e) { toast(e.message, 'error'); }
}
async function renderDashboard() {
    const el = document.getElementById('pageContent');
    if (currentUser.role === 'ADMIN') {
        const d = await api('/admin/dashboard');
        const s = d.appointments?.by_status || {};
        el.innerHTML = `
        <div class="stat-grid">
            <div class="stat-card purple"><div class="stat-header"><span class="stat-label">Total Appointments</span><div class="stat-icon">📅</div></div><div class="stat-value">${d.appointments?.total || 0}</div><div class="stat-change"><span class="up">Active platform</span></div></div>
            <div class="stat-card cyan"><div class="stat-header"><span class="stat-label">Doctors</span><div class="stat-icon">👨‍⚕️</div></div><div class="stat-value">${d.total_doctors || 0}</div></div>
            <div class="stat-card green"><div class="stat-header"><span class="stat-label">Patients</span><div class="stat-icon">👥</div></div><div class="stat-value">${d.total_patients || 0}</div></div>
            <div class="stat-card amber"><div class="stat-header"><span class="stat-label">Departments</span><div class="stat-icon">🏢</div></div><div class="stat-value">${d.total_departments || 0}</div></div>
        </div>
        <div class="grid-2">
            <div class="card"><div class="card-header"><h3>Appointments by Status</h3></div><div class="card-body">
                ${Object.keys(s).length ? Object.entries(s).map(([k, v]) => `<div class="flex justify-between items-center mb-2"><span class="badge badge-${k === 'COMPLETED' ? 'success' : k === 'CANCELLED' ? 'danger' : k === 'CONFIRMED' ? 'info' : 'warning'}">${k}</span><span class="font-semibold">${v}</span></div>`).join('') : '<div class="empty-state"><p>No appointments yet</p></div>'}
            </div></div>
            <div class="card"><div class="card-header"><h3>Quick Actions</h3></div><div class="card-body">
                <button class="btn btn-primary btn-full mb-2" onclick="navigate('doctors')">👨‍⚕️ Manage Doctors</button>
                <button class="btn btn-secondary btn-full mb-2" onclick="navigate('departments')">🏢 Manage Departments</button>
                <button class="btn btn-secondary btn-full mb-2" onclick="navigate('appointments')">📅 View Appointments</button>
                <button class="btn btn-secondary btn-full" onclick="navigate('audit')">📋 Audit Trail</button>
            </div></div>
        </div>`;
    } else if (currentUser.role === 'DOCTOR') {
        const appts = await api('/appointments/?per_page=5');
        el.innerHTML = `
        <div class="stat-grid">
            <div class="stat-card purple"><div class="stat-header"><span class="stat-label">Total Appointments</span><div class="stat-icon">📅</div></div><div class="stat-value">${appts.total || 0}</div></div>
            <div class="stat-card green"><div class="stat-header"><span class="stat-label">Completed</span><div class="stat-icon">✓</div></div><div class="stat-value">${(appts.items || []).filter(a => a.status === 'COMPLETED').length}</div></div>
        </div>
        <div class="card"><div class="card-header"><h3>Recent Appointments</h3></div><div class="card-body no-padding">${renderAppointmentTable(appts.items || [])}</div></div>`;
    } else {
        const appts = await api('/appointments/?per_page=5');
        el.innerHTML = `
        <div class="stat-grid">
            <div class="stat-card purple"><div class="stat-header"><span class="stat-label">My Appointments</span><div class="stat-icon">📅</div></div><div class="stat-value">${appts.total || 0}</div></div>
        </div>
        <div class="card"><div class="card-header"><h3>Upcoming Appointments</h3><button class="btn btn-primary btn-sm" onclick="navigate('book')">+ Book New</button></div><div class="card-body no-padding">${renderAppointmentTable(appts.items || [])}</div></div>`;
    }
}
function renderAppointmentTable(items) {
    if (!items.length) return '<div class="empty-state"><div class="empty-icon">📅</div><h3>No appointments</h3><p>No appointments found.</p></div>';
    return `<table class="data-table"><thead><tr><th>Date/Time</th><th>${currentUser.role === 'DOCTOR' ? 'Patient' : 'Doctor'}</th><th>Status</th><th>Actions</th></tr></thead><tbody>
    ${items.map(a => `<tr>
        <td><strong>${a.slot_date || 'N/A'}</strong><br><span class="text-sm text-muted">${a.slot_start_time || ''} - ${a.slot_end_time || ''}</span></td>
        <td>${currentUser.role === 'DOCTOR' ? (a.patient_name || 'Patient') : (a.doctor_name || 'Doctor')}<br><span class="text-sm text-muted">${a.specialization || ''}</span></td>
        <td><span class="badge badge-${a.status === 'COMPLETED' ? 'success' : a.status === 'CANCELLED' ? 'danger' : a.status === 'CONFIRMED' ? 'info' : a.status === 'NO_SHOW' ? 'secondary' : 'warning'}">${a.status}</span></td>
        <td>${getApptActions(a)}</td>
    </tr>`).join('')}
    </tbody></table>`;
}
function getApptActions(a) {
    let btns = '';
    if (a.status === 'REQUESTED' && (currentUser.role === 'ADMIN' || currentUser.role === 'DOCTOR'))
        btns += `<button class="btn btn-success btn-sm" onclick="updateApptStatus('${a.id}','CONFIRMED')">Confirm</button> `;
    if (a.status === 'CONFIRMED' && (currentUser.role === 'ADMIN' || currentUser.role === 'STAFF'))
        btns += `<button class="btn btn-primary btn-sm" onclick="updateApptStatus('${a.id}','CHECKED_IN')">Check In</button> `;
    if (a.status === 'CHECKED_IN' && currentUser.role === 'DOCTOR')
        btns += `<button class="btn btn-primary btn-sm" onclick="updateApptStatus('${a.id}','IN_PROGRESS')">Start</button> `;
    if (a.status === 'IN_PROGRESS' && currentUser.role === 'DOCTOR')
        btns += `<button class="btn btn-success btn-sm" onclick="showEncounterModal('${a.id}')">Complete</button> `;
    if (['REQUESTED', 'CONFIRMED'].includes(a.status))
        btns += `<button class="btn btn-danger btn-sm" onclick="cancelAppt('${a.id}')">Cancel</button>`;
    if (a.status === 'COMPLETED')
        btns += `<button class="btn btn-ghost btn-sm" onclick="viewEncounter('${a.id}')">View Notes</button>`;
    return btns || '—';
}
async function updateApptStatus(id, status) {
    try {
        await api(`/appointments/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
        toast('Status updated!', 'success'); loadPage(currentPage);
    } catch (e) { toast(e.message, 'error'); }
}
async function cancelAppt(id) {
    const reason = prompt('Cancel reason:');
    if (!reason) return;
    try {
        await api(`/appointments/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status: 'CANCELLED', cancel_reason: reason }) });
        toast('Appointment cancelled', 'success'); loadPage(currentPage);
    } catch (e) { toast(e.message, 'error'); }
}
async function renderDepartments() {
    const depts = await api('/departments/');
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>Departments</h2><p>Manage hospital departments</p></div>
        <button class="btn btn-primary" onclick="showDeptModal()">+ Add Department</button></div>
    <div class="card"><div class="card-body no-padding">
        <table class="data-table"><thead><tr><th>Name</th><th>Description</th><th>Doctors</th><th>Status</th><th>Actions</th></tr></thead><tbody>
        ${depts.map(d => `<tr><td class="font-semibold">${d.name}</td><td class="text-muted">${d.description || '—'}</td><td>${d.doctor_count}</td>
            <td><span class="badge badge-${d.is_active ? 'success' : 'danger'}">${d.is_active ? 'Active' : 'Inactive'}</span></td>
            <td><button class="btn btn-ghost btn-sm" onclick="showDeptModal('${d.id}','${d.name}','${d.description || ''}')">Edit</button></td></tr>`).join('')}
        ${depts.length === 0 ? '<tr><td colspan="5"><div class="empty-state"><h3>No departments</h3></div></td></tr>' : ''}
        </tbody></table>
    </div></div>`;
}
function showDeptModal(id, name, desc) {
    showModal('Department', `
        <div class="form-group"><label class="form-label">Name</label><input class="form-input" id="deptName" value="${name || ''}"></div>
        <div class="form-group"><label class="form-label">Description</label><textarea class="form-input" id="deptDesc">${desc || ''}</textarea></div>
    `, async () => {
        const data = { name: document.getElementById('deptName').value, description: document.getElementById('deptDesc').value };
        if (id) await api(`/departments/${id}`, { method: 'PUT', body: JSON.stringify(data) });
        else await api('/departments/', { method: 'POST', body: JSON.stringify(data) });
        closeModal(); toast('Department saved!', 'success'); renderDepartments();
    });
}
async function renderDoctors() {
    const users = await api('/admin/users?role=DOCTOR&per_page=50');
    const depts = await api('/departments/');
    window._depts = depts;
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>Doctors</h2><p>Manage doctor accounts</p></div>
        <button class="btn btn-primary" onclick="showDoctorModal()">+ Onboard Doctor</button></div>
    <div class="card"><div class="card-body no-padding">
        <table class="data-table"><thead><tr><th>Name</th><th>Email</th><th>Status</th><th>Actions</th></tr></thead><tbody>
        ${(users.items || []).map(u => `<tr><td class="font-semibold">${u.first_name} ${u.last_name}</td><td class="text-muted">${u.email}</td>
            <td><span class="badge badge-${u.status === 'ACTIVE' ? 'success' : 'danger'}">${u.status}</span></td>
            <td><button class="btn btn-sm ${u.status === 'ACTIVE' ? 'btn-danger' : 'btn-success'}" onclick="toggleUserStatus('${u.id}','${u.status === 'ACTIVE' ? 'BLOCKED' : 'ACTIVE'}')">${u.status === 'ACTIVE' ? 'Block' : 'Activate'}</button></td></tr>`).join('')}
        </tbody></table>
    </div></div>`;
}
function showDoctorModal() {
    const deptOpts = (window._depts || []).map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    showModal('Onboard Doctor', `
        <div class="form-row"><div class="form-group"><label class="form-label">First Name</label><input class="form-input" id="docFirst"></div><div class="form-group"><label class="form-label">Last Name</label><input class="form-input" id="docLast"></div></div>
        <div class="form-group"><label class="form-label">Email</label><input class="form-input" id="docEmail" type="email"></div>
        <div class="form-group"><label class="form-label">Password</label><input class="form-input" id="docPass" type="password" value="doctor123"></div>
        <div class="form-group"><label class="form-label">Department</label><select class="form-input" id="docDept">${deptOpts}</select></div>
        <div class="form-row"><div class="form-group"><label class="form-label">Specialization</label><input class="form-input" id="docSpec"></div><div class="form-group"><label class="form-label">Reg. Number</label><input class="form-input" id="docReg"></div></div>
        <div class="form-row"><div class="form-group"><label class="form-label">Qualification</label><input class="form-input" id="docQual"></div><div class="form-group"><label class="form-label">Experience (yrs)</label><input class="form-input" id="docExp" type="number" value="0"></div></div>
    `, async () => {
        await api('/admin/doctors', {
            method: 'POST', body: JSON.stringify({
                email: document.getElementById('docEmail').value, password: document.getElementById('docPass').value,
                first_name: document.getElementById('docFirst').value, last_name: document.getElementById('docLast').value,
                department_id: document.getElementById('docDept').value, specialization: document.getElementById('docSpec').value,
                registration_number: document.getElementById('docReg').value, qualification: document.getElementById('docQual').value,
                experience_years: parseInt(document.getElementById('docExp').value) || 0
            })
        });
        closeModal(); toast('Doctor onboarded!', 'success'); renderDoctors();
    });
}
async function toggleUserStatus(id, status) {
    try {
        await api(`/admin/users/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
        toast('User status updated!', 'success'); loadPage(currentPage);
    } catch (e) { toast(e.message, 'error'); }
}
async function renderPatients() {
    const users = await api('/admin/users?role=PATIENT&per_page=50');
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>Patients</h2><p>${users.total || 0} registered patients</p></div></div>
    <div class="card"><div class="card-body no-padding">
        <table class="data-table"><thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Status</th><th>Actions</th></tr></thead><tbody>
        ${(users.items || []).map(u => `<tr><td class="font-semibold">${u.first_name} ${u.last_name}</td><td class="text-muted">${u.email}</td><td>${u.phone || '—'}</td>
            <td><span class="badge badge-${u.status === 'ACTIVE' ? 'success' : 'danger'}">${u.status}</span></td>
            <td><button class="btn btn-sm ${u.status === 'ACTIVE' ? 'btn-danger' : 'btn-success'}" onclick="toggleUserStatus('${u.id}','${u.status === 'ACTIVE' ? 'BLOCKED' : 'ACTIVE'}')">${u.status === 'ACTIVE' ? 'Block' : 'Activate'}</button></td></tr>`).join('')}
        </tbody></table>
    </div></div>`;
}
async function renderAppointments() {
    const d = await api('/appointments/?per_page=50');
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>Appointments</h2><p>${d.total || 0} total</p></div>
        ${currentUser.role === 'PATIENT' ? '<button class="btn btn-primary" onclick="navigate(\'book\')">+ Book Appointment</button>' : ''}</div>
    <div class="card"><div class="card-body no-padding">${renderAppointmentTable(d.items || [])}</div></div>`;
}
async function renderBooking() {
    const depts = await api('/departments/');
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>Book Appointment</h2><p>Find a doctor and pick a time slot</p></div></div>
    <div class="card"><div class="card-body">
        <div class="form-group"><label class="form-label">Select Department</label>
            <select class="form-input" id="bookDept" onchange="loadDeptDoctors()"><option value="">— Choose —</option>${depts.filter(d => d.is_active).map(d => `<option value="${d.id}">${d.name} (${d.doctor_count} doctors)</option>`).join('')}</select></div>
        <div id="doctorList"></div><div id="slotList"></div><div id="bookConfirm"></div>
    </div></div>`;
}
async function loadDeptDoctors() {
    const deptId = document.getElementById('bookDept').value;
    if (!deptId) return;
    let doctors = [];
    try {
        doctors = await api(`/departments/${deptId}/doctors`);
    } catch (e) {
        toast('Could not load doctors: ' + e.message, 'error');
    }
    document.getElementById('doctorList').innerHTML = `<div class="form-group"><label class="form-label">Select Doctor</label>
        <select class="form-input" id="bookDoc" onchange="loadSlots()"><option value="">— Choose —</option>
        ${doctors.map(d => `<option value="${d.id}">${d.name} — ${d.specialization}</option>`).join('')}</select></div>`;
    document.getElementById('slotList').innerHTML = '';
    document.getElementById('bookConfirm').innerHTML = '';
}
async function loadSlots() {
    const docId = document.getElementById('bookDoc').value;
    if (!docId) return;
    const slots = await api(`/doctors/${docId}/slots`);
    if (!slots.length) {
        document.getElementById('slotList').innerHTML = '<div class="empty-state"><h3>No slots available</h3><p>This doctor has no available slots in the next 14 days.</p></div>';
        return;
    }
    const byDate = {};
    slots.forEach(s => { (byDate[s.slot_date] = byDate[s.slot_date] || []).push(s); });
    document.getElementById('slotList').innerHTML = `<label class="form-label mt-4">Available Slots</label>` +
        Object.entries(byDate).map(([date, sl]) => `
            <div class="date-group"><div class="date-group-header">📅 ${new Date(date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</div>
            <div class="slot-grid">${sl.map(s => `<button class="slot-btn ${s.is_booked ? 'booked' : ''}" onclick="selectSlot('${s.id}','${date}','${s.start_time}','${s.end_time}')" ${s.is_booked ? 'disabled' : ''}>${s.start_time?.substring(0, 5)} - ${s.end_time?.substring(0, 5)}</button>`).join('')}</div></div>
        `).join('');
}
function selectSlot(id, date, start, end) {
    document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
    event.target.classList.add('selected');
    window._selectedSlot = { id, date, start, end };
    document.getElementById('bookConfirm').innerHTML = `
        <div class="mt-4"><div class="form-group"><label class="form-label">Reason for Visit</label><textarea class="form-input" id="bookReason" placeholder="Describe your symptoms..."></textarea></div>
        <button class="btn btn-primary btn-lg btn-full" onclick="confirmBooking()">✓ Confirm Appointment — ${date} at ${start?.substring(0, 5)}</button></div>`;
}
async function confirmBooking() {
    const s = window._selectedSlot;
    if (!s) return;
    try {
        await api('/appointments/', {
            method: 'POST', body: JSON.stringify({
                doctor_id: document.getElementById('bookDoc').value,
                slot_id: s.id, reason: document.getElementById('bookReason').value
            })
        });
        toast('Appointment booked!', 'success');
        navigate('appointments');
    } catch (e) { toast(e.message, 'error'); }
}
function showEncounterModal(apptId) {
    showModal('Complete Visit — Clinical Notes', `
        <div class="form-group"><label class="form-label">Chief Complaint</label><input class="form-input" id="encComplaint"></div>
        <div class="form-group"><label class="form-label">Diagnosis</label><textarea class="form-input" id="encDiag"></textarea></div>
        <div class="form-group"><label class="form-label">Clinical Notes</label><textarea class="form-input" id="encNotes"></textarea></div>
        <div class="form-group"><label class="form-label">Follow-up Instructions</label><textarea class="form-input" id="encFollow"></textarea></div>
        <hr style="border-color:var(--border);margin:16px 0">
        <div class="form-label">Prescriptions</div>
        <div id="rxList"></div>
        <button class="btn btn-secondary btn-sm mt-2" onclick="addRxRow()">+ Add Medication</button>
    `, async () => {
        const rxEls = document.querySelectorAll('.rx-row');
        const prescriptions = Array.from(rxEls).map(r => ({
            medication_name: r.querySelector('.rx-name-input').value,
            dosage: r.querySelector('.rx-dose').value,
            frequency: r.querySelector('.rx-freq').value,
            duration_days: parseInt(r.querySelector('.rx-days').value) || 7,
            instructions: r.querySelector('.rx-instr').value
        })).filter(r => r.medication_name);
        await api(`/appointments/${apptId}/encounter`, {
            method: 'POST', body: JSON.stringify({
                chief_complaint: document.getElementById('encComplaint').value,
                diagnosis: document.getElementById('encDiag').value,
                clinical_notes: document.getElementById('encNotes').value,
                follow_up_instructions: document.getElementById('encFollow').value,
                prescriptions
            })
        });
        closeModal(); toast('Visit completed!', 'success'); loadPage(currentPage);
    });
}
function addRxRow() {
    const div = document.getElementById('rxList');
    const row = document.createElement('div');
    row.className = 'rx-row rx-card';
    row.innerHTML = `<div class="form-row"><div class="form-group"><label class="form-label">Medication</label><input class="form-input rx-name-input"></div><div class="form-group"><label class="form-label">Dosage</label><input class="form-input rx-dose" placeholder="500mg"></div></div>
        <div class="form-row"><div class="form-group"><label class="form-label">Frequency</label><input class="form-input rx-freq" placeholder="Twice daily"></div><div class="form-group"><label class="form-label">Duration (days)</label><input class="form-input rx-days" type="number" value="7"></div></div>
        <div class="form-group"><label class="form-label">Instructions</label><input class="form-input rx-instr" placeholder="After meals"></div>`;
    div.appendChild(row);
}
async function viewEncounter(apptId) {
    toast('Encounter details available in Medical History', 'info');
}
async function renderSchedules() {
    if (!currentUser.doctor_profile) { document.getElementById('pageContent').innerHTML = '<div class="empty-state"><h3>No doctor profile</h3></div>'; return; }
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>My Schedule</h2><p>Manage your availability</p></div></div>
    <div class="card"><div class="card-body">
        <p class="text-muted mb-4">Your weekly schedule is set up during onboarding. Contact admin to modify.</p>
        <div class="stat-grid">
            ${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map(d => `
                <div class="stat-card blue"><div class="stat-header"><span class="stat-label">${d}</span><div class="stat-icon">🗓️</div></div><div class="stat-value text-sm" style="font-size:16px">9:00 - 17:00</div><div class="stat-change">30 min slots</div></div>
            `).join('')}
        </div>
    </div></div>`;
}
async function renderHistory() {
    if (!currentUser.patient_profile) {
        document.getElementById('pageContent').innerHTML = '<div class="empty-state"><h3>No patient profile</h3></div>';
        return;
    }
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>Medical History</h2><p>Your visit records and prescriptions</p></div></div>
    <div class="card"><div class="card-body"><div class="empty-state"><div class="empty-icon">📂</div><h3>Your records will appear here</h3><p>After your doctor completes a visit, your diagnosis, notes, and prescriptions will be shown in this timeline.</p></div></div></div>`;
}
async function renderAuditLogs() {
    const d = await api('/admin/audit-logs?per_page=50');
    document.getElementById('pageContent').innerHTML = `
    <div class="page-header"><div><h2>Audit Trail</h2><p>${d.total || 0} log entries</p></div></div>
    <div class="card"><div class="card-body no-padding">
        <table class="data-table"><thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead><tbody>
        ${(d.items || []).map(l => `<tr><td class="text-sm">${l.created_at ? new Date(l.created_at).toLocaleString() : '—'}</td><td>${l.user_name || l.user_id}</td>
            <td><span class="badge badge-purple">${l.action}</span></td><td class="text-muted">${l.entity_type}</td>
            <td class="text-sm text-muted">${l.new_values ? JSON.stringify(l.new_values).substring(0, 60) : '—'}</td></tr>`).join('')}
        ${!(d.items || []).length ? '<tr><td colspan="5"><div class="empty-state"><h3>No audit logs yet</h3></div></td></tr>' : ''}
        </tbody></table>
    </div></div>`;
}
async function doGlobalSearch() {
    const q = document.getElementById('globalSearch').value;
    if (!q) return;
    try {
        const r = await api(`/admin/search?q=${encodeURIComponent(q)}`);
        showModal('Search Results', `
            <h4 class="mb-2">Patients (${r.patients?.length || 0})</h4>
            ${(r.patients || []).map(p => `<div class="rx-card"><strong>${p.first_name} ${p.last_name}</strong><br><span class="text-muted">${p.email}</span></div>`).join('') || '<p class="text-muted">None</p>'}
            <h4 class="mb-2 mt-4">Doctors (${r.doctors?.length || 0})</h4>
            ${(r.doctors || []).map(d => `<div class="rx-card"><strong>${d.name}</strong><br><span class="text-muted">${d.specialization} — ${d.department}</span></div>`).join('') || '<p class="text-muted">None</p>'}
        `);
    } catch (e) { toast(e.message, 'error'); }
}
function showModal(title, body, onSave) {
    let overlay = document.getElementById('modalOverlay');
    if (!overlay) { overlay = document.createElement('div'); overlay.id = 'modalOverlay'; overlay.className = 'modal-overlay'; document.body.appendChild(overlay); }
    overlay.innerHTML = `<div class="modal">
        <div class="modal-header"><h3>${title}</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
        <div class="modal-body">${body}</div>
        ${onSave ? '<div class="modal-footer"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" id="modalSaveBtn">Save</button></div>' : ''}
    </div>`;
    overlay.classList.add('active');
    overlay.onclick = e => { if (e.target === overlay) closeModal(); };
    if (onSave) document.getElementById('modalSaveBtn').onclick = async () => { try { await onSave(); } catch (e) { toast(e.message, 'error'); } };
}
function closeModal() {
    const o = document.getElementById('modalOverlay');
    if (o) o.classList.remove('active');
}
async function init() {
    if (authToken) {
        try {
            currentUser = await api('/auth/me');
            renderApp();
        } catch { renderLogin(); }
    } else { renderLogin(); }
}
init();