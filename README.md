# 🌏 世界国旗图鉴 (World Flag Encyclopedia)

**Toobey · 201 个国家和地区的国旗与百科大全**

在线访问：https://toobey521.github.io/flag-encyclopedia/

## 功能

- **🏳️ 卡片图鉴**：201 个国家/地区卡片（国旗 + 大洲 + 首都 + 人口），支持大洲筛选、关键词搜索、按名称/人口/面积排序，点击弹出详情（首都/面积/人口/语言/货币/自然资源/旅游经典/详细介绍）
- **🗺️ 世界地图**：交互式世界地图（中国居中版式），滚轮缩放、拖拽平移、大洲一键定位、搜索直达，点击国家弹出详情，与卡片页双向联动
- **详情弹窗**：每个国家/地区含 12 项完整数据，支持"在地图上查看"跳转
- **离线可用**：d3 + 世界地图数据全部内嵌单文件，国旗走 jsDelivr CDN（断网自动降级）

## 使用

双击 `index.html` 即可本地使用，或访问上方在线地址。

## 项目结构

```
├── index.html        # 单文件成品（双击即用）
├── template.html     # UI 模板（含注入点标记）
├── build.py          # 构建脚本：数据校验 + 内嵌 d3/地图数据 → 生成 index.html
├── verify_cdp.py     # headless Chrome CDP 端到端验证脚本
└── data/             # 5 大洲数据文件（Python 模块，共 201 条）
    ├── asia.py       # 51
    ├── europe.py     # 44
    ├── africa.py     # 55
    ├── americas.py   # 37
    └── oceania.py    # 14
```

## 重新构建

```bash
python build.py   # 读取 data/*.py → 校验 → 生成 index.html
```

数据为公开资料约数（2020-2024），仅供参考。国旗来源 [flag-icons](https://github.com/lipis/flag-icons)，地图数据 [Natural Earth](https://www.naturalearthdata.com/)。

© 2026 Toobey
