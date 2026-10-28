# 广告投放增量建模与用户分层

## 业务问题

在广告预算有限时，哪些用户更可能因为广告曝光而增加访问？如何把总体处理效果转化为可验证的投放优先级？

## 数据与抽样边界

Criteo Uplift Prediction Dataset 由 Criteo AI Lab 发布，字段包括 12 个匿名特征、`treatment`、`visit`、`conversion` 和 `exposure`。官方数据约 1,397.9 万行。

本作品集通过 Hugging Face 数据查看接口，在全量行索引上等间距抽取 50 页、共 5,000 行真实记录。这样可以复现完整分析流程而不下载约 300MB 压缩文件，但所有效果数字只代表该样本，不能写成全量数据结论。

## 分析过程

1. 检查 treatment 比例、visit、conversion 和 exposure 的基础分布。
2. 计算处理组与控制组的总体访问、转化和曝光差异，并给出近似置信区间。
3. 分别在处理组和控制组训练逻辑回归 T-learner，估计每条记录的预测 uplift：`P(visit|x,t=1)-P(visit|x,t=0)`。
4. 按预测 uplift 分成十组，比较每组真实处理组与控制组的访问差异，检查排序是否有业务价值。
5. 把 uplift 排名转化为预算分层方案，同时保留样本抽取、隐私抽样和模型稳定性的限制。

## 如何复现

```powershell
python src/fetch_criteo_sample.py
python src/analyze_criteo.py
```

主要输出：

- `data/criteo_sample_5000.csv`：真实数据样本
- `data/sample_metadata.json`：抽样规则与全量行数
- `results/treatment_summary.csv`
- `results/average_treatment_effects.csv`
- `results/uplift_deciles.csv`
- `results/visit_rate_by_treatment.png`
- `results/uplift_decile_curve.png`

## 简历可写

基于 Criteo 广告 uplift 数据的 5,000 行可复现样本，使用 Python/SQL 计算 treatment 对访问和转化的增量效果，构建处理组/控制组 T-learner 并按预测 uplift 分层，输出预算约束下的投放优先级；明确抽样、匿名特征和全量外推限制。
