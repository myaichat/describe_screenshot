import wx
import pyautogui
from PIL import Image
import io


class ScreenshotOverlay(wx.Frame):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback
        self.SetTitle("Screenshot Selector")
        self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        self.SetWindowStyle(wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.FRAME_SHAPED)
        self.Maximize()

        self.SetTransparent(150)  # Semi-transparent overlay

        self.start_pos = None
        self.end_pos = None

        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_drag)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_left_down(self, event):
        self.start_pos = wx.GetMousePosition()
        self.end_pos = None
        self.Refresh()

    def on_left_up(self, event):
        self.end_pos = wx.GetMousePosition()
        self.Refresh()

        if self.start_pos and self.end_pos:
            x1, y1 = self.start_pos
            x2, y2 = self.end_pos
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            self.callback((x, y, width, height))
            self.Close()

    def on_mouse_drag(self, event):
        if event.Dragging() and event.LeftIsDown() and self.start_pos:
            self.end_pos = wx.GetMousePosition()
            self.Refresh()

    def on_paint(self, event):
        if self.start_pos and self.end_pos:
            x1, y1 = self.start_pos
            x2, y2 = self.end_pos
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            dc = wx.PaintDC(self)
            pen = wx.Pen(wx.Colour(0, 255, 0), width=2, style=wx.PENSTYLE_SOLID)
            brush = wx.Brush(wx.Colour(0, 255, 0, 50))
            dc.SetPen(pen)
            dc.SetBrush(brush)
            dc.DrawRectangle(x, y, width, height)


class CoordinatesFrame(wx.Frame):
    def __init__(self, coordinates, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.coordinates = coordinates
        self.callback = callback
        self.screenshot_bitmap = None

        self.SetTitle("Screenshot Coordinates")
        self.SetSize((800, 400))

        panel = wx.Panel(self)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Canvas on the left
        self.canvas = wx.StaticBitmap(panel, size=(400, 300))
        self.canvas.SetBackgroundColour("white")
        hbox.Add(self.canvas, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)

        # Controls on the right
        control_panel = wx.BoxSizer(wx.VERTICAL)

        self.coord_label = wx.StaticText(panel, label=f"Selected Coordinates: {coordinates}")
        control_panel.Add(self.coord_label, flag=wx.ALL | wx.EXPAND, border=10)

        screenshot_btn = wx.Button(panel, label="Take Screenshot")
        screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_screenshot(self.coordinates))
        control_panel.Add(screenshot_btn, flag=wx.ALL | wx.CENTER, border=10)

        coord_btn = wx.Button(panel, label="Update Coordinates")
        coord_btn.Bind(wx.EVT_BUTTON, self.open_overlay)
        control_panel.Add(coord_btn, flag=wx.ALL | wx.CENTER, border=10)

        save_btn = wx.Button(panel, label="Save Screenshot")
        save_btn.Bind(wx.EVT_BUTTON, self.save_screenshot)
        control_panel.Add(save_btn, flag=wx.ALL | wx.CENTER, border=10)

        hbox.Add(control_panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)
        panel.SetSizer(hbox)

    def update_coordinates(self, new_coordinates):
        self.coordinates = new_coordinates
        self.coord_label.SetLabel(f"Selected Coordinates: {new_coordinates}")

    def open_overlay(self, event):
        self.Hide()
        overlay = ScreenshotOverlay(self.update_coordinates_callback, None, style=wx.NO_BORDER)
        overlay.ShowFullScreen(True)

    def update_coordinates_callback(self, new_coordinates):
        self.update_coordinates(new_coordinates)
        self.Show()

    def take_screenshot(self, coordinates):
        x, y, width, height = coordinates
        screenshot = pyautogui.screenshot(region=(x, y, width, height))

        # Convert screenshot to wx.Bitmap
        image_bytes = io.BytesIO()
        screenshot.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        wx_image = wx.Image(image_bytes, wx.BITMAP_TYPE_PNG)
        self.screenshot_bitmap = wx_image.ConvertToBitmap()

        # Display the screenshot on the canvas
        self.canvas.SetBitmap(self.screenshot_bitmap)

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
                image = wx.Image(self.screenshot_bitmap)
                image.SaveFile(filepath, wx.BITMAP_TYPE_PNG)
                wx.MessageBox(f"Screenshot saved to {filepath}", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No screenshot to save!", "Error", wx.OK | wx.ICON_ERROR)


class ScreenshotApp(wx.App):
    def OnInit(self):
        self.overlay = ScreenshotOverlay(self.show_coordinates_frame, None, style=wx.NO_BORDER)
        self.overlay.ShowFullScreen(True)
        return True

    def show_coordinates_frame(self, coordinates):
        self.coordinates_frame = CoordinatesFrame(coordinates, self.show_overlay, None)
        self.coordinates_frame.Show()

    def show_overlay(self, callback):
        self.coordinates_frame.Hide()
        overlay = ScreenshotOverlay(callback, None, style=wx.NO_BORDER)
        overlay.ShowFullScreen(True)


if __name__ == "__main__":
    app = ScreenshotApp()
    app.MainLoop()
