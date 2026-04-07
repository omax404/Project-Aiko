# SOP: System Optimization

## Goal
Monitor system health and proactively suggest optimizations if resources are low.

## Inputs
- `cpu_threshold`: 70% (Default)
- `ram_threshold`: 85% (Default)

## Process
1. Run `execution/system_check.py` to gather metrics.
2. If `cpu_percent` > `cpu_threshold`:
    - Identify top 3 CPU-consuming processes.
    - Prepare a "Worried" reaction.
    - Inform the user gently about the resource spike.
3. If `ram_percent` > `ram_threshold`:
    - Suggest closing unused applications.
4. Log findings to Aiko's session memory.

## Outputs
- `status`: "Normal" or "Critical".
- `top_processes`: List of [Name, CPU%].
- `proactive_msg`: Optional recommendation string.
