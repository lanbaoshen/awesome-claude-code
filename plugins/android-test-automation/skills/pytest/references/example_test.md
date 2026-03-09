# Example: conftest.py + pytest test file

A complete, copy-paste-ready example for writing Android UI tests with pytest + uiautomator2.

---

## conftest.py

Place this at the project root (same level as `pyproject.toml`):

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
    """Session-scoped uiautomator2 Device fixture shared across all tests.

    Connects once per pytest session. Use --serial to target a specific device.
    """
    serial = request.config.getoption("--serial")
    device = u2.connect(serial=serial) if serial else u2.connect()
    device.screen_on()
    device.unlock()
    yield device
    # Leave a clean state at the end of the session
    device.press("home")
```

---

## Example test file: tests/test_settings.py

```python
# tests/test_settings.py
"""
Example: testing the Android Settings app.

Demonstrates:
  - Class-based test grouping
  - setup + teardown via an autouse fixture (the recommended pattern)
  - Common uiautomator2 assertions
"""
import pytest


class TestWifi:
    """Tests for the Wi-Fi settings screen."""

    @pytest.fixture(autouse=True)
    def setup(self, d):
        """Open Settings before each test; close it after.

        Everything before `yield` is setup.
        Everything after `yield` is teardown.
        `self.d` stores the device so other methods can use it without
        receiving `d` as a parameter (setup_method can't take fixtures).
        """
        self.d = d
        # --- setup ---
        self.d.app_start("com.android.settings", stop=True)
        self.d.wait_activity(".Settings", timeout=5)
        yield
        # --- teardown ---
        self.d.app_stop("com.android.settings")
        self.d.press("home")

    def test_settings_opens(self, d):
        """Verify the Settings app launched successfully."""
        assert d(text="Network & internet").exists or d(text="Wi-Fi").exists

    def test_wifi_entry_visible(self, d):
        """Verify a Wi-Fi-related entry is present on the main settings screen."""
        # Scroll down a little in case it's off-screen
        d.swipe_ext("up", scale=0.3)
        assert d(textContains="Wi-Fi").exists

    def test_open_wifi_screen(self, d):
        """Tap the Wi-Fi entry and verify the Wi-Fi screen opens."""
        # Navigate to Wi-Fi — exact label varies by Android version
        if d(text="Network & internet").exists:
            d(text="Network & internet").click()
            d(text="Internet").click()
        else:
            d(text="Wi-Fi").click()

        # The Wi-Fi toggle should now be visible
        assert d(textContains="Wi-Fi").wait(timeout=5), "Wi-Fi screen did not open"


class TestDisplay:
    """Tests for the Display settings screen."""

    @pytest.fixture(autouse=True)
    def setup(self, d):
        self.d = d
        # Navigate directly to Display settings
        self.d.app_start("com.android.settings", stop=True)
        self.d.wait_activity(".Settings", timeout=5)
        yield
        self.d.app_stop("com.android.settings")
        self.d.press("home")

    def test_display_entry_accessible(self, d):
        """Verify the Display settings entry can be reached."""
        # Scroll to find Display
        for _ in range(3):
            if d(text="Display").exists:
                break
            d.swipe_ext("up", scale=0.4)

        assert d(text="Display").exists, "Display entry not found in Settings"

    def test_display_screen_opens(self, d):
        """Open Display settings and verify the screen title."""
        for _ in range(3):
            if d(text="Display").exists:
                break
            d.swipe_ext("up", scale=0.4)

        d(text="Display").click()
        assert d(text="Display").wait(timeout=5), "Display settings screen did not open"
```

---

## Running the tests

```bash
# Run all tests
uv run pytest

# Run with verbose output and print statements visible
uv run pytest -v -s

# Run only the Wi-Fi tests
uv run pytest -k "TestWifi"

# Run on a specific device
uv run pytest --serial emulator-5554

# Run a single test
uv run pytest tests/test_settings.py::TestWifi::test_open_wifi_screen -v
```

---

## Project layout

```
my-project/
├── pyproject.toml        # pytest + uiautomator2 as dependencies
├── conftest.py           # d fixture lives here
└── tests/
    ├── test_settings.py
    ├── test_calculator.py
    └── ...
```
