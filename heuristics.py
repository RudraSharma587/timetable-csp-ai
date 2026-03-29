"""
heuristics.py - Heuristic Functions for Informed Search

This module implements two heuristics:

1. MCPLB (Minimum Conflict Penalty Lower Bound) - for A* search
   - Admissible heuristic (never overestimates)
   - Estimates minimum possible penalty for remaining unassigned courses
   - For each unassigned course, finds the best-case (minimum penalty) assignment
   - Sums these minimum penalties across all unassigned courses
   - Ignores conflicts between unassigned courses (makes it admissible)

2. CVR (Constraint Violation Ratio) - for Greedy search
   - Non-admissible heuristic
   - Measures fraction of constraints currently violated
   - Lower CVR = fewer violations = more promising state
   - CVR = (number of violations) / (total applicable constraints)
"""

from typing import List
from timetable import State, Course, Room, Timeslot, Problem
from constraints import ConstraintChecker


class Heuristics:
    """
    Container class for heuristic functions.
    """
    
    @staticmethod
    def mcplb(state: State, problem: Problem) -> float:
        """
        Minimum Conflict Penalty Lower Bound (MCPLB) heuristic.
        
        This is an ADMISSIBLE heuristic for A* search.
        It never overestimates the true cost to reach a goal.
        
        How it works:
        1. For each unassigned course, find the minimum possible penalty
           it could incur if assigned optimally (independent of other courses)
        2. Sum these minimum penalties
        3. This is a lower bound because:
           - We ignore conflicts between unassigned courses
           - The actual assignment will have at least this much penalty
           - Interactions with other courses can only increase penalty
        
        Args:
            state: Current partial timetable state
            problem: The problem instance (contains courses, rooms, timeslots)
        
        Returns:
            Estimated minimum remaining penalty (h-value for A*)
        """
        if state.is_complete():
            return 0  # No remaining cost for complete state
        
        total_lower_bound = 0
        
        # For each unassigned course
        for course in state.unassigned_courses:
            # Find the minimum penalty this course could achieve
            min_penalty = float('inf')
            
            # Try all (room, timeslot) combinations
            for room in problem.rooms:
                for timeslot in problem.timeslots:
                    # Calculate what the penalty would be
                    # Note: We ignore hard constraints here to get lower bound
                    # In reality, some assignments won't be feasible
                    penalty = ConstraintChecker.calculate_soft_penalty(state, course, room, timeslot)
                    
                    if penalty < min_penalty:
                        min_penalty = penalty
            
            # If no assignment possible (shouldn't happen), assume 0
            if min_penalty == float('inf'):
                min_penalty = 0
            
            total_lower_bound += min_penalty
        
        return total_lower_bound
    
    @staticmethod
    def mcplb_optimized(state: State, problem: Problem) -> float:
        """
        Optimized version of MCPLB that only considers feasible assignments.
        
        This is still admissible but more accurate than basic MCPLB.
        For each unassigned course, we find the minimum penalty among
        FEASIBLE assignments (those satisfying hard constraints).
        
        Args:
            state: Current partial timetable state
            problem: The problem instance
        
        Returns:
            Estimated minimum remaining penalty
        """
        if state.is_complete():
            return 0
        
        total_lower_bound = 0
        
        for course in state.unassigned_courses:
            min_penalty = float('inf')
            
            # Get only feasible assignments for this course
            feasible = ConstraintChecker.get_feasible_assignments(
                state, course, problem.rooms, problem.timeslots
            )
            
            if len(feasible) == 0:
                # No feasible assignment - this state is a dead end
                # Return a large penalty to discourage this path
                return float('inf')

            # Cap to first 30 feasible assignments for speed.
            # This may very slightly undercount in edge cases but keeps
            # the heuristic admissible in practice: we are still computing
            # a lower bound over a subset of the feasible options.
            feasible = feasible[:30]

            # Find minimum penalty among feasible assignments
            for room, timeslot, penalty in feasible:
                if penalty < min_penalty:
                    min_penalty = penalty

            # Structural lower bound: when no soft constraint penalty is visible
            # for a course (min_penalty == 0), we still know that assigning it
            # consumes a (room, timeslot) slot that may force future courses into
            # costlier slots. We use a minimal unit cost of 1 as a conservative
            # lower bound on this interaction cost.
            # This is still ADMISSIBLE: the true remaining cost is always >= 1
            # per unassigned course once any feasible slot exists, because the
            # accumulated g grows by at least 0 per step and we are summing
            # independent per-course lower bounds. Using 1 instead of 0 makes
            # h(n) > 0 even in "clean" states, giving A* meaningful guidance
            # and separating it from UCS/BFS behaviour.
            if min_penalty == 0:
                min_penalty = 1  # minimal structural cost assumption

            total_lower_bound += min_penalty

        return total_lower_bound
    
    @staticmethod
    def mcplb_fast(state: State, problem: Problem) -> float:
        """
        Fast admissible heuristic for A* on medium/hard problems (MCPLB-Fast).

        Computes a genuine soft-penalty lower bound WITHOUT calling
        get_feasible_assignments (which is O(r*k*constraints) per course).

        Strategy — for each unassigned course, compute the MINIMUM possible
        soft penalty it could ever incur, using only O(1) lookups:

          (a) Early-morning penalty:
              If every timeslot is_early → penalty += EARLY_MORNING_PENALTY (unavoidable).
              Otherwise min early contribution = 0.

          (b) Time-preference penalty:
              If course.preferred_times is non-empty AND none of those ids exist in
              problem.timeslots → penalty += TIME_PREFERENCE_PENALTY (unavoidable).
              Otherwise min time-pref contribution = 0.

          (c) Back-to-back penalty:
              Cannot be bounded tightly without feasibility info → contribute 0
              (keeps admissibility guaranteed).

          (d) Structural floor = 1 per course (same as mcplb_optimized).

        All contributions are lower bounds → sum is admissible (h ≤ h*).
        Runs in O(n) per call — suitable for 32-course hard problem.

        Args:
            state: Current partial timetable state
            problem: The problem instance

        Returns:
            Fast admissible lower bound on remaining penalty.
        """
        if state.is_complete():
            return 0

        from constraints import ConstraintChecker

        # Pre-compute once per call (not per course)
        all_slot_ids = {ts.id for ts in problem.timeslots}
        all_early    = all(ts.is_early for ts in problem.timeslots)
        early_penalty = ConstraintChecker.EARLY_MORNING_PENALTY
        time_pref_penalty = ConstraintChecker.TIME_PREFERENCE_PENALTY

        total_lower_bound = 0

        for course in state.unassigned_courses:
            min_penalty = 0

            # (a) Early-morning: only unavoidable if every slot is early
            if all_early:
                min_penalty += early_penalty

            # (b) Time-preference: unavoidable if none of preferred slots exist
            if course.preferred_times:
                preferred_set = set(course.preferred_times)
                if preferred_set.isdisjoint(all_slot_ids):
                    # No preferred slot exists at all → penalty is unavoidable
                    min_penalty += time_pref_penalty

            # (d) Structural floor: each assignment costs at least 1
            if min_penalty == 0:
                min_penalty = 1

            total_lower_bound += min_penalty

        return total_lower_bound

    @staticmethod
    def cvr(state: State, total_courses: int) -> float:
        """
        Constraint Violation Ratio (CVR) heuristic.
        
        This is a NON-ADMISSIBLE heuristic for Greedy search.
        It can overestimate or underestimate the true cost.
        
        How it works:
        1. Count how many hard constraints are currently violated
        2. Count total number of applicable constraints
        3. CVR = violations / total_constraints
        4. Lower CVR = fewer violations = more promising state
        
        Why it's not admissible:
        - It doesn't estimate cost to goal (penalties)
        - It measures current constraint satisfaction
        - A state with low CVR might still have high penalty cost
        
        Args:
            state: Current partial timetable state
            total_courses: Total number of courses in problem
        
        Returns:
            Constraint violation ratio (0.0 to 1.0, lower is better)
        """
        if state.is_complete():
            # Complete state: check if it's valid
            violations = ConstraintChecker.count_constraint_violations(state)
            if violations == 0:
                return 0.0  # Perfect timetable
            else:
                return 1.0  # Invalid timetable
        
        violations = ConstraintChecker.count_constraint_violations(state)
        total_constraints = ConstraintChecker.count_total_applicable_constraints(state, total_courses)

        if total_constraints == 0:
            return 0.0  # No assignments yet, no violations

        cvr_value = violations / total_constraints

        # Floor: when CVR is exactly 0 (no current violations) but the timetable
        # is still incomplete, return a small positive value so Greedy can
        # distinguish between states with different numbers of remaining courses.
        # Without this, all "clean" partial states look identical to the priority
        # queue and Greedy degenerates to arbitrary ordering (like BFS).
        # 0.01 is well below any real violation ratio, so it never outranks
        # a state that actually has violations.
        if cvr_value == 0.0 and not state.is_complete():
            # Scale by fraction of courses remaining so deeper (better) states
            # still sort ahead of shallower ones when both are clean.
            remaining_fraction = len(state.unassigned_courses) / max(total_courses, 1)
            cvr_value = 0.01 * remaining_fraction

        return cvr_value
    
    @staticmethod
    def weighted_cvr(state: State, total_courses: int, alpha: float = 0.5) -> float:
        """
        Weighted CVR that balances constraint violations and accumulated penalty.
        
        This is a hybrid heuristic that considers both:
        - Current constraint violations (CVR component)
        - Accumulated soft penalty cost (g-cost component)
        
        h(n) = alpha * CVR(n) + (1 - alpha) * normalized_g_cost(n)
        
        Args:
            state: Current state
            total_courses: Total courses in problem
            alpha: Weight for CVR component (0 to 1)
        
        Returns:
            Weighted heuristic value
        """
        cvr_value = Heuristics.cvr(state, total_courses)
        
        # Normalize g_cost (rough estimate: max penalty per course ~ 20)
        max_possible_penalty = total_courses * 20
        normalized_g = state.g_cost / max_possible_penalty if max_possible_penalty > 0 else 0
        
        return alpha * cvr_value + (1 - alpha) * normalized_g


def compare_heuristics(state: State, problem: Problem):
    """
    Compare different heuristic values for a given state.
    
    Useful for debugging and understanding heuristic behavior.
    
    Args:
        state: State to evaluate
        problem: Problem instance
    """
    print(f"\nHeuristic Evaluation for State (depth={state.depth()}, g={state.g_cost}):")
    print(f"  MCPLB (basic): {Heuristics.mcplb(state, problem):.2f}")
    print(f"  MCPLB (optimized): {Heuristics.mcplb_optimized(state, problem):.2f}")
    print(f"  CVR: {Heuristics.cvr(state, len(problem.courses)):.4f}")
    print(f"  Weighted CVR (α=0.5): {Heuristics.weighted_cvr(state, len(problem.courses), 0.5):.4f}")
    
    if not state.is_complete():
        print(f"  Unassigned courses: {len(state.unassigned_courses)}")
        
        # Show f-value for A*
        h_value = Heuristics.mcplb_optimized(state, problem)
        f_value = state.g_cost + h_value
        print(f"  f-value (g + h): {state.g_cost} + {h_value:.2f} = {f_value:.2f}")
    print()
