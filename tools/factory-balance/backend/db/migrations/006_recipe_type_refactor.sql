-- =============================================================================
-- Migration 006: recipe_type / source metadata refactor
--
-- 目标：把世界开采从 "fb-extract:" 前缀 hack 提升为正式的 recipe_type='extraction'，
--      并在 snap_recipe 上附加 source_type、extractor_entity 等元数据。
--      不保留对 fb-extract:* 名称的旧兼容。
-- =============================================================================

PRAGMA foreign_keys = ON;

ALTER TABLE snap_recipe ADD COLUMN recipe_type TEXT NOT NULL DEFAULT 'manufacturing'
    CHECK (recipe_type IN ('extraction','manufacturing','smelting','chemistry','refining','logistics','energy'));

ALTER TABLE snap_recipe ADD COLUMN source_type TEXT
    CHECK (source_type IN ('map_resource','fluid_well','offshore_pump','catch','tree_harvest','enemy_drop','space_platform'));

ALTER TABLE snap_recipe ADD COLUMN extractor_entity TEXT;
ALTER TABLE snap_recipe ADD COLUMN resource_category TEXT;
ALTER TABLE snap_recipe ADD COLUMN location TEXT;
ALTER TABLE snap_recipe ADD COLUMN base_rate REAL;

-- 迁移旧的 fb-extract:* 合成配方：改名为 extract:{name}，并标记为 extraction
UPDATE snap_recipe
SET
    recipe_type = 'extraction',
    source_type = CASE
        WHEN category = 'pumping' THEN 'offshore_pump'
        ELSE 'map_resource'
    END,
    extractor_entity = CASE
        WHEN category = 'pumping' THEN 'offshore-pump'
        ELSE 'electric-mining-drill'
    END,
    name = 'extract:' || SUBSTR(name, LENGTH('fb-extract:') + 1)
WHERE name LIKE 'fb-extract:%';

-- 旧快照中保存的 request/response 可能引用 fb-extract:*，此处不做兼容；
-- 布局快照属于历史数据，本次破坏性重构后旧快照可能无法精确还原，但不会被删除。

-- 更新所有非 extraction 的已有配方：按 category 推断 recipe_type
UPDATE snap_recipe SET recipe_type = 'smelting'    WHERE recipe_type = 'manufacturing' AND category IN ('smelting');
UPDATE snap_recipe SET recipe_type = 'chemistry'   WHERE recipe_type = 'manufacturing' AND category IN ('chemistry');
UPDATE snap_recipe SET recipe_type = 'refining'    WHERE recipe_type = 'manufacturing' AND category IN ('oil-processing','advanced-oil-processing','basic-oil-processing','centrifuging');
UPDATE snap_recipe SET recipe_type = 'logistics'   WHERE recipe_type = 'manufacturing' AND category IN ('barrel');

INSERT INTO meta_schema (version, applied_at, note)
VALUES (6, datetime('now'), '006_recipe_type_refactor.sql');
