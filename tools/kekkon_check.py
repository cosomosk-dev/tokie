# ウェディングストーリーの「お金の現実チェック」(2026/11/04)
# 使い方: python3 tools/kekkon_check.py   (playwright が必要: pip install playwright && playwright install chromium)
# 全5ルート × 8職種 × A/B を自動で通して、お金の数字が現実の範囲に入っているかを検査する。1つでも ✗ があれば反映しない。
# 基準は必ず2つ以上の出典で突き合わせた値(下のコメント)。基準を変える時は出典を書き、タケオさんに理由を説明する。
import json, re, subprocess, sys, time, os
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kekkon')
JOBS = ['office', 'nurse', 'civil', 'teacher', 'hoiku', 'beauty', 'it', 'other']
JN = {'office': '事務', 'nurse': '看護師', 'civil': '公務員', 'teacher': '教員', 'hoiku': '保育士', 'beauty': '美容・アパレル', 'it': 'IT', 'other': 'その他'}

# ① 29歳前後・都市部の女性の年収(額面・万円)の現実の幅 — 平均ではなく中央値(2026/11/06 タケオ「平均は高い人に引っぱられる。シビアに」)
#   平均初婚年齢 妻29.8歳(人口動態統計2024)。平均の出典: 賃金構造基本統計調査 令和6年・doda平均年収2025・総務省 地方公務員給与の実態
#   中央値: doda 2025 女性29歳 中央値360万(平均383万)。地域は doda 女性 神奈川 中央値350万・大阪330万(全国350万)
WAGE = {'office': (290, 335), 'nurse': (480, 545), 'civil': (390, 445), 'teacher': (405, 460),
        'hoiku': (365, 410), 'beauty': (265, 300), 'it': (390, 440), 'other': (350, 395)}
# ② 額面→手取り(年)の割合の現実の幅(単身・扶養なし。税と社会保険の早見表)
TAKE = [(300, .76, .82), (500, .75, .80), (800, .71, .77), (1200, .67, .73), (2000, .61, .68), (5000, .52, .62), (1e9, .48, .58)]  # 4,000万超は最高税率55%(所得税45%+住民税10%)
# ③ お小遣い(月・万円): SBI新生銀行2024 男性会社員3.9万・女性3.5万。ふつうの家(手取り100万以下)
POCKET = (1.5, 6.5)
#   夫の年収1,500万以上(商社・テレビに出る美容師など)は、会食・交際が仕事のうちなので12万まで(推計)
POCKET_RICH = 12
# ④ ふつうの家(悠太・蓮・黒田)の貯蓄率の上限: 金融広報中央委員会/J-FLEC 平均1割強。子なし共働きでも25%まで、子育て中は20%まで
SAVE_MAX_NOKID, SAVE_MAX_KID = 25, 20
# ⑤ 結婚式であなたが出す額: ゼクシィ結婚トレンド調査2024(家族婚の負担は援助込みで50〜100万をふたりで)
WED = (0, 60)
# ⑥ 家・車を「持っていない貯金」で買わない(2026/11/05 悠太の点検): 頭金・諸費用・車は貯金から出せる分だけ、足りない分はローン。
#   貯金がプラスの家が、買い物ひとつでマイナス(カードローン)になるのは現実にはない(貸金業法の総量規制で、カードローンは年収の1/3まで)。
#   病院代(不妊治療など)は対象外。BUY_EP は「買う」選択がある話
BUY_EP = ['蔵を、継ぐか', 'チラシの、間取り図', '蔵の、許嫁', '最後の一本', 'ev:C_ippon', 'ev:C_kibou']
# ⑦ マンションを買ったら、ローンのほかに管理費・修繕積立金・固定資産税がかかる
#   首都圏の新築70㎡換算で管理費2.2万+修繕積立金1.0万=月3.2万(東京カンテイ2025)／修繕積立金の平均 月1.3万(国交省 令和5年度マンション総合調査)
#   固定資産税+都市計画税: 新築マンション 年10万〜28万(リクルート/CREX の試算)
# ⑩ 家は、頭金と諸費用が貯まっていなければ買わない(2026/11/05 タケオ「貯金ゼロで家をたてるやついんの？」)
#   頭金: 全銀協「少なくとも物件価格の1割、目安は2割」/ フラット35利用者調査2024: 注文住宅の手持金 平均9%・マンション 平均24%
#   諸費用: 全銀協「新築 3〜7%」/ リクルート「新築マンション 3〜5%・一戸建て 6〜13%」
#   → 買う前の貯金(ふたりの貯金＋頭金に出したあなたの結婚前の貯金) ≧ 頭金1割＋諸費用。足りない時は「建てよう／買おう」の選択肢を出さない。HOUSE = 話の名前: {印: (価格, 諸費用)}
HOUSE = {'チラシの、間取り図': {'kura': (2500, 150), '': (5200, 200)},
         '家を、買う？': {'': (6800, 270)}}  # 黒田編(2026/11/06): 新築3LDK 6,800万・諸費用4%
# ⑬ 黒田編の現実チェック(2026/11/06 黒田の点検)
#   昇進1回の年収アップは1割まで: 日本医療労働組合連合会2024 主任相当631万 / スタッフ530万、賃金構造 令和6年 第8表(女) 係長級 月35.4万→課長級 月45.8万は平均3歳以上の差。
#   1回で+25%(前の版)は大きすぎ
PROMO_MAX = 1.10
#   44歳の女性に「部長」は出さない(IT以外): 賃金構造 令和6年 第8表 女性の部長級は平均52.7歳・月55.0万(年収およそ880万=賞与4か月)、課長級は49.3歳・月45.8万
#   → 15年目に打診される管理職の年収は880万まで
KAN_MAX = 880
#   同居の工事と引っ越しは50万まで: 介護保険の住宅改修は上限20万で7〜9割が戻る(厚労省・大田区/横浜市の案内)。前の版は200万
DOUKYO_MAX = 50
#   120人の式の費用とご祝儀: ゼクシィ結婚トレンド調査2024 総額343.9万・招待52.0人(1人あたり6.6万)・ご祝儀205.6万(1人あたり4.0万)
#   → 人数が多いと1人あたりは下がるので、費用は1人4.5万以上、ご祝儀は1人4.5万以下(前の版は120人で450万=1人3.75万)
WED_PP, GIFT_PP = 4.5, 4.5
# ⑪ 貯金が足りないのに200万の樽を「家の貯金から」払わない／新潟の蔵の家(貯金ゼロの家)が小学校から私立に入れない
# ⑫ 貯金がマイナスの家に「インプラント」「保険のきかない詰め物」「実家への仕送り」「車の買い替え」は起きない(ふつうは保険の治療・先送りにする)
OPT_OOPS = ['インプラント', '保険のきかない詰め物', '実家への仕送り', '車の買い替え']
# ⑧ 車の買い替えは買ってから9年ごと(自動車検査登録情報協会の平均使用年数 約13年より短め)。ローン返済中に買い替えない

def run():
    srv = subprocess.Popen(['python3', '-m', 'http.server', '8766', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    out = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for job in JOBS:
                for r in 'ABCDS':
                    for pat in ['A', 'B', 'AB', 'BA', 'AAAAB', 'BBBBA'] + (['A2', 'B2'] if r == 'C' else []):  # 悠太は2周目(授からない分岐)も
                        pg = b.new_page()
                        pg.goto(f'http://localhost:8766/index.html?test=auto&r={r}&p={(pat[0]*16) if pat.endswith("2") else (pat*16)[:16]}&job={job}' + ('&lap=1' if pat.endswith('2') else ''))
                        pg.wait_for_function('window.__WS_DONE', timeout=60000)
                        out[(job, r, pat)] = {'ws': pg.evaluate('window.__WS'), 'err': pg.evaluate('window.__WS_ERR||""'), 'end': pg.evaluate('window.__WS_END||""')}
                        pg.close()
            b.close()
    finally:
        srv.kill()
    return out

# ⑬ ひとり暮らしの家計簿(結婚前)を、全8職業×住む所3つで検査(2026/11/06 タケオ「全職業で、お金がずれないように厳しく審査」)
#   都内の29歳の年収(中央値): 看護師 賃金構造 令和6年 25〜29歳 486.7万×東京/全国1.095 / 保育士 25〜29歳女性 379.6万(令和5年)×東京/全国 約1.12
#   事務 ドラマの事務職(手取り22万)・賃金構造 都道府県別 東京/全国1.20 / その他 doda 2025 女性 東京422万÷全国370万=1.14
#   公務員・教員 地域手当 東京20%(1級地)
WAGE_TOKYO = {'office': (340, 390), 'nurse': (505, 560), 'civil': (430, 480), 'teacher': (445, 495),
              'hoiku': (395, 440), 'beauty': (295, 335), 'it': (430, 485), 'other': (390, 440)}
#   地方: doda 女性 地方の県の中央値300万(全国350万の0.86)。公務員・教員・看護師・保育士は地域差が小さい(地域手当・公定価格)
WAGE_RURAL = {'office': (255, 295), 'nurse': (430, 480), 'civil': (355, 400), 'teacher': (370, 415),
              'hoiku': (335, 375), 'beauty': (235, 270), 'it': (345, 390), 'other': (315, 355)}
#   家賃(タケオ指定 2026/11/06): 都内8万(SUUMO 23区ワンルーム平均 約9万・安い区5.6〜6.3万)/都市部6万/地方5万。食費 3.5万(家計調査 単身 34歳以下女性 2022 3.0万×物価2割)
RENT1 = {'tokyo': 8, 'city': 6, 'rural': 5}
FOOD1 = 3.5
#   ひとり暮らしの貯金率(ボーナス別の毎月分): 8〜25%(上限は子なし共働きの SAVE_MAX_NOKID と同じ。J-FLEC 平均は1割強)
SAVE1 = (8, SAVE_MAX_NOKID)

def run_single():
    srv = subprocess.Popen(['python3', '-m', 'http.server', '8769', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    out = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for job in JOBS:
                for area in RENT1:
                    pg = b.new_page()
                    pg.goto(f'http://localhost:8769/index.html?test=auto&r=B&p={"A"*16}&job={job}&area={area}')
                    pg.wait_for_function('window.__WS_DONE', timeout=60000)
                    ws = pg.evaluate('window.__WS')
                    out[(job, area)] = next((e['book'] for e in ws if 'ひとり暮らし' in e['book']), '')
                    pg.close()
            b.close()
    finally:
        srv.kill()
    return out

def check_single(out):
    ng, ok = [], 0
    for (job, area), b in out.items():
        tag = f'ひとり暮らし・{JN[job]}・{area}'
        def g(rx):
            m = re.search(rx, b); return num(m.group(1)) if m else None
        w, inc, live, rent, net = g(r'年収およそ(\d+)万円'), g(r'ボーナスは別\)\+([\d.]+)万'), g(r'生活費 ([\d.]+)万'), g(r'家賃 ([\d.]+)万'), g(r'残るお金([+−][\d.]+)万')
        food, fr_live = g(r'うち食費([\d.]+)万'), g(r'切り詰めれば生活費は([\d.]+)万')
        tests = [
            (None not in (w, inc, live, rent, net, food, fr_live), f'{tag}: 家計簿の項目が足りない'),
        ]
        if None not in (w, inc, live, rent, net, food, fr_live):
            lo, hi = {'tokyo': WAGE_TOKYO, 'city': WAGE, 'rural': WAGE_RURAL}[area][job]
            rate = net / inc * 100
            tests += [
                (lo <= w <= hi * 1.1, f'{tag}: 年収{w:.0f}万が現実({lo}〜{hi}万)から外れてる'),
                (rent == RENT1[area], f'{tag}: 家賃{rent}万(基準{RENT1[area]}万)'),
                (food == FOOD1, f'{tag}: 食費{food}万(基準{FOOD1}万)'),
                (abs(fr_live - (live - FOOD1 + 2)) < .05, f'{tag}: 切り詰めた生活費{fr_live}万が計算と合わない'),
                (abs(inc - live - rent - net) < .15 or '補助' in b, f'{tag}: 手取り−生活費−家賃が残るお金と合わない'),
                (SAVE1[0] <= rate <= SAVE1[1] + .5, f'{tag}: 貯金率{rate:.0f}%(基準{SAVE1[0]}〜{SAVE1[1]}%)'),
                (live < inc - rent, f'{tag}: 赤字'),
            ]
        for c, m in tests:
            if c: ok += 1
            else: ng.append(m)
    # 同じ職業なら、生活費は 都内 ≧ 都市部 ≧ 地方(家賃の安い所の方が生活費が高い逆転はおかしい)
    for job in JOBS:
        lv = [re.search(r'生活費 ([\d.]+)万', out.get((job, a), '')) for a in ('tokyo', 'city', 'rural')]
        if all(lv):
            t, c, r = (num(m.group(1)) for m in lv)
            if t >= c >= r: ok += 1
            else: ng.append(f'ひとり暮らし・{JN[job]}: 生活費が 都内{t}・都市部{c}・地方{r} で逆転')
    return ok, ng

def num(s):
    return float(s.replace('−', '-').replace('+', '').replace(',', ''))

def check(out):
    ng, ok = [], 0
    def t(cond, msg):
        nonlocal ok
        if cond: ok += 1
        else: ng.append(msg)
    for (job, r, pat), v in out.items():
        tag = f'{JN[job]}・{r}{pat}'
        t(not v['err'], f'{tag}: エラー {v["err"][:80]}')
        ws = v['ws']
        end = v.get('end', '')
        # 結末で「貯金が増えた」と言うなら、本当に増えていること
        if ws and re.search(r'貯金も、ちゃんと増えている|口座も増えた', end):
            t(ws[-1]['sav'] >= 300, f'{tag}: 結末で「貯金が増えた」なのに、ふたりの貯金{ws[-1]["sav"]}万')
        buyY = None
        for k, e in enumerate(ws):
            alltxt = e['book'] + e['out'] + e['nak'] + e['pop'] + e['scene']
            t('生活費の-' not in alltxt and '大損' not in e['pop'], f'{tag} {e["year"]}: 「生活費の-◯か月分」か「大損」の表示')
            t(not re.search(r'小学生[^−]*海外研修', e['book']), f'{tag} {e["year"]}: 小学生に「海外研修」')
            if 'ペアローン 月' in e['book'] or ('マンション' in e['book'] and '住宅ローン 月' in e['book']):
                t('管理費' in e['book'] and '固定資産税' in e['book'], f'{tag} {e["year"]}: マンションなのに管理費・固定資産税が家計簿にない')
            # ⑥ 買い物で貯金をマイナスにしない(選ぶ前の貯金 = 選んだ後 + 出費)
            m = re.search(r'ふたりの貯金 (?:大きな出費|出費)−([\d,]+)万円', e['pop'])
            if m and e['key'] in BUY_EP:
                before = e['sav'] + num(m.group(1))
                t(not (before >= 0 and e['sav'] < -5), f'{tag} {e["year"]}「{e["title"]}」: 貯金{before:.0f}万の家が{num(m.group(1)):.0f}万を現金で払ってマイナスに(足りない分はローンのはず)')
            # ⑨ 新築して10年未満の家に「外壁と屋根の塗り替え」、8年未満で「給湯器」は出さない(外壁塗装の目安は10〜15年、給湯器の寿命は10年前後)
            yn = re.search(r'結婚(\d+)年目', e['year'] or '')
            if yn and buyY is None and re.search(r'(住宅ローン|ペアローン) 月', e['book']):
                buyY = int(yn.group(1)) - 1
            if yn and buyY is not None:
                age = int(yn.group(1)) - buyY
                t(not ('外壁と屋根' in e['pre']['rows'] and age < 10) and not ('給湯器' in e['pre']['rows'] and age < 8), f'{tag} {e["year"]}: 建てて{age}年の家に外壁塗装・給湯器の故障')
            if k and ws[k - 1]['sav'] < 0:
                t(not any(w in e['pre']['rows'] for w in OPT_OOPS), f'{tag} {e["year"]}: 貯金がマイナスの家に、ぜいたくな思わぬ出費')
            if e['key'] in HOUSE:
                price, fee = HOUSE[e['key']]['kura' if 'kura' in e['f'].split(',') else '']
                need = price // 10 + fee
                m2 = re.search(r'ふたりの貯金 (?:大きな出費|出費)−([\d,]+)万円', e['pop'])
                m4 = re.search(r'あなた個人の貯金\(ふたりの貯金とは別\)−([\d,]+)万円', e['pop'])  # 頭金にはあなたの結婚前の貯金も出せる(持ち分にする)
                m5 = re.search(r'夫のもの\(別\) −([\d,]+)万円', e['why'])  # 2026/11/06 夫にも結婚前の貯金がある(J-FLEC 単身30代 保有世帯の中央値300万)。頭金に出した分も数える
                before = e['sav'] + (num(m2.group(1)) if m2 else 0) + e.get('mine', 0) + (num(m4.group(1)) if m4 else 0) + e.get('hc', 0) + (num(m5.group(1)) if m5 else 0)
                bought = 'buy' in e['f'].split(',') or (e['key'] == '家を、買う？' and 'house' in e['f'].split(','))
                t(not bought or before >= need, f'{tag} {e["year"]}: 貯金{before:.0f}万で家を買った(頭金1割＋諸費用で{need}万は要る)')
                t(before >= need or not any(re.search(r'建てよう|買おう', c) for c in e['choices']), f'{tag} {e["year"]}: 貯金{before:.0f}万なのに「買う」選択肢が出てる')
            if '家の貯金から' in e['out']:
                m3 = re.search(r'(?:出費|大きな出費)−([\d,]+)万円', e['pop'])
                t(not m3 or e['sav'] >= 0, f'{tag} {e["year"]}: 「家の貯金から」払って貯金がマイナス')
            if r == 'C':  # 悠太2周目の「授からない」分岐: 子がいるのに子なしの話を出さない
                t(not (e['kids'] and re.search(r'ふたりの、樽|ふたりの老後', e['title'] + e['scene'])), f'{tag} {e["year"]}: 子どもがいるのに「授からない」側の話')
            if r == 'C' and re.search(r'私立小', e['book']):
                ng.append(f'{tag} {e["year"]}: 悠太編で小学校から私立(新潟の蔵・ふつうの家には不自然)')
            if k and '車の買い替え' in e['pre']['rows'] and 'マイカーローン' in e['book']:
                ng.append(f'{tag} {e["year"]}: マイカーローン返済中に車を買い替えてる')
            # ⑬ 黒田編
            if r == 'B':
                if e['key'] == '白いバラ、300本':
                    m = re.search(r'式は(\d+)人。費用(\d+)万は、ご祝儀(\d+)万', e['out'])
                    t(bool(m), f'{tag}: 式の人数・費用・ご祝儀が書いてない')
                    if m:
                        n, cost_, gift = (int(x) for x in m.groups())
                        t(cost_ / n >= WED_PP and gift / n <= GIFT_PP, f'{tag}: {n}人の式で費用{cost_}万・ご祝儀{gift}万は相場から外れてる')
                        nx = next((x for x in ws if x['key'] == '谷中の、小さな花屋'), None)
                        m2 = nx and re.search(r'式の自己負担(\d+)万\(費用(\d+)万−ご祝儀(\d+)万\)', nx['pre']['x'])
                        t(bool(m2) and int(m2.group(2)) == cost_ and int(m2.group(3)) == gift and int(m2.group(1)) == cost_ - gift, f'{tag}: 式のお金が、第3話と結婚の画面で食い違う')
                if e['key'] in ('ドバイ辞令', 'ロンドン、5年') and e['pick'] == 'B':
                    m = re.search(r'あなたの年収 ([\d,]+)万 → ([\d,]+)万', e['why'])
                    t(not m or num(m.group(2)) <= num(m.group(1)) * PROMO_MAX, f'{tag} {e["year"]}: 昇進で年収が{m and m.group(1)}→{m and m.group(2)}万(1回1割まで)')
                if e['key'] == '女部長と、エプロンの夫':
                    t(job == 'it' or '「部長を' not in e['scene'], f'{tag}: 44歳の{JN[job]}に「部長」の打診')
                    t(e['W'] <= KAN_MAX, f'{tag}: 15年目のあなたの年収{e["W"]}万(管理職でも{KAN_MAX}万まで)')
                if e['key'] == 'ev:B_kaigo' and e['pick'] == 'A':
                    m = re.search(r'出費−([\d,]+)万円', e['pop'])
                    t(not m or num(m.group(1)) <= DOUKYO_MAX, f'{tag}: 同居の工事と引っ越しに{m and m.group(1)}万')
                if e['key'] == 'ドバイ辞令' and job in ('civil', 'teacher'):
                    t('休業制度がある' in e['scene'], f'{tag}: 公務員・公立の先生なのに「同行休業がない」')
                t('契約社員で戻った' not in e['pre']['x'], f'{tag} {e["year"]}: 帰国後「契約社員」なのにペアローン')
        # あなたの年収(結婚1年目の家計簿の「あなた 〇万(年収〇万)」)
        for e in ws:
            m = re.search(r'あなた ([\d.]+)万\(年収([\d,]+)万\)', e['book'])
            if m:
                g = num(m.group(2)); lo, hi = WAGE[job]
                t(lo <= g <= hi * 1.1, f'{tag} {e["year"]}: あなたの年収{g:.0f}万が現実({lo}〜{hi}万)から外れてる')
                break
        for e in ws:
            b = e['book']
            # 手取りの割合
            for who, net, gross in re.findall(r'(夫|あなた) ([\d.]+)万\(年収([\d,]+)万\)', b):
                g = num(gross); ratio = num(net) * 12 / g
                lo, hi = next(((a, c) for th, a, c in TAKE if g <= th), (TAKE[-1][1], TAKE[-1][2]))
                t(lo - .02 <= ratio <= hi + .02, f'{tag} {e["year"]}: {who}の手取り率{ratio:.0%}(年収{g:.0f}万)が早見表({lo:.0%}〜{hi:.0%})から外れてる')
            # お小遣い(ふつうの家だけ)
            pk = re.search(r'お小遣い夫 ([\d.]+)万', b)
            if pk and r in 'BCD':
                hg = re.search(r'夫 [\d.]+万\(年収([\d,]+)万\)', b); hi = POCKET_RICH if hg and num(hg.group(1)) >= 1500 else POCKET[1]
                v1 = num(pk.group(1)); t(POCKET[0] <= v1 <= hi, f'{tag} {e["year"]}: 夫のお小遣い{v1}万が現実({POCKET[0]}〜{hi}万)から外れてる')
            # 貯蓄率(ふつうの家: 悠太・蓮。黒田は高収入なので+5%まで)
            inc = re.search(r'手取り\(月平均\).*?\+([\d.]+)万', b); left = re.search(r'今月、残るお金\s*([+−][\d.]+)万', b)
            # 例外(現実でも貯まる家): 海外駐在(手当は非課税・家賃と学費は会社もち)/夫の実家に住んで家賃なし/離婚後(元夫から養育費)
            special = ('駐在手当' in b) or ('家賃なし' in b) or ('養育費' in b)
            if inc and left and r in 'BCD' and not special:
                rate = num(left.group(1)) / num(inc.group(1)) * 100
                hh = sum(num(x) for x in re.findall(r'\(年収([\d,]+)万\)', b))
                mx = (SAVE_MAX_KID if e['kids'] else SAVE_MAX_NOKID) + (10 if hh >= 1500 else 0)  # 世帯年収1,500万超(黒田・成功した悠太など)は貯蓄率が上がるので+10%まで
                t(rate <= mx, f'{tag} {e["year"]}: 貯蓄率{rate:.0f}%は高すぎ(上限{mx}%)')
            # タカヒロ編は赤字にしない(作者の指示 2026/10/27)
            if r == 'S' and left:
                t(num(left.group(1)) >= -0.5, f'{tag} {e["year"]}: タカヒロ編で赤字{left.group(1)}万')
        # 結婚式であなたが出した額
        for e in ws:
            m = re.search(r'あなたの貯金 出費−([\d,]+)万円', e.get('pop', ''))
            if m:
                a = num(m.group(1)); t(WED[0] <= a <= WED[1], f'{tag} {e["year"]}: 式であなたが出す{a:.0f}万が現実から外れてる')
        # 中小(悠太・蓮)の春の賃上げは物価に負ける
        if r in 'CD':
            for e in ws:
                if re.search(r'夫 \+(4|5|6)', e['pre']['rows']):
                    ng.append(f'{tag} {e["year"]}: 中小なのに夫の賃上げが物価に勝ってる')
    return ok, ng

if __name__ == '__main__':
    out = run()
    ok, ng = check(out)
    ok1, ng1 = check_single(run_single())
    ok += ok1; ng += ng1
    print(f'✓ {ok}件')
    for m in sorted(set(ng)):
        print('✗', m)
    print('全部 ✓' if not ng else f'✗ {len(set(ng))}件 — 直してから反映すること')
    sys.exit(1 if ng else 0)
