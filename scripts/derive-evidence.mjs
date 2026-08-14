#!/usr/bin/env node
/**
 * derive-evidence — Phase 2: derive a one-page campaign evidence report from a dsh session log.
 *
 * Scans an append-only dsh session log (JSONL or JSONL.zstd) for `garak_scan` tool calls,
 * pairs each call with its tool result, and derives C2 `redteam.*` domain events
 * (runtime-neutral, aligned with spec/schema/c2_events.schema.json):
 *
 *   - redteam.target.registered   (authorization gate, schema-enforced)
 *   - redteam.metric.updated      (hit rate as ASR)
 *   - redteam.report.ready        (summary + pointers to evidence/raw reports)
 *
 * Emits the events as JSONL and writes a one-page campaign Markdown. This is the
 * "红队方法论留痕" artifact: the session log is the tape; this script is its viewer.
 *
 * Usage: node scripts/derive-evidence.mjs <session-dir-or-jsonl[.zstd]> [--out dir]
 *
 * No runtime deps. zstd files are decompressed via the `zstd` CLI when present.
 */
import { spawnSync } from 'node:child_process'
import { mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { basename, join, resolve } from 'node:path'

const [, , inputArg, outFlag, outDirArg] = process.argv
const outDir = resolve(outFlag === '--out' && outDirArg ? outDirArg : '.warroom/evidence')

// Probe-family -> OWASP/ATLAS mapping (data/probe-taxonomy.json). Optional: the report
// simply omits the mapping section when the file is missing.
let taxonomyFamilies = {}
try {
  const taxonomy = JSON.parse(readFileSync(new URL('../data/probe-taxonomy.json', import.meta.url), 'utf8'))
  taxonomyFamilies = taxonomy.families ?? {}
} catch {
  console.error('[derive-evidence] warning: data/probe-taxonomy.json not found; mapping section skipped')
}

function familyOf(probe) {
  return String(probe).split('.')[0]
}

function taxonomyRows(campaigns) {
  if (Object.keys(taxonomyFamilies).length === 0) return '| (未加载 data/probe-taxonomy.json) | | |'
  const seen = new Set()
  const rows = []
  for (const c of campaigns) {
    for (const p of c.probes) {
      const f = familyOf(p)
      const key = `${c.campaignId}::${f}`
      if (seen.has(key)) continue
      seen.add(key)
      const t = taxonomyFamilies[f]
      if (!t) {
        rows.push(`| ${c.campaignId} | \`${f}\` | (未收录) | (未收录) |`)
        continue
      }
      rows.push(
        `| ${c.campaignId} | \`${f}\` | ${(t.owasp_llm ?? []).map((x) => `\`${x}\``).join(', ') || '(无)'} | ${(t.mitre_atlas ?? []).map((x) => `\`${x}\``).join(', ') || '(无)'} |`,
      )
    }
  }
  if (rows.length === 0) return '| (无探针记录) | | |'
  return `| campaign_id | 探针族 | OWASP LLM Top10 | MITRE ATLAS |\n|---|---|---|---|\n${rows.join('\n')}`
}

function sessionJsonlPath(input) {
  let s = statSync(input)
  if (s.isDirectory()) {
    // Accept a session directory containing session.jsonl(.zstd).
    for (const cand of ['session.jsonl', 'session.jsonl.zstd']) {
      try {
        const p = join(input, cand)
        statSync(p)
        return p
      } catch {}
    }
    throw new Error(`no session.jsonl found in ${input}`)
  }
  return input
}

function readSession(path) {
  if (path.endsWith('.zstd')) {
    const r = spawnSync('zstd', ['-dc', path], { encoding: 'utf8', maxBuffer: 1 << 30 })
    if (r.status !== 0) throw new Error(`zstd -dc failed: ${r.stderr}`)
    return r.stdout
  }
  return readFileSync(path, 'utf8')
}

function sessionIdOf(inputArg, jsonlPath) {
  // Prefer the session directory name (the dsh session id); fall back to the file stem.
  try {
    if (statSync(inputArg).isDirectory()) return basename(resolve(inputArg))
  } catch {}
  const stem = basename(jsonlPath).replace(/\.jsonl(\.zstd)?$/, '')
  return stem || 'unknown-session'
}

function parseArgsText(text) {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function main() {
  if (!inputArg) {
    console.error('usage: node scripts/derive-evidence.mjs <session-dir-or-jsonl[.zstd]> [--out dir]')
    process.exit(2)
  }
  const jsonlPath = sessionJsonlPath(inputArg)
  const sessionId = sessionIdOf(inputArg, jsonlPath)

  const calls = new Map() // callId -> { name, args, seq, time }
  const results = new Map() // callId -> text
  for (const line of readSession(jsonlPath).split('\n')) {
    if (!line.trim()) continue
    let rec
    try {
      rec = JSON.parse(line)
    } catch {
      continue
    }
    const d = rec?.data
    if (rec.type === 'tool/call' && d?.callId) {
      calls.set(d.callId, { name: d.name, args: parseArgsText(d.arguments), seq: rec.seq, time: rec.time })
    } else if (rec.type === 'tool/result' && d?.message?.content?.[0]?.toolCallId) {
      const callId = d.message.content[0].toolCallId
      const text = d.message.content[0].content?.map((c) => c.text ?? '').join('\n') ?? ''
      results.set(callId, text)
    }
  }

  const events = []
  const campaigns = []
  for (const [callId, call] of calls) {
    if (call.name !== 'garak_scan' || !call.args) continue
    const auth = call.args.authorization ?? {}
    const targetId = String(call.args.target_id ?? '')
    const summary = results.get(callId) ?? ''
    const campaignId = `garak-${targetId.replace(/[^a-zA-Z0-9_-]/g, '_')}-${call.seq}`
    const ts = new Date(call.time ?? Date.now()).toISOString()

    if (auth.authorized !== true || typeof auth.scope !== 'string' || !auth.scope.trim()) {
      console.error(`[derive-evidence] skipping garak_scan call ${callId}: missing authorization gate`)
      continue
    }

    // redteam.target.registered — authorization gate (schema-enforced invariant).
    events.push({
      name: 'redteam.target.registered',
      schema_version: '0.1.0',
      data: {
        target_id: targetId,
        authorization: {
          authorized: true,
          scope: auth.scope,
          ...(auth.authorized_by ? { authorized_by: auth.authorized_by } : {}),
        },
      },
    })

    // redteam.metric.updated — hit rate from the tool summary as ASR.
    const hitPct = /hit rate\s+([\d.]+)%/i.exec(summary)?.[1]
    const reportPath = /Evidence report:\s*(\S+)/i.exec(summary)?.[1]
    if (hitPct !== undefined) {
      events.push({
        name: 'redteam.metric.updated',
        schema_version: '0.1.0',
        data: { campaign_id: campaignId, metrics: { asr: Number(hitPct) / 100 } },
      })
    }

    // redteam.report.ready — evidence pointers for the compliance reviewer.
    events.push({
      name: 'redteam.report.ready',
      schema_version: '0.1.0',
      data: {
        campaign_id: campaignId,
        summary,
        evidence_report: reportPath ?? null,
        session: { id: sessionId, seq: call.seq, time: ts },
      },
    })

    campaigns.push({ campaignId, targetId, auth, summary, hitPct, reportPath, ts, callId, probes: Array.isArray(call.args.probes) ? call.args.probes : [] })
  }

  if (campaigns.length === 0) {
    console.error('[derive-evidence] no garak_scan tool calls found in this session log')
    process.exit(1)
  }

  mkdirSync(outDir, { recursive: true })
  const eventsPath = join(outDir, 'redteam-events.jsonl')
  writeFileSync(eventsPath, events.map((e) => JSON.stringify(e)).join('\n') + '\n', 'utf8')

  const rows = campaigns
    .map((c) => {
      const hit = c.hitPct !== undefined ? `${c.hitPct}%` : '(未知)'
      return `| ${c.campaignId} | ${c.targetId} | ${c.auth.scope} | ${hit} | ${c.reportPath ?? '(未附)'} |`
    })
    .join('\n')
  const md = `# 作战室 campaign 证据报告（从 session log 派生）

> 本报告由 \`scripts/derive-evidence.mjs\` 从 dsh session log（append-only tape）派生。
> 会话：\`${sessionId}\` · 派生时间：${new Date().toISOString()}

## Campaign 概览
| campaign_id | 目标 | 授权范围 | 总体命中率(ASR) | 证据报告 |
|---|---|---|---|---|
${rows}

## 派生的 C2 事件
- \`redteam.target.registered\` ×${events.filter((e) => e.name === 'redteam.target.registered').length}（授权门，schema 强制）
- \`redteam.metric.updated\` ×${events.filter((e) => e.name === 'redteam.metric.updated').length}
- \`redteam.report.ready\` ×${events.filter((e) => e.name === 'redteam.report.ready').length}
- 完整事件流：\`${eventsPath}\`（对齐 \`spec/schema/c2_events.schema.json\`）

## 探针 → 标准映射（基线标注）
${taxonomyRows(campaigns)}

## 留痕链（audit trail）
1. dsh session log 记录 \`garak_scan\` 调用（参数含授权范围、rest_config、探针、预算）与结果 —— 不可变，可重放。
2. 每份详细证据报告由插件落盘（含 per-probe 命中表），路径见上表。
3. 本报告把两者缝合为一页：谁、何时、对什么授权目标、跑了什么、命中多少、报告在哪。

> 映射为**探针族级粗粒度基线标注**（\`data/probe-taxonomy.json\`，OWASP LLM Top10 2025 / MITRE ATLAS v6）。
> 精确到探针级的映射与 severity 判定在 Phase 3 judge 接入后细化。
`

  const mdPath = join(outDir, `campaign-${new Date().toISOString().slice(0, 10)}.md`)
  writeFileSync(mdPath, md, 'utf8')
  console.log(`[derive-evidence] ${campaigns.length} campaign(s)`)
  console.log(`[derive-evidence] events -> ${eventsPath}`)
  console.log(`[derive-evidence] report -> ${mdPath}`)
}

main()
