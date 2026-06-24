## test_suite.rpy
## Test Suite for Endless Summer Syndrome Demo

################################################################################
## Test Configuration
################################################################################

init python:
    ## 旁白的「逐句点击」现在由运行时 {w} 实现，整个序章约 138 个点击点。测试框架
    ## 默认把帧率压到 10fps（renpy/test/testexecution.py），每个点击点要等 1~2 帧，
    ## 138 点 → ~30s 走不完到 route_title。关掉限帧让 advance 全速推进，15s 即够。
    ## {w} 仍照常被测试驱动（当初就是它抓到了 id "what" 不一致的 bug）。
    _test.maximum_framerate = False
    _test.timeout = 20.0

    ## Tests need instant text, but `preferences.text_cps` is a PERSISTED
    ## preference — naively setting it to 0 leaves the player's text speed
    ## stuck on "instant" after a test run (worse if a test aborts mid-run).
    ## So we snapshot the real value the first time a test speeds up text, and
    ## restore it when Ren'Py exits. at_exit runs after autosaves settle
    ## (renpy/main.py), so restoring the in-memory value there — plus an
    ## explicit save_persistent() — guarantees the final on-disk value is the
    ## player's, not 0.
    ## 测试用 Chinese choice 文本匹配（"不对劲"/"疯了"…），但 _preferences.language
    ## 是 PERSISTED 的——如果上次有人切到 english 并留在存档里，测试就会在英文界面
    ## 里永远找不到中文选项、卡在第一个 menu。所以测试开始时把语言钉到中文（None），
    ## 退出时和 text_cps 一样还原成玩家原本的语言，绝不把测试语言写回玩家存档。
    def _test_fast_text():
        if not hasattr(store, "_test_saved_text_cps"):
            store._test_saved_text_cps = preferences.text_cps
        preferences.text_cps = 0
        if not hasattr(store, "_test_saved_language"):
            store._test_saved_language = _preferences.language
        if _preferences.language is not None:
            renpy.change_language(None)

    def _test_restore_text():
        if hasattr(store, "_test_saved_text_cps"):
            preferences.text_cps = store._test_saved_text_cps
            del store._test_saved_text_cps
            renpy.save_persistent()
        if hasattr(store, "_test_saved_language"):
            ## 直接写回 preference（不走 change_language —— 退出阶段无需再触发重翻译）。
            _preferences.language = store._test_saved_language
            del store._test_saved_language
            renpy.save_persistent()

    if _test_restore_text not in config.at_exit_callbacks:
        config.at_exit_callbacks.append(_test_restore_text)

################################################################################
## DEMO PLAYTHROUGH TESTS
################################################################################

testcase demo_playthrough_path_a:
    description "Demo - Path A: All first choices (no madness)"

    $ _test_fast_text()
    run Start()

    advance until screen "route_title"
    click

    advance until "不对劲"
    click "不对劲"

    advance until "疯了"
    click "疯了"

    advance until "算了"
    click "算了"

    advance until "就这样睡去"
    click "就这样睡去"

    advance until screen "main_menu"


testcase demo_playthrough_path_b:
    description "Demo - Path B: All madness choices"

    $ _test_fast_text()
    run Start()

    advance until screen "route_title"
    click

    advance until "很有精神"
    click "很有精神"

    advance until "睡着了"
    click "睡着了"

    # Use exact choice text with punctuation
    advance until "接受。"
    click "接受。"

    advance until "更多。"
    click "更多。"

    advance until screen "main_menu"


################################################################################
## VARIABLE TESTS
################################################################################

testcase test_madness_increment:
    description "Test madness variable increments correctly with madness choices"

    $ _test_fast_text()
    run Start()

    assert eval madness == 0

    advance until screen "route_title"
    click

    advance until "很有精神"
    click "很有精神"
    assert eval madness == 1

    advance until "睡着了"
    click "睡着了"
    assert eval madness == 2

    # Return to main menu to clean up game context
    run MainMenu(confirm=False)


testcase test_no_madness:
    description "Test madness stays 0 with safe choices"

    $ _test_fast_text()
    run Start()

    assert eval madness == 0

    advance until screen "route_title"
    click

    advance until "不对劲"
    click "不对劲"
    assert eval madness == 0

    advance until "疯了"
    click "疯了"
    assert eval madness == 0

    # Return to main menu to clean up game context
    run MainMenu(confirm=False)


################################################################################
## UI SCREEN TESTS
################################################################################

testcase test_main_menu_buttons:
    description "Test main menu screen exists"

    assert screen "main_menu"


testcase test_route_title_screen:
    description "Test route title screen displays after prologue"

    $ _test_fast_text()
    run Start()

    advance until screen "route_title"
    assert screen "route_title"

    # Return to main menu to clean up game context
    run MainMenu(confirm=False)


testcase test_choice_screen:
    description "Test choice menu screen appears at first decision"

    $ _test_fast_text()
    run Start()

    advance until screen "route_title"
    click

    advance until "不对劲"
    assert screen "choice"

    # Return to main menu to clean up game context
    run MainMenu(confirm=False)


## NOTE: A regression test for the language-toggle-on-main-menu bug
## ("switch language → click Continue → lands in prologue instead of save")
## was attempted here. The honest situation:
##
##   - Ren'Py's testcase framework does not drive the `timer 1.25` on the
##     main_menu screen forward — the timer waits for real wall-clock time
##     that the framework speeds past, so click "Continue" + advance hangs
##     until the global 15s timeout.
##   - The bug itself is in screens.rpy::_force_refresh_text:
##     `renpy.rollback(defer=True)` queues a deferred rollback even when
##     called from main menu (where there is no current say to refresh).
##     The deferred rollback fires on the next interaction — which is
##     usually the player clicking Continue. After the load, the rollback
##     rewinds one checkpoint from the saved state, landing the player in
##     prologue.
##   - Fix: _force_refresh_text early-returns when renpy.store.main_menu
##     is True. Verified manually via the actual player flow.
##
## If you have a more reliable way to drive the timer screen statement
## forward in testcase, plug a regression test in here.
