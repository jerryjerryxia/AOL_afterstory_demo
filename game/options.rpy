## options.rpy
## 游戏基本配置 / Basic game configuration

## 游戏基本信息
define config.name = _("无休夏日综合症")
define config.version = "1.0.3"
define build.name = "EndlessSummerSyndromeDemo"

## 是否显示游戏名称在主菜单
define gui.show_name = True

## 游戏存档目录名称
define config.save_directory = "EndlessSummerSyndromeDemo-1234567890"

## 分辨率配置 - 1920x1080 基准
define config.screen_width = 1920
define config.screen_height = 1080

## 游戏图标
define config.window_icon = "images/ui/icon/game_icon.png"

## 默认语言为中文（None 表示使用 script 中的原始文本）
define config.language = None

## 默认音量
define config.default_music_volume = 0.8
define config.default_sfx_volume = 0.8

## 允许跳过未读文本
define config.allow_skipping = True

## 对话历史记录的条数上限。引擎默认是 None = 完全不记录 —— 项目模板本该带
## 这行但这里一直缺失，导致"历史"界面永远显示"没有历史"。250 是官方模板值。
## （历史文本里的 {w} 点击停顿标签由 history 界面的 filter_text_tags 过滤，
## 不会显示出来。）
define config.history_length = 250

## 存档缩略图大小
## 存档截图尺寸。必须与 gui.slot_button_width/height 一致 —— 存档界面的槽位
## 就是这张截图本身（见 screens.rpy 的 slot_button），尺寸对不上就会出现
## 图浮在框里、四边留白不均的样子。16:9，和游戏分辨率同比例。
define config.thumbnail_width = 448
define config.thumbnail_height = 252

## 存档槽数量
define config.has_autosave = True
define config.autosave_slots = 5

## 音频通道设置
define config.has_music = True
define config.has_sound = True

## 过渡效果
define config.enter_transition = dissolve
define config.exit_transition = dissolve
define config.intra_transition = dissolve
define config.after_load_transition = dissolve
define config.end_game_transition = dissolve

## 窗口标题
## 窗口标题（系统级别的窗口栏文字。无法通过翻译动态切换，保持中文原名。）
define config.window_title = "无休夏日综合症"

## 主菜单音乐：glitter_in_the_dark。序章首曲也是它，且 set_scene_music 用 if_changed，
## 所以从主菜单到点"开始游戏"进序章，这首曲子无缝连续播放、不重启。整曲从头循环到尾。
## <volume 0.3>：序章首曲，刻意压得较轻（原 0.737≈-16.5 LUFS）。
## 必须与 music_config.rpy 里 polyhedron 轨的 volume 逐字一致，set_scene_music 会拼出
## 同样的前缀，if_changed 才认作同一首（否则主菜单→序章会重启这首）。
define config.main_menu_music = "<volume 0.3>audio/bgm/glitter_in_the_dark.ogg"

## 游戏菜单 - ESC/右键打开存档界面
define config.game_menu_action = ShowMenu("save")

## 层级定义（保留默认层级，添加自定义层）
## 默认层级: master, transient, screens, overlay
## 不要覆盖 config.layers，而是使用 config.tag_layer 来指定特定图像的层

## 默认文字速度和自动前进时间
default preferences.text_cps = 30
default preferences.afm_time = 15

## Steam / 发行配置
init python:
    ## 构建配置
    ## ★ 开发/隐私文件——绝不打包进发行版 ★
    ## Ren'Py 分类「先匹配先生效」，且末尾自带 ('**','all') catch-all，所以这些排除
    ## 规则必须排在下面所有 'all' 规则之前。以后调整打包范围时，保持它们在最前面。
    build.classify('client_secret_*.json', None)        # Google OAuth 密钥（绝不外发）
    build.classify('token.json', None)                  # Google API 令牌（绝不外发）
    build.classify('**/client_secret_*.json', None)
    build.classify('**/token.json', None)
    build.classify('CLAUDE.md', None)                   # Claude 项目说明
    build.classify('PLAN.md', None)                     # 策划稿
    build.classify('chapters.txt', None)
    build.classify('convergence.txt', None)
    build.classify('demo_script*.txt', None)            # 源文稿（生成 game/scripts/*.rpy）
    build.classify('**.before_merge', None)             # merge 备份
    build.classify('tmpclaude-*', None)                 # Claude 临时工作文件
    build.classify('tools/**', None)                    # 字体子集源缓存（generate_font_subset 下载）
    build.classify('tests/**', None)
    build.classify('**/__pycache__/**', None)
    build.classify('game/SourceHanSansLite.ttf', None)  # 旧全字体，代码未引用（现用 body.ttf 子集）
    build.classify('game/test_suite.rpyc', None)        # QA 测试，玩家用不到
    ## 处理前的原始素材：游戏只播成品（webm / ogg / 限幅后的 _bed），母带一律不打包。
    ## 之前没有这两条，55 MB 的 bgm/masters WAV + 34 MB 的 _video_masters MP4 每次
    ## 都跟着发行版一起走了 —— 玩家下载了 89 MB 永远不会被读取的文件。
    build.classify('game/audio/**/masters/**', None)    # 音频母带（bgm/ 与 sfx/ 下）
    build.classify('game/images/bg/_video_masters/**', None)  # 视频母带 MP4

    build.classify('**~', None)
    build.classify('**.bak', None)
    build.classify('**/.**', None)
    build.classify('**/#**', None)
    build.classify('**/thumbs.db', None)
    build.classify('**.rpy', None)
    build.classify('**.psd', None)
    build.classify('**.txt', 'all')
    build.classify('game/**.png', 'all')
    build.classify('game/**.jpg', 'all')
    build.classify('game/**.ogg', 'all')
    build.classify('game/**.mp3', 'all')
    build.classify('game/**.wav', 'all')
    build.classify('**', 'all')
