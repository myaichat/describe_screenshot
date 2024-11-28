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
        self.SetSize((500, 350))

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
        
        # Create horizontal box for radio box and auto execute
        
        
        self.radio_box = wx.RadioBox(
            panel,
            label="Choose a monitor:",
            choices=self.monitor_choices,
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        vbox.Add(self.radio_box, flag=wx.ALL | wx.EXPAND, border=10)
        

        
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.mode_radio = wx.RadioBox(
            panel,
            label="Select Mode:",
            choices=["Live", "Mock"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS
        )
        hbox.Add(self.mode_radio, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=10)  
        # Auto Execute checkbox
        self.auto_execute = wx.CheckBox(panel, label="Auto Execute")
        self.auto_execute.SetValue(True)
        hbox.Add(self.auto_execute, flag=wx.ALIGN_CENTER_VERTICAL)        
        vbox.Add(hbox, flag=wx.ALL | wx.EXPAND, border=10)
        ok_button = wx.Button(panel, wx.ID_OK, "OK", size=(200, 50))
        ok_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        vbox.Add(ok_button, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        panel.SetSizer(vbox)
        self.Layout()

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)

    def on_key_press(self, event):
        key_code = event.GetKeyCode()
        if event.AltDown():
            if key_code == wx.WXK_LEFT:
                self.mode_radio.SetSelection(0)
            elif key_code == wx.WXK_RIGHT:
                self.mode_radio.SetSelection(1)
            elif key_code == wx.WXK_RETURN:  # Alt+Enter
                self.auto_execute.SetValue(not self.auto_execute.GetValue())                
        elif key_code == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK)
        event.Skip()

    def get_mock_state(self):
        return self.mode_radio.GetSelection() == 1

    def get_auto_execute(self):
        return self.auto_execute.GetValue()


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
            print("Showing CoordinatesFrame")  # Debug print
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
                print("Showing CoordinatesFrame 222")  # Debug print
                self.coordinates_frame.Show()
                self.coordinates_frame.panel.on_show_webview(button=self.coordinates_frame.panel.show_webview_btn)
            self.Close() 





class ThumbnailToggleButton(wx.Panel):
    def __init__(self, parent, bitmap, orig_bitmap, label="Thumbnail", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.label = label
        self.enlarged_popup = None  # Popup window for enlargement
        self.stored_bitmap = orig_bitmap  # Store the bitmap directly

        self.SetBackgroundColour(wx.NullColour)  # Default background color

        # Create a sizer for the panel
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the toggle button
        self.button = wx.ToggleButton(self, label="")
        self.button.SetBitmap(bitmap)  # Assign bitmap
        self.button.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle)
        self.sizer.Add(self.button, 1, wx.EXPAND)

        self.SetSizer(self.sizer)

        # Bind hover events for enlargement
        self.button.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
        self.button.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def on_toggle(self, event=None):
        """Handle toggle state changes."""
        if self.button.GetValue():
            self.SetBackgroundColour(wx.Colour(255, 0, 0))  # Red border
        else:
            self.SetBackgroundColour(wx.NullColour)  # Default border
        self.Refresh()
        self.Update()

    def on_hover(self, event):
        """Show an enlarged version of the thumbnail on hover."""
        if not self.enlarged_popup:
            if not self.stored_bitmap.IsOk():  # Validate stored bitmap
                print("Invalid bitmap detected during hover!")
                return

            # Get mouse position and create popup
            mouse_x, mouse_y = wx.GetMousePosition()
            self.enlarged_popup = wx.PopupWindow(self)

            # Enlarge the bitmap for display while fitting 50% of the screen
            enlarged_bitmap, width, height = self.enlarge_bitmap(self.stored_bitmap, monitor_scale=0.5)

            # Create a panel to hold the enlarged image
            panel = wx.Panel(self.enlarged_popup)
            panel.SetSize((width, height))  # Set panel size to match bitmap
            panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # Set panel background

            # Add the enlarged bitmap to the panel
            static_bitmap = wx.StaticBitmap(panel, bitmap=enlarged_bitmap)
            static_bitmap.SetSize((width, height))  # Ensure bitmap fills the panel

            # Ensure the popup is fully visible on the screen
            screen_width, screen_height = wx.GetDisplaySize()
            popup_x = min(mouse_x + 10, screen_width - width - 10)
            popup_y = min(mouse_y + 10, screen_height - height - 10)

            # Configure popup size and position
            self.enlarged_popup.SetSize((width, height))  # Match popup size to bitmap
            self.enlarged_popup.SetPosition((popup_x, popup_y))  # Offset popup slightly from pointer

            # Refresh and show the popup
            self.enlarged_popup.Layout()
            self.enlarged_popup.Show()






    def on_leave(self, event):
        """Hide the enlarged popup when the mouse leaves."""
        if self.enlarged_popup:
            self.enlarged_popup.Destroy()
            self.enlarged_popup = None

    
    @staticmethod
    def enlarge_bitmap(bitmap, monitor_scale=0.5):
        """Helper method to enlarge a wx.Bitmap while maintaining aspect ratio and fitting 50% of the screen."""
        if not bitmap.IsOk():
            raise ValueError("Invalid bitmap passed for enlargement.")
        image = bitmap.ConvertToImage()

        # Get original dimensions
        img_width, img_height = image.GetWidth(), image.GetHeight()

        # Get 50% of screen dimensions
        screen_width, screen_height = wx.GetDisplaySize()
        max_width = int(screen_width * monitor_scale)
        max_height = int(screen_height * monitor_scale)

        # Scale the image to fit within 50% of the screen
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale_ratio = min(width_ratio, height_ratio, 1)  # Ensure image is not upscaled

        target_width = int(img_width * scale_ratio)
        target_height = int(img_height * scale_ratio)

        # Scale the image
        image = image.Scale(target_width, target_height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image), target_width, target_height








class _ThumbnailToggleButton(wx.Panel):
    """A custom toggle button with a thumbnail, red border on toggle, and hover enlargement."""
    def __init__(self, parent, bitmap, label="Thumbnail", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent
        self.label = label
        self.enlarged_popup = None  # Popup window for enlargement

        self.SetBackgroundColour(wx.NullColour)  # Default background color

        # Create a sizer for the panel
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the toggle button
        self.button = wx.ToggleButton(self, label="")
        self.button.SetBitmap(bitmap)  # Set the bitmap for the button
        self.button.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle)
        self.sizer.Add(self.button, 1, wx.EXPAND)

        self.SetSizer(self.sizer)

        # Bind hover events for enlargement
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

    def on_toggle(self, event=None):
        """Handle toggle state changes."""
        if self.button.GetValue():
            # Button is pressed (add red border)
            self.SetBackgroundColour(wx.Colour(255, 0, 0))  # Red border
            self.button.SetBackgroundColour(wx.Colour(240, 240, 240))  # Optional: Distinct button background
        else:
            # Button is unpressed (remove red border)
            self.SetBackgroundColour(wx.NullColour)  # Default border
            self.button.SetBackgroundColour(wx.NullColour)  # Reset button background

        # Force a UI refresh for both the panel and the button
        self.Refresh()
        self.Update()
        self.button.Refresh()
        self.button.Update()

        # Update the status bar or any parent-level feedback
        parent_frame = self.GetParent().GetParent().GetParent()
        if self.button.GetValue():
            parent_frame.status_bar.SetStatusText(f"{self.label} selected (pressed)")
        else:
            parent_frame.status_bar.SetStatusText(f"{self.label} deselected")

    def on_hover(self, event):
        print("on_hover called")  # Debug print    
        """Show an enlarged version of the thumbnail on hover."""
        if not self.enlarged_popup:
            mouse_x, mouse_y = wx.GetMousePosition()  # Get mouse pointer position
            self.enlarged_popup = wx.PopupWindow(self, style=wx.BORDER_SIMPLE)
            panel = wx.Panel(self.enlarged_popup)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # Enlarge the bitmap for display
            enlarged_bitmap = self.enlarge_bitmap(self.button.GetBitmap(), size=(200, 200))
            static_bitmap = wx.StaticBitmap(panel, bitmap=enlarged_bitmap)
            sizer.Add(static_bitmap, 1, wx.EXPAND | wx.ALL, 5)
            panel.SetSizer(sizer)

            self.enlarged_popup.SetSize((200, 200))
            self.enlarged_popup.SetPosition((mouse_x + 10, mouse_y + 10))  # Offset the popup slightly from the pointer
            self.enlarged_popup.Show()

    def on_leave(self, event):
        """Hide the enlarged popup when the mouse leaves."""
        if self.enlarged_popup:
            self.enlarged_popup.Destroy()
            self.enlarged_popup = None

    @staticmethod
    def enlarge_bitmap(bitmap, size):
        """Helper method to enlarge a wx.Bitmap."""
        image = bitmap.ConvertToImage()
        image = image.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
        return image.ConvertToBitmap()





import wx


class ThumbnailScrollPanel(wx.ScrolledWindow):
    """A scrollable panel for displaying ThumbnailToggleButtons."""
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create a vertical sizer to hold the toggle buttons
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Set up the scrolling properties
        self.SetScrollRate(10, 10)
        self.SetSizer(self.sizer)

        # Dictionary to track the state of toggle buttons by their labels
        self.thumbnail_buttons = {}

    def add_thumbnail_button(self, orig_image, pil_image, label="Thumbnail"):
        """Add a new ThumbnailToggleButton to the scrollable panel."""
        # Convert PIL.Image to wx.Bitmap
        wx_image = wx.Image(pil_image.width, pil_image.height)
        wx_image.SetData(pil_image.convert("RGB").tobytes())
        bitmap = wx_image.ConvertToBitmap()

        wx_image = wx.Image(orig_image.width, orig_image.height)
        wx_image.SetData(orig_image.convert("RGB").tobytes())
        oring_bitmap = wx_image.ConvertToBitmap()


        # Create the toggle button with the converted bitmap
        toggle_button = ThumbnailToggleButton(self, bitmap=bitmap, orig_bitmap=oring_bitmap, label=label)
        self.sizer.Add(toggle_button, 0, wx.EXPAND | wx.ALL, 5)
        self.Layout()  # Refresh layout
        self.FitInside()  # Ensure the scrollable area fits the new content

        return toggle_button  # Return the created toggle button



    def on_thumbnail_button_toggle(self, event):
        """Handle thumbnail toggle button state changes."""
        clicked_button = event.GetEventObject()

        for label, button in self.thumbnail_buttons.items():
            if button == clicked_button:
                # Handle the toggled button (already toggling logic is in the button itself)
                wx.MessageBox(f"Button '{label}' toggled.", "Toggle Event", wx.OK)
                break
