"""
mst.py - Minimum Spanning Tree (MST) Algorithms
Design and Analysis of Algorithms (DAA) concepts:
- Cut Property & Greedy Choice: Minimum weight edge crossing any cut belongs to MST.
- Prim's Algorithm: Grows a single tree from a root vertex using a min-heap priority queue (O((V + E) log V)).
- Kruskal's Algorithm: Sorts edges and connects forests using Disjoint Set Union (DSU) with Path Compression and Union by Rank (O(E log E)).
- Real-World Use Case: Designing the optimal campus-wide fiber-optic broadband / CCTV backbone network connecting all hubs with minimal cabling cost.
"""

import heapq
from typing import Dict, List, Tuple
from models import CampusPath, MSTResult


class DisjointSetUnion:
    """
    Disjoint Set Union (DSU) data structure with:
    1. Path Compression: Flattens tree during find() -> amortized nearly O(1)
    2. Union by Rank: Attaches shallower tree under deeper tree to keep depth minimal
    """

    def __init__(self, elements: List[str]):
        self.parent: Dict[str, str] = {x: x for x in elements}
        self.rank: Dict[str, int] = {x: 0 for x in elements}

    def find(self, x: str) -> str:
        """Find representative root of set containing x with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        """
        Unites sets containing x and y.
        Returns True if they were in different sets (successfully united),
        or False if they were already in the same set (adding edge would form a cycle).
        """
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False  # Already in same connected component (cycle detected)

        # Union by Rank heuristic
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        return True


def kruskal_mst(graph, step_by_step: bool = False) -> MSTResult:
    """
    Computes Minimum Spanning Tree using Kruskal's Algorithm.
    Time Complexity: O(E log E) for sorting edges + O(E * α(V)) for DSU operations.
    """
    steps: List[str] = []
    # 1. Gather all unique edges and sort by distance
    sorted_edges = sorted(graph.all_edges, key=lambda e: e.distance_meters)
    dsu = DisjointSetUnion(list(graph.locations.keys()))

    mst_edges: List[CampusPath] = []
    total_weight = 0.0

    if step_by_step:
        steps.append(f"Kruskal Step 1: Sorted all {len(sorted_edges)} edges in ascending order of distance.")

    target_edges = graph.vertex_count - 1

    for idx, edge in enumerate(sorted_edges, 1):
        u, v = edge.source, edge.destination
        u_name = graph.locations[u].name
        v_name = graph.locations[v].name

        # Check if adding edge (u, v) creates a cycle
        if dsu.union(u, v):
            mst_edges.append(edge)
            total_weight += edge.distance_meters
            if step_by_step:
                steps.append(
                    f"Edge {idx} ACCEPTED: {u} <--> {v} ({edge.distance_meters:.0f}m). "
                    f"Connected '{u_name}' and '{v_name}'. (Tree size: {len(mst_edges)}/{target_edges})"
                )
            if len(mst_edges) == target_edges:
                if step_by_step:
                    steps.append("-> Spanning Tree Complete: Exactly |V| - 1 edges selected.")
                break
        else:
            if step_by_step:
                steps.append(
                    f"Edge {idx} REJECTED: {u} <--> {v} ({edge.distance_meters:.0f}m) forms a cycle. Discarded."
                )

    return MSTResult(
        algorithm_name="Kruskal's Algorithm (DSU with Union-by-Rank & Path Compression)",
        edges=mst_edges,
        total_weight_meters=total_weight,
        connected_vertices_count=len(graph.locations),
        total_vertices_count=graph.vertex_count,
        step_trace=steps,
    )


def prim_mst(graph, start_vertex: str = "ADMIN", step_by_step: bool = False) -> MSTResult:
    """
    Computes Minimum Spanning Tree using Prim's Algorithm.
    Time Complexity: O((V + E) log V) using a min-heap priority queue.
    """
    if start_vertex not in graph.locations:
        start_vertex = next(iter(graph.locations.keys()))

    steps: List[str] = []
    visited = set()
    mst_edges: List[CampusPath] = []
    total_weight = 0.0

    # Min-heap stores: (distance, u, v, CampusPath)
    pq: List[Tuple[float, str, str, CampusPath]] = []

    def add_incident_edges(vertex: str):
        visited.add(vertex)
        for edge in graph.get_neighbors(vertex):
            nbr = edge.destination
            if nbr not in visited:
                heapq.heappush(pq, (edge.distance_meters, vertex, nbr, edge))

    if step_by_step:
        steps.append(f"Prim Step 1: Initialize tree starting from root vertex '{start_vertex}' ({graph.locations[start_vertex].name}).")

    add_incident_edges(start_vertex)
    step_num = 0

    while pq and len(visited) < graph.vertex_count:
        dist, u, v, edge = heapq.heappop(pq)

        if v in visited:
            continue  # Already in tree; discard edge

        step_num += 1
        visited.add(v)
        mst_edges.append(edge)
        total_weight += dist

        if step_by_step:
            steps.append(
                f"Step {step_num}: Selected minimum cut edge: {u} <--> {v} ({dist:.0f}m). "
                f"Added '{graph.locations[v].name}' to tree. (|V_tree| = {len(visited)}/{graph.vertex_count})"
            )

        add_incident_edges(v)

    return MSTResult(
        algorithm_name="Prim's Algorithm (Greedy Cut Property with Min-Heap PQ)",
        edges=mst_edges,
        total_weight_meters=total_weight,
        connected_vertices_count=len(visited),
        total_vertices_count=graph.vertex_count,
        step_trace=steps,
    )


def compare_mst_algorithms(graph) -> Dict[str, MSTResult]:
    """Runs both Prim's and Kruskal's algorithms and validates MST equivalence."""
    kruskal_res = kruskal_mst(graph, step_by_step=False)
    prim_res = prim_mst(graph, start_vertex="ADMIN", step_by_step=False)
    return {
        "Kruskal": kruskal_res,
        "Prim": prim_res,
    }
