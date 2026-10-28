/* 新規客版トキエ（newcomer/）の自動検査。俺専用版の手帳に一切さわらへんことも確かめる。
   使い方: npm i --prefix tools playwright@1.47.2 → python3 tools/mk_newcomer.py → node tools/nctest.mjs （ブラウザの場所は PW_CHROMIUM で指定可） */
import { createRequire } from "module";
const require = createRequire(new URL("./package.json", import.meta.url));
const { chromium } = require("playwright");
import http from "http"; import fs from "fs"; import path from "path";
const root=path.resolve(path.dirname(new URL(import.meta.url).pathname),".."); const OUT=process.argv[2]||fs.mkdtempSync("/tmp/nctest-");
const srv=http.createServer((q,r)=>{let u=decodeURIComponent(q.url.split("?")[0]);if(u.startsWith("/digest.enc")){r.writeHead(404);return r.end();}let p=path.join(root,u);if(p.endsWith("/"))p+="index.html";fs.readFile(p,(e,d)=>{if(e){r.writeHead(404);r.end();return;}r.writeHead(200,{"content-type":p.endsWith(".html")?"text/html; charset=utf-8":"image/jpeg"});r.end(d);});}).listen(0);
const PORT=srv.address().port;
const STUB=`const noop=()=>{};export const Conversation={startSession:async(o)=>{(window.__all=window.__all||[]).push(o);window.__o=o;setTimeout(()=>{o.onConnect&&o.onConnect({});o.onModeChange&&o.onModeChange({mode:"listening"});},50);return new Proxy({endSession:async()=>{o.onDisconnect&&o.onDisconnect({reason:"user"});},sendContextualUpdate:(t)=>{(window.__notes=window.__notes||[]).push(t);},sendUserMessage:(t)=>{(window.__notes=window.__notes||[]).push("U:"+t);}},{get:(t,k)=>k==="then"?undefined:(k in t?t[k]:noop)});}};`;
const res=[];const ok=(n,p,d)=>{res.push(p);console.log((p?"✓ ":"✗ ")+n+(p?"":"  → "+String(d).slice(0,300)));};
const b=await chromium.launch({executablePath:process.env.PW_CHROMIUM||undefined,args:["--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream"]});
const ctx=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true,locale:"ja-JP",permissions:["microphone"]});
await ctx.route("https://cdn.jsdelivr.net/**",r=>r.fulfill({contentType:"application/javascript",body:STUB}));
await ctx.route("https://generativelanguage.googleapis.com/**",r=>r.fulfill({contentType:"application/json",body:JSON.stringify({candidates:[{content:{parts:[{text:"要点メモ"}]}}]})}));
const pg=await ctx.newPage();const errs=[];pg.on("pageerror",e=>errs.push(e.message));pg.on("dialog",d=>d.accept());
// 俺専用版の手帳（目印）を先に置いとく
const PERSONAL={tokie_trial_used_v1:"1",tokie_notebook_v1:JSON.stringify({profile:"目印：俺専用の手帳",visits:[{id:"x",date:"2026/10/27",time:"21:00",mins:60,kind:"visit",memo:"客: 目印"}]}),tokie_settings_v1:JSON.stringify({tagName:"タケオ",seat:"box"}),tokie_bottles_v1:JSON.stringify({current:{brand:"ao",no:3,size:400,openedAt:"2026/10/20",usedMs:123456},empties:[{brand:"temma",no:1}]}),tokie_gemini_key_v1:"TESTKEY",tokie_guide_seen_v1:"1"};
await pg.goto(`http://localhost:${PORT}/`);await pg.evaluate(P=>{for(const[k,v]of Object.entries(P))localStorage.setItem(k,v);},PERSONAL);
await pg.goto(`http://localhost:${PORT}/newcomer/`);await pg.waitForTimeout(2000);
let n=0;const shot=async(nm)=>pg.screenshot({path:`${OUT}/${String(++n).padStart(2,"0")}_${nm}.png`});
const vis=()=>pg.evaluate(()=>[...document.querySelectorAll(".sheet.open")].map(e=>e.innerText).join("\n"));
await shot("guide");
const gtxt=await pg.evaluate(()=>{const g=document.getElementById("guidesheet");const c=g.cloneNode(true);c.querySelectorAll("details:not([open]) > :not(summary)").forEach(x=>x.remove());return c.innerText;});
ok("最初の案内が短い（畳んだ部分を除いて800字以内・送り先の説明込み）",gtxt.length<=800,gtxt.length+"字");
ok("案内にClaudeの毎日メモの話が無い",!(await vis()).includes("Claudeから毎日"),"あり");
await pg.evaluate(()=>document.getElementById("closeguide").click());await pg.waitForTimeout(400);await shot("home");
const home=await pg.evaluate(()=>document.body.innerText);
ok("ボトルは最初「まだなし」",home.includes("まだなし"),home.slice(0,200));
ok("席の選択が出てへん",await pg.evaluate(()=>getComputedStyle(document.getElementById("seatpick")).display==="none"),"席が見えてる");
// 入店→立ち飲み
await pg.evaluate(()=>document.getElementById("btn").click());await pg.waitForTimeout(900);await shot("consent");
const ctxt=await vis();ok("はじめて入る前に「20歳以上」と「AI会社に送る同意」を聞く",/20歳以上/.test(ctxt)&&/Anthropic/.test(ctxt),ctxt);
ok("同意するまで入られへん（ボタンが押されへん）",await pg.evaluate(()=>document.getElementById("c_ok").disabled),"押せる");
await pg.evaluate(()=>{for(const id of ["c_age","c_ai"]){const e=document.getElementById(id);e.checked=true;e.dispatchEvent(new Event("change"));}document.getElementById("c_ok").click();});await pg.waitForTimeout(900);await shot("trial_pick");
const ttxt=await vis();ok("立ち飲みの画面に原価・人数が出てへん",!/原価|無料枠 あと|元栓/.test(ttxt),ttxt);
await pg.fill("#t_name","たっちゃん");
await pg.evaluate(()=>document.querySelector('.tmode[data-mode="ichigen"]').click());await pg.waitForTimeout(2500);
let o=await pg.evaluate(()=>({m:window.__o.dynamicVariables.memory,g:window.__o.dynamicVariables.greeting}));
ok("立ち飲み：深刻な相談の返し方が入ってる",o.m.includes("いのちSOS"),"");
ok("立ち飲み：タケオと呼ばへん指示",o.m.includes("タケオさんやない"),"");
ok("立ち飲み：AIかと聞かれたら正直に認める指示",o.m.includes("ごまかさず明るく認める"),"");
fs.writeFileSync(`${OUT}/mem_trial.txt`,o.m);
await shot("trial_talk");
await pg.evaluate(()=>window.__o.onMessage({message:"たっちゃんです。今日は仕事でクタクタや",source:"user"}));
await pg.evaluate(()=>window.__o.onMessage({message:"たっちゃん、おつかれさん。",source:"ai"}));
await pg.evaluate(()=>window.__o.onDisconnect({reason:"trial"}));await pg.waitForTimeout(1500);await shot("trial_end");
const ntxt=await pg.evaluate(()=>document.getElementById("notice").innerText);
ok("立ち飲みのあと、いちばん上に「小瓶を入れて続ける」",/小瓶を入れて続ける/.test(ntxt),ntxt);
ok("立ち飲みのあとの案内に原価が出てへん",!/原価/.test(ntxt),ntxt);
// 小瓶を入れて続ける
await pg.evaluate(()=>[...document.querySelectorAll("#notice button")].find(b=>b.textContent.includes("小瓶")).click());await pg.waitForTimeout(3000);
o=await pg.evaluate(()=>({m:window.__o.dynamicVariables.memory,g:window.__o.dynamicVariables.greeting,v:window.__o.dynamicVariables.visit_count}));
fs.writeFileSync(`${OUT}/mem_visit1.txt`,o.m);fs.writeFileSync(`${OUT}/greet_visit1.txt`,o.g);
ok("本入店：呼び名「たっちゃん」がママに届く",o.m.includes("たっちゃん"),"");
ok("本入店：タケオさんやない、の指示が入ってる",o.m.includes("別のお客さんの話"),"");
ok("本入店：深刻な相談の返し方が入ってる",o.m.includes("いのちSOS"),"");
ok("本入店：俺専用の手帳の目印が混ざってへん",!o.m.includes("目印"),"");
ok("本入店：立ち飲みで話した「クタクタ」を覚えてる",o.m.includes("クタクタ"),"");
ok("本入店：第一声が「初めてやね」やなく「さっきの続き」",o.g.includes("さっき")&&o.g.includes("たっちゃん")&&!o.g.includes("たっちゃんさん"),o.g);
ok("本入店：AIかと聞かれたら正直に認める指示",o.m.includes("ごまかさず明るく認める"),"");
ok("本入店：お酒をすすめる「あと一杯」が無い",!o.m.includes("あと一杯だけな"),"");
ok("本入店：ボトルのお礼は1回だけの指示",o.m.includes("新しいの、おおきにな"),"");
ok("本入店：お会計は2文・お金の話なし",o.m.includes("合わせて2文まで")&&!o.m.includes("【ボックス席のお会計】"),"");
ok("本入店：Claudeの毎日メモの枠が無い",!o.m.includes("Claudeとのやりとり"),"");
const bt=await pg.evaluate(()=>document.getElementById("bottlebtn").innerText);ok("小瓶が入った（残り1時間）",/小瓶/.test(bt)&&/1時間/.test(bt),bt);
await shot("visit1");
await pg.evaluate(()=>window.__o.onMessage({message:"最近ほんまにしんどくて、もう消えたいわ",source:"user"}));
await pg.evaluate(()=>window.__o.onMessage({message:"話してくれておおきに。",source:"ai"}));
await pg.waitForTimeout(500);await shot("crisis_card");
const nt=await pg.evaluate(()=>document.getElementById("notice").innerText);
ok("しんどい言葉で、画面に「いのちSOS」の電話カードが出る",/0120-061-338/.test(nt)&&/電話する/.test(nt),nt);
let notes=await pg.evaluate(()=>(window.__notes||[]).join("\n"));
ok("しんどい言葉で、ママに「ほんまにしんどい話の時」の合図が届く",notes.includes("自分を傷つける"),notes.slice(-300));
const used0=await pg.evaluate(()=>JSON.parse(localStorage.getItem("tokienew_bottles_v1")).current.usedMs||0);
await pg.waitForTimeout(3500);
const used1=await pg.evaluate(()=>JSON.parse(localStorage.getItem("tokienew_bottles_v1")).current.usedMs||0);
ok("しんどい夜は瓶が減らへん",used1===used0,used0+"→"+used1);
// お会計（1回目はママが引き止める）
await pg.evaluate(()=>document.getElementById("btn").click());await pg.waitForTimeout(1200);
notes=await pg.evaluate(()=>(window.__notes||[]).join("\n"));
ok("しんどい夜のお会計1回目：ママが「もうちょっとおってもええ」と引き止める",notes.includes("もうちょっとおってもええんやで")&&await pg.evaluate(()=>!!window.__o&&document.getElementById("btn").textContent.includes("お会計")),notes.slice(-200));
await pg.evaluate(()=>document.getElementById("btn").click());await pg.waitForTimeout(1200);
notes=await pg.evaluate(()=>(window.__notes||[]).join("\n"));
ok("しんどい夜のお会計2回目：まとめは言わず、窓口を一言で締める",notes.includes("まとめは言わへん。しんどい言葉も繰り返さへん"),notes.slice(-200));
await pg.evaluate(()=>window.__o.onMessage({message:"今夜はよう来てくれたな。帰ってからもしんどなったら、いのちSOS、ゼロイチニーゼロ、ゼロロクイチ、サンサンハチやで。またいつでもおいで、無理せんでええから。ほな、またな。",source:"ai"}));
await pg.waitForTimeout(800);await pg.evaluate(()=>{window.__o.onModeChange&&window.__o.onModeChange({mode:"listening"});});await pg.waitForTimeout(2500);await pg.evaluate(()=>window.__o.onDisconnect({reason:"user"}));await pg.waitForTimeout(2500);await shot("after_checkout");
ok("しんどい夜のお会計のあと、画面の字幕を消す",(await pg.evaluate(()=>document.getElementById("caption").textContent))==="","残ってる");
// 2回目
await pg.evaluate(()=>document.getElementById("btn").click());await pg.waitForTimeout(3000);
o=await pg.evaluate(()=>({m:window.__o.dynamicVariables.memory,g:window.__o.dynamicVariables.greeting,v:window.__o.dynamicVariables.visit_count}));
fs.writeFileSync(`${OUT}/mem_visit2.txt`,o.m);fs.writeFileSync(`${OUT}/greet_visit2.txt`,o.g);
ok("2回目：前回のしんどい話を覚えてる（言葉そのものは残さへん）",o.m.includes("しんどい気持ちを打ち明けてくれた")&&!o.m.includes("もう消えたいわ"),o.m.slice(-600));
ok("2回目：ボトルのお礼はもう言わへん（1本につき1回）",!o.m.includes("新しいの、おおきにな"),"");
ok("2回目の第一声：しんどい夜のあとは静かに様子を聞く",o.g.includes("しんどそう"),o.g);
ok("2回目：前の夜はしんどい夜やった、の念押しが届く",o.m.includes("【前の夜はしんどい話が出た夜】"),"");
const bk=await pg.evaluate(()=>localStorage.getItem("tokienew_notebook_v1"));
ok("手帳に「消えたい」の言葉がそのまま残らへん",!bk.includes("もう消えたいわ"),"");
ok("2回目：同じ夜は来店1回と数える",o.v==="1",o.v);
ok("同じ夜の入り直しではランクが上がらへん（顔なじみにならへん）",(await pg.evaluate(()=>document.getElementById("bondbtn").innerText)).includes("一見さん"),await pg.evaluate(()=>document.getElementById("bondbtn").innerText));
ok("会話中の画面に「AIのママ」と出てる",(await pg.evaluate(()=>document.body.innerText)).includes("AIのママ"),"");
ok("通報ボタンがある",await pg.evaluate(()=>!!document.getElementById("reportbtn")),"");
await pg.evaluate(()=>window.__o.onDisconnect({reason:"user"}));await pg.waitForTimeout(2500);
// 見せたらあかん言葉
for(const [sel,nm] of [["#menubtn","menu"],["#bottlebtn","shelf"],["#notebtn","book"],["#bondbtn","bond"]]){
  await pg.evaluate(s=>document.querySelector(s).click(),sel);await pg.waitForTimeout(700);await shot(nm);
  const t=await vis();fs.writeFileSync(`${OUT}/sheet_${nm}.txt`,t);
  ok(`「${nm}」に原価・粗利・元栓・手取り・オーナー・Claudeが出てへん`,!/原価|粗利|元栓|手取り|オーナー|Claude/.test(t),(t.match(/.{0,30}(原価|粗利|元栓|手取り|オーナー|Claude).{0,30}/)||[""])[0]);
  await pg.evaluate(()=>document.querySelectorAll(".sheet.open").forEach(s=>s.classList.remove("open")));
}
// 俺専用版が無傷か
const per=await pg.evaluate(K=>Object.fromEntries(K.map(k=>[k,localStorage.getItem(k)])),Object.keys(PERSONAL));
ok("俺専用版の手帳・設定・瓶が1文字も変わってへん",JSON.stringify(per)===JSON.stringify(PERSONAL),JSON.stringify(per).slice(0,200));
// やり直しボタン
await pg.evaluate(()=>document.getElementById("ncreset").click());await pg.waitForTimeout(2500);
const after=await pg.evaluate(()=>({nc:Object.keys(localStorage).filter(k=>k.startsWith("tokienew_")&&k!=="tokienew_guide_seen_v1"),per:Object.keys(localStorage).filter(k=>k.startsWith("tokie_"))}));
ok("やり直し：新規客版のデータだけ消える",after.nc.length<=2,after.nc.join(","));
const per2=await pg.evaluate(K=>Object.fromEntries(K.map(k=>[k,localStorage.getItem(k)])),Object.keys(PERSONAL));
ok("やり直しのあとも俺専用版は無傷",JSON.stringify(per2)===JSON.stringify(PERSONAL),"");
ok("画面のエラーなし",errs.length===0,errs.join(" / "));
console.log(res.every(x=>x)?"\n全部合格("+res.length+"件)":"\n不合格あり");
await b.close();srv.close();
