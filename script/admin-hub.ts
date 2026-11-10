#!/usr/bin/env node
/**
 * VoiceIQ India — Terminal Admin & Voice Intelligence Hub
 *
 * Usage:
 *   npm run admin
 *   npm run admin -- --watch
 *   npx tsx script/admin-hub.ts
 */

const API_URL = process.env.API_URL || 'http://127.0.0.1:8000/api/admin/analytics';
const isWatch = process.argv.includes('--watch') || process.argv.includes('-w');

// ANSI Color Helpers
const C = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  italic: '\x1b[3m',
  underline: '\x1b[4m',
  orange: '\x1b[38;5;208m',
  yellow: '\x1b[38;5;220m',
  amber: '\x1b[38;5;214m',
  green: '\x1b[38;5;42m',
  red: '\x1b[38;5;196m',
  cyan: '\x1b[38;5;51m',
  blue: '\x1b[38;5;39m',
  white: '\x1b[38;5;15m',
  gray: '\x1b[38;5;244m',
  darkGray: '\x1b[38;5;238m',
  bgDark: '\x1b[48;5;234m',
};

function renderBar(value: number, max: number, width = 24, color = C.orange): string {
  const safeMax = max > 0 ? max : 1;
  const ratio = Math.min(1, Math.max(0, value / safeMax));
  const filled = Math.round(ratio * width);
  const empty = width - filled;
  const bar = '█'.repeat(filled) + '░'.repeat(empty);
  const pct = Math.round(ratio * 100).toString().padStart(3, ' ');
  return `${color}${bar}${C.reset} ${C.white}${pct}%${C.reset}`;
}

function formatINR(amount: number): string {
  return '₹' + amount.toLocaleString('en-IN');
}

async function fetchAnalytics(): Promise<any> {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err: any) {
    return { error: err.message || 'Connection failed' };
  }
}

function clearScreen(): void {
  process.stdout.write('\x1b[2J\x1b[0;0H');
}

function drawBox(content: string, width = 76): void {
  const horizontal = '─'.repeat(width - 2);
  console.log(`${C.amber}┌${horizontal}┐${C.reset}`);
  for (const line of content.split('\n')) {
    // Strip ansi for length calc
    const stripped = line.replace(/\x1b\[[0-9;]*m/g, '');
    const padding = Math.max(0, width - 4 - stripped.length);
    console.log(`${C.amber}│${C.reset} ${line}${' '.repeat(padding)} ${C.amber}│${C.reset}`);
  }
  console.log(`${C.amber}└${horizontal}┘${C.reset}`);
}

async function renderDashboard(): Promise<void> {
  const data = await fetchAnalytics();

  if (isWatch) {
    clearScreen();
  }

  const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  console.log(`\n${C.orange}${C.bold}  ╔════════════════════════════════════════════════════════════════════════════╗${C.reset}`);
  console.log(`${C.orange}${C.bold}  ║      VOICEIQ INDIA — ADMIN & VOICE INTELLIGENCE TERMINAL HUB        ║${C.reset}`);
  console.log(`${C.orange}${C.bold}  ╚════════════════════════════════════════════════════════════════════════════╝${C.reset}`);
  console.log(`  ${C.gray}Live Database & Gnani AI Metrics  •  Refreshed at: ${C.white}${now}${C.reset} ${isWatch ? C.green + '[LIVE WATCH]' + C.reset : ''}\n`);

  if (data.error) {
    console.log(`  ${C.red}${C.bold}⚠ Backend Server Unreachable (${API_URL})${C.reset}`);
    console.log(`  ${C.yellow}To view live database statistics, please ensure the backend is running:${C.reset}`);
    console.log(`  ${C.cyan}  npm run backend${C.reset}`);
    console.log(`  ${C.gray}Or test directly against SQLite via: ${C.white}python admin.py${C.reset}\n`);
    return;
  }

  const store = data.store || {};
  const support = data.support || {};
  const recentConvs = data.recent_conversations || [];

  // Top Key Metric Cards
  console.log(`  ${C.bold}KEY PERFORMANCE METRICS${C.reset}`);
  console.log(`  ${C.darkGray}${'─'.repeat(74)}${C.reset}`);

  const card1 = `${C.gray}Total Orders:${C.reset}    ${C.white}${C.bold}${store.total_orders ?? 0}${C.reset} (${C.green}${store.active_orders ?? 0} in transit${C.reset})`;
  const card2 = `${C.gray}Simulated Rev:${C.reset}   ${C.orange}${C.bold}${formatINR(store.simulated_revenue ?? 0)}${C.reset}`;
  const card3 = `${C.gray}Voice Queries:${C.reset}   ${C.white}${C.bold}${store.voice_conversations_count ?? 0}${C.reset} (${C.green}${store.transcription_success_rate ?? 100}% accuracy${C.reset})`;
  const card4 = `${C.gray}7-Day Returns:${C.reset}   ${C.yellow}${C.bold}${store.total_returns ?? 0} requests${C.reset} (${C.green}${store.delivered_orders ?? 0} delivered${C.reset})`;

  console.log(`  ${card1.padEnd(46)} ${card2}`);
  console.log(`  ${card3.padEnd(46)} ${card4}`);
  console.log(`  ${C.darkGray}${'─'.repeat(74)}${C.reset}\n`);

  // Intent Breakdown
  const intents = store.intent_distribution || {};
  const intentEntries = Object.entries(intents) as [string, number][];
  const maxIntent = Math.max(1, ...intentEntries.map(([_, v]) => v));

  console.log(`  ${C.amber}${C.bold}📊 CUSTOMER VOICE INTENTS BREAKDOWN${C.reset}`);
  if (intentEntries.length === 0) {
    console.log(`  ${C.gray}No voice intents logged yet. Speak queries into the Voice Assistant!${C.reset}`);
  } else {
    for (const [intent, count] of intentEntries) {
      const label = intent.replace(/_/g, ' ').toUpperCase().padEnd(20, ' ');
      const bar = renderBar(count, maxIntent, 20, C.orange);
      console.log(`  ${C.white}${label}${C.reset} ${bar} ${C.gray}(${count})${C.reset}`);
    }
  }
  console.log('');

  // Multilingual Indian Audio Distribution
  const langs = store.language_distribution || {};
  const langEntries = Object.entries(langs) as [string, number][];
  const maxLang = Math.max(1, ...langEntries.map(([_, v]) => v));

  console.log(`  ${C.yellow}${C.bold}🌐 MULTILINGUAL INDIAN AUDIO DISTRIBUTION (BCP-47)${C.reset}`);
  if (langEntries.length === 0) {
    console.log(`  ${C.gray}Languages will populate as voice sessions are recorded.${C.reset}`);
  } else {
    for (const [lang, count] of langEntries) {
      const label = lang.padEnd(20, ' ');
      const bar = renderBar(count, maxLang, 20, C.yellow);
      console.log(`  ${C.white}${label}${C.reset} ${bar} ${C.gray}(${count} recordings)${C.reset}`);
    }
  }
  console.log('');

  // Recent Voice Support Logs
  console.log(`  ${C.blue}${C.bold}🎙 RECENT CUSTOMER VOICE SUPPORT LOGS${C.reset}`);
  if (recentConvs.length === 0) {
    console.log(`  ${C.gray}No voice sessions logged in SQLite database yet.${C.reset}`);
  } else {
    console.log(`  ${C.gray}${'DATE / TIME'.padEnd(20)} ${'LANG'.padEnd(10)} ${'STATUS'.padEnd(12)} TRANSCRIPT${C.reset}`);
    console.log(`  ${C.darkGray}${'─'.repeat(74)}${C.reset}`);

    for (const c of recentConvs.slice(0, 5)) {
      const timeStr = c.created_at
        ? new Date(c.created_at).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        : 'Recent';
      const lang = (c.language_code || 'en-IN').padEnd(10, ' ');
      const statusColor = c.status === 'completed' ? C.green : c.status === 'failed' ? C.red : C.yellow;
      const status = `${statusColor}${c.status?.toUpperCase().padEnd(12, ' ')}${C.reset}`;
      const transcript = c.transcript
        ? `"${c.transcript.slice(0, 36)}${c.transcript.length > 36 ? '...' : ''}"`
        : C.gray + '(Speech processed via Gnani Prisma)' + C.reset;

      console.log(`  ${C.white}${timeStr.padEnd(20)}${C.reset} ${C.cyan}${lang}${C.reset} ${status} ${C.white}${transcript}${C.reset}`);
    }
  }
  console.log(`  ${C.darkGray}${'─'.repeat(74)}${C.reset}`);

  if (isWatch) {
    console.log(`\n  ${C.gray}Press ${C.white}Ctrl+C${C.gray} to exit live watch mode.${C.reset}\n`);
  } else {
    console.log(`\n  ${C.gray}Tip: Run ${C.white}npm run admin:watch${C.gray} or ${C.white}npm run admin -- --watch${C.gray} for real-time live monitoring.${C.reset}\n`);
  }
}

async function main() {
  await renderDashboard();

  if (isWatch) {
    setInterval(async () => {
      await renderDashboard();
    }, 3000);
  }
}

main().catch((err) => {
  console.error('Fatal CLI Error:', err);
  process.exit(1);
});
