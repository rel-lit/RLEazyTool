"""从 SQLite 构建 RecipeDatabase。"""

from __future__ import annotations

from core.recipe_loader import ItemDef, ItemStack, Recipe, RecipeDatabase
from db.connection import get_connection


def load_recipe_database(
    env_key: str,
    *,
    save_key: str | None = None,
    enabled_recipe_names: set[str] | None = None,
) -> RecipeDatabase:
    conn = get_connection()
    try:
        env = conn.execute(
            "SELECT snapshot_id FROM game_environment WHERE env_key = ?", (env_key,)
        ).fetchone()
        if not env:
            return RecipeDatabase(items={}, recipes={}, recipes_by_product={})
        snapshot_id = int(env["snapshot_id"])

        if save_key:
            gate_rows = conn.execute(
                """
                SELECT sr.name FROM save_recipe_gate g
                JOIN snap_recipe sr ON sr.id = g.recipe_id
                WHERE g.save_key = ?
                """,
                (save_key,),
            ).fetchall()
            enabled_recipe_names = {r["name"] for r in gate_rows}

        item_rows = conn.execute(
            """
            SELECT sr.name, sr.kind, sr.item_subgroup, sr.is_raw, sr.expansion, srt.label
            FROM snap_resource sr
            LEFT JOIN snap_resource_text srt ON srt.resource_id = sr.id
            WHERE sr.snapshot_id = ? AND sr.visibility = 'normal'
            """,
            (snapshot_id,),
        ).fetchall()
        items = {
            r["name"]: ItemDef(
                name=r["name"],
                label=r["label"] or r["name"],
                is_raw=bool(r["is_raw"]),
                expansion=r["expansion"] or "base",
                group=r["item_subgroup"],
                kind=r["kind"] or "item",
            )
            for r in item_rows
        }

        recipe_query = """
            SELECT r.id, r.name, r.category, r.energy, r.expansion, rt.label
            FROM snap_recipe r
            LEFT JOIN snap_recipe_text rt ON rt.recipe_id = r.id
            WHERE r.snapshot_id = ?
        """
        params: list = [snapshot_id]
        if enabled_recipe_names is not None:
            if not enabled_recipe_names:
                return RecipeDatabase(items=items, recipes={}, recipes_by_product={})
            placeholders = ",".join("?" * len(enabled_recipe_names))
            recipe_query += f" AND r.name IN ({placeholders})"
            params.extend(sorted(enabled_recipe_names))

        recipes: dict[str, Recipe] = {}
        by_product: dict[str, list[str]] = {}
        for rr in conn.execute(recipe_query, params).fetchall():
            rname = rr["name"]
            rid = int(rr["id"])
            flows = conn.execute(
                "SELECT direction, resource_kind, resource_name, amount FROM snap_recipe_flow WHERE recipe_id = ?",
                (rid,),
            ).fetchall()
            ingredients = [
                ItemStack(name=f["resource_name"], amount=float(f["amount"]), type=f["resource_kind"])
                for f in flows
                if f["direction"] == "in" and f["resource_kind"] in ("item", "fluid")
            ]
            products = [
                ItemStack(name=f["resource_name"], amount=float(f["amount"]), type=f["resource_kind"])
                for f in flows
                if f["direction"] == "out" and f["resource_kind"] in ("item", "fluid")
            ]
            if not products:
                continue
            recipe = Recipe(
                name=rname,
                category=rr["category"],
                energy=float(rr["energy"]),
                ingredients=ingredients,
                products=products,
                expansion=rr["expansion"] or "base",
                label=rr["label"] or rname,
            )
            recipes[rname] = recipe
            for prod in products:
                by_product.setdefault(prod.name, []).append(rname)

        return RecipeDatabase(items=items, recipes=recipes, recipes_by_product=by_product)
    finally:
        conn.close()
