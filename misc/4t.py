import wx
import pyautogui

class ScreenshotOverlay(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetTitle("Screenshot Selector")
        self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        self.SetWindowStyle(wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.FRAME_SHAPED)
        self.Maximize()

        # Set transparency to make the overlay semi-transparent
        self.SetTransparent(150)  # Adjust the value (0-255) for desired transparency

        self.start_pos = None
        self.end_pos = None

        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_drag)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_left_down(self, event):
        # Capture the starting position
        self.start_pos = wx.GetMousePosition()
        self.end_pos = None
        self.Refresh()  # Trigger a repaint

    def on_left_up(self, event):
        # Capture the ending position and take a screenshot
        self.end_pos = wx.GetMousePosition()
        self.Refresh()  # Trigger a repaint

        if self.start_pos and self.end_pos:
            x1, y1 = self.start_pos
            x2, y2 = self.end_pos
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            self.take_screenshot(x, y, width, height)
            self.Close()

    def on_mouse_drag(self, event):
        # Update the selection rectangle as the mouse is dragged
        if event.Dragging() and event.LeftIsDown() and self.start_pos:
            self.end_pos = wx.GetMousePosition()
            self.Refresh()  # Trigger a repaint

    def on_paint(self, event):
        # Draw the selection rectangle on the screen
        if self.start_pos and self.end_pos:
            x1, y1 = self.start_pos
            x2, y2 = self.end_pos
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            dc = wx.PaintDC(self)
            pen = wx.Pen(wx.Colour(0, 255, 0), width=2, style=wx.PENSTYLE_SOLID)
            brush = wx.Brush(wx.Colour(0, 255, 0, 50))  # Semi-transparent brush for selection rectangle
            dc.SetPen(pen)
            dc.SetBrush(brush)
            dc.DrawRectangle(x, y, width, height)

    def take_screenshot(self, x, y, width, height):
        # Capture the screenshot of the selected area
        screenshot = pyautogui.screenshot(region=(x, y, width, height))

        # Save the screenshot to a file
        save_dialog = wx.FileDialog(
            self,
            message="Save Screenshot",
            wildcard="PNG files (*.png)|*.png",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )

        if save_dialog.ShowModal() == wx.ID_OK:
            filepath = save_dialog.GetPath()
            screenshot.save(filepath)
            wx.MessageBox(f"Screenshot saved to {filepath}", "Success", wx.OK | wx.ICON_INFORMATION)

        save_dialog.Destroy()


class ScreenshotApp(wx.App):
    def OnInit(self):
        overlay = ScreenshotOverlay(None, style=wx.NO_BORDER)
        overlay.ShowFullScreen(True)
        return True


if __name__ == "__main__":
    app = ScreenshotApp()
    app.MainLoop()
