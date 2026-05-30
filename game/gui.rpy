## gui.rpy
## GUI 配置文件 / GUI Configuration

init offset = -2

## 初始化 GUI 系统 - 这是必需的！
init python:
    gui.init(1920, 1080)

################################################################################
## 颜色配置
################################################################################

## 强调色，用于标题和标签
define gui.accent_color = '#ffffff'

## 用于文字按钮的颜色（未选中/悬停/选中/不可用）
define gui.idle_color = '#aaaaaa'
define gui.idle_small_color = '#888888'
define gui.hover_color = '#ffffff'
define gui.selected_color = '#ffffff'
define gui.insensitive_color = '#555555'

## 用于对话和菜单选项的颜色
define gui.text_color = '#ffffff'
define gui.interface_text_color = '#ffffff'
define gui.muted_color = '#666666'
define gui.hover_muted_color = '#999999'

################################################################################
## 字体配置
################################################################################

## 正文/界面/标题字体 - 思源宋体 Medium（简体中文衬线体）
## body.ttf 由 generate_font_subset.py 生成
define gui.text_font = "body.ttf"
define gui.name_text_font = "body.ttf"
define gui.interface_text_font = "body.ttf"

## 周目标题卡片沿用正文字体
define gui.title_card_font = gui.text_font

################################################################################
## 字体大小
################################################################################

## 对话文字大小
define gui.text_size = 33

## 角色名字大小
define gui.name_text_size = 38

## 界面文字大小
define gui.interface_text_size = 33
define gui.label_text_size = 36
define gui.notify_text_size = 24
define gui.title_text_size = 75

################################################################################
## 对话框设置
################################################################################

## 对话框位置和大小
define gui.textbox_height = 340
define gui.textbox_yalign = 1.0

## 角色名字位置（相对于对话框窗口，窗口宽 1400 居中）
define gui.name_xpos = 100
define gui.name_ypos = 15
define gui.name_xalign = 0.0

## 对话文字位置（相对于对话框窗口）
define gui.dialogue_xpos = 142
define gui.dialogue_ypos = 75
define gui.dialogue_width = 1116
define gui.dialogue_text_xalign = 0.0

################################################################################
## 按钮设置
################################################################################

define gui.button_width = None
define gui.button_height = None
define gui.button_borders = Borders(6, 6, 6, 6)
define gui.button_tile = False

define gui.button_text_font = gui.interface_text_font
define gui.button_text_size = gui.interface_text_size
define gui.button_text_idle_color = gui.idle_color
define gui.button_text_hover_color = gui.hover_color
define gui.button_text_selected_color = gui.selected_color
define gui.button_text_insensitive_color = gui.insensitive_color

## Quick button
define gui.quick_button_borders = Borders(15, 6, 15, 6)
define gui.quick_button_tile = False
define gui.quick_button_text_size = 21
define gui.quick_button_text_idle_color = gui.idle_small_color
define gui.quick_button_text_hover_color = gui.hover_color
define gui.quick_button_text_selected_color = gui.selected_color

## Navigation button
define gui.navigation_button_width = 300
define gui.navigation_button_height = None
define gui.navigation_button_borders = Borders(6, 6, 6, 6)
define gui.navigation_button_tile = False
define gui.navigation_button_text_size = gui.interface_text_size
define gui.navigation_button_text_idle_color = gui.idle_color
define gui.navigation_button_text_hover_color = gui.hover_color
define gui.navigation_button_text_selected_color = gui.selected_color

## Radio button
define gui.radio_button_borders = Borders(28, 6, 6, 6)
define gui.radio_button_tile = False
define gui.radio_button_text_idle_color = gui.idle_color
define gui.radio_button_text_hover_color = gui.hover_color
define gui.radio_button_text_selected_color = gui.selected_color

## Check button
define gui.check_button_borders = Borders(28, 6, 6, 6)
define gui.check_button_tile = False
define gui.check_button_text_idle_color = gui.idle_color
define gui.check_button_text_hover_color = gui.hover_color
define gui.check_button_text_selected_color = gui.selected_color

## Confirm button
define gui.confirm_button_borders = Borders(60, 10, 60, 10)
define gui.confirm_button_tile = False
define gui.confirm_button_text_idle_color = gui.idle_color
define gui.confirm_button_text_hover_color = gui.hover_color

## Page button
define gui.page_button_borders = Borders(15, 6, 15, 6)
define gui.page_button_tile = False

## Slot button
define gui.slot_button_tile = False

################################################################################
## 选项按钮（游戏内选择支）
################################################################################

define gui.choice_button_width = 1185
define gui.choice_button_height = None
define gui.choice_button_tile = False
define gui.choice_button_borders = Borders(150, 8, 150, 8)
define gui.choice_button_text_font = gui.text_font
define gui.choice_button_text_size = gui.text_size
define gui.choice_button_text_xalign = 0.5
define gui.choice_button_text_idle_color = '#cccccc'
define gui.choice_button_text_hover_color = '#ffffff'
define gui.choice_button_text_insensitive_color = '#444444'

################################################################################
## 存档/读档按钮
################################################################################

define gui.slot_button_width = 414
define gui.slot_button_height = 309
define gui.slot_button_borders = Borders(15, 15, 15, 15)
define gui.slot_button_text_size = 21
define gui.slot_button_text_xalign = 0.5

## 存档网格
define gui.file_slot_cols = 3
define gui.file_slot_rows = 2

################################################################################
## 滑块配置
################################################################################

define gui.slider_size = 44
define gui.slider_tile = False
define gui.slider_borders = Borders(6, 6, 6, 6)

define gui.vslider_borders = Borders(6, 6, 6, 6)

################################################################################
## 历史记录（回顾）
################################################################################

define gui.history_height = 210
define gui.history_name_xpos = 233
define gui.history_name_ypos = 0
define gui.history_name_width = 233
define gui.history_name_xalign = 1.0
define gui.history_text_xpos = 255
define gui.history_text_ypos = 3
define gui.history_text_width = 1110
define gui.history_text_xalign = 0.0

################################################################################
## NVL 模式（如果需要）
################################################################################

define gui.nvl_borders = Borders(0, 15, 0, 30)
define gui.nvl_height = 173
define gui.nvl_spacing = 15
define gui.nvl_name_xpos = 645
define gui.nvl_name_ypos = 0
define gui.nvl_name_width = 225
define gui.nvl_name_xalign = 1.0
define gui.nvl_text_xpos = 675
define gui.nvl_text_ypos = 12
define gui.nvl_text_width = 885
define gui.nvl_text_xalign = 0.0
define gui.nvl_thought_xpos = 360
define gui.nvl_thought_width = 1170
define gui.nvl_thought_xalign = 0.0
define gui.nvl_button_xpos = 675
define gui.nvl_button_xalign = 0.0

################################################################################
## 快捷键
################################################################################

init python:
    config.keymap['game_menu'].append('mouseup_3')  # 右键打开菜单
    config.keymap['hide_windows'].append('mouseup_2')  # 中键隐藏界面
