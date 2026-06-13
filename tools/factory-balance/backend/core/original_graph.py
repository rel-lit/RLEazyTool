"""原始图 G：物品节点 + 依赖边（v2）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GraphNode:
    """一个物品在原始图中的唯一节点。"""

    item: str
    layer: int = 0
    rank: int = 0
    rank_frac: float = 0.0
    parents: set[str] = field(default_factory=set)
    children: set[str] = field(default_factory=set)
    is_terminal: bool = False
    is_external_leaf: bool = False
    is_pseudo_external: bool = False
    recipe_name: str | None = None


@dataclass
class OriginalGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    terminals: list[str] = field(default_factory=list)

    def ensure(self, item: str) -> GraphNode:
        if item not in self.nodes:
            self.nodes[item] = GraphNode(item=item)
        return self.nodes[item]

    def add_dependency(self, ingredient: str, product: str) -> None:
        """原料 ingredient → 产品 product（低 layer → 高 layer）。"""
        ing = self.ensure(ingredient)
        prod = self.ensure(product)
        ing.parents.add(product)
        prod.children.add(ingredient)

    def edges(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for item, node in self.nodes.items():
            for parent in node.parents:
                out.append((item, parent))
        return out

    def copy_structure(self) -> OriginalGraph:
        g = OriginalGraph(terminals=list(self.terminals))
        for item, node in self.nodes.items():
            g.nodes[item] = GraphNode(
                item=item,
                is_terminal=node.is_terminal,
                is_external_leaf=node.is_external_leaf,
                is_pseudo_external=node.is_pseudo_external,
                recipe_name=node.recipe_name,
                parents=set(node.parents),
                children=set(node.children),
            )
        return g

    def merge_from(self, other: OriginalGraph) -> None:
        for t in other.terminals:
            if t not in self.terminals:
                self.terminals.append(t)
        for item, on in other.nodes.items():
            tn = self.ensure(item)
            tn.parents |= on.parents
            tn.children |= on.children
            tn.is_terminal = tn.is_terminal or on.is_terminal
            tn.is_external_leaf = tn.is_external_leaf or on.is_external_leaf
            tn.is_pseudo_external = tn.is_pseudo_external or on.is_pseudo_external
            if on.recipe_name and not tn.recipe_name:
                tn.recipe_name = on.recipe_name
        for item, on in other.nodes.items():
            tn = self.nodes[item]
            tn.parents = {self.ensure(p).item for p in tn.parents}
            tn.children = {self.ensure(c).item for c in tn.children}
