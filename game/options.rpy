## options.rpy
## 游戏基本配置 / Basic game configuration

## 游戏基本信息
define config.name = _("无休夏日综合症")
define config.version = "1.0.2"
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

## 存档缩略图大小
define config.thumbnail_width = 384
define config.thumbnail_height = 216

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
## <volume 0.737>：响度配平到 -16.5 LUFS —— 必须与 music_config.rpy 里 polyhedron
## 轨的 volume 逐字一致，set_scene_music 会拼出同样的前缀，if_changed 才认作同一首。
define config.main_menu_music = "<volume 0.737>audio/bgm/glitter_in_the_dark.ogg"

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
