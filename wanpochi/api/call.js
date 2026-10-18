// 親の電話に、相棒から電話をかける
// 使い方: https://wanpochi.vercel.app/api/call?key=（CALL_KEY）  ← 開いた瞬間に鳴る
'use strict';
const P = require('../lib/phone');

module.exports = async (req, res) => {
  const c = P.cfg();
  const q = req.query || {};
  const auth = req.headers.authorization || '';
  const ok = (c.callKey && q.key === c.callKey) || (process.env.CRON_SECRET && auth === 'Bearer ' + process.env.CRON_SECRET);
  if (!ok) return res.status(403).json({ ok: false, error: 'key がちがいます' });

  const missing = ['sid', 'token', 'from', 'parentPhone'].filter(k => !c[k]);
  if (missing.length) return res.status(500).json({ ok: false, error: '設定が足りません: ' + missing.join(', ') });

  const base = P.baseUrl(req);
  try {
    const call = await P.twilio(c, 'Calls.json', {
      To: c.parentPhone,
      From: c.from,
      Url: base + '/api/twiml',
      Method: 'GET',
      Timeout: '40',
      StatusCallback: base + '/api/status',
      StatusCallbackEvent: 'completed',
      StatusCallbackMethod: 'POST',
    });
    res.status(200).json({ ok: true, message: c.parentName + 'さんの電話（' + c.parentPhone + '）にかけています', sid: call.sid });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
};
