"""从 Factorio --dump-data / --dump-prototype-locale 构建配方库。"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .factorio_paths import FactorioPaths, load_paths
from .locale_loader import ensure_locale_cache, locale_has_names, load_locale_from_install, merge_locale_tables
from .recipe_loader import ItemDef, ItemStack, Recipe, RecipeDatabase

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
DUMP_FILE = CACHE_DIR / "data-raw-dump.json"
LOCALE_FILE = CACHE_DIR / "prototype-locale.json"
DUMP_TIMEOUT_SEC = 300

# Factorio 2.0 中许多“物品”不在 item 表，而在 tool/armor 等表
EXTRA_ITEM_TABLES = (
    "tool",
    "armor",
    "module",
    "ammo",
    "capsule",
    "gun",
    "repair-tool",
    "item-with-entity-data",
    "rail-planner",
)


def _is_layout_recipe(name: str, proto: dict[str, Any]) -> bool:
    if proto.get("hidden"):
        return False
    if name.startswith("parameter-"):
        return False
    products = _stack_list(proto.get("results") or proto.get("products"))
    return any(p.type == "item" for p in products)


def _stack_list(raw: list[dict[str, Any]] | None) -> list[ItemStack]:
    stacks: list[ItemStack] = []
    for entry in raw or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            continue
        stacks.append(
            ItemStack(
                name=str(name),
                amount=float(entry.get("amount", 1)),
                type=str(entry.get("type", "item")),
            )
        )
    return stacks


def _lookup_locale_entry(locale: dict[str, Any], kind: str, name: str) -> str | None:
    try:
        loc = locale.get(kind, {}).get(name, {})
        if isinstance(loc, dict):
            localised = loc.get("localised_name")
            if isinstance(localised, list) and localised:
                return str(localised[-1])
            if isinstance(localised, str):
                return localised
    except (AttributeError, TypeError):
        pass
    return None


def _locale_label(locale: dict[str, Any], kind: str, name: str, fallback: str) -> str:
    kinds = (kind, "item", "tool", "armor", "module", "ammo", "capsule", "entity", "equipment", "fluid", "recipe")
    seen: set[str] = set()
    for k in kinds:
        if k in seen:
            continue
        seen.add(k)
        label = _lookup_locale_entry(locale, k, name)
        if label:
            return label

    if name.endswith("-barrel"):
        fluid = name[: -len("-barrel")]
        fluid_label = _lookup_locale_entry(locale, "fluid", fluid)
        if fluid_label:
            return f"{fluid_label}桶"

    return fallback


def load_locale(path: Path | None = None, paths: FactorioPaths | None = None) -> dict[str, Any]:
    if path and path.is_file():
        return _read_locale_file(path)
    merged: dict[str, Any] = {}
    for candidate in (LOCALE_FILE, CACHE_DIR / "item-locale.json", CACHE_DIR / "recipe-locale.json"):
        if candidate.is_file():
            chunk = _read_locale_file(candidate)
            merged = merge_locale_tables(merged, chunk)
    if not locale_has_names(merged):
        install = load_locale_from_install(paths)
        merged = merge_locale_tables(merged, install)
    return merged


def _read_locale_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def build_database_from_dump(
    dump_path: Path | None = None,
    locale_path: Path | None = None,
    *,
    enabled_recipes: set[str] | None = None,
) -> RecipeDatabase:
    dump_path = dump_path or DUMP_FILE
    if not dump_path.is_file():
        raise FileNotFoundError(f"未找到配方 dump: {dump_path}")

    raw = json.loads(dump_path.read_text(encoding="utf-8"))
    locale = load_locale(locale_path, load_paths())

    items: dict[str, ItemDef] = {}
    for name, proto in (raw.get("item") or {}).items():
        if not isinstance(proto, dict):
            continue
        if name.startswith("parameter-"):
            continue
        label = _locale_label(locale, "item", name, name)
        subgroup = proto.get("subgroup")
        items[name] = ItemDef(
            name=name,
            label=label,
            is_raw=_guess_is_raw(name, proto),
            expansion=_guess_expansion(name, raw),
            group=str(subgroup) if subgroup else None,
        )

    _ingest_extra_prototypes(raw, locale, items)

    for fluid_name, proto in (raw.get("fluid") or {}).items():
        if not isinstance(proto, dict):
            continue
        label = _locale_label(locale, "fluid", fluid_name, fluid_name)
        items[fluid_name] = ItemDef(
            name=fluid_name,
            label=label,
            is_raw=False,
            expansion=_guess_expansion(fluid_name, raw),
            group="fluid",
        )

    recipes: dict[str, Recipe] = {}
    by_product: dict[str, list[str]] = {}

    for name, proto in (raw.get("recipe") or {}).items():
        if not isinstance(proto, dict):
            continue
        if not _is_layout_recipe(name, proto):
            continue
        category = str(proto.get("category") or "crafting")
        if enabled_recipes is not None and name not in enabled_recipes:
            continue

        products = _stack_list(proto.get("results") or proto.get("products"))
        if not products:
            continue
        item_products = [p for p in products if p.type == "item"]
        if not item_products:
            continue

        main_product = proto.get("main_product") or item_products[0].name
        label = _locale_label(locale, "recipe", name, str(main_product))
        recipe = Recipe(
            name=name,
            category=category,
            energy=float(proto.get("energy") or proto.get("energy_required") or 0.5),
            ingredients=_stack_list(proto.get("ingredients")),
            products=item_products,
            expansion=_guess_expansion(name, raw),
            label=label,
        )
        recipes[name] = recipe
        for prod in item_products:
            by_product.setdefault(prod.name, []).append(name)

    _fill_recipe_referenced_items(raw, locale, items, recipes)

    return RecipeDatabase(items=items, recipes=recipes, recipes_by_product=by_product)


def _guess_is_raw(name: str, proto: dict[str, Any]) -> bool:
    if name.endswith("-ore") or name.endswith("-brine"):
        return True
    if proto.get("subgroup") == "raw-resource":
        return True
    return name in {"stone", "coal", "wood", "raw-fish", "crude-oil"}


def _find_prototype(raw: dict[str, Any], name: str) -> dict[str, Any] | None:
    for table in ("item", *EXTRA_ITEM_TABLES):
        proto = (raw.get(table) or {}).get(name)
        if isinstance(proto, dict):
            return proto
    return None


def _make_item_def(name: str, proto: dict[str, Any] | None, locale: dict[str, Any], raw: dict[str, Any]) -> ItemDef:
    proto = proto or {}
    label = _locale_label(locale, "item", name, name)
    subgroup = proto.get("subgroup")
    return ItemDef(
        name=name,
        label=label,
        is_raw=_guess_is_raw(name, proto),
        expansion=_guess_expansion(name, raw),
        group=str(subgroup) if subgroup else None,
    )


def _ingest_extra_prototypes(
    raw: dict[str, Any],
    locale: dict[str, Any],
    items: dict[str, ItemDef],
) -> None:
    for table in EXTRA_ITEM_TABLES:
        for name, proto in (raw.get(table) or {}).items():
            if not isinstance(proto, dict) or name.startswith("parameter-") or name in items:
                continue
            items[name] = _make_item_def(name, proto, locale, raw)


def _fill_recipe_referenced_items(
    raw: dict[str, Any],
    locale: dict[str, Any],
    items: dict[str, ItemDef],
    recipes: dict[str, Recipe],
) -> None:
    needed: set[str] = set()
    for recipe in recipes.values():
        for stack in (*recipe.products, *recipe.ingredients):
            if stack.type == "item":
                needed.add(stack.name)
    for name in needed:
        if name in items or name.startswith("parameter-"):
            continue
        items[name] = _make_item_def(name, _find_prototype(raw, name), locale, raw)


def _guess_expansion(name: str, raw: dict[str, Any]) -> str:
    proto = _find_prototype(raw, name) or (raw.get("recipe") or {}).get(name) or {}
    mod = str(proto.get("mod") or "")
    if "space-age" in mod or name in {
        "quantum-processor",
        "superconductor",
        "supercapacitor",
        "holmium-plate",
        "lithium-plate",
        "tungsten-carbide",
    }:
        return "space-age"
    return "base"


def run_prototype_dump(paths: FactorioPaths | None = None) -> tuple[Path, Path, list[str]]:
    paths = paths or load_paths()
    warnings: list[str] = []
    if paths.executable is None:
        raise FileNotFoundError("未找到 Factorio 可执行文件，请设置 FACTORIO_EXE")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    paths.script_output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [str(paths.executable), "--dump-data", "--dump-prototype-locale", "--disable-audio"]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=DUMP_TIMEOUT_SEC,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Factorio dump 失败 (code {proc.returncode}): {(proc.stderr or proc.stdout)[-400:]}")

    src_dump = paths.script_output_dir / "data-raw-dump.json"
    if not src_dump.is_file():
        raise FileNotFoundError("dump 未生成 data-raw-dump.json，请确认 script-output 目录可写")

    shutil_copy = __import__("shutil").copy2
    shutil_copy(src_dump, DUMP_FILE)
    for src in paths.script_output_dir.glob("*locale*.json"):
        dest = CACHE_DIR / src.name
        shutil_copy(src, dest)
        if "prototype-locale" in src.name or "item-locale" in src.name:
            shutil_copy(src, LOCALE_FILE)

    _, locale_warnings = ensure_locale_cache(paths)
    warnings.extend(locale_warnings)
    if not locale_has_names(load_locale(paths=paths)):
        warnings.append("未加载到物品中文名，界面将显示内部 ID（不影响布局计算）")

    return DUMP_FILE, LOCALE_FILE, warnings


def filter_craftable_products(db: RecipeDatabase, craftable_items: set[str]) -> list[ItemDef]:
    from .item_catalog import build_item_catalog

    return build_item_catalog(db, craftable_items).manufacture_items
