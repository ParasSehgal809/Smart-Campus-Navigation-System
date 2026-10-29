// app.js - Client-Side Controller for Smart Campus Navigation Web App

let campusLocations = [];
let campusPaths = [];
let locationMap = {};
let clickSelectionState = 0; // 0 = picking start, 1 = picking end
let currentUser = null;

// DOM Elements
const startSelect = document.getElementById("startSelect");
const endSelect = document.getElementById("endSelect");
const apiStatusPill = document.getElementById("apiStatusPill");
const apiStatusText = document.getElementById("apiStatusText");
const mapTooltip = document.getElementById("mapTooltip");
const svgWrapper = document.getElementById("svgWrapper");

// Helper: Normalize Edge Key
function getEdgeKey(u, v) {
  return [u, v].sort().join("--");
}

// 0. User Authentication State & Handlers
async function checkAuthStatus() {
  const token = localStorage.getItem("campus_token");
  const userSlot = document.getElementById("userHeaderSlot");
  if (!userSlot) return;

  if (!token) {
    userSlot.innerHTML = `
      <a href="login.html" class="btn-signin-link">
        <span>🔑</span>
        <span>Sign In</span>
      </a>
    `;
    return;
  }

  try {
    const res = await fetch("/api/me", {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.authenticated && data.user) {
      currentUser = data.user;
      renderUserHeader(currentUser);
      applyUserPreferences(currentUser);
    } else {
      localStorage.removeItem("campus_token");
      localStorage.removeItem("campus_user");
      userSlot.innerHTML = `
        <a href="login.html" class="btn-signin-link">
          <span>🔑</span>
          <span>Sign In</span>
        </a>
      `;
    }
  } catch (err) {
    const cached = localStorage.getItem("campus_user");
    if (cached) {
      currentUser = JSON.parse(cached);
      renderUserHeader(currentUser);
      applyUserPreferences(currentUser);
    }
  }
}

function renderUserHeader(user) {
  const userSlot = document.getElementById("userHeaderSlot");
  if (!userSlot || !user) return;

  userSlot.innerHTML = `
    <div class="user-profile-badge">
      <div class="user-avatar-circle">${user.avatar || "👤"}</div>
      <div class="user-details-mini">
        <span class="user-name-mini">${user.name}</span>
        <span class="user-role-mini">${user.role_title || user.role}</span>
      </div>
      <button class="btn-signout" onclick="logoutUser()" title="Sign Out">✕</button>
    </div>
  `;
}

function applyUserPreferences(user) {
  if (!user) return;

  if (user.default_start && locationMap[user.default_start] && startSelect) {
    startSelect.value = user.default_start;
  }

  if (user.accessibility_required) {
    const accRadio = document.querySelector('input[name="routePref"][value="accessible"]');
    if (accRadio) {
      accRadio.checked = true;
    }
  }
}

async function logoutUser() {
  const token = localStorage.getItem("campus_token");
  try {
    if (token) {
      await fetch("/api/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token })
      });
    }
  } catch (err) {
    console.warn("Logout error:", err);
  }

  localStorage.removeItem("campus_token");
  localStorage.removeItem("campus_user");
  currentUser = null;
  window.location.reload();
}

// 1. Initialize Application
async function initApp() {
  setupTabs();
  await checkAuthStatus();
  try {
    const healthRes = await fetch("/api/health");
    if (healthRes.ok) {
      apiStatusText.innerText = "API: Online";
      apiStatusPill.style.borderColor = "rgba(16, 185, 129, 0.4)";
    }
  } catch (err) {
    apiStatusText.innerText = "API: Offline / Local";
    apiStatusPill.style.borderColor = "rgba(239, 68, 68, 0.4)";
  }

  try {
    const [locsRes, pathsRes] = await Promise.all([
      fetch("/api/locations"),
      fetch("/api/paths"),
    ]);
    campusLocations = await locsRes.json();
    campusPaths = await pathsRes.json();

    campusLocations.forEach((loc) => {
      locationMap[loc.id] = loc;
    });

    populateDropdowns();
    renderSvgMap();

    // Default route
    startSelect.value = "GATE";
    endSelect.value = "TURING_LAB";
    if (currentUser) {
      applyUserPreferences(currentUser);
    }
    calculateRoute();
  } catch (err) {
    console.error("Initialization error:", err);
  }
}

// 2. Tab Navigation
function setupTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      const pane = document.getElementById(tabId);
      if (pane) pane.classList.add("active");

      if (tabId === "tab-mst") {
        loadMst();
      } else if (tabId === "tab-matrix") {
        loadMatrix();
      }
    });
  });
}

// 3. Populate Dropdowns
function populateDropdowns() {
  startSelect.innerHTML = "";
  endSelect.innerHTML = "";

  campusLocations.forEach((loc) => {
    const opt1 = document.createElement("option");
    opt1.value = loc.id;
    opt1.text = `${loc.name} (${loc.id})`;
    startSelect.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = loc.id;
    opt2.text = `${loc.name} (${loc.id})`;
    endSelect.appendChild(opt2);
  });

  startSelect.addEventListener("change", () => {
    updateNodeHighlights();
    calculateRoute();
  });
  endSelect.addEventListener("change", () => {
    updateNodeHighlights();
    calculateRoute();
  });
}

// 4. Render SVG Map Elements
function renderSvgMap() {
  const edgesLayer = document.getElementById("edgesLayer");
  const edgeLabelsLayer = document.getElementById("edgeLabelsLayer");
  const nodesLayer = document.getElementById("nodesLayer");

  edgesLayer.innerHTML = "";
  edgeLabelsLayer.innerHTML = "";
  nodesLayer.innerHTML = "";

  // Draw Edges
  campusPaths.forEach((edge) => {
    const u = locationMap[edge.source];
    const v = locationMap[edge.destination];
    if (!u || !v) return;

    const key = getEdgeKey(edge.source, edge.destination);

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", u.x);
    line.setAttribute("y1", u.y);
    line.setAttribute("x2", v.x);
    line.setAttribute("y2", v.y);
    line.setAttribute("id", "edge-" + key);
    line.setAttribute("class", "edge-line");
    edgesLayer.appendChild(line);

    // Distance Label
    const midX = (u.x + v.x) / 2;
    const midY = (u.y + v.y) / 2;
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", midX);
    text.setAttribute("y", midY - 4);
    text.setAttribute("class", "edge-weight-text");
    text.textContent = edge.distance_meters + "m";
    edgeLabelsLayer.appendChild(text);
  });

  // Draw Nodes
  campusLocations.forEach((loc) => {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "node-group");
    g.setAttribute("id", "node-" + loc.id);
    g.setAttribute("transform", `translate(${loc.x}, ${loc.y})`);

    // Invisible Hitbox to create a continuous, stable hover surface (eliminates flickering)
    const hitArea = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    hitArea.setAttribute("r", "28");
    hitArea.setAttribute("fill", "transparent");
    hitArea.setAttribute("class", "node-hitbox");
    g.appendChild(hitArea);

    // Circle
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("r", "16");
    circle.setAttribute("class", "node-base-circle");
    g.appendChild(circle);

    // Node ID Label
    const textId = document.createElementNS("http://www.w3.org/2000/svg", "text");
    textId.setAttribute("y", "4");
    textId.setAttribute("class", "node-text-id");
    textId.textContent = loc.id;
    g.appendChild(textId);

    // Node Subtitle
    const textSub = document.createElementNS("http://www.w3.org/2000/svg", "text");
    textSub.setAttribute("y", "30");
    textSub.setAttribute("class", "node-text-name");
    textSub.textContent = loc.name.length > 20 ? loc.name.substring(0, 18) + ".." : loc.name;
    g.appendChild(textSub);

    // Click handler: Set start / destination
    g.addEventListener("click", () => handleNodeClick(loc.id));

    // Hover tooltips (Static positioning, no jitter, hides cleanly on mouseleave)
    g.addEventListener("mouseenter", () => showTooltip(loc, g));
    g.addEventListener("mouseleave", hideTooltip);

    nodesLayer.appendChild(g);
  });

  updateNodeHighlights();
}

function handleNodeClick(nodeId) {
  if (clickSelectionState === 0) {
    startSelect.value = nodeId;
    clickSelectionState = 1;
  } else {
    endSelect.value = nodeId;
    clickSelectionState = 0;
    calculateRoute();
  }
  updateNodeHighlights();
}

function updateNodeHighlights() {
  const start = startSelect.value;
  const end = endSelect.value;
  campusLocations.forEach((loc) => {
    const el = document.getElementById("node-" + loc.id);
    if (!el) return;
    el.classList.remove("is-start", "is-end");
    if (loc.id === start) el.classList.add("is-start");
    if (loc.id === end) el.classList.add("is-end");
  });
}

function clearMapHighlights() {
  document.querySelectorAll(".edge-line").forEach((el) => {
    el.classList.remove("active-route", "active-mst", "active-heat");
    el.style.strokeWidth = "";
  });
}

function showTooltip(loc, gElement) {
  mapTooltip.innerHTML = `
    <div class="tooltip-title">${loc.name} (${loc.id})</div>
    <div class="tooltip-desc">🏷️ ${loc.category}</div>
    <div class="tooltip-desc">${loc.description}</div>
  `;

  const target = gElement || document.getElementById("node-" + loc.id);
  if (target && svgWrapper) {
    const nodeRect = target.getBoundingClientRect();
    const wrapRect = svgWrapper.getBoundingClientRect();

    // Static horizontal center relative to the svgWrapper
    const centerX = nodeRect.left - wrapRect.left + nodeRect.width / 2;

    // Check if node is near the top edge of the map container
    const isNearTop = (nodeRect.top - wrapRect.top) < 90;
    const posY = isNearTop
      ? (nodeRect.bottom - wrapRect.top + 8)
      : (nodeRect.top - wrapRect.top - 8);

    mapTooltip.style.left = `${centerX}px`;
    mapTooltip.style.top = `${posY}px`;
    mapTooltip.style.transform = isNearTop ? "translate(-50%, 0)" : "translate(-50%, -100%)";
  }

  mapTooltip.style.display = "block";
}

function hideTooltip() {
  mapTooltip.style.display = "none";
}

// 5. Calculate Shortest Path (Dijkstra)
async function calculateRoute() {
  const start = startSelect.value;
  const end = endSelect.value;
  const pref = document.querySelector('input[name="routePref"]:checked').value;

  updateNodeHighlights();
  clearMapHighlights();

  if (start === end) {
    document.getElementById("statDistance").innerText = "0 m";
    document.getElementById("statTime").innerText = "0 min";
    document.getElementById("statCalories").innerText = "0 kcal";
    document.getElementById("statHops").innerText = "0";
    document.getElementById("directionsList").innerHTML =
      '<div class="dir-step">Start and Destination are the exact same building!</div>';
    document.getElementById("routeBadges").innerHTML = "";
    return;
  }

  try {
    const res = await fetch(`/api/route?start=${start}&end=${end}&pref=${pref}`);
    const data = await res.json();

    if (!data.found) {
      document.getElementById("statDistance").innerText = "N/A";
      document.getElementById("directionsList").innerHTML =
        '<div class="dir-step" style="border-left-color: #ef4444;">No accessible route found connecting these locations!</div>';
      return;
    }

    // Highlight path on SVG
    data.edge_pairs.forEach(([u, v]) => {
      const line = document.getElementById("edge-" + getEdgeKey(u, v));
      if (line) line.classList.add("active-route");
    });

    // Populate Metrics
    document.getElementById("statDistance").innerText = `${data.total_distance.toFixed(0)} m`;
    document.getElementById("statTime").innerText = `${data.walking_time_minutes.toFixed(1)} min`;
    document.getElementById("statCalories").innerText = `${data.estimated_calories.toFixed(0)} kcal`;
    document.getElementById("statHops").innerText = `${data.path.length - 1}`;

    // Badges
    const badgeContainer = document.getElementById("routeBadges");
    badgeContainer.innerHTML = "";
    if (data.is_fully_accessible) {
      badgeContainer.innerHTML += '<span class="badge badge-success">♿ 100% Wheelchair Accessible</span>';
    } else {
      badgeContainer.innerHTML += '<span class="badge badge-warning">⚠️ Includes Stairs</span>';
    }
    if (data.all_covered) {
      badgeContainer.innerHTML += '<span class="badge badge-success">☔ Fully Covered Pathway</span>';
    }

    // Directions
    const dirList = document.getElementById("directionsList");
    dirList.innerHTML = "";
    data.directions.forEach((d) => {
      const step = document.createElement("div");
      step.className = "dir-step";
      step.textContent = d;
      dirList.appendChild(step);
    });

    // Algorithm Trace
    const traceBox = document.getElementById("dijkstraTraceBox");
    traceBox.innerHTML = "";
    data.algorithm_steps.forEach((step) => {
      const div = document.createElement("div");
      div.textContent = step;
      traceBox.appendChild(div);
    });
  } catch (err) {
    console.error("Route calculation error:", err);
  }
}

// 6. Compare All Routes
async function compareAllRoutes() {
  const start = startSelect.value;
  const end = endSelect.value;
  const container = document.getElementById("compareCardsContainer");
  container.innerHTML = '<div class="placeholder-box">Calculating routes...</div>';

  try {
    const res = await fetch(`/api/compare?start=${start}&end=${end}`);
    const data = await res.json();
    container.innerHTML = "";

    Object.keys(data).forEach((routeName) => {
      const r = data[routeName];
      if (!r.found) return;

      const card = document.createElement("div");
      card.className = "compare-card";
      card.onclick = () => {
        clearMapHighlights();
        r.edge_pairs.forEach(([u, v]) => {
          const line = document.getElementById("edge-" + getEdgeKey(u, v));
          if (line) line.classList.add("active-route");
        });
      };

      const accBadge = r.is_fully_accessible ? "♿ Accessible" : "⚠️ Stairs";
      const covBadge = r.all_covered ? "☔ Covered" : "";

      card.innerHTML = `
        <div class="compare-card-header">
          <span class="compare-card-title">${routeName}</span>
          <span class="badge ${r.is_fully_accessible ? "badge-success" : "badge-warning"}">${accBadge}</span>
        </div>
        <div class="compare-metrics">
          <span>📏 <strong>${r.total_distance.toFixed(0)}m</strong></span>
          <span>⏱️ <strong>${r.walking_time_minutes.toFixed(1)} min</strong></span>
          ${covBadge ? `<span>${covBadge}</span>` : ""}
        </div>
        <div class="compare-path">${r.path.join(" ➔ ")}</div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Comparison error:", err);
  }
}

// 7. Minimum Spanning Tree (MST)
async function loadMst() {
  clearMapHighlights();
  try {
    const res = await fetch("/api/mst");
    const data = await res.json();

    document.getElementById("mstLength").innerText = `${data.kruskal.total_weight.toFixed(0)} m`;
    document.getElementById("fullLength").innerText = `${data.total_graph_edges_length.toFixed(0)} m`;
    document.getElementById("mstSavings").innerText = `${data.cable_savings_meters.toFixed(0)} m (${data.cable_savings_percent}%)`;

    // Highlight MST edges on map
    data.kruskal.edge_pairs.forEach(([u, v]) => {
      const line = document.getElementById("edge-" + getEdgeKey(u, v));
      if (line) line.classList.add("active-mst");
    });

    // Populate links list
    const linksList = document.getElementById("mstLinksList");
    linksList.innerHTML = "";
    data.kruskal.edges.forEach((edge, idx) => {
      const row = document.createElement("div");
      row.className = "link-row";
      row.innerHTML = `
        <span>${idx + 1}. ${locationMap[edge.source].name} ↔ ${locationMap[edge.destination].name}</span>
        <strong style="color:var(--accent-cyan); font-family:var(--font-mono);">${edge.distance.toFixed(0)}m</strong>
      `;
      linksList.appendChild(row);
    });
  } catch (err) {
    console.error("MST load error:", err);
  }
}

function clearMstOverlay() {
  clearMapHighlights();
}

// 8. Batch Simulation & Congestion Heatmap
async function runBatchSimulation() {
  clearMapHighlights();
  const scenario = document.getElementById("batchScenarioSelect").value;
  try {
    const res = await fetch(`/api/batch?scenario=${scenario}`);
    const data = await res.json();

    document.getElementById("batchResultsCard").style.display = "flex";
    document.getElementById("batchTotalTrips").innerText = data.total_trips;
    document.getElementById("batchTotalKm").innerText = `${data.total_distance_km.toFixed(2)} km`;
    document.getElementById("batchAvgDist").innerText = `${data.avg_trip_distance_meters.toFixed(0)} m`;
    document.getElementById("batchExecTime").innerText = `${data.execution_time_ms} ms`;

    document.getElementById("bottleneckPath").innerText = data.most_congested_path;
    document.getElementById("bottleneckCount").innerText = data.most_congested_count;

    // Apply Heatmap to SVG lines
    const maxCount = Math.max(...Object.values(data.edge_traffic), 1);
    Object.entries(data.edge_traffic).forEach(([edgeKeyStr, count]) => {
      const [u, v] = edgeKeyStr.split(" <---> ");
      const line = document.getElementById("edge-" + getEdgeKey(u, v));
      if (line) {
        line.classList.add("active-heat");
        // Thickness proportional to traffic
        const thickness = 2.5 + (count / maxCount) * 8;
        line.style.strokeWidth = `${thickness}px`;
      }
    });

    // Traffic Bars
    const barsContainer = document.getElementById("trafficBarsContainer");
    barsContainer.innerHTML = "";
    const sortedEdges = Object.entries(data.edge_traffic)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    sortedEdges.forEach(([pathName, count]) => {
      const pct = (count / maxCount) * 100;
      barsContainer.innerHTML += `
        <div class="traffic-bar-row">
          <div class="traffic-bar-info">
            <span>${pathName}</span>
            <strong>${count} trips</strong>
          </div>
          <div class="traffic-bar-track">
            <div class="traffic-bar-fill" style="width: ${pct}%;"></div>
          </div>
        </div>
      `;
    });

    // Trips Log
    const tripsTable = document.getElementById("studentTripsTable");
    tripsTable.innerHTML = "";
    data.trips.forEach((t) => {
      tripsTable.innerHTML += `
        <div class="trip-item">
          <span><strong>${t.student_id}</strong> (${t.student_name})</span>
          <span>${t.start_id} ➔ ${t.end_id}</span>
          <strong>${t.distance_meters.toFixed(0)}m</strong>
        </div>
      `;
    });
  } catch (err) {
    console.error("Batch simulation error:", err);
  }
}

// 9. DAA Adjacency Matrix & List
async function loadMatrix() {
  try {
    const res = await fetch("/api/matrix");
    const data = await res.json();

    const topIds = data.node_ids.slice(0, 8);
    const mContainer = document.getElementById("matrixContainer");

    let tableHtml = '<table class="matrix-table"><thead><tr><th>Node</th>';
    topIds.forEach((id) => (tableHtml += `<th>${id}</th>`));
    tableHtml += "</tr></thead><tbody>";

    topIds.forEach((uId, i) => {
      tableHtml += `<tr><th>${uId}</th>`;
      topIds.forEach((vId, j) => {
        const val = data.matrix[i][j];
        if (val === null) {
          tableHtml += '<td><span style="color:#475569;">∞</span></td>';
        } else if (val === 0) {
          tableHtml += "<td>0</td>";
        } else {
          tableHtml += `<td class="has-edge">${val.toFixed(0)}</td>`;
        }
      });
      tableHtml += "</tr>";
    });
    tableHtml += "</tbody></table>";
    mContainer.innerHTML = tableHtml;

    // Adjacency List
    const adjContainer = document.getElementById("adjListContainer");
    adjContainer.innerHTML = "";
    Object.keys(data.adjacency_list).forEach((nodeId) => {
      const nbrs = data.adjacency_list[nodeId]
        .map((nbr) => `${nbr.to} (${nbr.distance.toFixed(0)}m)`)
        .join(" ➔ ");
      adjContainer.innerHTML += `
        <div class="adj-row">
          <strong style="color:var(--accent-blue);">${nodeId}:</strong> ${nbrs}
        </div>
      `;
    });
  } catch (err) {
    console.error("Matrix load error:", err);
  }
}

function resetView() {
  clickSelectionState = 0;
  clearMapHighlights();

  // Clear start/end node markers from map
  campusLocations.forEach((loc) => {
    const el = document.getElementById("node-" + loc.id);
    if (el) el.classList.remove("is-start", "is-end");
  });

  // Reset metrics
  const statDist = document.getElementById("statDistance");
  if (statDist) statDist.innerText = "-- m";
  const statTime = document.getElementById("statTime");
  if (statTime) statTime.innerText = "-- min";
  const statCal = document.getElementById("statCalories");
  if (statCal) statCal.innerText = "-- kcal";
  const statHops = document.getElementById("statHops");
  if (statHops) statHops.innerText = "--";

  // Reset directions and algorithm boxes to clean state
  const dirList = document.getElementById("directionsList");
  if (dirList) {
    dirList.innerHTML = '<div class="dir-step placeholder-box">Map reset. Click any 2 buildings or select from the dropdown to navigate.</div>';
  }

  const badgeContainer = document.getElementById("routeBadges");
  if (badgeContainer) badgeContainer.innerHTML = "";

  const traceBox = document.getElementById("dijkstraTraceBox");
  if (traceBox) traceBox.innerHTML = "";

  hideTooltip();
}

window.addEventListener("DOMContentLoaded", initApp);
