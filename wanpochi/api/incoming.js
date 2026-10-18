// 親がポチの番号にかけてきたら、ここに来る（Twilio から）
// 電話には出ずに切る（<Reject>）→ 誰にも通話料がかからない。番号で「誰からか」だけ見て、家族に「無事」を知らせる。
'use strict';
const P = require('../lib/phone');

const digits = s => String(s || '').replace(/\D/g, '').slice(-10); // +8190… と 090… を同じに扱う

module.exports = async (req, res) => {
  const c = P.cfg();
  const f = Object.assign({}, req.query || {}, P.form(req));
  const from = String(f.From || '');
  const isParent = c.parentPhone && digits(from) === digits(c.parentPhone);

  // 先に「出ないで切る」を返す（最初の命令が Reject なら課金されない）
  P.xml(res, '<Reject reason="busy"/>');

  if (isParent) {
    await P.sms(c, '【ワンポチ】' + c.parentName + 'さんから、きょうの「ワンポチ」が届きました（' + P.timeJST() + '）。きょうも無事です。');
  } else {
    console.log('知らない番号からの着信（無視）:', from ? from.slice(0, 4) + '…' : '非通知');
  }
};
