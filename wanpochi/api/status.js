// 電話が終わったときの報告（Twilio から POST）。出なかった・話し中なら家族に知らせる
'use strict';
const P = require('../lib/phone');

module.exports = async (req, res) => {
  const c = P.cfg();
  const f = P.form(req);
  const st = String(f.CallStatus || '');
  console.log('call status:', st, 'duration:', f.CallDuration);
  if (['no-answer', 'busy', 'failed', 'canceled'].includes(st)) {
    await P.sms(c, '【ワンポチ】' + c.parentName + 'さんは電話に出ませんでした（' + P.timeJST() + '）。時間をおいて、もう一度かけてみてください。');
  }
  res.status(200).send('ok');
};
