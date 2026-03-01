# Contributing to BharatSahayak

Thank you for your interest in contributing to BharatSahayak! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/bharatsahayak.git
   cd bharatsahayak
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make install
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the project style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**
   ```bash
   make test
   ```

4. **Format and lint code**
   ```bash
   make format
   make lint
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template

## Code Style

### Python Style Guide

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 100)
- Use isort for import sorting
- Use type hints for function signatures
- Write docstrings for all public functions and classes

### Example

```python
from typing import List, Optional

def calculate_eligibility(
    user_profile: UserProfile,
    scheme: Scheme
) -> EligibilityResult:
    """
    Calculate user eligibility for a government scheme.
    
    Args:
        user_profile: User profile containing demographic information
        scheme: Government scheme with eligibility criteria
        
    Returns:
        EligibilityResult with eligibility status and reasoning
    """
    # Implementation
    pass
```

## Testing Guidelines

### Test Structure

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **Property-based tests**: Test universal properties using Hypothesis

### Writing Tests

```python
# Unit test example
def test_eligibility_checker_age_criteria():
    """Test eligibility checker with age criteria."""
    user = UserProfile(age=25)
    scheme = Scheme(eligibility_criteria=EligibilityCriteria(age_min=18, age_max=30))
    
    result = eligibility_checker.check_eligibility(user, scheme)
    
    assert result.is_eligible is True

# Property-based test example
from hypothesis import given, strategies as st

@given(age=st.integers(min_value=0, max_value=120))
def test_age_validation_property(age):
    """
    Feature: bharatsahayak, Property: Age validation
    For any valid age, the system should accept it without errors.
    """
    user = UserProfile(age=age)
    assert user.age == age
```

### Test Coverage

- Aim for at least 80% code coverage
- All new features must include tests
- Critical paths require 100% coverage

## Commit Message Format

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(voice): add support for Marathi language

Implement Marathi language support in STT and TTS engines.
Includes language detection and voice profile configuration.

Closes #123
```

```
fix(eligibility): correct income bracket comparison

Fixed bug where income comparison was using string instead of numeric comparison.

Fixes #456
```

## Pull Request Guidelines

### PR Checklist

- [ ] Code follows the style guide
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts
- [ ] PR description is clear and complete

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add comments for complex logic
- Update design documents for architectural changes

## Code Review Process

1. **Automated checks**: CI/CD runs tests and linters
2. **Peer review**: At least one approval required
3. **Maintainer review**: Final approval from maintainer
4. **Merge**: Squash and merge to main branch

## Issue Reporting

### Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and logs

### Feature Requests

Include:
- Description of the feature
- Use case and motivation
- Proposed implementation (optional)
- Alternatives considered

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow the Code of Conduct

## Questions?

- Open an issue for questions
- Join our community discussions
- Contact the maintainers

Thank you for contributing to BharatSahayak!