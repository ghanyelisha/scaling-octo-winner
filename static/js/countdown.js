'use strict';

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDuration(totalSeconds) {
  if (totalSeconds <= 0) return { d: 0, h: 0, m: 0, s: 0, str: '00:00:00' };
  const d = Math.floor(totalSeconds / 86400);
  const h = Math.floor((totalSeconds % 86400) / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const pad = n => String(n).padStart(2, '0');
  const str = d > 0
    ? `${d}d ${pad(h)}h ${pad(m)}m ${pad(s)}s`
    : `${pad(h)}:${pad(m)}:${pad(s)}`;
  return { d, h, m, s, str };
}

// ── Mini countdowns (task list cards) ────────────────────────────────────────

function initMiniCountdowns() {
  const elements = document.querySelectorAll('.mini-countdown');
  if (!elements.length) return;

  function tick() {
    elements.forEach(el => {
      if (el.dataset.overdue === 'true') return;
      let secs = parseInt(el.dataset.seconds, 10);
      if (isNaN(secs)) return;
      secs = Math.max(0, secs - 1);
      el.dataset.seconds = secs;

      const display = el.querySelector('.countdown-display');
      if (!display) return;

      if (secs <= 0) {
        el.classList.remove('bg-primary', 'bg-opacity-10', 'text-primary');
        el.classList.add('bg-danger', 'bg-opacity-10', 'text-danger');
        display.textContent = 'Overdue';
        el.dataset.overdue = 'true';
      } else {
        display.textContent = formatDuration(secs).str;
      }
    });
  }

  // Initialise immediately then every second
  elements.forEach(el => {
    const display = el.querySelector('.countdown-display');
    if (display && el.dataset.overdue !== 'true') {
      display.textContent = formatDuration(parseInt(el.dataset.seconds, 10)).str;
    }
  });
  setInterval(tick, 1000);
}

// ── Main countdown (detail page) ─────────────────────────────────────────────

let _alarmEnabled  = false;
let _alarmFired    = false;
let _audioCtx      = null;
let _countdownSecs = 0;

function startMainCountdown(initialSeconds, taskId) {
  _countdownSecs = initialSeconds;

  const elDays    = document.getElementById('cdDays');
  const elHours   = document.getElementById('cdHours');
  const elMinutes = document.getElementById('cdMinutes');
  const elSeconds = document.getElementById('cdSeconds');
  const card      = document.getElementById('countdownCard');

  function render() {
    const { d, h, m, s } = formatDuration(_countdownSecs);
    if (elDays)    elDays.textContent    = d;
    if (elHours)   elHours.textContent   = String(h).padStart(2, '0');
    if (elMinutes) elMinutes.textContent = String(m).padStart(2, '0');
    if (elSeconds) elSeconds.textContent = String(s).padStart(2, '0');
  }

  render();

  const timer = setInterval(() => {
    if (_countdownSecs <= 0) {
      clearInterval(timer);
      triggerAlarm();
      return;
    }
    _countdownSecs--;
    render();

    // Sync with server every 60 s to stay accurate
    if (_countdownSecs % 60 === 0 && taskId) {
      fetch(`/tasks/${taskId}/countdown`)
        .then(r => r.json())
        .then(data => { _countdownSecs = data.seconds; })
        .catch(() => {});
    }
  }, 1000);
}

// ── Alarm ─────────────────────────────────────────────────────────────────────

function toggleAlarm() {
  _alarmEnabled = !_alarmEnabled;
  const btn  = document.getElementById('alarmBtn');
  const icon = document.getElementById('bellIcon');
  const text = document.getElementById('alarmBtnText');
  if (_alarmEnabled) {
    icon.className = 'bi bi-bell-fill me-1';
    text.textContent = 'Alarm On';
    btn.classList.add('active');
    // Resume audio context if suspended
    if (_audioCtx && _audioCtx.state === 'suspended') _audioCtx.resume();
  } else {
    icon.className = 'bi bi-bell me-1';
    text.textContent = 'Enable Alarm';
    btn.classList.remove('active');
  }
}

function requestNotification() {
  if (!('Notification' in window)) {
    alert('Your browser does not support notifications.');
    return;
  }
  Notification.requestPermission().then(perm => {
    const btn = document.getElementById('notifyBtn');
    if (perm === 'granted') {
      btn.textContent = 'Notifications On';
      btn.disabled = true;
    } else {
      alert('Notification permission denied.');
    }
  });
}

function triggerAlarm() {
  if (_alarmFired) return;
  _alarmFired = true;

  // Visual overlay
  const overlay = document.getElementById('alarmOverlay');
  if (overlay) overlay.classList.remove('d-none');

  // Browser notification
  if (Notification.permission === 'granted') {
    new Notification('⏰ Time\'s Up!', {
      body: document.title.replace(' - Afah', ''),
      icon: '/static/favicon.ico',
    });
  }

  // Alarm sound (Web Audio API — no file needed)
  if (_alarmEnabled) playAlarmSound();
}

function playAlarmSound() {
  try {
    _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    let count = 0;

    function beep() {
      if (count >= 6) return;
      const osc  = _audioCtx.createOscillator();
      const gain = _audioCtx.createGain();
      osc.connect(gain);
      gain.connect(_audioCtx.destination);
      osc.type = 'square';
      osc.frequency.setValueAtTime(880, _audioCtx.currentTime);
      osc.frequency.setValueAtTime(660, _audioCtx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.3, _audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, _audioCtx.currentTime + 0.4);
      osc.start(_audioCtx.currentTime);
      osc.stop(_audioCtx.currentTime + 0.4);
      count++;
      setTimeout(beep, 600);
    }
    beep();
  } catch (e) {
    console.warn('Audio alarm failed:', e);
  }
}

function dismissAlarm() {
  const overlay = document.getElementById('alarmOverlay');
  if (overlay) overlay.classList.add('d-none');
  if (_audioCtx) _audioCtx.close();
}
