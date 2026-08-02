# -*- coding: utf-8 -*-
"""世界国旗图鉴 build.py
- 读取 data/*.py 数据 → 校验 → 注入 ISO 数字码(num)
- 读取 template.html + 内嵌 d3/topojson/world-atlas → 输出单文件 index.html
用法: python build.py
"""
import os, sys, json, io, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")

# ============ ISO 3166-1 numeric → alpha-2 映射 ============
NUM = {
4:"af",8:"al",10:"aq",12:"dz",16:"as",20:"ad",24:"ao",28:"ag",31:"az",32:"ar",36:"au",40:"at",44:"bs",48:"bh",50:"bd",51:"am",52:"bb",56:"be",60:"bm",64:"bt",68:"bo",70:"ba",72:"bw",74:"bv",76:"br",84:"bz",86:"io",90:"sb",92:"vg",96:"bn",100:"bg",104:"mm",108:"bi",112:"by",116:"kh",120:"cm",124:"ca",132:"cv",136:"ky",140:"cf",144:"lk",148:"td",152:"cl",156:"cn",158:"tw",162:"cx",166:"cc",170:"co",174:"km",175:"yt",178:"cg",180:"cd",184:"ck",188:"cr",191:"hr",192:"cu",196:"cy",203:"cz",204:"bj",208:"dk",212:"dm",214:"do",218:"ec",222:"sv",226:"gq",231:"et",232:"er",233:"ee",234:"fo",238:"fk",239:"gs",242:"fj",246:"fi",248:"ax",250:"fr",254:"gf",258:"pf",260:"tf",262:"dj",266:"ga",268:"ge",270:"gm",275:"ps",276:"de",288:"gh",292:"gi",296:"ki",300:"gr",304:"gl",308:"gd",312:"gp",316:"gu",320:"gt",324:"gn",328:"gy",332:"ht",336:"va",340:"hn",344:"hk",348:"hu",352:"is",356:"in",360:"id",364:"ir",368:"iq",372:"ie",376:"il",380:"it",384:"ci",388:"jm",392:"jp",398:"kz",400:"jo",404:"ke",408:"kp",410:"kr",414:"kw",417:"kg",418:"la",422:"lb",426:"ls",428:"lv",430:"lr",434:"ly",438:"li",440:"lt",442:"lu",446:"mo",450:"mg",454:"mw",458:"my",462:"mv",466:"ml",470:"mt",474:"mq",478:"mr",480:"mu",484:"mx",492:"mc",496:"mn",498:"md",499:"me",504:"ma",508:"mz",512:"om",516:"na",520:"nr",524:"np",528:"nl",531:"cw",533:"aw",534:"sx",535:"bq",540:"nc",548:"vu",554:"nz",558:"ni",562:"ne",566:"ng",570:"nu",574:"nf",578:"no",580:"mp",581:"um",583:"fm",584:"mh",585:"pw",586:"pk",591:"pa",598:"pg",600:"py",604:"pe",608:"ph",612:"pn",616:"pl",620:"pt",624:"gw",626:"tl",630:"pr",634:"qa",638:"re",642:"ro",643:"ru",646:"rw",652:"bl",654:"sh",659:"kn",660:"ai",662:"lc",663:"mf",666:"pm",670:"vc",674:"sm",678:"st",682:"sa",686:"sn",688:"rs",690:"sc",694:"sl",702:"sg",703:"sk",704:"vn",705:"si",706:"so",710:"za",716:"zw",724:"es",728:"ss",729:"sd",732:"eh",740:"sr",744:"sj",748:"sz",752:"se",756:"ch",760:"sy",762:"tj",764:"th",768:"tg",772:"tk",776:"to",780:"tt",784:"ae",788:"tn",792:"tr",795:"tm",796:"tc",798:"tv",800:"ug",804:"ua",807:"mk",818:"eg",826:"gb",831:"gg",832:"je",833:"im",834:"tz",840:"us",850:"vi",854:"bf",858:"uy",860:"uz",862:"ve",876:"wf",882:"ws",887:"ye",894:"zm",
}

REQUIRED = ["code", "zh", "en", "continent", "capital", "area", "population", "language", "currency", "resources", "tourism", "intro"]
CODE2NUM = {v: k for k, v in NUM.items()}
CONTINENTS = ["亚洲", "欧洲", "非洲", "北美洲", "南美洲", "大洋洲"]
FILE_ORDER = ["asia.py", "europe.py", "africa.py", "americas.py", "oceania.py"]

def load_data():
    all_c = []
    errors = []
    for fn in FILE_ORDER:
        path = os.path.join(DATA_DIR, fn)
        if not os.path.exists(path):
            errors.append("缺失文件: %s" % fn)
            continue
        ns = {}
        src = open(path, encoding="utf-8").read()
        exec(compile(src, fn, "exec"), ns)
        lst = ns.get("COUNTRIES")
        if not isinstance(lst, list):
            errors.append("%s 未定义 COUNTRIES 列表" % fn)
            continue
        # 逐条校验
        for c in lst:
            if not isinstance(c, dict):
                errors.append("%s: 非字典条目 %r" % (fn, c)); continue
            miss = [k for k in REQUIRED if k not in c or c[k] in (None, "", [])]
            if miss:
                errors.append("%s [%s]: 缺失字段 %s" % (fn, c.get("code"), miss))
            if c.get("continent") not in CONTINENTS:
                errors.append("%s [%s]: 大洲不合法 %r" % (fn, c.get("code"), c.get("continent")))
            if not re.match(r"^[a-z]{2}$", str(c.get("code", ""))):
                errors.append("%s [%s]: code 不合法" % (fn, c.get("code")))
            if c.get("num") is None:
                # ISO 数字码必须 3 位零填充（地图 feature id 是 "076" 格式，不是 "76"）
                c["num"] = str(CODE2NUM.get(c["code"])).zfill(3) if c["code"] in CODE2NUM else None
            all_c.append(c)
    # 重复 code
    seen = {}
    for c in all_c:
        seen[c["code"]] = seen.get(c["code"], 0) + 1
    dup = {k: v for k, v in seen.items() if v > 1}
    if dup:
        errors.append("重复 code: %s" % dup)
    return all_c, errors

def read_local(name, url):
    path = os.path.join(BASE, name)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return open(path, encoding="utf-8", errors="replace").read()
    print("  下载 %s <- %s" % (name, url))
    import ssl, urllib.request
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60, context=ctx).read()
    open(path, "wb").write(data)
    return data.decode("utf-8", errors="replace")

def main():
    print("== 加载数据 ==")
    countries, errors = load_data()
    if errors:
        print("!! 数据校验失败 %d 项:" % len(errors))
        for e in errors[:40]:
            print("   -", e)
        sys.exit(1)
    print("  数据通过: %d 条" % len(countries))
    from collections import Counter
    for ct, n in Counter(c["continent"] for c in countries).items():
        print("    %s: %d" % (ct, n))
    no_num = [c["code"] for c in countries if not c.get("num")]
    print("  无数字码(地图无轮廓):", no_num if no_num else "无")

    print("== 读取资源 ==")
    d3 = read_local("d3.min.js", "https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js")
    topo = read_local("topo.min.js", "https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js")
    world = read_local("world.json", "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json")
    # world.json 必须是合法 topojson
    wj = json.loads(world)
    assert "objects" in wj and "countries" in wj["objects"], "world.json 结构异常"
    print("  世界地图要素: %d" % len(wj["objects"]["countries"]["geometries"]))

    print("== 生成 index.html ==")
    tpl = open(os.path.join(BASE, "template.html"), encoding="utf-8").read()
    data_js = json.dumps(countries, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    def inline(js):
        return js.replace("</script", "<\\/script")
    out = (tpl
           .replace("__HERMES_D3_JS__", inline(d3))
           .replace("__HERMES_TOPO_JS__", inline(topo))
           .replace("__HERMES_WORLD_JSON__", world)
           .replace("__HERMES_DATA_JSON__", data_js))
    # 校验所有 marker 都已替换
    for m in ["__HERMES_D3_JS__", "__HERMES_TOPO_JS__", "__HERMES_WORLD_JSON__", "__HERMES_DATA_JSON__"]:
        if m in out:
            print("!! 未替换的 marker: %s" % m); sys.exit(1)
    dst = os.path.join(BASE, "index.html")
    open(dst, "w", encoding="utf-8").write(out)
    print("  输出: %s (%.1f KB)" % (dst, os.path.getsize(dst) / 1024))

    # 最终 JS 语法冒烟：用 node 检查内嵌 data JSON 可解析
    try:
        import subprocess, tempfile
        tf = os.path.join(tempfile.gettempdir(), "flags_data_check.json")
        open(tf, "w", encoding="utf-8").write(data_js)
        r = subprocess.run(["node", "-e", "JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));console.log('data JSON ok')", tf],
                           capture_output=True, text=True, timeout=30)
        print("  node 语法检查:", r.stdout.strip() or r.stderr.strip()[:300])
    except Exception as e:
        print("  node 检查跳过:", e)
    print("== 完成 ==")

if __name__ == "__main__":
    main()
