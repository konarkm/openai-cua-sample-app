import base64
import io
import time
from typing import List, Dict, Literal
import pyautogui
import psutil
from PIL import Image
from ..computer import Computer


class MacOSComputer:
    """Native macOS computer automation using PyAutoGUI and system APIs."""
    
    def __init__(self):
        """Initialize macOS computer automation."""
        # Check for required accessibility permissions
        if not self._check_accessibility_permissions():
            self._request_accessibility_permissions()
        
        # Configure PyAutoGUI for safety
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Small delay between actions
        
        # Get screen dimensions
        self._width, self._height = pyautogui.size()
    
    def get_environment(self) -> Literal["windows", "mac", "linux", "browser"]:
        """Return the environment type."""
        return "mac"
    
    def get_dimensions(self) -> tuple[int, int]:
        """Get screen dimensions."""
        return self._width, self._height
    
    def screenshot(self) -> str:
        """Take a screenshot and return as base64 encoded string."""
        # Take screenshot using PyAutoGUI
        screenshot = pyautogui.screenshot()
        
        # Convert to base64
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at the specified coordinates."""
        # Validate coordinates
        if not (0 <= x <= self._width and 0 <= y <= self._height):
            raise ValueError(f"Coordinates ({x}, {y}) are outside screen bounds")
        
        # Map button names
        button_map = {
            "left": "left",
            "right": "right", 
            "middle": "middle"
        }
        
        if button not in button_map:
            raise ValueError(f"Unknown button: {button}")
        
        pyautogui.click(x, y, button=button_map[button])
    
    def double_click(self, x: int, y: int) -> None:
        """Double-click at the specified coordinates."""
        if not (0 <= x <= self._width and 0 <= y <= self._height):
            raise ValueError(f"Coordinates ({x}, {y}) are outside screen bounds")
        
        pyautogui.doubleClick(x, y)
    
    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        """Scroll at the specified coordinates."""
        if not (0 <= x <= self._width and 0 <= y <= self._height):
            raise ValueError(f"Coordinates ({x}, {y}) are outside screen bounds")
        
        # Move to position and scroll
        pyautogui.moveTo(x, y)
        
        # PyAutoGUI scroll: positive = up/right, negative = down/left
        if scroll_y != 0:
            pyautogui.scroll(scroll_y, x=x, y=y)
        if scroll_x != 0:
            pyautogui.hscroll(scroll_x, x=x, y=y)
    
    def type(self, text: str) -> None:
        """Type the specified text."""
        pyautogui.typewrite(text)
    
    def key(self, *keys: str) -> None:
        """Press one or more keys."""
        for key in keys:
            pyautogui.press(key)
    
    def wait(self, ms: int = 1000) -> None:
        """Wait for the specified number of milliseconds."""
        time.sleep(ms / 1000)
    
    def move(self, x: int, y: int) -> None:
        """Move mouse to the specified coordinates."""
        if not (0 <= x <= self._width and 0 <= y <= self._height):
            raise ValueError(f"Coordinates ({x}, {y}) are outside screen bounds")
        
        pyautogui.moveTo(x, y)
    
    def keypress(self, keys: List[str]) -> None:
        """Press the specified key combination."""
        if not keys:
            return
        
        # Map common key names to PyAutoGUI names
        key_map = {
            "cmd": "command",
            "ctrl": "ctrl", 
            "alt": "option",
            "shift": "shift",
            "enter": "enter",
            "return": "enter",
            "tab": "tab",
            "space": "space",
            "backspace": "backspace",
            "delete": "delete",
            "esc": "escape",
            "escape": "escape",
            "up": "up",
            "down": "down", 
            "left": "left",
            "right": "right",
            "home": "home",
            "end": "end",
            "pageup": "pageup",
            "pagedown": "pagedown"
        }
        
        # Convert keys to PyAutoGUI format
        mapped_keys = []
        for key in keys:
            mapped_key = key_map.get(key.lower(), key.lower())
            mapped_keys.append(mapped_key)
        
        # Execute key combination
        if len(mapped_keys) == 1:
            pyautogui.press(mapped_keys[0])
        else:
            pyautogui.hotkey(*mapped_keys)
    
    def drag(self, path: List[Dict[str, int]]) -> None:
        """Drag along the specified path."""
        if not path or len(path) < 2:
            raise ValueError("Path must contain at least 2 points")
        
        # Validate all coordinates
        for point in path:
            x, y = point.get('x', 0), point.get('y', 0)
            if not (0 <= x <= self._width and 0 <= y <= self._height):
                raise ValueError(f"Coordinates ({x}, {y}) are outside screen bounds")
        
        # Start drag from first point
        start_point = path[0]
        pyautogui.moveTo(start_point['x'], start_point['y'])
        pyautogui.mouseDown()
        
        try:
            # Drag through all subsequent points
            for point in path[1:]:
                pyautogui.moveTo(point['x'], point['y'])
                time.sleep(0.05)  # Small delay for smooth dragging
        finally:
            # Always release mouse button
            pyautogui.mouseUp()
    
    def get_current_url(self) -> str:
        """Get current URL - not applicable for native desktop automation."""
        return ""
    
    def get_running_applications(self) -> List[str]:
        """Get list of currently running applications."""
        apps = []
        for proc in psutil.process_iter(['name']):
            try:
                app_name = proc.info['name']
                if app_name and not app_name.startswith('.'):
                    apps.append(app_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(list(set(apps)))
    
    def get_active_window_title(self) -> str:
        """Get the title of the currently active window."""
        try:
            # Use AppleScript to get active window title
            import subprocess
            script = '''
            tell application "System Events"
                name of first application process whose frontmost is true
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return ""
    
    def focus_application(self, app_name: str) -> bool:
        """Focus/activate the specified application."""
        try:
            import subprocess
            script = f'''
            tell application "{app_name}"
                activate
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_accessibility_permissions(self) -> bool:
        """Check if the app has accessibility permissions."""
        # TODO: Implement actual accessibility permission checking
        # For now, assume permissions are granted
        return True
    
    def _request_accessibility_permissions(self) -> None:
        """Request accessibility permissions from the user."""
        # TODO: Implement permission request flow
        # Should guide user to System Preferences > Security & Privacy > Accessibility
        print("⚠️  Accessibility permissions required for macOS automation")
        print("Please grant accessibility access in System Preferences:")
        print("1. Open System Preferences > Security & Privacy > Accessibility")
        print("2. Click the lock to make changes")
        print("3. Add this application to the list")
        print("4. Restart the application")
        
        # TODO: Consider showing a native dialog or opening System Preferences automatically