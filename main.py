"""
main.py - Interactive Command-Line Interface (CLI) for Smart Campus Navigation
Demonstrates:
- Graph Representation (Adjacency List & Adjacency Matrix)
- Dijkstra's Shortest Path Algorithm
- Route Comparison (Shortest vs Wheelchair-Accessible vs All-Weather)
- Minimum Spanning Tree (Prim's and Kruskal's Algorithms)
- Step-by-step Viva / Educational Execution Trace
- Interactive HTML Map Export
"""

import os
import sys
from campus_graph import build_default_campus
from algorithms import dijkstra_shortest_path, find_alternative_routes, prim_mst, kruskal_mst, compare_mst_algorithms
from visualizer import render_terminal_overview, generate_interactive_html


def clear_screen():
    # Keep output clean
    pass


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def choose_location(graph, prompt: str, default: str = "") -> str:
    """Helper to let user pick a campus location by number or ID."""
    locs = sorted(graph.locations.keys())
    print(f"\n{prompt}")
    for idx, loc_id in enumerate(locs, 1):
        loc = graph.locations[loc_id]
        print(f"  [{idx:2d}] {loc_id:12} - {loc.name} ({loc.category.value})")

    while True:
        choice = input(f"\nEnter choice [1-{len(locs)}] or ID" + (f" (Default: {default})" if default else "") + ": ").strip()
        if not choice and default:
            return default
        if choice.upper() in graph.locations:
            return choice.upper()
        if choice.isdigit():
            val = int(choice)
            if 1 <= val <= len(locs):
                return locs[val - 1]
        print("Invalid selection. Please enter a valid number or location ID.")


def handle_shortest_path(graph):
    print_header("FIND SHORTEST CAMPUS PATH (DIJKSTRA'S ALGORITHM)")
    start_id = choose_location(graph, "Select START location:", default="GATE")
    end_id = choose_location(graph, "Select DESTINATION location:", default="TURING_LAB")

    print("\nSelect routing preference:")
    print("  [1] Standard Shortest Path (Fastest)")
    print("  [2] Wheelchair / Mobility Accessible (Ramps only, bypass stairs)")
    print("  [3] All-Weather Covered Route (Sheltered from rain/sun)")
    pref = input("Enter option [1-3] (Default: 1): ").strip()

    constraint_fn = None
    weight_fn = None
    route_type_name = "Shortest Route"

    if pref == "2":
        constraint_fn = lambda edge: edge.is_accessible
        route_type_name = "Accessible Route"
    elif pref == "3":
        weight_fn = lambda edge: edge.distance_meters * (1.0 if edge.is_covered else 2.0)
        route_type_name = "Covered / Weather-Protected Route"

    result = dijkstra_shortest_path(
        graph,
        start_id=start_id,
        end_id=end_id,
        constraint_fn=constraint_fn,
        weight_fn=weight_fn,
        step_by_step=False,
    )

    if not result.found:
        print(f"\n❌ No path found between {start_id} and {end_id} with the selected constraints!")
        return

    print("\n" + "-" * 70)
    print(f"ROUTE FOUND: {graph.locations[start_id].name} ➔ {graph.locations[end_id].name}")
    print("-" * 70)
    print(f"• Route Category     : {route_type_name}")
    print(f"• Total Distance     : {result.total_distance:.1f} meters")
    print(f"• Estimated Walk Time: {result.total_time_minutes:.1f} minutes (@ 80m/min)")
    print(f"• Calories Burned    : ~{result.estimated_calories:.1f} kcal")
    print(f"• Wheelchair Friendly: {'Yes ✅' if result.is_fully_accessible else 'No ⚠️ (Includes stairs)'}")
    print(f"• Weather Sheltered  : {'Fully Covered ☔' if result.all_covered else 'Partially Open ☀️'}")
    print(f"• Path Path Nodes    : {' ➔ '.join(result.path)}")

    print("\nTURN-BY-TURN DIRECTIONS:")
    for d in result.directions:
        print(f"  {d}")


def handle_compare_routes(graph):
    print_header("COMPARE CAMPUS ROUTES & TRADEOFFS")
    start_id = choose_location(graph, "Select START location:", default="GATE")
    end_id = choose_location(graph, "Select DESTINATION location:", default="TURING_LAB")

    routes = find_alternative_routes(graph, start_id, end_id)

    print("\n" + "=" * 80)
    print(f"ROUTE COMPARISON: {graph.locations[start_id].name} ➔ {graph.locations[end_id].name}")
    print("=" * 80)
    print(f"{'Route Profile':<28} {'Distance':<12} {'Walk Time':<12} {'Accessible':<12} {'Covered':<10}")
    print("-" * 80)

    for name, r in routes.items():
        if r.found:
            acc_str = "Yes ✅" if r.is_fully_accessible else "No ❌"
            cov_str = "Yes ☔" if r.all_covered else "No"
            print(f"{name:<28} {r.total_distance:6.0f} m     {r.total_time_minutes:4.1f} min     {acc_str:<12} {cov_str:<10}")
            print(f"   └── Path: {' ➔ '.join(r.path)}")
        else:
            print(f"{name:<28} {'Not Available':<12}")
    print("-" * 80)


def handle_mst(graph):
    print_header("CAMPUS BACKBONE NETWORK PLANNING (MINIMUM SPANNING TREE)")
    print("Scenario: Connecting all 16 campus facilities with a campus-wide Fiber-Optic")
    print("Broadband & Smart CCTV network minimizing total trenching and cable length.")
    print("\nExecuting Prim's and Kruskal's MST Algorithms...")

    results = compare_mst_algorithms(graph)
    kruskal_res = results["Kruskal"]
    prim_res = results["Prim"]

    print("\n" + "=" * 75)
    print("MINIMUM SPANNING TREE (MST) ALGORITHM COMPARISON")
    print("=" * 75)
    print(f"• Kruskal's Total Cable Weight: {kruskal_res.total_weight_meters:.1f} meters (|E_mst| = {len(kruskal_res.edges)})")
    print(f"• Prim's Total Cable Weight   : {prim_res.total_weight_meters:.1f} meters (|E_mst| = {len(prim_res.edges)})")
    print(f"• Optimality Verification     : {'EXACT MATCH ✅ (Both achieve minimum weight)' if kruskal_res.total_weight_meters == prim_res.total_weight_meters else 'Discrepancy ❌'}")
    print("-" * 75)

    print("\nSelected Spanning Tree Links (Kruskal's DSU Selection):")
    for idx, edge in enumerate(kruskal_res.edges, 1):
        u_name = graph.locations[edge.source].name
        v_name = graph.locations[edge.destination].name
        print(f"  {idx:2d}. {edge.source:12} <---> {edge.destination:12} [{edge.distance_meters:3.0f}m] ({u_name} to {v_name})")

    # Cable savings compared to full graph
    total_existing_length = sum(e.distance_meters for e in graph.all_edges)
    savings = total_existing_length - kruskal_res.total_weight_meters
    pct_savings = (savings / total_existing_length) * 100
    print(f"\n💡 Efficiency Insight:")
    print(f"• Total graph edges cabling : {total_existing_length:.0f} meters (all {graph.edge_count} pathways)")
    print(f"• MST optimal cable network : {kruskal_res.total_weight_meters:.0f} meters (only {len(kruskal_res.edges)} links)")
    print(f"• Infrastructure Savings    : {savings:.0f} meters ({pct_savings:.1f}% reduction in trenching cost!)")


def handle_graph_representations(graph):
    print_header("GRAPH DATA STRUCTURE INSPECTOR (DAA CONCEPTS)")
    print("1. Adjacency List: Space-efficient O(V + E), ideal for traversal & Dijkstra.")
    print("2. Adjacency Matrix: O(V^2) matrix, ideal for dense graphs and O(1) edge lookup.")
    print("-" * 70)

    print("\n[A] Campus Adjacency List Representation:")
    print(graph.format_adjacency_list())

    print("\n[B] Campus Adjacency Matrix Representation:")
    print(graph.format_adjacency_matrix(max_display_nodes=10))


def handle_viva_trace(graph):
    print_header("STEP-BY-STEP ALGORITHM TRACE (EDUCATIONAL VIVA MODE)")
    print("Select algorithm to trace step-by-step:")
    print("  [1] Dijkstra's Shortest Path Algorithm (Priority Queue & Edge Relaxations)")
    print("  [2] Kruskal's MST Algorithm (Sorted Edges & DSU Cycle Prevention)")
    print("  [3] Prim's MST Algorithm (Cut Property & Greedy Frontier Expansion)")
    sub = input("Enter choice [1-3]: ").strip()

    if sub == "1":
        start_id = choose_location(graph, "Select Start Vertex:", default="GATE")
        end_id = choose_location(graph, "Select Destination Vertex:", default="TURING_LAB")
        res = dijkstra_shortest_path(graph, start_id, end_id, step_by_step=True)
        print("\n" + "=" * 70)
        print(f"DIJKSTRA STEP-BY-STEP TRACE: {start_id} ➔ {end_id}")
        print("=" * 70)
        for line in res.algorithm_steps:
            print(f"  {line}")

    elif sub == "2":
        res = kruskal_mst(graph, step_by_step=True)
        print("\n" + "=" * 70)
        print("KRUSKAL'S MST STEP-BY-STEP TRACE (DSU)")
        print("=" * 70)
        for line in res.step_trace:
            print(f"  {line}")

    elif sub == "3":
        root = choose_location(graph, "Select Root Vertex for Prim's:", default="ADMIN")
        res = prim_mst(graph, start_vertex=root, step_by_step=True)
        print("\n" + "=" * 70)
        print(f"PRIM'S MST STEP-BY-STEP TRACE (Root: {root})")
        print("=" * 70)
        for line in res.step_trace:
            print(f"  {line}")


def handle_export_map(graph):
    print_header("GENERATE INTERACTIVE HTML/SVG CAMPUS MAP")
    default_route = dijkstra_shortest_path(graph, "GATE", "TURING_LAB")
    mst_res = kruskal_mst(graph)

    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "campus_map.html"))
    generate_interactive_html(graph, active_route=default_route, active_mst=mst_res, output_path=file_path)

    print(f"\n✅ Interactive HTML Map generated successfully!")
    print(f"📁 File location: {file_path}")
    print("🌐 You can open this file in any web browser to interactively test paths and visualize the campus!")


def main_menu():
    graph = build_default_campus()

    while True:
        print("\n" + "=" * 70)
        print("🗺️  SMART CAMPUS NAVIGATION SYSTEM (DAA PROJECT)")
        print("=" * 70)
        print("  [1] View Campus Directory & Map Overview")
        print("  [2] Find Shortest Path between Buildings (Dijkstra's Algorithm)")
        print("  [3] Compare Routes (Shortest vs Wheelchair-Accessible vs Alternate)")
        print("  [4] Plan Campus Backbone Network (Prim's & Kruskal's MST)")
        print("  [5] Inspect Graph Data Structures (Adjacency List vs Matrix)")
        print("  [6] Educational Step-by-Step Viva Trace (Dijkstra / Prim / Kruskal)")
        print("  [7] Generate & Export Interactive HTML/SVG Campus Map")
        print("  [0] Exit")
        print("=" * 70)

        choice = input("Enter your option [0-7]: ").strip()

        if choice == "1":
            print(render_terminal_overview(graph))
        elif choice == "2":
            handle_shortest_path(graph)
        elif choice == "3":
            handle_compare_routes(graph)
        elif choice == "4":
            handle_mst(graph)
        elif choice == "5":
            handle_graph_representations(graph)
        elif choice == "6":
            handle_viva_trace(graph)
        elif choice == "7":
            handle_export_map(graph)
        elif choice == "0":
            print("\nThank you for using the Smart Campus Navigation System. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please choose a valid option.")


if __name__ == "__main__":
    main_menu()
