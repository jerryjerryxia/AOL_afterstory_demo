## test_suite.rpy
## Test Suite for AOL Afterstory Demo

################################################################################
## Test Configuration
################################################################################

init python:
    _test.timeout = 15.0

################################################################################
## DEMO PLAYTHROUGH TESTS
################################################################################

testcase demo_playthrough_path_a:
    description "Demo - Path A: All first choices (no madness)"

    $ preferences.text_cps = 0
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

    $ preferences.text_cps = 0
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

    $ preferences.text_cps = 0
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

    $ preferences.text_cps = 0
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

    $ preferences.text_cps = 0
    run Start()

    advance until screen "route_title"
    assert screen "route_title"

    # Return to main menu to clean up game context
    run MainMenu(confirm=False)


testcase test_choice_screen:
    description "Test choice menu screen appears at first decision"

    $ preferences.text_cps = 0
    run Start()

    advance until screen "route_title"
    click

    advance until "不对劲"
    assert screen "choice"

    # Return to main menu to clean up game context
    run MainMenu(confirm=False)
