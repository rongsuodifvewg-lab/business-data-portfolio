# 电商转化漏斗与用户行为分析

## 业务问题

网站流量中哪些行为和用户场景与购买转化最相关？产品、运营和再营销团队应该优先优化哪些环节？

## 数据与边界

数据来自 UCI Online Shoppers Purchasing Intention Dataset，共 12,330 次网站会话，包含页面访问次数、停留时长、跳出率、退出率、PageValues、月份、用户类型、周末和最终购买标记 `Revenue`。

该数据没有随机投放或处理组，因此本项目做的是描述性分析和预测分析，不能把相关关系解释成因果关系。

## 分析过程

1. 校验字段类型，把 `Revenue` 和 `Weekend` 转为可计算的二元变量。
2. 按用户类型、月份和周末拆解会话量、购买量和转化率。
3. 对买家与非买家的产品页访问、停留时间、跳出率、退出率和 PageValues 做行为画像比较。
4. 使用带类别变量的逻辑回归建立转化概率排序模型，报告 ROC-AUC、Average Precision 和 Brier Score。
5. 将模型和描述性结果转化为页面优化、再营销和流量分配建议。

## 如何复现

```powershell
python src/analyze_uci_shoppers.py
```

主要输出：

- `results/visitor_type_summary.csv`
- `results/month_summary.csv`
- `results/buyer_behavior_summary.csv`
- `results/logit_coefficients.csv`
- `results/model_metrics.json`
- `results/conversion_by_visitor_type.png`
- `results/conversion_by_month.png`
- `results/buyer_behavior_profile.png`

## 简历可写

基于 12,330 次网站会话，使用 SQL/Python 拆解用户类型、月份和页面行为的转化差异，建立逻辑回归转化排序模型并使用 Power BI 设计经营看板；将结果转化为页面优化、再营销和流量分配建议，并明确相关分析与因果结论的边界。
