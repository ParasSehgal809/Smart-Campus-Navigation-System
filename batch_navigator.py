"""
batch_navigator.py - Batch Navigation & Campus Traffic Simulation Engine
Design and Analysis of Algorithms (DAA) concepts:
- Batch Execution: Runs high-volume shortest-path calculations across student cohorts.
- Edge Frequency & Congestion Analysis: Tracks edge traversal counts to identify campus bottlenecks.
- Algorithmic Scalability: Benchmarks batch routing throughput.
"""

import json
import csv
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from campus_graph import build_default_campus, CampusGraph
from algorithms import dijkstra_shortest_path


@dataclass
class StudentTrip:
    student_id: str
    student_name: str
    start_id: str
    end_id: str
    preference: str = "shortest"  # "shortest", "accessible", "covered"
    # Computed fields:
    path: List[str] = None
    distance_meters: float = 0.0
    walking_time_minutes: float = 0.0
    is_accessible: bool = True


@dataclass
class BatchSimulationResult:
    scenario_name: str
    total_trips: int
    successful_trips: int
    total_distance_km: float
    avg_trip_distance_meters: float
    avg_walking_time_minutes: float
    accessible_trips_count: int
    execution_time_ms: float
    edge_traffic: Dict[str, int]
    most_congested_path: str
    most_congested_count: int
    trips: List[StudentTrip]


def run_batch_simulation(
    graph: CampusGraph,
    trips_spec: List[Dict],
    scenario_name: str = "Custom Batch",
) -> BatchSimulationResult:
    """
    Executes batch routing for a list of student trips.
    Tracks individual routes and campus pathway traffic congestion.
    """
    t_start = time.perf_counter()
    edge_counter: Dict[str, int] = {}
    completed_trips: List[StudentTrip] = []

    total_dist = 0.0
    total_time = 0.0
    accessible_count = 0

    for item in trips_spec:
        s_id = item.get("student_id", f"STU_{len(completed_trips)+1:03d}")
        s_name = item.get("name", "Student")
        start = item["start"]
        end = item["end"]
        pref = item.get("pref", "shortest")

        constraint_fn = None
        weight_fn = None
        if pref == "accessible":
            constraint_fn = lambda e: e.is_accessible
        elif pref == "covered":
            weight_fn = lambda e: e.distance_meters * (1.0 if e.is_covered else 2.0)

        route = dijkstra_shortest_path(
            graph,
            start_id=start,
            end_id=end,
            constraint_fn=constraint_fn,
            weight_fn=weight_fn,
        )

        trip = StudentTrip(
            student_id=s_id,
            student_name=s_name,
            start_id=start,
            end_id=end,
            preference=pref,
            path=route.path if route.found else [],
            distance_meters=route.total_distance if route.found else 0.0,
            walking_time_minutes=route.total_time_minutes if route.found else 0.0,
            is_accessible=route.is_fully_accessible if route.found else False,
        )
        completed_trips.append(trip)

        if route.found:
            total_dist += route.total_distance
            total_time += route.total_time_minutes
            if route.is_fully_accessible:
                accessible_count += 1

            # Count edge usage
            for edge in route.edges:
                key = " <---> ".join(sorted([edge.source, edge.destination]))
                edge_counter[key] = edge_counter.get(key, 0) + 1

    t_end = time.perf_counter()
    exec_time_ms = round((t_end - t_start) * 1000, 2)

    # Find highest traffic edge
    most_congested_path = "None"
    most_congested_count = 0
    if edge_counter:
        most_congested_path, most_congested_count = max(edge_counter.items(), key=lambda x: x[1])

    n = len(completed_trips)
    return BatchSimulationResult(
        scenario_name=scenario_name,
        total_trips=n,
        successful_trips=sum(1 for t in completed_trips if t.path),
        total_distance_km=round(total_dist / 1000.0, 2),
        avg_trip_distance_meters=round(total_dist / n, 1) if n else 0.0,
        avg_walking_time_minutes=round(total_time / n, 1) if n else 0.0,
        accessible_trips_count=accessible_count,
        execution_time_ms=exec_time_ms,
        edge_traffic=edge_counter,
        most_congested_path=most_congested_path,
        most_congested_count=most_congested_count,
        trips=completed_trips,
    )


def get_predefined_scenarios() -> Dict[str, Tuple[str, List[Dict]]]:
    """Provides standard campus timetable transition scenarios for simulation."""
    # Scenario 1: Morning 08:45 AM Rush (Hostels & Gate to Classrooms and Labs)
    morning_trips = [
        {"student_id": "CS101", "name": "Aarav Sharma", "start": "HOSTEL_N", "end": "LECTURE_A", "pref": "shortest"},
        {"student_id": "CS102", "name": "Bhavna Patel", "start": "HOSTEL_S", "end": "CS_BLOCK", "pref": "shortest"},
        {"student_id": "CS103", "name": "Chetan Verma", "start": "GATE", "end": "TURING_LAB", "pref": "shortest"},
        {"student_id": "CS104", "name": "Divya Nair", "start": "GATE", "end": "TURING_LAB", "pref": "accessible"},
        {"student_id": "EC105", "name": "Eshan Gupta", "start": "HOSTEL_N", "end": "ECE_BLOCK", "pref": "shortest"},
        {"student_id": "EC106", "name": "Farhan Ali", "start": "GATE", "end": "IOT_LAB", "pref": "shortest"},
        {"student_id": "ME107", "name": "Gaurav Joshi", "start": "HOSTEL_N", "end": "MECH_BLOCK", "pref": "shortest"},
        {"student_id": "ME108", "name": "Hina Kaushik", "start": "HOSTEL_S", "end": "MECH_BLOCK", "pref": "shortest"},
        {"student_id": "BT109", "name": "Ishaan Roy", "start": "GATE", "end": "LECTURE_B", "pref": "covered"},
        {"student_id": "CS110", "name": "Jaya Sen", "start": "HOSTEL_S", "end": "LIB", "pref": "shortest"},
        {"student_id": "CS111", "name": "Karan Mehra", "start": "GATE", "end": "ADMIN", "pref": "shortest"},
        {"student_id": "EC112", "name": "Lavanya Rao", "start": "HOSTEL_N", "end": "LECTURE_A", "pref": "shortest"},
        {"student_id": "ME113", "name": "Manish Yadav", "start": "HOSTEL_S", "end": "LECTURE_B", "pref": "shortest"},
        {"student_id": "CS114", "name": "Neha Kapoor", "start": "GATE", "end": "CS_BLOCK", "pref": "shortest"},
        {"student_id": "CS115", "name": "Omkar Dixit", "start": "HOSTEL_N", "end": "TURING_LAB", "pref": "accessible"},
    ]

    # Scenario 2: 12:30 PM Lunch Peak (Classrooms & Labs to Cafeteria)
    lunch_trips = [
        {"student_id": "L001", "name": "Group A1", "start": "LECTURE_A", "end": "CAFETERIA", "pref": "shortest"},
        {"student_id": "L002", "name": "Group A2", "start": "LECTURE_B", "end": "CAFETERIA", "pref": "shortest"},
        {"student_id": "L003", "name": "Group CS", "start": "CS_BLOCK", "end": "CAFETERIA", "pref": "shortest"},
        {"student_id": "L004", "name": "Group AI", "start": "TURING_LAB", "end": "CAFETERIA", "pref": "shortest"},
        {"student_id": "L005", "name": "Group EC", "start": "ECE_BLOCK", "end": "CAFETERIA", "pref": "shortest"},
        {"student_id": "L006", "name": "Group IOT", "start": "IOT_LAB", "end": "CAFETERIA", "pref": "shortest"},
        {"student_id": "L007", "name": "Group ME", "start": "MECH_BLOCK", "end": "CAFETERIA", "pref": "shortest"},
        {"student_id": "L008", "name": "Library Readers", "start": "LIB", "end": "CAFETERIA", "pref": "covered"},
        {"student_id": "L009", "name": "Admin Staff", "start": "ADMIN", "end": "CAFETERIA", "pref": "covered"},
        {"student_id": "L010", "name": "Sports Team", "start": "SPORTS_CTR", "end": "CAFETERIA", "pref": "shortest"},
    ]

    # Scenario 3: 05:00 PM Evening Recreation & Library Study
    evening_trips = [
        {"student_id": "E001", "name": "Badminton Squad", "start": "HOSTEL_N", "end": "SPORTS_CTR", "pref": "shortest"},
        {"student_id": "E002", "name": "Gym Enthusiasts", "start": "HOSTEL_S", "end": "SPORTS_CTR", "pref": "shortest"},
        {"student_id": "E003", "name": "Research Scholars", "start": "CS_BLOCK", "end": "LIB", "pref": "shortest"},
        {"student_id": "E004", "name": "First Aid Visit", "start": "SPORTS_CTR", "end": "HEALTH_CTR", "pref": "shortest"},
        {"student_id": "E005", "name": "Evening Commuters", "start": "LIB", "end": "GATE", "pref": "covered"},
        {"student_id": "E006", "name": "Day Scholars", "start": "MECH_BLOCK", "end": "GATE", "pref": "shortest"},
        {"student_id": "E007", "name": "Hostel Return", "start": "CAFETERIA", "end": "HOSTEL_N", "pref": "shortest"},
        {"student_id": "E008", "name": "Hostel Return", "start": "CAFETERIA", "end": "HOSTEL_S", "pref": "shortest"},
    ]

    return {
        "morning_rush": ("Morning Class Rush (08:45 AM)", morning_trips),
        "lunch_peak": ("Lunch Break Influx (12:30 PM)", lunch_trips),
        "evening_recreation": ("Evening Sports & Library Transition (05:00 PM)", evening_trips),
    }


def print_batch_summary(result: BatchSimulationResult):
    """Outputs a formatted table of batch results and congestion analysis."""
    print("\n" + "=" * 80)
    print(f"📊 BATCH TRANSIT SIMULATION: {result.scenario_name.upper()}")
    print("=" * 80)
    print(f"• Total Student Trips Processed : {result.total_trips}")
    print(f"• Cumulative Cohort Distance    : {result.total_distance_km:.2f} km")
    print(f"• Average Walking Distance/Trip : {result.avg_trip_distance_meters:.1f} meters")
    print(f"• Average Walking Time/Trip     : {result.avg_walking_time_minutes:.1f} minutes")
    print(f"• Wheelchair Accessible Routes  : {result.accessible_trips_count}/{result.total_trips}")
    print(f"• Computation Execution Time    : {result.execution_time_ms:.2f} ms")
    print("-" * 80)
    print(f"🚨 CAMPUS BOTTLENECK ANALYSIS:")
    print(f"• Most Heavily Trafficked Edge  : {result.most_congested_path}")
    print(f"• Student Volume on Bottleneck  : {result.most_congested_count} trips")
    print("-" * 80)

    print("\nTop 5 Most Congested Pathways on Campus:")
    sorted_edges = sorted(result.edge_traffic.items(), key=lambda x: x[1], reverse=True)[:5]
    for idx, (path_name, count) in enumerate(sorted_edges, 1):
        bar = "█" * (count * 2)
        print(f"  {idx}. {path_name:<32} : {count:2d} trips {bar}")

    print("\nSample Student Route Allocations:")
    print(f"{'Student ID':<12} {'Name':<18} {'From':<12} {'To':<14} {'Dist':<8} {'Time':<8} {'Path'}")
    print("-" * 80)
    for t in result.trips[:8]:
        path_str = " ➔ ".join(t.path)
        print(f"{t.student_id:<12} {t.student_name:<18} {t.start_id:<12} {t.end_id:<14} {t.distance_meters:<6.0f}m {t.walking_time_minutes:<6.1f}m {path_str}")
    print("=" * 80)


def export_batch_csv(result: BatchSimulationResult, filename: str = "batch_simulation_report.csv"):
    """Exports batch simulation details to a CSV spreadsheet."""
    if not os.path.isabs(filename):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(script_dir, filename)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Student ID", "Student Name", "Start Location", "Destination", "Preference", "Distance (m)", "Walk Time (min)", "Accessible", "Path Route"])
        for t in result.trips:
            writer.writerow([
                t.student_id,
                t.student_name,
                t.start_id,
                t.end_id,
                t.preference,
                t.distance_meters,
                t.walking_time_minutes,
                "Yes" if t.is_accessible else "No",
                " -> ".join(t.path),
            ])


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch Navigation & Campus Traffic Simulation")
    parser.add_argument("--scenario", choices=["morning_rush", "lunch_peak", "evening_recreation", "all"], default="all")
    parser.add_argument("--csv", help="Optional CSV filename to export results", default="batch_results.csv")
    args = parser.parse_args()

    graph = build_default_campus()
    scenarios = get_predefined_scenarios()

    if args.scenario == "all":
        for key, (sc_name, trips) in scenarios.items():
            res = run_batch_simulation(graph, trips, scenario_name=sc_name)
            print_batch_summary(res)
    else:
        sc_name, trips = scenarios[args.scenario]
        res = run_batch_simulation(graph, trips, scenario_name=sc_name)
        print_batch_summary(res)
        if args.csv:
            export_batch_csv(res, args.csv)
            print(f"\n✔ Successfully exported batch report to: {args.csv}")


if __name__ == "__main__":
    main()
