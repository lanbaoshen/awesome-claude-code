---
name: pytest
description: >
  Write and run pytest test cases for Android UI automation using uiautomator2.
  Use this skill whenever the user wants to write pytest test cases, create test scripts,
  run pytest, set up conftest.py, or automate Android UI testing with pytest.
  Trigger on any mention of: pytest, test case, test script, conftest, write test,
  run test, uv run pytest, setup fixture, teardown, test automation, test file,
  or "test X on Android/phone/device". Don't wait for the user to say "pytest" explicitly —
  if they want to verify or automate behavior on an Android device through a test structure,
  this skill handles it.
---

# pytest + uiautomator2 — Android UI Test Framework

You help users write, structure, and run pytest-based Android UI tests using the `uiautomator2` library.
Tests use a shared `d` fixture (a live `uiautomator2.Device` object) provided by `conftest.py`.

---

## Project prerequisites

The project must have these dependencies (already in `pyproject.toml`):

```toml
[project]
dependencies = [
    "pytest>=9.0.2",
    "uiautomator2>=3.5.0",
]
```

Run tests with:

```bash
uv run pytest                         # run all tests
uv run pytest tests/test_settings.py  # run a specific file
uv run pytest -v -s                   # verbose with print output
uv run pytest -k "test_wifi"          # run tests matching a name pattern
```

---

## conftest.py — the d fixture

Every test project needs a `conftest.py` at the root (or the tests directory) that
provides the `d` fixture. If one doesn't exist, create it:

```python
# conftest.py
import pytest
import uiautomator2 as u2


def pytest_addoption(parser):
    parser.addoption(
        "--serial",
        action="store",
        default=None,
        help="ADB serial number of the target device (omit if only one device is connected)",
    )


@pytest.fixture(scope="session")
def d(request):
    """Session-scoped uiautomator2 Device fixture.

    Usage in tests:
        def test_something(d):
            d.app_start("com.android.settings")
            assert d(text="Wi-Fi").exists
    """
    serial = request.config.getoption("--serial")
    device = u2.connect(serial=serial) if serial else u2.connect()
    device.screen_on()
    device.unlock()
    yield device
    # Session teardown: press home to leave a clean state
    device.press("home")
```

To target a specific device when multiple are connected:

```bash
uv run pytest --serial d74e53a3
```

---

## Test file structure

### Basic pattern

```python
# tests/test_<feature>.py
import pytest


class TestFeatureName:
    """Group related test cases in a class."""

    def setup_method(self, method):
        """Runs before each test method in this class."""
        # e.g., launch the app fresh each time
        pass

    def teardown_method(self, method):
        """Runs after each test method in this class."""
        # e.g., close the app, press home
        pass

    def test_something(self, d):
        # your test logic
        pass
```

### setup_method / teardown_method with d

Because `d` is a fixture and `setup_method` / `teardown_method` are plain methods,
you cannot receive `d` directly in `setup_method`. The clean pattern is to store `d`
on `self` in the first test or use a class-scoped fixture. The recommended approach
is a per-class autouse fixture:

```python
class TestSettings:
    @pytest.fixture(autouse=True)
    def setup(self, d):
        """Runs before each test; d is available here and stored on self."""
        self.d = d
        # --- setup ---
        self.d.app_start("com.android.settings", stop=True)
        yield
        # --- teardown ---
        self.d.app_stop("com.android.settings")

    def test_wifi_toggle(self, d):
        d.click(text="Wi-Fi")
        assert d(text="Wi-Fi").exists
```

The `yield` inside the autouse fixture is the cleanest way to combine setup + teardown
in a single place. Everything before `yield` is setup; everything after is teardown.

---

## Example test file

See `references/example_test.md` for a complete, commented example showing:
- conftest.py setup
- class-based test structure
- setup/teardown via autouse fixture
- real uiautomator2 assertions

---

## Writing test assertions

`d` is a live `uiautomator2.Device`. Common assertion patterns:

```python
# Element exists
assert d(text="Submit").exists

# Element does not exist
assert not d(text="Error").exists

# Get text and compare
assert d(resourceId="com.example:id/title").get_text() == "Welcome"

# Wait for element (with timeout)
assert d(text="Loading...").wait_gone(timeout=10)
assert d(text="Done").wait(timeout=10)

# Screenshot on failure (attach to test output)
d.screenshot("/tmp/failure.png")
```

---

## Tips

- **Use `stop=True` in `app_start`** when you want a clean launch: `d.app_start("com.example", stop=True)`.
- **Prefer `text` and `resourceId` selectors** — they're the most stable across app updates.
- **`d.dump_hierarchy(pretty=True)`** is useful for discovering selectors during development.
- **`scope="session"`** on the `d` fixture means the device connection is shared across all tests — fast, but be careful about leftover state between test classes.
- **Use `wait()` and `wait_gone()`** instead of `time.sleep()` — they're faster and more reliable.
- **Screenshots on failure**: add a `pytest_runtest_makereport` hook in conftest.py if you want automatic screenshots when tests fail.
