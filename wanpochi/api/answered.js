// ポチが鳴らした電話に、親が出たとき（Twilio から）
//  ・留守番電話が出た → 何も言わずに切る（「無事」にしない）
//  ・初日の案内電話 → 使い方を声で伝える
//  ・ふだんの日にうっかり出た → 「元気だね」と言って切る。出たこと自体を「無事」にする
'use strict';
const P = require('../lib/phone');

module.exports = async (req, res) => {
  const c = P.cfg();
  const f = Object.assign({}, req.query || {}, P.form(req));
  const by = String(f.AnsweredBy || '');
  if (by.startsWith('machine') || by === 'fax') {
    console.log('留守番電話が出たので切る:', by);
    return P.xml(res, '<Hangup/>');
  }
  const mode = String((req.query || {}).mode || 'ring');
  if (mode === 'intro') {
    await P.sms(c, '【ワンポチ】' + c.parentName + 'さんが、' + c.petName + 'の案内電話に出ました（' + P.timeJST() + '）。あすから毎朝、電話を鳴らします。');
    const lines = [
      'もしもし、' + c.parentName + 'さん。' + c.petName + 'だよ。はじめまして！',
      'あしたから まいあさ、ちょっとだけ 電話を鳴らすね。出なくて いいよ。',
      '鳴りやんだら、着信履歴から かけ直してね。すぐ切れるけど、それで 大丈夫。お金も かからないよ。',
      'それから、' + c.petName + 'は お名前や 住所、お金や 暗証番号を 聞くことは ぜったいに ないよ。もし聞かれたら、それは ' + c.petName + 'じゃないからね。',
      c.familyName + 'さんに、元気だよって とどくからね。また あした！',
    ];
    return P.xml(res, lines.map(l => P.say(c, l) + '<Pause length="1"/>').join('') + '<Hangup/>');
  }
  await P.sms(c, '【ワンポチ】' + c.parentName + 'さん、きょうも無事です（' + P.timeJST() + '・電話に出ました）');
  P.xml(res, P.say(c, c.parentName + 'さん、' + c.petName + 'だよ。元気だね！' + c.familyName + 'さんに 知らせておくね。また あした！') + '<Hangup/>');
};
