"""
algorithms.py - Search Algorithm Implementations

This module implements four search algorithms for timetable CSP:

1. BFS (Breadth-First Search) - Uninformed
   - Explores states level by level using FIFO queue
   - Guarantees finding shallowest solution
   - Space: O(b^d) - stores entire frontier

2. IDDFS (Iterative Deepening DFS) - Uninformed
   - Repeatedly performs depth-limited DFS with increasing limits
   - Combines completeness of BFS with space efficiency of DFS
   - Space: O(bd) - only stores current path

3. A* Search - Informed (uses MCPLB heuristic)
   - Expands states in order of f(n) = g(n) + h(n)
   - g(n) = accumulated penalty cost
   - h(n) = MCPLB (minimum remaining penalty estimate)
   - Guarantees optimal solution with admissible heuristic

4. Greedy Best-First Search - Informed (uses CVR heuristic)
   - Expands states in order of h(n) only (ignores g(n))
   - h(n) = CVR (constraint violation ratio)
   - Fast but not optimal
"""

import heapq
import time
from typing import List, Optional, Tuple
from collections import deque

from timetable import State, Course, Room, Timeslot, Problem, Assignment
from constraints import ConstraintChecker
from heuristics import Heuristics


class SearchMetrics:
    """
    Tracks performance metrics during search.
    
    Attributes:
        nodes_expanded: Number of states expanded (popped from frontier)
        nodes_generated: Number of successor states generated
        max_frontier_size: Maximum size of frontier during search
        time_elapsed: Wall-clock time in seconds
        solution_cost: Total penalty of solution found (None if no solution)
        solution_depth: Depth of solution (number of courses assigned)
    """
    def __init__(self):
        self.nodes_expanded = 0
        self.nodes_generated = 0
        self.max_frontier_size = 0
        self.time_elapsed = 0.0
        self.solution_cost = None
        self.solution_depth = None
        self.start_time = None
    
    def start_timer(self):
        """Start the search timer"""
        self.start_time = time.time()
    
    def stop_timer(self):
        """Stop the timer and record elapsed time"""
        if self.start_time:
            self.time_elapsed = time.time() - self.start_time
    
    def __repr__(self):
        return (f"SearchMetrics(expanded={self.nodes_expanded}, "
                f"generated={self.nodes_generated}, "
                f"max_frontier={self.max_frontier_size}, "
                f"time={self.time_elapsed:.3f}s, "
                f"solution_cost={self.solution_cost}, "
                f"depth={self.solution_depth})")


def generate_successors(state: State, problem: Problem) -> List[State]:
    """
    Generate all valid successor states from the current state.
    
    For each unassigned course, try all feasible (room, timeslot) assignments.
    Each successor has one more course assigned than the parent state.
    
    This implements the "successor function" in search terminology.
    
    Args:
        state: Current state
        problem: Problem instance
    
    Returns:
        List of successor states (children in search tree)
    """
    successors = []
    
    if state.is_complete():
        return successors  # No successors for complete state
    
    # Choose the next unassigned course in deterministic sorted order.
    # Sorting by course id ensures consistent ordering across all algorithms,
    # enabling fair node-count comparisons. This is important for empirical
    # validation: without deterministic ordering, BFS and A* may pick different
    # courses first, making node-count differences hard to attribute to the
    # algorithm rather than random ordering.
    course = min(state.unassigned_courses, key=lambda c: c.id)
    
    # Get all feasible assignments for this course
    feasible = ConstraintChecker.get_feasible_assignments(
        state, course, problem.rooms, problem.timeslots
    )
    
    # Create a successor state for each feasible assignment
    for room, timeslot, penalty in feasible:
        # Copy the parent state
        successor = state.copy()
        
        # Create the assignment
        assignment = Assignment(course, room, timeslot, penalty)
        
        # Update successor state
        successor.assignments.append(assignment)
        successor.unassigned_courses.remove(course)
        successor.g_cost += penalty  # Add penalty to accumulated cost
        successor.parent = state  # Link back to parent for solution reconstruction
        
        successors.append(successor)
    
    return successors


def reconstruct_solution(goal_state: State) -> List[Assignment]:
    """
    Reconstruct the solution path from initial state to goal state.
    
    Follows parent pointers backwards from goal to initial state,
    then reverses to get the forward path.
    
    Args:
        goal_state: The goal state found by search
    
    Returns:
        List of assignments in the solution
    """
    return goal_state.assignments



# BFS (Breadth-First Search)


def bfs(problem: Problem, max_nodes: int = 100000) -> Tuple[Optional[State], SearchMetrics]:
    """
    Breadth-First Search for timetable CSP.
    
    Algorithm:
    1. Initialize frontier as FIFO queue with initial state
    2. Loop:
       a. If frontier empty, return failure
       b. Pop state from front of queue (FIFO order)
       c. If state is complete, return it as solution
       d. Generate successors and add to back of queue
    
    Properties:
    - Complete: Yes (if solution exists)
    - Optimal: For unit costs (finds shallowest solution)
    - Time: O(b^d) where b=branching factor, d=depth
    - Space: O(b^d) - stores entire frontier level
    
    Args:
        problem: Timetable problem instance
        max_nodes: Maximum nodes to expand (safety limit)
    
    Returns:
        Tuple of (solution_state, metrics)
        solution_state is None if no solution found within limit
    """
    metrics = SearchMetrics()
    metrics.start_timer()
    
    # Initialize frontier as FIFO queue (using Python deque)
    frontier = deque()
    initial_state = problem.get_initial_state()
    frontier.append(initial_state)
    
    # Track visited states to avoid cycles (optional for tree search)
    # In CSP, we use this to avoid revisiting the same partial assignment
    visited = set()
    visited.add(hash(initial_state))
    
    print("Starting BFS...")
    print(f"Initial state: {len(problem.courses)} courses to assign")
    print(f"Domain size: {len(problem.rooms)} rooms × {len(problem.timeslots)} timeslots")
    print()
    
    while frontier:
        # Track frontier size
        if len(frontier) > metrics.max_frontier_size:
            metrics.max_frontier_size = len(frontier)
        
        # Safety check: stop if too many nodes expanded
        if metrics.nodes_expanded >= max_nodes:
            print(f"Reached maximum node limit ({max_nodes})")
            metrics.stop_timer()
            return None, metrics
        
        # Pop from front (FIFO - breadth-first)
        current_state = frontier.popleft()
        metrics.nodes_expanded += 1
        
        # Progress update every 500 nodes (reduces console spam for larger problems)
        if metrics.nodes_expanded % 500 == 0:
            print(f"Expanded: {metrics.nodes_expanded}, "
                  f"Frontier: {len(frontier)}, "
                  f"Depth: {current_state.depth()}")
        
        # Goal test
        if current_state.is_complete():
            print(f"\n✓ Solution found!")
            print(f"  Total penalty: {current_state.g_cost}")
            metrics.solution_cost = current_state.g_cost
            metrics.solution_depth = current_state.depth()
            metrics.stop_timer()
            return current_state, metrics
        
        # Generate successors
        successors = generate_successors(current_state, problem)
        metrics.nodes_generated += len(successors)
        
        # Add successors to frontier (back of queue)
        for successor in successors:
            state_hash = hash(successor)
            if state_hash not in visited:
                visited.add(state_hash)
                frontier.append(successor)
    
    # Frontier exhausted without finding solution
    print("BFS: No solution found (frontier exhausted)")
    metrics.stop_timer()
    return None, metrics



# IDDFS (Iterative Deepening Depth-First Search)


def depth_limited_dfs(state: State, problem: Problem, depth_limit: int,
                      metrics: SearchMetrics, path_hashes: set) -> Optional[State]:
    """
    Depth-Limited DFS helper function for IDDFS.

    Uses path_hashes to detect cycles along the current root-to-node path ONLY.
    Sibling branches are NOT blocked — this is correct for a CSP search tree
    where each action assigns a new (different) course, so the same partial
    assignment cannot recur on a single path but CAN legitimately appear in
    sibling branches via different orderings.

    Bug fixed vs original: the original shared `visited` across all branches at
    a given depth level, which incorrectly pruned valid siblings and caused
    IDDFS to miss solutions even on easy problems.

    Args:
        state: Current state
        problem: Problem instance
        depth_limit: Maximum depth to explore
        metrics: Metrics tracker
        path_hashes: Set of state hashes on current root-to-node path (backtracked on return)

    Returns:
        Solution state if found, None otherwise
    """
    metrics.nodes_expanded += 1

    # Internal safety guard (in addition to outer max_nodes check)
    if metrics.nodes_expanded >= 200000:
        return None

    # Goal test
    if state.is_complete():
        return state

    # Depth limit reached
    if state.depth() >= depth_limit:
        return None

    # Generate successors
    successors = generate_successors(state, problem)
    metrics.nodes_generated += len(successors)

    # Recursively search each successor
    for successor in successors:
        state_hash = hash(successor)
        # Only block states already on the current path (true cycle detection)
        # Do NOT block siblings — they represent different valid partial assignments
        if state_hash not in path_hashes:
            path_hashes.add(state_hash)
            result = depth_limited_dfs(successor, problem, depth_limit, metrics, path_hashes)
            path_hashes.discard(state_hash)  # Backtrack: remove from path

            if result is not None:
                return result

    return None


def iddfs(problem: Problem, max_depth: int = 50, max_nodes: int = 100000) -> Tuple[Optional[State], SearchMetrics]:
    """
    Iterative Deepening Depth-First Search for timetable CSP.
    
    Algorithm:
    1. For depth_limit = 0, 1, 2, ..., max_depth:
       a. Perform depth-limited DFS with current limit
       b. If solution found, return it
       c. Otherwise, increment limit and try again
    
    Properties:
    - Complete: Yes (if solution exists within max_depth)
    - Optimal: For unit costs (finds shallowest solution)
    - Time: O(b^d) with small constant overhead (~1.03x for b=30)
    - Space: O(bd) - only stores current path (HUGE advantage over BFS)
    
    Args:
        problem: Timetable problem instance
        max_depth: Maximum depth limit to try
        max_nodes: Maximum nodes to expand (safety limit)
    
    Returns:
        Tuple of (solution_state, metrics)
    """
    metrics = SearchMetrics()
    metrics.start_timer()
    
    initial_state = problem.get_initial_state()
    
    print("Starting IDDFS...")
    print(f"Initial state: {len(problem.courses)} courses to assign")
    print(f"Max depth: {max_depth}")
    print()
    
    # Every complete timetable assigns all n courses, so solutions only exist
    # at depth d = n. Depths 0..n-1 will never contain a goal node.
    # Starting directly at depth n matches D2's claim that m = d = n, avoids
    # n wasted DLS passes, and keeps IDDFS output clean for the demo.
    # If a solution somehow can't be found at depth n, we try n+1, n+2, ...
    # up to max_depth (handles any edge cases in state hashing).
    target_depth = len(problem.courses)
    for depth_limit in range(target_depth, max_depth + 1):
        print(f"Trying depth limit: {depth_limit}")

        # path_hashes tracks only the current root-to-node path for cycle
        # detection. This is O(b*d) space — the key advantage over BFS.
        path_hashes = set()
        path_hashes.add(hash(initial_state))

        result = depth_limited_dfs(initial_state, problem, depth_limit, metrics, path_hashes)

        if result is not None:
            print(f"\n✓ Solution found at depth {result.depth()}!")
            print(f"  Total penalty: {result.g_cost}")
            metrics.solution_cost = result.g_cost
            metrics.solution_depth = result.depth()
            metrics.stop_timer()
            return result, metrics

        # Safety check
        if metrics.nodes_expanded >= max_nodes:
            print(f"Reached maximum node limit ({max_nodes})")
            metrics.stop_timer()
            return None, metrics

        print(f"  No solution at depth {depth_limit}. Expanded: {metrics.nodes_expanded}")
    
    # No solution found within max_depth
    print(f"IDDFS: No solution found within depth {max_depth}")
    metrics.stop_timer()
    return None, metrics
   

# A* Search (with MCPLB heuristic)


def astar(problem: Problem, max_nodes: int = 100000) -> Tuple[Optional[State], SearchMetrics]:
    """
    A* Search for timetable CSP using MCPLB heuristic.
    
    Algorithm:
    1. Initialize frontier as priority queue with initial state
    2. Loop:
       a. If frontier empty, return failure
       b. Pop state with minimum f(n) = g(n) + h(n)
       c. If state is complete, return it as solution
       d. Generate successors, compute f-values, add to priority queue
    
    f(n) = g(n) + h(n) where:
    - g(n) = accumulated penalty cost so far
    - h(n) = MCPLB (estimated minimum remaining penalty)
    
    Properties:
    - Complete: Yes (if solution exists)
    - Optimal: Yes (MCPLB is admissible)
    - Time: O(b^d) worst case, but often much better with good heuristic
    - Space: O(b^d) - stores frontier
    
    Args:
        problem: Timetable problem instance
        max_nodes: Maximum nodes to expand (safety limit)
    
    Returns:
        Tuple of (solution_state, metrics)
    """
    metrics = SearchMetrics()
    metrics.start_timer()
    
    # Initialize frontier as min-heap (priority queue)
    # Each entry is (f_value, counter, state)
    # counter breaks ties in f-value (ensures FIFO for equal f)
    frontier = []
    initial_state = problem.get_initial_state()
    
    # Compute initial f-value
    h_initial = Heuristics.mcplb_optimized(initial_state, problem)
    f_initial = initial_state.g_cost + h_initial
    
    counter = 0  # Tie-breaking counter
    heapq.heappush(frontier, (f_initial, counter, initial_state))
    counter += 1
    
    # Closed list: stores expanded states
    closed = set()
    
    print("Starting A* Search with MCPLB heuristic...")
    print(f"Initial state: {len(problem.courses)} courses to assign")
    print(f"Initial h-value (MCPLB): {h_initial:.2f}")
    print(f"Initial f-value: {f_initial:.2f}")
    print()
    
    while frontier:
        # Track frontier size
        if len(frontier) > metrics.max_frontier_size:
            metrics.max_frontier_size = len(frontier)
        
        # Safety check
        if metrics.nodes_expanded >= max_nodes:
            print(f"Reached maximum node limit ({max_nodes})")
            metrics.stop_timer()
            return None, metrics
        
        # Pop state with minimum f-value
        f_value, _, current_state = heapq.heappop(frontier)
        metrics.nodes_expanded += 1
        
        # Check if already expanded
        state_hash = hash(current_state)
        if state_hash in closed:
            continue
        closed.add(state_hash)
        
        # Progress update every 200 nodes
        if metrics.nodes_expanded % 200 == 0:
            h_current = f_value - current_state.g_cost
            print(f"Expanded: {metrics.nodes_expanded}, "
                  f"Frontier: {len(frontier)}, "
                  f"Depth: {current_state.depth()}, "
                  f"f={f_value:.1f} (g={current_state.g_cost}, h={h_current:.1f})")
        
        # Goal test
        if current_state.is_complete():
            print(f"\n✓ Optimal solution found!")
            print(f"  Total penalty (g): {current_state.g_cost}")
            print(f"  Final f-value: {f_value:.2f}")
            metrics.solution_cost = current_state.g_cost
            metrics.solution_depth = current_state.depth()
            metrics.stop_timer()
            return current_state, metrics
        
        # Generate successors
        successors = generate_successors(current_state, problem)
        metrics.nodes_generated += len(successors)
        
        # Add successors to frontier with f-values
        for successor in successors:
            successor_hash = hash(successor)
            if successor_hash not in closed:
                h_value = Heuristics.mcplb_optimized(successor, problem)
                
                # Check for dead-end state
                if h_value == float('inf'):
                    continue  # Skip this successor
                
                f_value = successor.g_cost + h_value
                heapq.heappush(frontier, (f_value, counter, successor))
                counter += 1
    
    print("A*: No solution found (frontier exhausted)")
    metrics.stop_timer()
    return None, metrics



# Greedy Best-First Search (with CVR heuristic)


def greedy(problem: Problem, max_nodes: int = 100000) -> Tuple[Optional[State], SearchMetrics]:
    """
    Greedy Best-First Search for timetable CSP using CVR heuristic.
    
    Algorithm:
    1. Initialize frontier as priority queue with initial state
    2. Loop:
       a. If frontier empty, return failure
       b. Pop state with minimum h(n) (CVR)
       c. If state is complete and valid, return it
       d. Generate successors, compute h-values, add to priority queue
    
    h(n) = CVR (constraint violation ratio)
    Note: Greedy ignores g(n) cost - only looks at h(n)
    
    Properties:
    - Complete: Yes in finite spaces with cycle detection
    - Optimal: NO - can return suboptimal solutions
    - Time: O(b^m) worst case, often much faster in practice
    - Space: O(b^m) worst case
    
    Args:
        problem: Timetable problem instance
        max_nodes: Maximum nodes to expand (safety limit)
    
    Returns:
        Tuple of (solution_state, metrics)
    """
    metrics = SearchMetrics()
    metrics.start_timer()
    
    # Initialize frontier as min-heap
    frontier = []
    initial_state = problem.get_initial_state()
    
    h_initial = Heuristics.cvr(initial_state, len(problem.courses))
    
    counter = 0
    heapq.heappush(frontier, (h_initial, counter, initial_state))
    counter += 1
    
    # Closed list
    closed = set()
    
    print("Starting Greedy Best-First Search with CVR heuristic...")
    print(f"Initial state: {len(problem.courses)} courses to assign")
    print(f"Initial h-value (CVR): {h_initial:.4f}")
    print()
    
    while frontier:
        # Track frontier size
        if len(frontier) > metrics.max_frontier_size:
            metrics.max_frontier_size = len(frontier)
        
        # Safety check
        if metrics.nodes_expanded >= max_nodes:
            print(f"Reached maximum node limit ({max_nodes})")
            metrics.stop_timer()
            return None, metrics
        
        # Pop state with minimum h-value
        h_value, _, current_state = heapq.heappop(frontier)
        metrics.nodes_expanded += 1
        
        # Check if already expanded
        state_hash = hash(current_state)
        if state_hash in closed:
            continue
        closed.add(state_hash)
        
        # Progress update every 200 nodes
        if metrics.nodes_expanded % 200 == 0:
            print(f"Expanded: {metrics.nodes_expanded}, "
                  f"Frontier: {len(frontier)}, "
                  f"Depth: {current_state.depth()}, "
                  f"h(CVR)={h_value:.4f}, "
                  f"g(penalty)={current_state.g_cost}")
        
        # Goal test
        if current_state.is_complete():
            # Check if solution is valid
            if ConstraintChecker.is_valid_complete_timetable(current_state):
                print(f"\n✓ Solution found!")
                print(f"  Total penalty (g): {current_state.g_cost}")
                print(f"  Final CVR: {h_value:.4f}")
                print(f"  Note: Solution may not be optimal (Greedy is not optimal)")
                metrics.solution_cost = current_state.g_cost
                metrics.solution_depth = current_state.depth()
                metrics.stop_timer()
                return current_state, metrics
            else:
                # Complete but invalid - skip it
                print(f"  Found complete but invalid timetable (CVR={h_value:.4f})")
                continue
        
        # Generate successors
        successors = generate_successors(current_state, problem)
        metrics.nodes_generated += len(successors)
        
        # Add successors to frontier with h-values
        for successor in successors:
            successor_hash = hash(successor)
            if successor_hash not in closed:
                h_value = Heuristics.cvr(successor, len(problem.courses))
                heapq.heappush(frontier, (h_value, counter, successor))
                counter += 1
    
    print("Greedy: No solution found (frontier exhausted)")
    metrics.stop_timer()
    return None, metrics


