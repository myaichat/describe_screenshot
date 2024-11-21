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

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Notebook for displaying screenshots
        self.notebook = wx.Notebook(self)
        vbox.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

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

    def clear_tabs(self):
        """Clear all tabs in the notebook."""
        while self.notebook.GetPageCount() > 0:
            self.notebook.DeletePage(0)

    def add_screenshot_tab(self, bitmap, label=None):
        """Add a new tab with a screenshot."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Display screenshot in a static bitmap
        canvas = wx.StaticBitmap(panel, bitmap=bitmap)
        sizer.Add(canvas, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        label = label or f"Screenshot {self.notebook.GetPageCount() + 1}"
        self.notebook.AddPage(panel, label)
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)

    def take_screenshot(self, coordinates, return_bitmap=False):
        import mss
        x, y, width, height = coordinates
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            screenshot = sct.grab(monitor)

            # Convert to PIL image
            pil_image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            pil_image.thumbnail((700, 600))  # Resize to fit notebook tabs

            # Convert to wx.Bitmap
            wx_image = wx.Image(*pil_image.size)
            wx_image.SetData(pil_image.convert("RGB").tobytes())
            bitmap = wx_image.ConvertToBitmap()

            # Optionally return bitmap
            if return_bitmap:
                return bitmap

            # Add screenshot to a tab
            self.add_screenshot_tab(bitmap)

    def save_screenshot(self, event):
        if self.notebook.GetPageCount() == 0:
            wx.MessageBox("No screenshots to save!", "Error", wx.OK | wx.ICON_ERROR)
            return

        save_dialog = wx.FileDialog(
            self,
            message="Save Screenshot",
            wildcard="PNG files (*.png)|*.png",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )

        if save_dialog.ShowModal() == wx.ID_OK:
            filepath = save_dialog.GetPath()
            active_page = self.notebook.GetCurrentPage()
            canvas = active_page.GetChildren()[0]  # StaticBitmap on the panel
            bitmap = canvas.GetBitmap()

            pil_image = Image.open(io.BytesIO(bitmap.ConvertToImage().GetDataBuffer()))
            pil_image.save(filepath, format="PNG")
            wx.MessageBox(f"Screenshot saved to {filepath}", "Success", wx.OK | wx.ICON_INFORMATION)



    def update_coordinates(self, new_coordinates):
        self.coordinates = new_coordinates
        self.coord_label.SetLabel(f"Selected Coordinates: {new_coordinates}")

    def open_overlay(self, event):
        self.Hide()
        self.callback()

    def _take_screenshot(self, coordinates, return_bitmap=False):
        import mss
        x, y, width, height = coordinates
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            screenshot = sct.grab(monitor)

            # Convert to PIL image
            pil_image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            pil_image.thumbnail(self.canvas_size)

            # Convert to wx.Image
            wx_image = wx.Image(*pil_image.size)
            wx_image.SetData(pil_image.convert("RGB").tobytes())
            self.screenshot_bitmap = wx_image.ConvertToBitmap()

            # Update UI
            self.canvas.SetBitmap(self.screenshot_bitmap)
            self.Layout()
            self.Refresh()

            if return_bitmap:
                return self.screenshot_bitmap




class CoordinatesFrame(wx.Frame):
    def __init__(self, coordinates, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize coordinates
        self.coordinates = coordinates  # Set coordinates here
        self.callback = callback
        self.screenshot_bitmap = None
        self.canvas_size = (700, 600)  # Fixed canvas size

        self.SetTitle("Screenshot Coordinates")
        self.SetSize((800, 1000))

        # Add the CoordinatesPanel
        self.panel = CoordinatesPanel(self, coordinates, callback)
        self.Center()


import threading
import keyboard  # For global hotkeys


class ScreenshotApp(wx.App):
    def OnInit(self):
        try:
            self.coordinates_frame = None
            self.screenshot_group = []  # List to store grouped screenshots
            self.grouping_mode = False  # Flag to indicate grouping mode

            print("Initializing App")
            self.show_monitor_selection_dialog()

            # Start global hotkey listener thread
            self.start_hotkey_listener()
            return True
        except Exception as e:
            wx.MessageBox(f"Error during initialization: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            return False

    def start_hotkey_listener(self):
        """Start a thread to listen for global hotkeys."""
        def listen_for_hotkey():
            keyboard.add_hotkey("ctrl+space", self.trigger_single_screenshot)
            keyboard.add_hotkey("ctrl+enter", self.start_or_add_to_group)
            keyboard.add_hotkey("ctrl+shift", self.end_group)
            keyboard.wait()  # Keeps the listener running

        thread = threading.Thread(target=listen_for_hotkey, daemon=True)
        thread.start()

    def trigger_single_screenshot(self):
        """Trigger a single screenshot action."""
        wx.CallAfter(self.capture_single_screenshot)

    def start_or_add_to_group(self):
        """Start a new group or add to the current group."""
        wx.CallAfter(self.add_to_group)

    def end_group(self):
        """End the grouping and process the screenshots in the group."""
        wx.CallAfter(self.process_group)

    def capture_single_screenshot(self):
        """Capture a single screenshot and display it."""
        if self.coordinates_frame:
            coordinates = self.coordinates_frame.coordinates
            self.coordinates_frame.panel.take_screenshot(coordinates)
        else:
            wx.MessageBox("CoordinatesFrame is not available!", "Error", wx.OK | wx.ICON_ERROR)

    def add_to_group(self):
        """Add a screenshot to the current group."""
        if not self.grouping_mode:
            self.grouping_mode = True
            if self.coordinates_frame:
                self.coordinates_frame.panel.clear_tabs()  # Clear existing tabs for new group
            self.screenshot_group = []  # Start a new group

        if self.coordinates_frame and hasattr(self.coordinates_frame.panel, "take_screenshot"):
            coordinates = self.coordinates_frame.coordinates  # Access coordinates
            bitmap = self.coordinates_frame.panel.take_screenshot(coordinates, return_bitmap=True)
            self.screenshot_group.append(bitmap)
            self.coordinates_frame.panel.add_screenshot_tab(bitmap, f"Screenshot {len(self.screenshot_group)}")
        else:
            wx.MessageBox("CoordinatesPanel or its take_screenshot method is not available!", "Error", wx.OK | wx.ICON_ERROR)



    def process_group(self):
        """End the grouping and process the screenshots in the group."""
        if self.grouping_mode and self.screenshot_group:
            self.grouping_mode = False
            wx.MessageBox(f"Group finalized with {len(self.screenshot_group)} screenshots!",
                        "Group Completed", wx.OK | wx.ICON_INFORMATION)
            self.screenshot_group = []  # Clear the group
            if self.coordinates_frame:
                self.coordinates_frame.panel.clear_tabs()  # Clear tabs after finalizing group
        else:
            wx.MessageBox("No group is currently active.", "Group Error", wx.OK | wx.ICON_ERROR)


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
            wx.CallAfter(self.coordinates_frame.panel.take_screenshot,coordinates)
        except Exception as e:
            wx.MessageBox(f"Error showing coordinates frame: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)



if __name__ == "__main__":
    app = ScreenshotApp()


    app.MainLoop()
