# Adobe 与 Figma 的竞争关系：Adobe 做了什么、没做什么、影响多大（2026-10-12）

## 结论摘要

1. **关系**：Figma 是 Adobe 出价约 200 亿美元没买成、随后放弃自研对抗的对手。Adobe 已经退出界面与产品设计这一品类：XD 从 2023-05 起只做维护，2024-01 表态不再投入，FY25 年报的产品清单里没有任何界面设计、原型或设计转代码的工具 [S13][S23][S33]。
2. **规模**：Figma 2026 年收入指引 14.63～14.67 亿美元（+39%），相当于 Adobe FY26E 收入的 5.5%；一年的收入增量约 4.1 亿，相当于 Adobe FY26 有机净新增 ARR（约 21 亿）的 19% [S1][S15]。
3. **直接替代很小**：Figma 的增长主要来自 Adobe 从未拥有的席位（开发者、产品经理）和 AI 用量。本文估计它每年从 Adobe 现有收入里直接拿走的不到 0.5 亿美元，不到 Adobe 收入的 0.2%。Adobe 输掉的是一个品类的机会，不是存量收入。
4. **Adobe 的应对是绕开，不是对抗**：做了 AI 情绪板（Firefly Boards）、把工具接进 ChatGPT／Claude／Gemini、反过来给 Figma 做插件；没有做界面设计、原型、设计转代码；Illustrator 网页版宣布近 5 年后帮助页仍标注 beta；最近一次电话会一次也没提 Figma、协作或 Boards [S17][S25][S26][S28][S31]。
5. **AI 的作用**：Figma 收入增速连续三个季度加快到 +48%，但非 GAAP 毛利率从 92% 掉到 85%，股价较上市高点跌 84%，市值约 120 亿美元，已低于 Adobe 当年的出价；它的 10-Q 新增了"第三方代理绕过席位定价"的风险因素 [S1][S2][S48]。对 Adobe 而言，Figma 被牵制是小幅减压，但同一股力量（模型厂商把设计做成聊天产品的功能）才是 Adobe 的主要威胁。
6. **未来 3～5 年**：最可能的情形是 Figma 每年从 Adobe 创意专业收入里拿走 0.5～1.0 亿（拖累 Adobe 总收入增速 0.2～0.4 个点）；坏情形是 FY28～FY31 每年 2.5～3.5 亿（0.8～1.1 个点）。
7. **对估值**：已包含在既有情景里。不因 Figma 上调坏情景概率，也不下调基准路径。即使坏情形全部兑现，基准情景 V 从 361 降到约 349～351 美元，概率加权 V 从 282 降到约 277，P/V 从 0.86 升到 0.87。
8. **跟踪**：Figma Q3 财报（预计 11 月初，日期未公布）的净留存率与 2027 年口风；Buzz、Sites 是否转正和 Content 席位是否开售；Adobe MAX 2026（11-10 至 11-12）；Adobe 创意与营销订阅收入增速。

口径：美元，"亿"即 1 亿美元。Adobe 财年止于 11 月末（FY26 止于 2026-11-27），Figma 财年为自然年。价格取 2026-10-09 收盘：ADBE 242.27、FIG 22.50。带 [S#] 的是有来源的事实；标"公司说法"的是管理层表述；标"本文估计"或"本文判断"的是分析者的推断，没有公司披露支撑。Adobe 的情景与估值框架沿用同批次的[独立估值复核](ADBE_Adobe.md)，本文不重做估值，只做敏感性。Canva 由另一份研究负责，本文只在三方交叉处点到。

## 1. 关系与时间线

### 1.1 时间线

| 时间 | 事件 | 来源 |
|---|---|---|
| 2012 | Dylan Field 与 Evan Wallace 创立 Figma；2015 年公开发布 Figma Design，2017 年开始收费 | [S8][S11] |
| 2016 起 | Adobe 推出 XD，对抗 Sketch 和 Figma（行业常识，未逐项取证） | — |
| 2021 | Figma 推出白板 FigJam；Adobe 在 2021-10-26 的 MAX 大会宣布 Photoshop 和 Illustrator 的网页版 | [S5][S31] |
| 2022-09-15 | Adobe 宣布以约 200 亿美元（现金与股票各半）收购 Figma。Adobe 披露：Figma 2022 年预计净新增 ARR 约 2 亿，年末 ARR 超过 4 亿，净留存率高于 150%，毛利率约 90% | [S11] |
| 2023-05 | XD 进入维护模式，不再开发新功能，不再单独销售 | [S33] |
| 2023 年内 | Figma 推出面向开发者的 Dev Mode | [S5] |
| 2023-11-28 | 英国 CMA 临时结论：约 80% 的专业产品设计市场使用 Figma；交易会消除 XD 对 Figma 的约束，并消除 Figma 对 Photoshop、Illustrator 的潜在威胁 | [S35] |
| 2023-12-18 | 双方终止合并，理由是看不到获得欧盟和英国批准的路径。Adobe 付给 Figma 10 亿美元分手费，计入 Adobe FY24 费用 | [S12][S13] |
| 2024-01-30 | Adobe 发言人：XD 处于维护模式，"没有进一步投入的计划" | [S33] |
| 2024 | Figma 推出 Slides；全年收入 7.49 亿（+48%） | [S8] |
| 2025-03 | Figma 调整定价与席位：最贵的 Full 席位提价，推出多产品席位，席位升级改为须管理员批准 | [S5] |
| 2025-05-07 | Config 2025：一次发布 Make、Draw、Sites、Buzz 四款产品，产品线翻倍 | [S7][S22] |
| 2025-07-31 | Figma 在纽交所上市，发行价 33 美元，首日收 115.50（+250%），08-01 盘中最高 142.92 | [S5][S36][S48] |
| 2025-09-24 | Adobe 的协作式 AI 情绪板 Firefly Boards 正式发布 | [S44] |
| 2025-10-03 | Figma 收购 Weavy（对价 0.85 亿，另发约 0.44 亿限制性股票），改名 Figma Weave | [S5] |
| 2025-12-10 | Adobe 把 Photoshop、Express、Acrobat 接入 ChatGPT | [S27] |
| 2026-03-18 | Figma 开始执行 AI 积分上限并出售加购包；同日谷歌更新 Stitch，FIG 当日跌 8.0% | [S3][S37][S48] |
| 2026-04-14／04-17 | Anthropic 首席产品官 Mike Krieger 辞去 Figma 董事；三天后 Anthropic 发布 Claude Design，FIG 当日跌 6.9% | [S9][S38][S48] |
| 2026-04-28 | Adobe 在 Claude 上线"Adobe for creativity"连接器（50 多个工具） | [S25] |
| 2026-06-23 至 06-25 | Config 2026：Figma agent、Code Layers、Motion、Shaders、Weave 工具进入 Design | [S18] |
| 2026-08-05 | Figma Q2：收入 3.70 亿（+48%），全年指引上调 0.40 亿；次日股价跌 14.8% | [S1][S41][S48] |
| 2026-09-24 | Adobe 进入 Gemini；Claude 连接器扩到 80 多个工具 | [S26] |
| 2026-10-06 | Figma agent 结束 beta，开始消耗 AI 积分 | [S19] |
| 2026-10-09 | FIG 22.50 美元，市值约 120 亿；ADBE 242.27 美元，市值约 943 亿 | [S2][S48] |

### 1.2 是纯竞争，还是既竞争又互补

**本文判断：现在更像上下游，而不是正面对手；竞争发生在 Figma 向外扩张的边缘。**

| 维度 | 现状 | 证据 |
|---|---|---|
| 双方怎么称呼对方 | 两家的年报都不把对方点名为竞争对手。Figma 年报里出现 Adobe 的地方只有"被放弃的合并"；Adobe FY25 年报里出现 Figma 的地方只有分手费和一桩证券诉讼 | [S5][S13] |
| Adobe 做给 Figma 的插件 | Adobe 自己把工具做进 Figma：Firefly Enterprise 与 GenStudio 插件（在 Figma 里用 Firefly 生成图像，并可把 Figma 画框转成 Photoshop 格式）；GenStudio for Performance Marketing 的 Figma 插件（发布说明记在 2025-10-16 版本，经搜索摘要）；AEM 的"从 Figma 生成内容片段"技能 | [S28][S29][S30] |
| Adobe 的官方措辞 | AEM 文档写明"模块化体验的视觉设计通常在 Figma 里完成"。Adobe 把 Figma 当作既定的上游设计工具 | [S30] |
| 文件互通 | 未查到 Figma 原生打开 PSD、AI 或 XD 文件的官方功能，也未查到 Adobe 当年承诺的 Adobe Fonts 和 Adobe Stock 接入 Figma 的落地。互通主要靠 SVG、PDF、图片和第三方插件（本项未逐一核实） | — |
| 客户重叠 | 高。2025-03 有 95% 的财富 500 强、78% 的福布斯全球 2000 强使用 Figma；这些公司基本也是 Adobe 的客户 | [S8] |
| 预算归属 | 大体分开。Figma 的席位由产品与研发部门买单：三分之二的月活用户不是设计师，约 30% 是开发者。Adobe Creative Cloud 由创意、市场和 IT 部门买单。两者在设计团队这里重合 | [S5][S8] |
| 竞争点 | Figma 在 2025～2026 年推出的 Draw、Buzz、Weave、Motion 分别伸向 Illustrator、Express／GenStudio、Firefly、After Effects 的用途 | [S5][S18] |

一桩旧账还没结：有股东起诉 Adobe 在 2021-07 至 2022-09 期间对"来自 Figma 的竞争"以及自家产品的应对能力作了误导性陈述。法院在 2025-03-27 驳回，2025-11-07 拒绝原告修改诉状，原告正在上诉 [S16]。

## 2. 产品重叠地图

### 2.1 逐项对应（以 2026-10-12 在售与公开测试为准）

| Figma 产品 | 状态 | 做什么 | 对应的 Adobe 产品 | 归类 | Adobe 侧敞口（本文估计） |
|---|---|---|---|---|---|
| Figma Design（含原型、设计系统） | 在售，核心 | 界面与产品设计 | XD（维护模式）。早年这是 Photoshop、Illustrator 的用途 | **Adobe 已失去** | 存量收入约为 0：XD 年收入从未超过 0.15～0.17 亿 [S34]。机会成本是 Figma 的全部收入 |
| Dev Mode、MCP 服务、Code Connect | 在售 | 设计交付开发，代理读写设计稿 | 无 | 互不相干 | 0 |
| Figma Make；Code Layers | Make 在售；Code Layers 自 2026-07 起候补早期访问 | 提示词生成原型和网页应用，代码与设计同画布 | 无 | 对 Adobe 互不相干；Figma 在这里对上 Claude Design、Stitch 和各类编程代理 | 0 |
| FigJam | 在售 | 白板、流程图 | Firefly Boards（定位是 AI 情绪板，不是通用白板） | 轻度重叠 | 很小 |
| Figma Slides | 在售 | 演示文稿 | Express 的演示功能 | 边缘 | 很小 |
| Figma Draw | 在售，含在 Full 席位里 | 矢量插画：笔刷、路径文字、图案填充 | Illustrator | **进入腹地**（图标、产品插画一端） | 计入下文 A 池 |
| 画布内 AI 修图（去背景、擦除、扩图）与 Weave 工具 | 在售；Weave 工具 2026-06 进入 Design | 基础修图、换背景、改比例 | Photoshop 的基础用途 | 进入腹地边缘 | 计入 A 池 |
| Figma Buzz | **仍是 beta** [S20] | 品牌模板，按表格批量生成社媒图和广告 | Express、GenStudio for Performance Marketing，以及 Illustrator／InDesign／Photoshop 的营销物料用途 | **进入腹地，但尚未转正** | 计入 B 池 |
| Figma Sites 与 Payload CMS | **Sites 仍是 beta** [S20] | 设计稿直接发布成网站，带内容管理 | 无直接对应；AEM Sites 面向大企业 | 基本不相干；长期可能成为 AEM 的中低端替代 | 很小 |
| Figma Weave | 在售，独立画布；2026-09-17 起可与 Figma 画框双向同步 [S19] | 把多家图像、视频模型串成可复用的工作流 | Firefly 应用、Firefly Boards、Project Graph | **正面竞争**，双方都是新业务 | C 池 |
| Motion、Shaders、3D transforms | Motion 公开 beta（2026-06-24 起，09-30 加入音轨与 Lottie 导出）；3D 候补 [S18][S19] | 界面动效与特效 | After Effects 的界面动效用途 | 进入腹地边缘 | D 池 |
| Figma agent、Skills、生成式插件 | 2026-06-23 开放，10-06 结束 beta 并开始计费 [S18][S19] | 画布内的代理 | Firefly AI Assistant（2026-04 beta）、Photoshop 与 Express 的 AI 助手 | 方向相同，场地不同 | — |

席位价格（2026-10-12 官网）：Professional 档 Full／Dev／Collab 为每月 16／12／3 美元，Organization 档 55／25／5，Enterprise 档 90／35／5；Full 席位每月含 3,000～4,250 个 AI 积分 [S20]。2025 年年报里预告的 Content 席位（面向营销人员）在定价页上仍未出现 [S5][S20]。对照：Adobe Creative Cloud Pro 个人版北美标价每月 69.99 美元 [S46]。也就是说，Figma 企业版一个设计师席位的标价已经高于 Adobe 全家桶个人版。

### 2.2 Adobe 的收入敞口有多大

Adobe 不披露分产品收入。下表全部是本文估计，基数取同批次评审的拆法：FY26E 创意专业约 120 亿、Acrobat 与 Express 74.8 亿、营销云约 62 亿。

| 池 | 是谁的钱 | 估计规模 | 占 Adobe 收入 | Figma 现在的位置 |
|---|---|---|---|---|
| A | 数字产品与界面设计师手里的 Creative Cloud 席位（用 Photoshop、Illustrator 处理图片、图标、插画） | 10～14 亿 | 4%～5% | 已是这些人的主工具。Draw 和画布内修图在减少他们打开 Adobe 的次数 |
| B | 品牌与营销设计团队做社媒图、广告、物料所用的 Creative Cloud 席位，加上 Express | 25～35 亿 | 9%～13% | Buzz、Slides、Sites 指向这里；Buzz 和 Sites 发布 17 个月仍是 beta |
| C | AI 生成与画布：Firefly 应用、积分包、Boards | 约 4 亿（Firefly ARR 在 Q2 末"接近 3 亿"，Q3 环比 +40%）[S17][S47] | 1.5% | Weave 正面竞争 |
| D | 界面动效（After Effects 的一部分用途） | 不到 3 亿 | 约 1% | Motion 还在 beta |
| 互不相干 | Acrobat／PDF、视频（Premiere、Frame.io）、摄影（Lightroom）、3D、印刷排版（InDesign）、营销云的数据与旅程编排 | 约 215 亿 | 约 81% | 没有产品 |

A 池的算法：Figma 月活超过 1,300 万，其中约三分之一是设计师，即约 430 万人（含免费用户和学生）[S8]；假设其中 150～200 万人同时付费订阅 Creative Cloud、人均每年 600～700 美元，得 9～14 亿。两个假设都没有公司披露支撑。

读法：Figma 现有产品线"够得着"的 Adobe 收入约 40～55 亿，占 Adobe 收入的 15%～21%；但它已经站稳的只有 A 池，约 4%～5%。

## 3. Figma 的经营数据

### 3.1 近 8 个季度（SEC 原文）

| 季度 | 收入（亿） | 同比 | 非 GAAP 毛利率 | GAAP 毛利率 | GAAP 营业利润（亿） | 非 GAAP 营业利润（亿）与利润率 | 经营现金流（亿） | 自由现金流（亿） | SBC（亿） | 净留存率 | 年付 >1 万美元客户 | 年付 >10 万美元客户 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2024 Q3 | 1.986 | +50% | 92% | 91% | −0.47 | 0.48，24% | 0.62 | 0.60 | 0.88 | 131% | 9,762 | 876 |
| 2024 Q4 | 2.169 | +50% | 92% | 92% | 0.52 | 0.56，26% | 0.73 | 0.71 | 0.00 | 134% | 10,517 | 963 |
| 2025 Q1 | 2.282 | +46% | 92% | 91% | 0.40 | 0.40，18% | 0.97 | 0.95 | 0.00 | 132% | 11,107 | 1,031 |
| 2025 Q2 | 2.496 | +41% | 90% | 89% | 0.02 | 0.11，5% | 0.62 | 0.61 | 0.07 | 129% | 11,906 | 1,119 |
| 2025 Q3 | 2.742 | +38% | 86% | 69% | −11.37 | 0.34，12% | 0.51 | 0.49 | 11.38 | 131% | 12,910 | 1,262 |
| 2025 Q4 | 3.038 | +40% | 86% | 82% | −1.96 | 0.44，14% | 0.40 | 0.38 | 2.18 | 136% | 13,861 | 1,405 |
| 2026 Q1 | 3.334 | +46% | 82% | 79% | −1.37 | 0.52，16% | 0.97 | 0.89 | 1.69 | 139% | 15,218 | 1,525 |
| 2026 Q2 | 3.701 | +48% | 85% | 84% | −1.17 | 0.36，10% | 0.61 | 0.53 | 1.48 | 136% | 15,964 | 1,635 |

来源：[S1][S3][S4][S6][S7][S8][S10]。说明：

- 2025 Q3 的 GAAP 亏损含上市触发的一次性股权激励费用 9.76 亿 [S6]。2024 Q3、Q4 的经营现金流由 XBRL 累计数相减得到，含与 Adobe 交易相关的税费影响 [S10]。
- 净留存率的口径是年付 1 万美元以上的客户，12 个月前的 ARR 对比现在的 ARR，含扩张、收缩和流失 [S1]。
- 付费客户总数：2025-03 约 45 万，2026-03 约 69 万（+54%）；2026 Q2 未披露 [S3][S8]。年付 100 万美元以上的客户在 2025 年末有 67 家 [S4]。
- 年付 1 万美元以上客户的季度净增：2026 Q1 为 1,357 家，Q2 回落到 746 家，低于去年同期的 799 家。

### 3.2 毛利率、利润与现金流

- **AI 成本吃掉 7 个点毛利率**。非 GAAP 毛利率从 2025 Q1 的 92% 降到 2026 Q1 的 82%，Q2 回升到 85%。2026 Q2 营业成本同比 +117%，增加的 0.33 亿里有 0.27 亿是"与 AI 和付费用户用量相关的基础设施与托管成本"；上半年合计多出 0.61 亿 [S2]。公司说法：Q2 的回升来自 AI 积分开始收费；beta 阶段的产品（agent、Motion、Code Layers）由公司承担推理成本而没有对应收入，毛利率近期会逐季波动；正在用模型路由和自研模型降成本 [S21]。
- **GAAP 亏损，原因是股权激励**。2026 上半年 SBC 3.17 亿，占收入 45%；GAAP 营业亏损 2.55 亿；非 GAAP 营业利润 0.88 亿（利润率 13%）。尚未确认的限制性股票费用还有 14 亿，在 3.4 年内摊销，不含 CEO 的专项激励 [S1][S2]。
- **现金流为正**。近四个季度自由现金流 2.29 亿（利润率 18%）；扣掉 SBC 后为负。账上现金与有价证券 16.7 亿，无有息负债 [S1]。

### 3.3 指引

| 项目 | 指引（2026-08-05） | 含义 |
|---|---|---|
| 2026 Q3 收入 | 3.73～3.75 亿 | 同比 +36%；环比只增 1% |
| 2026 全年收入 | 14.63～14.67 亿 | 同比 +39%；较上一次指引上调 0.40 亿 |
| 隐含 2026 Q4 收入 | 约 3.87 亿（推算） | 同比约 +28% |
| 2026 全年非 GAAP 营业利润 | 1.25～1.35 亿 | 利润率 9%；收入上调而利润不动 |

来源：[S1]。全年指引今年已上调两次：2 月为 13.66～13.74 亿，5 月上调 0.55 亿，8 月再上调 0.40 亿 [S3][S4]。公司说法：下半年增速回落是因为开始与去年 3 月的定价与席位调整同期相比；指引没有计入仍在 beta 或早期访问的产品 [S21]。Figma 的指引历来保守，Q2 实际比指引上限高 6%。

### 3.4 上市以来的股价与市值

| 日期 | 收盘价 | 事件与原因 |
|---|---|---|
| 2025-07-31 | 115.50 | 上市首日，发行价 33 美元。按发行价的市值约 161 亿，计入全部稀释后约 193 亿，与 Adobe 当年出价相当 [S36] |
| 2025-08-01 | 122.00 | 收盘最高；盘中最高 142.92 |
| 2025-09-04 | 54.56 | 首份财报后单日 −19.9%（原因未逐项核实；财报同时公布了提前解禁安排 [S7]） |
| 2025-12-31 | 37.37 | — |
| 2026-03-18 | 25.26 | −8.0%，谷歌更新 Stitch，主打"用提示词做界面" [S37] |
| 2026-04-08 至 04-10 | 18.16 | 三天 −14.3%，Anthropic 发布 Mythos 模型引发软件股抛售 [S38] |
| 2026-04-17 | 18.92 | −6.9%，Anthropic 发布 Claude Design；三天前其首席产品官辞任 Figma 董事 [S9][S38][S42] |
| 2026-05-15 | 22.92 | +13.2%，Q1 超预期并上调指引 [S39] |
| 2026-06-25 | 16.84 | 收盘最低，当日 −9.7%，Config 大会结束次日（原因未查到） |
| 2026-08-06 | 23.97 | −14.8%，Q2 收入超预期，但市场盯住 AI 成本、Q3 指引环比只增 1%、利润指引不上调 [S41] |
| 2026-10-09 | 22.50 | 较发行价 −32%，较收盘高点 −82%，较盘中高点 −84%，年内 −40% |

价格来自腾讯前复权日线 [S48]。按 2026-07-31 的 5.33 亿股（A 类 4.551 亿、B 类 0.779 亿）计，市值约 120 亿，扣现金后企业价值约 103 亿，相当于 2026 年指引收入的 7.0 倍 [S2]。Adobe 在 2022 年出的 200 亿对应当时约 4 亿的 ARR，是 50 倍。Figma 现在的收入是当时的 3.7 倍，市值却只有当年出价的六成。

同期 ADBE 年内 −31%。两只股票在 03-18（ADBE −3.2%）和 04-17（ADBE −1.5%）同日下跌。本文判断：市场把它们归进同一类"会被 AI 替代的设计软件"；未查到把 Adobe 这两天的跌幅归因于 Stitch 或 Claude Design 的报道。

### 3.5 与 Adobe 的可比口径

| 指标 | Figma | Adobe | Figma 相当于 Adobe 的 |
|---|---|---|---|
| FY25 收入 | 10.56 亿（+41%） | 237.69 亿（+11%） | 4.4% |
| FY26E 收入 | 14.65 亿（+39%） | 266.0 亿（+12%） | 5.5% |
| FY25 年增量 | 收入 +3.07 亿 | 净新增 ARR 约 26.0 亿（数字媒体约 19.8 亿），均为按披露增速推算 | 12%（对数字媒体为 15%） |
| FY26E 年增量 | 收入 +4.09 亿 | 净新增 ARR 指引约 26.2 亿，剔除 Semrush 约 4.8 亿后有机约 21.4 亿 | 16%（对有机为 19%） |
| 最近一季增速 | +48% | 创意与营销订阅收入 +13%（剔除 Semrush 约 +10%） | — |
| 市值 | 约 120 亿 | 约 943 亿 | 12.7% |

来源：[S1][S4][S14][S15]。口径提示：Figma 不按季披露 ARR，这里用收入增量对比 Adobe 的净新增 ARR，会低估 Figma 一侧。另一个读法：如果当年收购完成，Adobe FY26 的 ARR 增速会高出约 1.6 个点（4.09 ÷ 256.6）。

### 3.6 Figma 的增长有多少是"从 Adobe 手里拿走的"

**本文估计：每年不到 0.5 亿美元，占 Figma 年增量的 5%～10%，占 Adobe 净新增 ARR 的 1%～2%。**依据：

1. **XD 没有东西可拿**。XD 年收入从未超过 0.15～0.17 亿，2023 年已只剩约 5 人维护 [S34]；UX Tools 2024 年调查里只有 1.4% 的设计师还在用 [S43]。
2. **界面设计的份额之争在 2023 年就结束了**。CMA 当时认定 Figma 约占 80% [S35]。之后的增长不再来自抢份额。
3. **增长来自非设计师**。三分之二的月活不是设计师，约 30% 是开发者 [S5][S8]；公司说法：2024 年净留存率回升靠的是 Dev Mode [S8]，2026 Q1 超预期靠的是"整个组织范围的席位扩张"和 Make、MCP、Weave 的采用 [S3]；一家大型科技客户里工程师持有的付费席位已经多过设计师 [S21]。
4. **增长来自涨价和 AI 用量**。2025-03 Full 席位提价 [S5]；2026-03-18 起 AI 积分收费，Q2 末年付 1 万美元以上的客户里超过 80% 每周消耗积分 [S1]。
5. **伸向 Adobe 的产品不单独收费**。Draw、Buzz、Slides 都含在已有席位里。它们如果抢走用户，表现为 Adobe 一侧的席位流失，而不是 Figma 一侧的新增收入，所以从 Figma 的报表上看不出来。

对 2026 年约 4.1 亿增量的粗略拆分（本文估计，Figma 不披露分席位收入）：非设计师席位 35%～45%，设计师席位增长与涨价 30%～40%，AI 积分与新增小团队 15%～25%；其中直接替代 Adobe 支出的部分不超过 5%～10%。

## 4. Adobe 的应对

### 4.1 逐条清单

| # | 时间 | 动作 | 内容 | 现状与效果证据 |
|---|---|---|---|---|
| 1 | 2023-05 至今 | **处置 XD** | 进入维护模式，只修 bug 和安全问题，不再单独销售 | 2024-01-30 发言人称"没有进一步投入的计划"；2026-10-12 产品页仍写"目前处于维护模式"，未公布终止日期；FY25 年报产品清单里没有 XD [S13][S23][S33] |
| 2 | 2022-09 至 2023-12 | **收购 Figma** | 约 200 亿美元 | 被欧盟和英国监管挡下，付 10 亿分手费 [S12][S13] |
| 3 | 2023-12-18 | **收购失败后的表态** | 时任数字媒体业务总裁 Wadhwani："会寻找合作方式，服务共同客户" | 之后的动作确实是合作而不是对抗，见第 4 条。分析师当时建议改买 Miro、Webflow 或 InVision，Adobe 没有买 [S12][S34] |
| 4 | 2025 至 2026 | **给 Figma 做插件** | Firefly Enterprise 与 GenStudio 的 Figma 插件；GenStudio for Performance Marketing 的 Figma 插件；AEM 从 Figma 导入设计 | 承认 Figma 是上游设计工具，把 Adobe 定位成它下游的生成与投放环节。未披露使用量 [S28][S29][S30] |
| 5 | 2024 至今 | **Firefly Boards（原 Project Concept）** | 协作式 AI 情绪板：多人在无限画布上用 Adobe 与第三方模型生成、拼贴图像和视频。前身 Project Concept 的预览时间未取证；2025-04-24 公开 beta，2025-09-24 正式发布，2025-10-28 加入放大与 2D 转 3D，2026-03 加入引导流程 | 这是 Adobe 最接近"协作画布"的产品，对标的是 FigJam 和 Weave，不是 Figma Design。**Adobe 没有披露过用户数**；Q3 FY26 电话会全文没有出现 Boards 一词 [S17][S24][S32][S44] |
| 6 | 2021-10 至今 | **Photoshop、Illustrator 的网页版与协作** | 2021 年宣布网页版。Photoshop 在 2025-01 开始私测"实时共同编辑" | **Illustrator 网页版到 2026-04 的帮助页仍标注 Beta**，协作方式是邮件邀请编辑，未见多人实时编辑；Photoshop 共同编辑是否转正未查到 [S31][S45] |
| 7 | 持续 | **Express 的团队与品牌功能** | 团队版每人每月 7.99 美元（首年 4.99），含共享品牌库和管理后台；2025-10 加入 AI 助手 | 主要针对 Canva，也是挡 Figma Buzz 的防线。由另一份研究展开 [S24] |
| 8 | 2025-12 至 2026-09 | **把工具接进第三方 AI** | ChatGPT（2025-12-10）；Claude（2026-04-28，50 多个工具，09-24 扩到 80 多个并加入 Acrobat）；Gemini（2026-09-24） | 公司说法：让用户"在工作的界面里直接用 Adobe 的工具"。可以游客身份使用，登录后额度更高，未披露定价。Figma 做了同样的事（ChatGPT 应用、Claude 里的 MCP 应用）[S4][S25][S26][S27] |
| 9 | 2025-10 至 2026-04 | **自家 AI 助手与工作流** | Photoshop、Express、Firefly 的对话式助手（MAX 2025）；节点式工作流 Project Graph（2025-11 公布，现状未核实）；Firefly AI Assistant（2026-04 beta） | 对应 Figma agent 与 Weave [S24][S32][S51] |
| 10 | 2025-06 与 2026-06 | **定价与 freemium** | 2025-06 北美全家桶改名 Creative Cloud Pro，月费 69.99 美元，另设 Standard 档。2026-06 宣布推迟下半年的调价，把流量导向免费版 | 创意 freemium 月活超过 1 亿（+70%），代价是 Q3 净新增 ARR 同比 −37% [S17][S46][S47] |
| 11 | 2025-11 至 2026-09 | **收购** | Semrush（约 19 亿，搜索与 AI 可见度）；Topaz Labs（约 3.4 亿，图像增强） | 都不在协作或产品设计领域 [S16][S50] |
| 12 | 2026-04-19 至 04-22 | **Adobe Summit 2026** | 体验云改名 CX Enterprise，主打营销代理 | 未查到界面设计相关的发布 [S49] |

Adobe MAX 2026 在 11-10 至 11-12 举行，尚未发生。

### 4.2 Adobe 没有应对或已经放弃的地方

1. **界面与产品设计、原型**：放弃。XD 之后没有后继产品。
2. **设计转代码、面向开发者和产品经理的席位**：没有产品。未查到 Adobe 在 2025 年 MAX、2026 年 Summit 或其它场合发布过任何这类工具。这正是 Figma 增长最快的部分。
3. **专业设计工具的多人实时协作**：实质上没有做成。Illustrator 网页版宣布近 5 年仍是 beta。
4. **协作领域的收购**：收购 Figma 失败之后没有再出手。
5. **管理层的注意力**：Q3 FY26 电话会全文，Figma、Canva、XD、Illustrator、Boards、"协作"的出现次数都是 0，Firefly 出现 35 次 [S17]。Adobe 的叙事是 AI、freemium 和代理，不是协作。

**本文判断**：Adobe 的选择是理性的。重新进入一个对手占八成份额、自己已经失败过一次的品类，胜算很低；而这个品类本身正被模型厂商冲击（见第 5 节）。代价是 Adobe 在设计软件里增长最快的一块上没有任何参与。

## 5. AI 对这场竞争的改变

### 5.1 Figma 自己会不会被绕过

| 证据（2026 年） | 指向 |
|---|---|
| 收入增速 38% → 40% → 46% → 48%，净留存率 131% → 136% → 139% → 136%，付费客户 +54% [S1][S3][S4] | **到目前为止没有被绕过**。AI 把更多非设计师带进了 Figma |
| 编程代理生成的界面可以导回 Figma 画布（Claude Code、Codex、Cursor 等）；2026 Q1 MCP 周活环比增长 5 倍，使用 MCP 的大客户 Full 席位增速快约 70% [S3] | 公司说法：代理是入口，不是替代 |
| 非 GAAP 毛利率 92% → 82% → 85%；营业成本同比翻倍 [S1][S2] | AI 让 Figma 的生意变差：同样的收入要付更多算力钱 |
| 10-Q 新增风险因素（FY25 年报里没有，2026 Q1 的 10-Q 起出现）：第三方代理"可能减少同等产出所需的付费席位"，"把工作流从我们的界面转移到第三方代理的界面"；公司正在评估对 API 和 MCP 按用量收费 [S2] | 公司自己承认席位模式受威胁 |
| 股价：Stitch 当日 −8.0%，Claude Design 当日 −6.9%，Q2 财报次日 −14.8%，年内 −40% [S48] | 市场按"会被绕过"定价 |
| 指引：Q3 环比只增 1%，隐含 Q4 同比约 +28% [S1] | 增速高点可能已过，但 Figma 的指引一贯保守 |
| Claude Design 可导出 PDF、PPTX、HTML，并可转到 Canva 继续编辑；没有直接导出到 Figma（二手报道，官方原文未能打开）[S40] | 模型厂商选了 Canva 而不是 Figma 做下游 |
| 管理层：被问到 Claude Design 和各类"氛围编程"平台时，Field 说"它们解决的是不同的问题，有些主要是编程工具"；"当代码成为大宗商品，设计就是竞争优势" [S3][S21] | 公司说法 |
| 2026-10-06 Figma agent 开始消耗 AI 积分 [S19] | Figma 在把收费从"按人"挪向"按用量" |

**本文判断**：2026 年的数据支持"还没被绕过"，不支持"不会被绕过"。Figma 眼下的增长一部分来自涨价和 AI 积分的首年效应，这两项在 2027 年都会进入同比基数。真正的检验是 2027 年的净留存率和席位数。

### 5.2 对 Adobe 是减压还是加压

- **减压的一面**：Figma 要守住自己的地盘。2026 年 Config 的发布几乎全部指向代码和代理（Code Layers、agent、MCP），伸向营销物料的 Buzz 和 Sites 发布 17 个月仍是 beta，面向营销人员的 Content 席位还没开售 [S18][S20]。Figma 的毛利率和股权激励压力也限制了它打价格战的能力。它向 Adobe 腹地推进的速度比 2025 年发布时预期的慢。
- **加压的一面**：绕过 Figma 的那股力量同样在绕过 Adobe。Claude Design、Stitch 和聊天产品里的图像生成，让"只要结果的人"不必打开任何专业工具。这正是同批次评审里熊市情景的机制，与 Figma 无关。
- **净效果**：来自 Figma 的威胁没有因为 AI 变大；Adobe 面对的主要威胁从"Figma 这样的协作工具"换成了"模型厂商"。Adobe 也不必再考虑重返界面设计，这个选项已经没有价值。

## 6. 对 Adobe 未来的影响

### 6.1 已经造成的影响

| 项目 | 量级 | 说明 |
|---|---|---|
| 失去的品类 | Figma 2026 年收入 14.65 亿，增速 39% | 相当于 Adobe 收入的 5.5%。界面设计在 2015 年以前主要是 Photoshop 和 Illustrator 的用途，Adobe 用 XD 守了约 7 年没守住（行业常识） |
| 失去的增量 | 每年约 4 亿 | 若收购成功，Adobe 的 ARR 增速会高约 1.6 个点 |
| 失去的入口 | 月活超过 1,300 万，三分之二不是设计师 [S8] | Adobe 没有任何产品能进入产品经理和工程师的日常工作 |
| 一次性成本 | 分手费 10 亿（FY24），加 15 个月的管理层精力 | 已经发生，不影响今后 [S13] |
| 存量收入 | 看不出影响 | 创意与营销订阅收入 FY25 +11%，FY26 前三季 +12%～13% [S14][S15] |
| 净新增 ARR 放缓 | 与 Figma 无关 | 公司说法：2026 年的放缓来自主动转向 freemium 和推迟调价 [S17] |
| 定价权 | 间接影响，无法量化 | Figma 在 2025-03 给 Full 席位提价、2026-03 开始收 AI 积分费，Adobe 则在 2026-06 推迟了调价 [S5][S47]。本文判断：在设计师的工具预算里 Figma 的份额在升，但 Adobe 定价权变弱的主因是 AI 和免费工具，不是 Figma |

### 6.2 未来 3～5 年

传导机制有三条。第一条是数字产品设计师降级或退订 Creative Cloud（A 池）。第二条是品牌与营销团队把模板化的素材生产搬进 Figma（B 池）。第三条最慢：新一代数字设计师的第一个工具是 Figma，而不是 Photoshop，Adobe 的长期漏斗变窄。

| | 最可能的情形 | 坏情形 |
|---|---|---|
| 本文给的概率 | 约 60% | 约 15% |
| Figma 做到什么 | 守住产品开发平台；Draw、Motion、Weave 逐步成熟；Buzz 转正但主要卖给已有客户 | Buzz、Weave、Slides 加上代理，成为企业做品牌与营销内容的默认画布；Content 席位把营销人员成规模地带进来 |
| Figma 自身 | 收入增速逐年降到 20%～25%，2030 年收入 30～35 亿 | 增速维持 30% 以上，2030 年收入 40 亿以上 |
| Adobe 受影响的收入 | A 池的三到四成，B 池基本不动 | A 池的四到五成，加上 B 池的两到三成 |
| 每年从 Adobe 拿走 | 0.5～1.0 亿 | FY28～FY31 每年 2.5～3.5 亿 |
| 到 FY31 累计 | 2.5～5 亿，占创意专业收入的 2%～4% | 10～14 亿，占 8%～12% |
| 对 Adobe 总收入增速 | 每年 −0.2～−0.4 个点 | 每年 −0.8～−1.1 个点 |
| 对"营销专业"收入 | 无影响 | 很小。营销云的价值在数据与旅程编排；受影响的是 GenStudio 的素材生产环节和 Express |

剩下约 25% 的概率是 Figma 自己被 AI 削弱，对 Adobe 的直接威胁减轻；但那种情形下 Adobe 的处境不会更好，原因见 5.2。

以上数字全部是本文估计。

### 6.3 是否改变已有评审的情景假设

**判断：已包含。不因 Figma 上调坏情景概率，不下调基准路径。**

1. **量级不够**。最可能情形每年 0.2～0.4 个点，落在基准路径自带的减速之内（收入增速从 FY27 的 7.5% 降到 FY31 的 5.5%，再到 FY36 的 3%）。
2. **坏情形也撑不起熊市**。熊市情景假设创意专业收入每年萎缩 6%～8%、持续 8 年，累计减少约 50 亿。Figma 的坏情形累计 10～14 亿，只有它的四分之一左右。要走到熊市，靠的是生成式 AI、Canva 和免费替代品，Figma 只是其中一个次要推手。
3. **最大的损失已经发生，而且不在收入基数里**。Adobe 输掉的是品类，那部分收入从未进过 Adobe 的报表，不会再丢一次。
4. **推进速度在放慢**。Figma 2026 年的资源明显向代码和代理倾斜，伸向 Adobe 腹地的两款产品仍是 beta。
5. **敏感性**（按同批次评审公布的公式重算，r=9%）：

| 假设 | 基准情景 V | 概率加权 V | P/V |
|---|---|---|---|
| 现状 | 361 | 282 | 0.86 |
| 最可能情形额外叠加（FY27～FY31 每年 −0.3～−0.4 个点） | 354～356 | 约 279～280 | 0.87 |
| 坏情形全部兑现（FY28～FY31 每年 −0.8～−1.0 个点） | 349～351 | 约 277～278 | 0.87 |

即使把坏情形当成确定发生，P/V 也只变动 0.01，不改变档位。"额外叠加"一行是保守算法，因为本文认为最可能情形已经含在基准路径里。

什么会让这个判断改变：见 6.4 的第 2、3 条同时触发。那时应把坏情形的概率从 15% 提到 30% 以上，并把基准路径 FY28～FY31 的增速各下调 0.5 个点。

### 6.4 可跟踪的指标与门槛

| # | 指标 | 时点 | 威胁加重 | 威胁减轻 |
|---|---|---|---|---|
| 1 | Figma 净留存率与增速 | Q3 财报（第三方预计 2026-11-04，公司未公布）；2027 年指引（2027-02） | 净留存率不低于 130%，且 2027 年收入指引不低于 +28% | 净留存率低于 125%，或 2027 年指引低于 +22%。这说明 AI 绕过在伤到 Figma，但同时是 Adobe 自身风险的旁证 |
| 2 | Buzz、Sites 转正与 Content 席位 | 到 Config 2027（预计 2027 年年中） | Buzz 转正、Content 席位开售，并披露采用率（例如年付 10 万美元以上的客户里三成以上每周使用 Buzz） | 到 2027 年年中仍是 beta |
| 3 | Adobe 创意与营销订阅收入增速（剔除 Semrush） | FY26 Q4 财报（预计 12 月中旬）与 FY27 指引 | 低于 +6%；或连续两个季度不再把"Creative Cloud 在团队版和企业版的强劲表现"列为增长驱动（Q3 仍列为第一条）[S17] | 不低于 +9% |
| 4 | Adobe MAX 2026 | 2026-11-10 至 11-12 | 三项都没有：Illustrator 网页版转正并支持多人实时编辑；公布 Firefly Boards 的用户数；任何界面设计或设计转代码的产品 | 出现其中两项 |
| 5 | Figma 非 GAAP 毛利率 | 每季 | 不低于 86%，且 AI 积分成为单独披露的收入项。说明它有余力继续扩张 | 连续两个季度低于 82% |

另一个不定期的变量是并购。Figma 的市值已经低于 Adobe 当年的出价。Adobe 再买一次在监管上不现实；但如果买家是大型平台或模型厂商，Figma 的分发和捆绑能力会发生质变，上面的坏情形概率要重估。Dylan Field 通过多类别股权控制投票权 [S5]，这件事取决于他个人。

## 7. 最不确定的地方与未能核实的事项

**最不确定的两点**：

1. **A 池和 B 池的规模**。Adobe 不披露分产品、分客群的收入和席位数，本文对"数字设计师手里的 Creative Cloud 席位"的估计（10～14 亿）依赖两个没有披露支撑的假设。它决定了 6.2 里所有数字的量级。
2. **Figma 的增长有多少可以持续**。2026 年的加速里有涨价的尾声和 AI 积分的首年效应。如果 2027 年净留存率掉回 120% 多，"Figma 被 AI 绕过"就从担忧变成事实，本文对 Adobe 一侧的推论也要跟着重做。

**未能核实**：

- Adobe 的帮助页（XD 支持页、Illustrator 网页版、Firefly 的 Figma 插件）直接访问被拒，内容来自搜索引擎摘要；XD 产品页能打开并已核对。
- Anthropic 关于 Claude Design 的官方原文、彭博 2024-01-30 的原文、Adobe Q2 FY26 电话会纪要原文，没有直接打开，分别经二手报道、The Register 和同批次评审转引。
- Firefly Boards 的用户数、Illustrator 网页版和 Photoshop 共同编辑的最新状态、Project Graph 是否已上线：未查到。
- Figma 是否原生支持打开 PSD、AI、XD 文件，Adobe Fonts 与 Adobe Stock 是否接入 Figma：未查到官方说明。
- 有多少设计师因为 Figma 而退订或降级 Creative Cloud：未查到任何调查或公司披露。
- Figma 2026 Q2 的付费客户总数、分席位类型的收入、AI 积分收入金额：公司未披露。
- Figma Q3 财报日期、Adobe FY26 Q4 财报日期：公司均未公布。
- 2025-09-04 和 2026-06-25 两次 Figma 股价大跌的原因：未逐项核实。
- XD 的发布年份、Photoshop 网页版的转正时间：行业常识，未取证。

## 来源

**SEC 与公司申报**

- [S1] Figma 2026 Q2 业绩稿（8-K Ex.99.1，2026-08-05）：https://www.sec.gov/Archives/edgar/data/1579878/000162828026053331/q226pressrelease.htm
- [S2] Figma 10-Q（截至 2026-06-30，2026-08-05 提交）：https://www.sec.gov/Archives/edgar/data/1579878/000162828026053348/fig-20260630.htm
- [S3] Figma 2026 Q1 业绩稿（2026-05-14）：https://www.sec.gov/Archives/edgar/data/1579878/000162828026035087/q126pressrelease.htm ；10-Q：https://www.sec.gov/Archives/edgar/data/1579878/000162828026035209/fig-20260331.htm
- [S4] Figma 2025 Q4 与全年业绩稿（2026-02-18）：https://www.sec.gov/Archives/edgar/data/1579878/000162828026009024/fy25pressrelease.htm
- [S5] Figma FY2025 10-K（2026-02-18）：https://www.sec.gov/Archives/edgar/data/1579878/000162828026009228/fig-20251231.htm
- [S6] Figma 2025 Q3 业绩稿（2025-11-05）：https://www.sec.gov/Archives/edgar/data/1579878/000162828025049555/q325pressrelease.htm
- [S7] Figma 2025 Q2 业绩稿（2025-09-03）：https://www.sec.gov/Archives/edgar/data/1579878/000157987825000026/q225pressrelease.htm
- [S8] Figma 招股书 424B4（2025-07-31）：https://www.sec.gov/Archives/edgar/data/1579878/000162828025037014/figma424b4.htm
- [S9] Figma 8-K（2026-04-14，Mike Krieger 辞任董事）：https://www.sec.gov/Archives/edgar/data/1579878/000162828026025127/fig-20260414.htm
- [S10] Figma XBRL 与申报清单：https://data.sec.gov/api/xbrl/companyfacts/CIK0001579878.json ；https://data.sec.gov/submissions/CIK0001579878.json
- [S11] Adobe 宣布收购 Figma 的新闻稿（8-K Ex.99.1，2022-09-15）：https://www.sec.gov/Archives/edgar/data/796343/000114036122033412/ny20005310x2_ex99-1.htm
- [S12] Adobe 与 Figma 终止合并的新闻稿（8-K Ex.99.1，2023-12-18）：https://www.sec.gov/Archives/edgar/data/796343/000079634323000254/adbedecember182023pressrel.htm
- [S13] Adobe FY2025 10-K（截至 2025-11-28）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000003/adbe-20251128.htm
- [S14] Adobe FY2025 业绩稿（2025-12-10）：https://www.sec.gov/Archives/edgar/data/796343/000079634325000135/adbeex991q425.htm
- [S15] Adobe Q3 FY26 业绩稿（2026-09-10）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000147/adbeex991q326.htm
- [S16] Adobe 10-Q（截至 2026-08-28，2026-09-22 提交）：https://www.sec.gov/Archives/edgar/data/796343/000079634326000156/adbe-20260828.htm
- [S17] Adobe Q3 FY26 电话会纪要（2026-09-10，全文检索）：https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q3fy26-transcript.pdf

**Figma 官方**

- [S18] Config 2026 回顾（Figma 博客，2026-06-24）：https://www.figma.com/blog/config-2026-recap/ ；论坛汇总（2026-06-24）：https://forum.figma.com/product-updates-3/everything-announced-at-config-2026-55221
- [S19] Figma 发布说明（2026-09-16 至 10-06 的条目，2026-10-12 取数）：https://www.figma.com/release-notes/
- [S20] Figma 定价页（2026-10-12 取数）：https://www.figma.com/pricing/
- [S21] Figma 2026 Q2 电话会纪要（2026-08-05，Motley Fool 整理，Webull 转载）：https://www.webull.com/news/15392832623961088
- [S22] Config 2025 新功能（Figma 帮助中心，2025-05）：https://help.figma.com/hc/en-us/articles/30965205437975-What-s-new-from-Config-2025

**Adobe 官方**

- [S23] Adobe XD 产品页（2026-10-12 取数，写明"currently in maintenance mode"）：https://www.adobe.com/products/xd.html ；XD 支持页（直接访问被拒，经搜索摘要）：https://helpx.adobe.com/support/xd.html
- [S24] Adobe MAX 2025 Creative Cloud 新闻稿（2025-10-28）：https://news.adobe.com/news/downloads/pdfs/2025/10/102825-creative-cloud.pdf ；Express 团队版定价页：https://business.adobe.com/fragments/products/express/get-pricing.html
- [S25] Adobe 博客：Adobe for creativity 连接器登陆 Claude（2026-04-28）：https://blog.adobe.com/en/publish/2026/04/28/adobe-for-creativity-connector
- [S26] Adobe 博客：进入 Gemini 并扩展 Claude（2026-09-24）：https://blog.adobe.com/en/publish/2026/09/24/adobe-comes-to-gemini-expands-what-you-can-do-in-claude
- [S27] Adobe 新闻稿：Photoshop、Express、Acrobat 进入 ChatGPT（2025-12-10）：https://news.adobe.com/news/2025/12/adobe-photoshop-express-acrobat-chatgpt
- [S28] Firefly 的 Figma 插件帮助页（直接访问被拒，经搜索摘要；各区域页更新于 2026-02 至 07）：https://helpx.adobe.com/firefly/web/app-integrations/figma/firefly-plugin-for-figma.html
- [S29] GenStudio for Performance Marketing 集成说明（更新于 2026-03-09）：https://experienceleague.adobe.com/en/docs/genstudio-for-performance-marketing/user-guide/integrations/overview ；发布说明（经搜索摘要）：https://experienceleague.adobe.com/en/docs/genstudio-for-performance-marketing/user-guide/release-notes
- [S30] AEM：Figma to Visual Content Fragments（更新于 2026-10-12）：https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/ai-in-aem/agents/brand-experience/experience-production/figma-to-visual-content-fragments
- [S31] Illustrator 网页版（Beta）帮助页（直接访问被拒，经搜索摘要；更新于 2026-04）：https://helpx.adobe.com/illustrator/web/illustrator-on-the-web-overview.html ；2021 年发布报道（2021-10-26）：https://www.techtimes.com/articles/267136/20211026/adobe-announces-simplified-web-versions-photoshop-illustrator.htm
- [S32] Adobe Firefly 新功能页（经搜索摘要：Firefly AI Assistant 2026-04 beta，Boards 引导流程 2026-03）：https://helpx.adobe.com/firefly/using/whats-new.html

**媒体与第三方**

- [S33] The Register（2024-01-31）：https://www.theregister.com/2024/01/31/adobe_no_plans_to_invest/ ；彭博（2024-01-30，只核对标题与摘要）：https://www.bloomberg.com/news/articles/2024-01-30/adobe-gives-up-on-xd-after-figma-deal-collapse
- [S34] TechCrunch（2023-12-18）：https://techcrunch.com/2023/12/18/adobe-has-a-big-hole-to-fill-after-the-20b-figma-deal-falls-through
- [S35] 英国 CMA 新闻稿（2023-11-28）：https://www.gov.uk/government/news/adobe-figma-deal-could-harm-uk-digital-design-sector
- [S36] Figma 上市：IPOScoop（2025-07-31）：https://www.iposcoop.com/?p=35937 ；Renaissance Capital：https://www.renaissancecapital.com/IPO-Center/News/112482/Figma-flies-up-250-percent-in-largest-ever-pop-for-a-billion-dollar-IPO
- [S37] Benzinga 经雅虎财经（2026-03-21，谷歌 Stitch）：https://finance.yahoo.com/markets/stocks/articles/figma-fig-stock-trending-googles-233127606.html
- [S38] Motley Fool（2026-05-03，Figma 4 月为何下跌 16%）：https://www.fool.com/investing/2026/05/03/why-figma-fell-16-in-april/ ；DesignRush（Claude Design 发布）：https://news.designrush.com/anthropic-claude-design-launch-figma
- [S39] The Next Web（2026-05-14）：https://thenextweb.com/news/figma-q1-earnings-ai-monetization-stock-rebound
- [S40] Claude Design 的二手报道（Unite.AI，2026-04）：https://www.unite.ai/anthropic-launches-claude-design-for-visual-prototyping-and-presentations/ ；Anthropic 新闻页（原文未能打开）：https://www.anthropic.com/news
- [S41] 2026-08-06 股价反应：MarketBeat：https://www.marketbeat.com/instant-alerts/figma-nysefig-shares-gap-down-heres-what-happened-2026-08-06/ ；BingX：https://bingx.com/en/news/post/why-is-figma-fig-stock-price-down-today-august-rising-ai-costs-and-slower-growth-outlook-trigger-a-selloff
- [S42] TIKR（2026-05-09，Figma 股价回顾）：https://www.tikr.com/blog/figma-stock-is-down-83-from-its-ipo-era-highs-heres-what-could-drive-the-next-move
- [S43] UX Tools 2024 年设计工具调查（2,220 人）：https://www.uxtools.co/survey/interface-design/overview
- [S44] Firefly Boards 正式发布（Reworked，2025-09-30）：https://www.reworked.co/collaboration-productivity/adobes-firefly-boards-goes-live-with-multi-model-video-generation/ ；公开 beta（BusinessWire，2025-04-24）：https://www.businesswire.com/news/home/20250424667184/en
- [S45] Photoshop 实时共同编辑私测（PetaPixel，2025-01-14）：https://petapixel.com/2025/01/14/live-co-editing-brings-real-time-collaboration-to-adobe-photoshop
- [S46] Creative Cloud Pro 调价（The Register，2025-05-20）：https://www.theregister.com/2025/05/20/adobe_price_hikes/
- [S47] Adobe Q2 FY26 电话会（2026-06-11；经 GuruFocus 摘要与同批次评审转引，原文未重新打开）：https://www.gurufocus.com/stock/XSGO:ADBECL/transcripts/8913215 ；https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/adbe-q2fy26-transcript.pdf
- [S48] 价格：腾讯前复权日线：https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=usFIG.N,day,2025-07-25,2026-10-12,400,qfq ；https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=usADBE.OQ,day,2025-07-25,2026-10-12,400,qfq
- [S49] Adobe Summit 2026（Computerworld，2026-04）：https://www.computerworld.com/article/4146823/adobe-summit-2026-how-adobe-hopes-to-redesign-marketing-and-creativity-with-ai.html
- [S50] Adobe 收购 Semrush（Search Engine Land，2025-11）：https://searchengineland.com/adobe-semrush-464905
- [S51] Adobe Project Graph（经搜索摘要，原文未打开；Adobe 博客 2025-12-04 与 design-offset 报道）：https://blog.adobe.com/en/topics/creativity ；https://design-offset.com/?p=14252
