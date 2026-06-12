-- =============================================================================
-- v3.1 增补：架构优化 + UI 物品角色分类子系统
-- 附属于 schema_v3_design.sql，可合并为单一迁移
-- =============================================================================

-- -----------------------------------------------------------------------------
-- A. 架构优化 1 — 统一资源模型（合并 item / fluid 查询与图统计）
-- -----------------------------------------------------------------------------

CREATE TABLE resource (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    content_bundle_id   INTEGER NOT NULL REFERENCES content_bundle(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    kind                TEXT NOT NULL CHECK (kind IN ('item', 'fluid')),
    -- 原型静态属性（与进度无关）
    prototype_type      TEXT,              -- item|tool|armor|module（fluid 为 NULL）
    item_group          TEXT,
    item_subgroup       TEXT,
    is_raw              INTEGER NOT NULL DEFAULT 0,   -- 原型标记：可开采类
    expansion           TEXT NOT NULL DEFAULT 'base',
    icon                TEXT,
    stack_size          INTEGER,
    visibility          TEXT NOT NULL DEFAULT 'normal'
        CHECK (visibility IN ('normal', 'internal', 'hidden')),
    UNIQUE (content_bundle_id, kind, name)
);

CREATE TABLE resource_localization (
    resource_id     INTEGER NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
    locale          TEXT NOT NULL REFERENCES locale_code(code),
    label           TEXT NOT NULL,
    description     TEXT,
    PRIMARY KEY (resource_id, locale)
);

-- 注：实施时可保留 item/fluid 表作为视图指向 resource，或 ETL 只写 resource

-- -----------------------------------------------------------------------------
-- A. 架构优化 2 — Bundle 级配方图统计（ETL 一次计算，与进度无关）
-- -----------------------------------------------------------------------------

CREATE TABLE bundle_resource_graph (
    content_bundle_id       INTEGER NOT NULL REFERENCES content_bundle(id) ON DELETE CASCADE,
    resource_id             INTEGER NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
    produced_by_recipes     INTEGER NOT NULL DEFAULT 0,  -- 作为产物出现次数
    consumed_by_recipes     INTEGER NOT NULL DEFAULT 0,  -- 作为原料出现次数
    is_producible           INTEGER NOT NULL DEFAULT 0,  -- produced_by_recipes > 0
    is_consumed             INTEGER NOT NULL DEFAULT 0,  -- consumed_by_recipes > 0
    PRIMARY KEY (content_bundle_id, resource_id)
);

CREATE INDEX idx_bundle_graph_producible ON bundle_resource_graph(content_bundle_id, is_producible);
CREATE INDEX idx_bundle_graph_consumed ON bundle_resource_graph(content_bundle_id, is_consumed);

-- -----------------------------------------------------------------------------
-- B. UI 角色分类 — 核心设计
-- -----------------------------------------------------------------------------
-- 原则：
--   1. 「静态属性」来自原型 + ETL 规则（is_raw, visibility, expansion）
--   2. 「图属性」来自 bundle 全配方图（is_producible, is_consumed）
--   3. 「上下文角色」依赖 enabled_recipes 或 full 模式，在导入/切换时物化
--   4. UI 列表 = 对上下文角色的过滤，不在前端重复算逻辑
-- -----------------------------------------------------------------------------

-- 角色定义表（可扩展；code 稳定，供 API / 前端 i18n key 使用）
CREATE TABLE item_role_type (
    code            TEXT PRIMARY KEY,
    label_zh        TEXT NOT NULL,
    description     TEXT NOT NULL,
    layer           TEXT NOT NULL CHECK (layer IN ('static', 'graph', 'context')),
    ui_default      INTEGER NOT NULL DEFAULT 0   -- 是否默认出现在某 UI 面板
);

INSERT INTO item_role_type (code, label_zh, description, layer, ui_default) VALUES
    ('internal',           '内部项',       'parameter-* 等不应展示给玩家的项',           'static',  0),
    ('raw_intrinsic',      '原型原料',     '原型 is_raw=true，通常为矿/水等',            'static',  0),
    ('producible_full',    '全配方可产',   '在全 bundle 中至少有一条配方产出',            'graph',   0),
    ('consumed_full',      '全配方可消耗', '在全 bundle 中至少作为一次原料',              'graph',   0),
    ('craftable',          '当前可制造',   '当前上下文已启用配方能产出的物品',            'context', 0),
    ('pure_raw',           '纯粹原料',     '原型原料 且 当前上下文不可制造',              'context', 0),
    ('ingredient',         '配方原料',     '当前上下文已启用配方会消耗的物品',            'context', 0),
    ('terminal',           '终端产物',     '当前上下文中不作为任何已启用配方的原料',      'context', 0),
    ('intermediate',       '中间产物',     '当前上下文既可制造又被消耗',                  'context', 0),
    ('manufacture_target', '制造目标',     'UI 产出列表：craftable 且非 pure_raw',       'context', 1),
    ('supply_candidate',   '供给候选',     'UI 供给列表：在 scope 内且非 terminal',      'context', 1);

-- 分类上下文：一次「算完」的边界
CREATE TABLE catalog_context (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    context_kind    TEXT NOT NULL CHECK (context_kind IN ('save_progress', 'pack_full')),
    context_ref     TEXT NOT NULL,          -- save_progress.id 或 pack_key
    pack_key        TEXT NOT NULL REFERENCES recipe_pack(pack_key),
    rule_version    INTEGER NOT NULL DEFAULT 1,
    computed_at     TEXT NOT NULL,
    UNIQUE (context_kind, context_ref)
);

-- 物化：某上下文下每个 resource 的角色集合（多对多）
CREATE TABLE catalog_resource_role (
    catalog_context_id  INTEGER NOT NULL REFERENCES catalog_context(id) ON DELETE CASCADE,
    resource_id         INTEGER NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
    role_code           TEXT NOT NULL REFERENCES item_role_type(code),
    PRIMARY KEY (catalog_context_id, resource_id, role_code)
);

CREATE INDEX idx_catalog_role_lookup
    ON catalog_resource_role(catalog_context_id, role_code, resource_id);

-- UI 面板定义（列表按钮 = 显示逻辑，不是导入逻辑）
CREATE TABLE ui_catalog_panel (
    code            TEXT PRIMARY KEY,      -- manufacture | supply | all
    label_zh        TEXT NOT NULL,
    required_role   TEXT NOT NULL REFERENCES item_role_type(code),
    exclude_roles   TEXT,                  -- JSON array，如 ["internal","terminal"]
    sort_key        TEXT NOT NULL DEFAULT 'label'
);

INSERT INTO ui_catalog_panel (code, label_zh, required_role, exclude_roles) VALUES
    ('manufacture', '产出目标', 'manufacture_target', '["internal"]'),
    ('supply',      '外部供给', 'supply_candidate',   '["internal","terminal"]'),
    ('all',         '全部',     'craftable',          '["internal"]');

-- -----------------------------------------------------------------------------
-- C. 分类规则版本（逻辑变更时可批量重算）
-- -----------------------------------------------------------------------------

CREATE TABLE classification_rule_set (
    version         INTEGER PRIMARY KEY,
    description     TEXT NOT NULL,
    effective_at    TEXT NOT NULL
);

INSERT INTO classification_rule_set (version, description, effective_at) VALUES
    (1, '初版：pure_raw=raw_intrinsic∧¬craftable; terminal=¬ingredient; manufacture=craftable∧¬pure_raw; supply=scope∧¬terminal', datetime('now'));

-- -----------------------------------------------------------------------------
-- D. 推荐查询：UI 直接读物化角色，不再 JOIN 配方栈
-- -----------------------------------------------------------------------------

-- 产出目标列表（某存档进度上下文）
-- SELECT r.name, rl.label
-- FROM catalog_context cc
-- JOIN catalog_resource_role crr ON crr.catalog_context_id = cc.id
-- JOIN resource r ON r.id = crr.resource_id
-- JOIN resource_localization rl ON rl.resource_id = r.id AND rl.locale = 'zh-CN'
-- WHERE cc.context_kind = 'save_progress' AND cc.context_ref = ?
--   AND crr.role_code = 'manufacture_target'
-- ORDER BY rl.label;

-- -----------------------------------------------------------------------------
-- E. 上下文角色计算规则（ETL / 导入后 job 实现，文档化）
-- -----------------------------------------------------------------------------
--
-- 输入：
--   enabled_recipe_ids（save）或 全部 recipe（pack_full）
--   bundle_resource_graph
--   resource.is_raw, resource.visibility
--
-- craftable      = item 是 enabled 配方的 product
-- ingredient     = item 是 enabled 配方的 ingredient
-- pure_raw       = raw_intrinsic AND NOT craftable
-- terminal       = NOT ingredient（在 catalog scope 内的 item）
-- intermediate   = craftable AND ingredient
-- manufacture_target = craftable AND NOT pure_raw AND visibility=normal
-- supply_candidate   = (craftable OR ingredient) AND NOT terminal AND visibility=normal
--
-- catalog scope（与现逻辑一致）：
--   progress 模式：craftable ∪ ingredient 的物品集合
--   full 模式：visibility=normal 且 (is_producible OR is_consumed) 或全部 item
-- -----------------------------------------------------------------------------
