import wx
import pyautogui
from PIL import Image
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




class ScreenshotOverlay(wx.Frame):
    def __init__(self, callback, monitor_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.callback = callback
        self.monitor_index = monitor_index
        
        # Get selected monitor's geometry
        display = wx.Display(monitor_index)
        self.geometry = display.GetGeometry()
        if 1:

            print(f"Monitor {monitor_index}: {self.geometry}")

        
        self.SetSize(self.geometry.GetSize())
        self.SetPosition(self.geometry.GetTopLeft())
        self.SetWindowStyle(wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.FRAME_SHAPED)
        self.SetTransparent(150)
        
        self.start_pos = None
        self.current_pos = None
        
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_drag)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def get_relative_pos(self, screen_pos):
        client_pos = self.ScreenToClient(screen_pos)
        return (client_pos.x, client_pos.y)

    def on_left_down(self, event):
        self.start_pos = self.get_relative_pos(wx.GetMousePosition())
        self.current_pos = self.start_pos
        self.Refresh()

    def on_mouse_drag(self, event):
        if event.Dragging() and event.LeftIsDown() and self.start_pos:
            self.current_pos = self.get_relative_pos(wx.GetMousePosition())
            self.Refresh()

    def on_left_up(self, event):
        if self.start_pos and self.current_pos:
            x1, y1 = self.start_pos
            x2, y2 = self.current_pos
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # Convert back to screen coordinates
            screen_pos = self.ClientToScreen(wx.Point(x, y))
            
            self.callback((screen_pos.x, screen_pos.y, width, height))
            self.Close()

    def on_paint(self, event):
        if self.start_pos and self.current_pos:
            dc = wx.PaintDC(self)
            gc = wx.GraphicsContext.Create(dc)
            
            if gc:
                x1, y1 = self.start_pos
                x2, y2 = self.current_pos
                x = min(x1, x2)
                y = min(y1, y2)
                width = abs(x2 - x1)
                height = abs(y2 - y1)

                gc.SetBrush(wx.Brush(wx.Colour(0, 255, 0, 50)))
                gc.SetPen(wx.Pen(wx.Colour(0, 255, 0), 2))
                gc.DrawRectangle(x, y, width, height)




