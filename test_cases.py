"""
test_cases.py - Test Problem Generators

Generates three difficulty levels of timetable problems:

1. EASY: Small problem that all algorithms can solve quickly
   - 5-6 courses
   - 5-6 rooms
   - 10-12 timeslots
   - Low constraint density
   - Expected: All algorithms find solution in <1 second

2. MEDIUM: Moderate problem showing algorithm differences
   - 10-12 courses
   - 8-10 rooms
   - 15-20 timeslots
   - Medium constraint density
   - Expected: BFS struggles, IDDFS/A*/Greedy succeed

3. HARD: Large problem exposing scalability limits
   - 15-20 courses
   - 10-12 rooms
   - 20-25 timeslots
   - High constraint density
   - Expected: Only A*/Greedy succeed, BFS/IDDFS timeout
"""

from typing import List
from timetable import Course, Room, Timeslot, Problem


def generate_easy_problem() -> Problem:
    """
    Generate an EASY timetable problem.
    
    Characteristics:
    - 5 courses
    - 5 rooms (all have adequate capacity)
    - 10 timeslots
    - Low constraint conflicts
    
    Returns:
        Problem instance
    """
    # Create courses
    courses = [
        Course(id="CS101", name="Intro to Programming", enrollment=50, 
               instructor="Dr. Smith", preferred_times=[2, 3, 4]),
        Course(id="CS102", name="Data Structures", enrollment=45, 
               instructor="Dr. Jones", preferred_times=[5, 6, 7]),
        Course(id="MATH201", name="Calculus I", enrollment=60, 
               instructor="Prof. Brown", preferred_times=[1, 2, 3]),
        Course(id="PHYS101", name="Physics I", enrollment=55, 
               instructor="Dr. White", preferred_times=[4, 5, 6]),
        Course(id="ENG101", name="English Composition", enrollment=40, 
               instructor="Prof. Green", preferred_times=[7, 8, 9]),
    ]
    
    # Create rooms
    rooms = [
        Room(id="LH101", name="Lecture Hall 101", capacity=100),
        Room(id="LH102", name="Lecture Hall 102", capacity=80),
        Room(id="CR201", name="Classroom 201", capacity=60),
        Room(id="CR202", name="Classroom 202", capacity=50),
        Room(id="LAB301", name="Computer Lab 301", capacity=40),
    ]
    
    # Create timeslots (Monday and Tuesday, 9 AM - 2 PM)
    timeslots = [
        Timeslot(id=0, day="Monday", start_time="08:00", end_time="09:00", is_early=True),
        Timeslot(id=1, day="Monday", start_time="09:00", end_time="10:00"),
        Timeslot(id=2, day="Monday", start_time="10:00", end_time="11:00"),
        Timeslot(id=3, day="Monday", start_time="11:00", end_time="12:00"),
        Timeslot(id=4, day="Monday", start_time="12:00", end_time="13:00"),
        Timeslot(id=5, day="Tuesday", start_time="09:00", end_time="10:00"),
        Timeslot(id=6, day="Tuesday", start_time="10:00", end_time="11:00"),
        Timeslot(id=7, day="Tuesday", start_time="11:00", end_time="12:00"),
        Timeslot(id=8, day="Tuesday", start_time="12:00", end_time="13:00"),
        Timeslot(id=9, day="Tuesday", start_time="13:00", end_time="14:00"),
    ]
    
    return Problem(courses, rooms, timeslots)


def generate_medium_problem() -> Problem:
    """
    Improved MEDIUM problem (12 courses)
    Better reflects algorithm differences
    """

    courses = [
        Course("CS101", "Intro to Programming", 50, "Dr. Smith", [2,3,4]),
        Course("CS102", "Data Structures", 45, "Dr. Smith", [5,6,7]),

        Course("CS201", "Algorithms", 40, "Dr. Jones", [3,4,5]),
        Course("CS202", "Operating Systems", 38, "Dr. Jones", [8,9,10]),

        Course("CS203", "Networks", 35, "Dr. Brown", [10,11,12]),

        Course("MATH201", "Calculus I", 60, "Prof. Brown", [1,2,3]),
        Course("MATH202", "Linear Algebra", 55, "Prof. Davis", [4,5,6]),
        Course("MATH203", "Discrete Math", 50, "Prof. Davis", [6,7,8]),

        Course("PHYS101", "Physics I", 55, "Dr. White", [6,7,8]),
        Course("PHYS102", "Physics II", 50, "Dr. White", [11,12,13]),

        Course("ENG101", "English", 40, "Prof. Green", [7,8,9]),
        Course("HIST101", "History", 65, "Prof. Black", [10,11,12]),
    ]

    rooms = [
        Room("LH101", "Lecture Hall 101", 100),
        Room("LH102", "Lecture Hall 102", 80),
        Room("LH103", "Lecture Hall 103", 70),
        Room("CR201", "Classroom 201", 60),
        Room("CR202", "Classroom 202", 50),
        Room("CR203", "Classroom 203", 45),
        Room("LAB301", "Computer Lab 301", 40),
        Room("LAB302", "Computer Lab 302", 40),
    ]

    timeslots = []
    slot_id = 0

    for day in ["Monday", "Tuesday", "Wednesday"]:
        times = [
            ("08:00", "09:00", True),
            ("09:00", "10:00", False),
            ("10:00", "11:00", False),
            ("11:00", "12:00", False),
            ("12:00", "13:00", False),
            ("13:00", "14:00", False),
        ]

        for start, end, is_early in times:
            timeslots.append(
                Timeslot(slot_id, day, start, end, is_early)
            )
            slot_id += 1

    return Problem(courses, rooms, timeslots)


def generate_hard_problem() -> Problem:
    """
    TRUE L4 timetable problem.

    Characteristics
    ---------------
    Unique course types  (sections per type):
      - 24 lecture-only  courses (duration=1): 11 × 3 sections + 13 × 2 sections = 59 entries
      - 15 two-hour lab  courses (duration=2): 3 sections each                    = 45 entries
      -  5 three-hour lab courses (duration=3): 3 sections each                   = 15 entries
    -----------------------------------------------------------------------
    TOTAL course entries: 59 + 45 + 15 = 119
    -----------------------------------------------------------------------
    Rooms     : 14  (8 lecture halls/classrooms  +  6 LAB rooms)
    Timeslots : 60  (Mon–Fri 8 slots/day [ids 0–39] + Saturday 20 slots [ids 40–59])
    Instructors: 16  (Dr.A … Dr.P)

    Timeslot id layout
    ------------------
      Mon  0– 7  |  Tue  8–15  |  Wed 16–23
      Thu 24–31  |  Fri 32–39  |  Sat 40–59 (labs only)
    """

    # ------------------------------------------------------------------ #
    # Slot-range shorthands for preferred_times lists                      #
    # ------------------------------------------------------------------ #
    MON = list(range(0,  8))   #  0– 7
    TUE = list(range(8,  16))  #  8–15
    WED = list(range(16, 24))  # 16–23
    THU = list(range(24, 32))  # 24–31
    FRI = list(range(32, 40))  # 32–39
    SAT = list(range(40, 60))  # 40–59

    # ================================================================== #
    # COURSES                                                              #
    # ================================================================== #
    courses = [

        # ============================================================== #
        # LECTURE-ONLY  (23 unique courses, 56 section entries)           #
        # 10 courses × 3 sections = 30 entries                           #
        # 13 courses × 2 sections = 26 entries                           #
        # ============================================================== #

        # --- CS101  (3 sections)  Dr.A ---
        Course("CS101-A",  "CS101",  65, "Dr.A", MON[1:5], False, "A", 1),
        Course("CS101-B",  "CS101",  62, "Dr.A", TUE[1:5], False, "B", 1),
        Course("CS101-C",  "CS101",  60, "Dr.A", WED[1:5], False, "C", 1),

        # --- CS102  (3 sections)  Dr.B ---
        Course("CS102-A",  "CS102",  55, "Dr.B", MON[2:6], False, "A", 1),
        Course("CS102-B",  "CS102",  52, "Dr.B", THU[2:6], False, "B", 1),
        Course("CS102-C",  "CS102",  50, "Dr.B", FRI[2:6], False, "C", 1),

        # --- CS201  (3 sections)  Dr.C ---
        Course("CS201-A",  "CS201",  48, "Dr.C", TUE[2:6], False, "A", 1),
        Course("CS201-B",  "CS201",  46, "Dr.C", WED[3:7], False, "B", 1),
        Course("CS201-C",  "CS201",  44, "Dr.C", FRI[3:7], False, "C", 1),

        # --- MATH101 (3 sections)  Dr.E ---
        Course("MATH101-A","MATH101",72, "Dr.E", MON[1:5], False, "A", 1),
        Course("MATH101-B","MATH101",68, "Dr.E", WED[1:5], False, "B", 1),
        Course("MATH101-C","MATH101",65, "Dr.E", FRI[1:5], False, "C", 1),

        # --- MATH201 (3 sections)  Dr.F ---
        Course("MATH201-A","MATH201",62, "Dr.F", TUE[1:5], False, "A", 1),
        Course("MATH201-B","MATH201",58, "Dr.F", THU[1:5], False, "B", 1),
        Course("MATH201-C","MATH201",55, "Dr.F", FRI[4:8], False, "C", 1),

        # --- ENG101  (3 sections)  Dr.H ---
        Course("ENG101-A", "ENG101", 65, "Dr.H", MON[2:6], False, "A", 1),
        Course("ENG101-B", "ENG101", 62, "Dr.H", WED[2:6], False, "B", 1),
        Course("ENG101-C", "ENG101", 60, "Dr.H", FRI[2:6], False, "C", 1),

        # --- HIST101 (3 sections)  Dr.I ---
        Course("HIST101-A","HIST101",68, "Dr.I", TUE[3:7], False, "A", 1),
        Course("HIST101-B","HIST101",64, "Dr.I", THU[3:7], False, "B", 1),
        Course("HIST101-C","HIST101",60, "Dr.I", FRI[3:7], False, "C", 1),

        # --- PHYS101 (3 sections)  Dr.G ---
        Course("PHYS101-A","PHYS101",78, "Dr.G", TUE[2:6], False, "A", 1),
        Course("PHYS101-B","PHYS101",74, "Dr.G", THU[2:6], False, "B", 1),
        Course("PHYS101-C","PHYS101",70, "Dr.G", FRI[2:6], False, "C", 1),

        # --- AI101   (3 sections)  Dr.J ---
        Course("AI101-A",  "AI101",  48, "Dr.J", WED[1:5], False, "A", 1),
        Course("AI101-B",  "AI101",  45, "Dr.J", THU[4:8], False, "B", 1),
        Course("AI101-C",  "AI101",  43, "Dr.J", FRI[1:5], False, "C", 1),

        # --- DS101   (3 sections)  Dr.K ---
        Course("DS101-A",  "DS101",  42, "Dr.K", MON[1:4], False, "A", 1),
        Course("DS101-B",  "DS101",  40, "Dr.K", WED[3:6], False, "B", 1),
        Course("DS101-C",  "DS101",  38, "Dr.K", FRI[5:8], False, "C", 1),

        # 13 courses × 2 sections ----------------------------------------

        # --- CS202  (2 sections)  Dr.D ---
        Course("CS202-A",  "CS202",  42, "Dr.D", WED[3:7], False, "A", 1),
        Course("CS202-B",  "CS202",  40, "Dr.D", THU[3:7], False, "B", 1),

        # --- CS301  (2 sections)  Dr.D ---
        Course("CS301-A",  "CS301",  38, "Dr.D", MON[3:7], False, "A", 1),
        Course("CS301-B",  "CS301",  36, "Dr.D", FRI[3:7], False, "B", 1),

        # --- CS401  (3 sections)  Dr.C  [parent lecture for CSL401 3-hr lab] ---
        Course("CS401-A",  "CS401",  36, "Dr.C", MON[5:8], False, "A", 1),
        Course("CS401-B",  "CS401",  34, "Dr.C", WED[5:8], False, "B", 1),
        Course("CS401-C",  "CS401",  32, "Dr.C", FRI[5:8], False, "C", 1),

        # --- MATH301 (2 sections)  Dr.F ---
        Course("MATH301-A","MATH301",55, "Dr.F", MON[4:8], False, "A", 1),
        Course("MATH301-B","MATH301",52, "Dr.F", WED[4:8], False, "B", 1),

        # --- PHYS201 (2 sections)  Dr.G ---
        Course("PHYS201-A","PHYS201",60, "Dr.G", MON[2:5], False, "A", 1),
        Course("PHYS201-B","PHYS201",58, "Dr.G", WED[5:8], False, "B", 1),

        # --- ML101  (2 sections)  Dr.J ---
        Course("ML101-A",  "ML101",  45, "Dr.J", TUE[4:8], False, "A", 1),
        Course("ML101-B",  "ML101",  42, "Dr.J", THU[4:8], False, "B", 1),

        # --- SE101  (2 sections)  Dr.K ---
        Course("SE101-A",  "SE101",  52, "Dr.K", THU[1:4], False, "A", 1),
        Course("SE101-B",  "SE101",  50, "Dr.K", FRI[4:7], False, "B", 1),

        # --- DBMS101 (2 sections)  Dr.L ---
        Course("DBMS101-A","DBMS101",55, "Dr.L", TUE[1:4], False, "A", 1),
        Course("DBMS101-B","DBMS101",52, "Dr.L", THU[1:4], False, "B", 1),

        # --- NET101  (2 sections)  Dr.L ---
        Course("NET101-A", "NET101", 48, "Dr.L", MON[5:8], False, "A", 1),
        Course("NET101-B", "NET101", 45, "Dr.L", WED[5:8], False, "B", 1),

        # --- OS101   (2 sections)  Dr.N ---
        Course("OS101-A",  "OS101",  50, "Dr.N", TUE[5:8], False, "A", 1),
        Course("OS101-B",  "OS101",  48, "Dr.N", THU[5:8], False, "B", 1),

        # --- CHEM101 (2 sections)  Dr.N ---
        Course("CHEM101-A","CHEM101",55, "Dr.N", MON[1:4], False, "A", 1),
        Course("CHEM101-B","CHEM101",52, "Dr.N", FRI[1:4], False, "B", 1),

        # --- BIO101  (2 sections)  Dr.M ---
        Course("BIO101-A", "BIO101", 60, "Dr.M", TUE[3:7], False, "A", 1),
        Course("BIO101-B", "BIO101", 58, "Dr.M", THU[3:7], False, "B", 1),

        # --- ECO101  (2 sections)  Dr.O ---
        Course("ECO101-A", "ECO101", 65, "Dr.O", MON[2:6], False, "A", 1),
        Course("ECO101-B", "ECO101", 62, "Dr.O", WED[2:6], False, "B", 1),

        # --- STAT101 (2 sections)  Dr.O ---
        Course("STAT101-A","STAT101",58, "Dr.O", TUE[2:6], False, "A", 1),
        Course("STAT101-B","STAT101",55, "Dr.O", FRI[2:6], False, "B", 1),

        # ============================================================== #
        # 2-HOUR LABS  (15 unique × 3 sections = 45 entries)             #
        # ============================================================== #

        # CSL101 — Dr.A
        Course("CSL101-A","CSL101",32,"Dr.A",[1,2,8,9,17,18],    True,"A",2),
        Course("CSL101-B","CSL101",30,"Dr.A",[25,26,33,34],       True,"B",2),
        Course("CSL101-C","CSL101",28,"Dr.A",[41,42,47,48],       True,"C",2),

        # CSL102 — Dr.B
        Course("CSL102-A","CSL102",28,"Dr.B",[3,4,10,11],         True,"A",2),
        Course("CSL102-B","CSL102",26,"Dr.B",[27,28,35,36],       True,"B",2),
        Course("CSL102-C","CSL102",24,"Dr.B",[43,44,50,51],       True,"C",2),

        # CSL201 — Dr.C
        Course("CSL201-A","CSL201",30,"Dr.C",[9,10,17,18],        True,"A",2),
        Course("CSL201-B","CSL201",28,"Dr.C",[33,34,41,42],       True,"B",2),
        Course("CSL201-C","CSL201",26,"Dr.C",[46,47,53,54],       True,"C",2),

        # CSL202 — Dr.D
        Course("CSL202-A","CSL202",26,"Dr.D",[19,20,27,28],       True,"A",2),
        Course("CSL202-B","CSL202",24,"Dr.D",[35,36,40,41],       True,"B",2),
        Course("CSL202-C","CSL202",22,"Dr.D",[48,49,55,56],       True,"C",2),

        # MATHL101 — Dr.E
        Course("MATHL101-A","MATHL101",30,"Dr.E",[5,6,13,14],     True,"A",2),
        Course("MATHL101-B","MATHL101",28,"Dr.E",[29,30,37,38],   True,"B",2),
        Course("MATHL101-C","MATHL101",26,"Dr.E",[42,43,49,50],   True,"C",2),

        # MATHL201 — Dr.F
        Course("MATHL201-A","MATHL201",28,"Dr.F",[23,24,31,32],   True,"A",2),
        Course("MATHL201-B","MATHL201",26,"Dr.F",[39,40,44,45],   True,"B",2),
        Course("MATHL201-C","MATHL201",24,"Dr.F",[51,52,57,58],   True,"C",2),

        # DSL101 — Dr.K
        Course("DSL101-A","DSL101",26,"Dr.K",[10,11,18,19],       True,"A",2),
        Course("DSL101-B","DSL101",24,"Dr.K",[26,27,34,35],       True,"B",2),
        Course("DSL101-C","DSL101",22,"Dr.K",[44,45,52,53],       True,"C",2),

        # AML101 — Dr.J
        Course("AML101-A","AML101",28,"Dr.J",[21,22,29,30],       True,"A",2),
        Course("AML101-B","AML101",26,"Dr.J",[39,40,45,46],       True,"B",2),
        Course("AML101-C","AML101",24,"Dr.J",[50,51,56,57],       True,"C",2),

        # DBL101 — Dr.L
        Course("DBL101-A","DBL101",30,"Dr.L",[6,7,14,15],         True,"A",2),
        Course("DBL101-B","DBL101",28,"Dr.L",[30,31,38,39],       True,"B",2),
        Course("DBL101-C","DBL101",26,"Dr.L",[48,49,56,57],       True,"C",2),

        # SEL101 — Dr.K
        Course("SEL101-A","SEL101",26,"Dr.K",[12,13,20,21],       True,"A",2),
        Course("SEL101-B","SEL101",24,"Dr.K",[28,29,36,37],       True,"B",2),
        Course("SEL101-C","SEL101",22,"Dr.K",[50,51,58,59],       True,"C",2),

        # CSL301 — Dr.B
        Course("CSL301-A","CSL301",28,"Dr.B",[2,3,9,10],          True,"A",2),
        Course("CSL301-B","CSL301",26,"Dr.B",[34,35,43,44],       True,"B",2),
        Course("CSL301-C","CSL301",24,"Dr.B",[52,53,58,59],       True,"C",2),

        # BIOL101L 2-hr component — Dr.M
        Course("BIOL101L-A","BIOL101L",28,"Dr.M",[17,18,25,26],   True,"A",2),
        Course("BIOL101L-B","BIOL101L",26,"Dr.M",[41,42,49,50],   True,"B",2),
        Course("BIOL101L-C","BIOL101L",24,"Dr.M",[54,55,58,59],   True,"C",2),

        # CHEM101L — Dr.N
        Course("CHEM101L-A","CHEM101L",28,"Dr.N",[7,8,15,16],     True,"A",2),
        Course("CHEM101L-B","CHEM101L",26,"Dr.N",[31,32,39,40],   True,"B",2),
        Course("CHEM101L-C","CHEM101L",24,"Dr.N",[45,46,56,57],   True,"C",2),

        # NET101L — Dr.L
        Course("NET101L-A","NET101L",26,"Dr.L",[4,5,12,13],       True,"A",2),
        Course("NET101L-B","NET101L",24,"Dr.L",[28,29,37,38],     True,"B",2),
        Course("NET101L-C","NET101L",22,"Dr.L",[47,48,54,55],     True,"C",2),

        # STATL101 — Dr.O
        Course("STATL101-A","STATL101",26,"Dr.O",[6,7,14,15],     True,"A",2),
        Course("STATL101-B","STATL101",24,"Dr.O",[32,33,40,41],   True,"B",2),
        Course("STATL101-C","STATL101",22,"Dr.O",[50,51,57,58],   True,"C",2),

        # ============================================================== #
        # 3-HOUR LABS  (5 unique × 3 sections = 15 entries)              #
        # ============================================================== #

        # PHYL101 physics 3-hr lab — Dr.G
        Course("PHYL101-A","PHYL101",28,"Dr.G",[1,2,8,9],         True,"A",3),
        Course("PHYL101-B","PHYL101",26,"Dr.G",[33,34,40,41],     True,"B",3),
        Course("PHYL101-C","PHYL101",24,"Dr.G",[44,45,51,52],     True,"C",3),

        # BIOL101 biology 3-hr lab — Dr.M
        Course("BIOL101-A","BIOL101",28,"Dr.M",[16,17,24,25],     True,"A",3),
        Course("BIOL101-B","BIOL101",26,"Dr.M",[40,41,47,48],     True,"B",3),
        Course("BIOL101-C","BIOL101",24,"Dr.M",[53,54,57,58],     True,"C",3),

        # CHEML101 chemistry 3-hr lab — Dr.N
        Course("CHEML101-A","CHEML101",26,"Dr.N",[9,10,18,19],    True,"A",3),
        Course("CHEML101-B","CHEML101",24,"Dr.N",[34,35,43,44],   True,"B",3),
        Course("CHEML101-C","CHEML101",22,"Dr.N",[48,49,55,56],   True,"C",3),

        # CSL401 advanced CS 3-hr lab — Dr.C
        Course("CSL401-A","CSL401",24,"Dr.C",[22,23,30,31],       True,"A",3),
        Course("CSL401-B","CSL401",22,"Dr.C",[37,38,40,41],       True,"B",3),
        Course("CSL401-C","CSL401",20,"Dr.C",[51,52,57,58],       True,"C",3),

        # PHYL201 advanced physics 3-hr lab — Dr.P
        Course("PHYL201-A","PHYL201",26,"Dr.P",[5,6,13,14],       True,"A",3),
        Course("PHYL201-B","PHYL201",24,"Dr.P",[29,30,37,38],     True,"B",3),
        Course("PHYL201-C","PHYL201",22,"Dr.P",[46,47,53,54],     True,"C",3),
    ]

    # ------------------------------------------------------------------ #
    # ROOMS  (8 lecture halls/classrooms  +  6 LAB rooms = 14 total)     #
    # ------------------------------------------------------------------ #
    rooms = [
        Room("LH101", "Large Hall 101",    120),
        Room("LH102", "Large Hall 102",    100),
        Room("LH201", "Lecture Hall 201",   90),
        Room("LH202", "Lecture Hall 202",   80),
        Room("CR301", "Classroom 301",      70),
        Room("CR302", "Classroom 302",      65),
        Room("CR303", "Classroom 303",      60),
        Room("CR304", "Classroom 304",      55),
        Room("LAB401", "Computer Lab 1",    35),
        Room("LAB402", "Computer Lab 2",    35),
        Room("LAB403", "Computer Lab 3",    32),
        Room("LAB404", "Science Lab",       30),
        Room("LAB405", "Electronics Lab",   28),
        Room("LAB406", "Advanced Lab",      28),
    ]

    # ------------------------------------------------------------------ #
    # TIMESLOTS                                                            #
    #   Mon–Fri : ids  0–39  (8 slots/day × 5 days, 08:00–16:00)        #
    #   Saturday: ids 40–59  (20 slots, 08:00–20:00, labs only)          #
    # ------------------------------------------------------------------ #
    timeslots = []
    slot_id = 0

    weekday_times = [
        ("08:00", "09:00", True),
        ("09:00", "10:00", False),
        ("10:00", "11:00", False),
        ("11:00", "12:00", False),
        ("12:00", "13:00", False),
        ("13:00", "14:00", False),
        ("14:00", "15:00", False),
        ("15:00", "16:00", False),
    ]

    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        for start, end, is_early in weekday_times:
            timeslots.append(Timeslot(slot_id, day, start, end, is_early))
            slot_id += 1

    saturday_times = [
        ("08:00", "09:00", True),
        ("09:00", "10:00", False),
        ("10:00", "11:00", False),
        ("11:00", "12:00", False),
        ("12:00", "13:00", False),
        ("13:00", "14:00", False),
        ("14:00", "15:00", False),
        ("15:00", "16:00", False),
        ("16:00", "17:00", False),
        ("17:00", "18:00", False),
        ("18:00", "19:00", False),
        ("19:00", "20:00", False),
        ("20:00", "21:00", False),
        ("21:00", "22:00", False),
        ("22:00", "23:00", False),
        ("23:00", "23:59", False),
        ("05:00", "06:00", False),
        ("05:30", "06:30", False),
        ("06:00", "07:00", False),
        ("06:30", "07:00", False),
    ]
    for start, end, is_early in saturday_times:
        timeslots.append(Timeslot(slot_id, "Saturday", start, end, is_early))
        slot_id += 1

    return Problem(courses, rooms, timeslots)
def print_problem_summary(problem: Problem, difficulty: str):
    """
    Print a summary of the problem characteristics.
    
    Args:
        problem: Problem instance
        difficulty: "EASY", "MEDIUM", or "HARD"
    """
    import math

    print(f"\n{'='*60}")
    print(f"{difficulty} Problem Summary")
    print(f"{'='*60}")
    print(f"Courses: {len(problem.courses)}")
    print(f"Rooms: {len(problem.rooms)}")
    print(f"Timeslots: {len(problem.timeslots)}")
    print(f"Domain size per course: {len(problem.rooms)} × {len(problem.timeslots)} = {len(problem.rooms) * len(problem.timeslots)}")

    # ✅ FIXED overflow-safe calculation
    base = len(problem.rooms) * len(problem.timeslots)
    exp = len(problem.courses)
    log10_val = exp * math.log10(base)

    print(f"Total possible assignments: ~1e{int(log10_val)}")

    # Count instructor conflicts
    instructor_counts = {}
    for course in problem.courses:
        instructor_counts[course.instructor] = instructor_counts.get(course.instructor, 0) + 1
    
    max_conflicts = max(instructor_counts.values())
    print(f"Maximum courses per instructor: {max_conflicts}")
    
    # Count capacity constraints
    room_capacities = sorted([r.capacity for r in problem.rooms])
    course_enrollments = sorted([c.enrollment for c in problem.courses])
    print(f"Room capacities: {room_capacities[0]} - {room_capacities[-1]}")
    print(f"Course enrollments: {course_enrollments[0]} - {course_enrollments[-1]}")
    
    # Estimate branching factor
    avg_feasible = (len(problem.rooms) * len(problem.timeslots)) * 0.6
    print(f"Estimated avg branching factor: ~{avg_feasible:.0f}")
    print(f"{'='*60}\n")