# Skill: Code Generation Standards

## Purpose
Ensure all generated Python code follows DTL-Global standards.

## When to Use
Every time you generate or modify Python code.

## File Structure Template

Every Python file MUST follow this structure:

1. Module-level docstring explaining the file purpose
2. Standard Library Imports
3. Third-Party Imports
4. Local Imports
5. Constants (with comments)
6. Classes and Functions (with Google docstrings)
7. Main block (if applicable)

## Function Template

```python
def example_function(name: str, options: list[str]) -> dict:
    """Brief description of what this function does.

    Longer description if needed, explaining the business logic
    and how this fits into the DTL-Global onboarding workflow.

    Args:
        name: The display name for the resource.
        options: List of option values to configure.

    Returns:
        A dict containing the created resource ID and metadata.
        Example: {"id": "abc123", "name": "My Resource", "status": "active"}

    Raises:
        ValueError: If name is empty or options is empty.
        APIError: If the external API call fails.
    """
    # Validate inputs before making any API calls
    if not name:
        raise ValueError("Name cannot be empty")  # Guard clause

    # Build the configuration object from provided options
    config = {
        "label": name,  # Display name shown in the UI
        "options": [
            {"value": opt, "label": opt}  # Each option needs value and label
            for opt in options
        ]
    }

    # Call the external API with error handling
    try:
        response = api_client.create(config)  # Create the resource
        return {
            "id": response.id,  # Unique identifier from the API
            "name": response.label,  # Confirmed display name
            "status": "active"  # Resource is immediately active
        }
    except ApiException as e:
        # Log the error with context for debugging
        print(f"ERROR: Failed to create resource '{name}': {e}")
        raise APIError(f"Failed to create '{name}': {e}")  # Re-raise with context
```

## Rules Checklist (Verify Before Completing Any File)
- Module-level docstring present
- Imports organized: stdlib, third-party, local
- Constants defined with comments
- All functions have Google docstrings (Args, Returns, Raises)
- Every meaningful line has an inline comment
- All API calls wrapped in try/except
- No hardcoded secrets (use SSM/env vars)
- snake_case naming throughout
- Type hints on all function signatures