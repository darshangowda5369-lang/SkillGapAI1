def calculate_roadmap_completion_percentage(total_steps, completed_steps):
    """Return the roadmap progress percentage capped at 100%.

    The percentage must reflect the real completion state and never drift above
    the actual number of completed steps for the roadmap.
    """
    if total_steps <= 0:
        return 0.0

    if completed_steps >= total_steps:
        return 100.0

    return round((completed_steps / total_steps) * 100.0, 1)
