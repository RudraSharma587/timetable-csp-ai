"""
constraints.py - Hard and Soft Constraint Checking

This module handles:
1. Hard Constraints: Must be satisfied for a valid timetable
   - Room capacity >= course enrollment
   - No room double-booking across ALL slots a course occupies (multi-slot support)
   - No instructor conflicts across ALL slots a course occupies
   - Timeslot overflow protection (multi-slot courses must not exceed the slot list)
   - Section conflict: same-named courses in different sections cannot overlap
   - Lab/room compatibility: labs only in LAB rooms, lectures never in LAB rooms

2. Soft Constraints: Preferences that incur penalties when violated
   - Early morning classes (before 9 AM)
   - Back-to-back classes for same instructor
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

        Supports multi-slot courses (e.g. labs spanning 2-3 consecutive slots).
        For a course with duration d, it occupies slots:
            timeslot.id, timeslot.id+1, ..., timeslot.id+d-1

        Hard constraints checked:
        1. Room capacity must accommodate course enrollment
        2. Lab/room compatibility (uses course.is_lab flag, not id suffix)
        3. Room must be free for ALL slots the course occupies
        4. Instructor must be free for ALL slots the course occupies
        5. Section conflict: no two sections of the same course name at overlapping slots

        Note: Timeslot overflow is guarded in get_feasible_assignments before
        this function is called, so it is not rechecked here.

        Args:
            state: Current timetable state
            course: Course to assign
            room: Room to assign to
            timeslot: Starting timeslot

        Returns:
            True if valid, False if any hard constraint is violated
        """

        # --- Constraint 1: Room capacity ---
        if room.capacity < course.enrollment:
            return False

        # --- Constraint 2: Lab / room compatibility ---
        # Uses course.is_lab (not the old course.id.endswith("L") heuristic)
        if course.is_lab and not room.id.startswith("LAB"):
            return False
        if not course.is_lab and room.id.startswith("LAB"):
            return False

        duration = getattr(course, 'duration', 1)

        # --- Build lookup maps once per call ---
        room_timeslot_map = state.get_room_timeslot_map()
        instructor_timeslot_map = state.get_instructor_timeslot_map()

        # --- Constraints 3 & 4: Multi-slot room and instructor availability ---
        for d in range(duration):
            slot_id = timeslot.id + d

            # Room must be free at every occupied slot
            if (room.id, slot_id) in room_timeslot_map:
                return False

            # Instructor must be free at every occupied slot
            if (course.instructor, slot_id) in instructor_timeslot_map:
                return False

        # --- Constraint 5: Section conflict ---
        # Different sections of the same course (same course.name, different id)
        # must NOT be scheduled at overlapping timeslots.
        new_slots = set(range(timeslot.id, timeslot.id + duration))
        for assignment in state.assignments:
            if (assignment.course.name == course.name and
                    assignment.course.id != course.id):
                assigned_dur = getattr(assignment.course, 'duration', 1)
                assigned_slots = set(range(
                    assignment.timeslot.id,
                    assignment.timeslot.id + assigned_dur
                ))
                if assigned_slots & new_slots:  # any overlap => conflict
                    return False

        return True

    @staticmethod
    def calculate_soft_penalty(state: State, course: Course, room: Room, timeslot: Timeslot) -> int:
        """
        Calculate the soft constraint penalty for assigning a course to (room, timeslot).

        Penalties:
        1. Early morning: starting slot is_early
        2. Back-to-back: instructor has a class immediately before start or after end
        3. Time preference: starting slot not in course.preferred_times

        Args:
            state: Current timetable state
            course: Course to assign
            room: Room to assign to
            timeslot: Starting timeslot

        Returns:
            Total soft penalty value
        """
        penalty = 0
        duration = getattr(course, 'duration', 1)

        # Penalty 1: Early morning (based on starting slot)
        if timeslot.is_early:
            penalty += ConstraintChecker.EARLY_MORNING_PENALTY

        # Penalty 2: Back-to-back for instructor
        # Check the slot immediately before start and immediately after last occupied slot
        instructor_timeslot_map = state.get_instructor_timeslot_map()

        if timeslot.id > 0:
            if (course.instructor, timeslot.id - 1) in instructor_timeslot_map:
                penalty += ConstraintChecker.BACK_TO_BACK_PENALTY

        last_slot_after = timeslot.id + duration  # one past the last occupied slot
        if (course.instructor, last_slot_after) in instructor_timeslot_map:
            penalty += ConstraintChecker.BACK_TO_BACK_PENALTY

        # Penalty 3: Time preference (based on starting slot id)
        if course.preferred_times is not None:
            if timeslot.id not in course.preferred_times:
                penalty += ConstraintChecker.TIME_PREFERENCE_PENALTY

        return penalty

    @staticmethod
    def count_constraint_violations(state: State) -> int:
        """
        Count total hard constraint violations in a state.

        Multi-slot courses: a course with duration d occupies slots
        id, id+1, ..., id+d-1, so room/instructor maps cover all those slots.

        Used for CVR heuristic. A valid complete timetable has 0 violations.

        Args:
            state: State to check

        Returns:
            Number of hard constraint violations
        """
        violations = 0
        room_slot_assignments = {}       # (room_id, slot_id) -> [courses]
        instructor_slot_assignments = {} # (instructor, slot_id) -> [courses]

        for assignment in state.assignments:
            duration = getattr(assignment.course, 'duration', 1)

            # Room capacity check (once per assignment)
            if assignment.room.capacity < assignment.course.enrollment:
                violations += 1

            # Lab/room compatibility check
            if assignment.course.is_lab and not assignment.room.id.startswith("LAB"):
                violations += 1
            if not assignment.course.is_lab and assignment.room.id.startswith("LAB"):
                violations += 1

            # Register every occupied slot for double-booking detection
            for d in range(duration):
                slot_id = assignment.timeslot.id + d

                rk = (assignment.room.id, slot_id)
                room_slot_assignments.setdefault(rk, []).append(assignment.course)

                ik = (assignment.course.instructor, slot_id)
                instructor_slot_assignments.setdefault(ik, []).append(assignment.course)

        # Room double-booking violations
        for courses in room_slot_assignments.values():
            if len(courses) > 1:
                violations += len(courses) - 1

        # Instructor conflict violations
        for courses in instructor_slot_assignments.values():
            if len(courses) > 1:
                violations += len(courses) - 1

        return violations

    @staticmethod
    def count_total_applicable_constraints(state: State, total_courses: int) -> int:
        """
        Count total constraints that could be violated (CVR denominator).

        3 constraint types per assigned course:
          - Room capacity, room availability, instructor availability
        Total: 3n  (consistent with D2 analysis)

        Args:
            state: Current state
            total_courses: Total number of courses in the problem

        Returns:
            Total applicable constraints
        """
        num_assigned = len(state.assignments)
        return 3 * num_assigned

    @staticmethod
    def get_feasible_assignments(
        state: State,
        course: Course,
        rooms: List[Room],
        timeslots: List[Timeslot]
    ) -> List[Tuple[Room, Timeslot, int]]:
        """
        Get all valid (room, timeslot) pairs for a course with their soft penalties.

        Applies the timeslot overflow guard here: a course with duration d starting
        at slot s requires slots s..s+d-1 to all exist. If s+d-1 > max_slot_id,
        the assignment is rejected before check_hard_constraints is called.

        Args:
            state: Current state
            course: Course to assign
            rooms: All available rooms
            timeslots: All available timeslots

        Returns:
            List of (room, timeslot, penalty) tuples for valid assignments
        """
        feasible = []
        duration = getattr(course, 'duration', 1)

        if not timeslots:
            return feasible

        max_slot_id = max(t.id for t in timeslots)

        for room in rooms:
            for timeslot in timeslots:
                # Overflow guard: last occupied slot must exist in the timeslot list
                if timeslot.id + duration - 1 > max_slot_id:
                    continue

                if ConstraintChecker.check_hard_constraints(state, course, room, timeslot):
                    penalty = ConstraintChecker.calculate_soft_penalty(
                        state, course, room, timeslot
                    )
                    feasible.append((room, timeslot, penalty))

        return feasible

    @staticmethod
    def is_valid_complete_timetable(state: State) -> bool:
        """
        Check if a complete timetable satisfies all hard constraints.

        Args:
            state: Complete timetable state

        Returns:
            True if valid, False otherwise
        """
        if not state.is_complete():
            return False
        return ConstraintChecker.count_constraint_violations(state) == 0


def print_constraint_summary(state: State, total_courses: int):
    """
    Print a summary of constraint violations and penalties.

    Args:
        state: State to analyze
        total_courses: Total number of courses in the problem
    """
    violations = ConstraintChecker.count_constraint_violations(state)
    total_constraints = ConstraintChecker.count_total_applicable_constraints(
        state, total_courses
    )

    print(f"Constraint Summary for State (depth={state.depth()}):")
    print(f"  Hard Constraint Violations: {violations}")
    print(f"  Total Applicable Constraints: {total_constraints}")
    if total_constraints > 0:
        print(f"  Violation Rate: {violations / total_constraints * 100:.2f}%")
    print(f"  Soft Constraint Penalty (g-cost): {state.g_cost}")
    print()
