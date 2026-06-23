document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initForms();
});

function initTabs() {
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });
}

function initForms() {
    document.getElementById('form-base').addEventListener('submit', handleBase);
    document.getElementById('form-machine').addEventListener('submit', handleMachine);
    document.getElementById('form-fixed').addEventListener('submit', handleFixed);
    document.getElementById('form-float').addEventListener('submit', handleFloat);
    document.getElementById('form-ieee754').addEventListener('submit', handleIeee754);
}

async function post(endpoint, body) {
    console.log('POST', endpoint, body);
    const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    const data = await res.json();
    console.log('response', res.status, data);
    if (!res.ok) {
        let msg = data.detail || `请求失败 (${res.status})`;
        if (Array.isArray(data.detail)) {
            msg = data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join('; ');
        }
        throw new Error(msg);
    }
    return data;
}

function formDataToObject(form) {
    const data = new FormData(form);
    const obj = {};
    data.forEach((value, key) => {
        if (value === 'on') {
            obj[key] = true;
        } else {
            obj[key] = value;
        }
    });
    // Handle unchecked checkboxes (they are not in FormData)
    form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (!(cb.name in obj)) obj[cb.name] = false;
    });
    return obj;
}

async function handleBase(e) {
    e.preventDefault();
    const data = formDataToObject(e.target);
    const container = document.getElementById('result-base');
    container.innerHTML = '<p>计算中...</p>';
    try {
        const res = await post('/api/convert/base', data);
        container.innerHTML = renderBaseResult(res);
    } catch (err) {
        container.innerHTML = `<div class="result-error">错误：${err.message}</div>`;
    }
}

async function handleMachine(e) {
    e.preventDefault();
    const data = formDataToObject(e.target);
    const container = document.getElementById('result-machine');
    container.innerHTML = '<p>计算中...</p>';
    try {
        const res = await post('/api/convert/machine', data);
        container.innerHTML = renderMachineResult(res);
    } catch (err) {
        container.innerHTML = `<div class="result-error">错误：${err.message}</div>`;
    }
}

async function handleFixed(e) {
    e.preventDefault();
    const data = formDataToObject(e.target);
    const container = document.getElementById('result-fixed');
    container.innerHTML = '<p>计算中...</p>';
    try {
        const res = await post('/api/compute/fixed', data);
        container.innerHTML = renderFixedResult(res);
    } catch (err) {
        container.innerHTML = `<div class="result-error">错误：${err.message}</div>`;
    }
}

async function handleFloat(e) {
    e.preventDefault();
    const data = formDataToObject(e.target);
    const container = document.getElementById('result-float');
    container.innerHTML = '<p>计算中...</p>';
    try {
        const res = await post('/api/compute/float', data);
        container.innerHTML = renderFloatResult(res);
    } catch (err) {
        container.innerHTML = `<div class="result-error">错误：${err.message}</div>`;
    }
}

async function handleIeee754(e) {
    e.preventDefault();
    const data = formDataToObject(e.target);
    const container = document.getElementById('result-ieee754');
    container.innerHTML = '<p>转换中...</p>';
    try {
        const res = await post('/api/convert/ieee754', data);
        container.innerHTML = renderIeee754Result(res);
    } catch (err) {
        container.innerHTML = `<div class="result-error">错误：${err.message}</div>`;
    }
}

function renderBits(bits, groups) {
    if (!bits) return '';
    const colorMap = {};
    (groups || []).forEach(g => {
        for (let i = g.start; i < g.end; i++) {
            colorMap[i] = g.color || 'magnitude';
        }
    });
    let html = '<div class="bit-pattern">';
    for (let i = 0; i < bits.length; i++) {
        const ch = bits[i];
        if (ch === '.') {
            html += '<span style="padding:0 0.2rem;font-weight:bold;">.</span>';
        } else {
            const cls = colorMap[i] || '';
            html += `<span class="bit-cell ${cls}">${ch}</span>`;
        }
    }
    html += '</div>';
    if (groups && groups.length) {
        html += '<div class="bit-labels">';
        const seen = new Set();
        groups.forEach(g => {
            const key = `${g.color}-${g.label}`;
            if (g.label && !seen.has(key)) {
                seen.add(key);
                html += `<span class="bit-label"><span class="bit-label-dot ${g.color}"></span>${g.label}</span>`;
            }
        });
        html += '</div>';
    }
    return html;
}

function renderTable(headers, rows) {
    if (!rows || !rows.length) return '';
    let html = '<table class="step-table"><thead><tr>';
    (headers || []).forEach(h => html += `<th>${h}</th>`);
    html += '</tr></thead><tbody>';
    rows.forEach(row => {
        html += '<tr>';
        row.forEach(cell => html += `<td>${cell}</td>`);
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderStep(step) {
    let html = `<div class="step-card">`;
    html += `<div class="step-title">${escapeHtml(step.title)}</div>`;
    if (step.description) {
        html += `<div class="step-desc">${escapeHtml(step.description)}</div>`;
    }
    if (step.bit_patterns && step.bit_patterns.length) {
        step.bit_patterns.forEach(bp => {
            html += `<div class="bit-pattern-label">${escapeHtml(bp.label)}</div>`;
            html += renderBits(bp.bits, bp.groups);
        });
    } else {
        html += renderBits(step.bits, step.bit_groups);
    }
    html += renderTable(step.table_headers, step.table);
    html += `</div>`;
    return html;
}

function renderBaseResult(res) {
    let html = `<div class="result-summary">结果：${escapeHtml(res.result)}</div>`;
    if (res.note) html += `<div class="result-note">${escapeHtml(res.note)}</div>`;
    res.steps.forEach(step => html += renderStep(step));
    return html;
}

function renderMachineResult(res) {
    let html = `<div class="result-summary">`;
    html += `原码：${res.sign_magnitude}<br>`;
    html += `反码：${res.ones_complement}<br>`;
    html += `补码：${res.twos_complement}<br>`;
    html += `移码：${res.offset_binary}`;
    html += `</div>`;
    if (res.note) html += `<div class="result-note">${escapeHtml(res.note)}</div>`;
    res.steps.forEach(step => html += renderStep(step));
    return html;
}

function renderFixedResult(res) {
    let html = `<div class="result-summary">`;
    html += `[x]补 = ${res.x_comp}，[y]补 = ${res.y_comp}<br>`;
    if (res.operation === 'sub') html += `[-y]补 = ${res.neg_y_comp}<br>`;
    html += `结果补码 = ${res.result_comp}<br>`;
    html += `溢出：${res.overflow ? '是' : '否'}<br>`;
    html += `真值：${res.result_decimal}`;
    html += `</div>`;
    res.steps.forEach(step => html += renderStep(step));
    return html;
}

function renderFloatResult(res) {
    let html = `<div class="result-summary">`;
    html += `[x]浮 = ${res.x_machine}<br>`;
    html += `[y]浮 = ${res.y_machine}<br>`;
    html += `对阶后 [y]浮 = ${res.aligned_y_machine}<br>`;
    html += `尾数求和 = ${res.mantissa_sum}<br>`;
    html += `[结果]浮 = ${res.normalized}<br>`;
    html += `真值：${res.final}<br>`;
    html += `溢出：${res.overflow ? '是' : '否'}`;
    html += `</div>`;
    if (res.note) html += `<div class="result-note">${escapeHtml(res.note)}</div>`;
    res.steps.forEach(step => html += renderStep(step));
    return html;
}

function renderIeee754Result(res) {
    let html = `<div class="result-summary">`;
    html += `输入：${escapeHtml(res.input)}<br>`;
    html += `精度：${res.precision === 'float32' ? '单精度 (32 位)' : '双精度 (64 位)'}<br>`;
    html += `十六进制：${res.hex}<br>`;
    html += `二进制：${res.bits}<br>`;
    html += `符号位：${res.sign}，阶码：${res.exponent_bits}（偏置后 ${res.biased_exponent}）`;
    if (res.unbiased_exponent !== null && res.unbiased_exponent !== undefined) {
        html += `，真阶码：${res.unbiased_exponent}`;
    }
    html += `<br>尾数：${res.fraction_bits}<br>`;
    html += `十进制真值：${res.decimal_value}`;
    html += `</div>`;
    if (res.note) html += `<div class="result-note">${escapeHtml(res.note)}</div>`;
    res.steps.forEach(step => html += renderStep(step));
    return html;
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
