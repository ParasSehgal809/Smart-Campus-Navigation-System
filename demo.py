"""
demo.py - Automated Demonstration Script for Smart Campus Navigation
Runs non-interactively to demonstrate all DAA concepts and outputs formatted results.
"""

import sys
import os
from campus_graph import build_default_campus
from algorithms import dijkstra_shortest_path, find_alternative_routes, prim_mst, kruskal_mst, compare_mst_algorithms
from visualizer import generate_interactive_html


def run_demo():
    print("=" * 80)
    print("🚀 SMART CAMPUS NAVIGATION SYSTEM - AUTOMATED DEMONSTRATION")
    print("=" * 80)

    # 1. Initialize Campus Graph
    print("\n[STEP 1] Initializing Campus Graph...")
    graph = build_default_campus()
    print(f"✔ Successfully loaded campus graph: '{graph.name}'")
    print(f"  Total Vertices (|V|) : {graph.vertex_count} (Buildings, Classrooms, Labs, Library)")
    print(f"  Total Edges (|E|)    : {graph.edge_count} (Bidirectional Walking Paths)")

    # 2. Graph Representations
    print("\n[STEP 2] DAA Graph Representations:")
    print("  a) Adjacency List Sample (GATE and CS_BLOCK):")
    for nid in ["GATE", "CS_BLOCK", "LIB"]:
        nbrs = [f"{p.destination} ({p.distance_meters:.0f}m, {p.path_type.value})" for p in graph.get_neighbors(nid)]
        print(f"     {nid:10} -> {' | '.join(nbrs)}")

    print("\n  b) Adjacency Matrix (Top 5 Vertices):")
    matrix_str = graph.format_adjacency_matrix(max_display_nodes=5)
    for line in matrix_str.split("\n"):
        print(f"     {line}")

    # 3. Dijkstra's Algorithm Demo
    print("\n[STEP 3] Dijkstra's Shortest Path Algorithm:")
    start_loc = "GATE"
    end_loc = "TURING_LAB"
    print(f"  Calculating shortest route: '{start_loc}' ➔ '{end_loc}'...")

    res = dijkstra_shortest_path(graph, start_loc, end_loc, step_by_step=True)
    print(f"  ✔ Shortest Distance  : {res.total_distance:.1f} meters")
    print(f"  ✔ Estimated Walk Time: {res.total_time_minutes:.1f} minutes")
    print(f"  ✔ Optimal Path Nodes : {' ➔ '.join(res.path)}")
    print("  ✔ Turn-by-Turn Directions:")
    for d in res.directions:
        print(f"     • {d}")

    print("\n  Dijkstra Algorithm Trace (First 5 steps):")
    for step in res.algorithm_steps[:5]:
        print(f"     {step}")

    # 4. Route Comparison Feature
    print("\n[STEP 4] Multi-Criteria Route Comparison:")
    print(f"  Comparing paths from '{start_loc}' ➔ '{end_loc}':")
    routes = find_alternative_routes(graph, start_loc, end_loc)
    print(f"  {'Route Name':<30} {'Distance':<12} {'Walk Time':<12} {'Accessible':<12}")
    print("  " + "-" * 66)
    for r_name, r_obj in routes.items():
        if r_obj.found:
            acc = "Yes ✅" if r_obj.is_fully_accessible else "No ❌ (Stairs)"
            print(f"  {r_name:<30} {r_obj.total_distance:6.0f} m     {r_obj.total_time_minutes:4.1f} min     {acc:<12}")
            print(f"     Path: {' ➔ '.join(r_obj.path)}")

    # 5. Minimum Spanning Tree (MST) Demo
    print("\n[STEP 5] Minimum Spanning Tree (Campus Fiber-Optic Backbone):")
    mst_dict = compare_mst_algorithms(graph)
    k_res = mst_dict["Kruskal"]
    p_res = mst_dict["Prim"]

    print(f"  ✔ Kruskal's MST Total Length: {k_res.total_weight_meters:.1f} meters (|E_mst| = {len(k_res.edges)})")
    print(f"  ✔ Prim's MST Total Length   : {p_res.total_weight_meters:.1f} meters (|E_mst| = {len(p_res.edges)})")
    assert k_res.total_weight_meters == p_res.total_weight_meters, "MST weights do not match!"
    print("  ✔ Optimality Verified: Both algorithms compute the exact same optimal weight!")

    total_paths_length = sum(e.distance_meters for e in graph.all_edges)
    savings = total_paths_length - k_res.total_weight_meters
    print(f"  ✔ Cable Savings: Reduced from {total_paths_length:.0f}m to {k_res.total_weight_meters:.0f}m ({savings:.0f}m / {savings/total_paths_length*100:.1f}% savings)")

    # 6. Generate Interactive Visual Map
    print("\n[STEP 6] Generating Interactive HTML/SVG Campus Map...")
    html_file = os.path.join(os.path.dirname(__file__), "campus_map.html")
    generate_interactive_html(graph, active_route=res, active_mst=k_res, output_path=html_file)
    print(f"  ✔ Successfully exported interactive visual map to: {html_file}")

    print("\n" + "=" * 80)
    print("🎉 ALL DEMONSTRATION MODULES COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
