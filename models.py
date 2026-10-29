"""
models.py - Data models for Campus Navigation System
Defines Location, Path, and RouteResult data structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class LocationType(str, Enum):
    ENTRANCE = "Entrance / Gate"
    ADMIN = "Administration"
    LIBRARY = "Library"
    ACADEMIC = "Academic / Classrooms"
    LABORATORY = "Laboratory"
    DINING = "Dining / Cafeteria"
    HOSTEL = "Hostel / Residence"
    SPORTS = "Sports & Fitness"
    HEALTH = "Health Center"
    AUDITORIUM = "Auditorium / Events"


class PathType(str, Enum):
    PAVED = "Paved Walkway"
    COVERED = "Covered Pathway"
    INDOOR = "Indoor Corridor"
    GARDEN = "Garden Trail"
    STAIRWAY = "Stairway"


@dataclass
class CampusLocation:
    """Represents a vertex in the campus graph."""
    id: str
    name: str
    category: LocationType
    x: float  # Map X coordinate (in arbitrary canvas units, e.g. 0-1000)
    y: float  # Map Y coordinate (0-700)
    floor: int = 0  # 0 = Ground, 1 = 1st floor, etc.
    description: str = ""

    def __repr__(self) -> str:
        return f"{self.name} [{self.id}]"


@dataclass
class CampusPath:
    """Represents a weighted edge between two campus locations."""
    source: str
    destination: str
    distance_meters: float
    path_type: PathType = PathType.PAVED
    is_accessible: bool = True  # True if wheelchair / ramp accessible (no stairs)
    is_covered: bool = False    # True if shielded from rain/sun
    scenic_rating: int = 3      # 1 to 5 rating

    @property
    def walking_time_minutes(self) -> float:
        """Estimated walking time assuming average walking speed of 80m/min."""
        speed_m_per_min = 80.0
        if self.path_type == PathType.STAIRWAY:
            speed_m_per_min = 45.0  # Slower on stairs
        elif self.path_type == PathType.GARDEN:
            speed_m_per_min = 70.0
        return round(self.distance_meters / speed_m_per_min, 1)

    def __repr__(self) -> str:
        return f"{self.source} <--> {self.destination} ({self.distance_meters:.0f}m, {self.path_type.value})"


@dataclass
class RouteResult:
    """Result of shortest path calculation."""
    start_id: str
    end_id: str
    found: bool
    path: List[str] = field(default_factory=list)
    total_distance: float = 0.0
    total_time_minutes: float = 0.0
    estimated_calories: float = 0.0
    is_fully_accessible: bool = True
    all_covered: bool = False
    edges: List[CampusPath] = field(default_factory=list)
    directions: List[str] = field(default_factory=list)
    algorithm_steps: List[str] = field(default_factory=list)


@dataclass
class MSTResult:
    """Result of Minimum Spanning Tree calculation."""
    algorithm_name: str
    edges: List[CampusPath] = field(default_factory=list)
    total_weight_meters: float = 0.0
    connected_vertices_count: int = 0
    total_vertices_count: int = 0
    step_trace: List[str] = field(default_factory=list)
