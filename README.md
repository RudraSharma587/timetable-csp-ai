# Timetable Generator — CSP as Search (CS F407: AI Assignment D3)

A search-based intelligent agent that solves the university timetable scheduling problem formulated as a Constraint Satisfaction Problem (CSP). Implements four search algorithms (BFS, IDDFS, A\*, Greedy) across three difficulty levels (Easy, Medium, Hard).

---

## Problem Definition

The timetable generation problem is modeled as a state-space search over partial course assignments:

- **State**: A partial assignment mapping scheduled courses to `(room, timeslot)` pairs.
- **Initial State**: Empty assignment — no courses scheduled.
- **Goal Test**: All `n` courses assigned with all hard constraints satisfied.
- **Action**: `Assign(course, room, timeslot)` — schedule one unassigned course.
- **Path Cost** `g(n)`: Accumulated soft-constraint penalty across all assignments.

**State space size** (L4 parameters: 119 courses, 14 rooms, 60 timeslots):  
`|S| ≤ O(b^n)` where theoretical branching factor `b ≤ r × k = 840`.  
After hard-constraint pruning: effective branching factor `b_eff ≈ 300` (domain-dependent).

---

## Features

### Hard Constraints (must be satisfied)
- **Room capacity**: `enrollment(course) ≤ capacity(room)`
- **No room double-booking**: No two courses share the same room at any overlapping timeslot
- **No instructor conflicts**: No instructor assigned to two courses at overlapping times
- **Lab/room compatibility**: Lab courses only in LAB-prefixed rooms; lectures never in LAB rooms
- **Section conflicts**: Different sections of the same course cannot overlap
- **Multi-slot overflow protection**: A course of duration `d` starting at slot `s` requires slots `s` through `s+d−1` to exist

### Soft Constraints (minimize penalty)
| Penalty | Amount |
|---|---|
| Early morning slot (before 09:00) | 10 |
| Back-to-back classes for same instructor | 5 |
| Non-preferred timeslot | 2 |

### Advanced Features
- **Multi-slot labs**: Lab courses with `duration > 1` occupy consecutive timeslots as a single block
- **Course sections**: Multiple sections (A/B/C) of the same course are scheduled independently but cannot overlap
- **Deterministic successor ordering**: Courses expanded in consistent `id`-sorted order for reproducible comparisons

---

## Algorithms Implemented

| Algorithm | Type | Complete | Optimal | Time | Space |
|---|---|---|---|---|---|
| BFS | Uninformed | Yes | No (variable costs) | O(b^d) | O(b^d) |
| IDDFS | Uninformed | Yes | No | O(b^d) | O(b·d) |
| A\* | Informed | Yes\* | Yes (admissible h) | O(b^d) worst / O(b\*^d) typical | O(b^d) |
| Greedy | Informed | Yes\* | No | O(b^d) worst / O(b\*^d) typical | O(b^d) |

\*Complete when a closed list is maintained (implemented). `b* < b_eff < b`.

---

## Heuristics

### MCPLB — Minimum Constraint Penalty Lower Bound (Admissible, used in A\*)
For each unassigned course, computes the minimum possible soft penalty across all feasible `(room, timeslot)` pairs, then sums over all unassigned courses:

```
h₁(n) = Σ_{c ∈ unassigned} min_penalty(c, state)
```

**Admissibility**: Assumes independence between remaining assignments (a relaxation). Removing inter-course constraints cannot increase cost, so `h₁(n) ≤ h*(n)`.

Three variants are implemented:
- `mcplb` — basic (ignores hard constraints, pure lower bound)
- `mcplb_optimized` — considers only feasible assignments; more informed
- `mcplb_fast` — O(n) per call; used for medium/hard problems for scalability

A\* uses `mcplb_optimized` (easy) or `mcplb_fast` (medium/hard) with weighted A\* (`ε = 3.0`) on larger instances.

### CVR — Constraint Violation Ratio (Non-admissible, used in Greedy)

```
h₂(n) = violations(state) / total_applicable_constraints(state)
```

Measures the fraction of currently-violated hard constraints. Lower CVR = more promising state. Non-admissible (does not estimate future penalty cost), but guides Greedy to low-conflict regions quickly.

A scaled floor of `0.01 × (remaining/total)` is applied to distinguish clean partial states by depth, preventing Greedy from degenerating to arbitrary ordering.

---

## Project Structure

```
timetable_csp/
├── main.py            # Entry point: interactive menu + CLI runner
├── timetable.py       # Core data structures: Course, Room, Timeslot, Assignment, State, Problem
├── constraints.py     # Hard & soft constraint checking; feasible assignment generation
├── heuristics.py      # MCPLB (admissible) and CVR (non-admissible) heuristics
├── algorithms.py      # BFS, IDDFS, A*, Greedy implementations + SearchMetrics
├── visualizer.py      # Timetable grid plots and metrics comparison charts
├── test_cases.py      # Easy / Medium / Hard problem generators
└── results/           # Output directory (auto-created)
    ├── *_metrics_comparison.png
    └── *_timetable_<algo>.png
```

---

## Installation

**Requirements**: Python 3.9+

```bash
# Clone the repository
git clone https://github.com/<your-group>/timetable-csp.git
cd timetable-csp

# Install dependencies
pip install matplotlib numpy
```

No additional packages are required. All search algorithms are implemented from scratch.

---

## How to Run

### Interactive Menu (recommended)
```bash
python main.py
```
Follow the on-screen prompts to select difficulty and algorithm(s).

### Command-Line Flags
```bash
# Run all algorithms on the hard problem
python main.py --hard

# Run only A* on the medium problem
python main.py --medium --algo "A*"

# Run all difficulties, all algorithms (non-interactive)
python main.py --easy --medium --hard --no-menu

# Run only informed algorithms on all difficulties
python main.py --no-menu   # then choose from menu
```

### Available CLI Arguments
| Flag | Description |
|---|---|
| `--easy` | Run Easy problem (5 courses) |
| `--medium` | Run Medium problem (12 courses) |
| `--hard` | Run Hard problem (119 courses) |
| `--algo {BFS,IDDFS,A*,Greedy}` | Run a single algorithm |
| `--no-menu` | Skip interactive menu |

---

## Output Explanation

### Console Output
For each algorithm run:
- **Nodes Expanded**: States popped from the frontier and processed
- **Nodes Generated**: Successor states created (proportional to `b_eff × expansions`)
- **Max Frontier Size**: Peak memory usage of the frontier structure
- **Time (s)**: Wall-clock execution time
- **Solution Cost**: Total soft-constraint penalty (`g`-value of goal state); `FAILED` if limit reached

### Saved Files (`./results/`)
| File | Contents |
|---|---|
| `<difficulty>_metrics_comparison.png` | Bar charts: nodes expanded, time, solution quality |
| `<difficulty>_timetable_<algo>.png` | Grid visualization: rooms × timeslots, one per algorithm that found a solution |

### Timetable Grid
- Rows = timeslots (day + time); columns = rooms
- Each colored cell = a course assignment
- Multi-slot labs rendered as tall merged blocks with dashed internal borders
- Title displays total soft penalty

---

## Empirical Observations (Summary)

| Problem | BFS | IDDFS | A\* | Greedy |
|---|---|---|---|---|
| Easy (5 courses) | ✗ FAILED (10k limit) | 6 nodes, 0 penalty | 6 nodes, 0 penalty | 6 nodes, 0 penalty |
| Medium (12 courses) | ✗ FAILED (15k limit) | 13 nodes, 0 penalty | 13 nodes, 0 penalty | 13 nodes, 0 penalty |
| Hard (119 courses) | ✗ FAILED (10k limit) | 120 nodes, penalty=16 | 120 nodes, penalty=16 | 120 nodes, penalty=20 |

**Key findings**:
- BFS demonstrates O(b^d) frontier explosion — infeasible beyond trivial instances
- IDDFS achieves O(b·d) space while matching BFS time complexity; practical up to 119 courses
- A\* (weighted, ε=3.0) expands exactly `n+1` nodes when the heuristic consistently ranks the optimal successor first — best-case O(d) expansion with O(b_eff) generation per step
- Greedy is the fastest clock-time competitor but produces slightly suboptimal solutions (penalty=20 vs 16 on Hard)

---

## Team Members

| Name | ID |
|---|---|
| Rudra Sharma | 2023A70619P |
| Priyanshu Bhatnagar | 2021B3A71140P |

---

## License

For academic use only — CS F407: Artificial Intelligence, BITS Pilani, Second Semester 2025–2026.  
Not licensed for redistribution or commercial use.
