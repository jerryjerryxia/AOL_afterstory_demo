## route1.rpy
## Route 1

label route1_start:

## 一周目：浮潜

    call screen route_title(_("浮潜"))
    ## 脸入水后冒泡泡的音效
    ## 转场：虚空对视
    scene black with scene_soft
    $ current_scene_name = "虚空对视"
    $ current_scene_desc = "背景一片漆黑，场景里只有王霜和一张桌子，阿鹤第一视角看着盯着他的王霜，参考DDLC最后的莫妮卡"
    wangshuang "欢迎回来，阿鹤。"
    ahe "倒不如去死。"
    wangshuang "哦？有趣的提议，为什么呢？"
    ahe "我...不好意思...我觉得我有点..."

    menu:
        extend ""
        "不对劲...":
            pass
        "很有精神！":
            $ madness += 1
            pass

    wangshuang "嗯，从之前的病史来看，你总在这两个状态之间来回反复，但现在具体是什么感觉呢？"
    ahe "..."
    wangshuang "连这也说不出来么？"
    wangshuang "难说的话，或许聊聊你看到的，或者听到的，都是可以的，我在听呢。"
    ahe "我感觉...有某种暴戾的东西在我耳边一直说个不停，它想我去做一些非常恶毒的事情..."
    wangshuang "唔，这样。"
    ahe "我...又病了吗？"
    wangshuang "不，恰恰相反，阿鹤。要我说，你现在就像太阳一样稳定。"
    ahe "太阳？"
    ## 小吃惊
    wangshuang "哦，不好意思，太阳在那儿。"
    ## 玻璃破碎音效
    ## 转场：夏日对视
    scene bg_summergaze with scene_soft
    $ current_scene_name = "夏日对视"
    $ current_scene_desc = "金色的沙滩和蔚蓝的海，只是一个人都没有，场景里依然只有王霜。"
    ## 场景背景里的黑暗碎裂，变为完美夏日，金色的沙滩和蔚蓝的海，只是一个人都没有
    ## 场景音乐参考风格1：樹氷の輝き (Shine of Silver Thaw)，夜の向日葵（The sunflower of the night），Running Waters - https://audionautix.com/Music/RunningWaters.mp3 (Jason Shaw)，Shianchu
    ## 场景音乐参考风格2：Jellyfish - https://audionautix.com/Music/Jellyfish.mp3  (Jason Shaw)
    $ set_scene_music("route1_scene1")
    ## 默认
    wangshuang "你看，太阳。"
    ahe "嗯，太阳。"
    wangshuang "金色的，温暖的，让人舒适而安心的太阳，它就在那里。"
    wangshuang "对于沐浴日光中的人来说，明白这一点就够了。"
    ahe "可它分明是我视野里最暴烈而盛气凌人的造物。"
    wangshuang "那就闭上眼睛，你的问题便迎刃而解了。"
    ahe "可我还是我觉得我快要..."

    menu:
        extend ""
        "疯了...":
            pass
        "睡着了。":
            $ madness += 1
            pass

    wangshuang "那也是无可厚非的事情。"
    ahe "那怎么可能是——"
    wangshuang "当然就是这样的，阿鹤。"
    wangshuang "这是你的心理咨询，你是来访者，而我是咨询师。"
    ahe "所以...我该怎样才能好起来？"
    wangshuang "修补本就完整的东西，那自然是做不到的。"
    ahe "..."
    wangshuang "你不同意。"
    ahe "...你...求求你不要再浪费我的时间了..."
    wangshuang "时间，你要那东西有什么用？"
    ahe "我还要——我还得..."
    wangshuang "我在听。"
    wangshuang "不用紧张，阿鹤，你可以畅所欲言。"
    ahe "想不起来...什么都想不起来..."
    wangshuang "想想你为什么来到这里，或者想想你用你先前的时间做了什么事，都能帮助你回忆过去。"
    wangshuang "但即使什么也想不起来也不必懊恼，那是意料之中的过程。"
    ahe "这...这肯定又是你的把戏！"
    wangshuang "总是向外归因可解决不了问题啊，我的朋友。"
    wangshuang "你的病虽然看起来已经根治了，但以你的身心状态而言，任何时候复发我都不意外。"
    wangshuang "但你还是没回答我的问题——时间对现在的你而言，有什么用？"
    ahe "没用...完全没用...一切都结束了..."
    wangshuang "哦？所以还是想起来了一些。"
    ahe "你...毁掉了整个逝乐园。"
    wangshuang "不必谦虚啊，阿鹤，这件事少了你是绝对不可能成功的。"
    wangshuang "所以我愿意把领衔主演的名头让给你，我去当制片人就可以了。"
    wangshuang "你也不用觉得我抬举你，过度谦虚只会让人习惯性地逃避责任，是一种需要调整的心态。"
    ahe "我..."
    wangshuang "嗯，我懂的，在完成一件惊人的壮举后，出现冒充者综合征是非常常见的事情。"
    wangshuang "但不论你怎么想，事已至此，还是放平心态最重要。"
    ahe "...随便了..."
    wangshuang "哎你看你这人，三天两头向外归因，遇事不决就开始摆烂——"
    wangshuang "{size=-10}这就是为什么我——{/size}"
    ahe "什么？"
    wangshuang "没事。没事。阿鹤，你知道太阳为什么会死吗？"
    ahe "因为它想死。"
    wangshuang "错——太阳自出生的那一刻起便像氢弹般持续自毁，早就动了死的念头，但它还是在天上烧了四十多亿年。"
    ahe "我不明白..."
    wangshuang "你当然不明白，你肯定在想‘可这明明也是一种外因，毕竟整个太阳系都齐心协力地求它继续活下去’。"
    ahe "唔..."
    ## Extended文本框开始 - accumulating textbox
    wangshuang "然而现实恰恰相反"
    extend "——太阳不死仅仅是因为它的使命尚未完成而已。"
    extend "而它的死与它或其他任何造物的想法没有半点关系。"
    ## Extended文本框结束
    ## Extended文本框开始 - accumulating textbox
    wangshuang "想法是轻薄的、由外界塑造的，一坨烂泥一样谁都可以捏一把，但同时也是无足轻重的。"
    extend "而使命则是彻头彻尾、由内而外的"
    extend "——只有在‘使命’松手之后，‘想法’才配拥有虚假的自由。"
    ## Extended文本框结束
    ahe "这和我们又有什么关系？"
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
    wangshuang "但话说回来，瞪眼大赛啊，我接受挑战！"
    ahe "没说真要来啊..."
    ## 面无表情
    show screen op_lock(2)
    wangshuang "盯——"
    ahe "..."
    show screen op_lock(2)
    wangshuang "盯——"
    ahe "..."
    wangshuang "噗——"
    ahe "..."
    ## 大笑
    wangshuang "——噗噗呃啊——我败了..."
    ahe "自取其辱啊，阿霜。"
    wangshuang "你还有脸得意！能盯着你那张臭脸看这么久还不笑的就只有死人了。"
    ahe "嗯...所以我每天刷牙的时候都要死一次..."
    wangshuang "你能活到今天确实不容易。"
    ahe "还不是拜你所赐..."
    ## 默认
    wangshuang "不用谢不用谢。那你来吧，拿走你的战利品。"
    ahe "哈？"
    wangshuang "别哈，让你来你就来。"
    ## 屏幕缩放，显得王霜近了很多
    ahe "是什么东西？"
    wangshuang "你看就是了。"
    ## 转场：张目对日pt1
    scene bg_sungaze with scene_soft
    $ current_scene_name = "张目对日pt1"
    $ current_scene_desc = "王霜右手对着太阳比出OK的姿势，阳光透过拇指和食指构成的细小的孔洞透了过来"
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
    scene black with scene_soft
    $ current_scene_name = "白屏"
    $ current_scene_desc = "就是白屏。"
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "去找啊，否则这疼痛就永远不会有尽头。"
    extend "\n去别处，就是这样。"
    extend "\n否则这疼痛就永远不会有尽头。"
    extend "\n你的大脑不会适应，你也绝无希望自我了断。"
    extend "\n只能迈开步子。"
    extend "\n只有这一个选择。"
    extend "\n去找吧。"
    ## Extended大文本框结束
    ## 白屏逐渐褪去
    ## 转场：甜品店对视1
    scene bg_dessertgaze1 with scene_soft
    $ current_scene_name = "甜品店对视1"
    $ current_scene_desc = "基础款，暖色，桌上没有团子，背景完全正常"
    ## 一家疑似餐厅的背景，又是王霜和阿鹤面对面坐着
    ## 场景音乐风格参考：怎么说呢...虽然台词可能对抗感比较强，但这种场景还是得要一些 lo-fi 小调啊...Moonlit Reverie - 好lofi，Hoyoku, Sutekimeppou - 这几首物语的 ost 也很有内味儿嗷
    $ set_scene_music("route1_scene2")
    ahe "呃啊——！"
    ## 疑惑
    wangshuang "怎么了？"
    ahe "你刚刚...是不是对我做了非常不得了的事情。"
    wangshuang "你盯着我发呆，我盯着你发呆，确实挺不得了的。"
    ahe "呃...所以我们为什么在这里？"
    wangshuang "这可是你说要来的。"
    ahe "那我要走了。"
    wangshuang "我们刚坐下诶，你要去哪儿？"
    ahe "不知道，要离开这里就是了。"
    ahe "...能麻烦开一下门吗？"
    ## 默认
    wangshuang "不如问问店家。"
    ahe "好吧...你好，能帮我把门开一下吗？"
    wangshuang "不好意思啊先生，老板刚才说了，今天店里的客人都必须留到天黑之后才能走。"
    ahe "可是天已经黑了。"
    wangshuang "老板说，还不够黑。"
    ahe "好吧...所以我能走了吗？"
    wangshuang "不能。"
    ahe "你好烦。"
    ## 撇嘴
    wangshuang "就算出去了，你准备做什么？"
    ahe "把大石头推上山，把琴弦拧成电缆，什么都可以。"
    wangshuang "意思是你准备换个地方无所事事。"
    ahe "再无所事事都胜过和你呆在这里。"
    ## 疑惑
    wangshuang "啊，已经这么遭人嫌了么..."
    ahe "...多少有点自知之明吧你..."
    ## 撇嘴
    wangshuang "彼此彼此咯，我们都只是遵循着强烈的愿望，尝试了一直以来想要尝试的事情。"
    ahe "区别在于我不需要人陪葬。"
    wangshuang "不，区别在于我做到了，而你没有。"
    ahe "..."
    ## 默认
    wangshuang "而你拒绝与我共处一室的真正原因只是嫉妒，仅此而已。"
    ahe "闭嘴吧..."
    ## 坏笑
    wangshuang "我闭嘴了又有什么用？难道你那苍白的“理想”就不需要人来陪葬了？"
    wangshuang "你为了{i}尤里娅{/i}那小姑娘折断了多少人的骨头？阿鹤，狡辩是没有意义的，无论如何我们都是逝乐园覆灭的共犯。"
    ahe "..."
    ## 转场：甜品店对视2
    scene bg_dessertgaze2 with scene_dissolve
    $ current_scene_name = "甜品店对视2"
    $ current_scene_desc = "暖色，桌上出现了团子，背景完全正常"
    ## 默认
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
    wangshuang "你这人，连真心话都不让人说。"
    ahe "你？真心话？笑话可以再冷点么？"
    wangshuang "连这都分不清，以后可是要吃大亏哦。"
    ## 手中出现无色透明多面体，多面体形状略微改变2
    wangshuang "哦，对，团子有得是，千万别客气，请吧——"
    ## 转场：甜品店对视3
    scene bg_dessertgaze3 with scene_dissolve
    $ current_scene_name = "甜品店对视3"
    $ current_scene_desc = "暖色，桌上的团子被吃了几口，背景完全正常"
    ahe "明明刚说完不想我染上。"
    wangshuang "{i}KAS{/i}生理上确实不怎么成瘾啊。"
    wangshuang "但太多人会陷进它能让人看到的那些东西，最后心里离不开了，所以你才能在安息地见到那么多活死人。"
    wangshuang "那么你会怎样呢，阿鹤？我很期待哦。"
    ahe "只致幻的话岂不是很无聊，尤其对你来讲。"
    ## 小激动
    wangshuang "无聊？可别太刺激了！你知道十二小时起步的感官过载是什么感觉吗？"
    wangshuang "五感全部推到极限，尤其是视觉，所有东西的颜色都比平时看到的要鲜艳无数倍，而且全都彼此交融，到最后视野里就是五彩斑斓的白。"
    ## Extended文本框开始 - accumulating textbox
    wangshuang "所有东西都是饱满到极致的，你懂我意思吗？"
    extend "就不是某种感官上的饱满，而是存在上的饱满，第四维度上的饱满，就是那种...不论我们怎么干涉都无法改变的状态。"
    ## Extended文本框结束
    ## Extended文本框开始 - accumulating textbox
    wangshuang "然后就觉得“我操这下不得了了要被外部存在的压强挤碎了快他妈跑”，然后据说是就开始往窗户外面跳...也不知道是被谁拉住的，是你吗？"
    extend "应该不是，你应该拽不住我。"
    ## Extended文本框结束
    ## 默认
    wangshuang "总之要不是后来配了眼镜，不然我是绝对不敢乱用{i}KAS{/i}的，那次是真的差点死了..."
    ahe "哦，原来你那“磕完药差点死掉的小故事”还在更新啊。"
    ## 小激动
    wangshuang "那可是正儿八经的人命啊喂！"
    wangshuang "不过一般人应该不会那么夸张。你会喜欢的，我觉得。"
    ahe "所以我们要在这里待到什么时候？"
    wangshuang "等时机到了，自然就能离开。"
    ahe "也是一种较为朴素的过程？"
    wangshuang "哦？如此简明且精确的定义，谁教你的？"
    ahe "一个傻逼。"
    ## 小激动
    wangshuang "{shake}好刻薄！{/shake}"
    ahe "像您这样有成就的大人物，只被骂傻逼还请偷着乐吧。"
    wangshuang "所以确实没法放过我了吗？"
    ahe "你还需要人放过？"
    ## 默认
    wangshuang "当然，我又不是没有罪恶感的人。"
    ahe "存疑。"
    wangshuang "哎阿鹤，虽然有些事情我确实做得...不太好...从世俗意义上来说，但也没必要这样质疑我演戏的质量嘛。"
    ahe "你看，你都自首了。还不逮捕你自己。"
    ## 撇嘴
    wangshuang "那我还得兼任检察官辩护律师和法官，太麻烦了。"
    ahe "用来消磨时间正合适，反正用不完。"
    wangshuang "不不不那就不对了，如果你还想“消磨时间”，那就说明你修为尚浅，还没悟透其中道理。"
    ahe "...好的，师傅。"
    ahe "话说师傅，你手里拿的是什么？"
    wangshuang "哦，这个？不是什么重要的东西，但你可以尝尝看。"
    ahe "尝尝看？"
    wangshuang "对啊，吃的。要不要试试？"

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

    ahe "蓝色啊，怎么了？"
    wangshuang "你看——"
    ## 转场：甜品店对视4
    scene bg_dessertgaze4 with scene_dissolve
    $ current_scene_name = "甜品店对视4"
    $ current_scene_desc = "背景变成了蓝色调，桌上团子吃了几口，背景有微弱的波纹纹理"
    ## 蓝色波纹特效，并逐渐加入更多色彩
    ## 场景音乐参考：进入幻视，所以虽然场景没变音乐也要切换https://audionautix.com/Music/Beautiful%20Daughter.mp3 (Jason Shaw)，
    $ set_scene_music("route1_hallucination")
    ## Split Extended大文本框开始 - 左右分栏
    split_left_narrator "你正摸不着头脑，转眼间却发现了周遭惊人的变故——四周逐渐泛起蓝色、波浪状的纹理，很快侵蚀了整个视野。"
    extend "\n你反倒比先前要更加冷静，又低头吃了几口团子。甜腻腻的滋味在口腔中涟漪般散开，每颗味觉细胞都在欣喜若狂地发送着饱足的信号。"
    $ _split_left_text = "你正摸不着头脑，转眼间却发现了周遭惊人的变故——四周逐渐泛起蓝色、波浪状的纹理，很快侵蚀了整个视野。\n你反倒比先前要更加冷静，又低头吃了几口团子。甜腻腻的滋味在口腔中涟漪般散开，每颗味觉细胞都在欣喜若狂地发送着饱足的信号。"
    split_right_narrator "甜味的颜色？金黄的莓红的草绿的深棕的，味觉的色彩洪流汇入弥漫在整个视觉空间的海蓝色波浪中。"
    extend "\n你抬头望向王霜，她也望着你，脸上含蓄地挂了一抹邪魅而欣慰的笑，仿佛望着一个迷路的孩子。"
    extend "\n她略卷的水蓝色长发在空间的蓝色波浪中散着，勾勒出洋流的轮廓。"
    ## Split Extended大文本框结束
    ## Split Extended大文本框开始 - 左右分栏
    split_left_narrator "你心中对她海啸般的戒心早已荡然无存了——你几乎有些喜欢她现在的样子，宛如一个母亲，又像是神明，给视野不断抹上温柔的蓝色。"
    extend "\n每一缕神经都在扩张。启示性的景象。时间和空间波浪。无孔不入的色彩和甜味。蓝色的。交响。"
    $ _split_left_text = "你心中对她海啸般的戒心早已荡然无存了——你几乎有些喜欢她现在的样子，宛如一个母亲，又像是神明，给视野不断抹上温柔的蓝色。\n每一缕神经都在扩张。启示性的景象。时间和空间波浪。无孔不入的色彩和甜味。蓝色的。交响。"
    split_right_narrator "反复咀嚼伤痛直至淡而无味，直到甜味凭空冒出来。"
    extend "\n在一切都已结束的当下，连时间都已丧失价值，唯一还能让你睁开双眼的，就只有——"
    ## Split Extended大文本框结束
    ## 居中大字文本框开始 - centered large font textbox
    centered_large_narrator "瘾。"
    ## 居中大字文本框结束
    ## Split Extended大文本框开始 - 左右分栏
    ## 转场：甜品店对视5
    scene bg_dessertgaze5 with scene_dissolve
    $ current_scene_name = "甜品店对视5"
    $ current_scene_desc = "背景蓝色调，桌上团子吃了几口，背景有更明显的波纹纹理，王霜变得半透明，表情是默认表情"
    split_left_narrator "王霜的微笑越发邪魅——她逐渐成为了一个微笑。"
    extend "\n成瘾。糖分子的洪流只消一个浪头就使你深深染上了挥之不去的瘾。"
    extend "\n渴望的源头冲动的源头想往的源头发现了。"
    $ _split_left_text = "王霜的微笑越发邪魅——她逐渐成为了一个微笑。\n成瘾。糖分子的洪流只消一个浪头就使你深深染上了挥之不去的瘾。\n渴望的源头冲动的源头想往的源头发现了。"
    split_right_narrator "浪潮般的甜味反复沁进意识。她开始微笑。她停止微笑。目光所及之处就能看见她的微笑。"
    ## Split Extended大文本框结束
    ## Split Extended大文本框开始 - 左右分栏
    split_left_narrator "燥热意识模糊，痛苦消减。鼓的声音。恒久的鼓声从背景里逐渐浮现，强烈起来，震耳欲聋，每一击都与心跳同调。"
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
    $ current_scene_name = "甜品店对视6"
    $ current_scene_desc = "背景蓝色调，桌上团子吃了几口，背景有更加明显的波纹纹理。从这里开始王霜消失了，但是是和世界融为一体的感觉。"
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
    $ current_scene_name = "甜品店对视6.51"
    $ current_scene_desc = None
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
    extend "\n随着肠胃痉挛越发剧烈，你终于“哇”地一声吐了出来。"
    extend "\n和你所熟知的呕吐不同，你吐出的只有色彩。"
    ## 转场：甜品店对视7
    scene bg_dessertgaze7 with scene_dissolve
    $ current_scene_name = "甜品店对视7"
    $ current_scene_desc = "背景蓝色调和暖色调掺半，是那种正常色彩顺着阿鹤呕吐为中心开始向四周扩散的感觉，桌上团子吃了几口，背景里的波纹纹理消失，王霜完全消失"
    large_narrator "呕吐物与面前桌子接触的瞬间，水蓝的桌面便恢复了木材的颜色，这令人沮丧的还原随着你吐出更多的色彩而提速，很快覆盖了大半个视野。"
    extend "\n色彩还原的地方，水面般摇曳的空间停止了动态，原本随处可见的王霜的微笑也随着视野的复原逐渐消失了。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你感到疲惫不堪，只想回到一个更加清醒的地方。"
    extend "\n眼前桌子的存在与本质看起来产生了某种根本性的分离，但你已经没有心力去捕捉这种细节。"
    extend "\n因为你注意到，在美妙的蓝色消逝殆尽后，王霜并没有回来。"
    extend "\n空空如也的店里坐着空空如也的你。"
    ## Extended大文本框结束
    ## 画面出现裂痕
    ## Extended大文本框开始 - accumulating large textbox
    ## 转场：甜品店对视8
    scene bg_dessertgaze8 with scene_dissolve
    $ current_scene_name = "甜品店对视8"
    $ current_scene_desc = "这里就是以7为基础，逐渐碎裂然后转入黑屏的过程，我想就在周围背景里加一些裂纹就行。"
    large_narrator "还原之后的世界仿佛脱了水般脆弱不堪，单是目光扫过就让其表面生出了细小的裂痕。"
    extend "\n更多裂痕。"
    extend "\n直到周身的一切如同一副缺乏保养的老旧油画那样一片片剥落。"
    extend "\n即使如此，王霜依旧没有回来。"
    ## Extended大文本框结束
    ## 转场：黑屏
    scene black with scene_soft
    $ current_scene_name = "黑屏"
    $ current_scene_desc = "就是黑屏"
    ## 剥落完成后，黑屏
    ## 水底泡泡上浮音效：Bubbles_10
    ## 转场：粉红屏
    scene black with scene_soft
    $ current_scene_name = "粉红屏"
    $ current_scene_desc = "就是粉红屏。"
    $ current_music_scene = None
    stop music fadeout 1.0

    ## Route 1 结束
    $ unlock_route(1)
    ## demo 通关后整个游戏 reboot 一次，让 polyhedron channel 状态干净，
    ## 第二次 Start 不会渲染成 checker board。persistent 不会被清。
    ## 走 helper 而不是直接 utter_restart：自动化测试时跳过 reboot，
    ## 否则测试跑完进程无法退出（卡死在最后）。见 variables.rpy。
    $ demo_reboot_after_route()
