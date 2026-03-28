"""
timetable.py - Core Data Structures for Timetable CSP

This file defines the fundamental building blocks:
- Course: A class that needs to be scheduled
- Room: A physical location with capacity
- Timeslot: A time period (e.g., Monday 9:00-10:00)
- Assignment: Maps a course to a (room, timeslot) pair
- State: Represents a partial or complete timetable
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Course:
    """
    Represents a university course that needs scheduling.
    
    Attributes:
        id: Unique identifier (e.g., "CS101")
        name: Course name (e.g., "Data Structures")
        enrollment: Number of students enrolled
        instructor: Professor teaching the course
        preferred_times: List of preferred timeslot IDs (for soft constraints)
    """
    id: str
    name: str
    enrollment: int
    instructor: str
    preferred_times: List[int] = None
    
    def __hash__(self):
        """Allow Course to be used in sets and as dict keys"""
        return hash(self.id)
    
    def __eq__(self, other):
        """Two courses are equal if they have the same ID"""
        if not isinstance(other, Course):
            return False
        return self.id == other.id
    
    def __repr__(self):
        return f"Course({self.id}, enroll={self.enrollment})"


@dataclass
class Room:
    """
    Represents a classroom or lecture hall.
    
    Attributes:
        id: Unique identifier (e.g., "LH101")
        name: Room name
        capacity: Maximum number of students
        features: Set of features (e.g., {"projector", "lab_equipment"})
    """
    id: str
    name: str
    capacity: int
    features: Set[str] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Room):
            return False
        return self.id == other.id
    
    def __repr__(self):
        return f"Room({self.id}, cap={self.capacity})"


@dataclass
class Timeslot:
    """
    Represents a time period when classes can be scheduled.
    
    Attributes:
        id: Unique identifier (0, 1, 2, ...)
        day: Day of week (e.g., "Monday")
        start_time: Start time (e.g., "09:00")
        end_time: End time (e.g., "10:00")
        is_early: Boolean indicating if this is an undesirable early slot (penalty)
    """
    id: int
    day: str
    start_time: str
    end_time: str
    is_early: bool = False  # True if before 9:00 AM (soft constraint penalty)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Timeslot):
            return False
        return self.id == other.id
    
    def __repr__(self):
        return f"Timeslot({self.day} {self.start_time}-{self.end_time})"


@dataclass
class Assignment:
    """
    Represents assigning a course to a specific room and timeslot.
    
    Attributes:
        course: The Course object being assigned
        room: The Room object where it's scheduled
        timeslot: The Timeslot object when it's scheduled
        penalty: Soft constraint penalty for this assignment (calculated separately)
    """
    course: Course
    room: Room
    timeslot: Timeslot
    penalty: int = 0
    
    def __repr__(self):
        return f"{self.course.id} → {self.room.id} @ {self.timeslot.day} {self.timeslot.start_time}"


class State:
    """
    Represents a partial or complete timetable assignment.
    
    This is the fundamental unit of search. Each state represents:
    - Which courses have been assigned
    - Their room and timeslot assignments
    - The accumulated penalty cost (g-value)
    - Which courses remain unassigned
    
    Attributes:
        assignments: List of Assignment objects (courses already scheduled)
        unassigned_courses: Set of Course objects not yet scheduled
        g_cost: Accumulated soft constraint penalty (sum of all assignment penalties)
        parent: Previous state (for solution reconstruction)
    """
    
    def __init__(self, 
                 assignments: List[Assignment] = None,
                 unassigned_courses: Set[Course] = None,
                 g_cost: int = 0,
                 parent: 'State' = None):
        """
        Initialize a state.
        
        Args:
            assignments: List of course assignments made so far
            unassigned_courses: Set of courses not yet assigned
            g_cost: Total penalty accumulated so far
            parent: Previous state in search tree
        """
        self.assignments = assignments if assignments else []
        self.unassigned_courses = unassigned_courses if unassigned_courses else set()
        self.g_cost = g_cost  # Actual cost so far (for A*)
        self.parent = parent
        
        # Cache for quick lookups
        self._room_timeslot_map = None  # Dict[(room_id, timeslot_id)] -> Course
        self._instructor_timeslot_map = None  # Dict[(instructor, timeslot_id)] -> Course
        self._course_assignment_map = None  # Dict[course_id] -> Assignment
    
    def depth(self) -> int:
        """Return the depth of this state (number of courses assigned)"""
        return len(self.assignments)
    
    def is_complete(self) -> bool:
        """Check if this is a complete timetable (all courses assigned)"""
        return len(self.unassigned_courses) == 0
    
    def get_room_timeslot_map(self) -> Dict[Tuple[str, int], Course]:
        """
        Build and cache a map of (room_id, timeslot_id) -> Course.
        Used to quickly check if a room is occupied at a given time.
        """
        if self._room_timeslot_map is None:
            self._room_timeslot_map = {}
            for assignment in self.assignments:
                key = (assignment.room.id, assignment.timeslot.id)
                self._room_timeslot_map[key] = assignment.course
        return self._room_timeslot_map
    
    def get_instructor_timeslot_map(self) -> Dict[Tuple[str, int], Course]:
        """
        Build and cache a map of (instructor, timeslot_id) -> Course.
        Used to quickly check if an instructor is busy at a given time.
        """
        if self._instructor_timeslot_map is None:
            self._instructor_timeslot_map = {}
            for assignment in self.assignments:
                key = (assignment.course.instructor, assignment.timeslot.id)
                self._instructor_timeslot_map[key] = assignment.course
        return self._instructor_timeslot_map
    
    def get_course_assignment_map(self) -> Dict[str, Assignment]:
        """
        Build and cache a map of course_id -> Assignment.
        Used to quickly look up where a course is assigned.
        """
        if self._course_assignment_map is None:
            self._course_assignment_map = {}
            for assignment in self.assignments:
                self._course_assignment_map[assignment.course.id] = assignment
        return self._course_assignment_map
    
    def copy(self) -> 'State':
        """
        Create a shallow copy of this state.
        Used when generating successor states (we don't want to modify the original).
        """
        return State(
            assignments=self.assignments.copy(),
            unassigned_courses=self.unassigned_courses.copy(),
            g_cost=self.g_cost,
            parent=self.parent
        )
    
    def __repr__(self):
        return f"State(depth={self.depth()}, g={self.g_cost}, unassigned={len(self.unassigned_courses)})"
    
    def __lt__(self, other):
        """
        Less-than comparison for priority queue.
        States with lower g_cost have higher priority.
        This is used by heapq in A* and Greedy search.
        """
        return self.g_cost < other.g_cost
    
    def __hash__(self):
        """
        Hash function for storing states in sets/dicts.
        Based on which courses are assigned to which (room, timeslot) pairs.
        """
        # Create a frozenset of (course_id, room_id, timeslot_id) tuples
        assignment_tuples = frozenset(
            (a.course.id, a.room.id, a.timeslot.id) 
            for a in self.assignments
        )
        return hash(assignment_tuples)
    
    def __eq__(self, other):
        """
        Two states are equal if they have the same assignments.
        Used for duplicate detection in closed lists.
        """
        if not isinstance(other, State):
            return False
        
        if len(self.assignments) != len(other.assignments):
            return False
        
        # Compare assignment sets
        self_assignments = set(
            (a.course.id, a.room.id, a.timeslot.id) 
            for a in self.assignments
        )
        other_assignments = set(
            (a.course.id, a.room.id, a.timeslot.id) 
            for a in other.assignments
        )
        
        return self_assignments == other_assignments


class Problem:
    """
    Encapsulates the entire timetable CSP problem instance.
    
    This includes:
    - All courses that need scheduling
    - All available rooms
    - All available timeslots
    - Methods to create the initial state
    
    Attributes:
        courses: List of Course objects
        rooms: List of Room objects
        timeslots: List of Timeslot objects
    """
    
    def __init__(self, courses: List[Course], rooms: List[Room], timeslots: List[Timeslot]):
        """
        Initialize a timetable problem.
        
        Args:
            courses: List of all courses to schedule
            rooms: List of all available rooms
            timeslots: List of all available time periods
        """
        self.courses = courses
        self.rooms = rooms
        self.timeslots = timeslots
        
        # Create lookup dictionaries for quick access
        self.course_map = {c.id: c for c in courses}
        self.room_map = {r.id: r for r in rooms}
        self.timeslot_map = {t.id: t for t in timeslots}
    
    def get_initial_state(self) -> State:
        """
        Create the initial state for search.
        This is the empty timetable with no courses assigned.
        
        Returns:
            State with no assignments and all courses unassigned
        """
        return State(
            assignments=[],
            unassigned_courses=set(self.courses),
            g_cost=0,
            parent=None
        )
    
    def __repr__(self):
        return f"Problem(courses={len(self.courses)}, rooms={len(self.rooms)}, timeslots={len(self.timeslots)})"
