-- =============================================================================
-- 异星自平衡布局 — 终态数据库设计 (schema_final)
-- =============================================================================
--
-- 设计目标（从零推导，不兼容旧版）：
--   • 静态游戏数据：内容寻址、只写一次、可复用
--   • 运行环境：Factorio 版本 + 模组组合 + 语言 → 指向某份静态数据
--   • 存档状态：某存档在某环境下的「已启用配方」
--   • UI 分类：intrinsic tag（资源/配方语义）+ context tag，物化后 O(1) 查询
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

-- 地图资源实体（type=resource：矿脉、油井等）
CREATE TABLE snap_map_resource (
    snapshot_id     INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    category        TEXT,
    infinite        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (snapshot_id, name)
);

-- 抽取建筑（mining-drill / offshore-pump 等）
CREATE TABLE snap_extractor (
    snapshot_id         INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    entity_name         TEXT NOT NULL,
    entity_type         TEXT NOT NULL,
    resource_categories TEXT,
    output_kind         TEXT CHECK (output_kind IS NULL OR output_kind IN ('item', 'fluid')),
    output_name         TEXT,
    PRIMARY KEY (snapshot_id, entity_name)
);

-- 世界来源 → 产出物（百科「如何获得」的静态数据层）
CREATE TABLE snap_resource_extraction (
    snapshot_id         INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    resource_kind       TEXT NOT NULL CHECK (resource_kind IN ('item', 'fluid')),
    resource_name       TEXT NOT NULL,
    source_type         TEXT NOT NULL,
    source_name         TEXT NOT NULL,
    extractor_entity    TEXT,
    resource_category   TEXT,
    PRIMARY KEY (snapshot_id, resource_kind, resource_name, source_type, source_name)
);

CREATE INDEX idx_extraction_resource ON snap_resource_extraction(snapshot_id, resource_name);
CREATE INDEX idx_extraction_entity ON snap_resource_extraction(snapshot_id, extractor_entity);

-- Layer IR — 资源语义 tag（ETL 写入，与存档无关）
CREATE TABLE meta_tag (
    code            TEXT PRIMARY KEY,
    layer           TEXT NOT NULL CHECK (layer IN (
        'intrinsic_resource', 'intrinsic_recipe', 'graph', 'context'
    )),
    label_zh        TEXT NOT NULL,
    description     TEXT NOT NULL
);

INSERT INTO meta_tag (code, layer, label_zh, description) VALUES
    ('ir.internal',           'intrinsic_resource', '内部项',       'parameter-* 等'),
    ('ir.extractable',        'intrinsic_resource', '可抽取原料',   'snap_resource_extraction 或 item.subgroup=raw-resource'),
    ('ir.fluid',              'intrinsic_resource', '流体',         'kind=fluid'),
    ('ir.item',               'intrinsic_resource', '物品',         'kind=item'),
    ('ir.container.barrel',   'intrinsic_resource', '桶装容器',     '*-barrel 物品'),
    ('ip.extract',            'intrinsic_recipe',   '抽取',         '泵/矿机等主产线源头'),
    ('ip.smelting',           'intrinsic_recipe',   '冶炼',         'smelting'),
    ('ip.craft',              'intrinsic_recipe',   '制造',         'crafting 等'),
    ('ip.chemistry',          'intrinsic_recipe',   '化工',         'chemistry'),
    ('ip.refining',           'intrinsic_recipe',   '炼油',         'oil-processing 等'),
    ('ip.barrel.fill',        'intrinsic_recipe',   '装桶',         'fill-*-barrel'),
    ('ip.barrel.empty',       'intrinsic_recipe',   '倒桶',         'empty-*-barrel'),
    ('ip.excluded',           'intrinsic_recipe',   '排除',         '永不参与闭包'),
    ('producible',            'graph',              '可产出',       '全 snapshot 至少一条配方产出'),
    ('consumable',            'graph',              '可消耗',       '全 snapshot 至少作为原料'),
    ('craftable',             'context',            '可制造',       'gate 内 primary 配方可产出'),
    ('craftable_logistics_only','context',          '仅物流可产',   'gate 内仅有 logistics 配方产出'),
    ('used_as_input',         'context',            '配方原料',     'gate 内被消耗'),
    ('baseline_supply',       'context',            '基础供给物',   'ir.extractable'),
    ('pure_supply',           'context',            '默认外部供给', '基础且当前无 primary 产法'),
    ('closure_expandable',    'context',            '可闭包展开',   '应用 primary 配方制造'),
    ('intermediate',          'context',            '中间产物',     '可展开且被消耗'),
    ('terminal',              'context',            '终端产物',     '可展开且不被消耗'),
    ('manufacture',           'context',            '制造目标',     'UI 产出列表'),
    ('supply',                'context',            '供给候选',     'UI 供给列表'),
    ('internal',              'context',            '内部项',       'visibility=internal');

CREATE TABLE snap_resource_intrinsic_tag (
    snapshot_id     INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    resource_id     INTEGER NOT NULL REFERENCES snap_resource(id) ON DELETE CASCADE,
    tag_code        TEXT NOT NULL REFERENCES meta_tag(code),
    params_json     TEXT,
    PRIMARY KEY (snapshot_id, resource_id, tag_code)
);

CREATE TABLE snap_recipe_intrinsic_tag (
    snapshot_id     INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    recipe_id       INTEGER NOT NULL REFERENCES snap_recipe(id) ON DELETE CASCADE,
    tag_code        TEXT NOT NULL REFERENCES meta_tag(code),
    params_json     TEXT,
    PRIMARY KEY (snapshot_id, recipe_id, tag_code)
);

CREATE TABLE snap_recipe_closure_role (
    snapshot_id     INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    recipe_id       INTEGER NOT NULL REFERENCES snap_recipe(id) ON DELETE CASCADE,
    closure_role    TEXT NOT NULL CHECK (closure_role IN ('primary', 'logistics', 'excluded')),
    PRIMARY KEY (snapshot_id, recipe_id)
);

CREATE TABLE snap_resource_stats_primary (
    snapshot_id                 INTEGER NOT NULL REFERENCES game_snapshot(id) ON DELETE CASCADE,
    resource_id                 INTEGER NOT NULL REFERENCES snap_resource(id) ON DELETE CASCADE,
    recipes_as_output_primary   INTEGER NOT NULL DEFAULT 0,
    recipes_as_input_primary    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (snapshot_id, resource_id)
);

CREATE TABLE intrinsic_tag_override (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id     INTEGER REFERENCES game_snapshot(id) ON DELETE CASCADE,
    target_kind     TEXT NOT NULL CHECK (target_kind IN ('resource', 'recipe')),
    target_name     TEXT NOT NULL,
    add_tags        TEXT NOT NULL DEFAULT '[]',
    remove_tags     TEXT NOT NULL DEFAULT '[]',
    reason          TEXT NOT NULL,
    UNIQUE (snapshot_id, target_kind, target_name)
);

CREATE INDEX idx_resource_intrinsic ON snap_resource_intrinsic_tag(snapshot_id, tag_code);
CREATE INDEX idx_recipe_closure ON snap_recipe_closure_role(snapshot_id, closure_role);

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
-- §4 UI 分类子系统 — intrinsic + context tag，物化后供 API 直接读
-- =============================================================================

CREATE TABLE tag_rule_version (
    version         INTEGER PRIMARY KEY,
    spec            TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

INSERT INTO tag_rule_version (version, spec, created_at) VALUES (
    3,
    'baseline=world_extraction∨raw-resource; closure_expandable=primary_out∨(extractable∧extractor_unlocked); pure_supply=baseline∧¬closure_expandable',
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
    tag_code        TEXT NOT NULL REFERENCES meta_tag(code),
    PRIMARY KEY (build_id, resource_id, tag_code)
);

CREATE INDEX idx_catalog_tag_query ON catalog_tag(build_id, tag_code, resource_id);

-- UI 面板 = 对 tag 的声明式过滤（列表按钮只是显示逻辑）
CREATE TABLE ui_panel (
    code            TEXT PRIMARY KEY,
    label_zh        TEXT NOT NULL,
    require_tag     TEXT NOT NULL REFERENCES meta_tag(code),
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
-- §7 分类计算（CatalogBuilder v2 + IntrinsicClassifier）
-- =============================================================================
--
-- ETL 后 intrinsic：
--   extraction_etl → snap_map_resource / snap_extractor / snap_resource_extraction / fb-extract:* 配方
--   ResourceIntrinsicClassifier → snap_resource_intrinsic_tag, is_raw
--   RecipeIntrinsicClassifier   → snap_recipe_intrinsic_tag, snap_recipe_closure_role
--
-- Context（gate = save_recipe_gate 或全 snap_recipe）：
--   primary_out(M)     = M 是 enabled primary 配方的产物
--   extractable_out    = 抽取建筑已解锁 ∧ snap_resource_extraction 产出 M
--   closure_expandable = primary_out ∪ extractable_out
--   baseline_supply    = ir.extractable（来自地图实体，非手写名单）
--   pure_supply        = baseline_supply ∧ ¬closure_expandable(M)
--   used_as_input      = gate 内 in 流
--   terminal           = closure_expandable ∧ ¬used_as_input
--   intermediate       = closure_expandable ∧ used_as_input
--   manufacture        = closure_expandable ∧ ¬ir.container.barrel
--   supply             = (baseline ∨ used_as_input ∨ pure_supply) ∧ ¬terminal
--
-- 分析闭包仅使用 closure_role=primary 的配方。
--
-- =============================================================================

-- =============================================================================
-- §8 布局计算历史 — 完整请求/响应快照（合并图 + SBTO + 坐标）
-- =============================================================================

CREATE TABLE layout_compute_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    save_key        TEXT,
    env_key         TEXT,
    catalog_mode    TEXT NOT NULL DEFAULT 'progress',
    supply_mode     TEXT NOT NULL DEFAULT 'raw',
    target_summary  TEXT NOT NULL,
    target_count    INTEGER NOT NULL DEFAULT 0,
    node_count      INTEGER NOT NULL DEFAULT 0,
    edge_count      INTEGER NOT NULL DEFAULT 0,
    tap_count       INTEGER NOT NULL DEFAULT 0,
    request_json    TEXT NOT NULL,
    response_json   TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX idx_layout_history_created ON layout_compute_history(created_at DESC);
CREATE INDEX idx_layout_history_save ON layout_compute_history(save_key);
