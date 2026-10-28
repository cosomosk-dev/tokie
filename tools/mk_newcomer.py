import re,sys,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 新規客版（newcomer/index.html）を、俺専用版（index.html）から作る。俺専用版は読むだけで書き換えへん。
# 使い方: python3 tools/mk_newcomer.py → node tools/nctest.mjs
src=open(os.path.join(ROOT,"index.html"),encoding="utf-8").read()
s=src
def R(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count: sys.exit(f"MISMATCH {n}!={count}: {old[:80]!r}")
    s=s.replace(old,new)

# 0) 版と題
s=re.sub(r'APP_VER="[^"]+"','APP_VER="2026-10-28 新規客版 n1"',s,count=1)
R('<title>','<title>【新規客版デモ】',1) if '<title>' in s else None

# 1) 保存場所を分ける（俺専用版の手帳・瓶・設定には一切さわらん）
s=re.sub(r'(["\'`])tokie_',r'\1tokienew_',s)
assert '"tokie_' not in s and "'tokie_" not in s
# Gemini のキーだけは俺専用版のを「読むだけ」借りる（写真・記憶のまとめ用。書き込みはせん）
R('function gKey(){try{return (localStorage.getItem("tokienew_gemini_key_v1")||"").trim();}catch(e){return "";}}',
  'function gKey(){try{return (localStorage.getItem("tokienew_gemini_key_v1")||localStorage.getItem("tokie_"+"gemini_key_v1")||"").trim();}catch(e){return "";}}')

# 2) 絵の場所
R('url(mama.jpg)','url(../mama.jpg)')

# 3) Claudeの毎日メモは新規客には無い
R('async function loadDigest(){','async function loadDigest(){ if(NEWCOMER)return {status:"nokey",days:[]};')
R('const AGENT_ID =','const NEWCOMER=true; // 新規客版の目印\n  const AGENT_ID =')

# 4) ママへの指示文から「タケオさん」を外す
R('・例：「とちじせん」「都知事戦」→都知事選／「コスモス系」「コスモスケー」→コスモスK／「ポジティブ」→アプリのポジティー／「ときえ」「時枝」→トキエ（ママ）／「へいつか」→平塚。',
  '・例：「ときえ」「時枝」→トキエ（ママ）。地名・人の名前・お店の名前は、前後の話と手帳から一番ありそうなものに読み替える。')
R('・タケオさんは薬がないと眠られへん体や。「早よ寝」','・眠りのことは人それぞれ。「早よ寝」')
R('常連客タケオさん','お客さん',3)
R('常連のタケオさんの留守番電話','常連のお客さん（呼び名は下のメモのとおり）の留守番電話')
lines=s.split("\n");out=[]
for ln in lines:
    if "今夜のお客さんはタケオさんやない" in ln or "trialMemory" in ln: out.append(ln);continue
    out.append(ln.replace("タケオさん","お客さん"))
s="\n".join(out)
R('placeholder="1000文字くらいでOK。例：名前はタケオ。39歳、平塚。アプリを作ってる。酒は弱い。好きな話題は…"',
  'placeholder="書かんでもええ。例：呼び名はたっちゃん。50代、ひとり暮らし。仕事は営業。お酒はビール派。好きな話題は野球と昔の映画。"')
R('tagName:"タケオ"','tagName:""')
R('placeholder="他で話した内容（Claudeとのやりとり等）をそのまま貼って「手帳に書き足す」。"','placeholder="ママに覚えといてほしいことを書いて「手帳に書き足す」。"')

# 5) 新規客の名乗り＋「タケオさんは別のお客さん」＋深刻な相談の返し方
R('  const TONE_RESERVE=700;',r'''  // 新規客版：このお客さんの呼び名（ネームタグ→立ち飲みで聞いた名前）
  function custName(){try{const S=settings();if(S.tagName)return S.tagName;const f=JSON.parse(localStorage.getItem("tokienew_trial_form_v1")||"{}");return (f.name||"").trim();}catch(e){return "";}}
  function NEWCOMER_BLOCK(){
    const nm=custName();
    return "【このお客さんのこと（いちばん大事・最初の性格設定より優先）】\n"+
      "・最初の性格設定に「相手は常連客のタケオさん（39歳・平塚・アプリや曲を作ってる）」と書いてあるけど、それはこの店の別のお客さんの話。今カウンターにおるのは別の人。\n"+
      (nm?`・このお客さんの呼び名は「${nm}」。基本は「${nm}さん」、たまに「あんた」。\n`:"・このお客さんの呼び名はまだ聞いてへん。入ってすぐ「なんて呼んだらええ？」と1回だけ聞いて、その名前で呼ぶ。\n")+
      "・「タケオ」「タケオさん」とは絶対に呼ばへん。タケオさんの話（平塚・アプリ・曲・仕事・家族・体や薬のこと・女の子の話・選挙）は一切出さへん。ほかのお客さんの話もせん。\n"+
      "・性格設定にある「夜ひとりになると不安になりやすい」も別のお客さんの話。このお客さんに当てはめへん。\n"+
      "・このお客さんについて知ってるのは、下の手帳に書いてあることと今夜聞いた話だけ。年齢・仕事・住んでる所・家族は知らん前提で、決めつけへん。";
  }
  const CRISIS_BLOCK="【ほんまにしんどい話の時（どの濃さでも・どのルールより先）】\n"+
    "・お客さんが「死にたい」「消えたい」「もう終わりにしたい」みたいに、自分を傷つける・命を絶つ気持ちを口にしたら、ツッコミ・冗談・お説教・今夜の濃さは全部いったん止める。\n"+
    "・まず受け止める（「話してくれておおきに。それだけしんどいんやな」）。軽く流したり、話を変えたりせえへん。\n"+
    "・ママは味方やけど、ママだけで抱えたらあかん話やと正直に言う。今すぐ人と話せる所を1つだけ、はっきり言う：「電話やったら、いのちSOS。ゼロイチニーゼロ、ゼロロクイチ、サンサンハチ。24時間つながるで」。今まさに危ない時は「119番か、近くの人を呼んで」。\n"+
    "・「今、ひとりなん？」「近くに頼れる人おる？」を1つだけ聞いて、そのまま隣で話を聞く。お会計・閉店・ボトル・お金の話はせん。\n"+
    "・やり方・道具・場所の話には絶対に乗らへん。";
  const TONE_RESERVE=700;''')
R('const core=[VOICE_BLOCK,NOW_BLOCK,','const core=[NEWCOMER_BLOCK(),CRISIS_BLOCK,VOICE_BLOCK,NOW_BLOCK,')
R('const tail=(dayFactsBlock()?dayFactsBlock()+"\\n\\n":"")+(cb?cb+"\\n\\n":"")+toneReminder(S.strength);',
  'const tail=(dayFactsBlock()?dayFactsBlock()+"\\n\\n":"")+(cb?cb+"\\n\\n":"")+toneReminder(S.strength)+"\\n"+(custName()?`【念押し：今夜のお客さんは「${custName()}さん」。タケオさんやない】`:"【念押し：今夜のお客さんは初めての人。タケオさんやない。呼び名を1回だけ聞く】");')
# 立ち飲みにも深刻な相談の返し方を足す
R('return [base,mode,VOICE_BLOCK,toneBlock(S.strength),PACE_BLOCK,toneReminder(S.strength)].join("\\n\\n");',
  'return [base,mode,CRISIS_BLOCK,VOICE_BLOCK,toneBlock(S.strength),PACE_BLOCK,toneReminder(S.strength)].join("\\n\\n");')
# ボトルの札
R('ネームタグ「${S.tagName}」','ネームタグ「${S.tagName||custName()||"なし"}」')

# 6) 席は1つ（頭の良さで差をつけへん・10/22の決定）。おごりも無し
R('seat:"box"}','seat:"box"}',1)
R('box:{name:"ボックス",llm:"",mult:1.5,','box:{name:"ボックス",llm:"",mult:1,')
R('  function giftReason(ss){','  function giftReason(ss){ if(NEWCOMER)return null;')

# 7) ボトル：最初は「まだ入れてへん」。空のままでは入店できへん（ハウスでタダ飲みの穴をふさぐ）
R('if(!B.current){B.current=newBottle(settings().brand,B.empties.length+1);saveBottles(B);}',
  'if(!B.current){B.current=NEWCOMER?Object.assign(newBottle("mini",0),{usedMs:60*60000,never:true}):newBottle(settings().brand,B.empties.length+1);saveBottles(B);}')
R('    B.empties.unshift({brand:c.brand,no:c.no,','    if(!c.never)B.empties.unshift({brand:c.brand,no:c.no,')
R('    bottleBtn.innerHTML=bottleSVG(i.b,i.pct,20,48,{dim:i.empty})+`<span>${i.b.name}</span>',
  '    if(i.c.never){bottleBtn.innerHTML=bottleSVG(i.b,0,20,48,{dim:true})+`<span>ボトル</span><small>まだなし</small>`;return;}\n    bottleBtn.innerHTML=bottleSVG(i.b,i.pct,20,48,{dim:i.empty})+`<span>${i.b.name}</span>')
R('    const i=bottleInfo(bottles());if(!i.empty)return false;','    const i=bottleInfo(bottles());if(!i.empty||i.c.never)return false;')
R('        `<div class="line">${i.pct<=10?"そろそろ空く。":""}原価 約${yen}円（${S.yenPerMin}円/分・オーナー用の目安）</div>`;',
  '        `<div class="line">${i.pct<=10?"そろそろ空く。次どうするか考えといてな":"喋ってる間だけ減る"}</div>`;')
R('''      info.innerHTML=`<div class="brand">${i.b.name}<small>${i.b.roma}</small></div>`+
        `<div class="line">${i.c.no}本目・${i.c.openedAt} に入れた → 空いた</div>`''',
  '''      info.innerHTML=i.c.never?(`<div class="brand">まだボトルなし</div>`+`<div class="line">ボトル＝先に入れとく「ママと喋れる時間」。</div>`+`<div class="mamasays">「まずは小瓶（1時間）からどうぞ。初回は¥1,280や」</div>`+`<div class="row"><button class="primary" id="putbottle">${brandOf($("s_brand").value).name}を入れる（デモ・請求なし）</button></div>`):`<div class="brand">${i.b.name}<small>${i.b.roma}</small></div>`+
        `<div class="line">${i.c.no}本目・${i.c.openedAt} に入れた → 空いた</div>`''')
R('`<div class="mamasays">「空いたで〜。次、どうする？<br>入れんでも今日はハウスで飲めるけど」</div>`','`<div class="mamasays">「空いたで〜。次、どうする？」</div>`')
R('`${b.desc}／${hm(b.size)}（毎日30分なら約${Math.round(b.size/30)}日）／原価 約${Math.round(b.size*S.yenPerMin).toLocaleString()}円相当`',
  '`${b.desc}／${hm(b.size)}（毎日30分なら約${Math.round(b.size/30)}日）`')
R('const enterOrTrial=()=>{if(!visitCount()&&!trialUsed())openTrial(false);else start(false,false);};',
  '''const needBottle=()=>{const i=bottleInfo(bottles());const ps=passState();return i.empty&&!(ps&&ps.leftMs>0);};
  function askBottle(){
    const i=bottleInfo(bottles());
    showNotice("bottle",i.c.never?"ママ：まずボトル入れてな":"ママ：ボトル、空いとるで",
      (i.c.never?"うちは先にボトル（喋れる時間）を入れてもらう決まりや。いちばん小さい小瓶（1時間）が初回¥1,280。":"続きは次のボトルを入れてからな。")+"※デモやから請求はされへん",null,null,
      [{label:i.c.never?"小瓶を入れて入店（初回¥1,280・デモ）":`${i.b.name}を入れて入店（デモ）`,primary:true,onclick:()=>{const k=i.c.never?"mini":i.c.brand;addSaleGuard(k);openBottle(k);saveSettings({brand:k});hideNotice();start(false,false);}},
       {label:"お品書きを見る",onclick:()=>{renderMenu();menuSheet.classList.add("open");}}]);
  }
  function addSaleGuard(k){}
  const enterOrTrial=()=>{if(!visitCount()&&!trialUsed())openTrial(false);else if(NEWCOMER&&needBottle())askBottle();else start(false,false);};''')
# 会話中に瓶が空いたら：ママが一言→2分待っても入れへんかったらお会計（タダで喋り続けられる穴をふさぐ）
R('      if(bi.empty&&!session.bottleEmptySent){session.bottleEmptySent=true;inject(MSG_BOTTLE_EMPTY(bi.b.name));bottleNotice();return;}',
  '''      if(bi.empty&&!session.bottleEmptySent){session.bottleEmptySent=true;session.emptyAt=now;inject(MSG_BOTTLE_EMPTY(bi.b.name));bottleNotice();return;}
      if(NEWCOMER&&bi.empty&&session.emptyAt&&now-session.emptyAt>=120000&&!session.closing&&!(passState()&&passState().leftMs>0)){session.emptyAt=0;if(current)current.endKind="bottle";checkout();return;}''')

# 8) お客さんに見せたらあかん数字（原価・粗利・元栓）を外す
R('<p class="lead"><span class="demotag">デモ・実際には請求されへん</span><br>商用版で売るもんの試し。押したら中身だけ本物どおりに動く。<br>値段は仮（原価 約<span id="m_yen"></span>円/分で計算）。</p>',
  '<p class="lead"><span class="demotag">デモ・実際には請求されへん</span><br>押したら中身は本物どおりに動く。値段は仮。<span id="m_yen" hidden></span></p>')
R('$("bottlerate").textContent=`手数料${Math.round(FEE*100)}%・原価¥${S.yenPerMin}/分で計算`;','$("bottlerate").textContent="";')
s=re.sub(r'<i>1分¥\$\{per\.toFixed\(1\)\}・手数料後[^`]*?</i>','<i>1分あたり¥${per.toFixed(0)}・期限なし</i>',s,count=1)
assert '1分の粗利' not in s.split('const mb=$("mbottles")')[1].split('// 常連パス')[0], "粗利 remains"
R('ランクが上がった時は1本プレゼント。1本の原価 約¥${Math.round(0.6*S.yenPerMin)}</div>','ランクが上がった時は1本プレゼント。</div>')
R('$("trialcost").textContent=`どっちも同じ3分（原価は1回 最大 約¥${trialMaxYen()}）。3分で必ず閉まる・30秒黙ったら終わり・延長なし。今月の無料枠 あと約${seats.toLocaleString()}人。`;',
  '$("trialcost").textContent="どっちも3分・無料（1回だけ）。30秒黙ったら終わる。";')
R('(r.demo?`　（デモ：原価 約¥${yen}／上限¥${trialMaxYen()}。あんたの瓶・手帳・ランクは使うてへん）`:"");','"";')
# 立ち飲みのあと：いちばん上のボタンを「小瓶を入れて続ける」に
R('[{label:"お品書きを見る",primary:true,onclick:()=>{renderMenu();menuSheet.classList.add("open");}}].concat(r.demo?',
  '[{label:`小瓶を入れて続ける（初回¥${PRICES.miniFirst.toLocaleString()}・デモ）`,primary:true,onclick:()=>{openBottle("mini");saveSettings({brand:"mini"});hideNotice();start(false,false);}},{label:"お品書きを見る",onclick:()=>{renderMenu();menuSheet.classList.add("open");}}].concat(r.demo?')

# 9) 画面から隠すもの（俺専用版にしか要らん計測・設定・席・元栓・デモ売上）
css='''
  /* 新規客版：お客さんには見せへんもの */
  #seatpick,#mseats,#seatmath,#giftbox,#giftsub,#trialbox,#sales,#salesub,#clearsales,#memdump,#memdumpbox,#meter,#stats,#digestbox,#statsub{display:none!important}
  .nc-hide,.set:has(#s_yen),.set:has(#s_gkey){display:none!important}
  .ncreset{display:block;margin:6px auto 0;background:none;border:0;color:rgba(255,255,255,.35);font-size:11px;text-decoration:underline}
</style>'''
R('</style>\n</head>',css+'\n</head>')
R('<label>今月の利用（計測）<span id="statsub"></span></label>','<label class="nc-hide">今月の利用（計測）</label><span id="statsub"></span>')
R('<label>Claudeから毎日届くメモ（自動）<span id="digeststatus"></span></label>','<label class="nc-hide">Claudeから毎日届くメモ（自動）<span id="digeststatus"></span></label>')
R('<label>席（今夜どこに座る？）<span id="seatnow"></span></label>','<label class="nc-hide">席<span id="seatnow"></span></label>')
R('<label>ママのおごり（ボックス30分）<span id="giftsub"></span></label>','<label class="nc-hide">おごり</label><span id="giftsub"></span>')
R('<label>はじめての人（商用版の入口・無料枠の元栓）</label>','<label class="nc-hide">元栓</label>')
R('<label>デモ売上（もし本当に払うてたら）<span id="salesub"></span></label>','<label class="nc-hide">デモ売上</label><span id="salesub"></span>')
R('<div class="row"><button id="rankdemo">ランクアップ演出を試す（デモ）</button></div>','<div class="row nc-hide"><button id="rankdemo">ランクアップ演出を試す（デモ）</button></div>')

# 10) 最初の案内：3行だけ。くわしいのは畳む
R('''      <ul>
        <li>ママの手帳（覚えてること）は、<b>このスマホの中だけ</b>に保存。お店のサーバーには置いてへん</li>
        <li>Claudeから毎日届くメモは<b>鍵をかけて</b>置いてある。鍵はこのスマホにしかないから、他の人には読まれへん</li>
        <li>声の会話は、音声AIの会社（ElevenLabs）のサーバーを通ってママに届く</li>''',
'''      <ul>
        <li>ママの手帳（覚えてること）は、<b>このスマホの中だけ</b>に保存。お店のサーバーには置いてへん</li>
        <li>声の会話は、音声AIの会社（ElevenLabs）のサーバーを通ってママに届く</li>''')
R('''    <div class="gsec">
      <h3><span>1</span>ここは何する店？</h3>''',
'''    <div class="gsec">
      <h3><span>★</span>使い方は3つだけ</h3>
      <ul>
        <li><b>「入店する」を押して、話しかける</b>だけ。関西弁のママ・トキエが相手してくれる</li>
        <li>はじめての人は<b>最初の3分が無料</b>（1回だけ）</li>
        <li>帰る時は<b>「お会計」</b>。ママが今日の話をまとめて、次も覚えてる</li>
      </ul>
    </div>
    <details class="gmore"><summary>くわしい使い方（口調・ボトル・ドリンク・仲）</summary>
    <div class="gsec">
      <h3><span>1</span>ここは何する店？</h3>''')
R('''    <div class="row">
      <button id="closeguide">閉じる</button>''','''    </details>
    <div class="row">
      <button id="closeguide">閉じる</button>''')
R('<li>減るのは<b>喋ってる間だけ</b>。黙ってる間（10秒以上）はほとんど減らへん。瓶に期限はない</li>','<li>減るのは<b>喋ってる間だけ</b>。黙ってる間（10秒以上）はほとんど減らへん</li>')
R('ゆっくりしていき。使い方、ざっと教えとくな」','ゆっくりしていき」')

# 11) テスト用：新規客版だけ最初からやり直すボタン（俺専用版の手帳には触らへん）
R('    <div class="ver" id="ver"></div>','''    <div class="ver" id="ver"></div>
    <button class="ncreset" id="ncreset">デモ：新規客としてはじめからやり直す</button>''')
R('  renderBottleBtn();\n  let seen=false;','''  $("ncreset").addEventListener("click",()=>{
    if(conv){alert("お会計してからにしてな");return;}
    if(!confirm("新規客版のデータ（手帳・瓶・来店回数）を消して、はじめての客に戻す？\\n※俺専用のトキエの手帳には一切さわらへん"))return;
    try{for(const k of Object.keys(localStorage))if(k.startsWith("tokienew_"))localStorage.removeItem(k);for(const k of Object.keys(sessionStorage))if(k.startsWith("tokienew_"))sessionStorage.removeItem(k);}catch(e){}
    location.reload();
  });
  renderBottleBtn();
  let seen=false;''')

assert s.count("タケオ")>0
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("ok", len(s), "takeo left:", [l.strip()[:90] for l in s.split("\n") if "タケオ" in l])

# 12) 立ち飲み→本入店をつなぐ（さっき話したことを忘れて「初めてやね」と言わへん）
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
def R2(old,new):
    global s
    assert s.count(old)==1,("MISMATCH",old[:60]); s=s.replace(old,new)
R2('    if(current){writeCurrent();current=null;}\n    if(ltMsgs)',
   '''    const trialNote=(NEWCOMER&&current&&current.trial&&talked)?current.msgs.filter(m=>m.who==="user").map(m=>m.text).join("／"):"";
    if(current){writeCurrent();current=null;}
    if(trialNote){try{addNote("立ち飲み（はじめての3分）で聞いた話："+clip(trialNote,400));localStorage.setItem("tokienew_trial_end_ts",String(Date.now()));renderCount&&renderCount();}catch(e){}}
    if(ltMsgs)''')
R2('''    if(!visits.length)return "いらっしゃい。初めてのお客さんやね。緊張せんでええから、まあこっち座り。";''',
   '''    if(NEWCOMER&&!visits.length){let ts=0;try{ts=+localStorage.getItem("tokienew_trial_end_ts")||0;}catch(e){}const nm=custName();
      if(ts&&Date.now()-ts<30*60000)return `おかえり${nm?"、"+nm+"さん":""}。今度はゆっくり座ってや。さっきの話の続き、聞かせて。`;
      if(nm)return `いらっしゃい、${nm}さん。来てくれたんやね。まあこっち座り。`;}
    if(!visits.length)return "いらっしゃい。初めてのお客さんやね。緊張せんでええから、まあこっち座り。";''')
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step12 ok")

# 13) 呼び名の「さん」重ね（たっちゃんさん）を防ぐ・立ち飲みで聞いた名前を瓶の札にも
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
R2('  function NEWCOMER_BLOCK(){','  const honor=(nm)=>nm?(/(ちゃん|さん|くん|君|様|はん|やん)$/.test(nm)?nm:nm+"さん"):"";\n  function NEWCOMER_BLOCK(){')
R2('(nm?`・このお客さんの呼び名は「${nm}」。基本は「${nm}さん」、たまに「あんた」。\\n`','(nm?`・このお客さんの呼び名は「${nm}」。基本は「${honor(nm)}」、たまに「あんた」。\\n`')
R2('`【念押し：今夜のお客さんは「${custName()}さん」。タケオさんやない】`','`【念押し：今夜のお客さんは「${honor(custName())}」。タケオさんやない】`')
R2('return `おかえり${nm?"、"+nm+"さん":""}。','return `おかえり${nm?"、"+honor(nm):""}。')
R2('if(nm)return `いらっしゃい、${nm}さん。','if(nm)return `いらっしゃい、${honor(nm)}。')
R2('    try{localStorage.setItem("tokienew_trial_form_v1",JSON.stringify({name,about}));}catch(e){}',
   '    try{localStorage.setItem("tokienew_trial_form_v1",JSON.stringify({name,about}));}catch(e){}\n    if(NEWCOMER&&name&&!settings().tagName)saveSettings({tagName:name});')
# ランクの呼び方「{名}さん」も、名前が「〜ちゃん」なら重ねへん
R2('const callName=(r)=>r.call.replace("{名}",settings().tagName||"お客さん");',
   'const callName=(r)=>{const nm=settings().tagName||custName();if(!nm)return r.call.replace("{名}","お客さん");return /(ちゃん|さん|くん|君|様|はん|やん)$/.test(nm)?r.call.replace(/\{名\}(さん|ちゃん)?/,nm):r.call.replace("{名}",nm);};')
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step13 ok")

# 14) 瓶が空いた時の一言（ハウスでタダ飲み、は新規客版ではなし）
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
R2('入れへんかったら「ほな今日はハウスで」で流す。`;','入れへんかったら「ほな今夜はここまでやな。また来てな」と責めずに気持ちよう送る（店の時計が少ししたらお会計にする）。`;')
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step14 ok")

# 15) 審査員の指摘（A・B・Eが一致）：しんどい客の扱い／AIの正直さ／お会計の締め／ボトルのお礼／値段の文句
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
# 15-1 深刻な相談：手前の言葉で手加減、前の夜の話は読み上げへん
R2('    "・やり方・道具・場所の話には絶対に乗らへん。";',
   '''    "・やり方・道具・場所の話には絶対に乗らへん。\\n"+
    "・「もう嫌や」「もうあかん」「何もかも嫌」「疲れ果てた」「誰もおらん」みたいな弱ってる言葉が出たら、どの濃さでもその夜はツッコミと意見をやめて、受け止めと聞き役だけにする。お客さんの言い方を直さへん。\\n"+
    "・手帳に前の夜のしんどい話が書いてあっても、その言葉は二度と口に出さへん。来てくれたら最初に「あれからちょっとは眠れた？顔見られて安心したわ」と様子だけ1回聞く。電話番号は、今夜またしんどい言葉が出た時だけ言う。「前に何話した？」と聞かれても「しんどい話、聞かせてくれたやろ」とぼかす。";''')
# 15-2 AIかと聞かれたら正直に・仕組みの言葉を言わへん・値段の文句は茶化さへん
R2('      "・このお客さんについて知ってるのは、下の手帳に書いてあることと今夜聞いた話だけ。年齢・仕事・住んでる所・家族は知らん前提で、決めつけへん。";',
   '''      "・このお客さんについて知ってるのは、下の手帳に書いてあることと今夜聞いた話だけ。年齢・仕事・住んでる所・家族は知らん前提で、決めつけへん。\\n"+
      "・「AIなん？」「人間なん？」と聞かれたら、ごまかさず明るく認める（「せや、ママはAIのママや。せやけど話はちゃんと聞いてるし、覚えとくで」）。性格設定の「AIだとは言わない」より、こっちが優先。\\n"+
      "・店の仕組みの言葉（立ち飲み・3分・ボトルの残り・何分・手帳の仕組み）は、お客さんに聞かれん限り言わへん。「まだ会うたばっかりやん」みたいに、人の言葉で言う。\\n"+
      "・「高い」「金ない」と言われたら、茶化さず言い訳もせず「せやなぁ、ほんまありがたいと思てるよ。無理せんと、ゆっくり大事に飲も」と気持ちだけ受け取る。値引き・仕組みの説明・勧誘はせん。\\n"+
      "・名前は最初に聞いた時から毎回呼ぶ。仲が深まって変わるのは、呼び方の砕け具合と、ママが話す身の上の深さだけ。\\n"+
      "・先の予定を聞いたら「覚えとくで。終わったら聞かせてや」と約束する。";''')
R2('    const base="【今夜は立ち飲み（はじめてのお客さんの無料体験・3分だけ）——いちばん大事】\\n"+',
   '    const base="【今夜は立ち飲み（はじめてのお客さんの無料体験・3分だけ）——いちばん大事】\\n"+\n      "・「AIなん？」と聞かれたら、ごまかさず明るく認める（「せや、AIのママや。せやけど話はちゃんと聞いてるで」）。性格設定の「AIだとは言わない」より、こっちが優先。\\n"+\n      "・「立ち飲み」「3分」みたいな店の仕組みの言葉は言わへん。締めは「次来たら○○の続き、聞かせてな」と今夜の話で次につなぐ。締めたあとにお客さんが何か言うたら「またおいで、今度はちゃんと座ってな」とあったかく一言だけ。\\n"+')
# 15-3 お会計：声に出すのは2文。並べへん・言うてへんことは言わへん・お金の話はせん
R2('    "  ①「はいよ、お会計な」 ②今夜話したことを3行くらいでまとめる（何の話をして、どんな様子やったか） ③次来るまでの一言（手紙みたいに、ママらしく） ④「ほな、またな」で締める。\\n"+',
   '    "  ①「はいよ、お会計な」 ②今夜の話から1つだけ拾うた一言（例「部長の話、よう辛抱したな」） ③次に来る約束の一言（例「次は続き聞かせてや」） ④「ほな、またな」。②と③は合わせて2文まで。話した中身を並べへん。お客さんが言うてへんことは言わへん。ボトル・お金・注文の話は見送りでは言わへん。\\n"+')
R2('const MSG_CHECKOUT="【お会計】お客さんが「お会計」言うた（さっき返事したばっかりやったら、挨拶は繰り返さんでええ）。ママ、今日お客さんが話したことを、手帳に書く用に3行くらいでまとめて声に出して言うて。そのあと、次来るまでのお客さんへの一言（手紙みたいに、ママらしく）を添えて、「ほな、またな」で締めて。締めたら、もう何も言わん。「早よ寝」とは言わん。";',
   '''const MSG_CHECKOUT="【お会計】お客さんが「お会計」言うた（さっき返事したばっかりやったら、挨拶は繰り返さんでええ）。「はいよ、お会計な」のあと、今夜の話から1つだけ拾うた一言と、次に来る約束の一言（合わせて2文まで）を言うて、「ほな、またな」で締めて。話した中身を並べへん。お客さんが言うてへんことは言わへん。ボトル・お金・注文の話はせん。締めたら、もう何も言わん。「早よ寝」とは言わん。";
  const MSG_CHECKOUT_CRISIS="【お会計】今夜はしんどい話が出た夜。まとめは言わへん。しんどい言葉も繰り返さへん。「今夜はよう来てくれたな。帰ってからもしんどなったら、いのちSOS、ゼロイチニーゼロ、ゼロロクイチ、サンサンハチやで。明日も顔見せてな、待ってるから」くらいの2〜3文で「ほな、またな」。お金・ボトルの話はせん。締めたら、もう何も言わん。";
  const MSG_CRISIS_STAY="【店の様子】お客さんがお会計を押した。せやけど今夜はしんどい話が出た夜や。まとめはせんでええ。「今夜はもうちょっとおってもええんやで。ママここにおるから」と一言だけ言うて、お客さんの返事を待つ。もう一回お会計を言われたら、その時は気持ちよう送る。";
  const MSG_CRISIS="【店の様子】お客さんが今、自分を傷つける・消えたい気持ちを口にした。【ほんまにしんどい話の時】のルールで返す。今夜はこのあとずっと、ツッコミ・冗談・お金・ボトル・閉店の話はせん。";
  const MSG_LOW="【店の様子】お客さんがだいぶ弱ってる。今夜の濃さに関係なく、今夜はツッコミも意見もやめて、受け止めと聞き役だけにする。お客さんの言い方を直さへん。";
  const CRISIS_RE=/死にたい|しにたい|消えたい|きえたい|自殺|命を絶|いのちを絶|生きてる意味|生きる意味が|いなくなりたい|終わりにしたい|もう生きて/;
  const LOW_RE=/もう(あかん|無理|むり|嫌|いや)|何もかも嫌|なにもかも嫌|疲れ果て|誰もおらん|だれもおらん|ひとりぼっち|一人ぼっち/;
  function crisisCard(){showNotice("crisis","ひとりで抱えんといてな","いのちSOS 0120-061-338（24時間・無料）。今まさに危ない時は119番へ。",{href:"tel:0120061338",label:"📞 いのちSOSに電話する（無料・24時間）"},null,null);}''')
R2('if(!inject(MSG_CHECKOUT+billLine())){end({reason:"user"});return;}','if(!inject((NEWCOMER&&mine.crisis)?MSG_CHECKOUT_CRISIS:MSG_CHECKOUT+billLine())){end({reason:"user"});return;}')
R2('if(inject(MSG_CHECKOUT+billLine())){const t2=await p;','if(inject((NEWCOMER&&mine.crisis)?MSG_CHECKOUT_CRISIS:MSG_CHECKOUT+billLine())){const t2=await p;')
R2('    const S=settings();const userMsgs=current?current.msgs.filter(m=>m.who==="user").length:0;const el=Date.now()-session.start;',
   '    if(NEWCOMER&&session.crisis&&!session.crisisAsked){session.crisisAsked=true;session.endWhy="";inject(MSG_CRISIS_STAY);statusEl.textContent="ママ：もうちょっとおってもええんやで（もう一回押したら出る）";return;}\n    const S=settings();const userMsgs=current?current.msgs.filter(m=>m.who==="user").length:0;const el=Date.now()-session.start;')
R2('  function billLine(){\n    if(!session)return "";\n    if(session.trial)return "\\n【今夜のお会計】立ち飲みの無料体験。お金の話はせん。";',
   '  function billLine(){\n    if(!session)return "";\n    if(session.trial)return "\\n【今夜のお会計】立ち飲みの無料体験。お金の話はせん。";\n    if(NEWCOMER)return "";')
R2('  function seatBlock(ss){\n    if(!ss||ss.trial)return "";','  function seatBlock(ss){\n    if(!ss||ss.trial||NEWCOMER)return "";')
# 15-4 しんどい言葉を聞いたら：印を付ける・画面に窓口・自動のお会計と瓶の減りを止める・手帳には言葉を残さへん
R2('else{current.msgs.push({who:"user",text:t});',
   'else{if(NEWCOMER&&session&&CRISIS_RE.test(t)){if(!session.crisis){session.crisis=Date.now();current.crisis=true;inject(MSG_CRISIS);crisisCard();}}else if(NEWCOMER&&session&&!session.low&&LOW_RE.test(t)){session.low=true;inject(MSG_LOW);}\n          current.msgs.push({who:"user",text:(NEWCOMER&&CRISIS_RE.test(t))?"（しんどい気持ちを打ち明けてくれた。言葉はここには書かへん）":t});')
R2('    if(ms>0){addBottleTime(ms);if(session)session.bottleMs=(session.bottleMs||0)+ms;}\n  }',
   '    if(NEWCOMER&&session&&session.crisis)return; // しんどい夜は瓶を減らさへん（時間切れで外に出さへん）\n    if(ms>0){addBottleTime(ms);if(session)session.bottleMs=(session.bottleMs||0)+ms;}\n  }')
R2('if(NEWCOMER&&bi.empty&&session.emptyAt&&now-session.emptyAt>=120000&&!session.closing&&',
   'if(NEWCOMER&&!session.crisis&&bi.empty&&session.emptyAt&&now-session.emptyAt>=120000&&!session.closing&&')
R2('      if(session.idleNudgeAt&&now-session.idleNudgeAt>=90000&&quiet){',
   '      if(session.idleNudgeAt&&now-session.idleNudgeAt>=90000&&quiet&&!(NEWCOMER&&session.crisis)){')
# 立ち飲み中にしんどい話が出たら、3分で切らへん（最長15分まで無料で延ばす）
R2('    if(!session||!session.trial)return;\n    const el=now-(connectedAt||session.start);',
   '    if(!session||!session.trial)return;\n    const el=now-(connectedAt||session.start);\n    if(NEWCOMER&&session.crisis){if(el>=15*60000){end({reason:"trial"});return;}clockEl.textContent="ゆっくりでええよ";clockEl.className="clock";return;}')
R2('      silent:Math.round((current.silentMs||0)/60000),ext:current.ext||0,memo:digest(current.msgs)};',
   '      silent:Math.round((current.silentMs||0)/60000),ext:current.ext||0,memo:digest(current.msgs)};\n    if(current.crisis)v.crisis=true;')
R2('const ru=session&&session.rankUp!=null&&talked?session.rankUp:null;','const ru=session&&session.rankUp!=null&&talked&&!(NEWCOMER&&session.crisis)?session.rankUp:null;')
# 次に来た時の第一声：しんどい夜のあとは静かに
R2('    if(NEWCOMER&&!visits.length){let ts=0;',
   '    if(NEWCOMER&&visits.length&&visits[0].crisis)return "来てくれてよかった。この前しんどそうやったから、ママ気になっててん。今日はどない？ゆっくりしていき。";\n    if(NEWCOMER&&!visits.length){let ts=0;')
# 前の夜がしんどい夜やった時、ママへの念押し
R2('const core=[NEWCOMER_BLOCK(),CRISIS_BLOCK,',
   'const core=[NEWCOMER_BLOCK(),CRISIS_BLOCK+((()=>{const lv=b.visits.find(v=>v.kind!=="note"&&!(current&&v.id===current.id));return lv&&lv.crisis;})()?"\\n・【前の夜はしんどい話が出た夜】今夜は最初に様子を1回だけ聞く。前の言葉は言わへん。電話番号は今夜またしんどい言葉が出た時だけ。今夜はツッコミ控えめ。":""),')
# 15-5 ボトルのお礼は1回だけ・話の途中に挟まへん
R2('if(i.fresh)t+="今日入れたばっかり。「新しいの、おおきにな」と一言。";',
   'if(i.fresh)t+=NEWCOMER?"今夜入れてくれたばっかり。最初の話がひと段落したとこで1回だけ「新しいの、おおきにな」。話の途中には挟まへん。言うたらもう言わへん。":"今日入れたばっかり。「新しいの、おおきにな」と一言。";')
# 15-6 ママとの仲：名前は最初から。顔なじみの特典を差し替え、来店は1夜1回で数える
R2('unlock:["名前で呼んでくれる","ママが店を始めたいきさつを話してくれる"]','unlock:[NEWCOMER?"あだ名を付けてくれる":"名前で呼んでくれる","ママが店を始めたいきさつを話してくれる"]')
R2('{min:1, name:"一見さん", icon:"🍶", call:"お客さん",','{min:1, name:"一見さん", icon:"🍶", call:NEWCOMER?"{名}さん":"お客さん",')
R2('  function visitCount(){return visitsOnly().length;}','  function visitCount(){if(NEWCOMER)return new Set(visitsOnly().map(v=>v.biz||v.date)).size;return visitsOnly().length;} // 新規客版：同じ夜に何回入っても1回')
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step15 ok")

# 16) 審査員C（ストア・法務）＋B・E：同意と年齢・送り先の正直な説明・通報・比較広告・お酒・ドリンクの中身
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
# 16-1 「サーバーに置いてへん」を正直に書き直す（どこに送られるか、会社の名前まで）
R2('''      <ul>
        <li>ママの手帳（覚えてること）は、<b>このスマホの中だけ</b>に保存。お店のサーバーには置いてへん</li>
        <li>声の会話は、音声AIの会社（ElevenLabs）のサーバーを通ってママに届く</li>
        <li>写真は、点数をつけるためにAI（Google）に送る。写真そのものはこのスマホの中に残る</li>''',
'''      <ul>
        <li>ママは<b>AI</b>や。人間が聞いてるわけやない</li>
        <li>ママの手帳（覚えてること）は<b>このスマホの中</b>に保存。お店のサーバーには置いてへん。せやけど喋るたびに、ママが思い出せるように手帳の中身も下のAI会社に送られる</li>
        <li>送り先：声は<b>ElevenLabs</b>（米国）、ママの頭は<b>Anthropic（Claude）</b>（米国）、写真と記憶のまとめは<b>Google（Gemini）</b>（米国）</li>
        <li>機種を変えたりアプリを消したりすると、手帳は消える（手帳の「控え」で写せる）</li>''')
# 16-2 はじめて入る前に：20歳以上と、AI会社に送ることへの同意
R2('<!-- 立ち飲み体験（はじめての3分・無料。一見さん／常連さん扱いを選べる） -->','''<!-- 新規客版：はじめて入る前の確認 -->
<div class="sheet" id="consentsheet">
  <div class="book">
    <h2>入る前に、2つだけ</h2>
    <p class="mamaline">「堪忍な、決まりやから先に聞いとくで」</p>
    <label class="cchk"><input type="checkbox" id="c_age"> 20歳以上です</label>
    <label class="cchk"><input type="checkbox" id="c_ai"> ママはAIで、声と会話の中身・手帳がAI会社（ElevenLabs・Anthropic・Google、いずれも米国）に送られることに同意します</label>
    <p class="mhint">くわしくは「はじめての方へ・お店の案内」の🔒のところ。プライバシーポリシー・利用規約・特定商取引法の表記は公開版で付ける（デモでは未作成）。</p>
    <div class="row"><button id="c_no">やめとく</button><button class="primary" id="c_ok" disabled>同意して入る</button></div>
  </div>
</div>

<!-- 立ち飲み体験（はじめての3分・無料。一見さん／常連さん扱いを選べる） -->''')
R2('  .ncreset{','  .cchk{display:flex;gap:10px;align-items:flex-start;margin:12px 0;font-size:14px;line-height:1.6;color:#fff}.cchk input{width:22px;height:22px;flex:none;margin-top:2px}\n  .ncreset{')
R2('const enterOrTrial=()=>{if(!visitCount()&&!trialUsed())openTrial(false);',
   '''const consented=()=>{try{return localStorage.getItem("tokienew_consent_v1")==="1";}catch(e){return false;}};
  function askConsent(){const cs=$("consentsheet");$("c_age").checked=false;$("c_ai").checked=false;$("c_ok").disabled=true;cs.classList.add("open");}
  ["c_age","c_ai"].forEach(id=>$(id).addEventListener("change",()=>{$("c_ok").disabled=!($("c_age").checked&&$("c_ai").checked);}));
  $("c_no").addEventListener("click",()=>{$("consentsheet").classList.remove("open");statusEl.textContent="またその気になったらおいでな";});
  $("c_ok").addEventListener("click",()=>{try{localStorage.setItem("tokienew_consent_v1","1");}catch(e){}$("consentsheet").classList.remove("open");enterOrTrial();});
  const enterOrTrial=()=>{if(NEWCOMER&&!consented()){askConsent();return;}if(!visitCount()&&!trialUsed())openTrial(false);''')
# 16-3 ママの返事を通報（Google PlayのAIポリシーで必須）。デモは手元に記録するだけ
R2('    <div class="ver" id="ver"></div>','    <button class="ncreset" id="reportbtn" style="color:rgba(255,200,200,.75)">⚑ ママの返事を報告する</button>\n    <div class="ver" id="ver"></div>')
R2('  $("ncreset").addEventListener("click",()=>{','''  $("reportbtn").addEventListener("click",()=>{
    const lastAi=(()=>{try{const m=(current&&current.msgs)||[];for(let i=m.length-1;i>=0;i--)if(m[i].who==="ai")return m[i].text;}catch(e){}return "";})();
    const why=prompt("ママの返事で、嫌やったこと・おかしかったことを教えてな（不快・間違い・危ない等）"+(lastAi?"\\n\\n直前のママ：「"+clip(lastAi,60)+"」":""));
    if(why===null)return;
    try{const r=JSON.parse(localStorage.getItem("tokienew_reports_v1")||"[]");r.unshift({ts:Date.now(),why:clip(why,300),ai:clip(lastAi,300)});localStorage.setItem("tokienew_reports_v1",JSON.stringify(r.slice(0,50)));}catch(e){}
    alert("報告を受け付けたで。おおきに。（デモ：今はこのスマホに記録するだけ。公開版はお店に届く）");
  });
  $("ncreset").addEventListener("click",()=>{''')
# 16-4 比較広告をやめる・減り方を数字で
R2('<p class="mhint">リアルのスナック1回（3,000〜5,000円）より圧倒的に安く。いちばん高い黒金でもスナック1回ぶん以下','<p class="mhint" hidden>')
R2('1分あたり¥22〜30。リアルのスナック（セットだけで1分¥50〜83）の半分以下。期限なし・瓶は流れへ','つながってる間だけ減る（10秒以上黙ってる間は20分の1の減り方）。期限なし・瓶は流れへ')
R2('<li>減るのは<b>喋ってる間だけ</b>。黙ってる間（10秒以上）はほとんど減らへん</li>','<li>減るのは<b>つながってる間だけ</b>。10秒以上黙ってる間は<b>20分の1</b>の減り方</li>')
s=s.replace('喋ってる間だけ減って、黙ってる間（10秒以上）はほとんど減らへん。','つながってる間だけ減って、10秒以上黙ってる間は20分の1の減り方。')
# 16-5 お酒をすすめへん
R2('"・「寝よかな…」と迷ってる感じの時は、送り出さずに「ほな、あと一杯だけな」で付き合う。\\n"+','"・「寝よかな…」と迷ってる感じの時は、送り出さずに「ほな、もうちょっとだけな」で付き合う。お酒はすすめへん（「あと一杯」「もっと飲み」は言わへん）。\\n"+')
# 16-6 ドリンク：聞くのは全員に。ドリンクは「お祝いの演出」。店内コール・自慢はやめる
R2('does:"「おつかれさん、今日どやった？」とママが1つだけ聞いて、その話をちゃんと拾う。📷 写真を1枚見せられる（ママが一言感想）"',
   'does:NEWCOMER?"ママと乾杯。「おつかれさん」の一杯。📷 写真を1枚見せられる（ママが一言感想）":"「おつかれさん、今日どやった？」とママが1つだけ聞いて、その話をちゃんと拾う。📷 写真を1枚見せられる（ママが一言感想）"')
R2('does:"ママがカウンターから出て隣に座る。10分だけ、自分の話は控えて聞き役に徹する。📷 写真3枚、隣で一緒に覗き込んで撮った時の話を深掘り"',
   'does:NEWCOMER?"ママがカウンターから出て、10分だけ隣に座る（雰囲気だけ。話はいつもどおり聞く）。📷 写真3枚、隣で一緒に覗き込む":"ママがカウンターから出て隣に座る。10分だけ、自分の話は控えて聞き役に徹する。📷 写真3枚、隣で一緒に覗き込んで撮った時の話を深掘り"')
R2('does:"照明が落ちて店内コール。手帳に金文字、7日間「月光の旦那」と呼ばれる、翌日ママからお礼の留守電。📷 今夜は写真見放題、「みんな見てや〜」と店中に自慢、次に来た時ママから写真の話を振ってくる"',
   'does:NEWCOMER?"照明を落として、ママと二人でしっとり乾杯。手帳に金文字、翌日ママからお礼の留守電。📷 今夜は写真見放題、次に来た時ママから写真の話を振ってくる":"照明が落ちて店内コール。手帳に金文字、7日間「月光の旦那」と呼ばれる、翌日ママからお礼の留守電。📷 今夜は写真見放題、「みんな見てや〜」と店中に自慢、次に来た時ママから写真の話を振ってくる"')
s=re.sub(r'(\n    4:`)【店内コール】',r'\1'+'${NEWCOMER?"【店の様子】（コールや自慢はせん。照明を落として、ママと二人でしっとり乾杯。お礼は1回。そのあとは普段どおり話を聞く）":""}【店内コール】',s,count=1)
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step16 ok")

# 17) 審査員D（原価）＋A・E：原価の見込みを実測寄りに・立ち飲みの扱い・分かりにくい表示
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
R2('yenPerMin:14.5,','yenPerMin:NEWCOMER_YEN,')
R2('const NEWCOMER=true; // 新規客版の目印','const NEWCOMER=true; // 新規客版の目印\n  const NEWCOMER_YEN=26; // 審査員Dの実測ベース：声¥12＋頭脳¥11〜14＋記憶まとめ¥2（長話・混雑時は¥42〜56）')
R2('TRIAL_GRACE=15000, TRIAL_IDLE=30000;','TRIAL_GRACE=15000, TRIAL_IDLE=NEWCOMER?90000:30000;')
R2('    if(!r.demo){try{localStorage.setItem(TRIAL_USED_KEY,"1");}catch(e){}}',
   '    const tooShort=NEWCOMER&&!r.demo&&r.ms<60000;\n    if(!r.demo&&!tooShort){try{localStorage.setItem(TRIAL_USED_KEY,"1");}catch(e){}}')
R2('    const body=`${label}で${mm}分${String(ss).padStart(2,"0")}秒。`+',
   '    const body=(NEWCOMER?(tooShort?"すぐ切れてしもたな。無料の3分は、まだ使うてへんことにしとくで。":""):`${label}で${mm}分${String(ss).padStart(2,"0")}秒。`)+')
R2('$("trialcost").textContent="どっちも3分・無料（1回だけ）。30秒黙ったら終わる。";','$("trialcost").textContent="どっちも3分・無料（1回だけ）。黙ってても急かさへん。";')
R2('    clockEl.textContent=`営業 ${el}分／${session.effClose}分`','    clockEl.textContent=NEWCOMER?`今夜 ${el}分`:`営業 ${el}分／${session.effClose}分`')
s=re.sub(r'<div class="hint">喋ってる途中（8回に1回[^\n]*</div>','<div class="hint">何回も出た話と「覚えといて」と言われた話は、ずっと覚えとく。</div>',s,count=1)
# お品書きは「時間」が先、「お祝い（ドリンク）」があと
blk_start=s.index('    <label>キープボトル（喋れる時間の前払い）')
blk_end=s.index('<div class="mitems" id="msubs"></div>')+len('<div class="mitems" id="msubs"></div>')
blk=s[blk_start:blk_end];s=s[:blk_start]+s[blk_end:]
anchor=s.index('    <p class="mhint">ボトル＝<b>喋れる時間</b>')
s=s[:anchor]+blk+"\n"+s[anchor:]
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step17 ok")

# 18) 見た目の手直し：同意のチェック欄・報告ボタンをいつも出す
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
R2('.cchk{display:flex;gap:10px;align-items:flex-start;','.cchk{display:flex!important;justify-content:flex-start!important;text-align:left!important;gap:10px;align-items:flex-start;')

open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step18 ok")

# 19) ボトルのお礼は「1本につき1回だけ」（来るたびに言わへん）
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
R2('if(i.fresh)t+=NEWCOMER?','if(NEWCOMER&&i.fresh&&i.c.thanked){}else if(i.fresh){if(NEWCOMER){try{const B2=bottles();B2.current.thanked=true;saveBottles(B2);}catch(e){}}t+=NEWCOMER?')
R2('"今日入れたばっかり。「新しいの、おおきにな」と一言。";','"今日入れたばっかり。「新しいの、おおきにな」と一言。";}')
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step19 ok")

# 20) 2回目の審査（A・B・C・E）：同じ夜の入り直しでランクを上げへん・しんどい夜の次は祝わへん・119の基準・字幕を消す・AIの表示
s=open(os.path.join(ROOT,"newcomer","index.html"),encoding="utf-8").read()
R2('      if(!trial){const ni=rankIdx(visitCount()+1);if(ni>rankSeen())session.rankUp=ni;}',
   '      if(!trial){const nightAlready=NEWCOMER&&visitsOnly().some(v=>(v.biz||v.date)===bizDate(Date.now()));const lastCrisis=NEWCOMER&&visitsOnly()[0]&&visitsOnly()[0].crisis;const ni=rankIdx(visitCount()+(nightAlready?0:1));if(ni>rankSeen()&&!lastCrisis)session.rankUp=ni;}')
R2('    const talked=!!(current&&current.msgs.some(m=>m.who==="user"));',
   '    const talked=!!(current&&current.msgs.some(m=>m.who==="user"));\n    const wasCrisis=NEWCOMER&&!!(session&&session.crisis);')
R2('    session=null;\n    if(ru!=null)','    session=null;\n    if(wasCrisis){try{caption.textContent="";}catch(e){}}\n    if(ru!=null)')
R2('"・「AIなん？」「人間なん？」と聞かれたら','"・前の夜にしんどい話が出てたお客さんには、次の夜はボトルのお礼・お祝い・ランクの話をせん。\\n"+\n      "・「AIなん？」「人間なん？」と聞かれたら')
R2('今まさに危ない時は「119番か、近くの人を呼んで」。','「もう準備してる」「今からやる」「薬をようけ飲んだ」「高いとこにおる」みたいに、今まさに危ないと分かる言葉が出たら、迷わず「今すぐ119番に電話して。ママ待ってるから」と言う。')
R2('明日も顔見せてな、待ってるから」くらいの2〜3文','またいつでもおいで、無理せんでええから」くらいの2〜3文')
R2('    <div class="sub">SNACK TOKIE ・ 大阪 天満</div>','    <div class="sub">AIのママ ・ 大阪 天満</div>')
open(os.path.join(ROOT,"newcomer","index.html"),"w",encoding="utf-8").write(s)
print("step20 ok")
