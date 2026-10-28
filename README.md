# 商业分析与数据分析作品集

这套作品集按大厂分析项目的标准组织：先定义决策问题，再定义指标和口径，进行数据质量检查，完成描述性分析、因果/预测分析和商业化测算，最后给出建议、局限和可验证的下一步。

## 项目入口

1. [营销投放增量与因果分析：Hillstrom](01_hillstrom_incrementality/EXECUTIVE_REPORT.md)
2. [广告投放增量建模与用户分层：Criteo](02_criteo_uplift/EXECUTIVE_REPORT.md)
3. [电商转化漏斗与用户行为分析：UCI Online Shoppers](03_uci_shoppers/EXECUTIVE_REPORT.md)

## 能力覆盖

| 能力 | 对应项目 |
|---|---|
| A/B 测试、ITT、Bootstrap、增量 ROI | Hillstrom |
| T-learner、uplift 分层、预算约束 | Criteo |
| SQL 指标拆解、漏斗分析、逻辑回归、预测排序 | UCI Online Shoppers |
| 数据质量检查、指标口径、结果边界 | 三个项目均覆盖 |

## 复现环境

```powershell
python outputs/portfolio/01_hillstrom_incrementality/src/analyze_hillstrom.py
python outputs/portfolio/02_criteo_uplift/src/fetch_criteo_sample.py
python outputs/portfolio/02_criteo_uplift/src/analyze_criteo.py
python outputs/portfolio/03_uci_shoppers/src/analyze_uci_shoppers.py
```

## 面试时的统一讲法

每个项目都按以下顺序讲：

1. 业务决策是什么；
2. 核心指标和数据口径是什么；
3. 为什么使用该分析方法；
4. 结果能支持什么行动；
5. 结论有哪些限制；
6. 下一步如何用实验或持续监控验证。
