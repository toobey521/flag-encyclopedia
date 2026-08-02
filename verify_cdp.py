# -*- coding: utf-8 -*-
"""世界国旗图鉴 CDP 端到端验证脚本。
前置: python -m http.server 18766 --directory 桌面/国旗图鉴  &  headless chrome 9223
用法: python verify_cdp.py
"""
import json, urllib.request, websocket, time, base64, sys

CDP = '9223'
URL = 'http://localhost:18766/index.html'

tabs = json.loads(urllib.request.urlopen('http://localhost:%s/json' % CDP).read())
page = [t for t in tabs if t['type'] == 'page'][0]
ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=40)
mid = 0

def cmd(method, params=None):
    global mid
    mid += 1
    ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == mid:
            return r

def js(expr):
    r = cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    return r.get('result', {}).get('result', {}).get('value')

def shot(path):
    r = cmd('Page.captureScreenshot', {'format': 'png'})
    open(path, 'wb').write(base64.b64decode(r['result']['data']))
    print('截图:', path)

cmd('Page.enable')
cmd('Page.addScriptToEvaluateOnNewDocument', {'source': "window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(e.message+' @'+(e.lineno||'?'))});"})
cmd('Page.navigate', {'url': URL})
time.sleep(4)

print('== 基本信息 ==')
print('标题:', js('document.title'))
print('国家总数:', js('COUNTRIES.length'))
print('卡片渲染数:', js("document.querySelectorAll('#grid .card').length"))
print('大洲统计:', js('JSON.stringify(COUNTRIES.reduce(function(a,c){a[c.continent]=(a[c.continent]||0)+1;return a},{})).replace(/\\"/g,"")'))
print('数据字段完整(缺失字段数):', js('COUNTRIES.filter(function(c){return ["code","zh","en","continent","capital","area","population","language","currency","resources","tourism","intro"].some(function(k){return !c[k]})}).length'))

print('\n== 筛选测试 ==')
js("document.querySelectorAll('#pills .pill')[1].click()")  # 亚洲
time.sleep(0.3)
print('选亚洲后卡片数:', js("document.querySelectorAll('#grid .card').length"))
js("document.getElementById('q').value='伦';renderCards()")
time.sleep(0.3)
print('搜索「伦」:', js("Array.from(document.querySelectorAll('#grid .card .cn')).map(function(e){return e.textContent}).join(\",\")"))
js("document.getElementById('q').value='';renderCards()")
js("document.querySelectorAll('#pills .pill')[0].click()")
time.sleep(0.3)

print('\n== 卡片点击 → 详情弹窗 ==')
js("document.querySelector('#grid .card').click()")
time.sleep(0.5)
print('弹窗显示:', js("document.getElementById('modalBack').className.includes('show')"))
print('弹窗国家:', js("document.getElementById('mZh').textContent"))
print('统计格数量:', js("document.querySelectorAll('.mstat').length"))
print('资源chips:', js("document.querySelectorAll('.chip').length"))
print('旅游条目:', js("document.querySelectorAll('.tour li').length"))
print('intro长度:', js("(document.getElementById('mIntro').textContent||'').length"))
shot('verify_modal.png')
js("closeDetail()")
time.sleep(0.4)

print('\n== 地图页 ==')
js("switchTab('map')")
time.sleep(2.0)
print('地图svg存在:', js("!!document.querySelector('#mapBox svg')"))
print('地图国家路径数:', js("document.querySelectorAll('#mapBox .map-land').length"))
print('大洲按钮数:', js("document.querySelectorAll('#mapCont .cbtn').length"))
shot('verify_map.png')

print('\n== 地图点击国家 → 详情 ==')
r = js("(function(){var p=document.querySelector('#mapBox .map-land');var c=null;/* 模拟点击中国 */var cn=Array.from(document.querySelectorAll('#mapBox .map-land')).find(function(x){return x.__data__ && x.__data__.id==='156'});if(cn){cn.dispatchEvent(new MouseEvent('click',{bubbles:true}))};return cn?cn.__data__.id:'notfound'})()")
time.sleep(0.6)
print('点击中国(feature 156):', r)
print('弹窗国家:', js("document.getElementById('mZh').textContent"))
js("closeDetail()")
time.sleep(0.3)

print('\n== 大洲定位 ==')
js("flyToContinent('非洲')")
time.sleep(1.0)
print('非洲定位transform:', js("d3.zoomTransform(document.querySelector('#mapBox svg')).k"))

print('\n== 搜索定位 ==')
js("document.getElementById('mapQ').value='巴西';mapSearch()")
time.sleep(1.0)
print('巴西搜索→弹窗:', js("document.getElementById('mZh').textContent"))
js("closeDetail()")

print('\n== 弹窗内「在地图上查看」==')
js("openDetail('cn')")
time.sleep(0.4)
js("viewOnMap()")
time.sleep(1.2)
print('切换到地图tab:', js("document.getElementById('tab-map').style.display"))
print('缩放级别(应>1):', js("d3.zoomTransform(document.querySelector('#mapBox svg')).k"))
shot('verify_final.png')

print('\n== 控制台错误 ==')
errs = js("(window.__errs||[])")
print('错误数:', len(errs) if errs else 0)
ws.close()
print('ALL VERIFY DONE')
