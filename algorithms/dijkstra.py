"""
dijkstra.py - Dijkstra's Shortest Path Algorithm & Route Comparison
Design and Analysis of Algorithms (DAA) concepts:
- Greedy Strategy: Always expands the nearest unvisited vertex.
- Optimal Substructure: Subpaths of shortest paths are also shortest paths.
- Priority Queue (Min-Heap): Achieves O((V + E) log V) time complexity.
"""

import heapq
import math
from typing import Callable, Dict, List, Optional, Tuple
from models import CampusLocation, CampusPath, RouteResult, PathType


def dijkstra_shortest_path(
    graph,
    start_id: str,
    end_id: str,
    constraint_fn: Optional[Callable[[CampusPath], bool]] = None,
    weight_fn: Optional[Callable[[CampusPath], float]] = None,
    step_by_step: bool = False,
) -> RouteResult:
    """
    Computes the shortest path from start_id to end_id using Dijkstra's Algorithm.

    Args:
        graph: CampusGraph instance
        start_id: ID of the starting location
        end_id: ID of the target location
        constraint_fn: Optional filter predicate; edges returning False are bypassed
        weight_fn: Optional custom weighting function (defaults to distance_meters)
        step_by_step: If True, records a detailed trace of greedy decisions and relaxations

    Returns:
        RouteResult containing path, total distance, walking time, directions, and trace.
    """
    if start_id not in graph.locations:
        raise KeyError(f"Start location '{start_id}' not found.")
    if end_id not in graph.locations:
        raise KeyError(f"End location '{end_id}' not found.")

    if weight_fn is None:
        weight_fn = lambda edge: edge.distance_meters

    # Distance table: node_id -> shortest known distance from start
    dist: Dict[str, float] = {node_id: math.inf for node_id in graph.locations}
    # Predecessor map: node_id -> (predecessor_id, CampusPath)
    parent: Dict[str, Optional[Tuple[str, CampusPath]]] = {node_id: None for node_id in graph.locations}
    # Visited set
    visited = set()

    # Priority queue storing tuples of (tentative_distance, node_id)
    pq: List[Tuple[float, str]] = []
    dist[start_id] = 0.0
    heapq.heappush(pq, (0.0, start_id))

    steps_log: List[str] = []
    if step_by_step:
        steps_log.append(f"Initialization: Set dist[{start_id}] = 0, all other nodes = ∞")

    step_counter = 0
    while pq:
        curr_dist, u = heapq.heappop(pq)

        # Skip stale entries in priority queue
        if u in visited:
            continue
        visited.add(u)
        step_counter += 1

        if step_by_step:
            steps_log.append(
                f"Step {step_counter}: Visited '{graph.locations[u].name}' ({u}) with tentative distance = {curr_dist:.1f}m"
            )

        # Early exit if we reached the target vertex
        if u == end_id:
            if step_by_step:
                steps_log.append(f"-> Target '{end_id}' reached. Greedy shortest distance finalized.")
            break

        # Relax all outgoing edges from u
        for edge in graph.get_neighbors(u):
            v = edge.destination

            # Apply accessibility or filter constraint if supplied
            if constraint_fn and not constraint_fn(edge):
                if step_by_step:
                    steps_log.append(f"   [Skipped edge {u} -> {v}: constraint filtered]")
                continue

            if v in visited:
                continue

            edge_weight = weight_fn(edge)
            new_dist = curr_dist + edge_weight

            # Relaxation step: if new_dist < dist[v]
            if new_dist < dist[v]:
                old_dist_str = "∞" if math.isinf(dist[v]) else f"{dist[v]:.1f}m"
                dist[v] = new_dist
                parent[v] = (u, edge)
                heapq.heappush(pq, (new_dist, v))
                if step_by_step:
                    steps_log.append(
                        f"   Relaxation ({u} -> {v}): dist[{v}] improved from {old_dist_str} to {new_dist:.1f}m via {edge.path_type.value}"
                    )

    # Reconstruct path
    if math.isinf(dist[end_id]):
        return RouteResult(
            start_id=start_id,
            end_id=end_id,
            found=False,
            algorithm_steps=steps_log,
        )

    path_nodes: List[str] = []
    path_edges: List[CampusPath] = []
    curr = end_id
    while curr is not None:
        path_nodes.append(curr)
        par_entry = parent[curr]
        if par_entry is not None:
            p_node, edge = par_entry
            path_edges.append(edge)
            curr = p_node
        else:
            break

    path_nodes.reverse()
    path_edges.reverse()

    # Calculate actual distance and walking time
    actual_distance = sum(edge.distance_meters for edge in path_edges)
    walking_time = sum(edge.walking_time_minutes for edge in path_edges)
    calories = round(actual_distance * 0.045, 1)  # ~45 kcal per 1 km
    fully_accessible = all(edge.is_accessible for edge in path_edges)
    all_covered = all(edge.is_covered for edge in path_edges)

    # Build turn-by-turn directions
    directions: List[str] = []
    directions.append(f"Depart from {graph.locations[start_id].name}.")
    for idx, edge in enumerate(path_edges, 1):
        coverage = " [Covered]" if edge.is_covered else ""
        accessibility = " [Accessible]" if edge.is_accessible else " [Stairs/Not Accessible]"
        directions.append(
            f"Step {idx}: Walk {edge.distance_meters:.0f}m along {edge.path_type.value}{coverage}{accessibility} to {graph.locations[edge.destination].name} (~{edge.walking_time_minutes} min)."
        )
    directions.append(f"Arrive at destination: {graph.locations[end_id].name}.")

    return RouteResult(
        start_id=start_id,
        end_id=end_id,
        found=True,
        path=path_nodes,
        total_distance=actual_distance,
        total_time_minutes=round(walking_time, 1),
        estimated_calories=calories,
        is_fully_accessible=fully_accessible,
        all_covered=all_covered,
        edges=path_edges,
        directions=directions,
        algorithm_steps=steps_log,
    )


def find_alternative_routes(graph, start_id: str, end_id: str) -> Dict[str, RouteResult]:
    """
    Computes and compares 4 distinct route options for students:
    1. Shortest Path (Standard Dijkstra)
    2. Wheelchair Accessible Route (Filters out stairs/inaccessible edges)
    3. All-Weather Covered Route (Biased towards covered walkways & indoor corridors)
    4. Alternative 2nd-Best Route (Bypasses the primary route's major bottleneck edge)
    """
    routes: Dict[str, RouteResult] = {}

    # 1. Shortest Route
    primary = dijkstra_shortest_path(graph, start_id, end_id)
    routes["Shortest Route"] = primary

    # 2. Fully Accessible Route
    accessible = dijkstra_shortest_path(
        graph,
        start_id,
        end_id,
        constraint_fn=lambda edge: edge.is_accessible,
    )
    routes["Accessible Route (No Stairs)"] = accessible

    # 3. Weather-Safe / Covered Route
    # Weighs uncovered paths by 1.8x penalty to strongly favor sheltered walkways
    covered = dijkstra_shortest_path(
        graph,
        start_id,
        end_id,
        weight_fn=lambda edge: edge.distance_meters * (1.0 if edge.is_covered else 1.8),
    )
    routes["Covered / Rainy Day Route"] = covered

    # 4. Alternative 2nd Best Route
    # Bypasses the most significant edge of the primary route to produce a distinct alternate path
    if primary.found and len(primary.edges) > 0:
        longest_edge = max(primary.edges, key=lambda e: e.distance_meters)
        banned_pair = tuple(sorted([longest_edge.source, longest_edge.destination]))

        alternate = dijkstra_shortest_path(
            graph,
            start_id,
            end_id,
            constraint_fn=lambda e: tuple(sorted([e.source, e.destination])) != banned_pair,
        )
        if alternate.found:
            routes["Alternative Path"] = alternate

    return routes
