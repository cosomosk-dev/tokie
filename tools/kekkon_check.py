# ウェディングストーリーの「お金の現実チェック」(2026/11/04)
# 使い方: python3 tools/kekkon_check.py   (playwright が必要: pip install playwright && playwright install chromium)
# 全5ルート × 8職種 × A/B を自動で通して、お金の数字が現実の範囲に入っているかを検査する。1つでも ✗ があれば反映しない。
# 基準は必ず2つ以上の出典で突き合わせた値(下のコメント)。基準を変える時は出典を書き、タケオさんに理由を説明する。
import json, re, subprocess, sys, time, os
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kekkon')
JOBS = ['office', 'nurse', 'civil', 'teacher', 'hoiku', 'beauty', 'it', 'other']
JN = {'office': '事務', 'nurse': '看護師', 'civil': '公務員', 'teacher': '教員', 'hoiku': '保育士', 'beauty': '美容・アパレル', 'it': 'IT', 'other': 'その他'}

# ① 29歳前後・都市部の女性の年収(額面・万円)の現実の幅
#   平均初婚年齢 妻29.8歳(人口動態統計2024)。賃金構造基本統計調査 令和6年・doda平均年収2025・総務省 地方公務員給与の実態
WAGE = {'office': (320, 380), 'nurse': (480, 560), 'civil': (400, 470), 'teacher': (400, 480),
        'hoiku': (370, 430), 'beauty': (280, 340), 'it': (420, 500), 'other': (380, 440)}
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
                    for pat in ['A', 'B', 'AB', 'BA', 'AAAAB', 'BBBBA']:
                        pg = b.new_page()
                        pg.goto(f'http://localhost:8766/index.html?test=auto&r={r}&p={(pat*16)[:16]}&job={job}')
                        pg.wait_for_function('window.__WS_DONE', timeout=60000)
                        out[(job, r, pat)] = {'ws': pg.evaluate('window.__WS'), 'err': pg.evaluate('window.__WS_ERR||""'), 'end': pg.evaluate('window.__WS_END||""')}
                        pg.close()
            b.close()
    finally:
        srv.kill()
    return out

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
            if k and '車の買い替え' in e['pre']['rows'] and 'マイカーローン' in e['book']:
                ng.append(f'{tag} {e["year"]}: マイカーローン返済中に車を買い替えてる')
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
    print(f'✓ {ok}件')
    for m in sorted(set(ng)):
        print('✗', m)
    print('全部 ✓' if not ng else f'✗ {len(set(ng))}件 — 直してから反映すること')
    sys.exit(1 if ng else 0)
