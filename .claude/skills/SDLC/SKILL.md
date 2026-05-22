<!-- Version: 1.1.0 -->
```markdown
# SDLC Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill introduces the core development patterns and workflows used in the SDLC Python repository. It covers file organization, code style, commit conventions, and the process for updating documentation. By following these guidelines, contributors can maintain consistency and quality across the codebase.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `user_service.py`, `data_processor.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import parse_config
    from .models import User
    ```

### Export Style
- Use **named exports** to expose specific functions, classes, or variables.
  - Example:
    ```python
    __all__ = ['User', 'parse_config']
    ```

### Commit Messages
- Follow **conventional commit** patterns.
- Use the `feat` prefix for new features.
  - Example:
    ```
    feat: add user authentication module
    ```

## Workflows

### Documentation Update
**Trigger:** When you want to improve, update, or finalize project documentation (e.g., README or guides).  
**Command:** `/update-docs`

1. Edit `README.md` to add or update documentation, specifications, or guides.
2. Review and finalize your documentation changes.
3. Commit changes with a message indicating a documentation update or overhaul.
   - Example commit message:
     ```
     feat: update README with setup instructions
     ```

## Testing Patterns

- **Test Framework:** Not explicitly defined; use standard Python testing tools (e.g., `unittest`, `pytest`).
- **Test File Naming:** Name test files using the pattern `*.test.*`.
  - Example: `user_service.test.py`, `data_processor.test.py`
- **Test Example:**
  ```python
  import unittest
  from .user_service import create_user

  class TestUserService(unittest.TestCase):
      def test_create_user(self):
          user = create_user('alice')
          self.assertEqual(user.name, 'alice')

  if __name__ == '__main__':
      unittest.main()
  ```

## Commands
| Command      | Purpose                                      |
|--------------|----------------------------------------------|
| /update-docs | Start the documentation update workflow       |
```
