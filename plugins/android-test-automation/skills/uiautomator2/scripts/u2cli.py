import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import uiautomator2 as u2


@dataclass
class Result:
    success: bool
    code: str
    output: str


def _coord(value: str) -> int | float:
    """Parse a coordinate: returns float for ratios (0–1), int for absolute pixels."""
    v = float(value)
    return int(v) if v.is_integer() else v


_ELEMENT_SELECTOR_CHOICES = ['text', 'resource-id', 'description', 'classname', 'xpath']
_ALL_SELECTOR_CHOICES = _ELEMENT_SELECTOR_CHOICES + ['coords']


def _resolve_element(d, selector: str, value: str):
    """Return (element, code_repr) for the given selector/value pair."""
    match selector:
        case 'text':
            return d(text=value), f'd(text={value!r})'
        case 'resource-id':
            return d(resourceId=value), f'd(resourceId={value!r})'
        case 'description':
            return d(description=value), f'd(description={value!r})'
        case 'classname':
            return d(className=value), f'd(className={value!r})'
        case 'xpath':
            return d.xpath(value), f'd.xpath({value!r})'
        case _:
            raise ValueError(f'Unknown selector: {selector}')


_SKIP_CLASSES = {
    'android.widget.FrameLayout',
    'android.view.ViewGroup',
    'android.view.View',
}

_USEFUL_ATTRS = (
    'text',
    'resource-id',
    'content-desc',
    'class',
    'bounds',
    'clickable',
    'enabled',
    'checked',
    'scrollable',
)


def _parse_hierarchy(xml: str) -> str:
    """Parse UI hierarchy XML and return a compact, token-efficient text representation.

    Only includes nodes that have meaningful content (text, resource-id, content-desc,
    or interactive flags). Skips pure layout/container nodes.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return xml

    lines: list[str] = []

    def _visit(node: ET.Element, depth: int) -> None:
        cls = node.get('class', '')
        text = node.get('text', '').strip()
        rid = node.get('resource-id', '')
        desc = node.get('content-desc', '').strip()
        clickable = node.get('clickable') == 'true'
        scrollable = node.get('scrollable') == 'true'
        enabled = node.get('enabled') == 'true'
        checked = node.get('checked')
        bounds = node.get('bounds', '')

        # Determine if this node carries useful information
        has_content = bool(text or rid or desc)
        is_interactive = clickable or scrollable
        is_meaningful = has_content or is_interactive

        if is_meaningful:
            parts: list[str] = []
            # Shorten class name: keep only the last segment
            short_cls = cls.split('.')[-1] if cls else ''
            if short_cls:
                parts.append(short_cls)
            if text:
                parts.append(f'text="{text}"')
            if rid:
                # Strip package prefix for brevity: com.example:id/foo -> foo
                short_rid = rid.split('/')[-1] if '/' in rid else rid
                parts.append(f'id={short_rid}')
            if desc and desc != text:
                parts.append(f'desc="{desc}"')
            if bounds:
                parts.append(f'bounds={bounds}')
            flags: list[str] = []
            if clickable:
                flags.append('clickable')
            if scrollable:
                flags.append('scrollable')
            if not enabled:
                flags.append('disabled')
            if checked == 'true':
                flags.append('checked')
            elif checked == 'false' and cls and 'Check' in cls:
                flags.append('unchecked')
            if flags:
                parts.append(f'[{",".join(flags)}]')
            indent = '  ' * depth
            lines.append(f'{indent}{" ".join(parts)}')

        # Always recurse into children
        child_depth = (depth + 1) if is_meaningful else depth
        for child in node:
            _visit(child, child_depth)

    _visit(root, 0)
    return '\n'.join(lines) if lines else '(empty hierarchy)'


class CLI:
    def __init__(self, serial: str | None = None) -> None:
        self.d = u2.connect(serial=serial) if serial else u2.connect()

    # ── Element interaction ────────────────────────────────────────────────

    def click(self, selector: str, value: str, y: int | None = None) -> Result:
        try:
            if selector == 'coords':
                x = int(value)
                if y is None:
                    return Result(success=False, code='', output='Y coordinate is required for coords selector')
                self.d.click(x, y)
                code = f'd.click({x}, {y})'
            else:
                el, el_code = _resolve_element(self.d, selector, value)
                el.click()
                code = f'{el_code}.click()'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def long_click(self, selector: str, value: str, y: int | None = None, duration: float | None = None) -> Result:
        try:
            if selector == 'coords':
                x = int(value)
                if y is None:
                    return Result(success=False, code='', output='Y coordinate is required for coords selector')
                if duration is not None:
                    self.d.long_click(x, y, duration)
                    code = f'd.long_click({x}, {y}, {duration})'
                else:
                    self.d.long_click(x, y)
                    code = f'd.long_click({x}, {y})'
            else:
                el, el_code = _resolve_element(self.d, selector, value)
                el.long_click()
                code = f'{el_code}.long_click()'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def double_click(self, x: int, y: int, duration: float = 0.1) -> Result:
        try:
            self.d.double_click(x, y, duration)
            code = f'd.double_click({x}, {y}, {duration})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def get_text(self, selector: str, value: str) -> Result:
        try:
            el, el_code = _resolve_element(self.d, selector, value)
            text = el.get_text()
            code = f'{el_code}.get_text()'
            return Result(success=True, code=code, output=text or '')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def set_text(self, selector: str, value: str, text: str) -> Result:
        try:
            el, el_code = _resolve_element(self.d, selector, value)
            el.set_text(text)
            code = f'{el_code}.set_text({text!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def element_clear_text(self, selector: str, value: str) -> Result:
        try:
            el, el_code = _resolve_element(self.d, selector, value)
            el.clear_text()
            code = f'{el_code}.clear_text()'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def exists(self, selector: str, value: str) -> Result:
        try:
            el, el_code = _resolve_element(self.d, selector, value)
            result = bool(el.exists)
            code = f'{el_code}.exists'
            return Result(success=True, code=code, output=json.dumps(result))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def element_info(self, selector: str, value: str) -> Result:
        try:
            el, el_code = _resolve_element(self.d, selector, value)
            info = el.info
            code = f'{el_code}.info'
            return Result(success=True, code=code, output=json.dumps(info))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def element_swipe(self, selector: str, value: str, direction: str, steps: int = 20) -> Result:
        try:
            el, el_code = _resolve_element(self.d, selector, value)
            el.swipe(direction, steps=steps)
            code = f'{el_code}.swipe({direction!r}, steps={steps})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def element_screenshot(self, selector: str, value: str, path: str) -> Result:
        try:
            el, el_code = _resolve_element(self.d, selector, value)
            img = el.screenshot()
            img.save(path)
            code = f'{el_code}.screenshot()'
            return Result(success=True, code=code, output=path)
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── Gesture ───────────────────────────────────────────────────────────

    def swipe(
        self, sx: int | float, sy: int | float, ex: int | float, ey: int | float, duration: float | None = None
    ) -> Result:
        try:
            if duration is not None:
                self.d.swipe(sx, sy, ex, ey, duration)
                code = f'd.swipe({sx}, {sy}, {ex}, {ey}, {duration})'
            else:
                self.d.swipe(sx, sy, ex, ey)
                code = f'd.swipe({sx}, {sy}, {ex}, {ey})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def swipe_ext(self, direction: str, scale: float = 0.9) -> Result:
        try:
            self.d.swipe_ext(direction, scale=scale)
            code = f'd.swipe_ext({direction!r}, scale={scale})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def drag(self, sx: int, sy: int, ex: int, ey: int, duration: float | None = None) -> Result:
        try:
            if duration is not None:
                self.d.drag(sx, sy, ex, ey, duration)
                code = f'd.drag({sx}, {sy}, {ex}, {ey}, {duration})'
            else:
                self.d.drag(sx, sy, ex, ey)
                code = f'd.drag({sx}, {sy}, {ex}, {ey})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── Key / Screen ──────────────────────────────────────────────────────

    def press(self, key: str) -> Result:
        try:
            self.d.press(key)
            code = f'd.press({key!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def screen_on(self) -> Result:
        try:
            self.d.screen_on()
            return Result(success=True, code='d.screen_on()', output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def screen_off(self) -> Result:
        try:
            self.d.screen_off()
            return Result(success=True, code='d.screen_off()', output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def unlock(self) -> Result:
        try:
            self.d.unlock()
            return Result(success=True, code='d.unlock()', output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── Input / Clipboard ─────────────────────────────────────────────────

    def send_keys(self, text: str, *, clear: bool = False) -> Result:
        try:
            self.d.send_keys(text, clear=clear)
            code = f'd.send_keys({text!r}, clear={clear})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def clear_text(self) -> Result:
        try:
            self.d.clear_text()
            return Result(success=True, code='d.clear_text()', output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def get_clipboard(self) -> Result:
        try:
            content = self.d.clipboard
            return Result(success=True, code='d.clipboard', output=content or '')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def set_clipboard(self, text: str) -> Result:
        try:
            self.d.set_clipboard(text)
            code = f'd.set_clipboard({text!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── Screenshot / Hierarchy ────────────────────────────────────────────

    def screenshot(self, path: str) -> Result:
        try:
            self.d.screenshot(path)
            code = f'd.screenshot({path!r})'
            return Result(success=True, code=code, output=path)
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def dump_hierarchy(self, *, compressed: bool = False, pretty: bool = False) -> Result:
        try:
            xml = self.d.dump_hierarchy(compressed=compressed, pretty=pretty)
            code = f'd.dump_hierarchy(compressed={compressed}, pretty={pretty})'
            output = _parse_hierarchy(xml)
            return Result(success=True, code=code, output=output)
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def toast(self) -> Result:
        try:
            msg = self.d.toast.get_message(wait_timeout=5, default=None)
            return Result(success=True, code='d.toast.get_message(wait_timeout=5)', output=msg or '')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── Device / Orientation / Notification ───────────────────────────────

    def orientation(self) -> Result:
        try:
            o = self.d.orientation
            return Result(success=True, code='d.orientation', output=o)
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def set_orientation(self, orientation: str) -> Result:
        try:
            self.d.set_orientation(orientation)
            code = f'd.set_orientation({orientation!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def open_notification(self) -> Result:
        try:
            self.d.open_notification()
            return Result(success=True, code='d.open_notification()', output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def open_quick_settings(self) -> Result:
        try:
            self.d.open_quick_settings()
            return Result(success=True, code='d.open_quick_settings()', output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def shell(self, command: str) -> Result:
        try:
            result = self.d.shell(command)
            code = f'd.shell({command!r})'
            output = json.dumps({'exit_code': result.exit_code, 'output': result.output})
            return Result(success=True, code=code, output=output)
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── App info / current ────────────────────────────────────────────────

    def info(self) -> Result:
        try:
            info = self.d.info
            return Result(success=True, code='d.info', output=json.dumps(info))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def device_info(self) -> Result:
        try:
            device_info = self.d.device_info
            return Result(success=True, code='d.device_info', output=json.dumps(device_info))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def window_size(self) -> Result:
        try:
            size = self.d.window_size()
            return Result(success=True, code='d.window_size()', output=json.dumps(size))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_current(self) -> Result:
        try:
            app = self.d.app_current()
            return Result(success=True, code='d.app_current()', output=json.dumps(app))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def wait_activity(self, activity: str, timeout: int = 10) -> Result:
        try:
            found = self.d.wait_activity(activity, timeout=timeout)
            code = f'd.wait_activity({activity!r}, timeout={timeout})'
            return Result(success=True, code=code, output=json.dumps(found))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── App management ────────────────────────────────────────────────────

    def app_install(self, url_or_path: str) -> Result:
        try:
            self.d.app_install(url_or_path)
            code = f'd.app_install({url_or_path!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_uninstall(self, package: str) -> Result:
        try:
            result = self.d.app_uninstall(package)
            code = f'd.app_uninstall({package!r})'
            return Result(success=True, code=code, output=json.dumps(result))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_start(self, package: str, activity: str | None = None, *, stop: bool = False) -> Result:
        try:
            if activity:
                self.d.app_start(package, activity, stop=stop)
                code = f'd.app_start({package!r}, {activity!r}, stop={stop})'
            else:
                self.d.app_start(package, stop=stop)
                code = f'd.app_start({package!r}, stop={stop})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_stop(self, package: str) -> Result:
        try:
            self.d.app_stop(package)
            code = f'd.app_stop({package!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_stop_all(self, excludes: list[str] | None = None) -> Result:
        try:
            if excludes:
                self.d.app_stop_all(excludes=excludes)
                code = f'd.app_stop_all(excludes={excludes!r})'
            else:
                self.d.app_stop_all()
                code = 'd.app_stop_all()'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_clear(self, package: str) -> Result:
        try:
            self.d.app_clear(package)
            code = f'd.app_clear({package!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_info(self, package: str) -> Result:
        try:
            info = self.d.app_info(package)
            code = f'd.app_info({package!r})'
            return Result(success=True, code=code, output=json.dumps(info))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_list_running(self) -> Result:
        try:
            apps = self.d.app_list_running()
            return Result(success=True, code='d.app_list_running()', output=json.dumps(apps))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def app_wait(self, package: str, timeout: float = 20.0, *, front: bool = False) -> Result:
        try:
            pid = self.d.app_wait(package, timeout=timeout, front=front)
            code = f'd.app_wait({package!r}, timeout={timeout}, front={front})'
            return Result(success=True, code=code, output=json.dumps(pid))
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    # ── File transfer ─────────────────────────────────────────────────────

    def push(self, local_path: str, remote_path: str) -> Result:
        try:
            self.d.push(local_path, remote_path)
            code = f'd.push({local_path!r}, {remote_path!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))

    def pull(self, remote_path: str, local_path: str) -> Result:
        try:
            self.d.pull(remote_path, local_path)
            code = f'd.pull({remote_path!r}, {local_path!r})'
            return Result(success=True, code=code, output='')
        except Exception as e:  # noqa: BLE001
            return Result(success=False, code='', output=str(e))


def _add_selector_args(p, choices=None, *, require_y: bool = False) -> None:
    """Add the shared selector / value [y] positional arguments to a subparser."""
    p.add_argument('selector', choices=choices or _ELEMENT_SELECTOR_CHOICES, help='Type of selector to use')
    p.add_argument('value', help='Value for the selector (text, resource-id, xpath expression, etc.)')
    if require_y:
        p.add_argument('y', nargs='?', type=int, help='Y coordinate (required when selector is coords)')


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='u2cli',
        description='Uiautomator2 CLI — Control Android devices from the terminal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--serial', '-s', default=None, help='Serial number of the target device (optional)')
    cmd = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # ── Element interaction ────────────────────────────────────────────────
    p = cmd.add_parser('click', help='Tap an element or screen coordinate')
    _add_selector_args(p, choices=_ALL_SELECTOR_CHOICES, require_y=True)
    p.set_defaults(func=lambda a: CLI(a.serial).click(a.selector, a.value, a.y))

    p = cmd.add_parser('long-click', help='Long-press an element or screen coordinate')
    _add_selector_args(p, choices=_ALL_SELECTOR_CHOICES, require_y=True)
    p.add_argument('--duration', type=float, default=None, help='Press duration in seconds (coords only)')
    p.set_defaults(func=lambda a: CLI(a.serial).long_click(a.selector, a.value, a.y, a.duration))

    p = cmd.add_parser('double-click', help='Double-tap a screen coordinate')
    p.add_argument('x', type=int, help='X coordinate')
    p.add_argument('y', type=int, help='Y coordinate')
    p.add_argument('--duration', type=float, default=0.1, help='Interval between the two taps (default 0.1s)')
    p.set_defaults(func=lambda a: CLI(a.serial).double_click(a.x, a.y, a.duration))

    p = cmd.add_parser('get-text', help='Get text of an element')
    _add_selector_args(p)
    p.set_defaults(func=lambda a: CLI(a.serial).get_text(a.selector, a.value))

    p = cmd.add_parser('set-text', help='Set text of an editable element')
    _add_selector_args(p)
    p.add_argument('text', help='Text to set')
    p.set_defaults(func=lambda a: CLI(a.serial).set_text(a.selector, a.value, a.text))

    p = cmd.add_parser('element-clear-text', help='Clear text of an editable element')
    _add_selector_args(p)
    p.set_defaults(func=lambda a: CLI(a.serial).element_clear_text(a.selector, a.value))

    p = cmd.add_parser('exists', help='Check whether an element exists on screen')
    _add_selector_args(p)
    p.set_defaults(func=lambda a: CLI(a.serial).exists(a.selector, a.value))

    p = cmd.add_parser('element-info', help='Get detailed info of an element')
    _add_selector_args(p)
    p.set_defaults(func=lambda a: CLI(a.serial).element_info(a.selector, a.value))

    p = cmd.add_parser('element-swipe', help='Swipe from the center of an element towards its edge')
    _add_selector_args(p)
    p.add_argument('direction', choices=['left', 'right', 'up', 'down'], help='Swipe direction')
    p.add_argument('--steps', type=int, default=20, help='Number of swipe steps (default 20)')
    p.set_defaults(func=lambda a: CLI(a.serial).element_swipe(a.selector, a.value, a.direction, a.steps))

    p = cmd.add_parser('element-screenshot', help='Take a screenshot of a specific element')
    _add_selector_args(p)
    p.add_argument('output', help='Local file path to save the screenshot')
    p.set_defaults(func=lambda a: CLI(a.serial).element_screenshot(a.selector, a.value, a.output))

    # ── Gesture ───────────────────────────────────────────────────────────
    p = cmd.add_parser('swipe', help='Swipe from one coordinate to another')
    p.add_argument('sx', type=_coord, help='Start X (pixels or 0–1 ratio)')
    p.add_argument('sy', type=_coord, help='Start Y (pixels or 0–1 ratio)')
    p.add_argument('ex', type=_coord, help='End X (pixels or 0–1 ratio)')
    p.add_argument('ey', type=_coord, help='End Y (pixels or 0–1 ratio)')
    p.add_argument('--duration', type=float, default=None, help='Swipe duration in seconds')
    p.set_defaults(func=lambda a: CLI(a.serial).swipe(a.sx, a.sy, a.ex, a.ey, a.duration))

    p = cmd.add_parser('swipe-ext', help='Swipe in a direction across the screen')
    p.add_argument('direction', choices=['left', 'right', 'up', 'down'], help='Swipe direction')
    p.add_argument('--scale', type=float, default=0.9, help='Swipe distance as fraction of screen (default 0.9)')
    p.set_defaults(func=lambda a: CLI(a.serial).swipe_ext(a.direction, a.scale))

    p = cmd.add_parser('drag', help='Drag from one coordinate to another')
    p.add_argument('sx', type=int, help='Start X')
    p.add_argument('sy', type=int, help='Start Y')
    p.add_argument('ex', type=int, help='End X')
    p.add_argument('ey', type=int, help='End Y')
    p.add_argument('--duration', type=float, default=None, help='Drag duration in seconds')
    p.set_defaults(func=lambda a: CLI(a.serial).drag(a.sx, a.sy, a.ex, a.ey, a.duration))

    # ── Key / Screen ──────────────────────────────────────────────────────
    p = cmd.add_parser('press', help='Press a hardware or soft key')
    p.add_argument('key', help='Key name (home, back, menu, power, volume_up, volume_down, enter, delete, etc.)')
    p.set_defaults(func=lambda a: CLI(a.serial).press(a.key))

    p = cmd.add_parser('screen-on', help='Turn the screen on')
    p.set_defaults(func=lambda a: CLI(a.serial).screen_on())

    p = cmd.add_parser('screen-off', help='Turn the screen off')
    p.set_defaults(func=lambda a: CLI(a.serial).screen_off())

    p = cmd.add_parser('unlock', help='Unlock the device screen')
    p.set_defaults(func=lambda a: CLI(a.serial).unlock())

    # ── Input / Clipboard ─────────────────────────────────────────────────
    p = cmd.add_parser('send-keys', help='Send text input to the focused field')
    p.add_argument('text', help='Text to type')
    p.add_argument('--clear', action='store_true', help='Clear existing text before typing')
    p.set_defaults(func=lambda a: CLI(a.serial).send_keys(a.text, clear=a.clear))

    p = cmd.add_parser('clear-text', help='Clear all text in the currently focused input field')
    p.set_defaults(func=lambda a: CLI(a.serial).clear_text())

    p = cmd.add_parser('get-clipboard', help='Get clipboard content')
    p.set_defaults(func=lambda a: CLI(a.serial).get_clipboard())

    p = cmd.add_parser('set-clipboard', help='Set clipboard content')
    p.add_argument('text', help='Text to put in the clipboard')
    p.set_defaults(func=lambda a: CLI(a.serial).set_clipboard(a.text))

    # ── Screenshot / Hierarchy ────────────────────────────────────────────
    p = cmd.add_parser('screenshot', help='Take a screenshot and save to a local file')
    p.add_argument('output', help='Local file path (e.g., screen.png)')
    p.set_defaults(func=lambda a: CLI(a.serial).screenshot(a.output))

    p = cmd.add_parser('dump-hierarchy', help='Dump the UI hierarchy as XML')
    p.add_argument('--compressed', action='store_true', help='Include non-important nodes')
    p.add_argument('--pretty', action='store_true', help='Pretty-print the XML output')
    p.set_defaults(func=lambda a: CLI(a.serial).dump_hierarchy(compressed=a.compressed, pretty=a.pretty))

    p = cmd.add_parser('toast', help='Get the last displayed toast message (waits up to 5 s)')
    p.set_defaults(func=lambda a: CLI(a.serial).toast())

    # ── Device info ───────────────────────────────────────────────────────
    p = cmd.add_parser('info', help='Get UI-level device information')
    p.set_defaults(func=lambda a: CLI(a.serial).info())

    p = cmd.add_parser('device-info', help='Get detailed device information (brand, model, SDK, etc.)')
    p.set_defaults(func=lambda a: CLI(a.serial).device_info())

    p = cmd.add_parser('window-size', help='Get the physical screen size')
    p.set_defaults(func=lambda a: CLI(a.serial).window_size())

    p = cmd.add_parser('app-current', help='Get the package / activity currently in the foreground')
    p.set_defaults(func=lambda a: CLI(a.serial).app_current())

    p = cmd.add_parser('wait-activity', help='Wait until a given activity is in the foreground')
    p.add_argument('activity', help='Activity name (e.g., .MainActivity or com.example/.MainActivity)')
    p.add_argument('--timeout', type=float, default=10.0, help='Maximum wait time in seconds (default 10)')
    p.set_defaults(func=lambda a: CLI(a.serial).wait_activity(a.activity, a.timeout))

    p = cmd.add_parser('orientation', help='Get the current screen orientation')
    p.set_defaults(func=lambda a: CLI(a.serial).orientation())

    p = cmd.add_parser('set-orientation', help='Set the screen orientation')
    p.add_argument('orientation', choices=['natural', 'n', 'left', 'l', 'right', 'r'], help='Target orientation')
    p.set_defaults(func=lambda a: CLI(a.serial).set_orientation(a.orientation))

    p = cmd.add_parser('open-notification', help='Open the notification panel')
    p.set_defaults(func=lambda a: CLI(a.serial).open_notification())

    p = cmd.add_parser('open-quick-settings', help='Open the quick settings panel')
    p.set_defaults(func=lambda a: CLI(a.serial).open_quick_settings())

    p = cmd.add_parser('shell', help='Run an adb shell command on the device')
    p.add_argument('command', help='Shell command string to execute')
    p.set_defaults(func=lambda a: CLI(a.serial).shell(a.command))

    # ── App management ────────────────────────────────────────────────────
    p = cmd.add_parser('app-install', help='Install an APK from a URL or local path')
    p.add_argument('source', help='HTTP URL or local file path of the APK')
    p.set_defaults(func=lambda a: CLI(a.serial).app_install(a.source))

    p = cmd.add_parser('app-uninstall', help='Uninstall an app by package name')
    p.add_argument('package', help='Package name (e.g., com.example.app)')
    p.set_defaults(func=lambda a: CLI(a.serial).app_uninstall(a.package))

    p = cmd.add_parser('app-start', help='Start an app')
    p.add_argument('package', help='Package name')
    p.add_argument('--activity', default=None, help='Activity name to launch (optional)')
    p.add_argument('--stop', action='store_true', help='Stop the app before starting it')
    p.set_defaults(func=lambda a: CLI(a.serial).app_start(a.package, a.activity, stop=a.stop))

    p = cmd.add_parser('app-stop', help='Force-stop an app')
    p.add_argument('package', help='Package name')
    p.set_defaults(func=lambda a: CLI(a.serial).app_stop(a.package))

    p = cmd.add_parser('app-stop-all', help='Force-stop all running apps')
    p.add_argument(
        '--exclude',
        dest='excludes',
        action='append',
        default=None,
        metavar='PACKAGE',
        help='Package to spare (can be repeated)',
    )
    p.set_defaults(func=lambda a: CLI(a.serial).app_stop_all(a.excludes))

    p = cmd.add_parser('app-clear', help='Clear app data (equivalent to pm clear)')
    p.add_argument('package', help='Package name')
    p.set_defaults(func=lambda a: CLI(a.serial).app_clear(a.package))

    p = cmd.add_parser('app-info', help='Get app metadata (version, label, size, etc.)')
    p.add_argument('package', help='Package name')
    p.set_defaults(func=lambda a: CLI(a.serial).app_info(a.package))

    p = cmd.add_parser('app-list-running', help='List currently running app package names')
    p.set_defaults(func=lambda a: CLI(a.serial).app_list_running())

    p = cmd.add_parser('app-wait', help='Wait for an app to start running')
    p.add_argument('package', help='Package name')
    p.add_argument('--timeout', type=float, default=20.0, help='Maximum wait time in seconds (default 20)')
    p.add_argument('--front', action='store_true', help='Wait until the app is in the foreground')
    p.set_defaults(func=lambda a: CLI(a.serial).app_wait(a.package, a.timeout, front=a.front))

    # ── File transfer ─────────────────────────────────────────────────────
    p = cmd.add_parser('push', help='Push a local file to the device')
    p.add_argument('local', help='Local file path')
    p.add_argument('remote', help='Remote path on the device (file or directory)')
    p.set_defaults(func=lambda a: CLI(a.serial).push(a.local, a.remote))

    p = cmd.add_parser('pull', help='Pull a file from the device to the local machine')
    p.add_argument('remote', help='Remote file path on the device')
    p.add_argument('local', help='Local destination path')
    p.set_defaults(func=lambda a: CLI(a.serial).pull(a.remote, a.local))

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    result = args.func(args)
    print(
        json.dumps(
            {
                'success': result.success,
                'code': result.code,
                'output': result.output,
            },
            ensure_ascii=False,
        )
    )


if __name__ == '__main__':
    main()
