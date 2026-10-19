// ポチが鳴らした電話が終わったときの報告（Twilio から POST）
// 出なかった（no-answer）のは、ふだんどおり。親の折り返しを待つので、家族には何も送らない。
// 本番では「その日に折り返しが無ければ、昼と夕方にもう一度鳴らす」「決めた日数つづいたら家族に知らせる」をサーバーで数える。
'use strict';
const P = require('../lib/phone');

module.exports = async (req, res) => {
  const f = P.form(req);
  console.log('call status:', String(f.CallStatus || ''), 'answeredBy:', f.AnsweredBy || '-', 'duration:', f.CallDuration);
  res.status(200).send('ok');
};
