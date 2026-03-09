---
name: uiautomator2
description: >
  Control Android devices from the terminal using uiautomator2.
  Use this skill whenever the user wants to interact with a phone or Android device —
  tapping buttons, typing text, swiping, taking screenshots, launching apps, reading
  the screen, automating workflows, or anything else that involves touching the device.
  Trigger on any mention of: phone, Android, device, mobile, app automation, tap,
  swipe, screenshot the phone, send message on phone, open app, install APK, or
  "do X on my phone/device". Don't wait for the user to say "uiautomator" — if they
  want something done on a device, this skill handles it.
---

# uiautomator2 — Android Device Control

You control Android devices through **u2cli**, a thin CLI wrapper around the uiautomator2
Python library. For the full command reference, read:

> **`references/cli-reference.md`** — all commands with examples, selectors, and options.

---

## General workflow

1. **Orient yourself** — take a screenshot or dump the UI hierarchy to understand the current state.
2. **Act** — tap, type, swipe, or launch apps based on what you see.
3. **Verify** — take another screenshot or check `exists` / `get-text` to confirm the result.
4. Repeat until the task is done.

When you don't know an element's selector, run `dump-hierarchy --pretty` first and inspect
the XML for `text`, `resource-id`, `content-desc`, or `class` values.

---

## Common patterns

### Open an app and tap a button

```bash
uv run ... app-start com.android.settings
uv run ... wait-activity .Settings --timeout 5
uv run ... screenshot /tmp/before.png
uv run ... click text "Wi-Fi"
uv run ... screenshot /tmp/after.png
```

### Fill in a form

```bash
uv run ... click resource-id "com.example:id/username"
uv run ... send-keys "myuser" --clear
uv run ... click resource-id "com.example:id/password"
uv run ... send-keys "mypassword" --clear
uv run ... click text "Login"
```

### Scroll down to find an element

```bash
uv run ... swipe-ext up        # scroll down
uv run ... exists text "Load more"
```

---

## Tips

- **Prefer `text` or `resource-id` selectors** — most stable. Fall back to `xpath` or `coords`.
- **Use ratios (0.0–1.0) for swipe coordinates** to stay resolution-independent.
- **Always screenshot after complex actions** to verify before continuing.
- **`dump-hierarchy` is your map** — when unsure what's on screen, dump it and read it.
- **`app-current`** tells you the foreground package/activity, useful for debugging navigation.
