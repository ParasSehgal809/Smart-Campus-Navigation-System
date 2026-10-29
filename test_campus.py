"""
test_campus.py - Unit Tests for Smart Campus Navigation System
Validates graph representations, Dijkstra's algorithm, Kruskal's and Prim's MST.
"""

import unittest
import math
from campus_graph import build_default_campus, CampusGraph
from models import LocationType, PathType
from algorithms import dijkstra_shortest_path, find_alternative_routes, prim_mst, kruskal_mst, compare_mst_algorithms
from algorithms.mst import DisjointSetUnion


class TestCampusNavigation(unittest.TestCase):

    def setUp(self):
        self.graph = build_default_campus()

    def test_graph_initialization(self):
        """Test vertices and edges are correctly initialized."""
        self.assertEqual(self.graph.vertex_count, 16)
        self.assertGreater(self.graph.edge_count, 20)
        self.assertIn("GATE", self.graph.locations)
        self.assertIn("LIB", self.graph.locations)
        self.assertIn("TURING_LAB", self.graph.locations)

    def test_adjacency_matrix_symmetry(self):
        """Test adjacency matrix represents undirected graph symmetrically."""
        node_ids, matrix = self.graph.get_adjacency_matrix()
        n = len(node_ids)
        for i in range(n):
            self.assertEqual(matrix[i][i], 0.0)
            for j in range(n):
                self.assertEqual(matrix[i][j], matrix[j][i])

    def test_dijkstra_shortest_path(self):
        """Test Dijkstra finds optimal path between GATE and TURING_LAB."""
        res = dijkstra_shortest_path(self.graph, "GATE", "TURING_LAB")
        self.assertTrue(res.found)
        self.assertEqual(res.path[0], "GATE")
        self.assertEqual(res.path[-1], "TURING_LAB")
        # Direct shortest route uses GATE -> ADMIN -> CS_BLOCK -> TURING_LAB (120 + 190 + 40 = 350m)
        self.assertEqual(res.total_distance, 350.0)
        self.assertEqual(res.path, ["GATE", "ADMIN", "CS_BLOCK", "TURING_LAB"])

    def test_dijkstra_same_start_end(self):
        """Test shortest path from a node to itself."""
        res = dijkstra_shortest_path(self.graph, "LIB", "LIB")
        self.assertTrue(res.found)
        self.assertEqual(res.total_distance, 0.0)
        self.assertEqual(res.path, ["LIB"])

    def test_accessible_route_constraint(self):
        """
        CS_BLOCK -> TURING_LAB has stairs (40m, not accessible).
        Wheelchair accessible search should avoid stairs and take the ramp/accessible detour.
        """
        # Standard route includes stairs
        std_route = dijkstra_shortest_path(self.graph, "GATE", "TURING_LAB")
        self.assertFalse(std_route.is_fully_accessible)

        # Accessible route must bypass stairs
        acc_route = dijkstra_shortest_path(
            self.graph,
            "GATE",
            "TURING_LAB",
            constraint_fn=lambda e: e.is_accessible,
        )
        self.assertTrue(acc_route.found)
        self.assertTrue(acc_route.is_fully_accessible)
        # Accessible route must be longer than the stairs route
        self.assertGreater(acc_route.total_distance, std_route.total_distance)

    def test_mst_equivalence(self):
        """Verify Prim's and Kruskal's algorithms yield the exact same minimum weight."""
        kruskal_res = kruskal_mst(self.graph)
        prim_res = prim_mst(self.graph, start_vertex="ADMIN")

        self.assertEqual(len(kruskal_res.edges), self.graph.vertex_count - 1)
        self.assertEqual(len(prim_res.edges), self.graph.vertex_count - 1)
        self.assertAlmostEqual(kruskal_res.total_weight_meters, prim_res.total_weight_meters, places=2)

    def test_dsu_cycle_detection(self):
        """Test Disjoint Set Union correctly prevents cycles."""
        dsu = DisjointSetUnion(["A", "B", "C"])
        self.assertTrue(dsu.union("A", "B"))
        self.assertTrue(dsu.union("B", "C"))
        # Adding (A, C) should fail because cycle is formed
        self.assertFalse(dsu.union("A", "C"))


if __name__ == "__main__":
    unittest.main()
