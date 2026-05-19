```markdown
# SDLC Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill provides guidance on the development patterns and conventions used in the SDLC TypeScript codebase. It covers file naming, import/export styles, commit message formatting, and testing patterns. Use this as a reference to ensure consistency and maintainability when contributing to the project.

## Coding Conventions

### File Naming
- **Style:** Snake case
- **Example:**  
  ```plaintext
  user_service.ts
  order_processor.test.ts
  ```

### Import Style
- **Relative imports are used.**
- **Example:**  
  ```typescript
  import { calculateTotal } from './order_utils';
  ```

### Export Style
- **Named exports are preferred.**
- **Example:**  
  ```typescript
  // order_utils.ts
  export function calculateTotal(items: Item[]): number {
    // ...
  }
  ```

### Commit Messages
- **Conventional commit format**
- **Prefix:** `feat`
- **Example:**  
  ```
  feat: add order validation to checkout process
  ```

## Workflows

### Feature Development
**Trigger:** When implementing a new feature or module  
**Command:** `/feature-development`

1. Create a new file using snake_case naming.
2. Write your TypeScript code, using relative imports and named exports.
3. Add or update corresponding test files with the `.test.ts` pattern.
4. Commit your changes using the conventional commit format with the `feat` prefix.
5. Push your branch and open a pull request for review.

### Testing Code
**Trigger:** When you need to verify code correctness  
**Command:** `/run-tests`

1. Ensure your test files follow the `*.test.ts` naming convention.
2. Run the test suite using your preferred test runner (framework not specified).
3. Review test results and fix any failing tests.
4. Commit any necessary changes.

## Testing Patterns

- **Test files use the `*.test.ts` naming convention.**
- **Testing framework is not specified; use your team's standard.**
- **Example:**
  ```typescript
  // order_processor.test.ts
  import { processOrder } from './order_processor';

  describe('processOrder', () => {
    it('should process a valid order', () => {
      // test implementation
    });
  });
  ```

## Commands
| Command              | Purpose                                      |
|----------------------|----------------------------------------------|
| /feature-development | Start a new feature using project conventions|
| /run-tests           | Run the test suite for the codebase          |
```