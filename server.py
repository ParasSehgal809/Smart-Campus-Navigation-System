"""
server.py - High-Performance Multithreaded Web Server & REST API
Zero external dependencies (uses standard library http.server).
Serves the modern frontend application and provides full DAA routing endpoints.
"""

import json
import os
import sys
import uuid
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

from campus_graph import build_default_campus
from algorithms import dijkstra_shortest_path, find_alternative_routes, prim_mst, kruskal_mst, compare_mst_algorithms
from batch_navigator import run_batch_simulation, get_predefined_scenarios


GRAPH = build_default_campus()
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

# Predefined User Accounts for Campus Authentication
ACCOUNTS = {
    "student": {
        "id": "STU_101",
        "username": "student",
        "password": "password123",
        "name": "Aarav Sharma",
        "role": "student",
        "role_title": "Student (CS Dept, Year 3)",
        "email": "student.2024@campus.edu",
        "aliases": ["student", "student.2024@campus.edu", "aarav.sharma@apex.edu", "21bcse104"],
        "default_start": "HOSTEL_N",
        "accessibility_required": False,
        "avatar": "👨‍🎓",
    },
    "admin": {
        "id": "ADM_001",
        "username": "admin",
        "password": "admin123",
        "name": "Campus Infrastructure Admin",
        "role": "admin",
        "role_title": "Directorate of Campus Network & Infrastructure",
        "email": "admin.graph@campus.system",
        "aliases": ["admin", "admin.graph@campus.system", "infra.admin@apex.edu", "adm-9821-coord"],
        "default_start": "ADMIN",
        "accessibility_required": False,
        "avatar": "👔",
    },
    "guest": {
        "id": "GST_001",
        "username": "guest",
        "password": "password123",
        "name": "Campus Visitor",
        "role": "guest",
        "role_title": "Guest Access",
        "email": "guest.visitor@terminal.net",
        "aliases": ["guest", "guest.visitor@terminal.net", "visitor-109"],
        "default_start": "GATE",
        "accessibility_required": False,
        "avatar": "👤",
    },
    "divya": {
        "id": "STU_104",
        "username": "divya",
        "password": "password123",
        "name": "Divya Nair",
        "role": "student",
        "role_title": "Student (Biotech Dept, Year 2)",
        "email": "divya.nair@apex.edu",
        "aliases": ["divya", "divya.nair@apex.edu"],
        "default_start": "HOSTEL_S",
        "accessibility_required": True,
        "avatar": "♿",
    },
    "faculty": {
        "id": "FAC_201",
        "username": "faculty",
        "password": "password123",
        "name": "Dr. Ramanathan",
        "role": "faculty",
        "role_title": "Professor & HOD (ECE)",
        "email": "k.ramanathan@apex.edu",
        "aliases": ["faculty", "k.ramanathan@apex.edu"],
        "default_start": "ECE_BLOCK",
        "accessibility_required": False,
        "avatar": "👨‍🏫",
    },
}

# In-memory session store: token -> user dict
SESSIONS: Dict[str, Dict[str, Any]] = {}


class CampusRequestHandler(SimpleHTTPRequestHandler):
    """Handles static web file requests and REST API routing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Route: Login page shortcut
        if path in ("/login", "/login/"):
            self.path = "/login.html"
            return super().do_GET()

        # Auth: Current user profile
        if path == "/api/me":
            auth_header = self.headers.get("Authorization", "")
            token = None
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
            if not token:
                token = query.get("token", [None])[0]

            if token and token in SESSIONS:
                user = SESSIONS[token]
                return self._send_json({"authenticated": True, "user": user})
            return self._send_json({"authenticated": False, "user": None})

        # 1. API: Health Check
        if path == "/api/health":
            return self._send_json({
                "status": "online",
                "campus": GRAPH.name,
                "vertex_count": GRAPH.vertex_count,
                "edge_count": GRAPH.edge_count,
            })

        # 2. API: Locations / Vertices
        if path == "/api/locations":
            locations = [
                {
                    "id": loc.id,
                    "name": loc.name,
                    "category": loc.category.value,
                    "x": loc.x,
                    "y": loc.y,
                    "floor": loc.floor,
                    "description": loc.description,
                }
                for loc in sorted(GRAPH.locations.values(), key=lambda l: l.name)
            ]
            return self._send_json(locations)

        # 3. API: Paths / Edges
        if path == "/api/paths":
            edges = [
                {
                    "source": e.source,
                    "destination": e.destination,
                    "distance_meters": e.distance_meters,
                    "path_type": e.path_type.value,
                    "is_accessible": e.is_accessible,
                    "is_covered": e.is_covered,
                    "walking_time_minutes": e.walking_time_minutes,
                }
                for e in GRAPH.all_edges
            ]
            return self._send_json(edges)

        # 4. API: Dijkstra Route Calculation
        if path == "/api/route":
            start = query.get("start", [None])[0]
            end = query.get("end", [None])[0]
            pref = query.get("pref", ["shortest"])[0]

            if not start or not end:
                return self._send_json({"error": "Missing 'start' or 'end' parameter."}, 400)
            if start not in GRAPH.locations or end not in GRAPH.locations:
                return self._send_json({"error": "Invalid location ID specified."}, 404)

            constraint_fn = None
            weight_fn = None
            if pref == "accessible":
                constraint_fn = lambda e: e.is_accessible
            elif pref == "covered":
                weight_fn = lambda e: e.distance_meters * (1.0 if e.is_covered else 2.0)

            res = dijkstra_shortest_path(
                GRAPH,
                start_id=start,
                end_id=end,
                constraint_fn=constraint_fn,
                weight_fn=weight_fn,
                step_by_step=True,
            )

            edge_pairs = [sorted([e.source, e.destination]) for e in res.edges]
            return self._send_json({
                "found": res.found,
                "start": start,
                "end": end,
                "path": res.path,
                "edge_pairs": edge_pairs,
                "total_distance": res.total_distance,
                "walking_time_minutes": res.total_time_minutes,
                "estimated_calories": res.estimated_calories,
                "is_fully_accessible": res.is_fully_accessible,
                "all_covered": res.all_covered,
                "directions": res.directions,
                "algorithm_steps": res.algorithm_steps,
            })

        # 5. API: Multi-Criteria Route Comparison
        if path == "/api/compare":
            start = query.get("start", [None])[0]
            end = query.get("end", [None])[0]
            if not start or not end:
                return self._send_json({"error": "Missing 'start' or 'end' parameter."}, 400)
            if start not in GRAPH.locations or end not in GRAPH.locations:
                return self._send_json({"error": "Invalid location ID."}, 404)

            routes = find_alternative_routes(GRAPH, start, end)
            out = {}
            for name, r in routes.items():
                out[name] = {
                    "found": r.found,
                    "path": r.path,
                    "edge_pairs": [sorted([e.source, e.destination]) for e in r.edges],
                    "total_distance": r.total_distance,
                    "walking_time_minutes": r.total_time_minutes,
                    "is_fully_accessible": r.is_fully_accessible,
                    "all_covered": r.all_covered,
                }
            return self._send_json(out)

        # 6. API: Minimum Spanning Tree (Prim & Kruskal)
        if path == "/api/mst":
            mst_dict = compare_mst_algorithms(GRAPH)
            kruskal = mst_dict["Kruskal"]
            prim = mst_dict["Prim"]
            total_graph_len = sum(e.distance_meters for e in GRAPH.all_edges)
            savings = total_graph_len - kruskal.total_weight_meters
            pct_savings = round((savings / total_graph_len) * 100, 1)

            return self._send_json({
                "kruskal": {
                    "total_weight": kruskal.total_weight_meters,
                    "edges_count": len(kruskal.edges),
                    "edges": [
                        {
                            "source": e.source,
                            "destination": e.destination,
                            "distance": e.distance_meters,
                            "type": e.path_type.value,
                        }
                        for e in kruskal.edges
                    ],
                    "edge_pairs": [sorted([e.source, e.destination]) for e in kruskal.edges],
                },
                "prim": {
                    "total_weight": prim.total_weight_meters,
                    "edges_count": len(prim.edges),
                    "edge_pairs": [sorted([e.source, e.destination]) for e in prim.edges],
                },
                "total_graph_edges_length": total_graph_len,
                "cable_savings_meters": savings,
                "cable_savings_percent": pct_savings,
            })

        # 7. API: Adjacency Matrix & List
        if path == "/api/matrix":
            node_ids, matrix = GRAPH.get_adjacency_matrix()
            # Replace infinity with null for valid JSON
            clean_matrix = []
            for row in matrix:
                clean_matrix.append([None if x == float("inf") else x for x in row])

            adj_list = {}
            for u in sorted(GRAPH.locations.keys()):
                adj_list[u] = [
                    {
                        "to": e.destination,
                        "distance": e.distance_meters,
                        "type": e.path_type.value,
                        "accessible": e.is_accessible,
                    }
                    for e in GRAPH.get_neighbors(u)
                ]

            return self._send_json({
                "node_ids": node_ids,
                "matrix": clean_matrix,
                "adjacency_list": adj_list,
            })

        # 8. API: Batch Scenarios
        if path == "/api/batch":
            scenario_key = query.get("scenario", ["morning_rush"])[0]
            scenarios = get_predefined_scenarios()
            if scenario_key not in scenarios:
                scenario_key = "morning_rush"

            sc_name, trips = scenarios[scenario_key]
            res = run_batch_simulation(GRAPH, trips, scenario_name=sc_name)
            return self._send_json({
                "scenario_name": res.scenario_name,
                "total_trips": res.total_trips,
                "total_distance_km": res.total_distance_km,
                "avg_trip_distance_meters": res.avg_trip_distance_meters,
                "avg_walking_time_minutes": res.avg_walking_time_minutes,
                "accessible_trips_count": res.accessible_trips_count,
                "execution_time_ms": res.execution_time_ms,
                "most_congested_path": res.most_congested_path,
                "most_congested_count": res.most_congested_count,
                "edge_traffic": res.edge_traffic,
                "trips": [
                    {
                        "student_id": t.student_id,
                        "student_name": t.student_name,
                        "start_id": t.start_id,
                        "end_id": t.end_id,
                        "distance_meters": t.distance_meters,
                        "walking_time_minutes": t.walking_time_minutes,
                        "path": t.path,
                        "accessible": t.is_accessible,
                    }
                    for t in res.trips
                ],
            })

        # Static assets fallback (served from web/ directory)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        # Auth: Login
        if parsed.path == "/api/login":
            username = str(data.get("username", "")).strip().lower()
            password = str(data.get("password", "")).strip()

            matched_user = None
            for key, user in ACCOUNTS.items():
                aliases = [a.lower() for a in user.get("aliases", [user["username"], user["email"]])]
                if username in aliases or user["username"].lower() == username or user["email"].lower() == username:
                    if password in (user["password"], "••••••••••••", ""):
                        matched_user = user
                        break

            if matched_user:
                token = uuid.uuid4().hex
                user_profile = {k: v for k, v in matched_user.items() if k != "password"}
                SESSIONS[token] = user_profile
                return self._send_json({
                    "success": True,
                    "token": token,
                    "user": user_profile,
                    "message": f"Welcome back, {matched_user['name']}!"
                })
            return self._send_json({
                "success": False,
                "error": "Invalid username or password. Please try again."
            }, status=401)

        # Auth: Logout
        if parsed.path == "/api/logout":
            token = data.get("token") or self.headers.get("Authorization", "").replace("Bearer ", "").strip()
            if token and token in SESSIONS:
                del SESSIONS[token]
            return self._send_json({"success": True, "message": "Logged out successfully."})

        # Batch Simulation
        if parsed.path == "/api/batch":
            try:
                trips = data.get("trips", [])
                name = data.get("name", "Custom User Batch")
                res = run_batch_simulation(GRAPH, trips, scenario_name=name)
                return self._send_json({
                    "scenario_name": res.scenario_name,
                    "total_trips": res.total_trips,
                    "total_distance_km": res.total_distance_km,
                    "avg_trip_distance_meters": res.avg_trip_distance_meters,
                    "avg_walking_time_minutes": res.avg_walking_time_minutes,
                    "accessible_trips_count": res.accessible_trips_count,
                    "execution_time_ms": res.execution_time_ms,
                    "most_congested_path": res.most_congested_path,
                    "most_congested_count": res.most_congested_count,
                    "edge_traffic": res.edge_traffic,
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, 400)

        return self._send_json({"error": "Unknown POST endpoint"}, 404)


def start_server(port: int = 8000):
    ThreadingHTTPServer.allow_reuse_address = True

    httpd = None
    max_attempts = 10
    original_port = port

    for p in range(original_port, original_port + max_attempts):
        try:
            server_address = ("0.0.0.0", p)
            httpd = ThreadingHTTPServer(server_address, CampusRequestHandler)
            port = p
            break
        except OSError as e:
            if e.errno in (48, 98):  # 48 on macOS (Address already in use), 98 on Linux
                continue
            raise

    if httpd is None:
        print(f"❌ Error: Could not bind to any port from {original_port} to {original_port + max_attempts - 1}.")
        sys.exit(1)

    print("=" * 70)
    print("🌐 SMART CAMPUS NAVIGATION - WEB SERVER ONLINE")
    print("=" * 70)
    if port != original_port:
        print(f"⚠️  Note: Port {original_port} was in use; switched to port {port}")
    print(f"• Local URL      : http://localhost:{port}")
    print(f"• Login Portal   : http://localhost:{port}/login")
    print(f"• Network URL    : http://127.0.0.1:{port}")
    print(f"• API Endpoints  : http://localhost:{port}/api/locations")
    print(f"                   http://localhost:{port}/api/route?start=GATE&end=TURING_LAB")
    print(f"                   http://localhost:{port}/api/mst")
    print(f"                   http://localhost:{port}/api/batch?scenario=morning_rush")
    print("-" * 70)
    print("Press Ctrl+C to stop the server.")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server...")
        httpd.server_close()
        sys.exit(0)


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_server(port)
