#!/usr/bin/env python3
"""
DLT 预测系统版本管理 — 单源版本定义

所有其他模块通过 from version import VERSION, RELEASE_DATE 引用。
版本更新只需改这一个文件。
"""

# ============================================================
# 🎯 单源版本定义（升级时仅改此处！）
# ============================================================
VERSION = "3.13.0"
RELEASE_DATE = "2026-07-07"

# 自动派生横幅，杜绝代码 banner 与 VERSION 不一致
BANNER = f"V{VERSION} + NeuralEnsemble + RankingModel"

# 需要同步版本的文件列表（供 bump_version.py 和校验使用）
VERSION_FILES = [
    "scripts/version.py",          # 本文件
    "scripts/dlt_fusion_complete.py",  # 代码横幅
    "references/dlt_skill_config.json", # skill_name / version / reference_sync_version
]

# 3.13.0 (2026-07-07, 26075期失准优化)
# - [A] 后区冷号捕获(get_back_recommendations): 后区号码遗漏≥8期且非上期重号时,
#       强制注入至少1组含该号码的配对至selected
# - [B] WA评级校准层(predict): 基于近50期(和值段,跨度段)历史命中率加权修正final_score,
#       限幅[0.5,1.5], 拉大高分与低分置信差距
# - [C] Z2中段保底增强(_ensure_min_coverage): 阈值<2→<3, 确保每个候选Z2中段≥3个号码
# - [D] 中遗漏链式补缺(_ensure_min_coverage): 遗漏6-12期的Z2中段号码强制补充至候选
#
# 3.12.0 (2026-07-05)
# - [方案2] 后区错位交叉: top6单号码×3搭档交叉矩阵, 替代K-Medoids
# - [方案3] 重号灵敏度增强: 密集期boost翻倍(1.20×), 无密集期宽度扩展到1.05-1.15×
# - [方案3-2] 重号分散修复: 低频上期号码强制配对注入
# - [方案4] 回测修正排序: 最近N期模式相似度匹配(和值/奇偶/AC/重号), ±2%微调
# - [方案5] 三区平衡多样性: 偏小/偏大/均衡三种基线强制各覆盖1注
#
# 3.11.0 (2026-07-02)
# - [A] 分数归一化+动态展宽: z-score+sigmoid映射, 解决评分天花板饱和
# - [B] Z1/Z3均衡注入+Z2冷号门禁: 防止区间分布系统性偏离
#
# 3.3.0 (2026-06-26)
# - [P1] 可学习排序模型：55维特征提取+GBR排序替代20步串行评分pipeline
# - [P2] 评分标准化：base/gt/genetic三维度百分位排名加权替代绝对分数
# - [P3] 决策树排序：7维跨期特征训练DecisionTree预测号码概率，15%权重融合
# - [P4] 条件计算图：11节点DAG引擎，节点独立try/except+拓扑排序执行
# - [P5] 神经降级路径：三档内存调度(800MB+/500-800/<500)
# - [P6] 约束软化：策略通过数从硬过滤改为评分因子
# - [P7] 后区条件概率：P(back|front_max_bucket)条件矩阵替代均匀分配
# - [P8] 线性趋势和值预测：LinearRegression替代硬编码动量衰减
# - [P10] 增强回测：MRR/NDCG@5/ECE/热号基线指标
# - [方案4] 分级推理策略表：四级统一内存调度(≥800/≥500/≥300/<300MB)
# - [方案5] 三基线对比：随机+热号+模式基线 + model beats all rate
#
# 3.2.0 (2026-06-25)
# - [方向A] 冷热号动态分位数阈值(均值±0.5std替代固定Top-N)
# - [方向A] 极冷号强制注入(遗漏>30期的号码替换冷号池末位)
# - [方向C] 后区全枚举(C12,2=66组合)+K-Medoids覆盖优化
# - [方向C] get_back_recommendations()重写为全枚举路径
