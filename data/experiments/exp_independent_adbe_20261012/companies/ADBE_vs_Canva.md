# Canva 与 Adobe 的竞争关系及对 Adobe 的影响（2026-10-12）

```
一句话结论：Canva 已经拿走了 Adobe 本可以拥有的"非设计师做设计"市场（约 40 亿美元 ARR），但它自己也被聊天式生成和推理成本打慢了；它对 Adobe 现有收入的威胁是慢性的（压住提价、截走新用户、挤压企业里的非设计席位），已有评审的熊／基准情景已经包含，不需要因 Canva 单独调概率。
① 量级：Canva 2025 年底 ARR 40 亿美元（公司说法），约为 Adobe 总 ARR 的 16%；2025 年 ARR 增量约 11.4 亿，相当于 Adobe 净新增 ARR 的 44%。
② Canva 在减速：2026 年二季度收入 9.22 亿美元（+25.2%），全年增速预期从 30% 下调到 20%，原因是 AI 推理成本超支和部分用户转去 ChatGPT；估值被下调 17%～29%，上市推到 2027 年或更晚。
③ Affinity 免费 11 个月，下载约 700 万次，首月之后降到每月约 40 万次；没有查到可归因于它的 Adobe 订阅流失或降价，Adobe 只是暂停了提价。
④ Adobe 的应对集中在三处：Express 四次重做并接入 ChatGPT／Claude／Gemini、Firefly 聚合第三方模型、2026 年 6 月转向 freemium 并推迟提价；代价是下半年约 5 亿美元 ARR、Q3 净新增 ARR 同比 −37%、订阅毛利率降 0.8 个点。
⑤ 没有应对或无效：对"专业工具免费"没有价格回应；Express 的 AI 助手发布近一年仍是 beta，团队、企业、教育账户用不了；Express 的付费数据从未披露。
⑥ 坏情形下（Affinity 追平加企业席位被挤），到 FY30 Adobe 收入比基准路径少约 20～29 亿美元（6%～8%），约为基准与熊市差距的三成；Canva 是熊市情景的放大器，不是触发器。
⑦ 最该盯的是 Adobe 的定价行为和 FY27 指引，不是 Canva 的用户数。
```

口径：美元，"亿"即 1 亿美元。Adobe 财年止于 11 月末（FY26 止于 2026-11-27）；Canva 按自然年。Canva 未上市，数字来自公司自述、致股东信的媒体转述和二手报道，逐项标注可信度。文中"公司说法"指未经审计的自述，"估计"和"判断"是本文作者的。来源标 [S#]，链接见文末。本文只做 Canva，Figma 由另一份报告负责。已有的两份 Adobe 评审见 [S44]。

## 1. 关系与时间线

### 1.1 结论

两家公司是**错位竞争为主、在同一家企业里共存**，正面交锋只发生在三处：

| 战场 | 关系 | 现状 | 证据 |
|---|---|---|---|
| 非设计师的日常设计（社交图、海报、演示、简单视频） | 正面竞争 | Adobe 已经输了 | Canva 月活 2.65 亿、付费 3,120 万、ARR 40 亿 [S8][S26]；Adobe 把 Express、Firefly 和三款专业工具的网页与移动版合在一起，创意 freemium 月活才刚过 1 亿 [S2] |
| 专业设计工具（Photoshop、Illustrator、InDesign） | 正面竞争，刚开始 | Adobe 明显领先 | Canva 把 Affinity 改为免费并持续补功能 [S16][S19]；Adobe 创意与营销订阅收入仍增 12%～13% [S1] |
| 企业品牌内容 | 各占一端，中间重叠 | 设计部门用 Adobe，市场、销售、人力用 Canva | Canva 称 95% 的财富 500 强公司里有人在用 [S16]；Adobe 称 99% 的美国财富 500 强在用 Express [S4]。两个数字同时成立，本身就说明是共存 |

共存的典型样子：Docusign 的 17 人创意团队做品牌体系和模板，6,000 多名员工在 Canva 里自助出图 [S16]。Canva 2026 年 9 月发布的 ProSuite 把这个分工写成了产品定位：专业人员在 Affinity 里做模板，团队在 Canva 里套用 [S19]。Adobe 的对应做法是"设计师在 Photoshop／Illustrator 里做，营销人员在 Express 里改"。两家都想把另一端也拿下。

### 1.2 时间线

| 时间 | Canva | Adobe | 含义 |
|---|---|---|---|
| 2013 | 成立，模板加拖拽的网页设计工具 [S27] | 同年把 Creative Suite 改成订阅制 [S18] | 两条路线从同一年分叉 |
| 2016–2021 | 2017 年盈利；2019 年推出"企业版"（实际面向 5～100 人团队）和教育版 [S23][S27] | 2016 年推出 Spark（常识，未取证）；2021-12-13 改名 Creative Cloud Express（第一次重做）[S34] | Adobe 起步不晚，但一直把它当成 Creative Cloud 的附属品 |
| 2022 | 收购 Flourish [S27]；发布文档、白板等"视觉套件"（未取证） | 2022-09 签约收购 Figma，2023-12 终止并付 10 亿分手费 [S6] | Adobe 的注意力在 Figma |
| 2023 | 年化收入超过 15 亿；推出 Magic Studio [S27] | 2023-06 新版 Express 接入 Firefly（第二次重做），8 月正式发布；2023-06-08 推出 Express 企业版并为 Firefly 提供知识产权赔付 [S33][S34] | Adobe 的差异化定在"商用安全" |
| 2024-03 | 收购 Affinity（Serif），估计约 3.8 亿美元 [S27] | 2024-04-18 新版 Express 移动应用正式发布（第三次重做）[S34] | Canva 第一次拿到专业级桌面工具 |
| 2024-05 | 推出真正的企业版，300 美元／席／年起；原"企业版"改叫 Teams，100 美元／席／年 [S23] | — | Canva 开始按席位向大企业收费 |
| 2024-07～09 | 收购 Leonardo.Ai；Teams 涨价，部分老用户从 120 美元／年涨到 500 美元／年，引发反弹 [S24][S27] | 2024-10-14 GenStudio for Performance Marketing 正式发布 [S36] | Canva 也开始用提价变现 |
| 2025-02～06 | 2025-04-10 Visual Suite 2.0：Sheets、Code、Canva AI [S27] | 2025-02-12 Firefly 独立应用与订阅；2025-02-25 Photoshop iPhone 版免费；2025-04 Firefly 接入第三方模型和 Boards；2025-06-17 Creative Cloud Pro 涨到 69.99 美元／月 [S33][S35][S41] | Adobe 一边做免费层，一边提价 |
| 2025-08 | 员工售股估值 420 亿；年化收入 33 亿，付费 2,700 万 [S15] | 2025-08 发布 Acrobat Studio（Acrobat 加 Express 加 PDF Spaces）[S31] | Adobe 把 Express 塞进 Acrobat 的分发渠道 |
| 2025-10-28～30 | 10-30 发布"创意操作系统"：自研设计模型、Affinity 免费、Canva Grow、Business 套餐 [S16][S27] | 10-28 MAX：Express AI 助手（beta）、Firefly Image 5、第三方模型、Foundry [S29] | 同一周正面对撞 |
| 2025-12 | 年底 ARR 40 亿、月活 2.65 亿、付费 3,120 万 [S8][S26] | 12-10 Photoshop、Express、Acrobat 进入 ChatGPT [S32] | 两家都去聊天入口抢位置 |
| 2026-02～04 | 收购 Cavalry、MangoAI、Doohly、Simtheory、Ortto；4-16 发布 Canva AI 2.0（先开放给 100 万人）；COO 称 2027 年上市 [S14][S20][S21] | 4 月 Semrush 交割（对价 18.7 亿）；4-15 Firefly AI 助手；4-28 进入 Claude [S7][S32][S33] | Canva 向营销自动化延伸，Adobe 向搜索可见度延伸 |
| 2026-06 | 6-25 Canva Grow 2.0（广告直投 Meta、TikTok、LinkedIn）[S22] | 6-11 宣布全力转向 freemium、推迟下半年 Creative Cloud 提价，次日股价 −6.8% [S3][S43] | Adobe 改用 Canva 的打法，付出 ARR |
| 2026-08 | 二季度收入 9.22 亿（+25.2%），全年增速预期从 30% 下调到 20%；估值被投资人下调 17%～29% [S9][S13] | — | Canva 自己被 AI 成本和 ChatGPT 打慢 |
| 2026-09 | 9-15 ProSuite 与 Affinity 3.3（可导入 InDesign 文件、脚本、700 万次下载）；Pro 年费在 144 与 180 美元之间反复 [S18][S19][S25] | 9-03 宣布换 CEO，创意业务总裁 Wadhwani 离任；9-10 Q3 财报；9-23 Topaz 交割；9-24 进入 Gemini [S1][S32][S42][S44] | Canva 继续向上，Adobe 换帅 |
| 2026-11（待发生） | Affinity iPad 版（公司预告）[S16] | 11-10～12 Adobe MAX [S2][S44] | 下一次对照 |

### 1.3 2026 年 8 月 Canva 下调增长预期的来龙去脉

| 项 | 内容 | 来源与可信度 |
|---|---|---|
| 事件 | CEO Melanie Perkins 在二季度致股东信里把 2026 年收入增速预期从 30% 降到约 20%。二季度收入 9.219 亿美元，同比 +25.2% | The Information 首发（付费墙，本文只看到标题），Startup Daily、B&T、Fortune 引用信件原文 [S9][S10][S11][S12]。高 |
| 公司给的原因 | "单个 AI 任务的平均服务成本太高""过度依赖前沿模型""几款自研模型还没准备好""定价、用量模型和用量控制没跟上超预期的需求"，于是主动放慢 Canva AI 2.0 的开放 | 信件原文转引 [S9][S10]。高 |
| 媒体补充的内容 | 二季度收入低于公司自己的指引；部分用户在 OpenAI 改进图像生成之后把设计工作转去了 ChatGPT；部分 AI 功能比计划晚了最多 6 个月 | The Information 的二手摘要 [S12]。中 |
| 公司的补救 | 三个月重建架构，单任务成本降近 90%；自研图像模型比前沿模型便宜 30 倍、视频模型便宜 17 倍；Canva AI 2.1 开始放量；推出 100 美元／人／月的 AI Pass | 公司说法 [S9][S10][S20][S25]。成本降幅未经第三方验证 |
| 后果 | Blackbird 与 Airtree 的外部估值师把 Canva 从 420 亿下调 17% 到 349 亿；二级市场经纪商 Hiive 的报价隐含约 300 亿；员工持股的独立估值从一年前的 389 亿降到 310 亿 | Startup Daily 转引 AFR 与 Capital Brief [S13]。中高 |

判断：这不是 Canva 的偶发失误。它说明把生成式 AI 免费发给 2 亿多用户在单位经济上走不通，而 Adobe 在 2026 年 6 月选的正是同一条路。

## 2. 产品与客户重叠地图

### 2.1 产品对照（以 2026 年 10 月在售为准）

| Canva 产品 | 状态与定价 | 对应的 Adobe 产品 | Adobe 收入归属 | 重叠 |
|---|---|---|---|---|
| 设计编辑器与模板素材库（公司称 1.65 亿模板与素材）[S10] | Free；Pro 144 美元／年；Business 250 美元／人／年；Enterprise 2024 年起价 300 美元／席／年 [S19][S23][S25] | Adobe Express；Adobe Stock | Express 在 BP&C；Stock 在 C&MP | 高，正面 |
| Canva AI 2.0／2.1（对话生成、代理、连接器、记忆）；AI Pass 100 美元／人／月 [S20][S25] | 分批开放 | Express AI 助手（beta）；Firefly 应用与 Firefly AI 助手 | BP&C、C&MP | 高 |
| Docs、Presentations、Whiteboards、Websites、Forms | 含在各套餐内 | Acrobat Studio（生成演示文稿、PDF Spaces）、Express 演示；白板与建站未查到对应产品 [S31] | BP&C | 中。这一块 Adobe 的主要对手其实是微软和谷歌 |
| Video | 含在各套餐内 | Express 视频、Premiere 移动版、Firefly 视频编辑器 | BP&C、C&MP | 中 |
| Sheets、Code（小应用与网站工具月活超 1,000 万）[S8] | 含在各套餐内 | 无直接对应 | — | 低 |
| ProSuite：Affinity（图像、矢量、排版，免费）、Cavalry（动效，免费）、Flourish、Leonardo [S19] | 核心功能免费；AI 功能需付费 Canva 套餐 | Photoshop、Illustrator、InDesign、Lightroom 的 RAW 处理、After Effects 的一部分 | C&MP 的创意专业部分 | 中，在上升 |
| 自研模型（Design Model、Lucid Origin 等）与 Leonardo [S20] | — | Firefly 自有模型加多家第三方模型 | C&MP | 高（技术层） |
| 企业功能：Brand Kit／Brand System、模板锁定、审批、单点登录 [S23] | Enterprise | Express 企业版、Creative Cloud Libraries、GenStudio、Firefly Foundry、Brand Intelligence | C&MP 的企业协议与营销云 | 非设计岗位高；内容供应链低 |
| 营销：Canva Grow 2.0（广告制作、直投、效果分析）、Ortto（营销自动化与客户数据，1.1 万客户）、MagicBrief、MangoAI、Doohly [S21][S22] | Grow 各套餐可用 | GenStudio for Performance Marketing、Journey Optimizer、Semrush | 营销云 | 低到中。Canva 在中小企业，Adobe 在大企业 |
| 教育版（K-12 免费；公司称每月 1 亿教育用户）[S16] | 免费 | Express 教育版（K-12 免费；2022 年称覆盖 4,300 万师生，此后未查到更新）、学生版 Creative Cloud、Acrobat Student Spaces [S2][S40] | BP&C、C&MP | 高，影响的是未来的用户漏斗 |
| 印刷（Print Shop）[S16] | 按件收费 | 无 | — | 无 |

价格落差（美国标价）：Creative Cloud Pro 个人版 69.99 美元／月，约 840 美元／年 [S35]；Canva Pro 144 美元／年；Affinity 0 美元。专业套件的价差是 5.8 倍对"免费加 144 美元"。Express Premium 约 9.99 美元／月（第三方汇总，未在 Adobe 官网核到）。

### 2.2 按客户群拆 Adobe 的收入敞口

Adobe FY26 指引：BP&C 订阅收入 74.7～74.9 亿（+15%），即 Acrobat 加 Express；C&MP 订阅收入 182.4～182.7 亿（+12%），即创意专业加营销云 [S1][S6]。按 FY25 营销云订阅 54.1 亿推算，FY26E 营销云约 62 亿（含 Semrush 约 2.8 亿），创意专业约 120 亿。**再往下的拆分 Adobe 不披露，下表金额全部是本文估计。**

| 客户群 | Adobe FY26E 收入（估计） | Canva 的位置 | Canva 对这块 Adobe 收入的威胁 |
|---|---|---|---|
| 个人与学生（非专业）：Express 独立订阅、业余用户的单品与摄影计划、学生版 | Express 独立订阅约 2～4 亿（在 BP&C，不到 5%）；业余与学生的创意订阅约 20～30 亿（在 C&MP） | 主场。付费 3,120 万席，人均约 128 美元／年 | 高，而且新增用户这一端已经输了。存量订阅还在，但提价空间最小 |
| 自由职业者与小团队：Creative Cloud Pro 个人版、团队版 | 约 45～50 亿 | Canva Pro 加免费 Affinity，价格是 Adobe 的六分之一 | 中高，3～5 年见效。取决于 Affinity 能不能补齐插件、字体、协作 |
| 企业里的非设计岗位（市场、销售、人力） | 现有收入很小：Express 多是捆在企业协议和 Acrobat Studio 里送的；偶尔用 Creative Cloud 的"轻度席位"约 5～10 亿 | 主场。25 席以上客户 ARR 5 亿，同比翻倍 [S8] | 对现有收入低，对增量高：这块钱本来可以是 Adobe 的；另有轻度席位续约时被砍的风险 |
| 专业设计师（企业与代理商） | 约 40～45 亿 | Affinity、Cavalry 刚进入，企业里几乎没有 | 低。文件格式、插件、视频与动效、采购合规都还在 Adobe 这边 |
| 企业营销部门（营销云、GenStudio） | 约 62 亿 | Canva Grow、Ortto 从中小企业往上走 | 3 年内很低；5 年看是 GenStudio 向下拓展的天花板 |
| Acrobat／PDF（BP&C 的主体） | 约 70 亿 | 没有 PDF 业务 | 很低。Canva 抢的是"把文档变成演示和图"的延伸场景，不是 PDF 本身 |

核对：个人与学生约 25 亿、自由职业者与小团队约 47.5 亿、轻度席位约 5 亿、专业设计师约 42.5 亿，合计约 120 亿；前两项合计 65～80 亿，与已有评审"个人与小团队占创意专业 55%～65%"的假设一致 [S44]。

## 3. Canva 的经营数据

### 3.1 历年数字

| 时点 | 年化收入／ARR | 月活 | 付费用户 | 估值 | 来源与可信度 |
|---|---|---|---|---|---|
| 2023-08 | 年化收入超过 15 亿 | — | — | — | 公司通稿，经搜索摘要 [S27]。中 |
| 2024-05 | — | 超过 1.8 亿 | — | 260 亿 | TechCrunch [S23]。高 |
| 2024-10 | 年化收入 25 亿 | — | — | 320 亿（二级交易） | 公司通稿、Fortune [S15][S27]。中高 |
| 2025-08 | 年化收入 33 亿 | 2.4 亿 | 2,700 万 | 420 亿（员工售股） | Fortune [S15]。高 |
| 2025-10～12 | 年化收入 35 亿 | 2.6 亿 | 超过 2,800 万 | — | Canva 新闻稿 [S16]。公司说法 |
| 2025-12 | ARR 40 亿；其中 25 席以上客户 5 亿（+100%） | 超过 2.65 亿（全年 +20%） | 3,120 万 | — | COO 对 TechCrunch、联合创始人对 Inc. [S8][S26]。公司说法 |
| 2026-04 | — | "超过 2.5 亿" | — | — | 公司通稿 [S20]。未给新数 |
| 2026-06（季度） | 二季度收入 9.219 亿（+25.2%）；现金 14.7 亿 | — | — | — | 致股东信的媒体转述 [S9]。高 |
| 2026-08 | 全年收入增速预期 20%（原 30%） | — | — | 349 亿／约 300 亿／310 亿（三种口径） | [S9][S13] |
| 2026-09 | — | "2.5 亿用户"，每月 10 亿份设计 | — | — | Creative Boom 转述公司 [S18]。中 |

未查到 Canva 在 2026 年披露过高于 2.65 亿的月活或高于 3,120 万的付费用户数。第三方流量统计显示 canva.com 在 2025-05 至 2026-04 的访问量为 105 亿次，同比 +15.5% [S38]。判断：用户增长在 2026 年明显放慢，可信度中低。

### 3.2 口径提醒：Canva 的"ARR"比确认收入高一截

- 二季度确认收入 9.219 亿，年化只有 36.9 亿，低于半年前宣布的 40 亿 ARR。
- 同比 +25.2% 倒推 2025 年二季度收入约 7.36 亿，年化 29.5 亿，而公司 2025 年 8 月宣布的"年化收入"是 33 亿，高出约 12%。
- 一份二手材料称 Canva 2025 年法定报表收入 30.2 亿（2024 年 21.5 亿，+40%），税后利润约 0.26 亿，净利率不到 1% [S28]。这与 COO 说的"去年增长 40%"[S14] 和上面的季度倒推都对得上，但原始报表本文没有拿到，可信度中低。

判断：把 Canva 的 ARR 与 Adobe 的 ARR 并排比较时，应当打九折左右。Canva 的确认收入口径大约是：2025 年 30 亿，2026 年按 +20% 约 36 亿。

### 3.3 盈利与现金

- 公司说法不一致：COO 说"连续盈利九年"[S14]，另一位联合创始人说"连续七年"[S26]。
- 2026 年 6 月末现金 14.7 亿 [S9]。未查到自由现金流、毛利率和 AI 成本占比。
- 若 3.2 节的法定净利率（约 1%）属实，Canva 没有利润垫来消化推理成本，这解释了它为什么只能放慢开放、砍免费额度、提价。

定价动作（第三方价格追踪，可信度中）：Pro 年费 2026 年 3 月底从 120 涨到 144 美元，8 月初一度升到 180，9 月中回到 144；免费版的 AI 额度从"每月 200 次标准"砍到"20 次"；付费版标准 AI 改为合理使用不限量 [S25]。官方帮助页确认 AI Pass 为 100 美元／人／月 [S25]。

### 3.4 融资与上市

- 2025 年二级市场成交超过 20 亿美元 [S13]。未查到 2026 年有新的一级融资或员工售股。
- 上市：2025-11 COO 说"未来两三年内"；2026-04 改口"我想是明年"，并说要等 AI 积分制定价过渡完成之后 [S14]。8 月下调预期后，Startup Daily 认为 2027 年赴美上市可能再推迟 [S13]。未查到已提交招股书。

### 3.5 与 Adobe 的可比口径

| 指标 | Canva | Adobe | 比值 |
|---|---|---|---|
| 期末 ARR（2025 年底／FY25 末） | 40 亿（公司说法） | 总 ARR 252.0 亿；其中 Digital Media 192.0 亿 [S5] | 16%；21% |
| 2025 年 ARR 增量 | 约 11.4 亿（按"增长 40%"倒推年初 28.6 亿，估计） | 净新增总 ARR 约 26.0 亿；Digital Media 约 19.8 亿（按披露增速倒推） | 44%；58% |
| 2026 年 ARR／收入增量 | 收入增量约 6 亿（30 亿 ×20%）；若 ARR 也增 20% 则约 8 亿（估计） | FY26 有机净新增 ARR 约 21.4 亿（指引 10.2% 扣 Semrush 4.8 亿）[S1][S3] | 28%～37% |
| 最近一个季度收入 | 9.22 亿（+25.2%），同比多 1.86 亿 | 67.6 亿（+13%），同比多 7.72 亿，扣 Semrush 约 1.2 亿（估计）后约 6.5 亿 [S1] | 收入 14%；增量 29% |
| 月活 | 2.65 亿 | 创意 freemium 月活超过 1 亿（+70%）；Acrobat 加 Express 超过 9 亿 [S2] | 口径不可直接比 |

两家合计的增量里，Canva 的份额从 2025 年的约 31% 降到 2026 年的约 22%～27%。读法：2025 年是 Canva 相对 Adobe 最强的一年；2026 年两家都在减速，Canva 减得更多。Adobe 的净新增 ARR 下滑主要是自己的选择加生成式 AI 的压力，不能记在 Canva 一家头上。

## 4. Affinity 免费化的实际效果

| 项 | 内容 | 来源 |
|---|---|---|
| 做法 | 2025-10-30 把 Affinity Photo、Designer、Publisher 合成一个应用，Mac 与 Windows 版永久免费，需注册 Canva 账号；生成式填充、抠图等 AI 功能要付费 Canva 套餐。据第三方评测，此前"保留买断授权"的承诺未再提 | [S16][S19] |
| 下载 | 4 天 100 万人注册；33 天 300 万次下载（旧版用了 9 年才到这个数）；2026-04 称"500 多万创意人员已采用"；2026-09 称 700 万次下载 | [S16][S17][S18] |
| 节奏 | 首月 300 万；此后约 9 个半月共 400 万，即每月约 40 万次。这是下载和注册，不是活跃用户；Canva 没有披露 Affinity 的月活和付费转化 | 本文计算 |
| 功能进展 | 3.1（2026-03，首次大更新）；Create 2026（4 月）加入 Brand System，可把品牌元素发布到 Canva 的 Brand Kit，并接入 Capture One、DaVinci Resolve、Claude；3.3（2026-09-15）60 多项更新，含直接导入 InDesign 文件、脚本工作室、混合工具、RAW 处理；iPad 版预告 11 月发布 | [S16][S19] |
| 配套 | 动效工具 Cavalry 收购后也改为免费；四款工具合称 ProSuite，目前仍各自下载、各自使用，主要是品牌包装 | [S19] |
| 变现方式 | 公司的解释是"核心工具免费，高级内容、协作和 AI 收费"。三条路：应用内 AI 功能带动 Pro 订阅；设计师做的模板和品牌资产流进 Canva，带动 Business 与 Enterprise 席位；注册账号进入 Canva 的用户池。未查到任何收入数字 | [S16] |
| 对专业用户的吸引力 | 评测的共识：图像、矢量、排版可以当日常主力；短板是插件生态、Adobe 字体库、视频与后期、团队协作，以及对 Canva 长期承诺的不信任。未查到代理商或企业成规模迁移的案例 | 第三方评测汇总，可信度低到中 [S19] |

对 Adobe 的影响证据：

- **没有查到**可归因于 Affinity 的 Adobe 订阅流失数据、标价下调或免费桌面版。Adobe 官方页面在 2026-06-24 仍写明"网页版 Photoshop 没有免费版本"[S41]。
- Affinity 免费后的三个季度，Adobe 的 C&MP 订阅收入同比 +12%、+13%、+13%；Q3 管理层点名的增长来源是 Creative Cloud 的"团队版与企业版"，没有提个人版 [S1][S2]。Q4 指引隐含 +10%，扣 Semrush 约 +7%。
- 间接迹象有两条。其一，Adobe 2026 年 6 月推迟了下半年的 Creative Cloud 提价，并下调了"来自个人订阅者"的下半年 ARR 预期 [S3]。其二，摩根士丹利 7 月下调评级时，媒体摘要称其担心 Canva 和开源图像生成工具侵蚀单品订阅用户，尤其是 Photoshop [S37]。

判断：一年下来，Affinity 改变的是 Adobe 的定价空间，还没有改变 Adobe 的用户数。700 万次下载里有多少是 Adobe 的现有或潜在付费用户，没有数据；即使按一成算，也就是几十万个席位、2～5 亿美元的量级，占创意专业收入的 2%～4%。

## 5. Adobe 的应对

### 5.1 逐条清单

| 时间 | 动作 | 内容 | 现状与效果证据 | 评价 |
|---|---|---|---|---|
| 2021-12 至 2025-10 | Express 四次重做 | Spark 改名 Creative Cloud Express（2021-12-13）；接入 Firefly 的新版（2023-06 测试、8 月发布）；新移动应用（2024-04-18）；AI 助手与"后模板时代"的生成式设计（2025-10-28）[S29][S34] | Express 月活 FY26 Q1 同比增到 3 倍，Q2 环比再增 20% 以上；FY25 Q4 单季有 2.5 万家企业首次购买 Express 或 Studio [S3][S4][S5]。**绝对月活、付费数和 ARR 从未披露** | 用户量在涨，变现无法验证 |
| 2025-10 至今 | Express AI 助手 | 对话式生成与编辑 [S29] | 截至 2026 年 9 月前后官方帮助页仍标 beta，仅个人账户、仅桌面端、6 种语言；团队、企业、教育套餐不可用，Adobe 称团队与企业版"今年晚些时候"开放 [S30] | 发布近一年仍未全面可用 |
| 2023-06 至 2026 | Express 进企业与教育 | 2023-06-08 企业版；MAX 2025 后增加企业模板库、审批、品牌主页、细粒度权限 [S30][S33] | 称 99% 的美国财富 500 强在用；学校授权的高校学生数 FY25 +70%、FY26 Q2 +60%；与印度 Airtel、沙特政府做分发合作 [S2][S3][S4][S5] | 覆盖面大，但多是捆绑赠送，没有独立收入数字 |
| 2023 至 2026 | Firefly | 商用安全训练与企业赔付（2023-06）；独立应用与订阅，9.99 和 29.99 美元两档（2025-02-12）；第三方模型与 Boards（2025-04-24）；移动应用（2025-06）；Image 5、定制模型、Foundry（2025-10-28）；订阅用户限时无限生成（2026-02）；Firefly AI 助手与创意代理（2026-04、06）[S29][S33] | Firefly ARR FY26 Q1 超过 2.5 亿、Q2 接近 3 亿；应用与积分包 ARR Q2 环比 +50%、Q3 环比 +40%；AI-first ARR 超过 6.5 亿（+150%）[S2][S3][S4] | 有效，但体量小：Firefly 约占总 ARR 的 1%，AI-first 合计约 2.4% |
| 2025-02 起 | 专业工具的免费层 | Photoshop iPhone 版免费，付费档 7.99 美元／月（2025-02-25）；Premiere 手机版免费；Lightroom 网页与移动版 [S41] | 创意 freemium 月活：FY25 Q4 超 7,000 万，FY26 Q1 至 Q3 依次超 8,000 万、9,000 万、1 亿，同比 +35%、+50%、+70%、+70% [S2][S3][S4][S5] | 漏斗在变宽；这是五款产品的合计，仍不到 Canva 的四成 |
| 2025-08 起 | Acrobat Studio 与 PDF Spaces | Acrobat 加 Express Premium 加 AI 助手，上市价 24.99 美元／月；2026-01 生成演示文稿和播客；2026-05 生产力代理与新增的 Acrobat Express 档；2026-09-09 知识库与分析器 [S31] | FY25 Q4 续约的 Acrobat 商业企业协议近一半升级到 Studio；BP&C 订阅收入连续四个季度 +15%～16%，Q4 指引 +12.8% [S1][S5] | 最有效的一招：用 9 亿月活的 PDF 入口去分发 Express |
| 2024-10 起 | GenStudio 与品牌内容供应链 | GenStudio for Performance Marketing（2024-10-14）；Summit 2026（4-20～22）把体验云改名 CX Enterprise，GenStudio 拆三个模块；戛纳（2026-06）加入零售媒体网络 [S2][S36] | GenStudio ARR 同比 +20%～30%；Firefly 企业版生成资产数同比 4 倍 [S2][S3][S4][S5] | 大企业端守得住，Canva 短期够不着 |
| 2025-06、2026-06 | 分层与定价 | 2025-06-17 把 All Apps 改名 Creative Cloud Pro 并从 59.99 涨到 69.99 美元／月，另设 54.99 美元的 Standard 档 [S35]；2026-06-11 推迟下半年提价，把流量从"直接付费"改导向免费体验 [S3] | 见 5.2 | 2025 年还在提价，2026 年停了 |
| 2025-12 起 | 接入聊天平台 | ChatGPT（2025-12-10，媒体称免费可用）；Claude（2026-04-28）；Gemini 与 Claude 插件扩到 80 多个工具（2026-09-24）；ChatGPT 内的交互式编辑面板（2026-09-29）[S32] | 未披露使用量。Canva 的同类数字是截至 2025-10 在 ChatGPT 内 2,600 万次对话、位列 ChatGPT 外链前十 [S8] | 方向对，但 Canva 先到，且同样在场 |
| 2025-11 至 2026-09 | 收购 | Semrush（对价 18.7 亿，2026-04 交割，带来 4.8 亿 ARR）；Topaz Labs（约 3.4 亿，2026-09-23 交割，100 多万用户）[S2][S7][S42] | 品牌可见度方案的付费客户数环比翻倍 [S2] | 加强的是营销人员和专业画质，不是 Canva 的主场 |
| 2025-10、2026-04、2026-11 | 大会 | MAX 2025 面向创作者与营销人员的发布见上；Summit 2026 见上；MAX 2026 定于 11-10～12，管理层预告 Firefly 与 Creative Cloud 有"突破性发布"[S2][S29][S36] | 待观察 | — |

### 5.2 没有应对、应对无效或代价很大的地方

1. **对"专业工具免费"没有价格回应。** Photoshop 桌面版和网页版都没有免费档，Creative Cloud Pro 标价未降，也没有恢复买断 [S41]。Adobe 的回应是加 AI 额度和功能，不是价格。这在专业用户那里目前够用，在学生和业余用户那里不够。
2. **Express 没有追上。** 五年四次重做之后，Adobe 仍然不敢单独披露 Express 的月活和付费数；它最新的旗舰功能 AI 助手近一年还没走出 beta，企业和教育账户用不了 [S30]。而企业和教育正是 Canva 增长最快（B2B 翻倍）和漏斗最深（每月 1 亿教育用户）的两处。
3. **freemium 转向与推迟提价的代价很大。** 分析师在电话会上估算两项合计让有机 ARR 少约 5 亿美元，管理层没有否认，并说一半来自推迟提价、一半来自把流量导向免费 [S3]。可见的结果：
   - Q3 净新增 ARR 4.0 亿，同比 −37%；FY26 有机 ARR 增速约 8.3% [S1][S44]。
   - FY25 的 Digital Media 净新增 ARR 里不到四分之一来自提价 [S5]，即每年接近 5 亿美元的来源在 2026 年下半年被关掉。
   - Q3 订阅毛利率 90.4%，去年同期 91.2%；订阅成本同比 +24%，订阅收入 +14% [S1]。
   - 财报次日（6-12）股价 −6.8%，到 6-18 收盘较 6-11 收盘累计 −10.8% [S43]；十多家券商下调目标价，摩根士丹利 7 月、富国银行 10-12 先后降到减持 [S37]。
4. **素材库（Stock）在加速下滑。** FY26 Q1 管理层承认独立素材业务的下滑"快于预期"[S4]。模板和素材正是被生成式 AI 和 Canva 的内含素材库同时替代的东西，Adobe 的回应只是"让客户自己选素材还是生成"。
5. **人事。** 主导 Express、Firefly 和 freemium 转向的创意与生产力业务总裁 Wadhwani 已于 9 月底离任，接任者未查到；新任 CEO 出身企业营销业务 [S44]。战略由谁继续执行有不确定性。

## 6. AI 对这场竞争的改变

| 问题 | 证据 | 判断 |
|---|---|---|
| 聊天式生成在侵蚀谁 | OpenAI 2026-04-21 发布 ChatGPT Images 2.0，文字与版式渲染明显改善，能直接出海报和信息图 [S39]。Canva 管理层注意到用户转去 ChatGPT [S12]。Adobe 在 10-K 里自己写"AI 功能和对话界面正在取代传统模板"，Stock 下滑快于预期 [S4][S6] | 两边的低端都在被侵蚀。模板库是 Canva 的护城河，受伤更重；Express 体量小，受伤的是成长期权 |
| 谁受益 | Canva 和 Adobe 都变成了聊天助手可以调用的工具：Canva 在 ChatGPT、Claude、Copilot、Gemini 里；Adobe 在 ChatGPT、Claude、Gemini 里 [S8][S32][S39]。Anthropic 2026-04-17 发布 Claude Design 时，Canva 是导出合作方，当天 Adobe 股价跌约 1.5% [S39] | 入口归了聊天平台。从收入结构看 Adobe 相对受益：Canva 的绝大部分收入在会被聊天生成替代的轻量设计上，Adobe 这类收入约占一成（估计） |
| Canva 的推理成本说明什么 | 免费用户用前沿模型，单任务成本高到要砍掉三分之一的增长预期；补救靠自研小模型、砍免费额度、提价、卖 100 美元的 AI Pass [S9][S25] | 免费加生成式 AI 的模式有成本地板。Adobe 的 freemium 转向面对同一条成本曲线，但它从 2023 年起就有生成积分制，转嫁机制比 Canva 成熟；代价是"免费"不够大方，月活增速在促销结束后可能回落 |
| Adobe 聚合第三方模型的得失 | Firefly 自有模型主打商用安全和赔付，同时接入谷歌、OpenAI、Runway、Kling、ElevenLabs、Topaz 等 [S3][S29][S33] | 得：不必赢模型竞赛，成本可按积分转嫁，企业信任。失：同样的模型在 Canva 和 ChatGPT 里也能用，差异化弱；毛利要分给模型方；模型方同时是对手，10-Q 风险因素已写明对方可能限制 Adobe 使用其模型 [S7] |
| Canva 自研与收购模型的得失 | 收购 Leonardo（2024），自建 100 多人的研究团队，自研模型称比前沿模型便宜 17～30 倍，输出可编辑的分层设计 [S10][S20] | 得：单位成本低，输出是可编辑设计。失：自研模型没按时就绪，功能晚了最多半年；一家净利率很薄的公司要长期养模型研发 |

## 7. 对 Adobe 未来的影响

### 7.1 已经造成的影响

| 项 | 量级 | 说明 |
|---|---|---|
| 输掉的市场 | Canva 的 40 亿美元 ARR、3,120 万付费席 | 这是 Adobe 从 2016 年做 Spark 起就想要的客户群。Adobe 在其中的份额没有披露，本文估计不到一成（Express 独立订阅 2～4 亿）。这是没拿到的增量，不是丢掉的存量 |
| 教育漏斗 | Canva 每月 1 亿教育用户 | Adobe 上一次给出 Express 教育版数字是 2022 年的 4,300 万（覆盖数，非月活）。下一代用户先学会的是 Canva |
| 企业非设计席位 | Canva B2B ARR 5 亿，同比翻倍 | Adobe 的 Express 在企业里多为捆绑，没有对应的独立收入 |
| 净新增 ARR | FY25 约 26.0 亿，FY26 有机约 21.4 亿（−18%）；下半年约 11.8 亿，同比 −25% [S44] | 管理层归因于主动转向 freemium 和推迟提价，没有点名 Canva。判断：Canva、聊天助手和 AI 原生创作工具一起，让"访客直接付费"的老漏斗失效了，这是 Adobe 不得不改的原因 |
| 定价权 | 每年接近 5 亿美元的提价贡献在 FY26 下半年暂停 | Creative Cloud Pro 840 美元／年对"Canva Pro 144 美元加免费 Affinity"，继续提价的代价越来越高 |
| freemium 转型 | 创意 freemium 月活超 1 亿（+70%），订阅毛利率 −0.8 个点 | Adobe 在用利润率和短期 ARR 换 Canva 早就有的东西：免费用户池 |

### 7.2 未来 3～5 年

基准路径下 FY30 收入约 345 亿美元（已有评审的增速 7.5%、7%、6.5%、6%）。下表是 Canva 一家能造成的偏离，金额为本文估计。

| 客户群 | 最可能的情形（本文给 55%～60%） | 坏情形（本文给 20%～25%） |
|---|---|---|
| BP&C（FY26E 74.8 亿） | 增速从 15% 降到 FY29 的 9%～10%，主要是基数和聊天助手所致，Canva 贡献不到 1 个点。到 FY30 少 2～4 亿 | Canva 的文档、演示加 AI 抢走"把文档变成内容"的场景，Studio 升级停滞。到 FY30 少 4～6 亿 |
| 个人与小团队创意订阅（约 72 亿） | 新增放缓、提价受限，Canva 与 Affinity 每年拖 1～2 个点。到 FY30 少 4～8 亿 | Affinity 补齐插件、iPad、协作，ProSuite 有了团队功能；三年里一成多用户降级或流失，且无法提价。到 FY30 少 10～15 亿 |
| 企业创意协议（约 48 亿） | 轻度席位被挤，每年拖不到 1 个点。到 FY30 少 1～2 亿 | 一个三年续约周期里约一成席位价值被重新谈判。到 FY30 少 4～5 亿 |
| 营销云（约 62 亿） | 基本不受影响 | Canva 成为营销人员的制作入口并直连广告平台，GenStudio 增速从 25% 降到十几。到 FY30 少 2～3 亿 |
| 合计 | 到 FY30 少 7～14 亿，占基准收入 2%～4% | 到 FY30 少 20～29 亿，占 6%～8% |

两种情形之外的 15%～25%，是 Canva 继续减速、威胁减轻的情形。

读法：

- 最可能的情形基本就是基准路径本身（增速逐年下滑）已经包含的内容，不是额外的减项。
- 坏情形的 20～29 亿，约为 FY30 基准收入（345 亿）与熊市收入（271 亿）差距的三成左右。Canva 一家推不出熊市情景；熊市需要生成式 AI 的普遍替代和 Adobe 被迫降价，Canva 的作用是给想离开的用户提供一个现成、便宜、功能够用的落脚点。
- 对 Adobe 有利的变化：Canva 增速降到 20%、利润薄、上市推迟、自己在提价，补贴能力下降；它的中心任务从抢 Adobe 变成了守住被 ChatGPT 分流的基本盘。
- 对 Adobe 不利的变化：低端被聊天生成压缩之后，Canva 更有动力去拿 Adobe 的利润池（专业工具和企业营销）。Affinity 是本地软件，免费的边际成本接近零，推理成本的问题拦不住这一步。

### 7.3 是否改变已有评审的情景假设

**判断：已包含。不需要因 Canva 单独上调坏情景概率，也不需要下调基准路径；建议补充两条跟踪指标并修正两处表述。**

依据：

1. **熊市（37%）加压力（5%）不动。** 熊市的机制（生成式 AI 替代个人与小团队、freemium 吃掉付费、被迫降价）已经覆盖 Canva 所在的客户群。专业级免费替代品存在了 11 个月，Adobe 团队版和企业版仍在增长，没有出现降价；同期 Canva 自己从 +40% 减速到 +20%。这两组证据方向相反，大致抵消。
2. **基准（45%）路径不动，但它没有缓冲。** 基准假设净新增 ARR 稳定在每年约 20 亿美元。FY26 有机净新增约 21.4 亿，其中还没有计入提价暂停的全年影响。如果提价长期不能恢复（每年接近 5 亿），净新增会落到 16～17 亿，FY28 以后的增速要比基准低约 0.5 个点。
   - 敏感性（本文按已有评审的公式复算，基准 V 约 361）：FY28 至 FY30 每年增速各降 0.5 个点，基准 V 降约 5 美元，概率加权 V 从 282 降到约 280，P/V 仍是 0.86 到 0.87。
   - FY27 至 FY34 每年都降 0.5 个点左右，基准 V 降约 17 美元，加权 V 约 275，P/V 0.88。
   - 两种算法都不改变"温和低估"的档位，所以本文不建议现在就改路径，等 12 月的 FY27 指引。
3. **需要修正的两处表述。**
   - "Acrobat 与 Express 这块 FY26E 74.8 亿、增 15%"：这块几乎全是 Acrobat，Express 独立收入估计不到 5%。Canva 对这块现有收入的威胁很低；受影响的是"Express 成为第二个 Acrobat"的期权。Q4 指引已隐含增速降到 12.8%。
   - "Adobe 输给 Canva 的是范式变化"成立，但现在两家都在面对下一次范式变化（聊天式生成）。Canva 的减速不是 Adobe 的利好，它证明的是低端在被商品化，而且免费发 AI 有成本地板，这对 Adobe 的 freemium 转向同样适用，支持基准情景里"利润率不扩张"的假设。

什么情况下要改：出现 7.4 节第 2、3 条的"加重"信号之一，就把熊市概率上调 3～5 个点（从基准挪过去，V 约 271～276）；两条同时出现，按已有评审第 5.3 节的减仓规则处理。

### 7.4 可跟踪的指标与门槛

| 指标 | 现值 | 威胁加重 | 威胁减轻 | 时点 |
|---|---|---|---|---|
| 1. Canva 的增长 | 2026 Q2 收入 +25.2%；全年预期 +20%；B2B ARR 5 亿 | 2026 全年收入增速回到 25% 以上，或 B2B ARR 达到 10 亿，或披露月活超过 3 亿 | 全年增速低于 20%，或 2027 年预期低于 20% | 2027 年 2 月（上一年的年度数字在 2 月公布）；2027 年 4 月 Canva Create |
| 2. Adobe 的定价行为 | Creative Cloud Pro 69.99 美元／月；下半年提价已推迟 | 到 2027 年 6 月仍未恢复提价，或把 Creative Cloud Pro、Photoshop 单品标价下调 15% 以上，或推出免费的完整桌面版 | FY27 上半年恢复提价且 C&MP 增速不掉 | MAX（11-10～12）；12 月财报；FY27 Q2 财报 |
| 3. C&MP 订阅收入增速 | Q3 +13%；Q4 指引 +10%，扣 Semrush 约 +7% | FY27 指引低于 6%，或电话会首次承认个人或团队版订阅数净减少 | FY27 指引不低于 9% | 12 月财报 |
| 4. freemium 能否变现 | 创意 freemium 月活超 1 亿；AI-first ARR 超 6.5 亿；Firefly ARR 接近 3 亿（Q2）；订阅毛利率 90.4% | 到 FY27 Q2 AI-first ARR 仍低于 10 亿，或订阅毛利率跌破 89.5% | 月活超过 1.3 亿，同时 AI-first ARR 超过 10 亿 | FY27 Q1、Q2 财报 |
| 5. Express 与 Affinity 的产品进度 | Express AI 助手仍是 beta，企业与教育不可用；Affinity 700 万次下载，iPad 版 11 月 | MAX 之后 Express AI 助手仍未对团队与企业开放；或 Affinity 下载到 2027 年 10 月超过 1,200 万并出现代理商、企业成批迁移的公开案例 | Adobe 首次披露 Express 的月活或付费数（敢披露本身就是信号） | MAX；2027 年 4 月、10 月 |

BP&C 增速（FY27 指引低于 10% 为负面）已在已有评审的证伪条件里，不重复。

### 7.5 最不确定的地方与未能核实的事项

最不确定的两点：

1. **Adobe 推迟提价有多少是因为竞争。** 管理层说是为了集中精力抓用户；如果 12 月或 2027 年上半年顺利恢复提价，本文关于定价权受限的判断就过重了。
2. **Affinity 的 700 万次下载里有多少是 Adobe 的付费用户。** 没有任何数据。本文"没有造成可见流失"的结论依赖的是 Adobe 的汇总增速和管理层措辞，而 Adobe 的增速同时受 freemium 转向、提价暂停和 Semrush 并表的干扰，拆不开。

未能核实的事项：

- Canva 致股东信原文、The Information 报道正文（付费墙）、Canva 法定报表原件；毛利率、自由现金流、AI 成本占比均未查到。
- Canva 新闻稿与 Adobe 帮助页直接访问被拦，相关内容取自搜索引擎摘要 [S16][S30]；PetaPixel、Forbes、Business Wire 个别页面同样只核到标题或摘要。
- Canva 在 2026 年的月活、付费用户数、Affinity 月活、Affinity 带来的付费转化：未查到。
- Adobe Express 的绝对月活、付费数、ARR，以及 Adobe 工具在 ChatGPT、Claude、Gemini 内的使用量：公司未披露。
- Adobe 各客户群内部的收入拆分（个人、团队、企业）：公司不披露，文中金额均为估计。
- Canva 2022 年"视觉套件"与 2023 年 Magic Studio 的确切发布日期、Premiere 手机版和 Photoshop 安卓版的确切上线日期：未逐项核实。
- Canva Pro 年费在 2026 年的三次变动来自第三方价格追踪，未在官网核到历史价。
- Wadhwani 的接任者、Adobe 是否对 Affinity 或 Canva 有公开表态：未查到。
- 本文没有运行仓库的文档审计脚本，也没有提交 Git。

## 来源

- [S1] Adobe Q3 FY26 业绩稿（8-K Ex.99.1，2026-09-10）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000147/adbeex991q326.htm
- [S2] Adobe Q3 FY26 电话会纪要（2026-09-10）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q3fy26-transcript.pdf
- [S3] Adobe Q2 FY26 电话会纪要与业绩稿（2026-06-11）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q2fy26-transcript.pdf ；https://www.sec.gov/Archives/edgar/data/796343/000079634326000109/adbeex991q226.htm
- [S4] Adobe Q1 FY26 电话会纪要（2026-03-12）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q1fy26-transcript.pdf
- [S5] Adobe Q4 FY25 业绩稿与电话会纪要（2025-12-10）：https://www.sec.gov/Archives/edgar/data/796343/000079634325000135/adbeex991q425.htm ；https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q4fy25-transcript.pdf
- [S6] Adobe FY25 10-K（截至 2025-11-28；客户群定义、竞争描述、Figma 分手费）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000003/adbe-20251128.htm
- [S7] Adobe 10-Q（截至 2026-08-28，2026-09-22 提交；Semrush 对价、Topaz、AI 风险因素）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm
- [S8] TechCrunch，Canva gets to $4B in revenue as LLM referral traffic rises（2026-02-18）：https://techcrunch.com/2026/02/18/canva-gets-to-4b-in-revenue-as-llm-referral-traffic-rises/
- [S9] Startup Daily，Canva cuts revenue forecast by a third as it tackles high AI costs（2026-08-05）：https://www.startupdaily.net/?p=139035
- [S10] B&T，Canva slashes revenue forecast due to AI spend being higher than expected（2026-08-05）：https://www.bandt.com.au/canva-slashes-revenue-forecast-due-to-ai-spend-being-higher-than-expected/
- [S11] Fortune（2026-08-12）：https://fortune.com/2026/08/12/canva-startup-growth-ai-costs-revenue-forecast-by-third/
- [S12] The Information，Canva Hits AI Speedbump on Costs, ChatGPT Competition（2026-08 初，付费墙，只核到标题）：https://www.theinformation.com/articles/canva-hits-ai-speedbump-costs-chatgpt-competition ；Dealroom 摘要（2026-08-06）：https://dealroom.co/news/info-19trz12-canva-hits-ai-speedbump-on-costs-chatgpt-competition/ ；AI Weekly（2026-08-06）：https://aiweekly.co/alerts/canva-cuts-revenue-growth-forecast-on-ai-cost-blowout
- [S13] Startup Daily，Canva wipes $11 billion from its valuation, putting IPO plans in doubt（2026-08-17）：https://www.startupdaily.net/advice/business-strategy/canva-wipes-10-billion-from-its-valuation-putting-ipo-plans-in-doubt/
- [S14] Capital Brief（2026-04-17，Obrecht 谈 2027 年上市与"去年增长 40%"）：https://www.capitalbrief.com/article/scoop-cliff-obrecht-confirms-canva-is-now-working-towards-an-ipo-next-year-in-2027-cb530c42-3b29-4793-a7b9-e86f79af7812/ ；Bloomberg 标题（2025-11-21）：https://bloomberg.com/news/articles/2025-11-21/canva-s-obrecht-says-firm-eyeing-ipo-in-next-couple-of-years
- [S15] Fortune（2025-08-22，420 亿估值、年化收入 33 亿、月活 2.4 亿、付费 2,700 万）：https://fortune.com/2025/08/22/canva-billionaire-founders-minting-overnight-millionaires-employee-share-sale
- [S16] Canva 新闻稿（直接访问被拦，内容取自搜索引擎摘要）：Affinity 免费的理由 https://www.canva.com/newsroom/news/affinity-free/ ；2025 年回顾 https://www.canva.com/newsroom/news/canva-2025-wrap/ ；Canva Create 2026 https://www.canva.com/newsroom/news/canva-create-2026-launches/ ；ProSuite（2026-09）https://www.canva.com/newsroom/news/canva-prosuite-launch/ ；Canva Business https://www.canva.com/newsroom/news/introducing-canva-business/ ；企业案例 https://www.canva.com/newsroom/news/roi-canva-case-studies/
- [S17] PetaPixel，Affinity Hits 3M Downloads in Just 33 Days（2025-12-03，经搜索摘要）：https://petapixel.com/2025/12/03/affinity-hits-3m-downloads-of-its-new-editing-software-in-just-33-days
- [S18] Creative Boom，Canva launches ProSuite（2026-09-15）：https://www.creativeboom.com/news/canva-launches-prosuite-bringing-affinity-cavalry-flourish-and-leonardo-together-with-more-than-new-100-features/
- [S19] CG Channel，Affinity 3.3（2026-09）：https://www.cgchannel.com/2026/09/canva-releases-affinity-3-3/ ；heise（2026-09-15）：https://www.heise.de/en/news/Canva-launches-ProSuite-and-expands-Affinity-11451982.html ；Web Designer Depot（2026-09-25）：https://webdesignerdepot.com/canva-just-turned-affinity-into-adobes-biggest-free-problem/ ；评测汇总见 TechRadar：https://www.techradar.com/pro/affinity-by-canva-2026-review
- [S20] Canva AI 2.0 通稿（Business Wire，ANSA 转载，2026-04-16）：https://www.ansa.it/sito/notizie/economia/business_wire/2026/04/16/canva-unveils-canva-ai-2.0-reimagining-how-the-world-designs-and_1dd656c5-d9a1-4be0-ba76-a1d840827b9e.html
- [S21] TechCrunch，Simtheory 与 Ortto 收购（2026-04-08）：https://techcrunch.com/2026/04/08/canva-doubles-down-on-ai-and-marketing-automation-with-simtheory-ortto-acquisitions
- [S22] Canva Grow 2.0 通稿（Business Wire，2026-06-25，经搜索摘要）：https://secure.businesswire.com/news/home/20260625870253/en/Introducing-Canva-Grow-2.0-Create-Launch-and-Optimize-Ads-in-One-Place
- [S23] TechCrunch，Canva launches a proper enterprise product（2024-05-23）：https://techcrunch.com/2024/05/23/canva-launches-a-proper-enterprise-product-and-they-mean-it-this-time/
- [S24] Canva Teams 涨价（2024-09）：https://www.phonearena.com/news/design-platform-canva-reported-huge-price-hike-sparks-online-backlash_id162208 ；https://techcrunch.com/video/techcrunch-minute-canva-faces-backlash-over-price-hikes
- [S25] PricingSaaS 价格追踪（2026 年第 14、32、38 周）：https://pricingsaas.com/companies/canva/diffs/2026W38 ；Canva 帮助页 AI Pass：https://www.canva.com/help/ai-pass/
- [S26] Inc. 通讯，Cameron Adams 访谈（2026-02-25）：https://inc-1-smart-business-story.beehiiv.com/p/canva-co-founder-cameron-adams-on-hitting-4-billion-arr-the-power-of-free-and-that-ipo-825a
- [S27] Canva 历史：维基百科时间线 https://en.wikipedia.org/wiki/Canva ；TechCrunch，Leonardo 收购与 Affinity 估价（2024-07-29）https://techcrunch.com/2024/07/29/canva-acquires-leonardo-ai-to-boost-its-generative-ai-efforts/ ；Visual Suite 2.0 通稿（2025-04-10）https://www.businesswire.com/news/home/20250410082173/en/Canvas-Biggest-Launch-Yet-Introduces-Visual-Suite-2.0-to-Redefine-Creativity-and-Productivity ；创意操作系统通稿（2025-10-30）https://businesswire.com/news/home/20251030695119/en/Canva-Launches-Creative-Operating-System ；年化收入 25 亿通稿（2024-10-22）https://www.businesswire.com/news/home/20241022640737/en （Business Wire 页面经搜索摘要）
- [S28] Value For Startups（转述 Canva 2025 年法定报表，二手、单一来源）：https://valueforstartups.in/canva ；Sacra：https://sacra.com/c/canva/
- [S29] Adobe 新闻稿，Express AI 助手（2025-10-28）：https://news.adobe.com/news/2025/10/adobe-max-2025-express-ai-assistant ；MAX 2025 总览（2025-10-28）：https://news.adobe.com/news/2025/10/adobe-max-2025-news
- [S30] Adobe 帮助页，Express AI Assistant FAQ 与概览（2026 年中，经搜索摘要）：https://helpx.adobe.com/express/web/ai-assistant/adobe-express-ai-assistant-faq.html ；https://helpx.adobe.com/express/web/ai-assistant/adobe-express-ai-assistant-overview.html ；Adobe 社区，Express 企业版新功能（2026-01-16）：https://community.adobe.com/announcements-327/adobe-express-for-enterprise-new-features-announced-at-max-2025-1546582
- [S31] Acrobat Studio：上市价（eWeek，2025-08）https://www.eweek.com/news/adobe-acrobat-studio/ ；生成演示文稿（2026-01-21）https://news.adobe.com/news/2026/01/adobe-acrobat-studio-transforms ；生产力代理（2026-05-06）https://news.adobe.com/news/2026/05/adobes-new-productivity-agent ；知识库与分析器（2026-09-09）https://news.adobe.com/news/downloads/pdfs/2026/09/acrobat-press-release-9-9-26-final.pdf
- [S32] Adobe 接入聊天平台：ChatGPT（2025-12-10）https://news.adobe.com/news/2025/12/adobe-photoshop-express-acrobat-chatgpt ；Claude（2026-04-28）https://blog.adobe.com/en/publish/2026/04/28/adobe-for-creativity-connector ；Gemini 与 Claude 扩展（2026-09-24）https://blog.adobe.com/en/publish/2026/09/24/adobe-comes-to-gemini-expands-what-you-can-do-in-claude ；ChatGPT 交互式编辑（2026-09-29）https://blog.adobe.com/en/publish/2026/09/29/openai-devday-2026-introducing-hands-on-editing-adobe-plugin-chatgpt
- [S33] Firefly：企业版与赔付（2023-06-08）https://news.adobe.com/news/news-details/2023/adobe-brings-firefly-and-express-to-enterprises ；独立应用与订阅（2025-02-12）https://news.adobe.com/news/2025/02/firefly-web-app-commercially-safe ；Boards 与第三方模型（2025-04-24）https://blog.adobe.com/en/publish/2025/04/24/adobe-firefly-next-evolution-creative-ai-is-here ；移动应用（2025-06）https://news.adobe.com/news/2025/06/adobe-firefly-revolutionizes-creative-ideation-new-mobile-app ；无限生成促销（2026-02-02）https://blog.adobe.com/en/publish/2026/02/02/create-unlimited-generations-adobe-firefly-all-in-one-creative-ai-studio ；创意代理（2026-04、2026-06）https://news.adobe.com/news/2026/04/adobe-new-creative-agent ；https://news.adobe.com/news/2026/06/adobe-unveils-major-expansion
- [S34] Express 历史：改名（2021-12-13）https://www.schneider.im/adobe-spark-rebranded-as-adobe-express ；接入 Firefly 的新版发布（2023-08-16）https://appleinsider.com/articles/23/08/16/adobe-express-with-ai-firefly-app-is-available-worldwide ；移动应用（2024-04-18）https://news.adobe.com/news/news-details/2024/all-new-adobe-express-mobile-app-with-firefly-ai-now-available-to-millions-empowering-them-to-create-standout-content-on-the-go
- [S35] Creative Cloud Pro 提价（2025-05-20 报道，2025-06-17 生效）：https://appleinsider.com/articles/25/05/20/adobe-hikes-creative-cloud-prices-with-a-rebrand-no-one-asked-for ；https://www.theregister.com/2025/05/20/adobe_price_hikes/
- [S36] GenStudio for Performance Marketing（2024-10-14）：https://news.adobe.com/news/2024/10/101424-genstudio-for-performance-marketing ；Summit 2026（martech.org，2026-04）：https://martech.org/adobe-rebrands-experience-cloud-as-cx-enterprise-goes-all-in-on-ai-agents/
- [S37] 卖方反应：freemium 转向（2026-06）https://seekingalpha.com/news/4602933-adobes-leadership-transitions-and-freemium-push-create-uncertainty-analysts ；摩根士丹利降至减持（2026-07）https://seekingalpha.com/news/4615852-adobe-drops-to-underweight-due-to-leadership-changes-ai-disruption-risks-morgan-stanley ；https://www.tikr.com/blog/adobe-nyse-stock-slides-after-morgan-stanley-slashes-price-target-and-downgrades ；富国银行降至减持（2026-10-12）https://investing.com/news/stock-market-news/why-is-adobe-stock-sliding-today-93CH-4944223
- [S38] SmartCompany（2026-08-04，转述 OneLittleWeb 的访问量统计）：https://www.smartcompany.com.au/artificial-intelligence/canva-beats-claude-grok-gemini-worlds-second-most-visited-ai-platform-chatgpt/
- [S39] AI 环境：ChatGPT Images 2.0（PetaPixel，2026-04-21）https://petapixel.com/2026/04/21/openai-claims-chatgpt-images-2-0-can-think/ ；Claude Design 与股价反应（TechCentral，2026-04）https://www.techcentral.ie/figma-and-adobe-shares-fall-after-athropic-releases-design-tool/ ；Canva 进入 Gemini（The Next Web，2026-05-20）https://thenextweb.com/news/canva-google-gemini-connected-app-design
- [S40] Adobe Express 教育版 4,300 万师生（2022-10）：https://ecommercenews.com.au/story/adobe-express-reaches-over-43-million-students-and-teachers
- [S41] Photoshop iPhone 版免费（TechCrunch，2025-02-25）：https://techcrunch.com/2025/02/25/adobe-launches-a-photoshop-iphone-app/ ；网页版 Photoshop FAQ（2026-06-24 更新，经搜索摘要）：https://helpx.adobe.com/photoshop/web/get-set-up/learn-the-basics/adobe-photoshop-faq.html
- [S42] Adobe 完成收购 Topaz Labs（2026-09-23）：https://blog.adobe.com/en/publish/2026/09/23/adobe-completes-acquisition-of-topaz-labs
- [S43] 股价：腾讯前复权日线 https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=usADBE.OQ,day,2026-06-05,2026-06-22,20,qfq
- [S44] 已有评审：[2026-10-12 复核](ADBE_Adobe.md)；[2026-10-07 独立估值](../../exp_independent_us3_20261007/companies/ADBE_Adobe.md)
