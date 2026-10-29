# 🎓 Smart Campus Navigation System

A comprehensive Python implementation of a **Smart Campus Navigation & Infrastructure Planning System** designed for **Design and Analysis of Algorithms (DAA)** coursework, demonstrations, and viva examinations.

The system models a realistic university campus as a weighted, undirected graph $G = (V, E)$, helping students find the shortest walking paths between buildings, classrooms, laboratories, and the central library, while also calculating the optimal campus-wide network backbone using Minimum Spanning Tree (MST) algorithms.

---

## 🌟 Key Features

1. **Campus Authentication & Personalized Login Portal**:
   - Dedicated glassmorphism login portal (`login.html`) with role-based profiles (Student, Wheelchair-Accessible, Faculty, Campus Administrator).
   - Session tokens, active user profile pill in the header, and automated user preferences (e.g. setting default building to student's hostel, auto-enabling wheelchair-accessible routing for mobility users).
   - **1-Click Quick Demo Login** buttons for instant demonstration during project evaluation and viva.

2. **Interactive Web Application & Visual Frontend**:
   - Modern dark-mode glassmorphism interface with responsive SVG map.
   - Click-to-route navigation, real-time animated path highlighting, and hover tooltips.
   - Built-in multi-threaded REST API server with **zero external dependencies** (runs on Python standard library `http.server`).

3. **Batch Transit Simulation & Campus Traffic Bottlenecks**:
   - High-throughput batch routing calculating trajectories for entire student cohorts (Morning Class Rush, Lunch Peak, Evening Sports).
   - Dynamic **Congestion Heatmap**: visualizes heavily trafficked corridors and campus bottlenecks with traffic volume bars.
   - Automated reporting with CSV export (`batch_results.csv`).

3. **Campus Graph Representation**:
   - **Vertices ($V = 16$)**: Major campus facilities (Main Gate, Central Library, Turing AI Lab, Computer Science Block, Ramanujan & Curie Lecture Complexes, Cafeteria, Hostels, Sports Arena, Health Infirmary).
   - **Weighted Edges ($E = 29$)**: Walking paths with physical distances (meters), walking times (minutes @ 80 m/min pace), pathway types (paved walkway, covered corridor, garden trail, stairway), and wheelchair accessibility flags.
   - **Dual Graph Structures**: Supports both **Adjacency List** ($O(V + E)$ space) and **Adjacency Matrix** ($O(V^2)$ space) representations with built-in inspectors.

4. **Dijkstra's Shortest Path Algorithm**:
   - Greedy single-source shortest path using a Min-Heap priority queue (`heapq`).
   - Detailed step-by-step edge relaxation trace for viva demonstration.
   - Computes total distance, walking time, estimated calories burned, and turn-by-turn walking instructions.

5. **Multi-Criteria Route Comparison**:
   - **Shortest Route**: Absolute minimum walking distance.
   - **Wheelchair Accessible Route**: Automatically bypasses stairways and steep inclines to provide level or ramped pathways.
   - **All-Weather / Covered Route**: Strongly biases towards covered pathways and indoor corridors for rainy or hot days.
   - **Alternative 2nd-Best Route**: Identifies alternative options bypassing primary bottleneck paths.

6. **Campus Backbone Network Planning (Minimum Spanning Tree)**:
   - Real-world campus context: Designing a campus-wide Fiber-Optic Broadband & Smart CCTV network connecting all facilities with minimum cabling footprint and zero cyclic loops.
   - Implements **both** classic greedy algorithms:
     - **Prim's Algorithm**: Greedy cut-property expansion using a min-heap priority queue ($O((V+E)\log V)$).
     - **Kruskal's Algorithm**: Edge sorting with Disjoint Set Union (DSU) featuring **Path Compression** and **Union by Rank** ($O(E \log E)$).
   - Verifies that both algorithms yield identical optimal cable lengths (achieving **58.6% cable trenching savings** over the full graph).

---

## 📊 DAA Concepts & Algorithm Complexity

| Algorithm / Data Structure | Design Technique | Time Complexity | Space Complexity | Real-World Application in Campus System |
| :--- | :--- | :--- | :--- | :--- |
| **Adjacency List** | Data Structuring | $O(V + E)$ lookup | $O(V + E)$ | Memory-efficient graph storage for sparse campus walkway networks. |
| **Adjacency Matrix** | Matrix Representation | $O(1)$ edge existence | $O(V^2)$ | Fast distance lookup and dense graph representations. |
| **Dijkstra's Algorithm** | Greedy Strategy | $O((V + E) \log V)$ | $O(V)$ | Finding shortest student walking routes between campus buildings. |
| **Prim's Algorithm** | Greedy (Cut Property) | $O((V + E) \log V)$ | $O(V)$ | Growing fiber-optic network outwardly from central administrative server room. |
| **Kruskal's Algorithm** | Greedy (Edge Sorting) | $O(E \log E)$ | $O(V)$ | Laying campus cables by connecting nearest separate campus hubs first. |
| **Disjoint Set Union (DSU)** | Amortized Data Structure | $O(\alpha(V)) \approx O(1)$ | $O(V)$ | Cycle detection during Kruskal's edge addition using Rank & Path Compression. |

---

## 🏗️ Project Architecture

```
smart_campus_navigation/
├── models.py               # Data models: CampusLocation, CampusPath, RouteResult, MSTResult
├── campus_graph.py         # Graph class, Adjacency List & Matrix, Realistic Campus Dataset
├── algorithms/
│   ├── __init__.py         # Package exports
│   ├── dijkstra.py         # Dijkstra's algorithm & multi-criteria route comparison
│   └── mst.py              # Prim's & Kruskal's MST algorithms with DSU
├── visualizer.py           # Interactive SVG/HTML map generator & ASCII terminal renderer
├── main.py                 # Interactive terminal CLI menu
├── demo.py                 # Automated demonstration script (all features in sequence)
├── test_campus.py          # Unit test suite (7 tests verifying correctness & constraints)
├── campus_map.html         # Generated standalone interactive campus map
├── run.sh                  # Shell wrapper script
└── README.md               # Documentation & viva study guide
```

---

## 🚀 How to Run

### 1. Web Application Mode (Frontend + REST API)
Start the multithreaded web server and automatically launch your browser:
```bash
./run.sh web
# or on macOS/Linux: ./run_web.sh
# or on Windows: double-click run_web.bat
```
*Access in browser at:* `http://localhost:8000`

### 2. Batch Navigation & Traffic Simulation
Run high-volume student batch routing and congestion analysis:
```bash
./run.sh batch
# or on macOS/Linux: ./run_batch.sh morning_rush
# or on Windows: double-click run_batch.bat
```
*Exports a complete spreadsheet:* `batch_results.csv`

### 3. Interactive CLI Mode (Terminal)
Launch the interactive command-line interface:
```bash
./run.sh
# or: python3 main.py
```

### 4. Automated Demonstration Suite
Run the end-to-end automated demonstration displaying all algorithm steps and comparison tables:
```bash
./run.sh demo
# or: python3 demo.py
```

### 5. Run Unit Tests
Verify algorithm correctness and edge cases:
```bash
./run.sh test
# or: python3 test_campus.py
```

---

## 📋 Sample Demonstration Output

### Route Comparison: `GATE` ➔ `TURING_LAB`
```
ROUTE COMPARISON: Main Campus Gate ➔ Alan Turing AI & Robotics Lab
================================================================================
Route Profile                Distance     Walk Time    Accessible   Covered   
--------------------------------------------------------------------------------
Shortest Route                  350 m      4.8 min     No ❌ (Stairs) No        
   └── Path: GATE ➔ ADMIN ➔ CS_BLOCK ➔ TURING_LAB
Accessible Route (No Stairs)    550 m      6.9 min     Yes ✅        No        
   └── Path: GATE ➔ ADMIN ➔ LIB ➔ TURING_LAB
Covered / Rainy Day Route       350 m      4.8 min     No ❌ (Stairs) No        
   └── Path: GATE ➔ ADMIN ➔ CS_BLOCK ➔ TURING_LAB
Alternative Path                460 m      6.1 min     No ❌ (Stairs) No        
   └── Path: GATE ➔ HOSTEL_S ➔ CS_BLOCK ➔ TURING_LAB
--------------------------------------------------------------------------------
```

### MST Campus Backbone Network:
```
MINIMUM SPANNING TREE (MST) ALGORITHM COMPARISON
===========================================================================
• Kruskal's Total Cable Weight: 2090.0 meters (|E_mst| = 15)
• Prim's Total Cable Weight   : 2090.0 meters (|E_mst| = 15)
• Optimality Verification     : EXACT MATCH ✅ (Both achieve minimum weight)
---------------------------------------------------------------------------
💡 Efficiency Insight:
• Total graph edges cabling : 5050 meters (all 29 pathways)
• MST optimal cable network : 2090 meters (only 15 links)
• Infrastructure Savings    : 2960 meters (58.6% reduction in trenching cost!)
```

---

## 🎓 DAA Viva & Interview Prep Questions

**Q1: Why is Dijkstra's algorithm called a Greedy Algorithm?**  
*Answer:* At every iteration, it greedily selects the vertex with the current smallest tentative distance from the unvisited set. Because all edge weights are non-negative, this distance is guaranteed to be optimal and will never need to be reconsidered.

**Q2: What happens if a campus graph contains negative edge weights?**  
*Answer:* Dijkstra's algorithm may fail because its greedy assumption (that adding an edge can only increase path distance) no longer holds. Bellman-Ford ($O(VE)$) or Johnson's algorithm must be used instead. In campus navigation, physical distances and walking times are always non-negative ($\ge 0$).

**Q3: Explain the Cut Property in Minimum Spanning Trees.**  
*Answer:* For any cut $(S, V \setminus S)$ in a graph $G$, the minimum-weight edge crossing the cut is guaranteed to be part of an MST. Prim's algorithm repeatedly exploits this by cutting the vertices into the current tree $S$ and non-tree $V \setminus S$, picking the cheapest edge crossing the cut.

**Q4: How does Kruskal's algorithm detect cycles in near-constant time?**  
*Answer:* It uses a Disjoint Set Union (DSU) data structure. If two endpoints $u$ and $v$ belong to the same connected component (`find(u) == find(v)`), adding edge $(u, v)$ would introduce a cycle and is rejected. Path compression and union-by-rank reduce operation time to $O(\alpha(V))$, which is practically $O(1)$.
