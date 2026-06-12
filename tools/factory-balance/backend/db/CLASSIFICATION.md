# Intrinsic tag 分类子系统

完整设计见 `schema_final.sql` §7 与 `db/intrinsic/`、`db/extraction_etl.py`。

## 四层 Tag

| 层 | 存储 | 时机 |
|----|------|------|
| IR | `snap_resource_intrinsic_tag` | snapshot ETL |
| IP | `snap_recipe_intrinsic_tag` + `snap_recipe_closure_role` | snapshot ETL |
| G | `snap_resource_stats` / `snap_resource_stats_primary` | snapshot ETL |
| C | `catalog_tag` | 导入存档 / build_catalog |

## 世界抽取（游戏数据，非手写名单）

ETL 从 dump 读取：

- `resource` 实体 → 矿脉/油井（`minable.result` / `minable.results`）
- `mining-drill` → `resource_categories`（如 pumpjack → `basic-fluid`）
- `offshore-pump` → 产出 `water`

写入 `snap_resource_extraction`，并生成合成配方 `fb-extract:{name}`（category mining/pumping，无原料）。

`ir.extractable` = 出现在 `snap_resource_extraction` 中，或 item `subgroup=raw-resource`。

## 配方入库

凡产出 **item 或 fluid** 的可见配方均入库（含 `basic-oil-processing` 等纯流体配方）。

## 分析闭包

- 仅 `closure_role=primary` 的配方参与反向展开
- `ip.barrel.*` → logistics，永不闭包
- 抽取物在解锁对应抽取建筑（如 pumpjack）后 → `closure_expandable`，布局为 producer（`fb-extract:*`）

## 规则版本

`tag_rule_version = 3`

**完整分析集 / Context / Tag 对照：** [ANALYSIS_SUPPLY_SEMANTICS.md](./ANALYSIS_SUPPLY_SEMANTICS.md)
