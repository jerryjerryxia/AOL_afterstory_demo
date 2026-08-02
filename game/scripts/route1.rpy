## route1.rpy
## Route 1

label route1_start:

## 一周目：浮潜

    call screen route_title(_("浮潜"), sfx="audio/sfx/bubbles/face-down-bubble.wav")
    $ wait_sfx()
    ## 转场：虚空对视
    show void default with scene_dissolve
    ## 背手站立，默认表情
    wangshuang "欢迎回来，阿鹤。"
    ahe "倒不如去死。"
    ## 背手站立，小吃惊表情
    wangshuang "哦？有趣的提议，为什么呢？"
    ahe "我...不好意思...我觉得我有点..."

    menu:
        extend ""
        "不对劲...":
            pass
        "很有精神！":
            $ madness += 1
            pass

    ## 抱胸站立，默认表情
    wangshuang "嗯，从之前的病史来看，你总在这两个状态之间来回反复，但现在具体是什么感觉呢？"
    ahe "..."
    ## 抱胸站立，无奈表情
    wangshuang "连这也说不出来么？"
    ## 背手站立，默认表情
    wangshuang "难说的话，或许聊聊你看到的，或者听到的，都是可以的，我在听呢。"
    ahe "我感觉...有某种暴戾的东西在我耳边一直说个不停，它想我去做一些非常恶毒的事情..."
    ## 抱胸站立，思索表情
    wangshuang "唔，这样。"
    ahe "我...又病了吗？"
    ## 左手食指竖起做讲解状，温柔表情，大概就是笑容比默认再明显一点吧
    wangshuang "不，恰恰相反，阿鹤。要我说，你现在就像太阳一样稳定。"
    ahe "太阳？"
    ## 背手站立，小吃惊表情
    wangshuang "哦，不好意思，太阳在那儿。"
    ## 玻璃破碎音效：glass-smash-normalized
    $ play_sfx("audio/sfx/glass_smash/glass-smash-normalized.wav")
    ## 转场：夏日对视
    scene bg_summergaze with scene_soft
    ## 场景背景里的黑暗碎裂，变为完美夏日，金色的沙滩和蔚蓝的海，只是一个人都没有
    ## 场景音乐参考风格1：樹氷の輝き (Shine of Silver Thaw)，夜の向日葵（The sunflower of the night），Running Waters - https://audionautix.com/Music/RunningWaters.mp3 (Jason Shaw)，Shianchu
    ## 场景音乐参考风格2：Jellyfish - https://audionautix.com/Music/Jellyfish.mp3  (Jason Shaw)
    $ set_scene_music("route1_scene1")
    ## 表情：大笑
    scene summergaze_laugh
    $ renpy.transition(Dissolve(0.2), layer="master")
    $ wait_sfx()
    wangshuang "你看，太阳。"
    ahe "嗯，太阳。"
    wangshuang "金色的，温暖的，让人舒适而安心的太阳，它就在那里。"
    wangshuang "对于沐浴日光中的人来说，明白这一点就够了。"
    ahe "可它分明是我视野里最暴烈、最盛气凌人的造物。"
    ## 表情：面无表情
    scene summergaze_blank
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "那就闭上眼睛，你的问题便迎刃而解了。"
    ahe "可我还是觉得我快要..."

    menu:
        extend ""
        "疯了...":
            pass
        "睡着了。":
            $ madness += 1
            pass

    ## 表情：默认
    scene summergaze_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "那也是无可厚非的事情。"
    ahe "那怎么可能是——"
    wangshuang "当然就是这样的，阿鹤。"
    ## 表情：小吃惊
    scene summergaze_surprised
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "这是你的心理咨询，你是来访者，而我是咨询师。"
    ahe "所以...我该怎样才能好起来？"
    wangshuang "修补本就完整的东西，那自然是做不到的。"
    ahe "..."
    ## 表情：面无表情
    scene summergaze_blank
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "你不同意。"
    ahe "...你...求求你不要再浪费我的时间了..."
    ## 表情：小声嘀咕
    scene summergaze_mutter
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "时间，你要那东西有什么用？"
    ahe "我还要——我还得..."
    ## 表情：默认
    scene summergaze_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "我在听。"
    wangshuang "不用紧张，阿鹤，你可以畅所欲言。"
    ahe "想不起来...什么都想不起来..."
    wangshuang "想想你为什么来到这里，或者想想你用你先前的时间做了什么事，都能帮助你回忆过去。"
    wangshuang "但即使什么也想不起来也不必懊恼，那是意料之中的过程。"
    ahe "这...这肯定又是你的把戏！"
    ## 表情：小声嘀咕
    scene summergaze_mutter
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "总是向外归因可解决不了问题啊，我的朋友。"
    wangshuang "你的病虽然看起来已经根治了，但以你的身心状态而言，任何时候复发我都不意外。"
    wangshuang "但你还是没回答我的问题——时间对现在的你而言，有什么用？"
    ahe "没用...完全没用...一切都结束了..."
    ## 表情：小吃惊
    scene summergaze_surprised
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "哦？所以还是想起来了一些。"
    ahe "你...毁掉了整个逝乐园。"
    ## 表情：大笑
    scene summergaze_laugh
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "不必谦虚啊，阿鹤，这件事少了你是绝对不可能成功的。"
    wangshuang "所以我愿意把领衔主演的名头让给你，我去当制片人就可以了。"
    ## 表情：默认
    scene summergaze_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "你也不用觉得我抬举你，过度谦虚只会让人习惯性地逃避责任，是一种需要调整的心态。"
    ahe "我..."
    ## 表情：面无表情
    scene summergaze_blank
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "嗯，我懂的，在完成一件惊人的壮举后，出现冒充者综合征是非常常见的事情。"
    wangshuang "但不论你怎么想，事已至此，还是放平心态最重要。"
    ahe "...随便了..."
    wangshuang "哎你看你这人，三天两头向外归因，遇事不决就无视问题——"
    ## 表情：小声嘀咕
    scene summergaze_mutter
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "{size=-10}这就是为什么我——{/size}"
    ahe "什么？"
    ## 表情：默认
    scene summergaze_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "没事。没事。阿鹤，你知道太阳为什么会死吗？"
    ahe "因为它想死。"
    ## 表情：面无表情
    scene summergaze_blank
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "错——太阳自出生的那一刻起便像氢弹般持续自毁，早就动了死的念头，但它还是在天上烧了四十多亿年。"
    ahe "我不明白..."
    ## 表情：默认
    scene summergaze_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "你当然不明白，你肯定在想‘可这明明也是一种外因，毕竟整个太阳系都齐心协力地求它继续活下去’。"
    ahe "唔..."
    ## Extended文本框开始 - accumulating textbox
    ## 表情：面无表情
    scene summergaze_blank
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "然而现实恰恰相反——太阳不死仅仅是因为它的使命尚未完成而已。而它的死与它或其他任何造物的想法没有半点关系。"
    ## Extended文本框结束
    ## Extended文本框开始 - accumulating textbox
    ## 表情：小声嘀咕
    scene summergaze_mutter
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "想法是轻薄的、由外界塑造的，一坨烂泥一样谁都可以捏一把，但同时也是无足轻重的。而使命则是彻头彻尾、由内而外的——只有在‘使命’松手之后，‘想法’才配拥有虚假的自由。"
    ## Extended文本框结束
    ahe "这和我们又有什么关系？"
    ## 表情：默认
    scene summergaze_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "当然有关系了，不然你怎么会出现在这里？"
    ahe "我从来没有想过要出现在这里..."
    wangshuang "嗯，‘你’当然不想。"
    ahe "所以我在这里做什么？"
    wangshuang "你会明白的。"
    ahe "好吧...如果一切都无需解释，那我就只能在这里和你开瞪眼大赛了。"
    wangshuang "你也可以认为这只是一种较为朴素的过程而已。"
    ahe "...？"
    wangshuang "嗯，就是那样，过多的言语会污染概念。你还是不要再多探究了为好。"
    ahe "哦...对对对...懂了..."
    ## 表情：大笑
    scene summergaze_laugh
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "但话说回来，瞪眼大赛啊，我接受挑战！"
    ahe "没说真要来啊..."
    ## 表情：面无表情
    scene summergaze_blank
    $ renpy.transition(Dissolve(0.2), layer="master")
    show screen op_lock(2)
    wangshuang "盯——"
    hide screen op_lock
    ahe "..."
    show screen op_lock(2)
    wangshuang "盯——"
    hide screen op_lock
    ahe "..."
    wangshuang "噗——"
    ahe "..."
    ## 表情：大笑
    scene summergaze_laugh
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "——噗噗呃啊——我败了..."
    ahe "自取其辱啊，阿霜。"
    ## 表情：小声嘀咕
    scene summergaze_mutter
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "你还有脸得意！能盯着你那张臭脸看这么久还不笑的就只有死人了。"
    ahe "嗯...所以我每天刷牙的时候都要死一次..."
    wangshuang "你能活到今天确实不容易。"
    ahe "还不是拜你所赐..."
    ## 表情：默认
    scene summergaze_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "不用谢不用谢。那你来吧，拿走你的战利品。"
    ahe "哈？"
    wangshuang "别哈，让你来你就来。"
    ## 屏幕缩放，显得王霜近了很多
    ahe "是什么东西？"
    ## 表情：面无表情
    scene summergaze_blank
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "你看就是了。"
    ## 转场：张目对日pt1
    scene bg_sungaze with scene_soft
    ## 王霜右手轻轻握拳，阳光透过其中细小的孔洞透了过来
    ahe "什么都看不到。"
    wangshuang "凑近啊你，看仔细点！"
    ahe "啊你别拽我！"
    wangshuang "对准，仔细看好了。"
    ## Extended文本框开始 - accumulating textbox
    ahe "呃...嗯？"
    with fx_quake
    extend "——啊啊啊啊啊啊啊啊啊啊啊！"
    ## Extended文本框结束
    ## 背景开始旋转，白屏逐渐溢满了整个屏幕
    ## 右侧Split Extended大文本框开始 - 右半屏分页
    split_right_page_narrator "自你双眼完成聚焦的一瞬，一阵刺眼的光晕便抹去了视野里的一切，仿佛王霜把天上那轮烈日移植进了你的眼球。"
    extend "\n你立刻合上双眼，整张脸上的肌肉拧成一团，死死地挤压你抽搐的眼帘，但为时已晚，那令人绝望的强光已经在你脑海的更深处生了根。"
    split_right_page_narrator "随着炫目的光而来的是蚀骨的火。这由内而外的火顺着你的双眼、你的视神经蔓延。后脑勺烧了起来，随后是整个大脑皮层，最终你的全身都在这挥之不去的炫光中熊熊灼烧。"
    ## 右侧Split Extended大文本框结束
    ## 右侧Split Extended大文本框开始 - 右半屏分页
    split_right_page_narrator "你将身躯团成球状、死死绷住全身肌肉以抵御这钻心之痛，但在光与火的风暴面前也只是杯水车薪。"
    extend "\n就像太阳一般稳定..."
    extend "\n你想立刻去死，那是缓解疼痛的唯一方法，但你非常清楚，此刻死亡就和使命一样遥不可及。"
    ## 右侧Split Extended大文本框结束
    ## 转场：白屏
    scene bg_white_video with scene_soft
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "去找啊，否则这疼痛就永远不会有尽头。"
    extend "\n去别处，就是这样。"
    extend "\n否则这疼痛就永远不会有尽头。"
    extend "\n你的大脑不会适应，你也绝无希望自我了断。"
    extend "\n只能迈开步子。"
    extend "\n只有这一个选择。"
    extend "\n去找吧。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "去无人的深海。"
    extend "\n去银白的沙漠。"
    extend "\n去漆黑的深渊。"
    extend "\n去伸手。"
    extend "\n去坠落。"
    extend "\n去沉默。"
    extend "\n直到你再次回到这里为止。"
    ## Extended大文本框结束
    ## 白屏逐渐褪去
    ## 转场：甜品店对视1
    ## 长黑场过渡（不可点击快进）
    stop music fadeout 3.0
    show black zorder 100:
        alpha 0.0
        linear 3.0 alpha 1.0
    $ hard_pause(3.0)
    $ hard_pause(0.5)
    scene bg_dessertgaze1
    show black zorder 100:
        alpha 1.0
        linear 2.0 alpha 0.0
    $ hard_pause(2.0)
    hide black
    ## 一家疑似餐厅的背景，又是王霜和阿鹤面对面坐着
    ## 场景音乐风格参考：怎么说呢...虽然台词可能对抗感比较强，但这种场景还是得要一些 lo-fi 小调啊...Moonlit Reverie - 好lofi，Hoyoku, Sutekimeppou - 这几首物语的 ost 也很有内味儿嗷
    $ set_scene_music("route1_scene2")
    ahe "呃啊——！"
    ## 表情：疑惑
    scene dessert1_puzzled
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "怎么了？"
    ahe "你刚刚...是不是对我做了非常不得了的事情。"
    ## 表情：撇嘴
    scene dessert1_pout
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "你盯着我发呆，我盯着你发呆，确实挺不得了的。"
    ahe "呃...所以我们为什么在这里？"
    wangshuang "这可是你说要来的。"
    ahe "那我要走了。"
    ## 表情：疑惑
    scene dessert1_puzzled
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "我们刚坐下诶，你要去哪儿？"
    ahe "不知道，要离开这里就是了。"
    ahe "...能麻烦开一下门吗？"
    ## 表情：默认
    scene dessert1_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "不如问问店家。"
    ahe "好吧...你好，能帮我把门开一下吗？"
    wangshuang "不好意思啊先生，老板刚才说了，今天店里的客人都必须留到天黑之后才能走。"
    ahe "可是天已经黑了。"
    wangshuang "老板说，还不够黑。"
    ahe "好吧...所以我能走了吗？"
    ## 表情：坏笑
    scene dessert1_smirk
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "不能。"
    ahe "你好烦。"
    ## 表情：撇嘴
    scene dessert1_pout
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "就算出去了，你准备做什么？"
    ahe "把大石头推上山，把琴弦拧成电缆，什么都可以。"
    wangshuang "意思是你准备换个地方无所事事。"
    ahe "再无所事事都胜过和你呆在这里。"
    ## 表情：疑惑
    scene dessert1_puzzled
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "啊，已经这么遭人嫌了么..."
    ahe "...多少有点自知之明吧你..."
    ## 表情：撇嘴
    scene dessert1_pout
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "彼此彼此咯，我们都只是遵循着强烈的愿望，尝试了一直以来想要尝试的事情。"
    ahe "区别在于我不需要人陪葬。"
    wangshuang "不，区别在于我做到了，而你没有。"
    ahe "..."
    ## 表情：默认
    scene dessert1_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "而你拒绝与我共处一室的真正原因只是嫉妒，仅此而已。"
    ahe "闭嘴吧..."
    ## 表情：坏笑
    scene dessert1_smirk
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "我闭嘴了又有什么用？难道你那苍白的“理想”就不需要人来陪葬了？"
    wangshuang "你为了{i}尤里娅{/i}那小姑娘折断了多少人的骨头？阿鹤，狡辩是没有意义的，无论如何我们都是逝乐园覆灭的共犯。"
    ahe "..."
    ## 转场：甜品店对视2
    scene bg_dessertgaze2 with scene_dissolve
    ## 表情：默认
    scene dessert2_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "所以不如放下成见，吃点团子，如何？"
    ## 默默吃一口
    ahe "..."
    ## 手中出现无色透明多面体
    wangshuang "这就对了嘛，来都来了。"
    ahe "..."
    wangshuang "有件事你可能不知道，他们家团子是加了{i}KAS{/i}才这么好吃的。"
    ahe "哦，所以之后我会上瘾？"
    wangshuang "也许。"
    ahe "也好吧。"
    ## 手中出现无色透明多面体，多面体形状略微改变
    wangshuang "靠染上新瘾来戒旧瘾可是个无底洞啊。"
    ahe "你自己不也在做同样的事情。"
    wangshuang "只是不想看着你和我坠入同样的深渊嘛，毕竟我还挺在乎你的。"
    ahe "别恶心我了，求你了。"
    ## 表情：撇嘴
    scene dessert2_pout
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "你这人，连真心话都不让人说。"
    ahe "你？真心话？笑话可以再冷点么？"
    wangshuang "连这都分不清，以后可是要吃大亏哦。"
    ## 手中出现无色透明多面体，多面体形状略微改变2
    wangshuang "哦，对，团子有得是，千万别客气，请吧——"
    ## 转场：甜品店对视3
    scene bg_dessertgaze3 with scene_dissolve
    ahe "明明刚说完不想我染上。"
    wangshuang "{i}KAS{/i}生理上确实不怎么成瘾啊。"
    wangshuang "但太多人会陷进它能让人看到的那些东西，最后心里离不开了，所以你才能在安息地见到那么多活死人。"
    wangshuang "那么你会怎样呢，阿鹤？我很期待哦。"
    ahe "只致幻的话岂不是很无聊，尤其对你来讲。"
    ## 表情：小激动
    scene dessert3_excited
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "无聊？可别太刺激了！你知道十二小时起步的感官过载是什么感觉吗？"
    wangshuang "五感全部推到极限，尤其是视觉，所有东西的颜色都比平时看到的要鲜艳无数倍，而且全都彼此交融，到最后视野里就是五彩斑斓的白。"
    ## Extended文本框开始 - accumulating textbox
    wangshuang "所有东西都是饱满到极致的，你懂我意思吗？那已经不单是感官上的饱满，而是存在上的饱满，第四维度上的饱满——是那种...不论我们怎么干涉都无法改变的状态。"
    ## Extended文本框结束
    ## Extended文本框开始 - accumulating textbox
    wangshuang "然后脑子里就一个念头：“我操这下不得了了要被外部存在的压强挤碎了快他妈跑”，然后据说，我就开始往窗户外面跳...也不知道是被谁拉住的，是你吗？应该不是，你应该拽不住我。"
    ## Extended文本框结束
    ## 表情：默认
    scene dessert3_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "总之要不是后来配了眼镜，不然我是绝对不敢乱用{i}KAS{/i}的，那次是真的差点死了..."
    ahe "哦，原来你那“磕完药差点死掉的小故事”还在更新啊。"
    ## 表情：小激动
    scene dessert3_excited
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "那可是正儿八经的人命啊喂！"
    wangshuang "不过一般人应该不会那么夸张。你会喜欢的，我觉得。"
    ahe "所以我们要在这里待到什么时候？"
    ## 表情：默认
    scene dessert3_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "等时机到了，自然就能离开。"
    ahe "也是一种较为朴素的过程？"
    wangshuang "哦？如此简明且精确的定义，谁教你的？"
    ahe "一个傻逼。"
    ## 表情：小激动
    scene dessert3_excited
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "{shake}好刻薄！{/shake}"
    ahe "像您这样有成就的大人物，只被骂傻逼还请偷着乐吧。"
    ## 表情：撇嘴
    scene dessert3_pout
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "所以确实没法放过我了吗？"
    ahe "你还需要人放过？"
    ## 表情：默认
    scene dessert3_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "当然，我又不是没有罪恶感的人。"
    ahe "存疑。"
    wangshuang "哎阿鹤，虽然有些事情我确实做得...不太好...从世俗意义上来说，但也没必要这样质疑我演戏的质量嘛。"
    ahe "你看，你都自首了。还不逮捕你自己。"
    ## 表情：撇嘴
    scene dessert3_pout
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "那我还得兼任检察官辩护律师和法官，太麻烦了。"
    ahe "用来消磨时间正合适，反正用不完。"
    wangshuang "不不不那就不对了，如果你还想“消磨时间”，那就说明你修为尚浅，还没悟透其中道理。"
    ahe "...好的，师傅。"
    ahe "话说师傅，你手里拿的是什么？"
    ## 表情：默认
    scene dessert3_default
    $ renpy.transition(Dissolve(0.2), layer="master")
    wangshuang "哦，这个？不是什么重要的东西，但你可以尝尝看。"
    ahe "尝尝看？"
    wangshuang "对啊，吃的。要不要试试？"
    $ stash_music_pos()
    $ current_music_scene = None
    stop music fadeout 3.0

    menu:
        extend ""
        "算了":
            "阿霜手里把玩的那物件，你之前肯定见过，却想不起任何细节。"
            "总之没想到竟是一件吃食。"
            "从它那轻若无物又变幻莫测的形态来看，可能真是什么珍馐也说不定，抑或是另一剂猛药。"
            "但无论如何，在{i}KAS{/i}即将穿过血脑屏障的前一刻，再往身体里追加不明物质想必不是什么明智决定。"
            ahe "算了吧。"
            wangshuang "随你便咯——说起来，阿鹤，你喜欢红色还是蓝色？"
        "接受。":
            $ madness += 1
            "虽然你清楚地意识到你跳动的血管里，{i}KAS{/i}即将穿越脑血屏障，随时可能把你的意识送上云端，你那该死的好奇心还是压过了残存的理性。"
            "你接过王霜手里那无色透明的多面体。"
            "那东西轻若无物又变幻莫测，看似是固体，摸起来却又有介于凝胶和麻薯之间的质感，躺在你手心里，冰冰凉的。"
            "你毫无戒心地将那不明物件送进嘴里，简单地咀嚼了一阵，没有尝出任何味道。"
            ahe "没味道。"
            wangshuang "当然没味道。"
            ahe "那你还让我吃？"
            wangshuang "毕竟这也是实验的一部分——阿鹤，你喜欢红色还是蓝色？"

    ## 音乐开始 fade out
    $ current_music_scene = None
    stop music fadeout 4.0
    ahe "蓝色啊，怎么了？"
    wangshuang "你看——"
    ## 转场：甜品店对视4
    scene bg_dessertgaze4 with scene_dissolve
    ## 蓝色波纹特效，并逐渐加入更多色彩
    ## 场景音乐参考：进入幻视，所以虽然场景没变音乐也要切换https://audionautix.com/Music/Beautiful%20Daughter.mp3 (Jason Shaw)，
    $ set_scene_music("route1_hallucination")
    ## Split Extended大文本框开始 - 左右分栏
    split_left_narrator "你正摸不着头脑，转眼间却发现了周遭惊人的变故——四周逐渐泛起蓝色、波浪状的纹理，很快侵蚀了整个视野。"
    extend "\n你反倒比先前要更加冷静，又低头吃了几口团子。甜腻腻的滋味在口腔中涟漪般散开，每颗味觉细胞都在欣喜若狂地发送着饱足的信号。"
    split_right_narrator "甜味的颜色？金黄的莓红的草绿的深棕的，味觉的色彩洪流汇入弥漫在整个视觉空间的海蓝色波浪中。"
    extend "\n你抬头望向王霜，她也望着你，脸上含蓄地挂了一抹邪魅的笑容，眼神里却又流露出一丝欣慰，仿佛望着一个迷路的孩子。"
    extend "\n她略卷的水蓝色长发在周身空间的波浪里散着，勾勒出洋流的轮廓。"
    ## Split Extended大文本框结束
    ## Split Extended大文本框开始 - 左右分栏
    split_left_narrator "你心中对她海啸般的戒心早已荡然无存了——你几乎有些喜欢她现在的样子，宛如一个母亲，又像是神明，给视野不断抹上温柔的蓝色。"
    extend "\n每一缕神经都在扩张。启示性的景象。时间和空间波浪。无孔不入的色彩和甜味。蓝色的。交响。"
    split_right_narrator "反复咀嚼伤痛直至淡而无味，直到甜味凭空冒出来。"
    extend "\n在一切都已结束的当下，连时间都已丧失价值，唯一还能让你睁开双眼的，就只有——"
    ## Split Extended大文本框结束
    ## 居中大字文本框开始 - centered large font textbox
    centered_large_narrator "瘾。"
    ## 居中大字文本框结束
    ## Split Extended大文本框开始 - 左右分栏
    ## 转场：甜品店对视5
    scene bg_dessertgaze5 with scene_dissolve
    split_left_narrator "王霜的微笑越发邪魅——她逐渐成为了一个微笑。"
    extend "\n成瘾。糖分子的洪流只消一个浪头就使你深深染上了挥之不去的瘾。"
    extend "\n渴望的源头冲动的源头向往的源头发现了。"
    split_right_narrator "浪潮般的甜味反复沁入意识。她开始微笑。她停止微笑。目光所及之处就能看见她的微笑。"
    ## Split Extended大文本框结束
    ## Split Extended大文本框开始 - 左右分栏
    split_left_narrator "燥热使得意识模糊，痛苦消减。鼓的声音。恒久的鼓声从背景里逐渐浮现，强烈起来，震耳欲聋，每一击都与心跳同调。"
    extend "\n在这暧昧混沌里，你感到安逸。"
    extend "\n这样就够了。"
    ## Split Extended大文本框结束
    ## 撇嘴
    wangshuang "说到底，我们所做的一切也只是为了满足癖好而已。"
    ahe "这大概是一件无可厚非的事情。"
    ## 默认
    wangshuang "大概吧。也许那就是所有人的使命。"
    wangshuang "如此轻浮如此下作，如此美妙。"
    ahe "如此轻而易举。"
    wangshuang "如此唾手可得。"
    ahe "如此美妙..."
    ahe "我想要..."

    menu:
        extend ""
        "更多。":
            $ madness += 1
            ahe "我想要就这样继续下去。"
            wangshuang "那就这样继续下去吧。"
        "就这样睡去。":
            ahe "我困了。"
            wangshuang "就这样睡去也无可厚非。"

    ## Extended大文本框开始 - accumulating large textbox
    ## 转场：甜品店对视6
    scene bg_dessertgaze6 with scene_dissolve
    large_narrator "更多思绪已无意义，一如时间。"
    extend "\n溶解在蓝色空间里的凉爽糖分让你浑身的燥热与恶意消减了大半，你置身一片透明的海域里，又像是漂浮在空洞的宇宙空间中。"
    extend "\n一切都是许可的，这样的冲动从未如此强烈过。"
    extend "\n你迫切地想要伸出手，但双臂已经先你一步向前伸了出去，贪婪地揉捏着冰凉而柔顺的空气，水蓝色的空气。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "更深的见解就隐藏其中，因为一切都是许可的，视野中的所有事物都是从始至终连贯而统一的，如此怡人，如此饱满。"
    extend "\n人类的智识自然无力探寻其中奥秘，但在王霜无处不在的笑容辉耀之下，你的一部分认知已踏入了更深层的水域。"
    extend "\n越向深处就越被不可知所掣肘，当眼前的色彩开始回旋，你意识到或许梦境的另一面并非现实，而是某种更加完整且怖人的造物。"
    ## Extended大文本框结束
    ## 转场：甜品店对视6.51
    scene bg_dessertgaze6_51 with scene_dissolve
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你的知能越是提升，它的样貌就越发模糊，模糊的面容中只显露出一抹依稀可见的残酷笑容，仿佛在嘲讽你的徒劳。"
    extend "\n但你已经满足了，由内而外地满足了，在饱满的感官刺激中感到一阵——疲劳？"
    extend "\n幸福的疲劳、优质的疲劳、苦苦追寻的疲劳、允许你在辗转反侧后终于入睡的甜美疲劳。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "世界空无一人，因为任何个体都不具备足够的差异能够让它们自称“存在”，因此你将它们尽数吞下，如同团子。"
    extend "\n糖分继续满溢出来，沿着你存在的边缘缓缓淌下，坠入周身蔚蓝的虚空之中，粘稠而香甜。"
    extend "\n糖浆，万物的粘合剂。就用它来替代血液。"
    extend "\n完成之后就去睡吧。"
    extend "\n你的愿望在那念头浮出水面的瞬间便成为了现实，而你只想在这静谧安详的世界里睡去。"
    ## Extended大文本框结束
    ## 色彩开始还原
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "然而当你行将合眼时，一阵强烈的恶心自胃里上涌，就像有人抓住你的肠胃，自下而上地用力挤压。"
    extend "\n警告：过热。过热。"
    extend "\n钟表嘀嗒作响。"
    extend "\n恶心加剧，肠胃彻底拧成一团，而其中汹涌的内容物已经呼之欲出。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你死命闭气抵抗，汗如雨下，浑身冷颤使你几乎维持不住坐姿，眼看就要从座椅上滚下来。"
    extend "\n随着肠胃痉挛越发剧烈，你终究败在了本能反应面前，脖颈狠狠向前一抻，“哇”地一声吐了出来。"
    extend "\n和你所熟知的呕吐不同，你吐出的只有色彩。"
    ## Extended大文本框结束
    ## 转场：甜品店对视7
    scene bg_dessertgaze7 with scene_dissolve
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "呕吐物与面前桌子接触的瞬间，水蓝的桌面便恢复了原本的颜色。"
    extend "\n你吐出的色彩越多，这令人沮丧的还原就越发提速，转眼便侵蚀了大半个视野。"
    extend "\n色彩还原的地方，水面般摇曳的空间停止了动态，原本随处可见的王霜的微笑也随着视野的复原消散了。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "桌布洁白，金属餐具冷峻，暖色的室内灯光随着呕吐物飘散，不断渗入空气中的每个角落。"
    extend "\n面前盘子里躺着几个没吃完的团子，上面糖浆那金黄的色泽明艳地让你毛骨悚然。"
    extend "\n胃里再次翻腾起来，于是你赶紧移开了目光。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你感到疲惫不堪，只想回到一个更加清醒的地方。"
    extend "\n眼前桌面的存在与本质看起来产生了某种根本性的分离，但你已经没有心力去捕捉这种恼人的细节。"
    extend "\n因为你注意到，在美妙的水蓝色消逝殆尽后，王霜并没有回来。"
    extend "\n空空如也的店里坐着空空如也的你。"
    ## Extended大文本框结束
    ## 画面出现裂痕
    ## Extended大文本框开始 - accumulating large textbox
    ## 转场：甜品店对视8
    scene bg_dessertgaze8 with scene_dissolve
    large_narrator "还原之后的世界仿佛脱了水般脆弱不堪，单是目光扫过就让其表面生出了一连串细小的裂痕。"
    extend "\n更多裂痕。"
    extend "\n直到它们汇聚成令人不安的绵延裂隙。"
    extend "\n直到周身一切如同一幅缺乏保养的老旧油画那样，一片片剥落，露出背景里黑黢黢的虚空。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你明知该离开了，却仍旧无动于衷。"
    extend "\n周身空间在微颤中继续碎裂，而你则带着某种同样脆弱的信念静坐原地，任凭倦意侵蚀你脑海中所剩无几的清醒意识。"
    extend "\n{size=-10}只需要她带你离开这里...这样就够了...{/size}"
    extend "\n{size=-10}只需要她...这样...就够了...{/size}"
    extend "\n..."
    extend "\n......"
    extend "\n........."
    extend "\n就够了..."
    extend "\n即使如此，王霜依旧没有回来。"
    ## Extended大文本框结束
    ## 转场：黑屏
    scene bg_black_video with scene_soft
    ## 剥落完成后，黑屏
    ## 水底泡泡上浮音效：Bubbles_10
    $ play_sfx("audio/sfx/bubbles/Bubbles_10.wav")
    ## 转场：粉红屏
    scene bg_pink_video with scene_soft
    $ stash_music_pos()
    $ current_music_scene = None
    stop music fadeout 3.0
    ## Extended文本框开始 - accumulating textbox
    $ wait_sfx()
    ahe "阿霜？"
    extend "\n你在吗？"
    extend "\n你要是再装消失的话我就要去死咯？"
    ## Extended文本框结束
    ## Extended文本框开始 - accumulating textbox
    ahe "阿霜？"
    extend "\n有人吗？"
    extend "\n..."
    ## Extended文本框结束
    ## 场景音乐参考：https://audionautix.com/Music/DeepSpace.mp3 (Jason Shaw), the pain of recalling memories of an empty life (playlist) - 重要时间戳：3:16（øneheart x reidenshi - snowfall）， 7:50（time slows down），11:07（Broken Air），后面有兴趣可以继续听，风格和配器都类似
    $ set_scene_music("route1_deepspace")
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "没有人。周身只有一片暧昧的粉红色雾气。"
    extend "\n试着蜷起手指，只觉得手心传来一阵稍纵即逝的触感，冰凉而虚幻。"
    extend "\n你挣扎着想要活动身体，却猛地意识到自己的横膈膜停止了张弛。"
    extend "\n保持呼吸。"
    extend "\n空气中充斥着一股微妙的甜腻味道。"
    extend "\n在童年故乡的某个傍晚，太阳将要落山，你踌躇满志地幻想未来时，也闻到过这样的味道。"
    extend "\n它让你想起一些美好但没有意义的事情。"
    extend "\n无论如何也找不到，但要保持呼吸。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你漂浮着。"
    extend "\n腹中偶有痉挛，宛如方才经历了一场盛大的呕吐。"
    ## Extended大文本框结束
    ## 居中大字文本框开始 - centered large font textbox
    centered_large_narrator "原来如此，原来如此。"
    ## 居中大字文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "严肃呕吐。"
    extend "\n只要能够继续呼吸。"
    ## Extended大文本框结束
    ## 居中大字文本框开始 - centered large font textbox
    centered_large_narrator "请不要脱水。"
    centered_large_narrator "请保持呼吸。"
    ## 居中大字文本框结束
    ## 呼吸音效
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "粉红色的雾气。"
    extend "\n也许无论如何都必须去向更加遥远的地方。"
    extend "\n更加遥远，更加遥不可及，更加可望不可即。"
    extend "\n成为一个留给后人观测的坐标，仅此而已，仅此而已。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "凝胶柔软。"
    extend "\n玻璃也柔软。"
    extend "\n黑夜柔软。"
    extend "\n光源柔软。"
    extend "\n粉红色雾气坚硬如铁。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "需要时刻监测的数据点："
    extend "\n生命体征"
    extend "\n死亡体征"
    extend "\n不可有误。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "24小时核磁共振？小意思！除非这人的骨头是铁做的。"
    extend "\n当然，由内而外烤熟也不失为一种凄美悲壮的结局。"
    extend "\n所以会为你继续监测的。"
    extend "\n因为那正是你的目的，凄美悲壮地收场，然后为后人所铭记。"
    extend "\n你的目标。"
    extend "\n你的理想？"
    extend "\n理想？说得好像你这年近三十的男人是一个十三岁的孩子。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "所以你会为我保持呼吸么？"
    extend "\n为我拆出旁人的肋骨，为我洞穿无辜者的肺叶。"
    extend "\n为我毫无理由地献上溢美之词？"
    extend "\n无趣。"
    extend "\n但请保持呼吸。"
    ## Extended大文本框结束
    ## 呼吸音效
    ahe "哦。"
    ahe "呃..."
    ahe "啊...！"
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "横膈膜早就停止了张弛，而当你意识到自己无法呼吸时，一切已经晚了。"
    extend "\n一切？！"
    extend "\n又是他妈的一切！"
    extend "\n粉红色的神经毒素顺着透明细长的针刺注入你的血管。"
    extend "\n直到你全身都染上粉红色。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "粉红色的雾气散成一丝丝隐约可见的、游移的细线——水母的触手。"
    extend "\n这分明是一场长期疗程的开端，却因为视线模糊而永远定格在了肤浅的一面。"
    extend "\n杀人的也罢，懦弱的也罢，捏成一个便是了。"
    extend "\n剧毒的也罢，解毒的也罢，混成一锅就行了。"
    extend "\n总之要合而为一，总之要并联，总之要揉碎了再捏起来，总之不彻底毁灭就无法重生。"
    extend "\n所以必须要保持呼吸。"
    ## Extended大文本框结束
    ## 呼吸音效
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你想起她的善。"
    extend "\n你只能想起她的善。"
    extend "\n在这水母勾勒的温暖牢笼里，你只被允许想起她的善。"
    extend "\n伞盖边缘在你看不到的远处有节奏地收缩舒张。每一根触手都与你相连。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "呼吸停止的那一刻，你感到舌尖有些麻木。"
    extend "\n一阵苦涩液体自喉管深处涌上来。"
    extend "\n却在抵达舌尖的瞬间便消散了。"
    extend "\n所以要保持呼吸道畅通。"
    extend "\n保持呼吸。"
    ## Extended大文本框结束
    ## 呼吸音效
    ## Extended大文本框开始 - accumulating large textbox
    ## 转场：灰屏
    scene bg_grey_video with scene_soft
    large_narrator "仅此而已，仅此而已。"
    extend "\n她是治愈的灰，包容的灰。"
    extend "\n任何色彩倾泻其中，都只能归零的灰。"
    extend "\n灰在扩散，由点到面，最后变得像一帘浩大的幕布般徐徐展开。"
    extend "\n所以追求“还原”何罪之有？"
    extend "\n捂嘴。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你只能眼睁睁地看着面前的灰幕展开。"
    extend "\n无能为力。"
    extend "\n当然无能为力，因为还原的灰幕也是你的愿望。"
    extend "\n即使身处灰幕下就必须遭受你拼尽全力也难以忍受的痛苦。"
    extend "\n嚎叫。歇斯底里的嚎叫。你在嚎叫中睡去又醒来。"
    extend "\n在全身骨骼被碾碎又重组的欢欣中放声嚎叫，庆祝一个与你毫不相干的灵魂的“自由”。"
    ## Extended大文本框结束
    ## Extended文本框开始 - accumulating textbox
    "灰色是零。你也是。"
    extend "\n所以还要保持呼吸么？"
    ## Extended文本框结束

    menu:
        extend ""
        "保持呼吸。":
            ## 呼吸音效渐强，随着文字进程逐渐加快&变响
            ## Extended大文本框开始 - 大文本框分句
            large_narrator "仍要坚持？那就请继续忍耐吧。"
            extend "\n灰幕的蔓延永无止境，一如疼痛的叠加永无止境。"
            extend "\n更多毒液渗入血管，血液沸腾，内脏在沸腾血液的浇灌下燃烧，但你只能看见你执意选择的灰。"
            extend "\n继续呼吸，因为你必须活下去，在无止境的灰幕里像你不存在的爱人那样活下去。"
            ## Extended大文本框结束
            ## 电视机关机音效
            ## 转场：黑屏
            scene bg_black_video with scene_soft
            ## Extended大文本框开始 - 大文本框分句
            large_narrator "..."
            extend "\n......"
            extend "\n........"
            ## Extended大文本框结束
        "放弃。":
            $ madness += 1
            ## 呼吸音效停止
            ## Extended大文本框开始 - 大文本框分句
            large_narrator "主动放弃呼吸后，你反倒听见了某种远超于你存在的召唤。"
            extend "\n女人的声音，那嗓音神秘而熟悉 - 你的病终于和我一样，我羸弱的爱人。"
            extend "\n你听见那声音，就像听见了复活的钟声，虽然振聋发聩，却让你义无反顾地站了起来。"
            extend "\n要去哪儿呢？"
            extend "\n总要去些地方。即使不呼吸也罢。"
            extend "\n治病也罢，杀人也罢。"
            extend "\n总之要去些地方。"
            extend "\n在无际的灰幕中，你把灰色踩在脚下，开始仔细思考接下来的目的地。"
            ## Extended大文本框结束
            ## 转场：黑屏
            scene bg_black_video with scene_soft
            $ stash_music_pos()
            $ current_music_scene = None
            stop music fadeout 3.0
            ## Extended大文本框开始 - 大文本框分句
            large_narrator "..."
            extend "\n......"
            extend "\n........."
            ## Extended大文本框结束

    $ stash_music_pos()
    $ current_music_scene = None
    stop music fadeout 3.0
    ## 沙漠中的脚步声
    ## 转场：银白色沙漠
    scene bg_desert with scene_soft
    ## 沙漠长风音效
    $ play_ambient("audio/sfx/desert_wind/desert_wind_bed.ogg")
    ## 抱胸站立，抱怨表情
    wangshuang "喂，到了没啊？"
    ahe "没。"
    ## 抱胸站立，撇嘴表情
    wangshuang "那还要走多久？"
    ahe "到不了了。"
    ## 单手叉腰站立，吃惊表情
    wangshuang "啊？"
    ahe "或者说我们早就到了，但找不到对的骨头。"
    ## 单手叉腰站立，撇嘴表情
    wangshuang "你就一定要拼出一副完整的骨架才满意么？"
    ahe "不然好像我们也走不出这里。"
    ## 抱胸站立，抱怨表情
    wangshuang "啊啊啊我当初就不该听你的鬼话和你一起来这里的！"
    ahe "不是挺好的么？像你这样整天坐办公室的，偶尔就需要走动走动。"
    ## 单手叉腰站立，撇嘴表情
    wangshuang "就算要走也别让我来沙漠里找骨头啊！"
    ahe "可明明就是你自己要跟来的。"
    ## 单手叉腰站立，抱怨表情
    wangshuang "呃呃呃我究竟中了什么邪才把你——"
    ahe "嗯？把我怎么？"
    ## 背手站立，默认表情
    wangshuang "没事，别在意。"
    "..."
    "......"
    "........."
    ahe "嗯...大腿骨明明应该是最容易找到的才对..."
    ## 背手站立，默认表情
    wangshuang "这根不是？"
    ahe "那根我刚才试过了，髋关节对不上。"
    wangshuang "这边还有四五根，你都试过了？"
    ahe "诶？你是从哪儿找来的？"
    ## 单手叉腰站立，得意表情
    wangshuang "来的时候遍地都是啊，眼前一眼望去还有七八根。"
    ahe "所以精神科的也得会认骨头？"
    ## 抱胸站立，得意表情
    wangshuang "骨科可是我的强项。"
    ahe "好吧..."
    ## Extended文本框开始 - accumulating textbox
    "…"
    extend "\n……"
    extend "\n………"
    ## Extended文本框结束
    ahe "对上了诶。"
    ## 背手站立，默认表情
    wangshuang "所以呢？接下来要做什么？"
    ahe "头骨..."
    ## 右手叉腰，左手食指竖起做讲解状，严肃表情
    wangshuang "吼，只剩头骨了么...还有，阿鹤啊——"
    ## 场景音乐参考：Stranger_Files, Sweet_Regrets，Whispers in the Twilight
    $ set_scene_music("route1_desert")
    ahe "嗯？"
    wangshuang "你知道自己在做什么，对吧？"
    ahe "当然知道。"
    ## 背手站立，严肃表情
    wangshuang "那是最没有意义的事情。"
    ahe "确实如此。"
    wangshuang "而你还在坚持。"
    ahe "这是这里唯一能做的事情。"
    ## 抱胸站立，面无表情
    wangshuang "直接离开也可以，门就在那边。"
    ahe "哦，原来是有门的。"
    wangshuang "当然，只要我与你一同来，就有门。"
    ahe "嗯...所以你真的是阿霜吗？"
    ## 背手站立，默认表情
    wangshuang "当然。"
    ahe "阿霜，你在我不注意的时候，偷偷变成了某种神吗？"
    ## 背手站立，疑问表情
    wangshuang "神？什么神？连走路都走不动的神？"
    ahe "阿霜，之前进入这个梦的时候，永远都是我一个人。为什么这次你也在这里？"
    ## 单手叉腰站立，默认表情
    wangshuang "因为我也能做同样的梦。"
    ahe "唔..."
    ## 背手站立，坏笑
    wangshuang "只不过我不会无聊到去拼骨头就是了。"
    ahe "那你为什么要做这个梦？"
    ## 背手站立，默认表情
    wangshuang "嗯...当然是因为后悔，否则人是不可能来到这里的。"
    ahe "还有能让你后悔的事？"
    wangshuang "当然。只要做了选择，就一定会后悔。"
    ahe "可如果你已经变成神了——"
    ## 抱胸站立，撇嘴表情
    wangshuang "你才变成神了！"
    ahe "好吧..."
    ## 背手站立，面无表情
    wangshuang "不管多么成功地执行了计划，总会有疏漏，这是无法避免的，自然也就总会有后悔的空间。"
    wangshuang "你也别觉得那是什么见不得人的事情。应该说，完全无法后悔的认知架构才真的要命，我之前做过这方面的研究。"
    ahe "什么研究？"
    ## 右手叉腰，左手食指竖起做讲解状，严肃表情
    wangshuang "‘全知全能的代价’。"
    ahe "这一点都不相关吧！"
    ## 抱胸站立，默认表情
    wangshuang "别急，听我讲完你就懂了。"
    ## 右手叉腰，左手食指竖起做讲解状，默认表情
    wangshuang "所谓‘全知全能’，虽然听着像是造物主才被允许拥有的神力，但事实上以今天的技术，想要在有限时空里模拟这一状态不算难。"
    ## 抱胸站立，严肃表情
    wangshuang "试想，假若在我们与杰罗瓦的最后一战里，你在见到他放出的{i}尤里娅{/i}们就立刻放弃了抵抗，会怎么样？一切就结束了对吧？"
    ## 背手站立，默认表情
    wangshuang "那你再想，如果我能把这段不存在的“记忆”高清模拟出来，数据化掉，然后灌回你脑子里。"
    ## 右手叉腰，左手食指竖起做讲解状，默认表情
    wangshuang "加上你脑子里原本就存在的记忆，这时让你同时体验选择支两边的事件，那在这样的认知草拟完成后，你是不是就已经实现对于这段记忆的‘全知全能’了？"
    ahe "可这人肯定会发现记忆存在冲突的吧。"
    ## 抱胸站立，严肃表情
    wangshuang "当然，但假若两边的记忆，从肢体感官到事件次序，无不张弛有度地印在你脑海里，那对于一个不了解认知草拟的被试来说，该如何戳穿自己‘全知全能’的假象？"
    ahe "必须要外人点破才行。"
    ## 右手叉腰，左手食指竖起做讲解状，默认表情
    wangshuang "对，但不全对——即使有外人指出矛盾，又有多少人愿意摒弃自己的“切身体验”，转而允许他人的只言片语来定夺自己的认知？"
    ahe "..."
    ## 右手叉腰，左手食指竖起做讲解状，严肃表情
    wangshuang "我们的实验数据也指向这个方向——在草拟完成的三天内，所有被试都明确拒绝了外界干预，以不容置疑的姿态维持着选择支两边的草拟。"
    ahe "他们在自行草拟？"
    wangshuang "没错。我们人工植入的认知流并没有在结尾处安排收束性事件，而在我们灌进去的认知与现实发生冲突后，被试们全部选择了无视现实，并开始自行草拟选择支两边的后续内容。"
    ## 抱胸站立，默认表情
    wangshuang "更有意思的是，所有被试在自行草拟的过程中多巴胺通路都在暴走，就仿佛这虚假的全知全能让他们——"
    ahe "成瘾了。"
    ## 右手叉腰，左手食指竖起做讲解状，开心表情
    wangshuang "Bingo！我们用计算生成的认知数据让人染上了成瘾性的精神分裂，而这——"
    ahe "就是全知全能的代价？"
    ## 单手叉腰站立，坏笑表情
    wangshuang "嘿嘿，别兴奋过头了，阿鹤。"
    wangshuang "一个人双线程草拟时需要的算力...这么说吧，会在草拟开始后的短时间内爆炸增长，而最初的草拟全是在被试脑内执行的...。"
    ahe "..."
    ## 抱胸站立，严肃表情
    wangshuang "嗯，第一批被试的脑子大多都烧了，物理意义上的。后来第二批还动用了医院的计算机，效果也没好多少就是..."
    ## 右手叉腰，左手按着胸口，无奈表情
    wangshuang "所以说能后悔是好事啊，能用如此无可厚非的情感来替代脑细胞被烧干，是一桩好买卖。"
    ahe "那这个梦..."
    ## 背手站立，默认表情
    wangshuang "嗯，是我给自己搭的，用来强制认知收束的疗养院。后来发现效果不错，自然也就向一些VIP们开放咯。"
    ahe "你自己也参与了？"
    wangshuang "当然，我是第一批被试哦。只是我的脑子不太一样，成瘾这个问题对我来说并不存在，可以随时自行结束草拟，所以可以在当被试的同时一边跟进实验。"
    ahe "所以为什么没有让其他被试来这里..."
    ## 背手站立，心虚笑表情
    wangshuang "哦...哈哈...这个嘛，毕竟当时搭得比较匆忙，这个梦境第一版的认知收束任务只能单线程地跑，慢得不行的同时还会很吃资源，所以救不了太多人...哈哈..."
    $ stash_music_pos()
    $ current_music_scene = None
    stop music fadeout 3.0
    ## 沙漠长风音效
    $ play_ambient("audio/sfx/desert_wind/desert_wind_bed.ogg")
    ahe "..."
    wangshuang "..."
    ahe "这就是你后悔的事情？"
    ## 抱胸站立，默认表情
    wangshuang "你觉得呢？"
    ahe "我怎么知道..."
    wangshuang "嗯，还是保持无知比较好，阿鹤。"
    ahe "只要你心安理得就行..."
    ## 背手站立，面无表情
    wangshuang "..."
    ahe "所以这梦也是你那朴素过程的一部分？"
    ## 背手站立，默认表情
    wangshuang "那不一样，现在能够来到这里的都是游离于朴素过程之外的异客，而当他们离开这里时，我希望他们至少能明白自己为什么必须要这样游离。"
    ahe "唔，所以这也是你的实验的一部分，带课题的。"
    ## 右手叉腰，左手食指竖起做讲解状，严肃表情
    wangshuang "不不不，这里只是治疗场所而已。我不会控制任何变量，而你永远是自由的。换言之，课题得你自己定。"
    ## 右手叉腰，左手食指竖起做讲解状，默认表情
    wangshuang "不过从你手上一直在忙活的事情来看，这早就不是问题了。"
    ahe "但你说它没有意义。"
    ## 背手站立，默认表情
    wangshuang "嗯，现在我也维持原判。"
    ahe "..."
    ## 抱胸站立，坏笑表情
    wangshuang "不想知道为什么？"
    ahe "不是很想。"
    ## 背手站立，默认表情
    wangshuang "行吧。毕竟我们有得是时间。"
    ahe "..."
    ## 单手叉腰站立，得意表情
    wangshuang "嗯...但是我站累了，所以让我来告诉你吧——你要找的头骨是不存在的。"
    ahe "啊？你怎么知道的？"
    wangshuang "喏——"
    ## 原本王霜的位置闪过尸首的黑影
    with fx_shock
    ahe "啊——！"
    ## 王霜说话时播放glitchy音效
    ## 背手站立，默认表情上蒙了glitch
    wangshuang "因为——欧按物——咽——"
    ahe "阿...霜？"
    ## 王霜面部开始出现glitch
    with fx_glitch
    ## 抱胸站立，坏笑表情上蒙了glitch
    wangshuang "啊啊呐唔——一握艾鈤——..."
    ## 右手叉腰，左手食指竖起做讲解状，默认表情上蒙了glitch
    wangshuang "唵椅迩唵毋炆戊囮吔坳唔岙莪。"
    ## glitch消失
    with fx_glitch
    ahe "阿霜，你还好吗？"
    ## 抱胸站立，疑问表情
    wangshuang "嗯？怎么了？"
    ahe "你刚才...当我没说。所以为什么头骨不存在？"
    ## 右手叉腰，左手食指竖起做讲解状，得意表情
    wangshuang "因为我看不见。"
    ahe "这样..."
    ## 王霜面部开始出现glitch
    with fx_glitch
    ## 尸首黑影闪过
    with fx_shock
    ## 背手站立，默认表情上蒙了glitch
    wangshuang "一焱髻暨戊馹曳葳邑吖霭肮毐峪镍醪！"
    ahe "喂...阿霜你又——"
    ## glitch消失
    with fx_glitch
    ## 背手站立，得意表情
    wangshuang "哎，我也没说缺了头骨就不行啊。"
    wangshuang "既然你们这么想见面，那肯定得成全你嘛——你看，你的“作品”从各种意义上已经完成了。"
    ahe "什——"
    ## 一般态默认
    youliya "你好，阿鹤。"
    ahe "诶？你——"
    youliya "嗯，我当然还活着。"
    ahe "可是...可是我..."
    ## 一般态面部glitch
    youliya "你豋炅宓恇蠹璱钅飰棏巠敪玸——"
    ahe "啊...等等...等一下！"
    ## 一般态默认
    youliya "嗯，又失忆了么...离我们上次分别也没过多久吧，阿鹤？"
    ahe "不是...{i}尤里娅{/i}...不对..."
    ## 一般态面部glitch
    youliya "喔，确实是不太对啊呃呃呃啊——。"
    ## 尤里娅消失
    ## 场景音乐参考：N2-07
    $ set_scene_music("route1_horror1")
    ahe "{i}尤里娅{/i}，{i}尤里娅{/i}？"
    ## 抱胸站立，疑问表情上蒙了glitch
    wangshuang "飒炟曠莩皎靸礚睫覅是否解释你的诨涤？"
    ahe "啊...你们...你们..."
    ## 尤里娅出现
    ## 一般态坏笑
    youliya "嗯...只是撕碎了几百个长得和我一样的东西，你就扛不住了？这可不是我认识的阿鹤呢。"
    ahe "呃...啊...可是...可是..."
    ## 一般态邪恶表情1
    youliya "但那对你来说根本不重要吧，毕竟你在正当防卫，无论怎样都不能在最后关头输给一群杰罗瓦控制的假人嘛！"
    youliya "尤其当那些东西只是‘长得和我一样而已’的时候。"
    youliya "只要你“看到”那些东西不是“我”，自然就可以随手杀掉了——一切都理所当然，无可厚非，不是么？"
    ahe "..."
    ## 一般态默认
    youliya "可是阿鹤，你知道吗？所有复制体的感官都会回流到我的身体。"
    ahe "{i}尤里娅{/i}...这不是——"
    youliya "每根断掉的骨头、每滴流出来的血、每副碎掉的内脏——虽然尽是些无关紧要的事情，可还是让我记忆犹新啊，每一次死掉。"
    ## 一般态坏笑glitch
    youliya "死掉诶...那就是你口中那“无法重复的深邃体验”吧。能连续体验那么多次，我是不是该..."
    youliya "感谢你呢？"
    ahe "..."
    ## 一般态默认
    youliya "那么作为你的谢礼，让我来告诉你一点浅显的事实吧。"
    ## 一般态坏笑
    youliya "阿鹤哥，在逝乐园终结的前几天里，不只是你，你身边的大家，所有人都在演戏哦，我、王霜、米姐，全都一样。"
    ## 一般态默认
    youliya "你是不是觉得，只要强撑着送我离开了逝乐园，你就能跳出日常了？"
    ahe "——！"
    youliya "你是不是觉得，只要假装抛下你在乎的一切，最可怕的下场无非就是死掉而已？"
    ## 一般态邪恶表情1
    youliya "完全不动脑子就接受这样的结论，简直是错得不能再错了啊，我一败涂地的救世主先生。"
    youliya "那么——"
    ## 一般态邪恶表情2
    youliya "请见证你愚行真正的后果吧。"
    ## 尤里娅异变
    ## 炸裂jump scare音效
    ## 浑身伤痕累累仿佛由尸块缝纫而成的无头尸首登场
    ## 高速心跳音效
    ## 屏幕边缘开始随着心跳的节奏震动
    ## 场景音乐参考：N2-14，播放完一次N2-14之后，回到N2-07
    $ set_scene_music("route1_horror2")
    ahe "——么！！！"
    shishou "阿鹤，事到如今你又在害怕什么呢？"
    ahe "啊...啊啊啊啊...啊啊啊啊啊啊啊啊啊啊——"
    ## 抱胸站立，温柔表情
    wangshuang "别跑啊，这可是你们的感人重逢诶！"
    ahe "别过来！"
    shishou "阿鹤，我们还没聊完——"
    ahe "你别过来！！！"
    ## 沙地里跑步音效
    ## 进入一个向前跑动的sequence，可以是少量几帧透视感比较明显的画面，然后无限循环
    ## 做些古怪特效，世界有点崩解的感觉
    ahe "这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的这不是真的！"
    ## 背手站立，疑问表情
    wangshuang "阿鹤？"
    ahe "啊——！你为什么还在这里！"
    ## 抱胸站立，得意表情
    wangshuang "我当然在啦，她也还在——"
    shishou "哈喽~"
    ahe "别过来！你别过来！再见！"
    ## 重新开始跑动sequence
    ahe "啊...保持呼吸...保持呼吸...保持呼吸...保持呼吸..."
    shishou "你好。"
    ahe "..."
    ## 背手站立，得意表情
    wangshuang "跑不动了？"
    ahe "...不要...停下来..."
    wangshuang "要知道，你可是自愿来到这里的哦。"
    shishou "嗯。"
    ahe "我...一定...要...离开这里！"
    ## 抱胸站立，默认表情
    wangshuang "你费了这么大力气把她拼凑出来，却又无法直视她了？"
    ahe "这不是我想要的..."
    ## 背手站立，疑问表情
    wangshuang "只因为她没有头？"
    ahe "这不是我想要的！"
    ## 单手叉腰站立，得意表情
    wangshuang "那就把头埋进沙子里啊，那样你就什么都不用看了。"
    ahe "呃...啊——对不起——"
    ## 转场：图片黑屏
    scene bg_black_still with scene_soft
    $ stash_music_pos()
    $ current_music_scene = None
    stop music fadeout 3.0
    ## 沙漠长风音效
    $ play_ambient("audio/sfx/desert_wind/desert_wind_bed.ogg")
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "沙地冰凉而干燥，在这个无声的世界里，你艰难地呼吸。"
    extend "\n随着恐惧略微消散，你察觉到这地下似乎不像想象中那样黑暗，便试探性地睁开双眼，但立刻后悔了，因为你见到了比地面上那无头尸首更加令人绝望的恐怖——"
    extend "\n沙砾。"
    extend "\n满眼都是沙砾。但只消稍稍细看，那一颗颗的，分明就不是沙砾。"
    ## Extended大文本框结束
    ## 转场：眼珠背景
    scene black with scene_soft
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "每颗“沙砾”都是一颗无色透明多面体。"
    extend "\n而每颗多面体里，都有一颗泛着血丝的眼珠。"
    ## Extended大文本框结束
    ## 场景音乐参考：N2-14 - 从上次音乐停的位置继续播放，不要重头开始
    $ set_scene_music("route1_horror3")
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你绝望地想要把头抽出来，但原本稀松的沙地此刻如钢钳一般将你的头死死扼住，任凭双手在沙地上狂乱地挥舞抓挠，也无法动摇分毫 。"
    extend "\n你只能眼睁睁看着那些布满血丝的眼珠朝你的脸逐渐聚拢，随后——"
    ## Extended大文本框结束
    ## 连续破裂音效
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "它们一颗颗地在你眼前爆裂开来，里面迸发出浑浊的玻璃体与血液的混合物，飞溅到你脸上，温热而粘稠。"
    extend "\n所剩无几的空气中弥漫着你闻所未闻的诡异气味。那是尸体的味道，但其来源并非布满你颜面的异色粘液。"
    extend "\n几团大块的血污顺着你的脸颊缓缓滑下，留下一道道蜗牛足迹般的、亮晶晶的轨迹。"
    extend "\n尸体的味道越发浓烈。"
    extend "\n嘴唇也沾上了血污，怎奈双手与头颅天各一方，你无法想象在不扩大事态的前提下将嘴唇清理干净，只能强行忍受温热湿软的污物在唇上缓缓滑落的触感。"
    extend "\n你极力缩紧喉头，拼尽全力不哇地一声吐出来，但那念头很快就被另一种思绪所覆盖了。"
    ## Extended大文本框结束
    ## 居中大字文本框开始 - centered large font textbox
    centered_large_narrator "你想死。"
    ## 居中大字文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "尸体气味的浓度达到了顶峰。"
    extend "\n你早就清楚那气味的来源，只是还在试图移开目光。"
    extend "\n然而逃避与走投无路总是形影相随。"
    extend "\n当人制造了过多的尸体，那他自己迟早也会步入其造物的行列。"
    extend "\n你想死。"
    extend "\n你拼尽全力扼住自己的脖颈；你听见脑血管的轰鸣；视野四周开始坍缩，黑暗挤进来；你马上就要成功了。"
    extend "\n地心引力渐强，你的身躯逐渐被沙砾吞没。人为的窒息终于在血污将你口鼻覆盖之前到来。"
    extend "\n死亡，你此刻唯一的救赎在你面前舒展她魅惑的身躯。"
    extend "\n黑暗，一切都坠入黑暗，你的视野，你的身躯，你无际的意识。"
    extend "\n黑暗。"
    ## Extended大文本框结束
    $ stash_music_pos()
    $ current_music_scene = None
    stop music fadeout 3.0
    ## 转场：图片黑屏
    scene bg_black_still with scene_soft
    ## 电视机关闭音效
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "..."
    extend "\n......"
    extend "\n........."
    ## Extended大文本框结束
    ## 居中Extended文本框开始 - centered accumulating textbox
    centered_narrator "Demo到此结束，感谢游玩！"
    extend "\n欲知后事如何，还请在本作正式发售时继续支持！"
    ## 居中Extended文本框结束
    ## fade out 屏幕（图像+音乐+环境音）之后，reboot 回主菜单
    $ current_music_scene = None
    $ stop_ambient(2.0)
    stop music fadeout 2.0
    scene black with fade_to_black_long
    $ hard_pause(1.0)

    ## Route 1 结束
    $ unlock_route(1)
    ## demo 通关后整个游戏 reboot 一次，让 polyhedron channel 状态干净，
    ## 第二次 Start 不会渲染成 checker board。persistent 不会被清。
    ## 走 helper 而不是直接 utter_restart：自动化测试时跳过 reboot，
    ## 否则测试跑完进程无法退出（卡死在最后）。见 variables.rpy。
    $ demo_reboot_after_route()
