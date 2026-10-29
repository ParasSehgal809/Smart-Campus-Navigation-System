"""
visualizer.py - Campus Map Visualizer (Interactive SVG/HTML & Terminal Text Maps)
Generates:
1. Self-contained interactive HTML/SVG campus map with pathfinding & MST overlays.
2. Clean ASCII terminal map for CLI demonstration.
"""

import json
from typing import Dict, List, Optional
from models import RouteResult, MSTResult, LocationType


def render_terminal_overview(graph) -> str:
    """Renders a clean text-based overview of the campus map and locations."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"🎓 {graph.name.upper()} - DIRECTORY")
    lines.append("=" * 80)
    lines.append(f"{'ID':<14} {'Name':<36} {'Category':<22} {'Description'}")
    lines.append("-" * 80)
    for loc_id, loc in sorted(graph.locations.items()):
        lines.append(f"{loc.id:<14} {loc.name:<36} {loc.category.value:<22} {loc.description}")
    lines.append("-" * 80)
    lines.append(f"Total Facilities: {graph.vertex_count} vertices | Walking Pathways: {graph.edge_count} edges")
    return "\n".join(lines)


def generate_interactive_html(
    graph,
    active_route: Optional[RouteResult] = None,
    active_mst: Optional[MSTResult] = None,
    output_path: str = "campus_map.html",
) -> str:
    """
    Generates a rich, standalone interactive HTML file with an embedded SVG graph,
    dynamic path selection, accessibility toggles, MST fiber overlay, and DAA info cards.
    Requires no external internet connection or CDNs.
    """
    locations_data = []
    for loc_id, loc in graph.locations.items():
        locations_data.append({
            "id": loc.id,
            "name": loc.name,
            "category": loc.category.value,
            "x": loc.x,
            "y": loc.y,
            "floor": loc.floor,
            "desc": loc.description,
        })

    edges_data = []
    for edge in graph.all_edges:
        edges_data.append({
            "source": edge.source,
            "destination": edge.destination,
            "distance": edge.distance_meters,
            "type": edge.path_type.value,
            "accessible": edge.is_accessible,
            "covered": edge.is_covered,
            "time": edge.walking_time_minutes,
        })

    # Prepare initial route & MST edge lists if provided
    route_edges_keys = []
    if active_route and active_route.found:
        for e in active_route.edges:
            pair = tuple(sorted([e.source, e.destination]))
            route_edges_keys.append(f"{pair[0]}--{pair[1]}")

    mst_edges_keys = []
    if active_mst:
        for e in active_mst.edges:
            pair = tuple(sorted([e.source, e.destination]))
            mst_edges_keys.append(f"{pair[0]}--{pair[1]}")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Campus Navigation System - Interactive Map</title>
<style>
  :root {{
    --bg-dark: #0f172a;
    --card-bg: #1e293b;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent-blue: #38bdf8;
    --accent-green: #22c55e;
    --accent-purple: #a855f7;
    --accent-orange: #f97316;
    --border-color: #334155;
    --path-color: #64748b;
    --shortest-color: #10b981;
    --mst-color: #06b6d4;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg-dark);
    color: var(--text-primary);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  header {{
    background: var(--card-bg);
    border-bottom: 1px solid var(--border-color);
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }}
  header h1 {{ font-size: 1.4rem; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }}
  .badge {{
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
  }}
  .main-layout {{
    display: flex;
    flex: 1;
    overflow: hidden;
  }}
  .map-container {{
    flex: 1;
    position: relative;
    background: #090d16;
    overflow: auto;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
  }}
  svg {{
    max-width: 100%;
    height: auto;
    background: radial-gradient(circle at 50% 50%, #162032 0%, #090d16 100%);
    border-radius: 12px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  }}
  .sidebar {{
    width: 380px;
    background: var(--card-bg);
    border-left: 1px solid var(--border-color);
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    overflow-y: auto;
    max-height: calc(100vh - 70px);
  }}
  .card {{
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 14px;
  }}
  .card-title {{
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent-blue);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  label {{ font-size: 0.8rem; color: var(--text-secondary); display: block; margin-bottom: 4px; }}
  select, button {{
    width: 100%;
    padding: 10px 12px;
    background: #0f172a;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.9rem;
    margin-bottom: 10px;
    outline: none;
    cursor: pointer;
  }}
  select:focus {{ border-color: var(--accent-blue); }}
  .btn-primary {{
    background: #2563eb;
    border: none;
    font-weight: 600;
    transition: background 0.2s;
  }}
  .btn-primary:hover {{ background: #1d4ed8; }}
  .btn-accent {{
    background: #0891b2;
    border: none;
    font-weight: 600;
  }}
  .btn-accent:hover {{ background: #0e7490; }}
  .toggle-group {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 8px 0;
  }}
  .toggle-group input[type="checkbox"] {{
    width: 18px;
    height: 18px;
    accent-color: var(--accent-green);
    cursor: pointer;
  }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-top: 10px;
  }}
  .stat-box {{
    background: #0f172a;
    padding: 10px;
    border-radius: 6px;
    text-align: center;
  }}
  .stat-val {{ font-size: 1.25rem; font-weight: 700; color: var(--accent-green); }}
  .stat-label {{ font-size: 0.7rem; color: var(--text-secondary); }}
  .directions-list {{
    font-size: 0.82rem;
    color: #cbd5e1;
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 180px;
    overflow-y: auto;
  }}
  .dir-step {{
    background: #0f172a;
    padding: 6px 8px;
    border-left: 3px solid var(--accent-blue);
    border-radius: 2px;
  }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 0.75rem;
  }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  .legend-line {{ width: 20px; height: 3px; border-radius: 2px; }}

  /* SVG Specific Styles */
  .edge-line {{ stroke: #475569; stroke-width: 2.5; stroke-dasharray: 4, 3; transition: all 0.3s ease; }}
  .edge-line.active-route {{ stroke: #10b981; stroke-width: 5; stroke-dasharray: none; filter: drop-shadow(0 0 6px rgba(16,185,129,0.8)); }}
  .edge-line.active-mst {{ stroke: #06b6d4; stroke-width: 4; stroke-dasharray: none; filter: drop-shadow(0 0 4px rgba(6,182,212,0.8)); }}
  .edge-weight {{ fill: #94a3b8; font-size: 10px; font-weight: 600; text-anchor: middle; }}
  .node-group {{ cursor: pointer; transition: transform 0.2s; }}
  .node-group:hover {{ transform: scale(1.1); }}
  .node-circle {{ fill: #1e293b; stroke: #38bdf8; stroke-width: 2.5; transition: all 0.2s; }}
  .node-group.is-start .node-circle {{ fill: #15803d; stroke: #4ade80; stroke-width: 3.5; }}
  .node-group.is-end .node-circle {{ fill: #b91c1c; stroke: #f87171; stroke-width: 3.5; }}
  .node-label {{ fill: #f8fafc; font-size: 11px; font-weight: 600; text-anchor: middle; pointer-events: none; }}
  .node-sub {{ fill: #94a3b8; font-size: 8.5px; text-anchor: middle; pointer-events: none; }}
</style>
</head>
<body>

<header>
  <div>
    <h1>🗺️ Smart Campus Navigation System</h1>
    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px;">
      DAA Demonstration: Dijkstra's Shortest Path & Prim/Kruskal Minimum Spanning Tree
    </p>
  </div>
  <div style="display: flex; gap: 8px;">
    <span class="badge">Graph: |V| = {graph.vertex_count}, |E| = {graph.edge_count}</span>
    <span class="badge" style="background: rgba(34, 197, 94, 0.15); color: #4ade80; border-color: rgba(74, 222, 128, 0.3);">
      Dijkstra O((V+E) log V)
    </span>
  </div>
</header>

<div class="main-layout">
  <!-- Interactive Map SVG Area -->
  <div class="map-container">
    <svg id="campusSvg" viewBox="0 0 920 680" width="920" height="680">
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />

      <!-- Campus Pathways (Edges) -->
      <g id="edgesLayer"></g>
      <!-- Edge Distance Labels -->
      <g id="edgeLabelsLayer"></g>
      <!-- Campus Buildings (Vertices) -->
      <g id="nodesLayer"></g>
    </svg>
  </div>

  <!-- Interactive Controls Sidebar -->
  <div class="sidebar">
    <div class="card">
      <div class="card-title">📍 Path Navigation</div>
      <label for="startSelect">Start Location:</label>
      <select id="startSelect"></select>

      <label for="endSelect">Destination Location:</label>
      <select id="endSelect"></select>

      <div class="toggle-group">
        <input type="checkbox" id="accessibleToggle">
        <label for="accessibleToggle" style="margin-bottom:0; cursor:pointer;">
          ♿ Wheelchair Accessible (Avoid Stairs)
        </label>
      </div>

      <button class="btn-primary" onclick="calculateRoute()">Find Shortest Route (Dijkstra)</button>
      <button class="btn-accent" onclick="toggleMST()">Toggle Campus Backbone (MST)</button>
    </div>

    <div class="card" id="resultsCard">
      <div class="card-title">📊 Navigation Metrics</div>
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-val" id="resDist">0 m</div>
          <div class="stat-label">Total Distance</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="resTime">0 min</div>
          <div class="stat-label">Est. Walk Time</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="resCal">0 kcal</div>
          <div class="stat-label">Calories Burned</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="resHops">0</div>
          <div class="stat-label">Building Hops</div>
        </div>
      </div>
      <div style="margin-top: 10px;">
        <label>Turn-by-Turn Directions:</label>
        <div class="directions-list" id="directionsBox">
          <div class="dir-step">Select start & destination, then click "Find Shortest Route".</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">🎨 Map Legend</div>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:#22c55e;"></div> Start Location</div>
        <div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div> Destination</div>
        <div class="legend-item"><div class="legend-line" style="background:#10b981;"></div> Shortest Path</div>
        <div class="legend-item"><div class="legend-line" style="background:#06b6d4;"></div> Fiber MST Backbone</div>
        <div class="legend-item"><div class="legend-line" style="background:#475569; border-top: 1px dashed;"></div> Campus Walkway</div>
      </div>
    </div>
  </div>
</div>

<script>
const campusLocations = {json.dumps(locations_data)};
const campusEdges = {json.dumps(edges_data)};

let initialRouteKeys = {json.dumps(route_edges_keys)};
let initialMstKeys = {json.dumps(mst_edges_keys)};
let isMstActive = false;

// Populate Dropdowns
const startSelect = document.getElementById("startSelect");
const endSelect = document.getElementById("endSelect");

campusLocations.forEach(loc => {{
  const opt1 = document.createElement("option");
  opt1.value = loc.id;
  opt1.text = `${{loc.name}} (${{loc.id}})`;
  startSelect.appendChild(opt1);

  const opt2 = document.createElement("option");
  opt2.value = loc.id;
  opt2.text = `${{loc.name}} (${{loc.id}})`;
  endSelect.appendChild(opt2);
}});

startSelect.value = "GATE";
endSelect.value = "TURING_LAB";

function getEdgeKey(u, v) {{
  return [u, v].sort().join("--");
}}

// Draw SVG Elements
function renderSvg() {{
  const edgesLayer = document.getElementById("edgesLayer");
  const edgeLabelsLayer = document.getElementById("edgeLabelsLayer");
  const nodesLayer = document.getElementById("nodesLayer");

  edgesLayer.innerHTML = "";
  edgeLabelsLayer.innerHTML = "";
  nodesLayer.innerHTML = "";

  const locMap = {{}};
  campusLocations.forEach(l => locMap[l.id] = l);

  // Render Edges
  campusEdges.forEach(edge => {{
    const u = locMap[edge.source];
    const v = locMap[edge.destination];
    const key = getEdgeKey(edge.source, edge.destination);

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", u.x);
    line.setAttribute("y1", u.y);
    line.setAttribute("x2", v.x);
    line.setAttribute("y2", v.y);
    line.setAttribute("id", "edge-" + key);
    line.setAttribute("class", "edge-line");
    edgesLayer.appendChild(line);

    // Label at midpoint
    const midX = (u.x + v.x) / 2;
    const midY = (u.y + v.y) / 2;
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", midX);
    text.setAttribute("y", midY - 4);
    text.setAttribute("class", "edge-weight");
    text.textContent = edge.distance + "m";
    edgeLabelsLayer.appendChild(text);
  }});

  // Render Nodes
  campusLocations.forEach(loc => {{
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "node-group");
    g.setAttribute("id", "node-" + loc.id);
    g.setAttribute("transform", `translate(${{loc.x}}, ${{loc.y}})`);
    g.onclick = () => onNodeClick(loc.id);

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("r", "16");
    circle.setAttribute("class", "node-circle");
    g.appendChild(circle);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("y", "26");
    label.setAttribute("class", "node-label");
    label.textContent = loc.id;
    g.appendChild(label);

    const sub = document.createElementNS("http://www.w3.org/2000/svg", "text");
    sub.setAttribute("y", "37");
    sub.setAttribute("class", "node-sub");
    sub.textContent = loc.name.length > 20 ? loc.name.substring(0, 18) + ".." : loc.name;
    g.appendChild(sub);

    nodesLayer.appendChild(g);
  }});
}}

let clickState = 0;
function onNodeClick(nodeId) {{
  if (clickState === 0) {{
    startSelect.value = nodeId;
    clickState = 1;
  }} else {{
    endSelect.value = nodeId;
    clickState = 0;
    calculateRoute();
  }}
  updateNodeHighlights();
}}

function updateNodeHighlights() {{
  const startId = startSelect.value;
  const endId = endSelect.value;
  campusLocations.forEach(loc => {{
    const el = document.getElementById("node-" + loc.id);
    if (!el) return;
    el.classList.remove("is-start", "is-end");
    if (loc.id === startId) el.classList.add("is-start");
    if (loc.id === endId) el.classList.add("is-end");
  }});
}}

// Dijkstra's Algorithm in JS for Real-Time Interactive Browser Calculation
function runDijkstra(start, end, accessibleOnly) {{
  const dist = {{}};
  const prev = {{}};
  const prevEdge = {{}};
  const unvisited = new Set();

  campusLocations.forEach(l => {{
    dist[l.id] = Infinity;
    prev[l.id] = null;
    unvisited.add(l.id);
  }});

  dist[start] = 0;

  while (unvisited.size > 0) {{
    let u = null;
    let minD = Infinity;
    unvisited.forEach(node => {{
      if (dist[node] < minD) {{
        minD = dist[node];
        u = node;
      }}
    }});

    if (u === null || minD === Infinity || u === end) break;
    unvisited.delete(u);

    // Neighbors
    campusEdges.forEach(edge => {{
      let v = null;
      if (edge.source === u) v = edge.destination;
      else if (edge.destination === u) v = edge.source;

      if (v && unvisited.has(v)) {{
        if (accessibleOnly && !edge.accessible) return; // Skip stairs
        const alt = dist[u] + edge.distance;
        if (alt < dist[v]) {{
          dist[v] = alt;
          prev[v] = u;
          prevEdge[v] = edge;
        }}
      }}
    }});
  }}

  if (dist[end] === Infinity) return null;

  const path = [];
  const edges = [];
  let curr = end;
  while (curr) {{
    path.unshift(curr);
    if (prevEdge[curr]) edges.unshift(prevEdge[curr]);
    curr = prev[curr];
  }}

  return {{ path, edges, totalDistance: dist[end] }};
}}

function calculateRoute() {{
  isMstActive = false;
  const start = startSelect.value;
  const end = endSelect.value;
  const accessibleOnly = document.getElementById("accessibleToggle").checked;

  updateNodeHighlights();
  document.querySelectorAll(".edge-line").forEach(el => {{
    el.classList.remove("active-route", "active-mst");
  }});

  if (start === end) {{
    document.getElementById("resDist").innerText = "0 m";
    document.getElementById("resTime").innerText = "0 min";
    document.getElementById("resCal").innerText = "0 kcal";
    document.getElementById("resHops").innerText = "0";
    document.getElementById("directionsBox").innerHTML = "<div class='dir-step'>Start and Destination are the same building!</div>";
    return;
  }}

  const res = runDijkstra(start, end, accessibleOnly);
  if (!res) {{
    document.getElementById("resDist").innerText = "N/A";
    document.getElementById("directionsBox").innerHTML = "<div class='dir-step' style='border-color:#ef4444;'>No accessible route found connecting these locations!</div>";
    return;
  }}

  res.edges.forEach(e => {{
    const key = getEdgeKey(e.source, e.destination);
    const line = document.getElementById("edge-" + key);
    if (line) line.classList.add("active-route");
  }});

  const walkTime = Math.round(res.totalDistance / 80 * 10) / 10;
  const cals = Math.round(res.totalDistance * 0.045 * 10) / 10;

  document.getElementById("resDist").innerText = res.totalDistance + " m";
  document.getElementById("resTime").innerText = walkTime + " min";
  document.getElementById("resCal").innerText = cals + " kcal";
  document.getElementById("resHops").innerText = res.edges.length;

  const dirBox = document.getElementById("directionsBox");
  dirBox.innerHTML = "";
  const startLoc = campusLocations.find(l => l.id === start);
  const endLoc = campusLocations.find(l => l.id === end);

  dirBox.innerHTML += `<div class="dir-step">Depart from ${{startLoc.name}}.</div>`;
  res.edges.forEach((e, idx) => {{
    const targetId = res.path[idx + 1];
    const targetLoc = campusLocations.find(l => l.id === targetId);
    dirBox.innerHTML += `<div class="dir-step">Step ${{idx + 1}}: Walk ${{e.distance}}m via ${{e.type}} to ${{targetLoc.name}}.</div>`;
  }});
  dirBox.innerHTML += `<div class="dir-step">Arrive at ${{endLoc.name}}!</div>`;
}}

function toggleMST() {{
  isMstActive = !isMstActive;
  document.querySelectorAll(".edge-line").forEach(el => {{
    el.classList.remove("active-route", "active-mst");
  }});

  if (!isMstActive) return;

  // Apply MST keys
  initialMstKeys.forEach(key => {{
    const line = document.getElementById("edge-" + key);
    if (line) line.classList.add("active-mst");
  }});

  document.getElementById("directionsBox").innerHTML = `
    <div class="dir-step" style="border-color:#06b6d4;">
      <strong>Campus Fiber-Optic Backbone (MST)</strong><br>
      Optimally connects all 16 facilities with minimal cabling footprint and zero cyclic loops.
    </div>
  `;
}}

renderSvg();
calculateRoute();
</script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
