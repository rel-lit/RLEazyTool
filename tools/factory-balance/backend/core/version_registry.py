"""版本化配方包注册表：按 GameVersionKey 管理全配方 + 本地化。"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from models.game_data import GameVersionKey, ItemRecord, RecipePack, RecipeRecord, SaveProgressRecord

from .recipe_loader import ItemDef, Recipe, RecipeDatabase
from .save_index import _read_save_version

PACKS_ROOT = Path(__file__).resolve().parent.parent / "data" / "cache" / "packs"
REGISTRY_FILE = PACKS_ROOT / "registry.json"
LEGACY_DUMP = Path(__file__).resolve().parent.parent / "data" / "cache" / "data-raw-dump.json"
LEGACY_LOCALE = Path(__file__).resolve().parent.parent / "data" / "cache" / "prototype-locale.json"


def _read_registry() -> dict:
    if not REGISTRY_FILE.is_file():
        return {"packs": []}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"packs": []}
    return data if isinstance(data, dict) else {"packs": []}


def _write_registry(data: dict) -> None:
    PACKS_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def pack_dir(version_key: GameVersionKey) -> Path:
    return PACKS_ROOT / version_key.pack_slug()


def list_registered_packs() -> list[GameVersionKey]:
    reg = _read_registry()
    keys: list[GameVersionKey] = []
    for entry in reg.get("packs") or []:
        if isinstance(entry, dict) and isinstance(entry.get("version_key"), dict):
            keys.append(GameVersionKey.from_dict(entry["version_key"]))
    return keys


def has_pack(version_key: GameVersionKey) -> bool:
    manifest = pack_dir(version_key) / "manifest.json"
    dump = pack_dir(version_key) / "data-raw-dump.json"
    return manifest.is_file() and dump.is_file()


def resolve_pack(version_key: GameVersionKey) -> RecipePack | None:
    if not has_pack(version_key):
        return None
    pdir = pack_dir(version_key)
    try:
        manifest = json.loads((pdir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    dump_path = pdir / "data-raw-dump.json"
    locale_path = pdir / "prototype-locale.json"
    return RecipePack(
        version_key=version_key,
        dump_path=dump_path if dump_path.is_file() else None,
        locale_path=locale_path if locale_path.is_file() else None,
        created_at=manifest.get("created_at"),
    )


def version_key_for_save(save_path: Path, mod_names: list[str], *, locale: str = "zh-CN") -> GameVersionKey:
    game_version, _ = _read_save_version(save_path)
    return GameVersionKey.create(game_version, mod_names, locale=locale)


def pack_status(version_key: GameVersionKey) -> dict:
    pdir = pack_dir(version_key)
    manifest: dict = {}
    manifest_path = pdir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
    return {
        "version_key": version_key.to_dict(),
        "registered": has_pack(version_key),
        "pack_dir": str(pdir),
        "item_count": manifest.get("item_count"),
        "recipe_count": manifest.get("recipe_count"),
        "created_at": manifest.get("created_at"),
    }


def register_pack_from_files(
    version_key: GameVersionKey,
    dump_src: Path,
    locale_src: Path | None = None,
    *,
    item_count: int = 0,
    recipe_count: int = 0,
) -> RecipePack:
    """将 dump/locale 写入版本目录并更新 registry。"""
    pdir = pack_dir(version_key)
    pdir.mkdir(parents=True, exist_ok=True)

    dump_dest = pdir / "data-raw-dump.json"
    shutil.copy2(dump_src, dump_dest)

    locale_dest = pdir / "prototype-locale.json"
    if locale_src and locale_src.is_file():
        shutil.copy2(locale_src, locale_dest)

    created_at = datetime.now(timezone.utc).isoformat()
    pack = RecipePack(
        version_key=version_key,
        dump_path=dump_dest,
        locale_path=locale_dest if locale_dest.is_file() else None,
        created_at=created_at,
    )
    manifest = pack.manifest_dict()
    manifest["item_count"] = item_count
    manifest["recipe_count"] = recipe_count
    (pdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    reg = _read_registry()
    packs: list = [e for e in reg.get("packs") or [] if not isinstance(e, dict) or e.get("version_key", {}).get("pack_slug") != version_key.pack_slug()]
    packs.append({"version_key": version_key.to_dict(), "created_at": created_at})
    reg["packs"] = packs
    _write_registry(reg)

    # 兼容旧代码：同步一份到 cache 根目录
    shutil.copy2(dump_dest, LEGACY_DUMP)
    if locale_dest.is_file():
        shutil.copy2(locale_dest, LEGACY_LOCALE)

    return pack


def ensure_pack(version_key: GameVersionKey) -> tuple[RecipePack | None, bool]:
    """若已有 pack 则返回 (pack, False)；否则 (None, True) 表示需要 dump。"""
    existing = resolve_pack(version_key)
    if existing:
        return existing, False
    return None, True


def database_to_records(db: RecipeDatabase) -> tuple[dict[str, ItemRecord], dict[str, RecipeRecord]]:
    items = {
        name: ItemRecord(
            name=item.name,
            label=item.label,
            is_raw=item.is_raw,
            expansion=item.expansion,
            group=item.group,
        )
        for name, item in db.items.items()
    }
    recipes = {
        name: RecipeRecord(
            name=recipe.name,
            label=recipe.label,
            category=recipe.category,
            energy=recipe.energy,
            ingredients=[{"name": s.name, "amount": s.amount, "type": s.type} for s in recipe.ingredients],
            products=[{"name": s.name, "amount": s.amount, "type": s.type} for s in recipe.products],
            expansion=recipe.expansion,
        )
        for name, recipe in db.recipes.items()
    }
    return items, recipes


def records_to_database(items: dict[str, ItemRecord], recipes: dict[str, RecipeRecord]) -> RecipeDatabase:
    item_defs = {
        n: ItemDef(
            name=r.name,
            label=r.label,
            is_raw=r.is_raw,
            expansion=r.expansion,
            group=r.group,
        )
        for n, r in items.items()
    }
    recipe_defs: dict[str, Recipe] = {}
    by_product: dict[str, list[str]] = {}
    from .recipe_loader import ItemStack

    for name, r in recipes.items():
        recipe = Recipe(
            name=r.name,
            label=r.label,
            category=r.category,
            energy=r.energy,
            ingredients=[ItemStack(**x) for x in r.ingredients],
            products=[ItemStack(**x) for x in r.products],
            expansion=r.expansion,
        )
        recipe_defs[name] = recipe
        for prod in recipe.products:
            if prod.type == "item":
                by_product.setdefault(prod.name, []).append(name)
    return RecipeDatabase(items=item_defs, recipes=recipe_defs, recipes_by_product=by_product)


def progress_needs_reimport(save_record: SaveProgressRecord, save_path: Path) -> bool:
    if save_record.save_mtime is None:
        return False
    try:
        return save_path.stat().st_mtime > save_record.save_mtime + 1
    except OSError:
        return False
