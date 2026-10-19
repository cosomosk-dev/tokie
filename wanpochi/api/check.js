// 設定がそろっているかの確認（値は出さない。あるか無いかだけ）
'use strict';
module.exports = (req, res) => {
  const e = process.env;
  const has = k => !!(e[k] && String(e[k]).trim());
  const items = {
    TWILIO_ACCOUNT_SID: has('TWILIO_ACCOUNT_SID'),
    TWILIO_AUTH_TOKEN: has('TWILIO_AUTH_TOKEN'),
    TWILIO_FROM: has('TWILIO_FROM'),
    PARENT_PHONE: has('PARENT_PHONE'),
    FAMILY_PHONE: has('FAMILY_PHONE'),
    CALL_KEY: has('CALL_KEY'),
    PARENT_NAME: e.PARENT_NAME || '（未設定→ふみこ）',
    PET_NAME: e.PET_NAME || '（未設定→ポチ）',
  };
  const need = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_FROM', 'PARENT_PHONE', 'FAMILY_PHONE'];
  const missing = need.filter(k => !items[k]);
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.status(200).send(JSON.stringify({ ready: missing.length === 0, missing, items }, null, 2));
};
