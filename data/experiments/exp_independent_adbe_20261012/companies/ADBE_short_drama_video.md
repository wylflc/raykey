# 短剧与创意视频的增加，能不能给 Adobe（NASDAQ: ADBE）带来业务增加（2026-10-12）

```
结论：短剧本身对 Adobe 无关紧要；更广义的创意视频（主要是生成式视频）是真实增量，但已经包含在基准情景里，不构成上调基准的理由。
① 需求确实大增：中国微短剧 2025 年产业规模过千亿元，2026 年前 8 个月上线 43 万部（九成以上是 AI 剧）；海外短剧应用内购 2025 年 29.8 亿美元（+115%），2026 年已降到 +13%～+20%。
② 精品短剧会用 Adobe：正片后期招聘里 Premiere（剪辑）出现率 81%、After Effects（特效包装）39%；达芬奇出现率 87%，调色岗全部以它为首。证据来自招聘原文，强度中等；具体剧目的直接证据为零。
③ 用了不等于付费：Adobe 在中国大陆不卖个人订阅，Firefly（生成式 AI）与 Premiere 手机版都不对大陆开放，正版率未查到；中国短剧估计只带来约 100～200 万美元 ARR。
④ 海外短剧按席位算也只有百万美元级：一部剧的后期是 1 名剪辑、1 名调色、1 名混音，五六周做完；全行业几千人。
⑤ 真正的通道是生成积分：视频生成次数同比增 8 倍，Firefly 应用与积分包 ARR 连续三季环比 +75%、+50%、+40%，但体量只有约 1.3 亿美元（本文推算）；AI 原生对手更大（可灵年化约 5 亿美元）。
⑥ 未来 3～5 年增量 ARR：最可能每年约 +1.5 亿美元（Total ARR 的 0.5%，净新增 ARR 的 7%）；乐观每年 +5.7 亿；悲观每年 −0.6 亿。
⑦ 跟踪：Firefly ARR、AI-first ARR、创意 freemium 月活、圣丹斯 Premiere 占比、订阅毛利率，门槛见第 6 节。
```

口径与取证方式：

- 美元为主，"亿"即 1 亿；人民币注明"元"。人民币折美元按 1 美元约 7.2 元粗算（本文假设）。Adobe 财年止于 11 月末，FY26 止于 2026-11-27。ARR 指年化经常性收入。
- 每条内容按性质标注：**事实**（监管数据、公司申报、官方页面原文）、**说法**（公司或机构的口径与估计）、**估计**（本文自己算的，写明假设，读者可改数重算）。行业数据大多是机构估计，不同来源并列给出。
- 名词：Premiere 是 Adobe 的剪辑软件，After Effects 是特效与合成软件，Frame.io 是云端审片协作工具，Firefly 是 Adobe 的生成式 AI 模型与应用，按"生成积分"计量用量。达芬奇即 DaVinci Resolve，是 Blackmagic 公司的调色与剪辑软件。剪映的海外版叫 CapCut。freemium 指免费使用、高级功能付费。AI-first ARR 是 Adobe 对 AI 原生产品 ARR 的统称。MAX 是 Adobe 的年度大会，NAB 是美国广播电视设备展。
- 取证由本文作者加四个并行的检索子任务完成，作者对其中二十多条关键事实重新打开原文核对（文中不逐条标注）。本次联网检索额度在中途用尽（多项任务共用），所以"未查到"分两种：检索后没有结果，和没能检索；见第 7 节。
- 客户分类与各类客户的增长数据由另一份材料负责，本文只在需要时引用 Adobe 自己披露的数字。Adobe 的整体估值与情景见[10-12 复核](ADBE_Adobe.md)、[Canva 专项](ADBE_vs_Canva.md)、[Figma 专项](ADBE_vs_Figma.md) [S22]。

## 1. 需求端到底增加了多少

**结论**：内容产量是爆炸式增长，但增长主要来自 AI 生成的剧，而不是需要人做后期的实拍剧。实拍短剧的开机量在 2026 年是下降的；海外应用内购的增速也从三位数降到了一两成。专业剪辑师的人数几乎不增长。

### 1.1 中国微短剧

| 指标 | 2023 | 2024 | 2025 | 2026（最新） | 性质与来源 |
|---|---|---|---|---|---|
| 产业规模（亿元） | 约 374（由 2024 年反推） | 504.4（+34.9%），超过电影票房 425 亿 | "突破千亿元"；电影票房 518 亿 | DataEye 预估微短剧加 AI 剧漫剧合计超 1,210 亿 | 2024 年是协会白皮书口径；2025 年是广电总局口径；艾媒 2025 年只有 678 亿，口径不同 [S23][S24][S26] |
| 上线部数（全口径） | 未查到 | 未查到 | 3.3 万部 | 前 8 个月 43 万部，"是去年全年的 13 倍"，AI 剧占九成以上；同期下架违规 6.8 万部 | 事实（广电总局发布会）[S23] |
| 重点微短剧（投资 100 万元以上） | 备案 3,574 部 | 约 480 部上线（反推） | 上线 625 部（+30%） | 未查到 | 事实与反推 [S24] |
| 用户规模 | 未单列 | 6.62 亿（12 月，使用率 59.7%） | 6.64 亿（12 月，59.0%） | 广电总局称"超过 8 亿人"；QuestMobile 2026-05 去重 8.51 亿 | CNNIC 是抽样调查；后两者口径更宽 [S23][S25][S30] |
| 红果短剧月活 | — | — | 2025-06 破 2 亿；2025-12 为 2.75 亿 | 2026-06 为 3.68 亿（+74%），超过腾讯视频 3.19 亿、爱奇艺 2.91 亿 | 说法（QuestMobile）[S30] |
| 带动就业 | — | 64.7 万个 | 133.3 万个岗位（协会）；北大估计直接就业约 69 万人，其中制作团队约 45 万人 | AI 剧漫剧从业者与个人创作者"超过 50 万"（DataEye 预估） | 说法；**后期或剪辑人数没有任何机构单列** [S27][S28][S29] |

单部成本、周期与后期（均为访谈与调研口径，性质为说法）：

| 档次 | 单部成本 | 周期 | 后期 | 来源 |
|---|---|---|---|---|
| 下沉低成本 | 5 万～10 万元 | 拍 1～3 天，剪辑约 5 天 | — | [S31] |
| 常规实拍（80 集左右） | 40 万～80 万元；单分钟 8,000～1.2 万元 | 拍 6～10 天，剧组 40～80 人 | "一部 80 集短剧的剪辑约需半个月，剪辑师每集报酬 400～500 元"，折合每部 3.2 万～4 万元，约占成本 5%～8%（后一步是本文推算） | [S31] |
| 精品 | 《盛夏芬德拉》约 800 万元，《家里家外 2》约 600 万元 | 前者"拍摄 11 天＋后期三个月"，后者拍 30 天 | 后期预算与人数未查到 | [S31] |
| 平台自制（横屏） | 腾讯视频《执笔》2 亿元 | — | — | [S31] |
| 后期团队产能 | — | — | "后期团队亦可实现月度 8—10 部的交付节奏" | [S28] |

付费与免费的结构、精品化动作：

- **免费取代付费**：免费短剧的市场份额 2024 年 1 月为 11%，10 月到 50%；2025 年广告分账约占七成。DataEye 预估 2026 年免费微短剧约 573 亿元，同比只增 8%，"进入平稳增长期"。抖音小程序短剧用户同比 −83% [S26][S30]。
- **监管**：2025 年起按投资额分三层审核（100 万元以上为重点）；《微短剧发展管理办法》2026-09-01 施行，要求 AI 生成的剧每集加标识；AI 动画微短剧 2026-04-01 起未备案下线。**办法没有任何画质或技术指标**，各平台也没有查到公开的技术交付规范（分辨率、码率、色彩、响度）[S32]。
- **平台**：抖音与红果 2026 年真人短剧保底预算超 15 亿元，红果另投 5 亿元专项资金；广电总局表态"真人剧是精品创作的主力，要大力扶持"。同时红果在 2026 年初取消了中小团队 20 万～35 万元的保底 [S23][S33]。

### 1.2 出海与海外本土短剧

| 指标 | 数字 | 性质与来源 |
|---|---|---|
| 全球短剧应用内购收入（Sensor Tower，苹果加谷歌商店，不含广告与网页直付） | 2025 年 29.8 亿美元（+115%）；2026 年一季度约 7.5 亿美元（**+20%**）；一季度下载 8.5 亿次（+140%），四分之三来自东南亚、拉美、印度 | 说法 [S37] |
| 同一市场（DataEye，口径略窄） | 2025 年 22.8 亿美元（+129%）；2026 年上半年 12.7 亿美元（**+13%**）；8 月单月 2.89 亿美元 | 说法 [S38] |
| 全口径预测（含广告） | MPA：中国以外 2025 年 27 亿、2026 年 36 亿、2031 年 95 亿美元（年复合 21%）；美国 15 亿到 37 亿 | 说法 [S39] |
| ReelShort（枫叶互动）公司层面 | 2025 年收入 57.21 亿元（上年 29.10 亿），**净亏损 0.86 亿元**；2026 年 1～3 月收入 15.70 亿元、净利 0.56 亿元 | 事实（中文在线年报与半年报）[S40] |
| 头部应用 | 2026 年一季度 DramaBox 与 ReelShort 各近 1.4 亿美元内购；ReelShort 约 7,000 万月活，北美占收入 59%。中国以外份额：ReelShort 29%、DramaBox 21%、DramaWave 13%、NetShort 10%。ShortMax 2026-08 月收入约 860 万美元，已跌出千万美元档 | 说法 [S37][S38][S39] |
| 美国本土拍摄量 | 洛杉矶"估计每月 30 到 40 部在拍"（2025 年中）；温哥华任何时点至少 20 部；ReelShort 每月 15～16 部（2024 年），目标每天一部 | 说法；**没有全行业年产量的权威统计** [S41] |
| 单部预算与周期 | 10 万～30 万美元，拍 7～10 天，每天 13～20 页剧本；后期约占预算 10%，"通常是一名剪辑师、一名调色师、一名混音师" | 说法（制片人与承制方）[S41] |
| 后期周期 | "一部长片在大约五周内剪完"；哥伦比亚一家后期公司每部剧 6 周 | 说法 [S61][S62] |
| 本土剧与译制剧 | 2026 年上半年在投本土剧（含 AI 原生剧）份额从 27% 升到 46% | 说法（按投放素材统计）[S38] |
| 从业者总数 | 未查到。洛杉矶外景拍摄日 2026 年二季度同比 −12%，只有含网络内容的"其他"类 +10% | 事实（FilmLA）[S43] |

### 1.3 AI 短剧与漫剧

漫剧指 AI 生成的动态漫画短剧；仿真人剧指 AI 生成的真人风格短剧。

| 指标 | 数字 | 性质与来源 |
|---|---|---|
| 产量占比 | 2026 年一季度上线约 12.8 万部，AI 剧占 95% 以上，**但只占核心播放量 4%**；前 8 个月 AI 剧占上线量九成以上 | 事实与说法（协会、广电总局）[S23][S35] |
| 抖音端新剧 | 2026 年上半年 AI 剧漫剧 22.19 万部，破亿播放的 1,055 部（0.48%），过盈亏线的 1.3% | 说法（DataEye）[S27] |
| 市场规模 | 2025 年 168 亿元，2026 年预估 400 亿元；其中超过 200 亿是付给视频大模型的钱，Seedance 占 69%、可灵占 17% | 说法；同一机构 3 月还只预测 240 亿，可信度低 [S27] |
| 每分钟成本 | 漫剧 2024 年约 1.5 万元，2026 年上半年 200～300 元；仿真人剧 800～1,000 元；约为实拍的 2%～10% | 说法（公司访谈、券商研报）[S34] |
| 团队 | 从 15 人减到 3～5 人，周期从 4 周压到 10 天；"5 个人花了 8 天左右"做完 60 集 | 说法 [S34][S63] |
| 对实拍的替代 | 横店在拍竖屏短剧剧组：2025-08 约 150 个，2026-05-12 为 33 个；一家头部公司导演团队从 80 多人减到 30 人、AI 部门扩到 200 多人；九州文化 4,000 名员工里 80% 是 AI 创作者和剪辑师 | 前者是事实（横店官方海报），后者是说法 [S31][S36] |
| 海外 | DramaWave 2026 年 7 月上新超 90% 为 AI 生成；Inkitt 的 AI 短剧每部 3～4 周、6 万美元以内（实拍 10 万～30 万美元、约三个月）；一位承制方称二季度实拍项目缩减三到五成（单一受访者） | 说法 [S41][S42] |

### 1.4 更广义的创意视频

| 指标 | 数字 | 性质与来源 |
|---|---|---|
| 专业剪辑师人数（美国） | 2025 年 39,400 人，预计 2035 年 40,800 人，**十年只增 4%**；中位年薪 75,420 美元；35% 自雇 | 事实（美国劳工统计局，2026-08-27 更新）[S44] |
| 好莱坞整体就业 | 电影与视频制作业雇员 2022-08 为 27.8 万，2026-08 为 18.6 万（−33%） | 事实（美国劳工统计局）[S44] |
| 创作者人数 | 全球约 5,000 万创作者，约 4% 是年入 10 万美元以上的职业创作者（2023 年数）；美国创作者广告支出 2025 年 370 亿美元（+26%） | 说法（高盛、IAB）[S45] |
| 平台创作量 | YouTube Shorts 日均播放超 2,000 亿次；全站日均上传超 2,000 万条；2025 年 12 月日均超过 100 万个频道使用 YouTube 自带的 AI 创作工具 | 事实（YouTube 官方）[S46] |
| 平台自带工具的渗透 | "每天被观看的 Reels 中近 10% 是用我们的 Edits 应用制作的，较上季度几乎增至三倍" | 事实（Meta 2025 年四季度电话会）[S47] |
| 视频广告 | 美国数字视频广告 2024 年 640 亿美元，2026 年预计超 800 亿（+11%）；近三分之二买方已把生成式 AI 用于视频创意 | 说法（IAB）[S48] |
| 企业视频 | 40% 的团队计划增加视频预算（2023 年是 57%），近四成公司全年视频制作花费低于 5,000 美元 | 说法（Wistia，样本 900 多人）[S49] |

### 1.5 需求增加不等于后期人数增加

- **事实**：2025 年中国全口径上线 3.3 万部。**估计**：按"一名剪辑师半个月剪一部"算，全部正片主剪只需要约 1,400 个全职剪辑师年；加上调色、声音、包装、助理，正片后期约几千到一两万人。人数更多的是剪投放广告素材的"投流剪辑"和 AI 生成岗位。
- 2026 年新增的四十万部里九成以上是 AI 剧，它们的"后期"是三五个人在剪映里完成的（见第 2.5 节）。
- 美国的对照：视频内容十年来一直在增，剪辑师人数预测十年只增 4%，影视制作业就业四年减少三分之一。视频的量和专业席位的量早已脱钩。

## 2. 短剧实际用什么工具做后期

**结论**：实拍短剧的正片后期是"达芬奇加 Premiere"的组合，Adobe 的位置在剪辑和特效包装，调色不在 Adobe 手里。越靠近低成本、投流素材和 AI 剧，剪映越是主力。海外头部平台的岗位同时要求 Premiere 与达芬奇。Adobe 的生成式功能在这条产业链上没有出现过。

### 2.1 招聘启事统计（主要证据）

样本：中国 124 条（猎聘 118 条、校招转载 6 条，2023-10 至 2026-10 发布，2026-10-12 抓取时均在线）；海外 23 条（已打开原文且点名软件）。同一职位多城市重复发布只计一条。数字是点名该软件的启事条数 [S59][S60]。

| 软件 | 中国正片后期（点名软件 31 条） | 中国投流素材（29 条） | 中国漫剧与 AI 短剧（56 条） | 海外（23 条，其中正片 12 条） |
|---|---|---|---|---|
| 达芬奇（DaVinci Resolve） | **27（87%）** | 5 | 21 | 18（正片 10） |
| Premiere | **25（81%）** | 27（93%） | 44（79%） | 18（正片 11） |
| After Effects | 12（39%） | 17 | 29 | 10 |
| 剪映（海外为 CapCut） | 6（19%） | 19（66%） | 38（68%） | 3 |
| Final Cut Pro | 7 | 3 | 13 | 3 |
| Photoshop | 4 | 13 | 13 | 4 |
| Audition / Pro Tools | 4 / 1 | 2 / 0 | 3 / 0 | 0 / 1 |
| 可灵、Runway、即梦或 Seedance | 0 | 1 | 22、20、19 | — |
| Firefly、Frame.io、Substance | 0 | 0 | 0 | 0 |

读表要点：

- 正片后期 31 条里，22 条同时写 Premiere 与达芬奇；只写达芬奇的 5 条（含九州文化、横店的刚刚好影视）；只写 Premiere 的 3 条（含巨豹互娱、四月文化）。没有一条只写剪映。
- 调色岗 3 条全部以达芬奇为首。没有一条启事把 Premiere 或 After Effects 写成调色工具。
- 把剪映写成主力的原文集中在 AI 剧和投流岗："剪映（主力）""优先剪映专业版（短剧行业主流）""用电脑版剪映完成 AI 短剧成片""剪映专业版（主要）"。
- 海外核心样本（ReelShort、DramaBox、中文在线海外子公司、Holywater 的正片岗共 6 条）：Premiere 6 条、达芬奇 6 条（其中 2 条为加分项）、After Effects 4 条，CapCut 0 条。
- 局限：中国样本几乎来自猎聘一家，不是随机样本；启事写的是雇主接受哪些软件，不等于实际装机，更不等于付费。124 条里"正版""授权"出现 0 次。

### 2.2 其它证据

| 类型 | 内容 | 强度 |
|---|---|---|
| 承制公司在职位描述里的一手表述 | 巨豹互娱"红果真人竖屏短剧剪辑（主剪）"："熟练使用 PR、AE 等剪辑工具进行竖屏短剧的后期制作"，自述代表作《朱砂吻》等十部；麦芽传媒自制剧后期："精通 pr 或 DaVinci 软件操作，能用 pr 完成 80% 的后期处理"；自述"专注精品短剧制作"的杭州云帧："熟练使用 PR/剪映/Davinci/AE 等工具"；九州文化正片剪辑："熟练使用达芬奇等视频剪辑工具"；映客系剪辑组长岗把三个环节分开写：剪辑用 Premiere 或 Final Cut，特效用 After Effects 或 Nuke，调色用达芬奇 [S59] | 中 |
| 海外幕后报道 | 洛杉矶竖屏工作室 Super Punchy 的 60 集短剧《Step by Step》："Editing was via Adobe Premiere."；制片人 Elizabeth Dell："Frame.io is a lifeline for edit notes across all our team"（Frame.io 是 Adobe 的云端审片工具）[S61] | 中 |
| 达芬奇厂商（Blackmagic）案例 | 官网有 5 条竖屏短剧案例，全部是海外项目，后期全程在达芬奇里完成；其中一位为 My Drama 拍剧的导演说"我使用其他剪辑软件已经超过十年了，但 Resolve……真的让我成了它的忠实粉丝"。中国内地短剧案例 0 条（2023-01 至 2026-10 的 658 篇新闻稿）[S62] | 中（厂商自选案例，不代表份额） |
| Adobe 官方渠道 | 官方英文博客 2025 年以来 311 篇正文，"microdrama""vertical drama""ReelShort"均 0 命中；6 份财报电话会逐字稿（FY25 Q2 至 FY26 Q3，本文自行检索）里短剧相关词、"Frame.io"均出现 0 次；Frame.io 官方博客与客户案例页也没有短剧客户 [S1][S2][S3][S4][S5][S65] | 较强（限已查范围） |
| 培训课程大纲（14 个样本） | 真人短剧后期课教 Premiere、After Effects、达芬奇、C4D；8 门 AI 漫剧课里 5 门教剪映，0 门教 Premiere，全部教即梦、可灵等生成工具；Firefly 出现 0 次 [S64] | 弱（样本小，含机构软文） |
| 中国从业者访谈、具体剧目的后期公司与工程信息 | 《盛夏芬德拉》《家里家外》等剧目，听花岛、柠萌、长信等厂牌，爱奇艺、腾讯、优酷、芒果与红果自制的后期流程：**未查到** | 无 |

### 2.3 按环节与类型的工具表

| 环节 | 中国常规实拍 | 中国精品与平台定制 | 海外本土实拍 | AI 短剧与漫剧 |
|---|---|---|---|---|
| 剪辑 | Premiere 或达芬奇；低成本项目有剪映专业版 | Premiere 或达芬奇（招聘层面证据）；具体剧目未查到 | Premiere 与达芬奇并列；偶见 Avid、Final Cut | 剪映为主，Premiere 次之；一站式工具自带合成 |
| 调色 | 达芬奇 | 达芬奇 | 达芬奇 | 多数不单独调色；少数用达芬奇 |
| 特效与包装 | After Effects；少量 Nuke | After Effects、Nuke | After Effects | After Effects 做合成与字幕包装；修复补帧用 Topaz、RIFE |
| 声音 | Audition（少量点名） | Audition、Pro Tools（各有个别点名） | Pro Tools（个别点名） | AI 配音（ElevenLabs、云厂商语音），Audition 降噪 |
| 字幕与多语言 | 剪映批量字幕（个别点名）；专门工具未查到 | 未查到 | 助理剪辑"嵌入字幕"，并用 AI 做转写与字幕 | 剪映、平台自带 |
| 审片与交付 | 未查到 | 未查到 | Frame.io（一位制片人自述） | 导出到剪映或本地 |
| 生成 | — | — | — | Seedance／即梦、可灵为主，另有 Vidu、Runway、Midjourney 等 |

### 2.4 直接回答：品质优秀的短剧会不会用 Adobe 工具做深入处理

- **会用，主要在两个环节。** 剪辑用 Premiere（正片岗 81% 点名，与达芬奇并列）；特效、合成、片头与字幕包装用 After Effects（39% 点名）。Photoshop 主要出现在海报和投放素材岗，Audition 偶见于声音处理。
- **最"深入"的那一步不是 Adobe。** 精品化最花功夫的调色，证据一边倒指向达芬奇；达芬奇同时能剪辑，一部分公司（九州文化、横店的承制方、海外四个具名项目）整条后期都在达芬奇里完成，不经过 Adobe。
- **是不是付费正版：没有直接证据。** 短剧公司的采购公告、Adobe 的维权报道、从业者说法均未查到。间接证据都指向"大多不是"：Adobe 在大陆不卖个人订阅，只通过经销商卖团队版和企业版；最后一版商业软件联盟调查里中国未授权软件比例是 66%（2017 年，全部电脑软件口径）；Adobe 自己在年报里写"我们持续因非法使用而损失收入"（见第 4.1 节）。
- **证据强度**：招聘层面为中；具体剧目和头部厂牌层面为零。结论的方向（Premiere 与 After Effects 在用、调色归达芬奇、AI 剧归剪映）可信，比例数字只能当作量级。

### 2.5 AI 短剧的流程

| 步骤 | 实际在用的工具 | Adobe 的位置 |
|---|---|---|
| 剧本、分镜、生图 | 豆包、Midjourney、Stable Diffusion、即梦等 | Photoshop 修图（少量点名） |
| 生成视频 | Seedance／即梦最多（火山引擎称头部公司"差不多都签了年框"；一家媒体称市占率 80%，口径不明），其次可灵、Vidu | Firefly 视频模型与 Firefly 里的第三方模型：在 56 条 AI 岗启事和 8 份课程大纲里出现 0 次 |
| 剪辑合成 | 酱油文化的五个环节是"剧本创作、AI 生图、AI 抽卡、剪辑、审核"；56 条 AI 岗里 50 条仍要求传统剪辑软件（Premiere 44、剪映 38、After Effects 29） | Premiere、After Effects 仍被点名 |
| 修复与放大 | "处理 AI 生成素材的瑕疵修复（口型不对、表情僵硬、穿帮等）""使用 Topaz Video AI 修复、RIFE 补帧" | Adobe 2026-09-23 完成收购 Topaz Labs（约 3.4 亿美元）[S7][S19] |
| 配音与口型 | 平台自带、ElevenLabs、云厂商语音 | Audition 个别点名 |
| 一站式工具 | 字节的小云雀短剧 Agent 从剧本做到"合成全集"，"导出到剪映，或者导出到本地"；剪映专业版可导入外部生成的短剧草稿继续精修；巨量引擎的流程图把配音、口型、剪辑、字幕、超分、插帧全部对应到自家工具 | 没有查到任何中文一站式工具导出 Premiere 工程或通用交换格式（这是没找到，不是证实没有） |

来源见 [S34][S59][S63]。

判断：AI 生成之后**仍然需要剪辑**，这一点证据充分；但需要的是"把几百个片段快速拼起来、加字幕配音"的轻剪辑，不是需要专业工具的重后期。在中国这一步的默认工具是与生成模型同属一家的剪映。Premiere 的"生成式延展"（Generative Extend，用 AI 把镜头延长几秒）等功能在这条流程里没有位置，而且在大陆本来就用不了（见第 4.1 节）。

## 3. Adobe 在视频工具里的位置与对手

**结论**：在专业和半专业剪辑里 Premiere 仍是用得最多的工具之一，After Effects 在动态图形与合成上没有同量级对手。在手机端和入门创作者里 Adobe 几乎没有份额。2025 年以来 Adobe 的动作集中在三处：免费的手机版 Premiere、把十多家第三方视频模型接进 Firefly、在 Premiere 里补调色。

### 3.1 Adobe 的视频产品与近两年的发布

| 时间 | 事件 | 来源 |
|---|---|---|
| FY25 Q2（2025 年 3～5 月） | Firefly 视频模型正式发布，可生成 4K 素材；Premiere 加入生成式延展；管理层在 2025-06-12 电话会上口头报价 Firefly 三档约 10、20、200 美元／月 | [S5] |
| 2025-09-30 | Premiere iPhone 版上线，免费，取代 Premiere Rush；只有生成式功能和额外存储收费 | [S17] |
| 2025-10-28（MAX 2025） | 与 YouTube 合作，在 Premiere 手机版里做"Create for YouTube Shorts"；Firefly 网页版视频剪辑器、生成配乐与语音；管理层称要"把 Premiere 手机版带给全球数百万 YouTuber" | [S8][S16] |
| 2025-12-18 | 与 Runway 签多年合作，Adobe 成为其首选的创意接口伙伴 | [S19] |
| 2026-01-20 | Premiere 加入对象遮罩等功能；Firefly 视频剪辑器公测 | [S15] |
| 2026-04-15（NAB 2026） | Premiere 的"Color Mode"调色环境公测（至 6 月仍是测试版）；Frame.io Drive；Firefly 视频剪辑器接入可灵 3.0；Firefly 内已有 30 多个模型 | [S18] |
| 2026-06（日期据第三方博客，只看到摘要） | Firefly 接入字节的 Seedance 2.0；Adobe 官方页面单列"关于中国模型的披露"（Seedance 2.0、可灵 3.0），这些模型只对个人用户开放 | [S10] |
| 2026-09-22 | Premiere 安卓版上线，免费；YouTube Shorts 模板功能"无需付费订阅" | [S13][S17] |
| 2026-09-23 | 完成收购 Topaz Labs（AI 画质增强与放大） | [S19] |
| 2026-11-10 至 11-12 | Adobe MAX 2026（尚未举行） | [S22] |

Premiere 手机版的下载量和月活：Adobe 没有单独披露，第三方数字未查到。可得的代理指标是美国区应用商店的累计评分数（2026-10-12）：Premiere 手机版 2.6 万条（上线一年），Instagram 的 Edits 9.3 万条（上线一年半），CapCut 112 万条 [S20]。评分数不等于下载量，只能看出量级差距。

### 3.2 份额证据

| 证据 | 数字 | 可信度 |
|---|---|---|
| 圣丹斯电影节入围影片（Adobe 每年 1 月公布，源自电影节的年度问卷） | 用 Adobe 创意应用的：2024 年 83%，2025 年"近 85%"，2026 年"近 85%"。用 Premiere 剪辑的：2023 年 67%，2024 年 57%，2025 年 60%；**2026 年不再给百分比，只说"超过 75 个项目"** | 厂商自述；独立电影是 Premiere 最强的领域 [S15] |
| 创作者调查（MIDiA，2024 年二季度） | 用 Premiere 的：初学者 24%，中级 47%，高级 58%。用 CapCut 的：26%、23%、8% | 中；样本量未披露 [S21] |
| 手机端活跃用户（Sensor Tower，2024-07） | CapCut 月活超 3 亿，占手机视频剪辑活跃用户 81%；Adobe 两款视频应用不到 CapCut 的 2% | 中 [S21] |
| 奥斯卡（Avid 自述，2026-03） | 最佳剪辑 5 部提名中 4 部用 Avid | 厂商自述，只看到摘要 [S50] |
| Adobe 自己的披露 | FY25 四季度"单品增长由 Photoshop 和 Lightroom 带动"，没有提 Premiere；年报竞争章节不点名任何对手；6 份电话会逐字稿里"中国"出现 0 次 | 事实 [S4][S6] |

### 3.3 对手

| 对手 | 体量 | 与短剧和创意视频的关系 | 来源 |
|---|---|---|---|
| 剪映与 CapCut（字节跳动） | 合计月活"已经超过 8 亿"，2024 年收入"正接近百亿元人民币"（界面，未具名信源）；美国活跃用户超 2,500 万 | 投流素材和 AI 剧的默认工具；2026-02 起剪映内置 Seedance 2.0，生成素材"自动同步至剪映草稿箱"。CapCut 在美国 2025-01 一度下架，2026-01 起纳入 TikTok 美国合资公司的保障范围，目前在美国区应用商店在架 | [S20][S51][S53][S54] |
| 达芬奇（Blackmagic） | 2019 年免费版用户超 200 万，之后未查到新数 | 调色标准；免费版可剪可调；Resolve 20 增加竖屏界面布局 | [S55] |
| Final Cut Pro（苹果） | 2018 年 250 万用户，之后未查到 | 2026-01 推出 Apple Creator Studio，六款专业应用每月 12.99 美元（中国 38 元） | [S56] |
| 平台自带工具 | Edits 做出的内容占 Reels 日播放近 10%；日均超 100 万个 YouTube 频道用自带 AI 工具 | 免费，离发布最近 | [S46][S47] |
| 面向创作者的轻量工具 | Canva 2025 年底 ARR 40 亿美元、月活 2.65 亿（视频只是其中一项功能，Pro 年费 180 美元）；Descript 2024 年底 ARR 约 5,500 万美元（第三方估计），Creator 档每月 24～35 美元 | 做口播、切片、营销短片，不做剧集后期；与 Adobe 的 Express 和 Premiere 手机版争同一批人 | [S22][S50] |
| AI 原生视频工具 | 可灵：2026 年二季度收入超 8.5 亿元，3 月年化约 5 亿美元，用户破 1 亿；Higgsfield 年化 10 亿美元、Runway 2 亿美元（第三方估计）；OpenAI 的 Sora 已于 2026 年停止服务 | 生成这一步的钱主要流向这些公司 | [S57] |

定价对比（美国标价，2026-10-12；剪映与苹果另列中国价）：

| 产品 | 价格 | 备注 |
|---|---|---|
| Premiere 单品 | 22.99 美元／月（年付），约 276 美元／年 | 只含 25 个生成积分 [S9][S11] |
| Creative Cloud Pro（全家桶） | 69.99 美元／月，约 840 美元／年 | 含 4,000 个高级生成积分 [S9][S11] |
| Firefly Standard／Pro／Pro Plus／Premium | 9.99／19.99／49.99／199.99 美元／月 | 2,000／4,000／10,000／50,000 积分 [S11] |
| Premiere 手机版 | 免费 | 生成功能按积分收费 [S13] |
| CapCut Pro | 19.99 美元／月，179.99 美元／年 | 2026-02 年费从约 77 美元涨上来 [S52] |
| 剪映 SVIP（中国） | 79 元／月，标价 758 元／年，连续包年 599 元 | 2024-06 前只有 25 元／月的 VIP [S52] |
| 达芬奇 Studio | 一次性 295 美元；另有免费版 | 历次大版本升级未收费 [S55] |
| Final Cut Pro | 一次性 299.99 美元（中国 1,998 元）；Creator Studio 129 美元／年（中国 380 元／年） | [S56] |

一个专业剪辑师用 Adobe 全家桶一年约 840 美元，用达芬奇是 0 或一次性 295 美元，用苹果套装一年 129 美元。在中国，剪映一年约 600 元，而 Adobe 根本没有面向个人的正价订阅。

## 4. Adobe 能不能把这些需求变成收入

### 4.1 中国大陆：用得不少，收不到钱

| 事项 | 现状 | 性质与来源 |
|---|---|---|
| 销售方式 | 中国站只有团队版和企业版，不标价，"查找经销商联系购买"；分销商是神州数码和伟仕佳杰。帮助文档写明"在中国使用的许可必须通过位于中国的 Adobe 授权经销商购买" | 事实（Adobe 官网，2026-10-12）[S14] |
| 个人订阅 | 2019-08 才推出唯一的个人计划（摄影计划，888 元／年，不含云存储）；据《南华早报》2023-11 报道，该计划 2023-12 起停售。**个人无法在大陆官方渠道订阅 Premiere 或全家桶** | 事实与报道（后者原文直接访问被拒，由检索子任务经存档快照读取，本文未能直接核对）[S14][S58] |
| 云服务 | "服务目前不包含在面向中国使用和部署的许可中"；Adobe Fonts 对中国注册账号不可用 | 事实（Adobe 帮助文档，2026-03-27、2023-07-11）[S14] |
| 生成式 AI | "Adobe Firefly 在俄罗斯、白俄罗斯和中国不可用"；Premiere 的生成式延展同样不可用 | 事实（Adobe 帮助文档，2026-05-13、2026-05-25）[S12] |
| Premiere 手机版 | 可下载国家名单里有香港、台湾，**没有中国大陆** | 事实（Adobe 帮助文档，2026-09-22）[S13] |
| 研发 | 2014 年关闭中国研发分支，裁员约 400 人，只留销售 | 事实（Fortune 2014-09-24）[S58] |
| 盗版 | 商业软件联盟最后一版调查：中国未授权软件安装比例 2017 年为 66%（2015 年 70%），全球 37%。之后没有更新。Adobe 年报："我们积极打击软件盗版，但仍持续因非法使用而损失收入" | 说法与事实；66% 是九年前的全部电脑软件口径，且只看到摘要 [S6][S58] |
| 中国收入 | **未披露**。FY25 亚太区收入 33.6 亿，占 14%（美国 125.3 亿，占 53%）；FY26 三季度亚太 9.3 亿，占 14%，同比 +10%。年报除美国外不单列任何国家；六份电话会逐字稿里"中国"出现 0 次 | 事实 [S1][S6][S7] |
| 近年维权 | 2012～2016 年有向企业发函和起诉的报道；2023～2026 年未查到 | [S58] |

结论：中国短剧行业用 Adobe 工具的那部分，绝大多数变不成 Adobe 的收入，原因有四层，一层比一层硬。个人买不到；公司要经经销商按年预付，小承制方没有动力；生成式功能和手机版不开放，连"按用量收费"的口子都没有；增量又主要是用剪映的 AI 剧。

**估计**（假设可改）：

- 会用到桌面剪辑软件的短剧与漫剧后期人员 15 万人（北大估计制作团队约 45 万人，本文假设其中后期与素材剪辑约三分之一）；
- 其中用 Adobe 工具的 50%（招聘出现率 79%～93%，打折是因为"接受"不等于"在用"）；
- 其中付费正版的 3%（纯假设，没有数据）；
- 团队版年费按 700 美元（约 5,000 元，官网不标价，纯假设）。
- 15 万 × 50% × 3% × 700 美元，约 **160 万美元**。把人数放大到 30 万、付费率放大到 10%、单价 800 美元，也只有 1,440 万美元。

### 4.2 海外短剧：按席位算是百万美元级

公式：年产部数 × 每部后期人年 × 周边剪辑倍数 × 每个全职岗位对应的人数 × 用 Adobe 的比例 × 年费。

| 参数 | 最可能 | 乐观 | 悲观 | 依据 |
|---|---|---|---|---|
| 中国以外本土实拍部数／年（2029 年） | 3,000 | 10,000 | 1,500 | 洛杉矶每月 30～40 部、温哥华同时 20 部、几家平台各每月 15～30 部，本文推算当前全球两三千部；AI 正在替代实拍 [S41][S42] |
| 每部后期人年 | 0.2 | 0.33 | 0.15 | 9 个人六周同时做 8 部，约 7 人周；五周、多名剪辑师并行，约 15 人周 [S61][S62] |
| 周边剪辑倍数（预告、投放素材、本地化） | 3 | 3 | 2 | 本文假设 |
| 每个全职岗位对应的人数（自由职业者兼职） | 1.5 | 1.5 | 1.5 | 本文假设 |
| 用 Adobe 的比例 | 60% | 70% | 50% | 核心岗位 6 条全写 Premiere，但也全写达芬奇 [S60] |
| 年费（美元） | 900 | 1,000 | 840 | 全家桶个人 840，团队更高 [S11] |
| **席位 ARR** | **约 150 万美元** | **约 1,040 万美元** | **约 30 万美元** | |

这些人里很多本来就订阅着 Adobe 做别的活，真正的新增更少。后期软件只是预算里的零头：一部 20 万美元的剧，后期总共约 2 万美元；三个人用六周，全家桶订阅摊下来约 300 美元（本文推算），占后期预算的 1%～2%，占总预算的千分之一二。

### 4.3 创作者与广告、电商视频：有用户、有用量，付费的那部分还很小

Adobe 披露过的指标（均为事实，来自电话会）：

| 指标 | FY25 Q4 | FY26 Q1 | FY26 Q2 | FY26 Q3 | 来源 |
|---|---|---|---|---|---|
| 创意 freemium 月活（Firefly、Express，以及 Premiere、Photoshop、Lightroom 的网页与手机版） | 超 7,000 万（+35%） | 超 8,000 万（+50%） | 超 9,000 万（+70%） | 超 1 亿（+70%） | [S1][S2][S3][S4] |
| 生成积分消耗 | 环比 3 倍，"视频消耗出现巨大拐点" | 环比 +45%，视频生成次数同比 8 倍多，音频 2 倍 | "由视频和音频带动" | "环比加速" | 同上 |
| Firefly 应用与积分包 ARR 环比 | — | +75% | 约 +50% | +40% | 同上 |
| Firefly 合计 ARR（应用、积分包、企业版） | — | 超 2.5 亿 | "接近 3 亿" | 未给合计 | [S2][S3] |
| AI-first ARR（AI 原生产品合计） | — | 同比 3 倍多 | 超 5 亿 | 超 6.5 亿（+150%） | [S1][S2][S3] |

读法：

- **估计**：合计 ARR 从 Q1 的 2.5 亿多涨到 Q2 的近 3 亿，一个季度约 +15%，而应用与积分包同期涨五成，说明后者基数很小。假设企业版每季增 5%，反推应用与积分包 ARR 在 Q1、Q2、Q3 约为 0.6 亿、0.9 亿、1.3 亿，Firefly 合计 Q3 末约 3.4 亿。企业版增速假设改成 10% 时，应用与积分包 Q3 约 0.8 亿。**面向创作者、与视频生成直接相关的付费 ARR 大约是 1 亿美元出头，占 Total ARR 的 0.5%。**
- AI-first ARR 一年增加约 3.9 亿美元（6.5 亿对一年前不超过 2.6 亿），而过去四个季度剔除 Semrush 的净新增 ARR 约 22.9 亿（275.0 − 4.8 − 275.0／1.112）。**AI 原生产品只占 ARR 的 2.4%，却贡献了净新增的约 17%。**
- 转化证据的另一面：Premiere 手机版、YouTube Shorts 模板都免费 [S13]；FY26 下半年公司主动把流量导向免费层并推迟提价，分析师估算代价约 5 亿美元 ARR；订阅毛利率 Q3 为 90.4%，同比降 0.8 个点 [S22]。视频生成是最耗算力的品类：同样一次生成，1080p 视频每秒耗 100 个积分，而标准图像生成不限量 [S9]。
- 广告与电商视频走的是企业通道（Firefly 企业版、GenStudio 内容生产方案）：GenStudio ARR 同比 +20%～25%，Firefly 企业版用量环比加速，但没有披露其中视频的占比 [S1][S2]。

### 4.4 生成式视频对 Adobe 是增量还是替代

| 方向 | 证据 |
|---|---|
| 增量 | 视频生成次数同比 8 倍、积分消耗由视频带动、Firefly 应用与积分包 ARR 连续三季高增长 [S1][S2][S3]；AI 剧岗位九成仍要求传统剪辑软件，Premiere 出现率 79% [S59]；修复、放大、补帧是生成之后的刚需，Adobe 已买下 Topaz [S19] |
| 替代或绕过 | 中国：Firefly 不可用，生成与剪辑被字节的 Seedance 加剪映一条龙包走，Adobe 的生成式功能出现 0 次 [S12][S63]。海外：Holywater 官方招聘板上的影像岗全是 AI 岗，没有传统剪辑岗 [S60]；AI 剧团队从 15 人减到 3～5 人，实拍剧组在减少 [S34][S36]。钱的去向：可灵一家年化约 5 亿美元，比 Firefly 合计 ARR 还大 [S57] |
| 价格 | **估计**：Firefly 每个积分约 0.004～0.005 美元。用 Firefly 里的可灵 3.0 生成 1080p 视频每秒 25 积分，约 6～7.5 美元／分钟；Seedance 2.0（720p，每秒 90 积分）约 22～27 美元／分钟；Adobe 自己的视频模型每秒 100 积分，约 24～30 美元／分钟 [S9][S10][S11]。一部 90 分钟的 AI 短剧按 3～5 倍废片率，经 Firefly 生成要花 1,600～1.35 万美元。中国漫剧的制作成本已低到每分钟 200～300 元（约 28～42 美元）[S34]。Adobe 是在转售别人的模型，价格没有优势，毛利还要分给模型方 |

判断：对 Adobe 是**小幅净增量**。生成这一步的大头被模型公司和字节拿走，Adobe 拿到的是"已经在用 Adobe 的人顺手在里面生成"的那一份，以及企业客户看重的商用安全与赔付。它带来积分加购，但也在压低"需要多少个专业剪辑席位"。

## 5. 量化与判断

### 5.1 基数

| 项 | 数字 | 性质 |
|---|---|---|
| Total ARR（FY26 Q3 末） | 275.0 亿美元（+11.2%，含 Semrush 约 4.8 亿） | 事实 [S1] |
| 过去四个季度净新增 ARR（剔除 Semrush） | 约 22.9 亿；FY26 全年有机约 21.4 亿 | 估计 [S22] |
| AI-first ARR | 超 6.5 亿（+150%） | 事实 [S1] |
| Firefly 应用与积分包 ARR | 约 1.3 亿（0.8～1.4 亿） | 估计，见 4.3 |
| 专业视频席位（Premiere、After Effects、Frame.io 为主因的订阅）ARR | 约 25 亿（18～36 亿） | **纯假设**：创意专业收入约 120 亿的 15%～30%；Adobe 不披露，也没有查到可靠的外部估计 |

### 5.2 三种情形（FY27～FY31，每年新增 ARR，亿美元）

| 来源 | 最可能 | 乐观 | 悲观 | 主要假设 |
|---|---|---|---|---|
| ① 短剧直接贡献：海外席位、中国正版席位、AI 短剧经 Firefly 消耗的积分 | 0.03 | 0.25 | 0 | 到 2029 年三项合计约 0.1 亿／0.75 亿／0.01 亿（海外席位见 4.2；中国见 4.1；积分按海外每年 5 万／10 万／3 万部 AI 剧 × 每部模型支出 5,000／5,000／3,000 美元 × 经 Firefly 的比例 3%／10%／0.5%） |
| ② 创作者的生成式视频：Firefly 应用与积分包、Premiere 手机版内购 | 0.95 | 3.7 | 0.3 | FY29 末该项 ARR 从 1.3 亿到 5.5～7 亿／20 亿／3 亿，增量的 60% 算作视频与音频带动 |
| ③ 专业视频席位 | 0.25 | 0.75 | −1.0 | 25 亿基数每年 +1%／+3%／−4%；美国剪辑师人数十年 +4%，对手更便宜 |
| ④ 企业的广告与电商视频生产 | 0.3 | 1.0 | 0.1 | 基数未披露，纯假设，可信度低 |
| **合计（每年）** | **约 1.5** | **约 5.7** | **约 −0.6** | |
| 三年累计（FY27～FY29） | 约 4.5（4～5.5） | 约 17 | 约 −1.8 | |
| 五年累计（FY27～FY31） | 约 7（6～9，后两年放缓） | 约 25～28 | 约 −3 | |
| 相当于 Total ARR 的 | 每年 0.5% | 每年 2.1% | 每年 −0.2% | 对 275 亿 |
| 相当于年净新增 ARR 的 | 约 7% | 约 26% | 约 −3% | 对 21～23 亿 |

三种情形各自对应的世界：

- **最可能**：AI 剧继续替代实拍，海外实拍量持平；Adobe 靠 1 亿多免费月活把一部分人转成 10～50 美元／月的 Firefly 订阅，环比增速从 40% 逐季降到个位数；专业席位靠涨价和企业协议微增。
- **乐观**：Firefly 成为创作者做 AI 视频的主要入口之一，三年做到 20 亿美元 ARR（相当于今天可灵的四倍）；海外短剧工业化并留在 Premiere 与 Frame.io 上；MAX 2026 之后 Premiere 手机版拿到千万级月活。
- **悲观**：生成与剪辑在字节系、平台自带工具和 AI 原生产品里闭环；模型降价让积分卖不上价；专业剪辑席位每年流失 4%。这就是已有评审熊市情景（创意专业收入每年萎缩 6%～8%）在视频这一块的样子。

### 5.3 对已有情景假设的判断

已有评审：基准情景收入增速 7.5% 逐年降到 3%（净新增 ARR 稳定在约 20 亿／年后回落）；熊市情景创意专业收入每年萎缩 6%～8% [S22]。

| 问题 | 判断 | 依据 |
|---|---|---|
| 短剧（含 AI 短剧） | **无关紧要** | 最可能情形下三年后约 0.1 亿美元，占 ARR 的 0.04%；乐观也只有 0.75 亿、0.3%。量最大的中国市场 Adobe 收不到钱，增量又是用剪映的 AI 剧 |
| 更广义的创意视频与生成式视频 | **已包含在基准里** | 基准要求每年约 20 亿净新增 ARR，而 AI 原生产品已经在贡献其中约 17%（一年 3.9 亿）。最可能情形的每年 1.5 亿是这块增长的延续，不是额外的一层 |
| 是否上调基准 | **不上调** | 要让收入增速比基准高 1 个点，需要每年多出约 2.75 亿美元 ARR，接近乐观情形的一半。目前支持乐观的只有环比增速，基数太小，且增速已经在 75%、50%、40% 地下降 |
| 是否影响熊市情景 | **不改路径与概率，但提供了一个旁证** | 短剧行业两年内从"实拍、多人后期"变成"AI 生成、三五个人在剪映里出片"，正是熊市机制（生成式 AI 让低端用户不再需要专业工具）的现实样本。它发生在 Adobe 本来就收不到钱的市场，所以不影响 Adobe 的数字；它说明这个机制在技术上是成立的 |

一句话：视频内容越来越多这件事，过去十年没有按比例变成专业剪辑席位，今后也不会；它能变成 Adobe 收入的部分是生成积分，这部分真实、增长快、体量小，已经在基准里。

## 6. 可跟踪的指标与门槛

| # | 指标 | 现值 | 支持"视频在转化为收入"的门槛 | 相反信号 | 时点 |
|---|---|---|---|---|---|
| 1 | Firefly ARR | 合计 Q2 末"接近 3 亿"；应用与积分包环比 +75%、+50%、+40% | FY26 Q4 披露的合计不低于 4 亿，应用与积分包环比不低于 25%；FY27 Q2 合计不低于 5.5 亿 | 环比跌破 15%，或公司不再披露这一项 | 2026 年 12 月中旬财报；2027 年 6 月财报 |
| 2 | AI-first ARR | 超 6.5 亿（+150%） | FY26 Q4 不低于 8 亿；FY27 Q2 不低于 10 亿（与已有评审第 4 条证伪条件一致） | FY27 Q2 仍低于 10 亿 | 同上 |
| 3 | 创意 freemium 月活与 Premiere 手机版 | 月活超 1 亿（+70%）；手机版美国区评分 2.6 万条 | FY27 Q2 月活不低于 1.3 亿；Adobe 在 MAX 2026 或财报上单独披露 Premiere 手机版月活且达到千万级；美国区评分数到 2027-06 不低于 6 万条 | 安卓版上线后月活增速回落到 +40% 以下；仍不披露手机版数字 | 2026-11-10 至 11-12 的 MAX；2027 年 6 月 |
| 4 | 专业份额：圣丹斯 Premiere 占比 | 2024 年 57%，2025 年 60%，2026 年不给百分比 | 2027 年 1 月重新给出且不低于 55% | 低于 50%，或连续第二年不给百分比 | 2027 年 1 月下旬 |
| 5 | 订阅毛利率（视频生成最耗算力） | Q3 为 90.4%，同比 −0.8 个点 | 保持在 89.5% 以上，同时第 1 项达标 | 跌破 89.5% 而 Firefly ARR 增速放缓，说明用量没有换来收入 | 每季财报 |

短剧这条线不需要单独跟踪。如果想留一个观察点：Firefly 是否对中国大陆开放（现在不开放），以及 Adobe 是否在 MAX 2026 上第一次点名短剧客户或发布竖屏短剧功能。两者都不发生，本文结论不变。

## 7. 最不确定的地方与未能核实的事项

最不确定的两点：

1. **专业视频席位的基数（本文假设 25 亿美元）和它的方向。** Adobe 不披露分产品收入。悲观情形的 −1 亿／年和乐观情形的 +0.75 亿／年都挂在这个假设上。圣丹斯的 Premiere 占比从 67% 降到 57% 再回到 60%，然后 Adobe 不再给百分比，这是唯一的时间序列，而且是厂商自述。
2. **Firefly 应用与积分包 ARR 的绝对值（本文推算约 1.3 亿）和增速能维持多久。** 推算依赖"企业版每季增 5%"的假设。如果真实值是 2 亿并保持环比 30% 以上，乐观情形的概率就要上调。12 月财报是检验点。

未能核实的事项：

- 具体精品剧目（《盛夏芬德拉》《家里家外》等）和头部厂牌、长视频平台自制短剧的后期公司与所用软件：检索后未查到。搜索工具对公众号、知乎、B 站的从业者内容几乎无效。
- 中国短剧公司的 Adobe 正版率、采购或维权信息：未查到。4.1 节的 3% 是纯假设。
- 中国后期与剪辑从业人数：没有机构单列。
- 各平台的技术交付规范：未查到。
- Adobe 中国团队版与企业版的人民币价格：官网不标价，未查到。
- Premiere 手机版的下载量与月活；Frame.io 的用户数：Adobe 未披露，第三方未查到。
- 海外本土短剧全行业年产量与后期从业人数：没有权威统计，4.2 节的部数是本文推算。
- 《南华早报》关于中国摄影计划停售的报道、商业软件联盟 2018 年报告原文：原站访问被拒，前者由检索子任务经存档快照读取，后者只有摘要与二手印证。
- 因检索额度用尽没能检索的：Adobe 是否对中国企业或高校停服、淘宝低价授权与破解版的比例、商业软件联盟 2018 年之后的更新、剪映专业版桌面端用户量、Blackmagic 中文公众号里的内地短剧案例、多家 AI 视频工具的现行定价。
- 行业数据内部的矛盾（并列给出，未能裁决）：协会称 2026 年上半年 AI 剧占 74%，广电总局称前 8 个月占九成以上；DataEye 对 2026 年 AI 剧漫剧规模 3 月预测 240 亿元、7 月改为 400 亿元；Sensor Tower 与 DataEye 的海外内购口径相差约三成。

## 来源

Adobe 一手资料：

- [S1] Adobe FY26 Q3 电话会纪要（2026-09-10）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q3fy26-transcript.pdf
- [S2] Adobe FY26 Q2 电话会纪要（2026-06-11）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q2fy26-transcript.pdf
- [S3] Adobe FY26 Q1 电话会纪要（2026-03-12）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q1fy26-transcript.pdf
- [S4] Adobe FY25 Q4 电话会纪要（2025-12-10）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q4fy25-transcript.pdf
- [S5] Adobe FY25 Q3（2025-09-11）与 Q2（2025-06-12）电话会纪要：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q3fy25-transcript.pdf ；https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q2fy25-transcript.pdf
- [S6] Adobe FY25 10-K（截至 2025-11-28；地区收入、竞争、盗版风险因素）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000003/adbe-20251128.htm
- [S7] Adobe 10-Q（截至 2026-08-28，2026-09-22 提交；地区收入、Topaz 对价）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm
- [S8] Adobe MAX 2025 投资者演示（2025-10-28）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/a55tgresq435t.pdf
- [S9] Adobe 帮助文档，生成积分常见问题（更新 2026-09-30；各功能每秒积分、各套餐积分）：https://helpx.adobe.com/firefly/get-set-up/learn-the-basics/generative-credits-faq.html
- [S10] Adobe 帮助文档，Adobe 产品中的伙伴模型（更新 2026-10-09；视频模型清单、每秒积分、中国模型披露）：https://helpx.adobe.com/creative-cloud/apps/generative-ai/non-adobe-models-in-adobe-products.html ；Seedance 2.0 接入日期（第三方博客，2026-06-25，只看到摘要）https://design-offset.com/en/20260625-adobe-firefly-bytedance-seedance-2-0/
- [S11] Adobe 套餐页（2026-10-12 取数）：https://www.adobe.com/products/firefly/plans.html ；https://www.adobe.com/creativecloud/plans.html ；Firefly 四档美元价另见价格追踪 https://design-offset.com/en/20260319-adobe-firefly-pro-plus/
- [S12] Adobe 帮助文档，Firefly 常见问题（更新 2026-05-13）：https://helpx.adobe.com/firefly/get-set-up/learn-the-basics/adobe-firefly-faq.html ；生成式延展常见问题（更新 2026-05-25）：https://helpx.adobe.com/premiere/desktop/edit-projects/edit-with-generative-ai/generative-extend-faq.html
- [S13] Adobe 帮助文档，Premiere 手机版常见问题（更新 2026-10-08）：https://helpx.adobe.com/premiere/mobile/get-started/common-questions.html ；可用国家（更新 2026-09-22）：https://helpx.adobe.com/premiere/mobile/get-started/availability-by-country.html ；YouTube 模板常见问题（更新 2026-09-22）：https://helpx.adobe.com/premiere/mobile/use-premiere-with-other-apps/youtube-integration-faq.html
- [S14] Adobe 中国：计划页（2026-10-12 取数）https://www.adobe.com/cn/creativecloud/plans.html ；中国版常见问题（更新 2022-03-15）https://helpx.adobe.com/cn/creative-cloud/faq-china.html ；VIP in China（更新 2026-03-27）https://helpx.adobe.com/business/teams/vip/get-started/vip-in-china.html ；Adobe Fonts 对中国账号不可用（更新 2023-07-11）https://helpx.adobe.com/fonts/web/font-licensing/adobe-fonts-unavailable.html ；分销商 https://www.adobe.com/cn/creativecloud/roc/information/resellers-disti.html ；反盗版页 https://www.adobe.com/cn/aboutadobe/antipiracy/
- [S15] 圣丹斯：Adobe 新闻稿（2026-01-20）https://news.adobe.com/news/2026/01/sundance-filmmakers-choose-adobe ；Adobe 博客（2026-01-20）https://blog.adobe.com/en/publish/2026/01/20/sundance-film-festival-2026-creativity-community-power-storytelling ；Adobe 新闻稿（2025-01-22）https://news.adobe.com/news/2025/1/adobe-delivers-new-innovations-and-ai-tools-for-video-pros-and-invests-6-million-in-filmmaker-community ；RedShark（2024-01-17）https://redsharknews.com/what-editing-software-was-used-for-the-majority-of-the-2024-sundance-film-festival-program
- [S16] Adobe 与 YouTube 合作新闻稿（2025-10-28）：https://news.adobe.com/news/2025/10/adobe-max-2025-youtube
- [S17] Premiere iPhone 版（TechCrunch，2025-09-30）：https://techcrunch.com/2025/09/30/adobes-video-editing-app-premiere-arrives-on-iphones ；安卓版（Android Authority，2026-09-22，只看到搜索摘要；上线事实另由 [S13] 证实）：https://androidauthority.com/adobe-premiere-android-launch-official-3713985
- [S18] NAB 2026：No Film School（2026-04-15）https://nofilmschool.com/adobe-updates-nab-2026 ；Adobe 社区公告（2026-06-24）https://community.adobe.com/announcements-727/adobe-since-nab-2026-what-editors-should-know-1629489
- [S19] Adobe 与 Runway 合作（2025-12-18）：https://news.adobe.com/news/2025/12/adobe-and-runway-partner ；收购 Topaz Labs（2026-06-25）https://news.adobe.com/news/2026/06/adobe-to-acquire-topaz-labs ；交割（PetaPixel，2026-09-23）https://petapixel.com/2026/09/23/adobe-completes-acquisition-of-topaz-labs/
- [S20] 苹果应用商店搜索接口，美国区评分数（2026-10-12 取数）：https://itunes.apple.com/search?term=adobe+premiere&entity=software&country=us （CapCut、Edits 同接口）
- [S21] MIDiA Research，CapCut 挑战 Premiere（2024-08-15）：https://www.midiaresearch.com/blog/how-capcut-is-challenging-adobe-premiere-pros-dominance-of-the-video-editing-market ；ChannelNews 转述 Sensor Tower 与彭博（2024-07-30）：https://www.channelnews.com.au/bytedances-capcut-dominates-mobile-video-editing-market/
- [S22] 已有评审：[2026-10-12 复核](ADBE_Adobe.md)；[Canva 专项](ADBE_vs_Canva.md)；[Figma 专项](ADBE_vs_Figma.md)；[2026-10-07 独立估值](../../exp_independent_us3_20261007/companies/ADBE_Adobe.md)

中国微短剧与 AI 漫剧：

- [S23] 广电总局网络视听司司长王小亮在国新办发布会的发言（新华网，2026-09-18）：https://www.news.cn/tech/20260918/1fc21cfba8334e9bba130af8eb50b565/c.html ；2025 年全年上线 3.3 万部（光明网，2026-02-11）：https://www.yzwb.net/news/yw/202602/t20260211_321197.html
- [S24] 协会《微短剧行业发展白皮书（2024）》（第一财经，2024-11-06）：https://www.yicai.com/news/102346009.html ；《中国网络视听发展研究报告（2026）》（上海证券报，2026-04-17）https://paper.cnstock.com/html/2026-04/17/content_2200985.htm ；（中国作家网转文汇报，2026-04-16）https://www.chinawriter.com.cn/n1/2026/0416/c404003-40702348.html ；备案数（人民日报海外版，2025-01-13）https://paper.people.com.cn/rmrbhwb/pc/content/202501/13/content_30051407.html ；2024 年电影票房（前瞻，2025-06-20）https://www.qianzhan.com/analyst/detail/220/250619-335b3ca0.html
- [S25] CNNIC 第 55 次（2025-01-17）https://cnnic.cn/NMediaFile/2025/0117/MAIN1737100758200NNZ5AVJ3C1.pdf ；第 57 次（2026-03-04）https://www.cnnic.cn/NMediaFile/2026/0304/MAIN1772588317069TUXN3827X8.pdf
- [S26] DataEye 国内：2025 年中（澎湃号，2025-07-09）https://m.thepaper.cn/newsDetail_forward_31132177 ；2026 年上半年真人微短剧与全年预估（36 氪，2026-08-04）https://www.36kr.com/p/3924831083435650 ；艾媒报告页 https://report.iimedia.cn/repo160-0 ；2025 年电影票房与年终口径（界面，2026-01-21）https://www.jiemian.com/article/13912771.html
- [S27] DataEye《2026 上半年国内 AI 剧漫剧数据报告》（2026-07-27）：https://pdf.dfcfw.com/pdf/H3_AP202607301827488941_1.pdf
- [S28] 北京大学国家发展研究院微短剧就业报告（2025-12-30 发布）：https://nsd.pku.edu.cn/docs/2026-02/48accc85b74f4939b8f4c4b612e610ec.pdf
- [S29] 协会《2025 微短剧行业生态洞察报告》（澎湃号，2025-12-06）：https://m.thepaper.cn/newsDetail_forward_32113842 ；2024 年 64.7 万个就业机会（中证网，2025-11-05）：https://cs.com.cn/cj2020/202511/t20251105_6521613.html
- [S30] QuestMobile《2026 年短剧营销行业报告》（IT 之家，2026-07-29）：https://www.ithome.com/0/983/018.htm ；红果月活与日活（虎嗅，2026-09-30）https://www.huxiu.com/article/4894940.html ；（华尔街见闻，2026-09-11）https://wallstreetcn.com/articles/3781574 ；（界面）https://m.jiemian.com/article/15072049.html ；2025-12 月活（澎湃号，2026-04-09）https://m.thepaper.cn/newsDetail_forward_32928828
- [S31] 成本、周期与横店：虎嗅转 Vista 看天下（2026-03-14）https://www.huxiu.com/article/4842127.html ；虎嗅转新浪财经（2026-06-04）https://www.huxiu.com/article/4864555.html ；36 氪转号外工作室（2025-06-17）https://www.36kr.com/p/3339987276113414 ；界面转伯虎财经（2026-01-21）https://www.jiemian.com/article/13912771.html ；界面转毒眸（2026-01-07）https://www.jiemian.com/article/13853577.html ；极目新闻（2026-07-24）https://www.ctdsb.net/c1716_202607/2809929.html ；虎嗅（2025-09-25）https://m.huxiu.com/article/4784894.html
- [S32] 《微短剧发展管理办法》（广电总局令第 16 号，2026-07-31）：https://www.nrta.gov.cn/art/2026/7/31/art_1588_73827.html ；分类分层审核（新华网，2025-02-05）https://www.news.cn/politics/20250205/3fbf8abbfa344641b01f799ae42a6318/c.html ；AI 动画微短剧备案（21 世纪经济报道，2026-04-10）https://www.sfccn.com/2026/4-10/yMMDE0NDlfMjEyODAyMg.html
- [S33] 平台扶持：IT 之家（2026-05-14）https://www.ithome.com/0/950/472.htm ；界面（2026-05）https://m.jiemian.com/article/14416061.html ；科技日报（2026-04-18）https://www.stdaily.com/web/gdxw/2026-04/18/content_504507.html ；取消保底（虎嗅转新浪财经，2026-05-23）https://www.huxiu.com/article/4860854.html
- [S34] AI 剧成本与团队：第一财经（2026-03-13）https://www.yicai.com/news/103084978.html ；（2026-03-10）https://www.yicai.com/news/103078817.html ；新民周刊（2026-04-13）https://img1.xinmin.cn/xmzk/2026-04-13/430413.pdf ；海西晨报（2026-04-13）https://hxdb.fjdaily.com/pc/att/202604/13/c5306fce-5b1f-49a1-ab03-71565f363052.pdf ；新华每日电讯（2026-04-29）https://www.news.cn/politics/20260429/b541e4e3478c4a43916c4777eb9b8b80/c.html ；中泰证券研报口径（虎嗅转海克财经，2026-09-30）https://www.huxiu.com/article/4894940.html
- [S35] 协会 2026 年一季度上线量与播放占比（中国经济网，2026-07-18）：https://news.10jqka.com.cn/20260718/c678267840.shtml
- [S36] 九州文化（虎嗅转最话，2026-06-01）：https://www.huxiu.com/article/4863444.html ；（新京报，2026-08-11）https://www.bjnews.com.cn/detail/1786438144169364.html ；上市公司半年报汇总（中新网，2026-09-03）https://www.chinanews.com.cn/cul/2026/09-03/10689528.shtml

出海与海外本土短剧：

- [S37] Sensor Tower《State of Short Drama Apps 2026》（2026-06）：https://sensortower.com/blog/state-of-short-drama-apps-2026-report ；2025 版（2025-07）https://sensortower.com/blog/state-of-short-drama-apps-2025 ；2025 全年数（Marketing Dive 转述，2026-02-20）https://www.marketingdive.com/news/microdrama-apps-stand-on-mobile-heres-what-the-numbers-say/812610
- [S38] DataEye 海外：2025 全年（澎湃号，2026-01-22）https://m.thepaper.cn/newsDetail_forward_32432287 ；2026 上半年（澎湃号，2026-08-03）https://m.thepaper.cn/newsDetail_forward_33708735 ；2026-08（36Kr 欧洲站，2026-09-18）https://eu.36kr.com/en/p/3987140189378434
- [S39] Media Partners Asia（Screen Daily，2026-08-06）：https://www.screendaily.com/news/microdrama-revenue-outside-china-to-hit-36bn-in-2026-says-report/5219165.article ；（Indiantelevision，2026-08-06）https://indiantelevision.com/iworld/reelshort-set-to-cross-1-bn-as-micro-drama-market-gathers-pace/ ；Omdia（Advanced Television，2026-05-29）https://www.advanced-television.com/2026/05/29/study-uk-emerges-as-europes-leading-microdrama-market/
- [S40] 中文在线 2025 年年度报告（2026-04-23，枫叶互动财务信息在第 202～203 页）：https://static.cninfo.com.cn/finalpage/2026-04-23/1225157276.PDF ；2026 年半年度报告（2026-08-26）：http://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?stockid=300364&id=12538177
- [S41] 美国本土制作：TheWrap（2024-10-18）https://thewrap.com/reelshort-growth-model-short-form-content-profitable ；（2025-10-21）https://www.thewrap.com/vertical-short-dramas-industry-explained-8-billion-business/ ；LAist（2025-07-10）https://laist.com/news/los-angeles-activities/how-vertical-dramas-are-reshaping-hollywoods-job-market ；C21Media（2025-10-30）https://www.c21media.net/department/c21investigates/microdrama-under-the-microscope/ ；Marketplace（2026-05-18）https://www.marketplace.org/story/2026/05/18/vertical-dramas-put-film-industry-professionals-back-to-work ；路透（Interaksyon 转载，2026-08-19）https://interaksyon.philstar.com/hobbies-interests/2026/08/19/317988/microdramas-boom-in-a-shrinking-hollywood-as-studios-chase-a-tiktok-audience/ ；Real Reel（2026-04-18）https://www.real-reel.com/vertical-drama-production-budget-la/
- [S42] 海外 AI 短剧：36 氪转 DataEye（2026-07-29）https://www.36kr.com/p/3916490999142280 ；澎湃号（2026-06-19）https://m.thepaper.cn/newsDetail_forward_33409546 ；虎嗅转扬帆出海（2026-10-05）https://www.huxiu.com/article/4895398.html ；昆仑万维（白鲸出海，2026-08-21）https://www.baijing.cn/article/56438
- [S43] FilmLA 季报（2026-04-28）：https://filmla.com/wp-content/uploads/FilmLA-News-Release_4.28.26-ResearchUpdate-q1-2026.pdf ；二季度（TheWrap，2026-07-23）https://www.thewrap.com/creative-content/movies/filmla-production-decline-q2-2026/

更广义的创意视频：

- [S44] 美国劳工统计局《职业展望手册》，剪辑师与摄像师（更新 2026-08-27）：https://www.bls.gov/ooh/media-and-communication/film-and-video-editors-and-camera-operators.htm ；行业就业序列（数据至 2026-09）https://api.bls.gov/publicAPI/v2/timeseries/data/CES5051200001
- [S45] 高盛，创作者经济（2023-04-19）：https://www.goldmansachs.com/insights/articles/the-creator-economy-could-approach-half-a-trillion-dollars-by-2027 ；IAB 创作者广告支出（2025-11-20）https://www.iab.com/insights/2025-creator-economy-ad-spend-strategy-report/
- [S46] YouTube 首席执行官年度信（2026-01-21）：https://blog.youtube/inside-youtube/the-future-of-youtube-2026/ ；Made on YouTube 2025（2025-09-16）https://blog.youtube/news-and-events/made-on-youtube-2025/
- [S47] Meta 2025 年四季度电话会纪要（2026-01-28）：https://s21.q4cdn.com/399680738/files/doc_financials/2025/q4/META-Q4-2025-Earnings-Call-Transcript.pdf
- [S48] IAB 数字视频广告：2025 报告（2025-07-15）https://www.iab.com/insights/video-ad-spend-report-2025/ ；2026 预测（2026-05-05）https://www.iab.com/news/u-s-digital-video-ad-spend-to-surpass-80b-in-2026/ ；生成式 AI 使用（2026-07-14）https://www.iab.com/news/business-outcomes-are-just-the-beginning/
- [S49] Wistia《2026 State of Video》（HubSpot 转述，2026-04-22 更新）：https://blog.hubspot.com/marketing/state-of-video-marketing-new-data
- [S50] 其它工具：Avid 奥斯卡统计新闻稿（2026-03-19，只看到摘要）https://www.avid.com/press-room/2026/03/one-battle-after-another-and-f1-among-majority-of-oscar-wins-created-using-avid ；Canva 与 Descript 的 ARR（Sacra 估计，页面无日期）https://sacra.com/c/canva/ ；https://sacra.com/c/descript/ ；Canva Pro 年费（PricingSaaS，2026-07-28）https://pricingsaas.com/companies/canva/diffs/2026D209 ；Descript 定价页（2026-10-12 取数）https://www.descript.com/pricing

对手与中国销售环境：

- [S51] 剪映与 CapCut 的用户和收入：界面新闻（2024-12-11）https://m.jiemian.com/article/12108171.html ；Sensor Tower 博客（2026-01）https://sensortower.com/blog/2025-q4-unified-top-5-photo-and-video-revenue-us-615c8a30ad269d38a8b6acd0
- [S52] 定价：CapCut 官网资源页（2026-09-23）https://www.capcut.com/resource/capcut-standard-vs-pro ；Newsweek（2026-02-17）https://newsweek.com/app-used-millions-nearly-doubles-subscription-price-overnight-11535999 ；剪映 SVIP（IT 之家，2025-12-27、2026-06-09）https://www.ithome.com/0/908/477.htm ；https://www.ithome.com/0/962/031.htm ；光锥智能（澎湃号，2025-11-05）https://m.thepaper.cn/newsDetail_forward_31881745
- [S53] CapCut 美国：TikTok 美国合资公司公告（2026-01-23）https://newsroom.tiktok.com/announcement-from-the-new-tiktok-usds-joint-venture-llc?lang=en ；Yahoo News（2025-01-21）https://www.yahoo.com/news/tiktok-sister-app-returns-us-174635954.html
- [S54] 剪映接入 Seedance 2.0：HK01（2026-02-14）https://global.hk01.com/数码生活/60322126/剪映接入字节ai影片模型seedance-2-0-网民惊称-效果媲美荷里活 ；DoNews（2026-03-05）https://www.donews.com/news/detail/4/6453862.html ；剪映专业版升级（快科技，2026-06-10）https://finance.sina.com.cn/tech/roll/2026-06-10/doc-iniaxkrn5911027.shtml
- [S55] 达芬奇：产品页（2026-10-12 取数）https://www.blackmagicdesign.com/products/davinciresolve ；RedShark（2026-04-14）https://www.redsharknews.com/davinci-resolve-studio-free-updates-grant-petty-nab-2026 ；Resolve 20 新闻稿（2025-04-04）https://www.blackmagicdesign.com/media/partial/release/20250404-02 ；用户数（维基百科转引 2019 年报道）https://en.wikipedia.org/wiki/DaVinci_Resolve
- [S56] 苹果 Creator Studio（2026-01-13）：https://www.apple.com/newsroom/2026/01/introducing-apple-creator-studio-an-inspiring-collection-of-creative-apps/ ；中国价格（IT 之家，2026-01-28）https://www.ithome.com/0/917/337.htm ；Final Cut Pro 2018 年用户数（维基百科转引苹果）https://en.wikipedia.org/wiki/Final_Cut_Pro
- [S57] AI 原生工具：可灵季度收入（财联社，2026-03-26）https://finance.eastmoney.com/a/202603253684458834.html ；（华尔街见闻，2026-05-27、2026-08-19）https://wallstreetcn.com/articles/3773231 ；https://wallstreetcn.com/articles/3779792 ；Runway 与 Higgsfield（Sacra 估计，页面无日期）https://sacra.com/c/runway/ ；https://sacra.com/c/higgsfield/ ；Sora 停止服务（Engadget，2026-03-24）https://engadget.com/ai/openai-is-shutting-down-its-sora-video-generation-app-211023358.html
- [S58] 中国销售与盗版：《南华早报》（2023-11-20，经存档快照）https://www.scmp.com/tech/tech-trends/article/3242208/adobe-stop-selling-china-photoshop-software-bundle-deal-after-business-assessment ；爱范儿（2019-08-22）https://www.ifanr.com/1251062 ；Fortune（2014-09-24）https://fortune.com/2014/09/24/adobe-shuts-down-china-rd-amid-worsening-business-environment ；商业软件联盟 2018 年调查（只看到摘要）https://www.bsa.org/news-events/news/bsa-survey-unlicensed-software-use-still-high-globally-despite-costly-cybersecurity-threats-0 ；二手印证（Mondaq，2018-07-24）https://www.mondaq.com/china/trademark/721630/ ；历史维权（爱范儿，2016-09-21）https://www.ifanr.com/720629 ；Adobe 社区用户与回复（2022-07-06、2026-03-31）https://community.adobe.com/questions-617/adobe-for-china-users-561588 ；https://community.adobe.com/questions-729/issues-regarding-the-use-of-adobe-in-china-1555842

工具证据：

- [S59] 中国招聘样本 124 条（2026-10-12 抓取）。文中引用的原文：巨豹互娱 https://www.liepin.com/job/1983376665.shtml ；麦芽传媒 https://www.liepin.com/job/1976368653.shtml ；杭州云帧 https://www.liepin.com/job/1983250793.shtml ；九州文化 https://www.liepin.com/job/1974103377.shtml ；刚刚好影视 https://www.liepin.com/job/1976525053.shtml ；https://www.liepin.com/job/1975482571.shtml ；映客系 https://www.liepin.com/job/1964265249.shtml ；杭州炼金术影视 https://www.liepin.com/job/1985097305.shtml ；武汉像素跃动 https://www.liepin.com/job/1985942619.shtml ；巨准互娱 https://www.liepin.com/job/1983202947.shtml ；深圳蓝核像素 https://www.liepin.com/job/1984279467.shtml ；AI 短剧剪辑（猎头代招）https://www.liepin.com/a/80236727.shtml 。其余启事的地址格式相同，完整清单保存在取证记录里，未随本文附上
- [S60] 海外招聘样本：DramaBox 助理剪辑（2026-03-16）https://www.nywift.org/jobs/view/4BPZk ；ReelShort 纽约剪辑（2026-03-24）https://www.nywift.org/jobs/view/jGyRa ；枫叶互动双语剪辑（2025-11-07）https://www.hollylist.com/jobs/8L3dgh5q3dvxvzypv ；DramaBox 主剪（2025-07-07）https://www.hollylist.com/jobs/jTB8dzXygLEt6hund ；中文在线海外（2024-08-26）https://hollylist.com/jobs/kHRh5KHERtzskup6R ；Holywater 剪辑 https://www.netinfluencer.com/jobs/video-editor-film-editor-holywater-at-genesis/ ；Holywater 官方招聘板（2026-10-12）https://jobs.ashbyhq.com/holywater
- [S61] 海外幕后：postPerspective，Super Punchy（2026-03-31）https://postperspective.com/vertical-media-studio-super-punchy-opens-intros-first-micro-drama/ ；美国制片人工会《Produced By》2026 年 6～7 月刊 https://producersguild.org/wp-content/uploads/2026/05/Tool-Kit-Elizabeth-Dell.pdf ；Media Services 博客（2026-06-25）https://www.mediaservices.com/blog/on-the-frontier-of-vertical-microdramas-lessons-from-nancy-pop-and-james-barker/
- [S62] Blackmagic 新闻稿：Stargate Studios 哥伦比亚（2026-05-28）https://www.blackmagicdesign.com/cn/media/release/20260528-01 ；《Playback》（2026-06-12）https://www.blackmagicdesign.com/cn/media/release/20260612-01 ；《Beneath Crimson Sails》（2026-06-17）https://www.blackmagicdesign.com/cn/media/release/20260617-01 ；《Vultures》（2026-08-24）https://www.blackmagicdesign.com/cn/media/release/20260824-01 ；UPSIDE（2025-08-11）https://www.blackmagicdesign.com/cn/media/release/20250811-01
- [S63] AI 短剧流程：国金证券研报（2026-06-13）https://pdf.dfcfw.com/pdf/H3_AP202606141823549289_1.pdf ；东吴证券研报（2025-10-24）https://pdf.dfcfw.com/pdf/H3_AP202510241768351710_1.pdf ；小云雀（科技日报，2026-03-20）https://www.stdaily.com/web/gdxw/2026-03/20/content_488925.html ；（智东西，2026-05-29）https://news.qq.com/rain/a/20260529A02Z3W00 ；Seedance 市占率说法（Tech 星球，2026-06-22）https://m.jiemian.com/article/14620825.html
- [S64] 培训大纲样本：站酷高高手 https://www.gogoup.com/course/GMzcyNw== ；https://www.gogoup.com/course/GMzczOA== ；慕课网 https://coding.imooc.com/class/1014.html ；深圳技术大学（澎湃，2026-09-26）https://m.thepaper.cn/newsDetail_forward_34148340 ；内蒙古电子信息职业技术学院培养方案（2025）https://www.imeic.edu.cn/__local/5/C8/FC/C87D1ED5E1FB2E19ECF0B5C9FF4_C4529C05_AD558.pdf ；机构软文两篇 https://m.tech.china.com/redian/2026/0518/052026_1871860.html ；https://m.tech.china.com/hea/articles/20260526/202605261878667.html
- [S65] Adobe 官方博客文章索引（2026-10-12 取数）：https://blog.adobe.com/en/query-index.json ；Frame.io 博客与客户案例页 https://blog.frame.io/?s=microdrama ；https://frame.io/customers
