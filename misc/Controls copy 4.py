import wx
import pyautogui
from PIL import Image, ImageDraw
import io
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)
class MonitorSelectionDialog(wx.Dialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.SetTitle("Select Monitor")
        self.SetSize((500, 250))  # Increase size for better button visibility

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.radio_box = None
        self.monitor_choices = []

        num_displays = wx.Display.GetCount()
        for i in range(num_displays):
            display = wx.Display(i)
            geometry = display.GetGeometry()
            self.monitor_choices.append(f"Monitor {i + 1}: {geometry.GetSize()}")

        if not self.monitor_choices:
            wx.MessageBox("No monitors detected!", "Error", wx.OK | wx.ICON_ERROR)
            self.EndModal(wx.ID_CANCEL)
            return

        self.radio_box = wx.RadioBox(
            panel,
            label="Choose a monitor:",
            choices=self.monitor_choices,
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        vbox.Add(self.radio_box, flag=wx.ALL | wx.EXPAND, border=10)

        # Button sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.ok_button = wx.Button(panel, wx.ID_OK, "OK", size=(100, 40))  # Increased size
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        button_sizer.Add(self.ok_button, flag=wx.ALL | wx.ALIGN_CENTER, border=10)

        vbox.Add(button_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        panel.SetSizer(vbox)
        vbox.Fit(panel)  # Ensure the panel's size fits the content
        self.Layout()  # Ensure layout updates correctly

        # Set OK button as the default button
        self.ok_button.SetDefault()

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)




import wx
import mss

import wx
import mss
from PIL import Image, ImageDraw

import wx
import mss
from PIL import Image, ImageDraw


class ScreenshotOverlay(wx.Frame):
    def __init__(self, callback, monitor_index, coordinates_frame, parent=None, style=wx.NO_BORDER):
        super().__init__(parent, style=style)

        self.callback = callback
        self.monitor_index = monitor_index
        self.coordinates_frame = coordinates_frame  # Store CoordinatesFrame reference

        # Initialize attributes
        self.start_pos = None  # Starting position of the selection rectangle
        self.current_pos = None  # Current position of the mouse
        self.is_selecting = False  # Flag to track if the user is selecting

        # Screen dimensions setup
        with mss.mss() as sct:
            monitor = sct.monitors[monitor_index]
            self.screen_width = monitor["width"]
            self.screen_height = monitor["height"]
            self.monitor_left = monitor["left"]
            self.monitor_top = monitor["top"]

        # Set frame size to match the monitor
        self.SetSize((self.screen_width, self.screen_height))
        self.SetPosition((self.monitor_left, self.monitor_top))
        self.SetTransparent(100)

        # Bind events
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.ShowFullScreen(True)
    def on_close(self, event):
        """Ensure the CoordinatesFrame is shown when the overlay is closed."""
        print("ScreenshotOverlay on_close called")  # Debug print
        if self.coordinates_frame:
            self.coordinates_frame.GetParent().Show()  # Ensure the main frame is shown
        self.Destroy()
        event.Skip()  # Propagate the close event
    def on_paint(self, event):
        """Draw the selection rectangle during the paint event."""
        if self.start_pos and self.current_pos:
            dc = wx.PaintDC(self)
            brush = wx.Brush(wx.Colour(0, 255, 0, 50))  # Transparent green brush
            pen = wx.Pen(wx.Colour(0, 255, 0), width=3)  # Green pen for the border
            dc.SetBrush(brush)
            dc.SetPen(pen)

            x1, y1 = self.start_pos
            x2, y2 = self.current_pos
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            dc.DrawRectangle(x, y, width, height)

    def on_left_down(self, event):
        """Start the selection rectangle."""
        self.start_pos = event.GetPosition()
        self.current_pos = self.start_pos
        self.is_selecting = True
        self.Refresh()  # Trigger a repaint to start drawing

    def on_mouse_move(self, event):
        """Update the selection rectangle as the mouse moves."""
        if self.is_selecting:
            self.current_pos = event.GetPosition()
            self.Refresh()  # Trigger a repaint to update the rectangle

    def on_left_up(self, event):
        """Finalize the selection and capture the screenshot."""
        self.is_selecting = False
        self.current_pos = event.GetPosition()
        self.capture_screenshot_with_selection()

    def capture_screenshot_with_selection(self):
        """Capture the full monitor with the green rectangle."""
        if not self.start_pos or not self.current_pos:
            wx.MessageBox("No valid coordinates found.", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Calculate selection rectangle coordinates
        x1, y1 = self.start_pos
        x2, y2 = self.current_pos
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        if width == 0 or height == 0:
            wx.MessageBox("Selection area must have a width and height greater than zero.", "Error", wx.OK | wx.ICON_ERROR)
            self.Close()
            return

        # Capture the full monitor
        with mss.mss() as sct:
            monitor = {
                "top": self.monitor_top,
                "left": self.monitor_left,
                "width": self.screen_width,
                "height": self.screen_height,
            }
            screenshot = sct.grab(monitor)

            # Convert to PIL Image
            pil_image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # Draw the selection rectangle
            draw = ImageDraw.Draw(pil_image)
            draw.rectangle(
                [x + self.monitor_left, y + self.monitor_top, x + width + self.monitor_left, y + height + self.monitor_top],
                outline="green",
                width=5,
            )

            # Create a thumbnail of the full screen
            thumbnail = pil_image.copy()
            thumbnail.thumbnail((100, 100))

            # Pass coordinates and thumbnail to the callback
            coordinates = (x + self.monitor_left, y + self.monitor_top, width, height)
            self.callback(pil_image, thumbnail, coordinates)

            # Restore CoordinatesFrame and close overlay
            if self.coordinates_frame:
                self.coordinates_frame.Show()
            self.Close() 











