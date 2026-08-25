# English character name translations.
#
# Ren'Py 的 `translate LANG python:` 块只在切到那个语言时执行一次。
# 切到 English 之后再切回中文 (Language(None))，Ren'Py 不会"复位"
# Character.name —— mutation 留在 .name 里，名字框还是英文。
# 解决：给原语言 (None) 也写一个对称块，每次切回中文都重新赋值。
translate None python:

    ## 主要角色（中文复位 —— 见上方注释）
    wangshuang.name = "王霜"
    wangshuang_unknown.name = "王霜（？）"
    wangshuang_clerk.name = "王霜（店员）"
    wangshuang_clerk2.name = "王霜（店员2）"
    ahe.name = "阿鹤"
    shishou.name = "尸首"

    ## 配角
    lurenjia.name = "路人甲"
    lurenyi.name = "路人乙"
    lurenbing.name = "路人丙"
    lurending.name = "路人丁"
    jieluowa.name = "杰罗瓦"
    mijie.name = "米姐"
    youliya.name = "尤里娅"

translate english python:

    ## Main characters
    wangshuang.name = "Wang Shuang"
    wangshuang_unknown.name = "Wang Shuang (?)"
    wangshuang_clerk.name = "Wang Shuang (Clerk)"
    wangshuang_clerk2.name = "Wang Shuang (Clerk 2)"
    ahe.name = "Kaku"
    shishou.name = "The Corpse"

    ## Supporting characters
    lurenjia.name = "Passerby A"
    lurenyi.name = "Passerby B"
    lurenbing.name = "Passerby C"
    lurending.name = "Passerby D"
    jieluowa.name = "Jerowald"
    mijie.name = "Sister Mi"
    youliya.name = "Julia"

translate english strings:

    old "语言 / Language"
    new "Language"

    old "确定要删除所有存档吗？此操作无法撤销。"
    new "Delete all saves? This cannot be undone."

    old "确定要清除所有通关进度吗？\n（已解锁的路线和结局将被重置）\n此操作无法撤销。"
    new "Clear all progress?\n(Unlocked routes and endings will be reset)\nThis cannot be undone."
