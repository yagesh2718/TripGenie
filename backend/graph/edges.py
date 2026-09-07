from backend.schemas.state import TripState

def should_continue(state: TripState) -> str:
    """
    Determines whether to loop back to the planner or end the workflow.
    """
    is_valid = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)
    
    if is_valid or retry_count >= 3:
        # If the plan is valid or we've hit the max retries, finish
        return "end"
    else:
        # Loop back to planner with the critic's feedback
        return "planner"
