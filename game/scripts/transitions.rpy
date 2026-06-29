## transitions.rpy
## 场景转场效果定义 / Scene Transition Definitions
##
## 在此统一调整全游戏的转场手感。route .rpy 由 convert_script.py 生成，
## 转场与特效处会引用下面这些名字。

## 默认场景转场 —— 经过黑场的淡入淡出（淡出 0.4s / 黑场停留 0.1s / 淡入 0.5s）
## 比纯溶解更明确：无论前后背景多相似，黑场都能让"换场"被清楚感知。
define scene_soft = Fade(0.4, 0.1, 0.5)

## 白屏 → 甜品店：较长的"屏幕逐渐黑下来"过渡。淡出到黑 1.5s / 黑场停留 0.3s /
## 淡入 0.8s。比 scene_soft 更慢更重，给"光褪去、世界沉入黑暗再浮现"的感觉。
define fade_to_black_long = Fade(1.5, 0.3, 0.8)

## 同场景渐变 —— 直接交叉淡入淡出，不经过黑场。
## 用于"同一地点、同一时刻"内的视觉渐变（甜品店对视 1→2→3...），让画面像
## 时间慢慢流过去那样彼此过渡，而不是每次都"切走又切回来"。
define scene_dissolve = Dissolve(0.8)

## 戏剧性瞬间的特效转场（由舞台提示关键词触发，见 convert_script.py 的 SPECIAL_FX）
define fx_glitch = hpunch    ## 故障 / glitch —— 横向震动
define fx_shock = vpunch     ## 惊吓 / 冲击 —— 纵向震动

## 【屏幕震动】专用的"剧烈版"屏幕震动（阿鹤惨叫处，见 convert_script.py）。
## 想调整剧烈程度就改这一行：
##   - 前两个点 (±X, ±Y) 是位移幅度：X 横向、Y 纵向，越大抖得越凶（vpunch 是纯纵向 10）。
##   - 第 3 个参数是单次位移时长，越小抖得越快越密。
##   - delay 是总时长，越大抖得越久。
## 现在是斜向对角抖动，同时含横向+纵向分量（想要更横就把 X 调大、Y 调小）。
define fx_quake = Move((28, 36), (-28, -36), .04, bounce=True, repeat=True, delay=.55)
