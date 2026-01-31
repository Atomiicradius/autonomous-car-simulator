# Contributing to Autonomous Car Simulator

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** and test locally
   ```bash
   python test_physics.py
   python test_sensors.py
   python test_integration.py
   ```

3. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: description of what changed"
   ```

4. **Push to your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

## Code Standards

- **Python 3.8+** compatible
- **PEP 8** style guide
- **Type hints** for function signatures (optional but appreciated)
- **Docstrings** for classes and methods
- **Unit tests** for new features

## Testing Requirements

All changes must pass:
```bash
python test_physics.py      # 12 tests
python test_sensors.py      # 14 tests
python test_integration.py  # 3 tests
python test_adapter.py      # 1 test
```

Expected output: **30/30 PASS** ✅

## File Naming Conventions

- Modules: `lowercase_with_underscores.py`
- Tests: `test_<module_name>.py`
- Directories: `lowercase_with_underscores/`

## Prohibited in Repository

- `__pycache__/` directories (use `.gitignore`)
- `.pyc`, `.pyo` files
- Virtual environment folders (`venv/`, `.env/`)
- IDE-specific files (`.vscode/`, `.idea/`)
- Temporary debug files

## Adding New Features

### Adding a New Scenario

1. Update `config.json`:
   ```json
   "scenarios": {
       "my_scenario": {
           "description": "What this tests",
           "obstacles": [...]
       }
   }
   ```

2. Add test in `test_sensors.py`:
   ```python
   def test_scenario_my_scenario():
       """Test my_scenario loads."""
       ...
   ```

3. Add to test runner:
   ```python
   tests = [..., test_scenario_my_scenario]
   ```

### Adding New Physics Features

1. Implement in `physics.py`
2. Add unit test in `test_physics.py`
3. Add integration test in `test_integration.py` if needed
4. Update docstring and `FINAL_STATUS.md`

### Adding Sensor Features

1. Implement in `sensors.py`
2. Add unit test in `test_sensors.py`
3. Test with all scenarios
4. Update documentation

## Documentation

Update relevant docs when making changes:
- Code comments for implementation details
- Docstrings for public APIs
- `README.md` for user-facing features
- `docs/` folder for architecture notes

## Performance Considerations

- Raycast algorithm is O(n) per sensor per timestep
- Collision detection is O(n) per timestep
- With <20 obstacles, performance is not a bottleneck
- Profile before optimizing

## Questions?

Check the docs in `docs/` folder for detailed implementation notes.

---

**Happy coding!** 🚀
