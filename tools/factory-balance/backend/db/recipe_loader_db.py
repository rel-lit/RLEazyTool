"""从 SQLite 构建 RecipeDatabase。"""



from __future__ import annotations



from core.icon_assets import icon_slug_from_path
from core.recipe_loader import ItemDef, ItemStack, Recipe, RecipeDatabase, _finalize_database
from db.extraction_etl import EXTRACT_RECIPE_PREFIX
from db.connection import get_connection

from db.intrinsic.constants import CLOSURE_PRIMARY





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

            return RecipeDatabase(items={}, recipes={})

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

            SELECT sr.name, sr.kind, sr.item_subgroup, sr.is_raw, sr.expansion, sr.icon, srt.label

            FROM snap_resource sr

            LEFT JOIN snap_resource_text srt ON srt.resource_id = sr.id

            WHERE sr.snapshot_id = ? AND sr.visibility = 'normal'

            """,

            (snapshot_id,),

        ).fetchall()

        def _slug(icon_path: str | None) -> str | None:
            if not icon_path:
                return None
            try:
                return icon_slug_from_path(icon_path)
            except (ValueError, IndexError):
                return None

        items = {

            r["name"]: ItemDef(

                name=r["name"],

                label=r["label"] or r["name"],

                is_raw=bool(r["is_raw"]),

                expansion=r["expansion"] or "base",

                group=r["item_subgroup"],

                kind=r["kind"] or "item",

                icon_slug=_slug(r["icon"]),

            )

            for r in item_rows

        }



        resource_tags: dict[str, set[str]] = {}

        for row in conn.execute(

            """

            SELECT sr.name, rit.tag_code

            FROM snap_resource_intrinsic_tag rit

            JOIN snap_resource sr ON sr.id = rit.resource_id

            WHERE rit.snapshot_id = ?

            """,

            (snapshot_id,),

        ).fetchall():

            resource_tags.setdefault(row["name"], set()).add(row["tag_code"])



        recipe_query = """

            SELECT r.id, r.name, r.category, r.energy, r.expansion, rt.label

            FROM snap_recipe r

            LEFT JOIN snap_recipe_text rt ON rt.recipe_id = r.id

            WHERE r.snapshot_id = ?

        """

        params: list = [snapshot_id]

        if enabled_recipe_names is not None:

            if not enabled_recipe_names:

                return RecipeDatabase(items=items, resource_intrinsic_tags=resource_tags)

            placeholders = ",".join("?" * len(enabled_recipe_names))

            recipe_query += f" AND (r.name IN ({placeholders}) OR r.name LIKE ?)"

            params.extend(sorted(enabled_recipe_names))

            params.append(f"{EXTRACT_RECIPE_PREFIX}%")



        closure_roles: dict[int, str] = {

            int(r["recipe_id"]): r["closure_role"]

            for r in conn.execute(

                "SELECT recipe_id, closure_role FROM snap_recipe_closure_role WHERE snapshot_id = ?",

                (snapshot_id,),

            ).fetchall()

        }



        recipes: dict[str, Recipe] = {}

        recipe_roles: dict[str, str] = {}

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

            recipe_roles[rname] = closure_roles.get(rid, CLOSURE_PRIMARY)



        db = _finalize_database(items, recipes, {}, recipe_roles)

        db.resource_intrinsic_tags = resource_tags

        return db

    finally:

        conn.close()

