---
name: dlt-lottery-prediction
description: 中国体育彩票超级大乐透（DLT）预测技能，基于深度学习的彩票号码预测系统。六池采样（热号/冷号/均衡/博弈/遗传/趋势）+ 博弈论遗传算法融合 + 约束满足引擎 + 跨期模式识别 + 尾号聚合检测 + AC值跟踪 + 偏差仪表盘校准。使用场景：(1) 预测下一期DLT大乐透号码 (2) 生成复式投注方案 (3) 回测模型性能 (4) 自动同步最新开奖数据
---

# DLT大乐透预测技能

六池采样 + 博弈论遗传算法融合 + 跨期模式识别 + 约束引擎，数据自动同步，支持复式+胆拖投注。

---

## 📡 数据同步

仅在调用 `predict()` 时触发。双源自动切换：
1. 优先查体彩API（webapi.sporttery.cn），被拦截则回退到 500彩票网
2. 发现新期号 → 追加到 Excel → 重新初始化子模块
3. 无新数据 → 跳过，直接使用现有数据

> 两个数据源均失败时可手动补充 Excel 文件。

---

## 核心架构

### 1. 多池加权采样（MultiPoolSampler，6池）

前后区各 6 个独立池，共 12 个生成器：

| 池 | 权重 | 策略 |
|----|------|------|
| 🔥 热号池 | 30% | 最近30期高频号码 |
| ❄️ 冷号池 | 15% | 最近30期低频号码 |
| ⚖️ 均衡池 | 20% | 热冷折中 |
| 📈 趋势池 | 20% | 和值趋势方向加权（上行→大号区，下行→小号区） |
| 🎯 博弈池 | 10% | 博弈论期望值排序 |
| 🧬 遗传池 | 5% | 遗传算法进化组合 |

### 2. 博弈论 + 遗传算法

- **博弈论输出层**：纳什均衡优化多策略输出
- **遗传算法**：全局组合适应度优化（频率 + 遗漏值 + 奇偶比 + 和值 + 30%模式匹配度）

### 3. 🧩 跨期模式识别（10种特征 + 第7池）

在6池基础上叠加模式识别层，从历史数据提取10种特征频率分布：

| 模式 | 权重 | 描述 |
|------|------|------|
| 跨度 | 12% | 最大号与最小号的差值 |
| 连号 | 10% | 相邻号码间隔分布 |
| **三联号** | **15%** | **≥3个连续簇检测(V3.1.1)** |
| 和值 | 12% | 5号之和，按5分组距 |
| 奇偶比 | 10% | 3:2 或 2:3 为高频 |
| 重号 | 15% | 与上期重复的号码数 |
| 尾号 | 10% | 个位数字分布多样性 |
| 三区分布 | 12% | 1-12/13-24/25-35 分布 |
| 质数 | 7% | 1-35中11个质数的命中数 |
| AC值 | 12% | 算术复杂度（6为最高频） |

**集成方式**：
- **模式池**（第7池）：从高频模式反推号码集合
- **评分增强**：base + 模式匹配度×35%
- **多样性池**：覆盖不同模式值的代表性号码

### 4. 尾号聚合 + AC值跟踪 + 偏差校准（V2.1.0）

- **尾号聚合检测**：候选组合尾号≤3种时降3%，4种(1重复)加1%
- **AC值跟踪评分**：基于最近100期AC值概率分布调整候选
- **偏差仪表盘**：自动跟踪和值/跨度/大小号偏差，偏差过大时补偿覆盖被低估方向的候选
- **置信度重校准**：根据偏差修正最终评分

### 5. 约束满足引擎

- 唯一性：每注内号码不重复
- 范围：前区1-35，后区1-12
- 格式：5+2 标准注
- 数学：和值、AC值、跨度限制

### 6. 复式投注生成

12种方案：6+3(18注) / 6+4(36注) / 7+2(21注) / 7+3(63注) / 7+4(126注) / 8+2(56注) / 8+3(168注) / 8+4(336注) / 8+5(560注) / 9+3(378注) / 9+4(756注) / 9+6(1890注)

---

## 使用方法

```python
from pathlib import Path
import sys

# 自动定位技能包的 scripts/ 目录
skill_dir = Path(__file__).resolve().parent / 'skills' / 'dlt-lottery-prediction'
scripts_dir = skill_dir / 'scripts'
sys.path.insert(0, str(scripts_dir))

from dlt_fusion_complete import DLTFusionComplete

# 初始化（不检查网络）
fusion = DLTFusionComplete()

# 预测（返回单式+复式，已保证每注号码唯一）
result = fusion.predict(include_compound=True)
print(result['single_bets'])    # 5注单式
print(result['compound_bets'])  # 12种复式

# 回测验证
bt = fusion.backtest(n_recent=100)
print(bt['pool_performance'])

# 独立检查数据更新
from dlt_data_updater import check_and_update
result = check_and_update()
print(f"新增{result['new_count']}期，最新{result['last_period']}")
```

---

## 输出格式

所有群聊和单聊的预测回复，严格遵循 `scripts/dlt_lottery_skill.py` 中 `_print_predict()` 的终端输出格式。

### 单式方案
```
🎯 单式方案 (Top 5)
 1. [xx xx xx xx xx] + [xx xx]  score=0.xxxx  p=xx.x%
 2. [xx xx xx xx xx] + [xx xx]  score=0.xxxx  p=xx.x%
```

### 复式方案
```
📋 复式方案
  6+3 (18注, 36元) × 2组:
    1: [xx xx xx xx xx] + [xx xx]
    2: [xx xx xx xx xx] + [xx xx]
```

### 胆拖方案
```
📊 胆拖方案
  🎯 多池融合胆拖:
    2胆3拖: 胆[xx xx] 拖[xx xx xx] 后区[xx xx]  336注672元  p=xx.x%
```

末尾加：`⚠️  仅供参考娱乐，请理性投注！`

---

## 技术指标

| 指标 | 数值 |
|------|------|
| 历史数据 | 自动同步（体彩API + 500彩票网双源） |
| 数据范围 | 7001期 ~ 最新 |
| 前区/后区 | 1-35 / 1-12 |
| 基础池数 | 6池 × 前后区 = 12个生成器 |
| 模式池 | 9种特征（第7池） |
| 复式方案 | 12种 |

---

## 文件结构

```
dlt-lottery-prediction/
├── SKILL.md                           # 技能说明文档（本文档）
├── scripts/                            # 可执行代码
│   ├── __init__.py                     # Python包入口
│   ├── dlt_fusion_complete.py          # 主入口（DLTFusionComplete类）
│   ├── dlt_data_updater.py             # 📡 自动数据更新器
│   ├── dlt_five_pool_fusion.py         # 多池融合（类名历史遗留）
│   ├── dlt_five_pool_sampler.py        # 旧版采样器（历史遗留）
│   ├── five_pool_sampler_complete_final.py # 多池采样器 (MultiPoolSampler)
│   ├── dlt_constraint_engine.py        # 约束引擎
│   ├── strategy_fusion_engine.py       # 策略融合引擎
│   ├── dlt_back_fusion.py              # 后区融合
│   ├── dlt_predictor_upgraded.py       # 升级版预测器
│   ├── dlt_optimized_predictor.py      # 优化预测器
│   ├── dlt_lottery_skill.py            # OpenClaw技能封装入口
│   ├── lottery_bayesian.py             # 贝叶斯分析
│   ├── lottery_calibration.py          # 校准模块
│   ├── lottery_metrics.py              # 指标计算
│   ├── lottery_time_series_cv.py       # 时间序列交叉验证
│   ├── prediction_store.py             # 预测存储模块
│   └── modules/                        # 子模块
│       ├── dlt_game_theory.py           # 博弈论分析
│       ├── dlt_genetic_optimizer.py     # 遗传算法
│       ├── dlt_math_filter.py           # 数学过滤
│       ├── dlt_statistics_analyzer.py   # 统计分析
│       ├── dlt_number_gravity.py        # 号码引力
│       ├── dlt_kill_number.py           # 杀号
│       ├── dlt_difference_sequence.py   # 差数序列
│       ├── dlt_matrix_displacement.py   # 矩阵位移
│       ├── dlt_compound_betting.py      # 复式投注
│       ├── dlt_betting.py               # 基础投注
│       ├── dlt_strategy_recommender.py  # 策略推荐
│       ├── dlt_pattern_recognizer.py    # 🧩 跨期模式识别器
│       └── neural_models.py             # 神经网络模型
├── assets/                             # 运行时文件
│   └── data/
│       └── DLT历史数据_适配模型版.xlsx   # 历史开奖数据
├── references/                         # 参考文档（需与代码版本同步）
│   ├── STRATEGY_FUSION_DESIGN.md       # 策略融合架构设计文档
│   ├── dlt_skill_config.json           # 运行时配置定义
│   ├── skill.yaml                      # 技能描述文件
│   └── sync_check.py                   # 🔁 版本同步检查工具
├── _meta.json                          # ClawHub元数据
└── .clawhub/                           # ClawHub元数据
```

---

## 版本历史

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| **V3.1.1** | 2026-06-14 | 基于26065期四维优化：和值动量衰减、三联号检测、热号衰减瓶颈、后区段覆盖、弱化隔期重号 |
| V3.0.3 | 2026-06-11 | 滑动窗口权重校准、连续大和值补偿、盲区最小覆盖、配对重号、复式三区配额 |
| V3.0.2 | 2026-06-09 | 奇偶比补充、三区强制约束、漂移检测增强、隔期重号奖惩平衡、复式独立采样 |
| V3.0.1 | 2026-06-08 | 胆拖重构、Python 3.11迁移、输出格式标准化 |
| V3.0.0 | 2026-06-07 | 代码清理、复式重写、胆拖投注、凯利公式、四大质量优化 |
| V2.1.0 | 2026-06-02 | 趋势池修正(5→6池)、NeuralEnsemble集成、尾号/AC值/偏差校准 |
| V2.0 | 2026-05-28 | 隔期重号增强、双期候选池、智能重号惩罚 |
| V1.1 | 2026-05-21 | 跨期模式识别9种特征 |
| V1.0 | 2026-05-18 | 五池采样+博弈论遗传+约束引擎 |

### V3.1.1 (2026-06-14) — 基于26065期四维优化

**① 和值动量衰减**：连续≥3期和值下降 → 趋势池强度×1.5，小号区范围扩至1-12，评分补偿低和值候选

**② 三联号(≥3)簇检测**：跨期识别新增三联号子模块，连号簇评分×1.5补偿

**③ 热号衰减瓶颈**：连续出现≥3期号码，候选包含≥2个时最终分×0.7

**④ 后区段覆盖**：后区5-8段强制至少2个号码

**⑤ 弱化隔期重号增强**：移除激进加成，仅对≥4期连续号码保留轻度×1.10兜底

### V3.1.1 Bug修复 & 优化

**🐛 Bug修复**
- 修复 `_calc_compound_score()` 中 `pattern_stats` 不存在的属性引用 → 正确使用 `_pattern_distributions`，恢复复式/胆拖模式匹配评分
- 修复 Step 9 防御性填充：纯随机填充改为候选池频率加权填充，non-random
- 修复 `_sample_pool_candidates` 后区随机：改为使用 `get_back_recommendations()` 后区推荐
- 修复 `_calc_probability` 子项量级不匹配：各子项归一化到 [0,1] 后加权

**⚡ Token/性能优化**
- 神经网络惰性加载：首次 predict 时训练，`__init__` 和 `info` 命令不再触发 50 epoch 训练
- 数据同步缓存：30秒内不重复检测新数据
- `from dlt_data_updater import check_and_update` 移至模块级 import
- 复式枚举剪枝：大型复式(>10000组合)预评分过滤保留Top 60%
- 多重衰减保护：`final_score` 下限锁定 ≥ 0.50
- 评分链顺序优化：热号衰减在神经网络评分前执行，避免覆盖
- 子模块重初始化时神经网络标记惰性等待，不立即重训练

### V3.1.1 OOM修复 & 性能调优

**🐛 OOM根因**：`_recalibrate_score_weights()` 执行 49权重组合×20期=980次 `stratified_sample`，每次创建独立 MultiPoolSampler，内存耗尽被SIGKILL

**修复**：
- 权重校准从49×20=980次降为5×5=25次（使用候选自身评分代替完整采样）
- 可用内存<800MB时跳过权重校准
- `DLTGeneticOptimizer` 默认参数从100/50降至30/15
- `MultiPoolSampler` 内部 GA 默认从 100/50 → 30/15
- 初始化时检测 `/proc/meminfo` 动态调整 GA 参数：<400MB→15/10, <800MB→30/15, ≥800MB→50/25
- `evolve(generations=5, ...)` 错误 kwargs 修复为设置 `self.genetic.generations = 5`

---

## 🔁 references/ 版本同步机制

版本升级时，必须同步更新 `references/` 下的文件，确保文档、配置与代码一致。

### 同步检查流程

```bash
# 运行同步检查脚本
python skills/dlt-lottery-prediction/references/sync_check.py
```

脚本自动检查以下内容：
- `dlt_fusion_complete.py` 中的 `VERSION` 常量
- `references/dlt_skill_config.json` 中的 `reference_sync_version`
- `references/skill.yaml` 中的 `reference_sync_version`
- `references/STRATEGY_FUSION_DESIGN.md` 中的版本标记

### 版本升级 Checklist

每次新版发布时：

1. **更新 `dlt_fusion_complete.py`**：修改 `VERSION` 和 `RELEASE_DATE` 常量
2. **更新 `references/dlt_skill_config.json`**：
   - `version` → 新版本号
   - `release_date` → 新日期
   - `reference_sync_version` → 新版本号
   - `reference_sync_date` → 新日期
3. **更新 `references/skill.yaml`**：
   - `version` → 新版本号
   - `metadata.updated` → 新日期
   - `metadata.reference_sync_version` → 新版本号
   - `metadata.reference_sync_date` → 新日期
4. **更新 `references/STRATEGY_FUSION_DESIGN.md`**：
   - 顶部的版本标记和同步日期
   - 如有架构变更，同步更新文档正文
5. **运行 `python sync_check.py` 验证**

### 运行时自动检查

`DLTFusionComplete.predict()` 调用时自动执行版本同步检查，发现不匹配会输出 warning（不影响预测流程）：
```
⚠️ 版本不匹配: 代码 VERSION=2.1.0, 配置 reference_sync_version=2.0.0
```
