// 親がボタンを押したら、ここに来る（Twilio から POST）
'use strict';
const P = require('../lib/phone');

module.exports = async (req, res) => {
  const c = P.cfg();
  const f = P.form(req);
  const d = String(f.Digits || '');
  const qq = P.questionFor();
  const t = P.timeJST();

  let i = -2;
  if (d === '0') i = -1;
  else if (['1', '2', '3'].includes(d)) i = parseInt(d, 10) - 1;

  if (i === -2) {
    // ちがうボタン → もう一度
    return P.xml(res, P.say(c, 'いち、に、さん、か、ゼロを、おしてね。') + '<Redirect method="GET">/api/twiml?n=1</Redirect>');
  }

  const ans = qq.c[qq.a];
  let line;
  if (i === -1) line = 'わからなくても、だいじょうぶ。こたえは、' + ans + '、だよ。';
  else if (i === qq.a) line = 'せいかい！';
  else line = 'おしい！こたえは、' + ans + '、だよ。';

  const picked = i === -1 ? 'わからない' : qq.c[i];
  const result = i === -1 ? '' : (i === qq.a ? '（せいかい）' : '（こたえは ' + ans + '）');
  await P.sms(c, '【ワンポチ】' + c.parentName + 'さん、きょうも無事です（' + t + '・電話で回答）\nきょうの答え：' + picked + result);

  P.xml(res, P.say(c, line + c.familyName + 'さんに、ぶじを、しらせておくね。また、あしたね！') + '<Hangup/>');
};
