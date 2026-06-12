-- =============================================================================
-- 异星自平衡布局 — 终态数据库设计 (schema_final)
-- =============================================================================
--
-- 设计目标（从零推导，不兼容旧版）：
--   • 静态游戏数据：内容寻址、只写一次、可复用
--   • 运行环境：Factorio 版本 + 模组组合 + 语言 → 指向某份静态数据
--   • 存档状态：某存档在某环境下的「已启用配方」
--   • UI 分类：静态标签 + 上下文标签，物化后可 O(1) 查列表
--   • 布局计算：沿 recipe_flow 图遍历，用 save_recipe_gate 过滤
--
-- 不在本库做的事：
--   • 科技树推导进度（进度来源仍是 companion 的 enabled_recipes）
--   • 产能/机器数/蓝图（应用层或未来扩展）
--
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- §0 元数据
-- =============================================================================

CREATE TABLE meta_schema (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL,
    note        TEXT NOT NULL
);

CREATE TABLE meta_locale (
    code    TEXT PRIMARY KEY,
    name    TEXT NOT NULL
);

INSERT INTO meta_locale (code, name) VALUES ('zh-CN', '简体中文');

CREATE TABLE meta_recipe_category (
    code        TEXT PRIMARY KEY,
    label_zh    TEXT NOT NULL
);

-- ETL 时 INSERT OR IGNORE
-- crafting, smelting, chemistry, centrifuging, ...

-- =============================================================================
-- §1 静态内容平面 — 由 dump 内容 hash 唯一确定，不可变
-- =============================================================================

CREATE TABLE game_snapshot (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    content_sha256  TEXT NOT NULL UNIQUE,
    source_path     TEXT,
    item_count      INTEGER NOT NULL DEFAULT 0,
    recipe_count    INTEGER NOT NULL DEFAULT 0,
    fluid_count     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL
);

-- 统一资源：物品 + 流体
CREATE TABLE snap_resource (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id     INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL CHECK (kind IN ('item', 'fluid')),
    -- 原型静态属性（与存档无关）
    proto_type      TEXT,
    item_group      TEXT,
    item_subgroup   TEXT,
    expansion       TEXT NOT NULL DEFAULT 'base',
    icon            TEXT,
    stack_size      INTEGER,
    is_raw          INTEGER NOT NULL DEFAULT 0,
    visibility      TEXT NOT NULL DEFAULT 'normal'
        CHECK (visibility IN ('normal', 'internal', 'hidden')),
    UNIQUE (snapshot_id, kind, name)
);

CREATE TABLE snap_resource_text (
    resource_id     INTEGER NOT NULL REFERENCES snap_resource(id) ON DELETE CASCADE,
    locale          TEXT NOT NULL REFERENCES meta_locale(code),
    label           TEXT NOT NULL,
    description     TEXT,
    PRIMARY KEY (resource_id, locale)
);

CREATE TABLE snap_recipe (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id     INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    energy          REAL NOT NULL DEFAULT 0.5,
    hidden          INTEGER NOT NULL DEFAULT 0,
    expansion       TEXT NOT NULL DEFAULT 'base',
    main_product    TEXT,
    UNIQUE (snapshot_id, name)
);

CREATE TABLE snap_recipe_text (
    recipe_id       INTEGER NOT NULL REFERENCES snap_recipe(id) ON DELETE CASCADE,
    locale          TEXT NOT NULL REFERENCES meta_locale(code),
    label           TEXT NOT NULL,
    PRIMARY KEY (recipe_id, locale)
);

-- 配方流：单表表达原料(in)与产物(out)，避免 ingredient/product 双表重复结构
CREATE TABLE snap_recipe_flow (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id       INTEGER NOT NULL REFERENCES snap_recipe(id) ON DELETE CASCADE,
    direction       TEXT NOT NULL CHECK (direction IN ('in', 'out')),
    resource_kind   TEXT NOT NULL CHECK (resource_kind IN ('item', 'fluid')),
    resource_name   TEXT NOT NULL,
    amount          REAL NOT NULL,
    probability     REAL,
    ord             INTEGER NOT NULL DEFAULT 0
);

-- 全配方图统计（ETL 一次写入；与存档无关）
CREATE TABLE snap_resource_stats (
    snapshot_id         INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    resource_id         INTEGER NOT NULL REFERENCES snap_resource(id) ON DELETE CASCADE,
    recipes_as_output   INTEGER NOT NULL DEFAULT 0,
    recipes_as_input    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (snapshot_id, resource_id)
);

CREATE INDEX idx_flow_recipe ON snap_recipe_flow(recipe_id, direction);
CREATE INDEX idx_flow_resource ON snap_recipe_flow(resource_kind, resource_name);
CREATE INDEX idx_snap_recipe ON snap_recipe(snapshot_id, name);
CREATE INDEX idx_snap_resource ON snap_resource(snapshot_id, kind, name);
CREATE INDEX idx_stats_output ON snap_resource_stats(snapshot_id, recipes_as_output);

-- =============================================================================
-- §2 运行环境 — 用户感知的「配方包 / 版本 + mod 组合」
-- =============================================================================

CREATE TABLE game_environment (
    env_key             TEXT PRIMARY KEY,
    -- 格式: {factorio_version}__{mod_fp16}__{locale}
    factorio_version    TEXT NOT NULL,
    mod_fingerprint     TEXT NOT NULL,
    locale              TEXT NOT NULL DEFAULT 'zh-CN' REFERENCES meta_locale(code),
    snapshot_id         INTEGER NOT NULL REFERENCES game_snapshot(id),
    label               TEXT,
    last_used_at        TEXT,
    created_at          TEXT NOT NULL,
    UNIQUE (factorio_version, mod_fingerprint, locale)
);

CREATE TABLE environment_mod (
    env_key         TEXT NOT NULL REFERENCES game_environment(env_key) ON DELETE CASCADE,
    mod_name        TEXT NOT NULL,
    mod_version     TEXT,
    sort_ord        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (env_key, mod_name)
);

CREATE INDEX idx_env_snapshot ON game_environment(snapshot_id);
CREATE INDEX idx_env_last_used ON game_environment(last_used_at);

-- =============================================================================
-- §3 存档与解锁 — 进度 = 某环境下的一组已启用 recipe
-- =============================================================================

CREATE TABLE game_save (
    save_key        TEXT PRIMARY KEY,
    save_path       TEXT NOT NULL,
    save_mtime      REAL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE save_binding (
    save_key            TEXT PRIMARY KEY REFERENCES game_save(save_key) ON DELETE CASCADE,
    env_key             TEXT NOT NULL REFERENCES game_environment(env_key),
    exported_tick       INTEGER,
    imported_at         TEXT NOT NULL,
    enabled_count       INTEGER NOT NULL DEFAULT 0
);

-- 进度来源：companion force.recipes.enabled（准确）
CREATE TABLE save_recipe_gate (
    save_key        TEXT NOT NULL REFERENCES save_binding(save_key) ON DELETE CASCADE,
    recipe_id       INTEGER NOT NULL REFERENCES snap_recipe(id) ON DELETE CASCADE,
    PRIMARY KEY (save_key, recipe_id)
);

-- 冗余名：snapshot 重建后仍可诊断
CREATE TABLE save_recipe_gate_name (
    save_key        TEXT NOT NULL REFERENCES save_binding(save_key) ON DELETE CASCADE,
    recipe_name     TEXT NOT NULL,
    PRIMARY KEY (save_key, recipe_name)
);

CREATE INDEX idx_gate_save ON save_recipe_gate(save_key);

-- =============================================================================
-- §4 UI 分类子系统 — 静态 tag + 上下文 tag，物化后供 API 直接读
-- =============================================================================

-- tag 定义：分三层，避免把「终端产物」写进 snap_resource 列
CREATE TABLE tag_spec (
    code            TEXT PRIMARY KEY,
    layer           TEXT NOT NULL CHECK (layer IN ('static', 'graph', 'context')),
    label_zh        TEXT NOT NULL,
    description     TEXT NOT NULL
);

INSERT INTO tag_spec (code, layer, label_zh, description) VALUES
    ('internal',        'static',  '内部项',     'parameter-* 等不应展示'),
    ('raw',             'static',  '原型原料',   '原型 is_raw，通常为矿/水'),
    ('producible',      'graph',   '可产出',     '在全 snapshot 中至少一条配方产出'),
    ('consumable',      'graph',   '可消耗',     '在全 snapshot 中至少作为原料'),
    ('craftable',       'context', '当前可制造', '当前 gate 内配方可产出'),
    ('used_as_input',   'context', '当前原料',   '当前 gate 内配方会消耗'),
    ('pure_raw',        'context', '纯粹原料',   'raw 且当前不可制造'),
    ('terminal',        'context', '终端产物',   '当前上下文中不作为任何 gate 内配方原料'),
    ('intermediate',    'context', '中间产物',   '当前可制造且会被消耗'),
    ('manufacture',     'context', '制造目标',   'UI 产出列表'),
    ('supply',          'context', '供给候选',   'UI 供给列表');

-- 分类规则版本：逻辑变更时 bump，触发重算
CREATE TABLE tag_rule_version (
    version         INTEGER PRIMARY KEY,
    spec            TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

INSERT INTO tag_rule_version (version, spec, created_at) VALUES (
    1,
    'pure_raw=raw+craftable; terminal=!used_as_input; manufacture=craftable+!pure_raw; supply=scope+!terminal; scope=craftable|used_as_input',
    datetime('now')
);

-- 一次「算完」的边界
CREATE TABLE catalog_build (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_kind      TEXT NOT NULL CHECK (scope_kind IN ('save', 'environment')),
    scope_key       TEXT NOT NULL,
    env_key         TEXT NOT NULL REFERENCES game_environment(env_key),
    rule_version    INTEGER NOT NULL REFERENCES tag_rule_version(version),
    built_at        TEXT NOT NULL,
    UNIQUE (scope_kind, scope_key)
);

-- scope_kind='save'     → scope_key = save_key     （仅当前进度）
-- scope_kind='environment' → scope_key = env_key   （完整全配方，gate=全部 recipe）

CREATE TABLE catalog_tag (
    build_id        INTEGER NOT NULL REFERENCES catalog_build(id) ON DELETE CASCADE,
    resource_id     INTEGER NOT NULL REFERENCES snap_resource(id) ON DELETE CASCADE,
    tag_code        TEXT NOT NULL REFERENCES tag_spec(code),
    PRIMARY KEY (build_id, resource_id, tag_code)
);

CREATE INDEX idx_catalog_tag_query ON catalog_tag(build_id, tag_code, resource_id);

-- UI 面板 = 对 tag 的声明式过滤（列表按钮只是显示逻辑）
CREATE TABLE ui_panel (
    code            TEXT PRIMARY KEY,
    label_zh        TEXT NOT NULL,
    require_tag     TEXT NOT NULL REFERENCES tag_spec(code),
    exclude_tags    TEXT NOT NULL DEFAULT '[]',
    sort_by         TEXT NOT NULL DEFAULT 'label'
);

INSERT INTO ui_panel (code, label_zh, require_tag, exclude_tags) VALUES
    ('manufacture', '产出目标', 'manufacture', '["internal"]'),
    ('supply',      '外部供给', 'supply',      '["internal","terminal"]'),
    ('all',         '全部物品', 'craftable',   '["internal"]');

-- =============================================================================
-- §5 应用状态与运维
-- =============================================================================

CREATE TABLE app_state (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    active_save_key     TEXT REFERENCES game_save(save_key) ON DELETE SET NULL,
    active_panel        TEXT NOT NULL DEFAULT 'manufacture',
    catalog_scope       TEXT NOT NULL DEFAULT 'save'
        CHECK (catalog_scope IN ('save', 'environment')),
    updated_at          TEXT
);

INSERT INTO app_state (id) VALUES (1);

CREATE TABLE import_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kind            TEXT NOT NULL CHECK (kind IN ('snapshot_dump', 'save_export')),
    env_key         TEXT REFERENCES game_environment(env_key),
    save_key        TEXT REFERENCES game_save(save_key),
    status          TEXT NOT NULL CHECK (status IN ('running', 'ok', 'failed')),
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    message         TEXT,
    detail_json     TEXT
);

-- =============================================================================
-- §6 视图 — 常用查询
-- =============================================================================

CREATE VIEW v_environment_usage AS
SELECT
    e.env_key,
    e.label,
    e.last_used_at,
    e.snapshot_id,
    s.content_sha256,
    COUNT(DISTINCT b.save_key) AS save_count
FROM game_environment e
JOIN game_snapshot s ON s.id = e.snapshot_id
LEFT JOIN save_binding b ON b.env_key = e.env_key
GROUP BY e.env_key;

-- UI：产出目标（save 上下文）
-- SELECT sr.name, srt.label
-- FROM catalog_build cb
-- JOIN catalog_tag ct ON ct.build_id = cb.id AND ct.tag_code = 'manufacture'
-- JOIN snap_resource sr ON sr.id = ct.resource_id
-- JOIN snap_resource_text srt ON srt.resource_id = sr.id AND srt.locale = 'zh-CN'
-- WHERE cb.scope_kind = 'save' AND cb.scope_key = :save_key
-- ORDER BY srt.label;

-- =============================================================================
-- §7 分类计算伪算法（由应用层 CatalogBuilder 实现，非 SQL）
-- =============================================================================
--
-- 阶段 A — ETL 后（static + graph）：
--   internal  ← visibility = 'internal'
--   raw       ← is_raw = 1
--   producible← snap_resource_stats.recipes_as_output > 0
--   consumable← snap_resource_stats.recipes_as_input > 0
--
-- 阶段 B — 导入存档 / 切换 scope 后（context，gate = save_recipe_gate 或 全 snap_recipe）：
--   craftable     ← item 是 gate 配方的 out 流
--   used_as_input ← item 是 gate 配方的 in 流
--   pure_raw      ← raw ∧ ¬craftable
--   terminal      ← ¬used_as_input（在 scope 集合内）
--   intermediate  ← craftable ∧ used_as_input
--   manufacture   ← craftable ∧ ¬pure_raw ∧ visibility=normal
--   supply        ← (craftable ∨ used_as_input) ∧ ¬terminal ∧ visibility=normal
--
-- scope 集合（与现逻辑一致）：
--   save  scope: craftable ∪ used_as_input
--   full  scope: visibility=normal ∧ (producible ∨ consumable)
--
-- =============================================================================
