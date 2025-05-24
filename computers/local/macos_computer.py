import base64
import io
import time
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Literal
import pyautogui
import psutil
from PIL import Image
from ..computer import Computer


class MacOSComputer:
    """Native macOS computer automation using PyAutoGUI and system APIs."""
    
    # Target resolution for scaled screenshots (same as mac_computer_use)
    SCALE_TARGET_WIDTH = 1366
    SCALE_TARGET_HEIGHT = 768
    
    def __init__(self):
        """Initialize macOS computer automation."""
        # Check for required accessibility permissions
        if not self._check_accessibility_permissions():
            self._request_accessibility_permissions()
        
        # Configure PyAutoGUI for safety
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Small delay between actions
        
        # Get actual screen dimensions from PyAutoGUI
        self._width, self._height = pyautogui.size()
        
        # Calculate scaling factors for coordinate transformation
        # When AI sends coordinates, they're in scaled space and need to be scaled up
        self._x_scale_factor = self._width / self.SCALE_TARGET_WIDTH
        self._y_scale_factor = self._height / self.SCALE_TARGET_HEIGHT
        
        print(f"Screen dimensions: {self._width}x{self._height}")
        print(f"Screenshot scaling: {self.SCALE_TARGET_WIDTH}x{self.SCALE_TARGET_HEIGHT}")
        print(f"Coordinate scale factors: {self._x_scale_factor:.2f}x{self._y_scale_factor:.2f}")
    
    def get_environment(self) -> Literal["windows", "mac", "linux", "browser"]:
        """Return the environment type."""
        return "mac"
    
    def get_dimensions(self) -> tuple[int, int]:
        """Get screen dimensions - returns actual screen size."""
        return self._width, self._height
    
    def _scale_coordinates_from_ai(self, x: int, y: int) -> tuple[int, int]:
        """Scale coordinates from AI (scaled screenshot space) to actual screen space."""
        # AI sends coordinates based on scaled screenshot (1366x768)
        # We need to scale them up to actual screen dimensions
        actual_x = int(x * self._x_scale_factor)
        actual_y = int(y * self._y_scale_factor)
        return actual_x, actual_y
    
    def screenshot(self) -> str:
        """Take a screenshot and return as base64 encoded string."""
        # Take screenshot using PyAutoGUI
        screenshot = pyautogui.screenshot()
        
        # Scale down to target resolution for efficiency
        # This matches what mac_computer_use does
        scaled_screenshot = screenshot.resize(
            (self.SCALE_TARGET_WIDTH, self.SCALE_TARGET_HEIGHT),
            Image.Resampling.LANCZOS
        )
        
        # Convert to base64
        buffer = io.BytesIO()
        scaled_screenshot.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at the specified coordinates."""
        # Validate coordinates against scaled screenshot dimensions
        if not (0 <= x <= self.SCALE_TARGET_WIDTH and 0 <= y <= self.SCALE_TARGET_HEIGHT):
            raise ValueError(f"Coordinates ({x}, {y}) are outside scaled bounds {self.SCALE_TARGET_WIDTH}x{self.SCALE_TARGET_HEIGHT}")
        
        # Scale coordinates from AI space to actual screen space
        actual_x, actual_y = self._scale_coordinates_from_ai(x, y)
        
        # Map button names
        button_map = {
            "left": "left",
            "right": "right", 
            "middle": "middle"
        }
        
        if button not in button_map:
            raise ValueError(f"Unknown button: {button}")
        
        pyautogui.click(actual_x, actual_y, button=button_map[button])
    
    def double_click(self, x: int, y: int) -> None:
        """Double-click at the specified coordinates."""
        if not (0 <= x <= self.SCALE_TARGET_WIDTH and 0 <= y <= self.SCALE_TARGET_HEIGHT):
            raise ValueError(f"Coordinates ({x}, {y}) are outside scaled bounds {self.SCALE_TARGET_WIDTH}x{self.SCALE_TARGET_HEIGHT}")
        
        # Scale coordinates from AI space to actual screen space
        actual_x, actual_y = self._scale_coordinates_from_ai(x, y)
        pyautogui.doubleClick(actual_x, actual_y)
    
    def scroll(self, x: int = None, y: int = None, direction: str = "down", amount: int = 5) -> None:
        """Scroll at the specified coordinates or current position."""
        # Handle both old and new scroll API formats
        if isinstance(x, str):  # New format: scroll(direction="down", amount=5)
            direction = x
            amount = y if y is not None else 5
            x = None
            y = None
        
        # If coordinates provided, move there first
        if x is not None and y is not None:
            if not (0 <= x <= self.SCALE_TARGET_WIDTH and 0 <= y <= self.SCALE_TARGET_HEIGHT):
                raise ValueError(f"Coordinates ({x}, {y}) are outside scaled bounds {self.SCALE_TARGET_WIDTH}x{self.SCALE_TARGET_HEIGHT}")
            actual_x, actual_y = self._scale_coordinates_from_ai(x, y)
            pyautogui.moveTo(actual_x, actual_y)
        
        # Scroll based on direction
        scroll_amount = amount if direction in ["down", "right"] else -amount
        if direction in ["up", "down"]:
            pyautogui.scroll(scroll_amount)
        elif direction in ["left", "right"]:
            pyautogui.hscroll(scroll_amount)
    
    def type(self, text: str) -> None:
        """Type the specified text."""
        pyautogui.typewrite(text)
    
    def key(self, *keys: str) -> None:
        """Press one or more keys."""
        for key in keys:
            pyautogui.press(key)
    
    def wait(self, seconds: float = 1.0) -> None:
        """Wait for the specified number of seconds."""
        time.sleep(seconds)
    
    def move(self, x: int, y: int) -> None:
        """Move mouse to the specified coordinates."""
        if not (0 <= x <= self.SCALE_TARGET_WIDTH and 0 <= y <= self.SCALE_TARGET_HEIGHT):
            raise ValueError(f"Coordinates ({x}, {y}) are outside scaled bounds {self.SCALE_TARGET_WIDTH}x{self.SCALE_TARGET_HEIGHT}")
        
        # Scale coordinates from AI space to actual screen space
        actual_x, actual_y = self._scale_coordinates_from_ai(x, y)
        pyautogui.moveTo(actual_x, actual_y)
    
    def mouse_move(self, x: int, y: int) -> None:
        """Alias for move() to match OpenAI CUA action names."""
        return self.move(x, y)
    
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
            if not (0 <= x <= self.SCALE_TARGET_WIDTH and 0 <= y <= self.SCALE_TARGET_HEIGHT):
                raise ValueError(f"Coordinates ({x}, {y}) are outside scaled bounds {self.SCALE_TARGET_WIDTH}x{self.SCALE_TARGET_HEIGHT}")
        
        # Convert first point and start drag
        start_point = path[0]
        start_x, start_y = self._scale_coordinates_from_ai(start_point['x'], start_point['y'])
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown()
        
        try:
            # Drag through all subsequent points
            for point in path[1:]:
                actual_x, actual_y = self._scale_coordinates_from_ai(point['x'], point['y'])
                pyautogui.moveTo(actual_x, actual_y)
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