import wx
import pyautogui
from PIL import Image
import io
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from include.Controls import MonitorSelectionDialog, ScreenshotOverlay, CoordinatesFrame


import threading
import keyboard  # For global hotkeys

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
