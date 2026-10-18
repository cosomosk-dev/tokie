// 電話に出たあとの台本（Twilio が読みに来る）
'use strict';
const P = require('../lib/phone');

module.exports = async (req, res) => {
  const c = P.cfg();
  const qq = P.questionFor();
  const n = parseInt((req.query && req.query.n) || '0', 10) || 0; // 聞き直しの回数
  const opts = qq.c.map((t, i) => (i + 1) + 'は、' + t).join('。') + '。';
  let body = '';
  if (n === 0) {
    body += P.say(c, 'もしもし、' + c.parentName + 'さん。' + c.petName + 'だよ。' + P.greeting() + '！');
    body += '<Pause length="1"/>';
  }
  body += '<Gather input="dtmf" numDigits="1" timeout="10" action="/api/answer" method="POST">';
  body += P.say(c, (n === 0 ? 'きょうの、いちもん。' : 'もういちど、きくね。') + qq.q);
  body += '<Pause length="1"/>';
  body += P.say(c, opts + 'わからないときは、ゼロを、おしてね。');
  body += '</Gather>';
  if (n < 2) {
    body += '<Redirect method="GET">/api/twiml?n=' + (n + 1) + '</Redirect>';
  } else {
    body += P.say(c, 'また、あとで、かけなおすね。' + c.familyName + 'さんには、つたえておくよ。');
    await P.sms(c, '【ワンポチ】' + c.parentName + 'さんは電話に出ましたが、ボタンが押されませんでした（' + P.timeJST() + '）。一度、様子を聞いてみてください。');
  }
  P.xml(res, body);
};
