# u2cli Reference

Full command reference for `u2cli.py`, a CLI wrapper around uiautomator2.

## Invocation

```bash
uv run .claude/skills/uiautomator2/scripts/u2cli.py [--serial <SERIAL>] <command> [args]
```

- Omit `--serial` when only one device is connected.
- Use `--serial <SERIAL>` (e.g. `-s d74e53a3`) when multiple devices are attached.

Every command outputs a JSON object:

```json
{"success": true, "code": "<uiautomator2 Python equivalent>", "output": "<result or error>"}
```

Always check `success`. If `false`, read `output` for the error message.

---

## Selectors

Most element commands take a `<selector> <value>` pair:

| Selector | Example value |
|---|---|
| `text` | `"Sign in"` |
| `resource-id` | `"com.android.settings:id/search"` |
| `description` | `"Navigate up"` |
| `classname` | `"android.widget.EditText"` |
| `xpath` | `"//android.widget.TextView[@text='OK']"` |
| `coords` | `540` (x), then `y` as a positional arg |

---

## Device info

```bash
uv run ... info                        # UI-level info (screen size, orientation)
uv run ... device-info                 # hardware info (brand, model, SDK version)
uv run ... window-size                 # physical screen dimensions in pixels
uv run ... app-current                 # foreground package + activity
uv run ... orientation                 # current orientation
uv run ... set-orientation natural     # force orientation: natural|n|left|l|right|r
```

---

## Screenshot & UI hierarchy

```bash
# Full-screen screenshot
uv run ... screenshot /tmp/screen.png

# Screenshot of a specific element
uv run ... element-screenshot text "Submit" /tmp/btn.png

# Dump XML UI tree (use to find selectors)
uv run ... dump-hierarchy
uv run ... dump-hierarchy --compressed --pretty

# Get last toast message (waits up to 5 s)
uv run ... toast
```

**Tip:** Run `dump-hierarchy --pretty` to discover `text`, `resource-id`, `content-desc`,
`class`, or build an XPath expression for any element.

---

## Tapping & clicking

```bash
uv run ... click text "OK"
uv run ... click resource-id "com.example:id/btn_submit"
uv run ... click xpath "//android.widget.Button[@text='Continue']"
uv run ... click coords 540 960

uv run ... long-click text "Delete"
uv run ... long-click coords 540 960 --duration 1.5

uv run ... double-click 540 960
uv run ... double-click 540 960 --duration 0.2
```

---

## Text input

```bash
uv run ... send-keys "hello world"           # type into focused field
uv run ... send-keys "new text" --clear      # clear first, then type
uv run ... clear-text                        # clear focused field

uv run ... set-text resource-id "com.example:id/input" "hello"
uv run ... element-clear-text resource-id "com.example:id/input"
uv run ... get-text text "Username"
```

---

## Gestures

```bash
uv run ... swipe-ext up                      # scroll down
uv run ... swipe-ext down --scale 0.6        # shorter swipe

uv run ... swipe 0.5 0.8 0.5 0.2             # scroll up (ratio coords)
uv run ... swipe 100 900 100 400 --duration 0.3

uv run ... drag 300 800 300 400
uv run ... drag 300 800 300 400 --duration 0.5

uv run ... element-swipe text "List" up --steps 30
```

---

## Hardware keys

```bash
uv run ... press home
uv run ... press back
uv run ... press menu
uv run ... press power
uv run ... press volume_up
uv run ... press volume_down
uv run ... press enter
uv run ... press delete
```

---

## Screen & lock

```bash
uv run ... screen-on
uv run ... screen-off
uv run ... unlock
uv run ... open-notification
uv run ... open-quick-settings
```

---

## Clipboard

```bash
uv run ... get-clipboard
uv run ... set-clipboard "text to paste"
```

---

## Element inspection

```bash
uv run ... exists text "Logout"
uv run ... element-info resource-id "com.example:id/title"
```

---

## App management

```bash
uv run ... app-start com.android.settings
uv run ... app-start com.example.app --activity .MainActivity --stop

uv run ... app-stop com.example.app
uv run ... app-stop-all
uv run ... app-stop-all --exclude com.android.systemui

uv run ... app-clear com.example.app

uv run ... app-install /tmp/myapp.apk
uv run ... app-uninstall com.example.app

uv run ... app-info com.android.settings
uv run ... app-list-running

uv run ... app-wait com.example.app --timeout 20 --front
uv run ... wait-activity .MainActivity --timeout 10
```

---

## File transfer

```bash
uv run ... push /tmp/file.txt /sdcard/Download/file.txt
uv run ... pull /sdcard/Download/file.txt /tmp/file.txt
```

---

## ADB shell

For anything not covered above:

```bash
uv run ... shell "dumpsys battery"
uv run ... shell "am start -a android.intent.action.VIEW -d 'https://example.com'"
uv run ... shell "input text 'hello'"
```

Output: `{"exit_code": 0, "output": "..."}`.
