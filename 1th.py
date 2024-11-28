import wx
import os, time
import threading
import keyboard  # For global hotkeys
from PIL import Image
from pprint import pprint as pp
import wx.html2 
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)


import sys
sys.setrecursionlimit(10000)

import  openai
import base64
import io 
class ThumbnailToggleButton(wx.Panel):
    def __init__(self, parent, bitmap, label="Thumbnail", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.label = label
        self.enlarged_popup = None  # Popup window for enlargement
        self.stored_bitmap = bitmap  # Store the bitmap directly

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

            # Enlarge the bitmap for display while fitting the screen
            enlarged_bitmap, width, height = self.enlarge_bitmap(self.stored_bitmap, scale_factor=2)

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
    def enlarge_bitmap(bitmap, scale_factor=2):
        """Helper method to enlarge a wx.Bitmap while maintaining aspect ratio and fitting the screen."""
        if not bitmap.IsOk():
            raise ValueError("Invalid bitmap passed for enlargement.")
        image = bitmap.ConvertToImage()

        # Get original dimensions
        img_width, img_height = image.GetWidth(), image.GetHeight()

        # Get screen dimensions
        screen_width, screen_height = wx.GetDisplaySize()

        # Scale the image by the factor
        target_width = int(img_width * scale_factor)
        target_height = int(img_height * scale_factor)

        # Ensure the image fits within the screen dimensions
        if target_width > screen_width or target_height > screen_height:
            width_ratio = screen_width / target_width
            height_ratio = screen_height / target_height
            scale_ratio = min(width_ratio, height_ratio)

            target_width = int(target_width * scale_ratio)
            target_height = int(target_height * scale_ratio)

        # Scale the image
        image = image.Scale(target_width, target_height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image), target_width, target_height






class MyApp(wx.App):
    def OnInit(self):
        frame = wx.Frame(None, title="Thumbnail Hover Example", size=(600, 400))
        panel = wx.Panel(frame)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Load an example bitmap
        if not os.path.exists('test.jpg'):
            wx.MessageBox("test.jpg not found in the current directory!", "Error", wx.ICON_ERROR)
            return False
        bmp = wx.Bitmap('test.jpg', wx.BITMAP_TYPE_JPEG)
        if not bmp.IsOk():
            wx.MessageBox("Failed to load bitmap!", "Error", wx.ICON_ERROR)
            return False

        bmp = wx.Bitmap('test.jpg', wx.BITMAP_TYPE_JPEG)

        # Create and add ThumbnailToggleButton
        thumbnail_button = ThumbnailToggleButton(panel, bitmap=bmp, label="Example Thumbnail")
        sizer.Add(thumbnail_button, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
