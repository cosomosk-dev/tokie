// 親の電話を、ポチの番号から鳴らす
// 使い方:
//   https://wanpochi.vercel.app/api/call?key=（CALL_KEY）            ← 毎朝の「鳴らすだけ」（2〜3回で切る。出なければ0円）
//   https://wanpochi.vercel.app/api/call?key=（CALL_KEY）&mode=intro ← 初日だけの「使い方を声で伝える電話」
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

  const intro = q.mode === 'intro';
  const base = P.baseUrl(req);
  try {
    const call = await P.twilio(c, 'Calls.json', {
      To: c.parentPhone,
      From: c.from,
      Url: base + '/api/answered?mode=' + (intro ? 'intro' : 'ring'),
      Method: 'POST',
      // 鳴らすだけの日は10秒（2〜3回）で切る。留守電が出る前に切るためでもある。案内の電話は出てもらうので長め
      Timeout: intro ? '40' : '10',
      // 留守番電話が出たら「無事」にしない（answered.js で見分ける）
      MachineDetection: 'Enable',
      StatusCallback: base + '/api/status',
      StatusCallbackEvent: 'completed',
      StatusCallbackMethod: 'POST',
    });
    res.status(200).json({ ok: true, message: c.parentName + 'さんの電話（' + c.parentPhone + '）を' + (intro ? '案内の電話で' : '2〜3回') + '鳴らしています', sid: call.sid });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
};
