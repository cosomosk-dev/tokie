// ワンポチ 電話版（ガラケー・家の電話）の共通部品
// 本番は相棒の声をElevenLabsで作る予定。試しの段階では Twilio の日本語読み上げ（Polly Mizuki）を使う。
'use strict';

const DAY = 86400000;

// 電話で聞いて分かる問題だけ（答えが数字のものは、ボタンの番号とまぎらわしいので入れない）
const BANK = [
  { q: 'ワンワンと なくのは、どれ？', c: ['いぬ', 'ねこ', 'うし'] },
  { q: 'はるに さく はなは、どれ？', c: ['さくら', 'ひまわり', 'もみじ'] },
  { q: 'うみに すむのは、どれ？', c: ['たこ', 'くま', 'うさぎ'] },
  { q: 'あめの ひに さすのは、どれ？', c: ['かさ', 'ぼうし', 'めがね'] },
  { q: 'なつに たべるのは、どれ？', c: ['すいか', 'やきいも', 'おなべ'] },
  { q: 'さるも きから、の つづきは？', c: ['おちる', 'のぼる', 'とぶ'] },
  { q: 'ニャーと なくのは、どれ？', c: ['ねこ', 'ぶた', 'にわとり'] },
  { q: 'そらを とぶのは、どれ？', c: ['とり', 'さかな', 'かめ'] },
  { q: 'バナナの いろは、どれ？', c: ['きいろ', 'あか', 'あお'] },
  { q: 'ふゆに つかうのは、どれ？', c: ['マフラー', 'ふうりん', 'かきごおり'] },
  { q: 'ごはんを たべるときに つかうのは、どれ？', c: ['おはし', 'かなづち', 'はさみ'] },
  { q: 'いそがば、の つづきは？', c: ['まわれ', 'はしれ', 'とまれ'] },
  { q: 'おしょうがつに かざるのは、どれ？', c: ['かどまつ', 'かぼちゃ', 'ツリー'] },
  { q: 'モーと なくのは、どれ？', c: ['うし', 'いぬ', 'かえる'] },
];

function jst(now) {
  return new Date((now || Date.now()) + 9 * 3600000); // UTC+9 の壁時計を UTC のメソッドで読む
}

// きょうの問題（正解の位置は日ごとにずらす）
function questionFor(now) {
  const d = jst(now);
  const idx = Math.floor(d.getTime() / DAY);
  const base = BANK[idx % BANK.length];
  const k = idx % 3;
  const c = [0, 1, 2].map(i => base.c[(i + k) % 3]);
  return { q: base.q, c, a: (3 - k) % 3 };
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
    parentName: e.PARENT_NAME || 'おかあさん',
    familyName: e.FAMILY_NAME || 'かぞく',
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

module.exports = { questionFor, greeting, timeJST, esc, cfg, baseUrl, say, xml, twilio, sms, form };
