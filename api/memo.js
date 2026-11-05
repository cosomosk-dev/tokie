// 夜メモの預かり所（クラウド側）
// しくみ：Vercel Blob（Vercelの「Storage」で Blob を1つ作って、このプロジェクトにつなぐだけ。鍵は自動で入る）に
//   memo/<id>.json  … まだ本人に渡してへんメモ
//   sent/<id>.json  … 朝8時にClaudeへ渡した／本人が済みにしたメモ
// を1件1ファイルで置く。上書きはせえへん（場所を移すだけ）ので、CDNの古いキャッシュを読む事故が起きへん。
//
// 使い方
//   GET  /api/memo?k=KEY            → {ok:true, memos:[{id,ts,text,from}], cloud:true}
//   POST /api/memo  {k, op:"add", text, from, ts}      → 1件足す
//   POST /api/memo  {k, op:"sync", memos:[...]}        → 端末のメモをまとめて足す（同じidは飛ばす）
//   POST /api/memo  {k, op:"sent", ids:[...]}          → 渡した／済みにした（sent/ へ移す）
//   POST /api/memo  {k, op:"del",  ids:[...]}          → 消す
// Blob がまだつながってへん時は 503 {ok:false, cloud:false} を返す（画面側は端末だけで動き続ける）
'use strict';

const KEY = 'yorumemo-7a3k9q2v'; // URLの合言葉（この場所を知ってる人だけ読み書きできる程度の鍵）

function json(res, code, obj) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.status(code).send(JSON.stringify(obj));
}

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  let s = '';
  for await (const c of req) s += c;
  try { return s ? JSON.parse(s) : {}; } catch (e) { return {}; }
}

function clean(x) {
  const text = String(x && x.text || '').replace(/\s+/g, ' ').trim().slice(0, 2000);
  if (!text) return null;
  const id = String(x && x.id || (Date.now() + Math.random().toString(36).slice(2, 6))).replace(/[^A-Za-z0-9_-]/g, '').slice(0, 40) || String(Date.now());
  const ts = Number(x && x.ts) || Date.now();
  const from = String(x && x.from || 'web').slice(0, 20);
  return { id, ts, text, from };
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') { res.setHeader('Access-Control-Allow-Origin', '*'); res.setHeader('Access-Control-Allow-Headers', 'content-type'); return res.status(204).end(); }
  if (!process.env.BLOB_READ_WRITE_TOKEN) return json(res, 503, { ok: false, cloud: false, why: 'Vercel Blob がまだつながってへん（Vercel → tokie → Storage → Create Database → Blob → Connect）' });

  let blob;
  try { blob = require('@vercel/blob'); } catch (e) { return json(res, 503, { ok: false, cloud: false, why: '@vercel/blob が入ってへん' }); }
  const { put, list, del } = blob;

  const q = req.query || {};
  const body = req.method === 'POST' ? await readBody(req) : {};
  const k = String(q.k || body.k || '');
  if (k !== KEY) return json(res, 403, { ok: false, why: '合言葉がちゃう' });

  async function listAll(prefix) {
    const out = [];
    let cursor;
    do {
      const r = await list({ prefix, cursor, limit: 1000 });
      out.push(...r.blobs);
      cursor = r.hasMore ? r.cursor : undefined;
    } while (cursor);
    return out;
  }
  async function readMemos(prefix) {
    const blobs = await listAll(prefix);
    const memos = [];
    await Promise.all(blobs.map(async (b) => {
      try {
        const r = await fetch(b.url, { cache: 'no-store' });
        const x = clean(await r.json());
        if (x) memos.push(x);
      } catch (e) {}
    }));
    memos.sort((a, b) => a.ts - b.ts);
    return { memos, blobs };
  }
  async function write(prefix, x) {
    await put(prefix + x.id + '.json', JSON.stringify(x), { access: 'public', addRandomSuffix: false, contentType: 'application/json', cacheControlMaxAge: 60 });
  }

  try {
    if (req.method === 'GET') {
      const { memos } = await readMemos('memo/');
      return json(res, 200, { ok: true, cloud: true, memos });
    }
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    const op = String(body.op || '');

    if (op === 'add') {
      const x = clean(body);
      if (!x) return json(res, 400, { ok: false, why: '中身が空' });
      await write('memo/', x);
      return json(res, 200, { ok: true, memo: x });
    }
    if (op === 'sync') {
      const incoming = (Array.isArray(body.memos) ? body.memos : []).map(clean).filter(Boolean).slice(0, 200);
      const have = new Set();
      for (const b of await listAll('memo/')) have.add(b.pathname.replace(/^memo\//, '').replace(/\.json$/, ''));
      for (const b of await listAll('sent/')) have.add(b.pathname.replace(/^sent\//, '').replace(/\.json$/, ''));
      let n = 0;
      for (const x of incoming) { if (!have.has(x.id)) { await write('memo/', x); n++; } }
      const { memos } = await readMemos('memo/');
      return json(res, 200, { ok: true, cloud: true, added: n, memos });
    }
    if (op === 'sent' || op === 'del') {
      const ids = new Set((Array.isArray(body.ids) ? body.ids : []).map(String));
      const { memos, blobs } = await readMemos('memo/');
      let n = 0;
      for (const b of blobs) {
        const id = b.pathname.replace(/^memo\//, '').replace(/\.json$/, '');
        if (!ids.has(id)) continue;
        if (op === 'sent') { const x = memos.find((m) => m.id === id); if (x) await write('sent/', Object.assign({}, x, { sentAt: Date.now() })); }
        await del(b.url); n++;
      }
      return json(res, 200, { ok: true, moved: n });
    }
    return json(res, 400, { ok: false, why: 'op がちゃう' });
  } catch (e) {
    return json(res, 500, { ok: false, cloud: true, why: String(e && e.message || e) });
  }
};
