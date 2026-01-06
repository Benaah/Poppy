# Contributing to Poppy

Thank you for considering contributing to Poppy! This document outlines the development process and guidelines.

## Development Setup

1. Fork and clone the repository
2. Run the workspace initialization script:

   ```bash
   ./tools/scripts/init_workspace.sh
   ```

3. Install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use Black formatter: `black .`
- Lint with Flake8: `flake8 .`

### C++

- Follow Google C++ Style Guide
- Use clang-format
- Use modern C++17 features

### ROS2 Conventions

- Node names: `snake_case`
- Topic names: `snake_case`
- Service/Action names: `PascalCase`
- Package names: `poppy_<component>`

## Commit Messages

Follow Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:

```
feat(vision): add MediaPipe person tracking
fix(navigation): resolve DWA collision detection bug
docs(api): update SDK reference documentation
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and commit
3. Write/update tests as needed
4. Ensure all tests pass: `colcon test`
5. Update documentation
6. Push and create PR with clear description

## Testing

- Unit tests: `colcon test --packages-select <package>`
- Integration tests: `ros2 launch poppy_bringup test.launch.py`
- Coverage: `colcon test --pytest-args --cov`

## Questions?

Open an issue or reach out to the maintainers.

---

**Happy coding!**
