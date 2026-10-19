// ワンポチ 電話版（ガラケー・家の電話）の共通部品
// しくみ：毎朝ポチの番号から親の電話を2〜3回だけ鳴らして切る（出なければ0円）→ 親が着信履歴から折り返す → 出ずに切る（0円）→ 家族に「無事」。
// 親がうっかり出たら短い声で「元気だね」と言って切る（それも無事）。初日だけ使い方を声で伝える電話を1回かける。
// 本番は相棒の声をElevenLabsで作る予定。試しの段階では Twilio の日本語読み上げ（Polly Mizuki）を使う。
'use strict';

function jst(now) {
  return new Date((now || Date.now()) + 9 * 3600000); // UTC+9 の壁時計を UTC のメソッドで読む
}

function greeting(now) {
  const h = jst(now).getUTCHours();
  return h < 11 ? 'おはよう' : (h < 17 ? 'こんにちは' : 'こんばんは');
}

function timeJST(now) {
  const d = jst(now);
  return d.getUTCHours() + ':' + String(d.getUTCMinutes()).padStart(2, '0');
}

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function cfg() {
  const e = process.env;
  return {
    sid: e.TWILIO_ACCOUNT_SID || '',
    token: e.TWILIO_AUTH_TOKEN || '',
    from: e.TWILIO_FROM || '',
    parentPhone: e.PARENT_PHONE || '',
    familyPhone: e.FAMILY_PHONE || '',
    parentName: e.PARENT_NAME || 'ふみこ',
    familyName: e.FAMILY_NAME || 'ゆか',
    petName: e.PET_NAME || 'ポチ',
    callKey: e.CALL_KEY || '',
    voice: e.TWILIO_VOICE || 'Polly.Mizuki',
    lang: 'ja-JP',
  };
}

function baseUrl(req) {
  const proto = (req.headers['x-forwarded-proto'] || 'https').split(',')[0];
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  return proto + '://' + host;
}

function say(c, text) {
  return '<Say language="' + c.lang + '" voice="' + c.voice + '">' + esc(text) + '</Say>';
}

function xml(res, body) {
  res.setHeader('Content-Type', 'text/xml; charset=utf-8');
  res.status(200).send('<?xml version="1.0" encoding="UTF-8"?><Response>' + body + '</Response>');
}

// Twilio REST（ライブラリなし・fetchだけ）
async function twilio(c, path, form) {
  const url = 'https://api.twilio.com/2010-04-01/Accounts/' + c.sid + '/' + path;
  const body = new URLSearchParams(form);
  const r = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: 'Basic ' + Buffer.from(c.sid + ':' + c.token).toString('base64'),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error('Twilio ' + r.status + ': ' + (j.message || JSON.stringify(j)));
  return j;
}

async function sms(c, text) {
  if (!c.familyPhone) return null;
  try {
    return await twilio(c, 'Messages.json', { From: c.from, To: c.familyPhone, Body: text });
  } catch (e) {
    console.error('SMS失敗:', e.message);
    return null;
  }
}

// Vercel は form を req.body に入れてくれるが、文字列で来たときのため
function form(req) {
  const b = req.body;
  if (!b) return {};
  if (typeof b === 'string') return Object.fromEntries(new URLSearchParams(b));
  return b;
}

module.exports = { greeting, timeJST, esc, cfg, baseUrl, say, xml, twilio, sms, form };
