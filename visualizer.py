"""
visualizer.py - Search Process Visualization

Provides visualization and reporting for:
1. Search metrics comparison (tables and charts)
2. Solution quality visualization (timetable grids)
3. Performance analysis
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict, Optional
from timetable import State, Problem
from algorithms import SearchMetrics


def print_timetable(state: State, problem: Problem):
    """
    Print the timetable in a readable grid format.
    
    Shows which course is assigned to which room at each timeslot.
    
    Args:
        state: Complete timetable state
        problem: Problem instance
    """
    if not state.is_complete():
        print("Cannot print incomplete timetable")
        return
    
    print("\n" + "="*80)
    print("TIMETABLE SOLUTION")
    print("="*80)
    
    # Build a map: (room_id, timeslot_id) -> course_id
    # For multi-slot courses, register every occupied slot
    schedule = {}
    for assignment in state.assignments:
        duration = getattr(assignment.course, 'duration', 1)
        for d in range(duration):
            slot_id = assignment.timeslot.id + d
            key = (assignment.room.id, slot_id)
            label = assignment.course.id
            if d > 0:
                label = f"  └{assignment.course.id}"  # continuation marker
            schedule[key] = label
    
    # Group timeslots by day
    days = {}
    for ts in problem.timeslots:
        if ts.day not in days:
            days[ts.day] = []
        days[ts.day].append(ts)
    
    # Print schedule for each day
    for day, timeslots in sorted(days.items()):
        print(f"\n{day}:")
        print("-" * 80)
        
        # Header row with room names
        rooms_sorted = sorted(problem.rooms, key=lambda r: r.id)
        header = "Time".ljust(15)
        for room in rooms_sorted:
            header += f"{room.id}".ljust(12)
        print(header)
        print("-" * 80)
        
        # Each timeslot row
        for ts in sorted(timeslots, key=lambda t: t.id):
            row = f"{ts.start_time}-{ts.end_time}".ljust(15)
            for room in rooms_sorted:
                key = (room.id, ts.id)
                if key in schedule:
                    row += f"{schedule[key]}".ljust(12)
                else:
                    row += "---".ljust(12)
            print(row)
    
    print("\n" + "="*80)
    print(f"Total Soft Constraint Penalty: {state.g_cost}")
    print("="*80 + "\n")


def print_metrics_comparison(results: Dict[str, tuple]):
    """
    Print a comparison table of search metrics.
    
    Args:
        results: Dictionary mapping algorithm name -> (state, metrics) tuple
    """
    print("\n" + "="*90)
    print("ALGORITHM PERFORMANCE COMPARISON")
    print("="*90)
    
    # Table header
    header = f"{'Algorithm':<20} {'Nodes Exp':<12} {'Nodes Gen':<12} {'Max Front':<12} {'Time(s)':<10} {'Sol Cost':<10}"
    print(header)
    print("-" * 90)
    
    # Table rows
    for algo_name, (solution, metrics) in results.items():
        if solution is not None:
            cost_str = str(metrics.solution_cost)
        else:
            cost_str = "FAILED"
        
        row = (f"{algo_name:<20} "
               f"{metrics.nodes_expanded:<12} "
               f"{metrics.nodes_generated:<12} "
               f"{metrics.max_frontier_size:<12} "
               f"{metrics.time_elapsed:<10.3f} "
               f"{cost_str:<10}")
        print(row)
    
    print("="*90 + "\n")


def plot_metrics_comparison(results: Dict[str, tuple], save_path: str = None):
    """
    Create bar charts comparing algorithm performance.
    
    Args:
        results: Dictionary mapping algorithm name -> (state, metrics) tuple
        save_path: Optional path to save the figure
    """
    # Extract data
    algorithms = []
    nodes_expanded = []
    time_taken = []
    solution_costs = []
    
    for algo_name, (solution, metrics) in results.items():
        algorithms.append(algo_name)
        nodes_expanded.append(metrics.nodes_expanded)
        time_taken.append(metrics.time_elapsed)
        if solution is not None:
            solution_costs.append(metrics.solution_cost)
        else:
            solution_costs.append(None)
    
    # Create subplots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot 1: Nodes Expanded
    axes[0].bar(algorithms, nodes_expanded, color='skyblue')
    axes[0].set_ylabel('Nodes Expanded')
    axes[0].set_title('Nodes Expanded by Algorithm')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].grid(axis='y', alpha=0.3)
    
    # Plot 2: Time Taken
    axes[1].bar(algorithms, time_taken, color='lightcoral')
    axes[1].set_ylabel('Time (seconds)')
    axes[1].set_title('Execution Time by Algorithm')
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].grid(axis='y', alpha=0.3)
    
    # Plot 3: Solution Quality
    valid_algos = [algo for algo, cost in zip(algorithms, solution_costs) if cost is not None]
    valid_costs = [cost for cost in solution_costs if cost is not None]
    
    if valid_costs:
        axes[2].bar(valid_algos, valid_costs, color='lightgreen')
        axes[2].set_ylabel('Total Penalty')
        axes[2].set_title('Solution Quality (Lower is Better)')
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].grid(axis='y', alpha=0.3)
    else:
        axes[2].text(0.5, 0.5, 'No solutions found', 
                    ha='center', va='center', transform=axes[2].transAxes)
        axes[2].set_title('Solution Quality')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {save_path}")
    else:
        plt.show()


def plot_timetable_grid(state: State, problem: Problem, save_path: str = None):
    """
    Create a visual grid representation of the timetable.
    Multi-slot courses (labs with duration > 1) are rendered as tall
    rectangles spanning all the timeslot rows they occupy.

    Args:
        state: Complete timetable state
        problem: Problem instance
        save_path: Optional path to save the figure
    """
    if not state.is_complete():
        print("Cannot visualize incomplete timetable")
        return

    # Assign a colour to every course
    course_colors = {}
    color_palette = plt.cm.Set3.colors
    for i, assignment in enumerate(state.assignments):
        cid = assignment.course.id
        if cid not in course_colors:
            course_colors[cid] = color_palette[i % len(color_palette)]

    # Build slot-id → grid-row index (top of grid = slot 0)
    rooms_sorted    = sorted(problem.rooms,     key=lambda r: r.id)
    timeslots_sorted = sorted(problem.timeslots, key=lambda t: t.id)
    slot_to_row = {ts.id: j for j, ts in enumerate(timeslots_sorted)}

    n_rooms     = len(rooms_sorted)
    n_timeslots = len(timeslots_sorted)
    room_to_col = {r.id: i for i, r in enumerate(rooms_sorted)}

    # Figure height scales with number of timeslots
    fig_h = max(10, n_timeslots * 0.45)
    fig_w = max(14, n_rooms * 1.6)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # Draw empty background grid first
    for i in range(n_rooms):
        for j in range(n_timeslots):
            y = n_timeslots - j - 1
            rect = mpatches.Rectangle(
                (i, y), 1, 1,
                facecolor="white", edgecolor="lightgray", linewidth=0.4
            )
            ax.add_patch(rect)

    # Draw each assignment — multi-slot courses span 'duration' rows
    for assignment in state.assignments:
        cid      = assignment.course.id
        duration = getattr(assignment.course, "duration", 1)
        col      = room_to_col[assignment.room.id]
        start_j  = slot_to_row[assignment.timeslot.id]

        # Grid y-axis: row 0 is the BOTTOM, so convert
        # start_j is the topmost occupied row in logical order (slot order).
        # In matplotlib the bottom of the figure = n_timeslots-1 row.
        y_bottom = n_timeslots - (start_j + duration)
        height   = duration

        color = course_colors[cid]
        rect = mpatches.Rectangle(
            (col, y_bottom), 1, height,
            facecolor=color, edgecolor="black", linewidth=0.7
        )
        ax.add_patch(rect)

        # Label in vertical centre of the block
        label = cid
        ax.text(
            col + 0.5,
            y_bottom + height / 2,
            label,
            ha="center", va="center",
            fontsize=6.5, weight="bold",
            wrap=True
        )

        # For multi-slot labs, shade the extra rows slightly darker
        if duration > 1:
            for d in range(1, duration):
                y_extra = n_timeslots - (start_j + d + 1)
                border = mpatches.Rectangle(
                    (col, y_extra), 1, 1,
                    facecolor="none", edgecolor="black",
                    linewidth=0.4, linestyle="--"
                )
                ax.add_patch(border)

    # Axis ticks
    ax.set_xlim(0, n_rooms)
    ax.set_ylim(0, n_timeslots)
    ax.set_xticks([i + 0.5 for i in range(n_rooms)])
    ax.set_xticklabels([r.id for r in rooms_sorted], rotation=45, ha="right", fontsize=8)
    ax.set_yticks([i + 0.5 for i in range(n_timeslots)])
    ax.set_yticklabels(
        [f"{ts.day[:3]} {ts.start_time}" for ts in reversed(timeslots_sorted)],
        fontsize=7
    )

    ax.set_xlabel("Rooms")
    ax.set_ylabel("Timeslots")
    ax.set_title(f"Timetable Solution (Penalty: {state.g_cost})")

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Timetable visualization saved to {save_path}")
    else:
        plt.show()


def generate_report(results: Dict[str, tuple], problem: Problem, 
                   difficulty: str, save_dir: str = "."):
    """
    Generate a complete performance report with visualizations.
    
    Args:
        results: Dictionary mapping algorithm name -> (state, metrics)
        problem: Problem instance
        difficulty: Problem difficulty level
        save_dir: Directory to save outputs
    """
    print(f"\n{'='*80}")
    print(f"GENERATING REPORT FOR {difficulty} PROBLEM")
    print(f"{'='*80}\n")
    
    # Print metrics table
    print_metrics_comparison(results)
    
    # Save metrics plot
    metrics_plot_path = f"{save_dir}/{difficulty.lower()}_metrics_comparison.png"
    plot_metrics_comparison(results, save_path=metrics_plot_path)
    
    # Print best solution
    best_algo = None
    best_cost = float('inf')
    
    for algo_name, (solution, metrics) in results.items():
        if solution is not None and metrics.solution_cost < best_cost:
            best_cost = metrics.solution_cost
            best_algo = algo_name
            best_solution = solution
    
    if best_algo:
        print(f"\nBest Solution Found by: {best_algo}")
        print(f"Penalty: {best_cost}")
        print_timetable(best_solution, problem)
    else:
        print("\nNo solutions found by any algorithm!")

    # Save a timetable grid image for EVERY algorithm that found a solution.
    # Characters like * : ? < > | \ / are illegal in Windows filenames —
    # sanitise each algorithm name before building the path.
    def _safe(name: str) -> str:
        return (name.lower()
                .replace(' ', '_')
                .replace('*', 'star')
                .replace(':', '')
                .replace('?', '')
                .replace('"', '')
                .replace('<', '')
                .replace('>', '')
                .replace('|', ''))

    saved_any = False
    for algo_name, (solution, metrics) in results.items():
        if solution is not None:
            timetable_plot_path = (
                f"{save_dir}/{difficulty.lower()}_timetable_{_safe(algo_name)}.png"
            )
            print(f"\nSaving timetable grid for {algo_name} → {timetable_plot_path}")
            plot_timetable_grid(solution, problem, save_path=timetable_plot_path)
            saved_any = True

    if not saved_any:
        print("\nNo timetable grids saved (no algorithm found a solution).")
