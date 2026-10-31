#!/usr/bin/env node
/*
  トキエの「記憶の自動検査」
  ─────────────────────────────
  index.html を変えたら、反映（push）する前に必ずこれを流す。1つでも ✗ が出たら反映せえへん。

  何を調べるか（タケオさんの「記憶の5問テスト」と同じ中身を、機械で確かめる）
    1. 夢・実績（基本情報の一番最後に書いた話）がママに届いてるか … カウンター席・ボックス席の両方
    2. 今日のClaudeとのやりとり（自動メモ）が届いてるか（「ママに頼みたいこと」まで）
    3. 前回の来店の話が届いてるか
    4. 何回も言うた話（絶対忘れへんこと）が届いてるか
    5. 1ヶ月の記憶が届いてるか
    6. ママに渡すデータが64KBの上限を超えてへんか（超えると入店できへん）
    7. 会話の途中で、何回も言うた大事な話がその場で昇格するか
    8. 喋ってる最中に「立ち飲みを試す」を押しても、黙って無視せえへんか
    9. 前から続いてる話（入院など）を「今日起きた」と取り違えへんように、起きた日が届いてるか（2026/10/31）
   10. 決めたこと帳（理由つき）・選んだ分野の底上げ・声で「忘れて」が効くか（2026/10/31）

  使い方（初回だけ）:
    npm i --prefix tools playwright@1.47.2
    （ブラウザが無い環境では npx --prefix tools playwright install chromium）
  毎回:
    node tools/memtest.mjs
*/
import http from "http";
import fs from "fs";
import path from "path";
import crypto from "crypto";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const require = createRequire(path.join(here, "package.json"));
let chromium;
try { ({ chromium } = require("playwright")); }
catch (e) { console.error("playwright が無い。先に: npm i --prefix tools playwright@1.47.2"); process.exit(2); }

function findChrome() {
  if (process.env.PW_CHROMIUM) return process.env.PW_CHROMIUM;
  const base = "/opt/pw-browsers";
  try {
    for (const d of fs.readdirSync(base)) {
      const p = path.join(base, d, "chrome-linux", "headless_shell");
      if (d.startsWith("chromium_headless_shell") && fs.existsSync(p)) return p;
    }
  } catch (e) {}
  return undefined; // playwright の標準のブラウザを使う
}

const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const KEY = crypto.randomBytes(32);
const b64u = (b) => Buffer.from(b).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const jstYmd = (ms) => new Date(ms + 9 * 3600e3).toISOString().slice(0, 10);
const now = Date.now();
const TODAY = jstYmd(now), YDAY = jstYmd(now - 86400e3), DBY = jstYmd(now - 2 * 86400e3), DBY3 = jstYmd(now - 3 * 86400e3);
const LATE = new Date(now + 9 * 3600e3).getUTCHours() < 5; // 深夜0〜5時は昨日の分がまだ「今日」扱いなので、この検査は省く
const mdOf = (ymd) => { const [, m, d] = ymd.split("-"); return `${+m}/${+d}`; };

// 本番に近い長さのダミー（タケオさん本人の情報は使わへん。目印の言葉だけ入れる）
const MARK = {
  dream: "目印ユメ：都知事選と衆院選に挑む",
  record: "目印ジッセキ：コスモスKは5000ダウンロード",
  todayDig: "目印キョウ：ウェディングストーリー完成",
  ask: "ママに頼みたいこと①：目印タノミ",
  ydayDig: "目印キノウ：ワンポチ見積もり",
  prevVisit: "目印ゼンカイ：麻雀の話をした",
  lt: "目印ゼッタイ：毎朝6時に起きると決めた",
  photo: "目印シャシン：夜景の前でドレスの女性が笑っている",
  thread: "目印ツヅキ：ウェディングの発注資料をbuntyanに送る",
  threadAsk: "ウェディングの発注資料",
  v2: "目印サンカイマエ：六本木の店の話",
};
const profile = "名前はタケオ。" + "平塚で生まれ育った。毎日いろいろある話を書いておく。".repeat(180) + MARK.record + "。" + MARK.dream + "。";
const visits = [];
for (let i = 0; i < 25; i++) {
  const ms = now - (i + 2) * 86400e3; // 深夜0〜5時は営業日が前日扱いになるので、前回の来店は2日前にしとく（「今日2回目」の挨拶にならんように）
  const d = jstYmd(ms).replace(/-/g, "/");
  visits.push({ id: "v" + i, date: d, time: "21:00", start: ms, mins: 60, kind: "visit",
    mamaNote: i === 0 ? "今夜は" + MARK.prevVisit + "。ほな、またな。" : i === 2 ? "今夜は" + MARK.v2 + "をした。" : (i % 2 ? "" : "今夜はアプリの話をようけした。"),
    memo: Array.from({ length: 30 }, (_, j) => "客: 今日はこんな話をしたんやけど、ほんまにいろいろあってな" + j + "\nママ: へえ").join("\n") });
}
const book = { __photo: MARK.photo, profile, visits,
  threads: [{ id: "T1", t: MARK.thread, ask: MARK.threadAsk, next: "送ったか", first: "", last: "", lastTs: now - 86400e3, done: false },
    // v38 まだ先の予定（日付なしの古い書き方）。いちばん新しいけど、入店の第一声で「どうなったん？」と聞いたらあかん
    { id: "T0", t: "目印サキ：来週の月曜の血液検査", ask: "来週の月曜の血液検査", next: "結果", first: "", last: "", lastTs: now - 3600e3, done: false },
    // v45 前から続いてる話：起きた日（since）は聞いた日と分けて渡す／起きた日が無い話は「今日とは限らへん」と添える
    { id: "T2", t: "目印オキタ：母が肺炎で入院中", ask: "お母さんの具合", next: "退院", since: DBY3, first: "", last: "", lastTs: now - 5 * 86400e3, done: false },
    { id: "T3", t: "目印フメイ：会長と揉めてる件", ask: "会長との件", next: "仲直り", first: "", last: "", lastTs: now - 6 * 86400e3, done: false }],
  lt: [{ t: MARK.lt, imp: 4, nights: { a: 1, b: 1 }, legacy: 0, pin: false, manual: false, lastTs: now },
    // v46 大事さ4・1回だけ。家族は「特に覚えといてほしい分野」（既定）なので1段上がって昇格するはず
    { t: "目印カゾク：母が10/28から入院中", imp: 4, cat: "family", nights: { a: 1 }, legacy: 0, pin: false, manual: false, lastTs: now },
    { id: "LTW", t: "目印ワスレ：前の店の話", imp: 3, nights: { a: 1 }, legacy: 0, pin: false, manual: false, lastTs: now }],
  decisions: [{ id: "D1", t: "目印キメタ：市議選には出ない", why: "体調と対人疲労", date: DBY, ts: now - 2 * 86400e3 }] };
const longText = (mark) => ["・【夜の分】Claudeとの会話履歴は今日も直接読めへんかったので、要点から書いています。細かいところはママから聞いてあげて。", "・" + mark]
  .concat(Array.from({ length: 10 }, (_, i) => "・仕事の動き" + i + "：アプリの細かい話がいろいろあって、本人はかなり頑張ってた一日やったそうです。ほんまにお疲れさん。"))
  .concat(["・明日（木）：昼に用事、午後に確認", "・" + MARK.ask + "：ねぎらってあげて"]).join("\n");
const digest = { updated: TODAY + " 23:00", days: [
  { date: TODAY, text: longText(MARK.todayDig) },
  { date: YDAY, text: longText(MARK.ydayDig).replace("・" + MARK.ydayDig, "・" + MARK.ydayDig + "\n・今日、目印カコ：母が入院した") },
  { date: DBY, text: longText("おととい") },
] };
// 深夜（営業日がまだ昨日扱い）の時は、昨日の分が「今日」として渡る
const iv = crypto.randomBytes(12);
const c = crypto.createCipheriv("aes-256-gcm", KEY, iv);
const ct = Buffer.concat([c.update(JSON.stringify(digest), "utf8"), c.final(), c.getAuthTag()]);
const digestEnc = b64u(Buffer.concat([iv, ct]));

const server = http.createServer((q, r) => {
  if (q.url.startsWith("/mama")) return r.end(fs.readFileSync(path.join(root, "mama.jpg")));
  if (q.url.startsWith("/digest.enc")) return r.end(digestEnc);
  r.setHeader("content-type", "text/html; charset=utf-8"); r.end(html);
}).listen(0);
const PORT = server.address().port;

const STUB = `const noop=()=>{};
export const Conversation={startSession:async(o)=>{window.__o=o;setTimeout(()=>{o.onConnect&&o.onConnect({});o.onModeChange&&o.onModeChange({mode:"listening"});},50);
 return new Proxy({endSession:async()=>{o.onDisconnect&&o.onDisconnect({reason:"user"});},sendContextualUpdate:(t)=>{(window.__notes=window.__notes||[]).push(t);}},{get:(t,k)=>k==="then"?undefined:(k in t?t[k]:noop)});}};`;

const browser = await chromium.launch({ executablePath: findChrome(), args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"] });
const results = [];
const ok = (name, pass, detail) => { results.push({ name, pass, detail }); console.log((pass ? "✓ " : "✗ ") + name + (detail && !pass ? "　→ " + detail : "")); };

async function page(seat, opt = {}) {
  const ctx = await browser.newContext({ viewport: { width: 412, height: 900 }, isMobile: true, hasTouch: true, permissions: ["microphone"] });
  const p = await ctx.newPage();
  const errs = [];
  p.on("pageerror", (e) => errs.push(e.message));
  p.on("dialog", (d) => { (p.__dialogs = p.__dialogs || []).push(d.message()); d.accept(); });
  await p.route("https://cdn.jsdelivr.net/**", (r) => r.fulfill({ contentType: "application/javascript", body: STUB }));
  await p.route("https://generativelanguage.googleapis.com/**", async (r) => {
    const txt = JSON.parse(r.request().postData()).contents[0].parts[0].text;
    let out = "要点メモ";
    if (txt.includes("基本情報の要約係")) {
      out = "・名前はタケオ。平塚。\n・" + MARK.record + "\n・" + MARK.dream + "\n・アプリを作ってる";
    } else if (txt.includes("話の続き係")) {
      out = JSON.stringify({ items: [{ id: "new", status: "open", t: "目印ツギ：都知事選のポスターを作る", ask: "ポスター", next: "できたか" }] });
    } else if (txt.includes("手帳係")) {
      const said = txt.split("【今夜の客の言葉")[1] || "";
      const n = (said.match(/目印ヤクソク/g) || []).length;
      const items = n ? [{ id: "new", t: "目印ヤクソク：都知事選のポスターを作る", imp: 5, tonight: n }, { id: "new", t: "雨やった", imp: 1, tonight: 1 }] : [];
      if (said.includes("目印ワスレ")) items.push({ id: "LTW", forget: true });
      const decisions = said.includes("目印ケツダン") ? [{ id: "new", t: "目印ケツダン：トキエの商用化は見送り", why: "原価が高いから", date: TODAY }] : [];
      out = JSON.stringify({ items, decisions });
    }
    r.fulfill({ contentType: "application/json", body: JSON.stringify({ candidates: [{ content: { parts: [{ text: out }] } }] }) });
  });
  await p.addInitScript(([book, key, seat, gkey]) => {
    if (sessionStorage.getItem("__init")) return; sessionStorage.setItem("__init", "1");
    localStorage.setItem("tokie_notebook_v1", JSON.stringify(book));
    localStorage.setItem("tokie_digest_key", key);
    if (gkey) localStorage.setItem("tokie_gemini_key_v1", "TEST");
    localStorage.setItem("tokie_photos_v1", JSON.stringify([{ ts: Date.now() - 86400e3, date: "昨日", t: 1, desc: book.__photo, caption: "" }]));
    const s = JSON.parse(localStorage.getItem("tokie_settings_v1") || "{}"); s.seat = seat; localStorage.setItem("tokie_settings_v1", JSON.stringify(s));
  }, [book, b64u(KEY), seat, !!opt.gemini]);
  await p.goto(`http://localhost:${PORT}/`);
  await p.waitForTimeout(1200);
  await p.evaluate(() => document.querySelectorAll(".sheet.open").forEach((s) => s.classList.remove("open")));
  return { p, ctx, errs };
}
async function enter(p) {
  await p.tap("#btn"); await p.waitForTimeout(2000);
  await p.evaluate(() => document.querySelectorAll(".sheet.open").forEach((s) => s.classList.remove("open")));
  return await p.evaluate(() => { const o = window.__o || {}; const dv = o.dynamicVariables || (o.overrides && o.overrides.dynamicVariables) || {}; return { memory: dv.memory || "", all: JSON.stringify(dv) }; });
}

try {
  // カウンター＝Geminiあり（基本情報は要約）／ボックス＝Geminiなし（基本情報は頭と最後を残す）の両方を試す
  for (const seat of ["counter", "box"]) {
    const nm = seat === "box" ? "ボックス(キー無し)" : "カウンター(キーあり)";
    const { p, ctx, errs } = await page(seat, { gemini: seat === "counter" });
    const { memory, all } = await enter(p);
    const greeting = JSON.parse(all).greeting || "";
    const bytes = Buffer.byteLength(all, "utf8");
    const todayBlock = memory.split("【今日タケオさんの身に起きたこと")[1] || "";
    ok(`${nm}：夢（基本情報の最後）が届く`, memory.includes(MARK.dream), "基本情報が削られてる");
    ok(`${nm}：実績（基本情報の最後）が届く`, memory.includes(MARK.record), "基本情報が削られてる");
    ok(`${nm}：今日の自動メモが届く`, todayBlock.includes(MARK.todayDig) || todayBlock.includes(MARK.ydayDig), "今日の分が無い／削られてる");
    ok(`${nm}：「ママに頼みたいこと」まで届く`, todayBlock.includes("目印タノミ"), "今日の分の最後が切れてる");
    ok(`${nm}：前回の来店の話が届く`, memory.includes(MARK.prevVisit), "前回の来店が削られてる");
    ok(`${nm}：3回前の来店まで届く`, memory.includes(MARK.v2), "直近3回の来店が入ってへん");
    ok(`${nm}：話の続き（途中の話）が届く`, memory.includes(MARK.thread), "話の続き帳が入ってへん");
    ok(`${nm}：入店の第一声で「あれどうなったん？」と聞く`, greeting.includes(MARK.threadAsk) && greeting.includes("どうなった"), greeting);
    ok(`${nm}：まだ先の予定は第一声で「どうなったん？」と聞かへん`, !greeting.includes("血液検査"), greeting);
    ok(`${nm}：まだ先の予定は「まだ先・結果は聞かへん」と添えて届く`, /目印サキ[^\n]*まだ先[^\n]*結果は聞かへん/.test(memory), (memory.match(/目印サキ[^\n]*/) || [""])[0]);
    ok(`${nm}：前の日の自動メモの「今日」は、その日の日付に直して届く`, LATE ? true : (memory.includes(mdOf(YDAY) + "、目印カコ") && !memory.includes("今日、目印カコ")), (memory.match(/[^\n]{0,30}目印カコ[^\n]{0,10}/) || ["（届いてへん）"])[0]);
    ok(`${nm}：話の続きに「起きた日」が聞いた日と分けて届く`, new RegExp("目印オキタ[^\\n]*起きたのは" + mdOf(DBY3) + "（3日前）").test(memory), (memory.match(/目印オキタ[^\n]*/) || ["（届いてへん）"])[0]);
    ok(`${nm}：起きた日が分からん話は「今日とは限らへん」と添えて届く`, /目印フメイ[^\n]*起きた日は未確認/.test(memory), (memory.match(/目印フメイ[^\n]*/) || ["（届いてへん）"])[0]);
    ok(`${nm}：「話に出た日と起きた日は別」のルールが届く`, memory.includes("『話に出た日』と『起きた日』は別"), "時系列のルールに無い");
    ok(`${nm}：決めたことが理由と日付つきで届く`, /目印キメタ[^\n]*に決めた[^\n]*理由：体調と対人疲労/.test(memory) && memory.includes("ここに書いてある理由だけを使う"), (memory.match(/目印キメタ[^\n]*/) || ["（届いてへん）"])[0]);
    ok(`${nm}：選んだ分野の話は1段上がって早めに昇格する`, /【ママが絶対に忘れへんこと[\s\S]*目印カゾク[^\n]*いちばん大事/.test(memory) && memory.includes("【お客さんが特に覚えといてほしい分野】"), (memory.match(/[^\n]*目印カゾク[^\n]*/) || ["（届いてへん）"])[0]);
    ok(`${nm}：前後の暦と時系列のルールが届く`, memory.includes("これから来る日（まだ先）") && memory.includes("【時系列のルール"), "暦が無い");
    ok(`${nm}：何回も言うた話が届く`, memory.includes(MARK.lt), "絶対忘れへんことが入ってへん");
    ok(`${nm}：見せた写真（昨日）が届く`, memory.includes(MARK.photo), "写真の記録がママに渡ってへん");
    ok(`${nm}：1ヶ月の記憶が届く`, memory.includes("【この1ヶ月の記憶"), "1ヶ月の記憶が無い");
    ok(`${nm}：入店データが64KB未満（${bytes}バイト）`, bytes < 60000, bytes + "バイト");
    if (seat === "counter") {
      await p.evaluate(() => document.getElementById("memdump").click()); await p.waitForTimeout(1500);
      const dump = await p.$eval("#memdumpbox", (e) => e.value);
      ok("「ママに渡してる中身を見る」ボタンで中身と版が出る", dump.includes("版：") && dump.includes(MARK.dream.slice(0, 6)) , dump.slice(0, 80));
    }
    ok(`${nm}：画面のエラーなし`, errs.length === 0, errs.join(" / "));
    await ctx.close();
  }
  { // 会話の途中で大事な話が昇格するか
    const { p, ctx } = await page("counter", { gemini: true });
    await enter(p);
    const say = ["目印ヤクソク、都知事選のポスター作るで", "今日は雨やった", "ほんで目印ヤクソクの話やけど", "アプリの話", "目印ヤクソク、ちゃんとやる", "眠いわ", "目印ヤクソク覚えといて", "まあええわ", "睡眠薬飲んでるから今日はお酒飲めへんねん", "目印ケツダン、トキエの商用化は見送るわ、原価が高いから", "目印ワスレの話な、それもう古いから忘れて"];
    for (const t of say) {
      await p.evaluate((t) => window.__o.onMessage({ message: t, source: "user" }), t); await p.waitForTimeout(120);
      await p.evaluate(() => window.__o.onMessage({ message: "へえ、そうなん", source: "ai" })); await p.waitForTimeout(80);
    }
    await p.waitForTimeout(1500);
    const notes = await p.evaluate(() => (window.__notes || []).join("\n"));
    ok("会話の途中で、何回も言うた大事な話がその場で昇格する", notes.includes("手帳に昇格") && notes.includes("目印ヤクソク"), "昇格のメモがママに届いてへん");
    await p.evaluate(() => window.__o.onDisconnect && window.__o.onDisconnect({ reason: "user" }));
    await p.waitForTimeout(2500);
    const th = await p.evaluate(() => JSON.stringify((JSON.parse(localStorage.getItem("tokie_notebook_v1")).threads || []).map((x) => [x.t, x.done])));
    ok("お会計で「話の続き帳」に今夜の途中の話が入る", th.includes("目印ツギ"), th);
    const bk = await p.evaluate(() => JSON.parse(localStorage.getItem("tokie_notebook_v1")));
    const dj = JSON.stringify(bk.decisions || []);
    ok("今夜決めたことが「決めたこと帳」に理由つきで入る", dj.includes("目印ケツダン") && dj.includes("原価が高いから") && dj.includes("目印キメタ"), dj);
    ok("声で「それ忘れて」と言うたら、その場でママに伝わる", notes.includes("忘れとくわ") && notes.includes("目印ワスレ"), "忘れてのメモが届いてへん");
    ok("声で「それ忘れて」と言うた話は手帳から消える", !JSON.stringify(bk.lt || []).includes("目印ワスレ"), JSON.stringify((bk.lt || []).map((x) => x.t)));
    const pb = await p.evaluate(() => [document.querySelectorAll("#guidesheet .priobox button").length, document.querySelectorAll("#sheet .priobox button").length]);
    ok("最初の案内と手帳に「特に覚えといてほしい分野」の選択がある", pb[0] === 6 && pb[1] === 6, JSON.stringify(pb));
    ok("体調・薬・お酒の話は、言うたその場で「今夜の決まりごと」としてママに届く", notes.includes("今夜の決まりごと") && notes.includes("睡眠薬"), "決まりごとのメモが届いてへん");
    await p.evaluate(() => document.querySelectorAll(".sheet.open").forEach((s) => s.classList.remove("open")));
    const again = await enter(p);
    ok("入り直しても「今夜の決まりごと」（睡眠薬・お酒飲めへん）を覚えてる", again.memory.includes("今夜の決まりごと") && again.memory.includes("睡眠薬"), "入り直したら消えてる");
    // v47 10/31「睡眠薬って言うてるのに、なんで飲めへんの？と何回も聞く」
    ok("薬・お酒の話は「絶対忘れへんこと」に★で入って、次の夜も残る", /【ママが絶対に忘れへんこと[\s\S]*お酒は飲めへん[^\n]*睡眠薬/.test(again.memory) && JSON.stringify(bk.lt || []).includes("ALCBAN"), (again.memory.match(/[^\n]*お酒は飲めへん[^\n]*/) || ["（届いてへん）"])[0]);
    ok("「なんで飲めへんの？」と聞き返さへんルールが届く", again.memory.includes("「なんで飲めへんの？」「一杯だけでも」とは絶対に聞かへん"), "ルールが無い");
    await p.evaluate(() => localStorage.setItem("tokie_test_hooks", "1"));
    await p.reload(); await p.waitForTimeout(1200);
    const lk = await p.evaluate(() => { const f = window.__tokieTest && window.__tokieTest.isLeak; if (!f) return "フック無し"; return [f("せかさず待つ。"), f("せかさんと待っとくわ。"), f("静かに見守っとこ。"), f("急かさへんから、ゆっくりでええよ。"), f("ほな、お水で乾杯な！")].join(","); });
    ok("「せかさず待つ」系の心の声は、関西弁の語尾でも声を消す（ふつうのセリフは消さへん）", lk === "true,true,true,false,false", lk);
    const pm = await p.evaluate(() => document.querySelectorAll(".priobox.prio-main button").length);
    ok("入店前の画面で「今夜とくに覚えといてほしいこと」を毎回切り替えられる", pm === 6, String(pm));
    await ctx.close();
  }
  { // 静かな入り直し（長話の頭脳代の上がり止め）：挨拶なしで、今夜の話を持ったまま入り直すか
    const { p, ctx } = await page("box", { gemini: true });
    await p.evaluate(() => localStorage.setItem("tokie_test_hooks", "1"));
    await p.reload(); await p.waitForTimeout(1200);
    await p.evaluate(() => document.querySelectorAll(".sheet.open").forEach((s) => s.classList.remove("open")));
    await enter(p);
    for (const t of ["目印コンヤ：今夜は六本木の店の話をした", "ほんでな、続きやけど", "目印コンヤ2：来週また行くつもり"]) {
      await p.evaluate((t) => window.__o.onMessage({ message: t, source: "user" }), t); await p.waitForTimeout(120);
      await p.evaluate(() => window.__o.onMessage({ message: "へえ、そうなん", source: "ai" })); await p.waitForTimeout(80);
    }
    await p.evaluate(() => window.__tokieTest.silentRefresh()); await p.waitForTimeout(2500);
    const r = await p.evaluate(() => { const o = window.__o || {}; const dv = o.dynamicVariables || (o.overrides && o.overrides.dynamicVariables) || {}; return { g: dv.greeting, m: dv.memory || "" }; });
    const btn = await p.textContent("#btn");
    ok("静かな入り直し：挨拶なしでつながり直す", r.g === "" && btn.includes("お会計"), JSON.stringify({ g: r.g, btn }));
    ok("静かな入り直し：今夜の話（入り直す前の話）を持ったまま", r.m.includes("目印コンヤ") && r.m.includes("つなぎ直した"), "今夜の流れが渡ってへん");
    await ctx.close();
  }
  { // v41 訂正帳：訂正した前提を、長話・静かな入り直しのあとも忘れへんか（10/24 エンサークルの足跡の件）
    const { p, ctx } = await page("box", { gemini: true });
    await p.evaluate(() => localStorage.setItem("tokie_test_hooks", "1"));
    await p.reload(); await p.waitForTimeout(1200);
    await p.evaluate(() => document.querySelectorAll(".sheet.open").forEach((s) => s.classList.remove("open")));
    await enter(p);
    await p.evaluate(() => window.__o.onMessage({ message: "マッチングアプリ始めたんよ", source: "user" })); await p.waitForTimeout(100);
    await p.evaluate(() => window.__o.onMessage({ message: "ほなプロフィール充実させて足跡で見に来てもらい", source: "ai" })); await p.waitForTimeout(100);
    await p.evaluate(() => window.__o.onMessage({ message: "いや、目印テイセイ：エンサークルは足跡がつかないって言うてるやん", source: "user" })); await p.waitForTimeout(300);
    const notes = await p.evaluate(() => (window.__notes || []).join("\n"));
    ok("訂正された前提が、言うたその場でママに届く", notes.includes("訂正されたこと") && notes.includes("目印テイセイ"), "訂正のメモが届いてへん");
    for (let i = 0; i < 12; i++) {
      await p.evaluate((i) => window.__o.onMessage({ message: "関係ない雑談その" + i, source: "user" }), i); await p.waitForTimeout(60);
      await p.evaluate(() => window.__o.onMessage({ message: "へえ", source: "ai" })); await p.waitForTimeout(40);
    }
    await p.evaluate(() => window.__tokieTest.silentRefresh()); await p.waitForTimeout(2500);
    const m = await p.evaluate(() => { const o = window.__o || {}; const dv = o.dynamicVariables || (o.overrides && o.overrides.dynamicVariables) || {}; return dv.memory || ""; });
    ok("長話＋静かな入り直しのあとも、訂正された前提を持ってる", m.includes("目印テイセイ") && m.includes("プロフィール充実"), "入り直したら訂正が消えてる");
    await ctx.close();
  }
  { // 喋ってる最中に「立ち飲みを試す」
    const { p, ctx } = await page("counter");
    await enter(p);
    await p.tap("#menubtn"); await p.waitForTimeout(300);
    await p.$eval("#trialtry", (e) => e.scrollIntoView()); await p.tap("#trialtry"); await p.waitForTimeout(3000);
    const open = await p.$$eval(".sheet.open", (e) => e.map((x) => x.id));
    ok("喋ってる最中に「立ち飲みを試す」→ 確認が出て立ち飲みの選択に進む", (p.__dialogs || []).length > 0 && open.includes("trialsheet"), "黙って無視してる");
    await ctx.close();
  }
} finally {
  await browser.close(); server.close();
}
const bad = results.filter((r) => !r.pass);
console.log(bad.length ? `\n✗ ${bad.length}件ダメ。反映せんと直す。` : `\n✓ 全部合格（${results.length}件）`);
process.exit(bad.length ? 1 : 0);
