"""Generate n8n/fcurban-daily-send-workflow.json: the two daily send waves for the London outreach pipeline.

The morning build job (Claude Code routine) writes the day's QA-passed emails to the "Queue" tab of the
queue sheet, one row each, with Wave = 1 or 2 and Approved = "" . The approval step sets Approved = "yes"
once Brian replies "go" in Slack (phase 1) or, in phase 2, unless he replies "stop" before 08:55.
This workflow only ever sends rows that are for today, for the current wave, QA = pass, Approved = yes
and have no Status yet.

Placeholders to replace after import: QUEUE_SHEET_ID, LOG_SHEET_ID (and pick the credentials).
"""
import json, uuid

QUEUE = 'QUEUE_SHEET_ID'
LOG = 'LOG_SHEET_ID'
def rl(v, mode='id'): return {'__rl': True, 'value': v, 'mode': mode}
def node(name, typ, ver, params, pos, **kw):
    n = {'parameters': params, 'id': str(uuid.uuid5(uuid.NAMESPACE_DNS, name)), 'name': name, 'type': typ, 'typeVersion': ver, 'position': pos}
    n.update(kw); return n

BUILD_WAVE = r"""// Pick this wave's rows from the queue. Europe/London date and hour decide the wave.
const DAILY_CAP = 200, WAVE_CAP = 100;
const now = $now.setZone('Europe/London');
const today = now.toFormat('yyyy-MM-dd');
const wave = now.hour < 12 ? '1' : '2';
const rows = $input.all().map(i => i.json);
const sentToday = rows.filter(r => r['Date'] === today && String(r['Status']).trim() === 'Sent').length;
if (sentToday >= DAILY_CAP) return [];
const seenDomains = new Set(rows.filter(r => r['Date'] === today && r['Status'] === 'Sent').map(r => String(r['Email']).split('@').pop().toLowerCase()));
const out = [];
for (const r of rows) {
  if (r['Date'] !== today || String(r['Wave']) !== wave) continue;
  if (String(r['QA']).trim() !== 'pass' || String(r['Approved']).trim().toLowerCase() !== 'yes') continue;
  if (String(r['Status'] ?? '').trim()) continue;
  const email = String(r['Email'] ?? '').trim().toLowerCase();
  if (!email.includes('@')) continue;
  const dom = email.split('@').pop();
  if (seenDomains.has(dom)) continue;
  if (/google\.com\/url/i.test(String(r['HTML body'])) || /[–—]/.test(String(r['Body']) + String(r['Subject']))) continue; // belt and braces
  seenDomains.add(dom);
  out.push({ json: { ...r, _to: email, _wave: wave, _today: today, _waveStart: Math.floor(Date.now() / 1000) } });
  if (out.length >= Math.min(WAVE_CAP, DAILY_CAP - sentToday)) break;
}
return out;
"""

BOUNCE_GATE = r"""// Stop the wave if bounces since the wave started exceed 3% of emails sent in this wave.
// Checked after every 10th send (needs at least 20 sends before it can trip).
// This node runs once per 10 sends, so its own run index gives the sent count.
const sent = ($runIndex + 1) * 10;
const bounces = $input.all().filter(i => i.json && i.json.id).length;
if (sent >= 20 && bounces / sent > 0.03) {
  throw new Error(`Bounce rate ${bounces}/${sent} is over 3%: wave stopped. Check the Inbox for mailer-daemon notices before the next wave.`);
}
return [{ json: { ok: true, sent, bounces } }];
"""

RATE_GATE = r"""// Any Gmail rate-limit / quota / blocked error stops the whole wave. Other errors just mark the row Failed.
const err = String($json.error?.message || $json.error || '');
if (/rate|quota|429|too many|blocked|suspend|limit exceeded|user-rate/i.test(err)) {
  throw new Error('Gmail refused to send (' + err + '). Wave stopped; nothing else will be sent today until checked.');
}
return $input.item;
"""

nodes = [
    node('Wave 1 (09:00) and wave 2 (14:00), weekdays', 'n8n-nodes-base.scheduleTrigger', 1.2,
         {'rule': {'interval': [{'field': 'cronExpression', 'expression': '0 9 * * 1-5'}, {'field': 'cronExpression', 'expression': '0 14 * * 1-5'}]}}, [0, 0]),
    node('Manual test run', 'n8n-nodes-base.manualTrigger', 1, {}, [0, 200]),
    node('Read queue', 'n8n-nodes-base.googleSheets', 4.5, {'documentId': rl(QUEUE), 'sheetName': rl('Queue', 'name'), 'options': {}}, [220, 100]),
    node('Build wave', 'n8n-nodes-base.code', 2, {'jsCode': BUILD_WAVE}, [440, 100]),
    node('Loop over queue', 'n8n-nodes-base.splitInBatches', 3, {'options': {'reset': False}}, [660, 100]),
    node('Wave summary', 'n8n-nodes-base.code', 2, {'jsCode': "return [{ json: { sentThisWave: $input.all().length, finishedAt: $now.toISO() } }];"}, [880, -100]),
    node('Send email', 'n8n-nodes-base.gmail', 2.1, {'sendTo': '={{ $json._to }}', 'subject': "={{ $json['Subject'] }}", 'emailType': 'html',
         'message': "={{ $json['HTML body'] }}", 'options': {'appendAttribution': False}}, [880, 100], onError='continueErrorOutput'),
    node('Mark sent', 'n8n-nodes-base.googleSheets', 4.5, {'operation': 'update', 'documentId': rl(QUEUE), 'sheetName': rl('Queue', 'name'),
         'columns': {'mappingMode': 'defineBelow', 'value': {'row_number': "={{ $('Loop over queue').item.json.row_number }}", 'Status': 'Sent',
                     'Sent at': "={{ $now.setZone('Europe/London').toFormat('yyyy-MM-dd HH:mm:ss') }}", 'Message ID': '={{ $json.id }}', 'Thread ID': '={{ $json.threadId }}'},
                     'matchingColumns': ['row_number'], 'schema': []}, 'options': {}}, [1100, 0]),
    node('Log send', 'n8n-nodes-base.googleSheets', 4.5, {'operation': 'append', 'documentId': rl(LOG), 'sheetName': rl('Log', 'name'),
         'columns': {'mappingMode': 'defineBelow', 'value': {
             'Date': "={{ $('Loop over queue').item.json._today }}", 'Wave': "={{ $('Loop over queue').item.json._wave }}",
             'Sent at': "={{ $now.setZone('Europe/London').toFormat('yyyy-MM-dd HH:mm:ss') }}",
             'Message ID': "={{ $('Send email').item.json.id }}", 'Thread ID': "={{ $('Send email').item.json.threadId }}",
             'Recipient': "={{ $('Loop over queue').item.json._to }}", 'Company': "={{ $('Loop over queue').item.json['Company'] }}",
             'Venue': "={{ $('Loop over queue').item.json['Venue'] }}", 'Hook': "={{ $('Loop over queue').item.json['Hook'] }}"}, 'schema': []}, 'options': {}}, [1320, 0]),
    node('Every 10th send?', 'n8n-nodes-base.if', 2.2, {'conditions': {'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'loose', 'version': 2},
         'conditions': [{'id': 'tenth', 'leftValue': '={{ ($runIndex + 1) % 10 }}', 'rightValue': 0, 'operator': {'type': 'number', 'operation': 'equals'}}], 'combinator': 'and'}, 'options': {}}, [1540, 0]),
    node('Bounces since wave start', 'n8n-nodes-base.gmail', 2.1, {'operation': 'getAll', 'returnAll': True,
         'filters': {'q': "=from:mailer-daemon after:{{ $('Build wave').first().json._waveStart }}"}}, [1760, -100], alwaysOutputData=True),
    node('Bounce gate (3%)', 'n8n-nodes-base.code', 2, {'jsCode': BOUNCE_GATE}, [1980, -100]),
    node('Stop on rate limit', 'n8n-nodes-base.code', 2, {'mode': 'runOnceForEachItem', 'jsCode': RATE_GATE}, [1100, 250]),
    node('Mark failed', 'n8n-nodes-base.googleSheets', 4.5, {'operation': 'update', 'documentId': rl(QUEUE), 'sheetName': rl('Queue', 'name'),
         'columns': {'mappingMode': 'defineBelow', 'value': {'row_number': "={{ $('Loop over queue').item.json.row_number }}", 'Status': 'Failed',
                     'Sent at': "={{ $now.setZone('Europe/London').toFormat('yyyy-MM-dd HH:mm:ss') }}", 'Send error': "={{ $json.error?.message || $json.error || 'send failed' }}"},
                     'matchingColumns': ['row_number'], 'schema': []}, 'options': {}}, [1320, 250]),
    node('Random wait 20 to 40 s', 'n8n-nodes-base.wait', 1.1, {'amount': '={{ 20 + Math.floor(Math.random() * 21) }}', 'unit': 'seconds'}, [2200, 100]),
]
C = lambda *targets: {'main': [[{'node': t, 'type': 'main', 'index': 0} for t in grp] for grp in targets]}
connections = {
    'Wave 1 (09:00) and wave 2 (14:00), weekdays': C(['Read queue']),
    'Manual test run': C(['Read queue']),
    'Read queue': C(['Build wave']),
    'Build wave': C(['Loop over queue']),
    'Loop over queue': C(['Wave summary'], ['Send email']),
    'Send email': C(['Mark sent'], ['Stop on rate limit']),
    'Mark sent': C(['Log send']),
    'Log send': C(['Every 10th send?']),
    'Every 10th send?': C(['Bounces since wave start'], ['Random wait 20 to 40 s']),
    'Bounces since wave start': C(['Bounce gate (3%)']),
    'Bounce gate (3%)': C(['Random wait 20 to 40 s']),
    'Stop on rate limit': C(['Mark failed']),
    'Mark failed': C(['Random wait 20 to 40 s']),
    'Random wait 20 to 40 s': C(['Loop over queue']),
}
wf = {'name': 'FC Urban - London daily outreach send (2 waves)', 'nodes': nodes, 'connections': connections, 'active': False,
      'settings': {'executionOrder': 'v1', 'timezone': 'Europe/London', 'saveManualExecutions': True}, 'pinData': {}}
json.dump(wf, open('../n8n/fcurban-daily-send-workflow.json', 'w'), indent=1)
print('wrote n8n/fcurban-daily-send-workflow.json with', len(nodes), 'nodes')
