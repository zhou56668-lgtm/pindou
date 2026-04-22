def plan_steps(grid: list[list[dict]], rows_per_step: int = 3) -> list[dict]:
    """
    Split the grid into steps. Each step covers `rows_per_step` rows.

    Returns a list of steps:
    [
      {
        "step": 1,
        "row_start": 0,   # inclusive
        "row_end": 2,     # inclusive
        "cells": [{"row": int, "col": int, "name": str, "r": int, "g": int, "b": int}, ...]
      },
      ...
    ]
    """
    steps = []
    total_rows = len(grid)
    step_num = 1

    for start in range(0, total_rows, rows_per_step):
        end = min(start + rows_per_step - 1, total_rows - 1)
        cells = []
        for row_i in range(start, end + 1):
            for col_i, cell in enumerate(grid[row_i]):
                cells.append({
                    "row": row_i,
                    "col": col_i,
                    "name": cell["name"],
                    "r": cell["r"],
                    "g": cell["g"],
                    "b": cell["b"],
                })
        steps.append({
            "step": step_num,
            "row_start": start,
            "row_end": end,
            "cells": cells,
        })
        step_num += 1

    return steps
