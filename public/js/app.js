let allData = null;
let currentSort = 'premium';
let sortAsc = false;
let currentFilter = 'all';
let currentPeriod = 1;

function fmt(n) {
  if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return '$' + (n / 1e3).toFixed(1) + 'K';
  return '$' + n.toFixed(0);
}

function fmtNum(n) {
  return n.toLocaleString();
}

async function loadData() {
  const btn = document.getElementById('refresh-btn');
  const loading = document.getElementById('loading');
  btn.disabled = true;
  loading.style.display = 'flex';

  try {
    const res = await fetch(`/api/options?period=${currentPeriod}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allData = await res.json();
    renderAll();
  } catch (e) {
    console.error('Failed to load data:', e);
    document.getElementById('stats-bar').innerHTML =
      '<div class="stat-card" style="grid-column:1/-1;text-align:center"><div class="label">Error</div><div class="value red">Failed to load data — check server</div></div>';
  } finally {
    loading.style.display = 'none';
    btn.disabled = false;
  }
}

function renderAll() {
  if (!allData) return;
  renderStats();
  renderHeatmap();
  renderExpHeatmap();
  renderTable();
}

function renderStats() {
  const s = allData.summary;
  const h = allData.heatmap.by_ticker;

  let totalCallVol = 0, totalPutVol = 0, totalCallPrem = 0, totalPutPrem = 0;
  for (const t of Object.values(h)) {
    totalCallVol += t.calls.volume;
    totalPutVol += t.puts.volume;
    totalCallPrem += t.calls.premium;
    totalPutPrem += t.puts.premium;
  }

  const pcRatio = totalCallVol > 0 ? (totalPutVol / totalCallVol).toFixed(2) : 'N/A';

  document.getElementById('timestamp').textContent = s.timestamp;
  const periodText = s.period_days === 1 ? 'Today' : `Last ${s.period_days} days`;
  document.getElementById('stats-bar').innerHTML = `
    <div class="stat-card">
      <div class="label">Period</div>
      <div class="value" style="color:var(--accent)">${periodText}</div>
    </div>
    <div class="stat-card">
      <div class="label">Contracts Scanned</div>
      <div class="value">${fmtNum(s.total_contracts_scanned)}</div>
    </div>
    <div class="stat-card">
      <div class="label">Unusual Alerts</div>
      <div class="value" style="color:var(--gold)">${s.unusual_count}</div>
    </div>
    <div class="stat-card">
      <div class="label">Call Premium</div>
      <div class="value green">${fmt(totalCallPrem)}</div>
    </div>
    <div class="stat-card">
      <div class="label">Put Premium</div>
      <div class="value red">${fmt(totalPutPrem)}</div>
    </div>
    <div class="stat-card">
      <div class="label">Put/Call Ratio</div>
      <div class="value">${pcRatio}</div>
    </div>
  `;
}

function renderHeatmap() {
  const h = allData.heatmap.by_ticker;
  let html = '';

  for (const [ticker, data] of Object.entries(h)) {
    const totalVol = data.calls.volume + data.puts.volume;
    const callPct = totalVol > 0 ? (data.calls.volume / totalVol * 100) : 50;
    const putPct = totalVol > 0 ? (data.puts.volume / totalVol * 100) : 50;
    const cls = ticker.toLowerCase();

    html += `
      <div class="heatmap-card ${cls}">
        <h3><span class="ticker-${cls}">${ticker}</span> Options Flow</h3>
        <div class="heatmap-row">
          <span class="label">Total Volume</span>
          <span>${fmtNum(totalVol)}</span>
        </div>
        <div class="heatmap-row">
          <span class="label">Call Volume</span>
          <span style="color:var(--green)">${fmtNum(data.calls.volume)}</span>
        </div>
        <div class="heatmap-row">
          <span class="label">Put Volume</span>
          <span style="color:var(--red)">${fmtNum(data.puts.volume)}</span>
        </div>
        <div class="heatmap-row">
          <span class="label">Call Premium</span>
          <span style="color:var(--green)">${fmt(data.calls.premium)}</span>
        </div>
        <div class="heatmap-row">
          <span class="label">Put Premium</span>
          <span style="color:var(--red)">${fmt(data.puts.premium)}</span>
        </div>
        <div class="heatmap-row">
          <span class="label">Unusual Flags</span>
          <span style="color:var(--gold)">${data.unusual_count}</span>
        </div>
        <div class="bar-container">
          <span class="bar-label" style="color:var(--green)">Calls</span>
          <div class="bar-track">
            <div class="bar-fill call" style="width:${callPct}%"></div>
          </div>
        </div>
        <div class="bar-container">
          <span class="bar-label" style="color:var(--red)">Puts</span>
          <div class="bar-track">
            <div class="bar-fill put" style="width:${putPct}%"></div>
          </div>
        </div>
      </div>
    `;
  }

  document.getElementById('heatmap-grid').innerHTML = html;
}

function renderExpHeatmap() {
  const exps = allData.heatmap.by_expiration;
  if (!exps || exps.length === 0) {
    document.getElementById('exp-grid').innerHTML = '<div class="empty-state"><p>No expiration data</p></div>';
    return;
  }

  const maxUnusual = Math.max(...exps.map(e => e.unusual_count), 1);
  let html = '';

  for (const exp of exps.slice(0, 30)) {
    const heatLevel = Math.min(4, Math.ceil((exp.unusual_count / maxUnusual) * 4));
    const totalVol = exp.call_volume + exp.put_volume;
    const tickerCls = exp.ticker.toLowerCase();

    html += `
      <div class="exp-cell heat-${heatLevel}">
        <div class="exp-ticker"><span class="ticker-${tickerCls}">${exp.ticker}</span></div>
        <div class="exp-date">${exp.expiration}</div>
        <div class="exp-vol">${fmtNum(totalVol)} vol</div>
        ${exp.unusual_count > 0 ? `<div class="exp-unusual">${exp.unusual_count} unusual</div>` : ''}
      </div>
    `;
  }

  document.getElementById('exp-grid').innerHTML = html;
}

function getFilteredData() {
  let trades = allData.notable;
  if (currentFilter === 'call') trades = trades.filter(t => t.type === 'call');
  else if (currentFilter === 'put') trades = trades.filter(t => t.type === 'put');
  else if (currentFilter === 'GLD') trades = trades.filter(t => t.ticker === 'GLD');
  else if (currentFilter === 'SLV') trades = trades.filter(t => t.ticker === 'SLV');
  return trades;
}

function getSortedData(trades) {
  const dir = sortAsc ? 1 : -1;
  return [...trades].sort((a, b) => {
    switch (currentSort) {
      case 'premium': return dir * (a.premium - b.premium);
      case 'expiration': return dir * (a.expiration.localeCompare(b.expiration));
      case 'ticker': return dir * (a.ticker.localeCompare(b.ticker));
      case 'volume': return dir * (a.volume - b.volume);
      case 'ratio': return dir * (a.volumeOiRatio - b.volumeOiRatio);
      case 'strike': return dir * (a.strike - b.strike);
      case 'lastPrice': return dir * (a.lastPrice - b.lastPrice);
      case 'bid': return dir * (a.bid - b.bid);
      case 'ask': return dir * (a.ask - b.ask);
      case 'oi': return dir * (a.openInterest - b.openInterest);
      case 'iv': return dir * (a.iv - b.iv);
      case 'type': return dir * (a.type.localeCompare(b.type));
      default: return 0;
    }
  });
}

function renderTable() {
  const trades = getSortedData(getFilteredData());
  document.getElementById('notable-count').textContent = trades.length;

  if (trades.length === 0) {
    document.getElementById('trades-body').innerHTML =
      '<tr><td colspan="13" style="text-align:center;padding:40px;color:var(--text-dim)">No unusual options activity found matching filters</td></tr>';
    return;
  }

  let html = '';
  for (const t of trades) {
    const rowCls = t.type === 'call' ? 'call-row' : 'put-row';
    const badgeCls = t.type === 'call' ? 'badge-call' : 'badge-put';
    const tickerCls = t.ticker === 'GLD' ? 'ticker-gld' : 'ticker-slv';

    html += `<tr class="${rowCls}">
      <td><span class="${tickerCls}">${t.ticker}</span></td>
      <td><span class="${badgeCls}">${t.type.toUpperCase()}</span></td>
      <td>$${t.strike.toFixed(2)}</td>
      <td>${t.expiration}</td>
      <td>$${t.lastPrice.toFixed(2)}</td>
      <td>$${t.bid.toFixed(2)}</td>
      <td>$${t.ask.toFixed(2)}</td>
      <td>${fmtNum(t.volume)}</td>
      <td>${fmtNum(t.openInterest)}</td>
      <td class="ratio-hot">${t.volumeOiRatio}x</td>
      <td>${t.iv}%</td>
      <td class="premium-val">${fmt(t.premium)}</td>
      <td>${t.moneyness}</td>
    </tr>`;
  }

  document.getElementById('trades-body').innerHTML = html;
}

function setSort(field) {
  if (currentSort === field) {
    sortAsc = !sortAsc;
  } else {
    currentSort = field;
    sortAsc = false;
  }

  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.sort === field);
    if (btn.dataset.sort === field) {
      btn.querySelector('.arrow').textContent = sortAsc ? '▲' : '▼';
    }
  });

  renderTable();
}

function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });
  renderTable();
}

function setPeriod(days) {
  currentPeriod = days;
  document.querySelectorAll('.period-btn').forEach(btn => {
    btn.classList.toggle('active', parseInt(btn.dataset.period) === days);
  });
  loadData();
}

// Load on page ready
loadData();
