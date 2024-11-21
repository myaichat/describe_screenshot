import wx
import os
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
        self.screenshot_groups = {}  # Dictionary to store groups of screenshots
        self.current_group = None

        # Main horizontal sizer for overall layout
        main_hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Vertical sizer for group list and buttons
        left_vbox = wx.BoxSizer(wx.VERTICAL)

        # List control for groups
        self.group_list = wx.ListBox(self, style=wx.LB_SINGLE)
        self.group_list.Bind(wx.EVT_LISTBOX, self.on_group_selected)
        left_vbox.Add(self.group_list, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons column
        button_vbox = wx.BoxSizer(wx.VERTICAL)

        # "Take Screenshot" button
        screenshot_btn = wx.Button(self, label="Take Screenshot")
        screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_single_screenshot())
        button_vbox.Add(screenshot_btn, flag=wx.ALL, border=5)

        # New "Take Group Screenshot" button
        group_screenshot_btn = wx.Button(self, label="Take Group Screenshot")
        group_screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_group_screenshot())
        button_vbox.Add(group_screenshot_btn, flag=wx.ALL, border=5)

        # New "End Group" button
        end_group_btn = wx.Button(self, label="End Group")
        end_group_btn.Bind(wx.EVT_BUTTON, lambda evt: self.end_group())
        button_vbox.Add(end_group_btn, flag=wx.ALL, border=5)

        # "Update Coordinates" button
        coord_btn = wx.Button(self, label="Update Coordinates")
        coord_btn.Bind(wx.EVT_BUTTON, self.open_overlay)
        button_vbox.Add(coord_btn, flag=wx.ALL, border=5)

        # "Save Screenshot" button
        save_btn = wx.Button(self, label="Save Screenshot")
        save_btn.Bind(wx.EVT_BUTTON, self.save_screenshot)
        button_vbox.Add(save_btn, flag=wx.ALL, border=5)

        # Add button_vbox to the left vertical layout
        left_vbox.Add(button_vbox, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # Add left_vbox to the main horizontal sizer
        main_hbox.Add(left_vbox, 0, wx.EXPAND | wx.ALL, 5)

        # Notebook for displaying screenshots
        self.notebook = wx.Notebook(self)
        main_hbox.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_hbox)

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

    def add_list_item(self, item_name):
        """Add an item to the group list."""
        self.group_list.Append(item_name)
        self.group_list.SetSelection(self.group_list.GetCount() - 1)

    def take_single_screenshot(self):
        """Take a single screenshot, clear the notebook, and add it as a new list item."""
        # Clear the notebook to reset the display
        self.clear_tabs()

        # Take the screenshot
        bitmap = self.take_screenshot(self.coordinates, return_bitmap=True)

        # Create a new list item for the screenshot
        new_item_name = f"Single Screenshot {self.group_list.GetCount() + 1}"
        self.add_list_item(new_item_name)

        # Add the screenshot to the group list and notebook
        self.screenshot_groups[new_item_name] = [bitmap]
        self.add_screenshot_tab(bitmap)

        # Update the status bar to indicate the action
        self.GetParent().status_bar.SetStatusText(f"Added a new single screenshot: '{new_item_name}'")


    def take_group_screenshot(self):
        """Start a new group or add a screenshot to the current group."""
        if self.current_group is None:
            # Start a new group if no active group exists
            group_name = f"Group {len(self.screenshot_groups) + 1}"
            self.add_group(group_name)

        # Take a screenshot and add it to the current group
        bitmap = self.take_screenshot(self.coordinates, return_bitmap=True)

        # Ensure the group exists in the dictionary
        if self.current_group in self.screenshot_groups:
            self.screenshot_groups[self.current_group].append(bitmap)
        else:
            self.screenshot_groups[self.current_group] = [bitmap]

        # Add the screenshot as a tab in the notebook
        self.add_screenshot_tab(bitmap)

        # Update the status bar
        parent_frame = self.GetParent()
        parent_frame.status_bar.SetStatusText(
            f"Added screenshot to '{self.current_group}'. Total: {len(self.screenshot_groups[self.current_group])}"
        )


    def end_group(self):
        """End the current group and finalize it."""
        if self.current_group:
            screenshots = len(self.screenshot_groups.get(self.current_group, []))
            # Update the status bar with the group completion message
            self.GetParent().status_bar.SetStatusText(
                f"Group '{self.current_group}' finalized with {screenshots} screenshots!"
            )
            self.current_group = None
        else:
            # Update the status bar with an error message
            self.GetParent().status_bar.SetStatusText("No group is currently active.")


    def take_screenshot(self, coordinates, return_bitmap=False):
        """Take a screenshot and optionally return the bitmap."""
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

            if return_bitmap:
                return bitmap



    def save_screenshot(self, event):
        # Use the currently selected group if there's no active group
        selected_group = self.group_list.GetStringSelection()

        if not selected_group or selected_group not in self.screenshot_groups:
            wx.MessageBox("No active or selected group with screenshots to save!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Open directory selection dialog
        dir_dialog = wx.DirDialog(
            self,
            message="Select a directory to save screenshots",
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        )

        if dir_dialog.ShowModal() == wx.ID_OK:
            base_dir = dir_dialog.GetPath()
            group_dir = os.path.join(base_dir, selected_group)

            # Create a subdirectory for the selected group
            if not os.path.exists(group_dir):
                os.makedirs(group_dir)

            screenshots = self.screenshot_groups[selected_group]
            if not screenshots:
                wx.MessageBox(f"No screenshots in the group '{selected_group}' to save!", "Error", wx.OK | wx.ICON_ERROR)
                return

            # Save each screenshot in the group directory
            for idx, bitmap in enumerate(screenshots):
                wx_image = bitmap.ConvertToImage()

                # Save the image to the group directory as PNG
                filepath = os.path.join(group_dir, f"screenshot_{idx + 1}.png")
                wx_image.SaveFile(filepath, wx.BITMAP_TYPE_PNG)

            #wx.MessageBox(f"All screenshots in group '{selected_group}' saved to {group_dir}", "Success", wx.OK | wx.ICON_INFORMATION)
            # Update the status bar
            self.GetParent().status_bar.SetStatusText(f"All screenshots in group '{selected_group}' saved to {group_dir}")
        else:
            #wx.MessageBox("Save operation cancelled.", "Info", wx.OK | wx.ICON_INFORMATION)
            self.GetParent().status_bar.SetStatusText("Save operation cancelled.")



    def on_group_selected(self, event):
        """Handle group selection from the list."""
        selected_group = self.group_list.GetStringSelection()
        if selected_group:
            self.current_group = selected_group
            self.clear_tabs()
            for bitmap in self.screenshot_groups[selected_group]:
                self.add_screenshot_tab(bitmap)

    def add_group(self, group_name):
        """Add a new screenshot group."""
        if group_name in self.screenshot_groups:
            # Avoid duplicate groups
            self.GetParent().status_bar.SetStatusText(f"Group '{group_name}' already exists.")
            return

        # Create a new group and add it to the list
        self.screenshot_groups[group_name] = []
        self.add_list_item(group_name)
        self.current_group = group_name
        self.clear_tabs()

        # Update the status bar
        self.GetParent().status_bar.SetStatusText(f"Started new group: '{group_name}'")


    def update_coordinates(self, new_coordinates):
        self.coordinates = new_coordinates

    def open_overlay(self, event):
        self.Hide()
        self.callback()






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

        # Add a status bar
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText("Ready")  # Default message



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
        """Capture a single screenshot and reset the notebook with it."""
        if self.coordinates_frame:
            panel = self.coordinates_frame.panel

            # Clear existing tabs
            panel.clear_tabs()

            # Take a single screenshot
            bitmap = panel.take_screenshot(panel.coordinates, return_bitmap=True)

            # Add the screenshot as a single tab
            panel.add_screenshot_tab(bitmap)

            # Add the screenshot to a new single screenshot list item
            new_item_name = f"Single Screenshot {panel.group_list.GetCount() + 1}"
            panel.add_list_item(new_item_name)
            panel.screenshot_groups[new_item_name] = [bitmap]
        else:
            wx.MessageBox("CoordinatesFrame is not available!", "Error", wx.OK | wx.ICON_ERROR)


    def add_to_group(self):
        """Start a new group or add screenshots to the current group."""
        if not self.grouping_mode:
            # Start a new group
            self.grouping_mode = True
            group_name = f"Group {self.coordinates_frame.panel.group_list.GetCount() + 1}"
            self.coordinates_frame.panel.add_group(group_name)
            self.coordinates_frame.panel.current_group = group_name

        # Use the active group
        group_name = self.coordinates_frame.panel.current_group

        if self.coordinates_frame:
            coordinates = self.coordinates_frame.coordinates

            # Take a screenshot and append to the current group
            bitmap = self.coordinates_frame.panel.take_screenshot(coordinates, return_bitmap=True)

            # Add the screenshot to the group
            if group_name in self.coordinates_frame.panel.screenshot_groups:
                self.coordinates_frame.panel.screenshot_groups[group_name].append(bitmap)
            else:
                self.coordinates_frame.panel.screenshot_groups[group_name] = [bitmap]

            # Add the screenshot as a tab
            self.coordinates_frame.panel.add_screenshot_tab(bitmap)

            # Update the status bar
            self.coordinates_frame.status_bar.SetStatusText(
                f"Added screenshot to '{group_name}'. Total: {len(self.coordinates_frame.panel.screenshot_groups[group_name])}"
            )
        else:
            wx.MessageBox("CoordinatesPanel or its take_screenshot method is not available!", "Error", wx.OK | wx.ICON_ERROR)







    def process_group(self):
        """End the grouping and process the screenshots in the group."""
        if self.grouping_mode and self.coordinates_frame:
            current_group = self.coordinates_frame.panel.current_group

            if current_group and current_group in self.coordinates_frame.panel.screenshot_groups:
                screenshots = self.coordinates_frame.panel.screenshot_groups[current_group]
                print(
                    f"Group '{current_group}' finalized with {len(screenshots)} screenshots!",
                    "Group Completed"
                )

                # Reset grouping mode and current group
                self.grouping_mode = False
                self.coordinates_frame.panel.current_group = None
            else:
                wx.MessageBox("No screenshots in the current group.", "Group Error", wx.OK | wx.ICON_ERROR)
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
            wx.CallAfter(self.capture_single_screenshot)
        except Exception as e:
            wx.MessageBox(f"Error showing coordinates frame: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)



if __name__ == "__main__":
    app = ScreenshotApp()


    app.MainLoop()
