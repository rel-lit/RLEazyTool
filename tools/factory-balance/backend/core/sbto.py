"""阶段 5：SBTO 链组（v2：仅 layer/rank，生产者侧发现）。"""

from __future__ import annotations

from dataclasses import dataclass

from core.original_graph import OriginalGraph


@dataclass
class SbtoChain:
    item: str
    root: str
    tap_order: list[str]


@dataclass
class TapOrderResult:
    item: str
    order: list[str]
    rule: str
    explanation: str


def _sort_key(graph: OriginalGraph, item: str) -> tuple[int, int, str]:
    node = graph.nodes[item]
    return (-node.layer, -node.rank, item)


def discover_sbto_chains(graph: OriginalGraph) -> list[SbtoChain]:
    chains: list[SbtoChain] = []
    items = sorted(
        graph.nodes.keys(),
        key=lambda i: (
            graph.nodes[i].layer,
            graph.nodes[i].rank,
            i,
        ),
    )
    registered: set[str] = set()

    for item in items:
        if item in registered:
            continue
        node = graph.nodes[item]
        consumers = sorted(node.parents, key=lambda c: _sort_key(graph, c))
        if len(consumers) < 2:
            continue
        registered.add(item)
        chains.append(
            SbtoChain(
                item=item,
                root=item,
                tap_order=sorted(consumers, key=lambda c: _sort_key(graph, c)),
            )
        )

    return chains


def chains_to_tap_results(
    chains: list[SbtoChain],
    graph: OriginalGraph,
    labels: dict[str, str],
) -> list[TapOrderResult]:
    results: list[TapOrderResult] = []
    for chain in chains:
        names = [labels.get(c, c) for c in chain.tap_order]
        item_label = labels.get(chain.item, chain.item)
        results.append(
            TapOrderResult(
                item=chain.item,
                order=list(chain.tap_order),
                rule="layer_rank",
                explanation=(
                    f"共享物「{item_label}」上，{' → '.join(names)}。"
                    f"下游优先：层级高优先、同层 rank 大优先。"
                ),
            )
        )
    return results
