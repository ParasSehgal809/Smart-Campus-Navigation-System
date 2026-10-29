"""
campus_graph.py - Graph representation of campus locations and pathways
Implements both Adjacency List and Adjacency Matrix representations for DAA.
"""

from typing import Dict, List, Optional, Tuple
import math
from models import CampusLocation, CampusPath, LocationType, PathType


class CampusGraph:
    """
    Represents the campus as a weighted, undirected graph G = (V, E).
    Provides both Adjacency List and Adjacency Matrix representations.
    """

    def __init__(self, name: str = "Apex University Campus"):
        self.name = name
        # Vertices: id -> CampusLocation
        self.locations: Dict[str, CampusLocation] = {}
        # Adjacency List: id -> list of incident CampusPath objects
        self.adjacency_list: Dict[str, List[CampusPath]] = {}
        # List of unique undirected edges (each edge stored once with u < v)
        self.all_edges: List[CampusPath] = []

    def add_location(
        self,
        loc_id: str,
        name: str,
        category: LocationType,
        x: float,
        y: float,
        floor: int = 0,
        description: str = "",
    ) -> CampusLocation:
        """Add a vertex to the campus graph."""
        location = CampusLocation(
            id=loc_id,
            name=name,
            category=category,
            x=x,
            y=y,
            floor=floor,
            description=description,
        )
        self.locations[loc_id] = location
        if loc_id not in self.adjacency_list:
            self.adjacency_list[loc_id] = []
        return location

    def add_path(
        self,
        u: str,
        v: str,
        distance_meters: float,
        path_type: PathType = PathType.PAVED,
        is_accessible: bool = True,
        is_covered: bool = False,
        scenic_rating: int = 3,
    ) -> CampusPath:
        """Add a weighted, undirected edge between vertex u and vertex v."""
        if u not in self.locations:
            raise KeyError(f"Location '{u}' does not exist in graph.")
        if v not in self.locations:
            raise KeyError(f"Location '{v}' does not exist in graph.")

        forward_path = CampusPath(
            source=u,
            destination=v,
            distance_meters=distance_meters,
            path_type=path_type,
            is_accessible=is_accessible,
            is_covered=is_covered,
            scenic_rating=scenic_rating,
        )
        reverse_path = CampusPath(
            source=v,
            destination=u,
            distance_meters=distance_meters,
            path_type=path_type,
            is_accessible=is_accessible,
            is_covered=is_covered,
            scenic_rating=scenic_rating,
        )

        self.adjacency_list[u].append(forward_path)
        self.adjacency_list[v].append(reverse_path)

        # Store undirected edge once for algorithms like Kruskal's
        edge_id = tuple(sorted([u, v]))
        if not any(tuple(sorted([e.source, e.destination])) == edge_id for e in self.all_edges):
            self.all_edges.append(forward_path)

        return forward_path

    @property
    def vertex_count(self) -> int:
        return len(self.locations)

    @property
    def edge_count(self) -> int:
        return len(self.all_edges)

    def get_neighbors(self, u: str) -> List[CampusPath]:
        """Return list of outgoing paths from vertex u (Adjacency List lookup)."""
        return self.adjacency_list.get(u, [])

    def get_edge(self, u: str, v: str) -> Optional[CampusPath]:
        """Find the direct edge connecting u and v if it exists."""
        for path in self.adjacency_list.get(u, []):
            if path.destination == v:
                return path
        return None

    def get_adjacency_matrix(self) -> Tuple[List[str], List[List[float]]]:
        """
        Constructs the Adjacency Matrix representation.
        Returns (node_ids, matrix) where matrix[i][j] is the edge distance,
        0.0 if i == j, and math.inf if no direct path exists.
        Complexity: O(V^2) space and time.
        """
        node_ids = sorted(self.locations.keys())
        node_index = {node_id: idx for idx, node_id in enumerate(node_ids)}
        n = len(node_ids)

        matrix = [[math.inf] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 0.0

        for u in self.adjacency_list:
            u_idx = node_index[u]
            for path in self.adjacency_list[u]:
                v_idx = node_index[path.destination]
                matrix[u_idx][v_idx] = path.distance_meters

        return node_ids, matrix

    def format_adjacency_list(self) -> str:
        """Formatted string representation of Adjacency List for DAA analysis."""
        lines = []
        lines.append(f"Campus Adjacency List Representation (|V|={self.vertex_count}, |E|={self.edge_count}):")
        lines.append("=" * 75)
        for loc_id in sorted(self.locations.keys()):
            loc = self.locations[loc_id]
            neighbors = self.adjacency_list.get(loc_id, [])
            neighbor_strs = [
                f"{p.destination} ({p.distance_meters:.0f}m, {p.path_type.value})"
                for p in sorted(neighbors, key=lambda x: x.destination)
            ]
            nbr_text = " -> ".join(neighbor_strs) if neighbor_strs else "None (isolated)"
            lines.append(f"{loc_id:14} [{loc.name[:24]:24}] -> {nbr_text}")
        return "\n".join(lines)

    def format_adjacency_matrix(self, max_display_nodes: int = 10) -> str:
        """Formatted string representation of Adjacency Matrix."""
        node_ids, matrix = self.get_adjacency_matrix()
        display_nodes = node_ids[:max_display_nodes]
        indices = range(len(display_nodes))

        lines = []
        lines.append(f"Campus Adjacency Matrix (Top {len(display_nodes)} of {len(node_ids)} vertices, ∞ = No Direct Edge):")
        lines.append("-" * (12 + len(display_nodes) * 9))
        header = f"{'':12}" + "".join(f"{nid:>9}" for nid in display_nodes)
        lines.append(header)
        lines.append("-" * (12 + len(display_nodes) * 9))

        for i in indices:
            row_vals = []
            for j in indices:
                val = matrix[i][j]
                if math.isinf(val):
                    row_vals.append(f"{'∞':>9}")
                elif val == 0:
                    row_vals.append(f"{'0':>9}")
                else:
                    row_vals.append(f"{val:>9.0f}")
            lines.append(f"{display_nodes[i]:12}" + "".join(row_vals))
        lines.append("-" * (12 + len(display_nodes) * 9))
        return "\n".join(lines)


def build_default_campus() -> CampusGraph:
    """
    Builds a realistic university campus graph with 16 hubs,
    including buildings, classrooms, laboratories, and the library.
    """
    g = CampusGraph("Apex Institute of Technology Campus")

    # 1. Vertices (Locations)
    # Entrance & Admin
    g.add_location("GATE", "Main Campus Gate", LocationType.ENTRANCE, x=100, y=350, description="Main entrance, bus stop & cab pick-up point")
    g.add_location("ADMIN", "Administrative Block", LocationType.ADMIN, x=220, y=350, description="Registrar, Admissions, and Dean's office")
    
    # Library & Central Core
    g.add_location("LIB", "APJ Abdul Kalam Central Library", LocationType.LIBRARY, x=420, y=350, description="3-story library, digital archives & study rooms")
    g.add_location("CAFETERIA", "Campus Cafeteria & Food Court", LocationType.DINING, x=560, y=350, description="Central food court, coffee lounge & student plaza")
    
    # Academic & Classrooms
    g.add_location("LECTURE_A", "Ramanujan Lecture Hall Complex", LocationType.ACADEMIC, x=340, y=200, description="Lecture Halls A101-A110 (First Year Core Subjects)")
    g.add_location("LECTURE_B", "Curie Lecture Hall Complex", LocationType.ACADEMIC, x=520, y=200, description="Lecture Halls B201-B210 (Advanced Electives)")
    
    # Engineering & Labs
    g.add_location("CS_BLOCK", "Computer Science Building", LocationType.ACADEMIC, x=350, y=500, description="Department of CS & Information Science")
    g.add_location("TURING_LAB", "Alan Turing AI & Robotics Lab", LocationType.LABORATORY, x=420, y=580, floor=2, description="High-performance computing, GPU clusters & Robotics")
    g.add_location("ECE_BLOCK", "Electronics & Comm. Building", LocationType.ACADEMIC, x=680, y=230, description="ECE Department & Signal Processing")
    g.add_location("IOT_LAB", "IoT & Embedded Systems Lab", LocationType.LABORATORY, x=780, y=200, floor=1, description="Microcontroller kits, sensors & wireless testing")
    g.add_location("MECH_BLOCK", "Mechanical Engineering Workshop", LocationType.LABORATORY, x=700, y=490, description="CNC machines, 3D printing & automotive workshop")
    
    # Hostels & Health
    g.add_location("HOSTEL_N", "North Boys Hostel (Aryabhata)", LocationType.HOSTEL, x=220, y=100, description="Boys undergraduate residence halls & mess")
    g.add_location("HOSTEL_S", "South Girls Hostel (Kalpana)", LocationType.HOSTEL, x=220, y=600, description="Girls undergraduate residence halls & mess")
    g.add_location("HEALTH_CTR", "Campus Health & Wellness Infirmary", LocationType.HEALTH, x=130, y=480, description="24/7 emergency clinic, doctors & pharmacy")
    
    # Sports & Events
    g.add_location("SPORTS_CTR", "Sports Complex & Gymnasium", LocationType.SPORTS, x=780, y=370, description="Indoor basketball, badminton, gym & running track")
    g.add_location("AUDITORIUM", "Bhabha Memorial Auditorium", LocationType.AUDITORIUM, x=350, y=80, description="1,500-seat university auditorium & event hall")

    # 2. Weighted Edges (Walking Paths)
    # GATE connections
    g.add_path("GATE", "ADMIN", 120, PathType.COVERED, is_accessible=True, is_covered=True, scenic_rating=4)
    g.add_path("GATE", "HEALTH_CTR", 140, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    g.add_path("GATE", "HOSTEL_S", 260, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    
    # ADMIN connections
    g.add_path("ADMIN", "LIB", 200, PathType.COVERED, is_accessible=True, is_covered=True, scenic_rating=4)
    g.add_path("ADMIN", "LECTURE_A", 180, PathType.GARDEN, is_accessible=True, is_covered=False, scenic_rating=5)
    g.add_path("ADMIN", "CS_BLOCK", 190, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    g.add_path("ADMIN", "HEALTH_CTR", 150, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)

    # LIBRARY connections
    g.add_path("LIB", "CAFETERIA", 140, PathType.COVERED, is_accessible=True, is_covered=True, scenic_rating=4)
    g.add_path("LIB", "LECTURE_A", 160, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=4)
    g.add_path("LIB", "LECTURE_B", 170, PathType.GARDEN, is_accessible=True, is_covered=False, scenic_rating=5)
    g.add_path("LIB", "CS_BLOCK", 160, PathType.COVERED, is_accessible=True, is_covered=True, scenic_rating=3)

    # CS_BLOCK & TURING_LAB connections
    # Note: Turing Lab has a fast stair route (40m, not wheelchair accessible) AND a ramp/elevator corridor (75m, fully accessible)
    g.add_path("CS_BLOCK", "TURING_LAB", 40, PathType.STAIRWAY, is_accessible=False, is_covered=True, scenic_rating=2)
    g.add_path("CS_BLOCK", "MECH_BLOCK", 340, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    g.add_path("CS_BLOCK", "CAFETERIA", 220, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    g.add_path("CS_BLOCK", "HOSTEL_S", 160, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    
    # Secondary accessible route to Turing Lab via CS East Wing Ramp
    g.add_path("LIB", "TURING_LAB", 230, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)

    # LECTURE COMPLEXES
    g.add_path("LECTURE_A", "LECTURE_B", 180, PathType.COVERED, is_accessible=True, is_covered=True, scenic_rating=4)
    g.add_path("LECTURE_A", "AUDITORIUM", 120, PathType.GARDEN, is_accessible=True, is_covered=False, scenic_rating=5)
    g.add_path("LECTURE_A", "HOSTEL_N", 160, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    g.add_path("LECTURE_B", "CAFETERIA", 160, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)
    g.add_path("LECTURE_B", "ECE_BLOCK", 160, PathType.COVERED, is_accessible=True, is_covered=True, scenic_rating=4)

    # ECE & IOT LAB
    g.add_path("ECE_BLOCK", "IOT_LAB", 110, PathType.INDOOR, is_accessible=True, is_covered=True, scenic_rating=3)
    g.add_path("ECE_BLOCK", "SPORTS_CTR", 180, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=4)
    g.add_path("ECE_BLOCK", "MECH_BLOCK", 260, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)

    # CAFETERIA connections
    g.add_path("CAFETERIA", "SPORTS_CTR", 220, PathType.GARDEN, is_accessible=True, is_covered=False, scenic_rating=4)
    g.add_path("CAFETERIA", "MECH_BLOCK", 200, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)

    # MECH_BLOCK & SPORTS
    g.add_path("MECH_BLOCK", "SPORTS_CTR", 150, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)

    # AUDITORIUM & HOSTELS
    g.add_path("AUDITORIUM", "HOSTEL_N", 140, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=4)
    g.add_path("HEALTH_CTR", "HOSTEL_S", 150, PathType.PAVED, is_accessible=True, is_covered=False, scenic_rating=3)

    return g
