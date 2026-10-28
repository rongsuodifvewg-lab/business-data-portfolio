# 营销投放增量与因果分析

## 业务问题

给客户发送营销邮件是否带来增量访问、增量购买和增量收入？如果有效，应该优先投放给哪些客户，预算是否值得扩大？

## 数据与分析边界

数据来自 MineThatData 的公开邮件营销随机实验，约 64,000 名客户被随机分配到男装邮件、女装邮件或不发邮件三组。`visit`、`conversion` 和 `spend` 是结果变量；`history_segment`、`newbie` 和 `channel` 用于分层分析。

分析估计的是 ITT（按随机分配比较），不是“打开邮件的人”的效果。`spend` 是收入而不是利润，因此 ROI 结果依赖显式的毛利率和邮件成本假设。该实验发生于 2008 年，不能直接外推到今天的投放环境。

## 分析过程

1. 校验字段、缺失值、处理组规模和结果变量类型。
2. 计算各组访问率、转化率、客均消费和总收入。
3. 以 No E-Mail 为控制组，估计访问、转化和客均消费的增量效果。
4. 用 Bootstrap 置信区间与显著性检验评估效果稳定性。
5. 按历史消费、是否新客和渠道分析异质性效果。
6. 在毛利率与邮件成本情景下测算增量利润与 ROI。
7. 将统计结果转化为投放人群、预算和后续实验建议。

## 如何复现

```powershell
python src/analyze_hillstrom.py
```

主要输出：

- `results/group_summary.csv`：三组描述统计
- `results/effect_vs_control.csv`：处理效应与置信区间
- `results/balance_check.csv`：随机分组前置变量的标准化差异
- `results/subgroup_effects.csv`：客户分层效果
- `results/economic_scenarios.csv`：毛利率和邮件成本情景
- `results/conversion_by_treatment.png`：转化率比较
- `results/conversion_lift_by_history_segment.png`：分层转化提升
- `results/profit_sensitivity.png`：经济敏感性

## 简历可写

基于约 64,000 名客户的随机邮件营销实验，使用 Python/SQL 完成实验组与对照组平衡性检查、ITT 效果估计、Bootstrap 置信区间和客户分层分析；在毛利率与邮件成本假设下测算增量利润和投放 ROI，形成预算扩量建议并明确因果结论边界。
