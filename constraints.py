"""
constraints.py - Hard and Soft Constraint Checking

This module handles:
1. Hard Constraints: Must be satisfied for a valid timetable
   - Room capacity >= course enrollment
   - No room double-booking (one course per room per timeslot)
   - No instructor conflicts (one course per instructor per timeslot)

2. Soft Constraints: Preferences that incur penalties when violated
   - Early morning classes (before 9 AM)
   - Back-to-back classes for same instructor
   - Room preference violations
   - Non-preferred timeslots
"""

from typing import List, Tuple
from timetable import State, Course, Room, Timeslot, Assignment


class ConstraintChecker:
    """
    Handles all constraint checking for timetable assignments.
    """
    
    # Penalty values for soft constraints
    EARLY_MORNING_PENALTY = 10      # Classes before 9:00 AM
    BACK_TO_BACK_PENALTY = 5        # Instructor has classes in consecutive slots
    ROOM_PREFERENCE_PENALTY = 3     # Course assigned to non-preferred room
    TIME_PREFERENCE_PENALTY = 2     # Course assigned to non-preferred timeslot
    
    @staticmethod
    def check_hard_constraints(state: State, course: Course, room: Room, timeslot: Timeslot) -> bool:
        """
        Check if assigning a course to (room, timeslot) violates any hard constraints.
        
        Hard constraints that MUST be satisfied:
        1. Room capacity must accommodate course enrollment
        2. Room must not be occupied at this timeslot
        3. Instructor must not be teaching another course at this timeslot
        
        Args:
            state: Current timetable state
            course: Course to assign
            room: Room to assign to
            timeslot: Timeslot to assign to
        
        Returns:
            True if assignment is valid (no hard constraints violated)
            False if assignment violates a hard constraint
        """
        
        # Constraint 1: Room capacity check
        if room.capacity < course.enrollment:
            return False  # Room too small for the class
        
        # Constraint 2: Room availability check
        # Is this room already occupied at this timeslot?
        room_timeslot_map = state.get_room_timeslot_map()
        room_key = (room.id, timeslot.id)
        if room_key in room_timeslot_map:
            # Room is already occupied by another course
            return False
        
        # Constraint 3: Instructor availability check
        # Is this instructor already teaching at this timeslot?
        instructor_timeslot_map = state.get_instructor_timeslot_map()
        instructor_key = (course.instructor, timeslot.id)
        if instructor_key in instructor_timeslot_map:
            # Instructor is already teaching another course at this time
            return False
        
        # All hard constraints satisfied
        return True
    
    @staticmethod
    def calculate_soft_penalty(state: State, course: Course, room: Room, timeslot: Timeslot) -> int:
        """
        Calculate the soft constraint penalty for assigning a course to (room, timeslot).
        
        Soft constraints add penalties but don't make assignments invalid:
        1. Early morning penalty (if timeslot is before 9 AM)
        2. Back-to-back penalty (if instructor has another class immediately before/after)
        3. Room preference penalty (if room is not in course's preferred list)
        4. Time preference penalty (if timeslot is not in course's preferred list)
        
        Args:
            state: Current timetable state
            course: Course to assign
            room: Room to assign to
            timeslot: Timeslot to assign to
        
        Returns:
            Total penalty value (sum of all applicable soft constraint penalties)
        """
        penalty = 0
        
        # Penalty 1: Early morning classes
        if timeslot.is_early:
            penalty += ConstraintChecker.EARLY_MORNING_PENALTY
        
        # Penalty 2: Back-to-back classes for instructor
        # Check if instructor has a class immediately before or after this timeslot
        instructor_timeslot_map = state.get_instructor_timeslot_map()
        
        # Check timeslot immediately before (id - 1)
        if timeslot.id > 0:
            prev_key = (course.instructor, timeslot.id - 1)
            if prev_key in instructor_timeslot_map:
                penalty += ConstraintChecker.BACK_TO_BACK_PENALTY
        
        # Check timeslot immediately after (id + 1)
        next_key = (course.instructor, timeslot.id + 1)
        if next_key in instructor_timeslot_map:
            penalty += ConstraintChecker.BACK_TO_BACK_PENALTY
        
        # Penalty 3: Time preference
        # If course has preferred timeslots and this isn't one of them
        if course.preferred_times is not None:
            if timeslot.id not in course.preferred_times:
                penalty += ConstraintChecker.TIME_PREFERENCE_PENALTY
        
        return penalty
    
    @staticmethod
    def count_constraint_violations(state: State) -> int:
        """
        Count the total number of hard constraint violations in a state.
        
        This is used for the CVR (Constraint Violation Ratio) heuristic.
        A valid timetable should have 0 violations.
        
        Args:
            state: State to check
        
        Returns:
            Number of hard constraint violations
        """
        violations = 0
        
        # Build maps for efficient checking
        room_timeslot_assignments = {}  # (room_id, timeslot_id) -> [courses]
        instructor_timeslot_assignments = {}  # (instructor, timeslot_id) -> [courses]
        
        for assignment in state.assignments:
            # Track room usage
            room_key = (assignment.room.id, assignment.timeslot.id)
            if room_key not in room_timeslot_assignments:
                room_timeslot_assignments[room_key] = []
            room_timeslot_assignments[room_key].append(assignment.course)
            
            # Track instructor usage
            instructor_key = (assignment.course.instructor, assignment.timeslot.id)
            if instructor_key not in instructor_timeslot_assignments:
                instructor_timeslot_assignments[instructor_key] = []
            instructor_timeslot_assignments[instructor_key].append(assignment.course)
            
            # Check room capacity
            if assignment.room.capacity < assignment.course.enrollment:
                violations += 1
        
        # Check for room double-booking
        for room_key, courses in room_timeslot_assignments.items():
            if len(courses) > 1:
                violations += len(courses) - 1  # Each extra course is a violation
        
        # Check for instructor conflicts
        for instructor_key, courses in instructor_timeslot_assignments.items():
            if len(courses) > 1:
                violations += len(courses) - 1  # Each extra course is a violation
        
        return violations
    
    @staticmethod
    def count_total_applicable_constraints(state: State, total_courses: int) -> int:
        """
        Count the total number of constraints that could be violated.
        
        This is the denominator for CVR (Constraint Violation Ratio).
        
        For n assigned courses:
        - Room capacity: n constraints
        - Room availability: n constraints
        - Instructor availability: n constraints
        
        Total: 3n constraints
        
        Args:
            state: Current state
            total_courses: Total number of courses in the problem
        
        Returns:
            Total number of applicable constraints
        """
        num_assigned = len(state.assignments)
        return 3 * num_assigned  # 3 types of constraints per assignment
    
    @staticmethod
    def get_feasible_assignments(state: State, course: Course, 
                                 rooms: List[Room], timeslots: List[Timeslot]) -> List[Tuple[Room, Timeslot, int]]:
        """
        Get all valid (room, timeslot) pairs for a course, along with their penalties.
        
        This is used during successor generation to find all possible next states.
        Only returns assignments that satisfy hard constraints.
        
        Args:
            state: Current state
            course: Course to assign
            rooms: List of available rooms
            timeslots: List of available timeslots
        
        Returns:
            List of (room, timeslot, penalty) tuples for valid assignments
        """
        feasible = []
        
        for room in rooms:
            for timeslot in timeslots:
                # Check hard constraints
                if ConstraintChecker.check_hard_constraints(state, course, room, timeslot):
                    # Calculate soft penalty
                    penalty = ConstraintChecker.calculate_soft_penalty(state, course, room, timeslot)
                    feasible.append((room, timeslot, penalty))
        
        return feasible
    
    @staticmethod
    def is_valid_complete_timetable(state: State) -> bool:
        """
        Check if a complete timetable satisfies all hard constraints.
        
        Used for final validation of solutions.
        
        Args:
            state: Complete timetable state
        
        Returns:
            True if all hard constraints are satisfied, False otherwise
        """
        if not state.is_complete():
            return False
        
        return ConstraintChecker.count_constraint_violations(state) == 0


def print_constraint_summary(state: State, total_courses: int):
    """
    Print a summary of constraint violations and penalties.
    
    Useful for debugging and understanding solution quality.
    
    Args:
        state: State to analyze
        total_courses: Total number of courses in the problem
    """
    violations = ConstraintChecker.count_constraint_violations(state)
    total_constraints = ConstraintChecker.count_total_applicable_constraints(state, total_courses)
    
    print(f"Constraint Summary for State (depth={state.depth()}):")
    print(f"  Hard Constraint Violations: {violations}")
    print(f"  Total Applicable Constraints: {total_constraints}")
    if total_constraints > 0:
        print(f"  Violation Rate: {violations / total_constraints * 100:.2f}%")
    print(f"  Soft Constraint Penalty (g-cost): {state.g_cost}")
    print()
