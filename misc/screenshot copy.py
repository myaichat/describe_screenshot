import wx

import threading
import keyboard  # For global hotkeys
from PIL import Image
import io
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from include.Controls import MonitorSelectionDialog, ScreenshotOverlay



class CoordinatesPanel(wx.Panel):
    def __init__(self, parent, coordinates, callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.coordinates = coordinates
        self.callback = callback
        self.screenshot_bitmap = None
        self.canvas_size = (700, 600)  # Fixed canvas size

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Canvas
        self.canvas = wx.StaticBitmap(self, size=self.canvas_size)
        self.canvas.SetBackgroundColour("white")
        vbox.Add(self.canvas, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=5)

        # Coordinates label
        self.coord_label = wx.StaticText(self, label=f"Selected Coordinates: {coordinates}")
        vbox.Add(self.coord_label, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=5)

        # Buttons in a single row
        button_hbox = wx.BoxSizer(wx.HORIZONTAL)

        screenshot_btn = wx.Button(self, label="Take Screenshot")
        screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_screenshot(self.coordinates))
        button_hbox.Add(screenshot_btn, flag=wx.ALL, border=5)

        coord_btn = wx.Button(self, label="Update Coordinates")
        coord_btn.Bind(wx.EVT_BUTTON, self.open_overlay)
        button_hbox.Add(coord_btn, flag=wx.ALL, border=5)

        save_btn = wx.Button(self, label="Save Screenshot")
        save_btn.Bind(wx.EVT_BUTTON, self.save_screenshot)
        button_hbox.Add(save_btn, flag=wx.ALL, border=5)

        vbox.Add(button_hbox, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=5)

        self.SetSizer(vbox)
        wx.CallAfter(self.take_screenshot, self.coordinates)

    def update_coordinates(self, new_coordinates):
        self.coordinates = new_coordinates
        self.coord_label.SetLabel(f"Selected Coordinates: {new_coordinates}")

    def open_overlay(self, event):
        self.Hide()
        self.callback()

    def take_screenshot(self, coordinates):
        import mss
        x, y, width, height = coordinates
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            screenshot = sct.grab(monitor)  # Capture the screenshot

            # Convert the screenshot to a PIL image
            pil_image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # Resize the image to fit the canvas
            pil_image.thumbnail(self.canvas_size)

            # Convert the PIL image to wx.Image for display in the wx.StaticBitmap
            wx_image = wx.Image(*pil_image.size)
            wx_image.SetData(pil_image.convert("RGB").tobytes())
            self.screenshot_bitmap = wx_image.ConvertToBitmap()

            # Update the canvas with the new screenshot
            self.canvas.SetBitmap(self.screenshot_bitmap)
            self.Layout()
            self.Refresh()

    def save_screenshot(self, event):
        if self.screenshot_bitmap:
            save_dialog = wx.FileDialog(
                self,
                message="Save Screenshot",
                wildcard="PNG files (*.png)|*.png",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )

            if save_dialog.ShowModal() == wx.ID_OK:
                filepath = save_dialog.GetPath()
                pil_image = Image.open(io.BytesIO(self.screenshot_bitmap.ConvertToImage().GetDataBuffer()))
                pil_image.save(filepath, format="PNG")
                wx.MessageBox(f"Screenshot saved to {filepath}", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No screenshot to save!", "Error", wx.OK | wx.ICON_ERROR)


class CoordinatesFrame(wx.Frame):
    def __init__(self, coordinates, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetTitle("Screenshot Coordinates")
        self.SetSize((800, 1000))

        # Add the CoordinatesPanel
        self.panel = CoordinatesPanel(self, coordinates, callback)
        self.Center()

class ScreenshotApp(wx.App):
    def OnInit(self):
        try:
            print("Initializing App")
            self.coordinates_frame = None  # Reference to the CoordinatesFrame
            self.show_monitor_selection_dialog()

            # Start a global hotkey listener thread
            self.start_hotkey_listener()
            return True
        except Exception as e:
            wx.MessageBox(f"Error during initialization: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            return False

    def start_hotkey_listener(self):
        """Start a thread to listen for global hotkeys."""
        def listen_for_hotkey():
            keyboard.add_hotkey("ctrl+space", self.trigger_screenshot_hotkey)
            keyboard.wait()  # Keeps the listener running

        thread = threading.Thread(target=listen_for_hotkey, daemon=True)
        thread.start()

    def trigger_screenshot_hotkey(self):
        """Trigger the screenshot action when Ctrl+Space is pressed."""
        wx.CallAfter(self.update_existing_coordinates_frame)

    def update_existing_coordinates_frame(self):
        """Update the existing CoordinatesFrame with a new screenshot."""
        if self.coordinates_frame:
            # Coordinates for the screenshot; adjust as needed or make dynamic
            coordinates = self.coordinates_frame.coordinates
            self.coordinates_frame.take_screenshot(coordinates)
        else:
            # Handle case where CoordinatesFrame doesn't exist yet
            wx.MessageBox("CoordinatesFrame is not available!", "Error", wx.OK | wx.ICON_ERROR)


    def show_monitor_selection_dialog(self):
        dialog = MonitorSelectionDialog(None)
        dialog.CenterOnScreen()
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            selected_monitor = dialog.radio_box.GetSelection()
            dialog.Destroy()
            print(f"Selected Monitor: {selected_monitor}")
            self.show_overlay(selected_monitor)
        else:
            dialog.Destroy()
            self.ExitMainLoop()

    def show_overlay(self, monitor_index):
        try:
            print("Opening overlay...")
            self.overlay = ScreenshotOverlay(self.show_coordinates_frame, monitor_index, None, style=wx.NO_BORDER)
            self.overlay.Show()
        except Exception as e:
            wx.MessageBox(f"Error opening overlay: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def show_coordinates_frame(self, coordinates):
        try:
            print(f"Coordinates selected: {coordinates}")
            self.coordinates_frame = CoordinatesFrame(coordinates, self.show_monitor_selection_dialog, None)
            self.coordinates_frame.Center()
            self.coordinates_frame.Show()
        except Exception as e:
            wx.MessageBox(f"Error showing coordinates frame: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)


if __name__ == "__main__":
    app = ScreenshotApp()


    app.MainLoop()
