import wx
import wx.adv
import pyautogui

class ScreenshotFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetTitle("Screenshot Tool")
        self.SetSize((400, 300))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        instructions = wx.StaticText(panel, label="Resize the window to the desired area, then press 'Take Screenshot'")
        vbox.Add(instructions, flag=wx.ALL | wx.EXPAND, border=10)

        screenshot_btn = wx.Button(panel, label="Take Screenshot")
        screenshot_btn.Bind(wx.EVT_BUTTON, self.on_screenshot)
        vbox.Add(screenshot_btn, flag=wx.ALL | wx.CENTER, border=10)

        panel.SetSizer(vbox)

    def on_screenshot(self, event):
        # Get the window's position and size relative to the screen
        x, y = self.GetScreenPosition()
        width, height = self.GetSize()

        # Take a screenshot of the specified region
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
        frame = ScreenshotFrame(None)
        frame.Show()
        return True

if __name__ == "__main__":
    app = ScreenshotApp()
    app.MainLoop()
