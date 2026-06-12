-- =============================================================================
-- 异星自平衡布局 — 完整版 SQLite Schema (v3 设计稿)
-- =============================================================================
-- 设计原则
--   1. 配方包 (recipe_pack) = 某次「游戏版本 + 模组组合 + 语言」下的完整静态数据快照
--   2. 存档进度 (save_progress) = 在某个配方包上的「已启用配方」过滤视图
--   3. 内容寻址：相同 dump 内容 (dump_sha256) 只存一份，多个 pack_key 可共享
--   4. 业务主键 pack_key 人类可读：{factorio_version}__{mod_fingerprint}
--   5. 存档业务主键 save_key = 存档显示名 (不含 .zip)
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 0. 迁移与元数据
-- -----------------------------------------------------------------------------

CREATE TABLE schema_migration (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE locale_code (
    code        TEXT PRIMARY KEY,          -- zh-CN, en
    label       TEXT NOT NULL
);

INSERT OR IGNORE INTO locale_code (code, label) VALUES ('zh-CN', '简体中文');

-- -----------------------------------------------------------------------------
-- 1. 模组与版本维度
-- -----------------------------------------------------------------------------

-- Factorio 客户端版本（如 2.0.76）
CREATE TABLE factorio_version (
    version     TEXT PRIMARY KEY,          -- 2.0.76
    label       TEXT,
    first_seen  TEXT NOT NULL
);

-- 单个模组发行版（base、space-age、某第三方 mod）
CREATE TABLE mod_release (
    mod_name    TEXT NOT NULL,             -- base, space-age
    mod_version TEXT NOT NULL,             -- 2.0.76
    title       TEXT,
    PRIMARY KEY (mod_name, mod_version)
);

-- 一次启用的模组组合（原版 only、SA、带 mod 等）
CREATE TABLE mod_set (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint     TEXT NOT NULL UNIQUE,  -- sha256(sorted "name@ver")[:16]
    display_label   TEXT,                  -- "base + space-age"
    created_at      TEXT NOT NULL
);

CREATE TABLE mod_set_member (
    mod_set_id   INTEGER NOT NULL REFERENCES mod_set(id) ON DELETE CASCADE,
    mod_name     TEXT NOT NULL,
    mod_version  TEXT NOT NULL,
    PRIMARY KEY (mod_set_id, mod_name),
    FOREIGN KEY (mod_name, mod_version) REFERENCES mod_release(mod_name, mod_version)
);

-- -----------------------------------------------------------------------------
-- 2. 配方包（你的「1」— 完整配方集合的入口）
-- -----------------------------------------------------------------------------

-- 不可变内容快照：由 Factorio dump 内容 hash 唯一确定
CREATE TABLE content_bundle (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dump_sha256     TEXT NOT NULL UNIQUE,
    dump_path       TEXT,                  -- 磁盘上的 data-raw-dump.json
    item_count      INTEGER NOT NULL DEFAULT 0,
    recipe_count    INTEGER NOT NULL DEFAULT 0,
    fluid_count     INTEGER NOT NULL DEFAULT 0,
    ingested_at     TEXT NOT NULL,
    ingest_status   TEXT NOT NULL DEFAULT 'ready'  -- pending | ready | failed
);

-- 配方包：面向业务的「名称_版本」入口
-- pack_key 示例: "2.0.76__a1b2c3d4e5f67890"  (游戏版本__模组指纹)
CREATE TABLE recipe_pack (
    pack_key            TEXT PRIMARY KEY,
    factorio_version    TEXT NOT NULL REFERENCES factorio_version(version),
    mod_set_id          INTEGER NOT NULL REFERENCES mod_set(id),
    locale              TEXT NOT NULL DEFAULT 'zh-CN' REFERENCES locale_code(code),
    content_bundle_id   INTEGER NOT NULL REFERENCES content_bundle(id),
    display_name        TEXT,              -- UI 用，如 "2.0.76 · Space Age"
    last_used_at        TEXT,              -- 上一次被导入/引用时间（清理依据）
    created_at          TEXT NOT NULL,
    UNIQUE (factorio_version, mod_set_id, locale)
);

CREATE INDEX idx_recipe_pack_last_used ON recipe_pack(last_used_at);
CREATE INDEX idx_recipe_pack_bundle ON recipe_pack(content_bundle_id);

-- -----------------------------------------------------------------------------
-- 3. 物品（你的「3」）
-- -----------------------------------------------------------------------------

CREATE TABLE item (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    content_bundle_id INTEGER NOT NULL REFERENCES content_bundle(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,         -- iron-plate
    prototype_type  TEXT NOT NULL DEFAULT 'item',  -- item | tool | armor | module ...
    item_group      TEXT,                  -- intermediate-product
    item_subgroup   TEXT,                  -- raw-material
    is_raw          INTEGER NOT NULL DEFAULT 0,
    expansion       TEXT NOT NULL DEFAULT 'base',  -- base | space-age
    icon            TEXT,                  -- 图标路径或 icon 字段
    stack_size      INTEGER,
    UNIQUE (content_bundle_id, name)
);

CREATE TABLE item_localization (
    item_id         INTEGER NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    locale          TEXT NOT NULL REFERENCES locale_code(code),
    label           TEXT NOT NULL,
    description     TEXT,
    PRIMARY KEY (item_id, locale)
);

CREATE INDEX idx_item_bundle_name ON item(content_bundle_id, name);
CREATE INDEX idx_item_localization_locale ON item_localization(locale);

-- -----------------------------------------------------------------------------
-- 4. 流体（与物品并列的资源类型）
-- -----------------------------------------------------------------------------

CREATE TABLE fluid (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    content_bundle_id INTEGER NOT NULL REFERENCES content_bundle(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    expansion       TEXT NOT NULL DEFAULT 'base',
    default_temperature REAL,
    UNIQUE (content_bundle_id, name)
);

CREATE TABLE fluid_localization (
    fluid_id        INTEGER NOT NULL REFERENCES fluid(id) ON DELETE CASCADE,
    locale          TEXT NOT NULL REFERENCES locale_code(code),
    label           TEXT NOT NULL,
    PRIMARY KEY (fluid_id, locale)
);

-- -----------------------------------------------------------------------------
-- 5. 配方（你的「2」— 通过明细表指向物品/流体）
-- -----------------------------------------------------------------------------

CREATE TABLE recipe_category (
    name        TEXT PRIMARY KEY,          -- crafting, smelting, chemistry ...
    label       TEXT
);

CREATE TABLE recipe (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    content_bundle_id INTEGER NOT NULL REFERENCES content_bundle(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,         -- advanced-circuit
    category        TEXT NOT NULL REFERENCES recipe_category(name),
    energy          REAL NOT NULL DEFAULT 0.5,
    hidden          INTEGER NOT NULL DEFAULT 0,
    enabled_by_default INTEGER NOT NULL DEFAULT 1,
    main_product    TEXT,                  -- 主产物 item/fluid 名
    expansion       TEXT NOT NULL DEFAULT 'base',
    UNIQUE (content_bundle_id, name)
);

CREATE TABLE recipe_localization (
    recipe_id       INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    locale          TEXT NOT NULL REFERENCES locale_code(code),
    label           TEXT NOT NULL,
    PRIMARY KEY (recipe_id, locale)
);

-- 配方原料（多对多：recipe → item/fluid）
CREATE TABLE recipe_ingredient (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id       INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    resource_kind   TEXT NOT NULL CHECK (resource_kind IN ('item', 'fluid')),
    resource_name   TEXT NOT NULL,
    amount          REAL NOT NULL,
    sort_order      INTEGER NOT NULL DEFAULT 0
);

-- 配方产物
CREATE TABLE recipe_product (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id       INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    resource_kind   TEXT NOT NULL CHECK (resource_kind IN ('item', 'fluid')),
    resource_name   TEXT NOT NULL,
    amount          REAL NOT NULL,
    probability     REAL,                  -- 概率产物（可选）
    sort_order      INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_recipe_bundle_name ON recipe(content_bundle_id, name);
CREATE INDEX idx_recipe_ingredient_resource ON recipe_ingredient(recipe_id, resource_kind, resource_name);
CREATE INDEX idx_recipe_product_resource ON recipe_product(recipe_id, resource_kind, resource_name);
CREATE INDEX idx_recipe_product_by_item ON recipe_product(resource_kind, resource_name);

-- 可选：产物 → 配方的反查（布局/catalog 热路径）
CREATE TABLE recipe_product_index (
    content_bundle_id INTEGER NOT NULL,
    resource_kind     TEXT NOT NULL,
    resource_name     TEXT NOT NULL,
    recipe_id         INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    PRIMARY KEY (content_bundle_id, resource_kind, resource_name, recipe_id)
);

-- -----------------------------------------------------------------------------
-- 6. 科技（辅助；进度仍以 enabled_recipe 为准）
-- -----------------------------------------------------------------------------

CREATE TABLE technology (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    content_bundle_id INTEGER NOT NULL REFERENCES content_bundle(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    UNIQUE (content_bundle_id, name)
);

CREATE TABLE technology_localization (
    technology_id   INTEGER NOT NULL REFERENCES technology(id) ON DELETE CASCADE,
    locale          TEXT NOT NULL REFERENCES locale_code(code),
    label           TEXT NOT NULL,
    PRIMARY KEY (technology_id, locale)
);

CREATE TABLE technology_unlocks_recipe (
    technology_id   INTEGER NOT NULL REFERENCES technology(id) ON DELETE CASCADE,
    recipe_id       INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    PRIMARY KEY (technology_id, recipe_id)
);

CREATE TABLE technology_prerequisite (
    technology_id       INTEGER NOT NULL REFERENCES technology(id) ON DELETE CASCADE,
    prerequisite_id     INTEGER NOT NULL REFERENCES technology(id) ON DELETE CASCADE,
    PRIMARY KEY (technology_id, prerequisite_id)
);

-- -----------------------------------------------------------------------------
-- 7. 存档进度（你的「4」）
-- -----------------------------------------------------------------------------

-- 存档实体：以存档名为业务主键
CREATE TABLE save_file (
    save_key        TEXT PRIMARY KEY,      -- 存档名，如 "new relax world"
    save_path       TEXT NOT NULL,         -- 当前磁盘路径（可变）
    save_mtime      REAL,
    first_imported  TEXT NOT NULL,
    last_imported   TEXT NOT NULL
);

-- 进度快照：每个 save_key 仅保留最新一条（导入时 UPSERT）
CREATE TABLE save_progress (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    save_key            TEXT NOT NULL UNIQUE REFERENCES save_file(save_key) ON DELETE CASCADE,
    pack_key            TEXT NOT NULL REFERENCES recipe_pack(pack_key),
    exported_at_tick    INTEGER,
    imported_at         TEXT NOT NULL,
    enabled_recipe_count INTEGER NOT NULL DEFAULT 0,
    researched_tech_count INTEGER NOT NULL DEFAULT 0
);

-- 解锁进度：已启用配方（来源 companion 模组 force.recipes，最准确）
CREATE TABLE save_enabled_recipe (
    save_progress_id    INTEGER NOT NULL REFERENCES save_progress(id) ON DELETE CASCADE,
    recipe_id           INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    PRIMARY KEY (save_progress_id, recipe_id)
);

-- 冗余 recipe_name 便于跨版本诊断 / pack 重建后 fallback 匹配
CREATE TABLE save_enabled_recipe_name (
    save_progress_id    INTEGER NOT NULL REFERENCES save_progress(id) ON DELETE CASCADE,
    recipe_name         TEXT NOT NULL,
    PRIMARY KEY (save_progress_id, recipe_name)
);

CREATE TABLE save_researched_technology (
    save_progress_id    INTEGER NOT NULL REFERENCES save_progress(id) ON DELETE CASCADE,
    technology_id       INTEGER REFERENCES technology(id) ON DELETE SET NULL,
    tech_name           TEXT NOT NULL,
    PRIMARY KEY (save_progress_id, tech_name)
);

CREATE INDEX idx_save_enabled_recipe ON save_enabled_recipe(save_progress_id);
CREATE INDEX idx_save_progress_pack ON save_progress(pack_key);

-- -----------------------------------------------------------------------------
-- 8. 物化视图 / 缓存（catalog 热路径，可选但推荐）
-- -----------------------------------------------------------------------------

CREATE TABLE catalog_cache (
    save_progress_id    INTEGER NOT NULL REFERENCES save_progress(id) ON DELETE CASCADE,
    view_mode           TEXT NOT NULL CHECK (view_mode IN ('progress', 'full')),
    manufacture_json    TEXT NOT NULL,     -- JSON array of ItemInfo
    supply_json         TEXT NOT NULL,
    computed_at         TEXT NOT NULL,
    PRIMARY KEY (save_progress_id, view_mode)
);

-- full 模式无 save_progress 时，按 pack_key 缓存
CREATE TABLE pack_catalog_cache (
    pack_key            TEXT NOT NULL REFERENCES recipe_pack(pack_key) ON DELETE CASCADE,
    manufacture_json    TEXT NOT NULL,
    supply_json         TEXT NOT NULL,
    computed_at         TEXT NOT NULL,
    PRIMARY KEY (pack_key)
);

-- -----------------------------------------------------------------------------
-- 9. 导入任务与其它（你的「5」）
-- -----------------------------------------------------------------------------

CREATE TABLE ingest_job (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type            TEXT NOT NULL,     -- dump_pack | export_progress
    pack_key            TEXT REFERENCES recipe_pack(pack_key),
    save_key            TEXT REFERENCES save_file(save_key),
    status              TEXT NOT NULL,     -- running | success | failed
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    error_message       TEXT,
    warnings_json       TEXT
);

CREATE TABLE app_session (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    active_save_key     TEXT REFERENCES save_file(save_key) ON DELETE SET NULL,
    catalog_view_mode   TEXT NOT NULL DEFAULT 'progress',  -- progress | full
    updated_at          TEXT
);

INSERT OR IGNORE INTO app_session (id) VALUES (1);

-- -----------------------------------------------------------------------------
-- 10. 清理策略辅助
-- -----------------------------------------------------------------------------

-- 记录 pack 被哪些存档引用（冗余，加速 purge；也可运行时 JOIN）
CREATE VIEW v_pack_usage AS
SELECT
    rp.pack_key,
    rp.last_used_at,
    rp.content_bundle_id,
    COUNT(sp.id) AS save_ref_count
FROM recipe_pack rp
LEFT JOIN save_progress sp ON sp.pack_key = rp.pack_key
GROUP BY rp.pack_key;
