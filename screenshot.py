import wx
import os
import threading
import keyboard  # For global hotkeys
from PIL import Image
import io
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from include.Controls import MonitorSelectionDialog, ScreenshotOverlay

import wx


class ThumbnailToggleButton(wx.Panel):
    """A custom toggle button with a thumbnail and a red border on toggle."""
    def __init__(self, parent, bitmap, label="Thumbnail", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.SetBackgroundColour(wx.NullColour)  # Default background color
        self.label = label

        # Create a sizer for the panel
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the toggle button
        self.button = wx.ToggleButton(self, label="")
        self.button.SetBitmap(bitmap)  # Set the bitmap for the button
        self.button.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle)
        self.sizer.Add(self.button, 1, wx.EXPAND)

        self.SetSizer(self.sizer)

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

    def add_thumbnail_button(self, pil_image, label="Thumbnail"):
        """Add a new ThumbnailToggleButton to the scrollable panel."""
        # Convert PIL.Image to wx.Bitmap
        wx_image = wx.Image(pil_image.width, pil_image.height)
        wx_image.SetData(pil_image.convert("RGB").tobytes())
        bitmap = wx_image.ConvertToBitmap()

        # Create the toggle button with the converted bitmap
        toggle_button = ThumbnailToggleButton(self, bitmap=bitmap, label=label)
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



class CoordinatesPanel(wx.Panel):
    def __init__(self, parent, coordinates, callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.coordinates = coordinates
        self.callback = callback
        self.screenshot_groups = {}
        self.current_group = None
        self.current_coordinates = None

        # Main horizontal sizer for overall layout
        main_hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Vertical sizer for scrollable thumbnails and the button
        thumbnail_vbox = wx.BoxSizer(wx.VERTICAL)

        # Scrollable thumbnail panel
        self.thumbnail_scroll_panel = ThumbnailScrollPanel(self, size=(150, -1))  # Fixed width
        thumbnail_vbox.Add(self.thumbnail_scroll_panel, 1, wx.EXPAND | wx.ALL, 5)

        # Add New Coordinates button
        add_coordinates_button = wx.Button(self, label="Add New Coordinates")
        add_coordinates_button.Bind(wx.EVT_BUTTON, self.add_new_coordinates)
        thumbnail_vbox.Add(add_coordinates_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        main_hbox.Add(thumbnail_vbox, 0, wx.EXPAND | wx.ALL, 5)

        # Vertical sizer for group list and buttons
        left_vbox = wx.BoxSizer(wx.VERTICAL)

        # List control for groups
        self.group_list = wx.ListBox(self, style=wx.LB_SINGLE)
        self.group_list.Bind(wx.EVT_LISTBOX, self.on_group_selected)
        left_vbox.Add(self.group_list, 1, wx.EXPAND | wx.ALL, 5)

        # New list control for active tab coordinates
        self.coordinates_listbox = wx.ListBox(self, style=wx.LB_SINGLE)
        left_vbox.Add(self.coordinates_listbox, 1, wx.EXPAND | wx.ALL, 5)
        # Inside the CoordinatesPanel constructor
        self.coordinates_listbox.Bind(wx.EVT_LISTBOX, self.on_coordinates_listbox_selection)


        # Buttons column
        button_vbox = wx.BoxSizer(wx.VERTICAL)

        screenshot_btn = wx.Button(self, label="Take Screenshot")
        screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_single_screenshot())
        button_vbox.Add(screenshot_btn, flag=wx.ALL, border=5)

        group_screenshot_btn = wx.Button(self, label="Take Group Screenshot")
        group_screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_group_screenshot())
        button_vbox.Add(group_screenshot_btn, flag=wx.ALL, border=5)

        end_group_btn = wx.Button(self, label="End Group")
        end_group_btn.Bind(wx.EVT_BUTTON, lambda evt: self.end_group())
        button_vbox.Add(end_group_btn, flag=wx.ALL, border=5)

        coord_btn = wx.Button(self, label="Update Coordinates")
        coord_btn.Bind(wx.EVT_BUTTON, self.open_overlay)
        button_vbox.Add(coord_btn, flag=wx.ALL, border=5)

        save_btn = wx.Button(self, label="Save Screenshot")
        save_btn.Bind(wx.EVT_BUTTON, self.save_screenshot)
        button_vbox.Add(save_btn, flag=wx.ALL, border=5)

        left_vbox.Add(button_vbox, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        main_hbox.Add(left_vbox, 0, wx.EXPAND | wx.ALL, 5)

        # Notebook for displaying screenshots
        self.notebook = wx.Notebook(self)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_notebook_page_changed)
        main_hbox.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_hbox)
    def on_coordinates_listbox_selection(self, event):
        """Handle selection of an item in the coordinates list control."""
        selected_index = self.coordinates_listbox.GetSelection()
        if selected_index == wx.NOT_FOUND:
            return  # No selection made

        # Get the corresponding notebook tab
        current_tab_index = self.notebook.GetSelection()
        if current_tab_index == wx.NOT_FOUND:
            return  # No active tab

        current_tab = self.notebook.GetPage(current_tab_index)
        if not isinstance(current_tab, wx.ScrolledWindow):
            return  # Ensure the tab is a scrollable panel

        # Scroll to the selected canvas
        selected_canvas = current_tab.GetChildren()[selected_index]
        if isinstance(selected_canvas, wx.StaticBitmap):
            # Ensure the canvas is visible
            x, y = selected_canvas.GetPosition()
            current_tab.Scroll(x // 10, y // 10)  # Scroll to the canvas position (scaled by scroll rate)
            selected_canvas.SetFocus()  # Optional: Set focus to the canvas

            # Update status bar
            self.GetParent().status_bar.SetStatusText(f"Scrolled to coordinate {selected_index + 1}")



    def on_notebook_page_changed(self, event):
        """Update the coordinates listbox when the notebook tab changes."""
        self.coordinates_listbox.Clear()

        # Get the current group name
        current_tab_index = self.notebook.GetSelection()
        if current_tab_index == wx.NOT_FOUND:
            return

        tab_label = self.notebook.GetPageText(current_tab_index)
        group_name = tab_label.split(" ")[-1].strip("()")

        if group_name in self.screenshot_groups:
            for i, _ in enumerate(self.screenshot_groups[group_name], start=1):
                self.coordinates_listbox.Append(f"coord_{i}")

        event.Skip()  # Allow the default behavior

    def add_new_coordinates(self, event):
        """Open overlay window to define new screenshot coordinates."""
        try:
            # Hide the main frame
            main_frame = self.GetParent()
            main_frame.Hide()

            # Create the overlay
            overlay = ScreenshotOverlay(
                callback=self.on_coordinates_selected,
                monitor_index=1,  # Assuming monitor index starts from 1
                coordinates_frame=self,  # Pass the reference to this frame if needed
                parent=self,
                style=wx.NO_BORDER
            )

            overlay.Show()
            print("Overlay opened")
            
            # Restore the main frame after the overlay is closed
            def restore_main_frame(evt):
                print("Overlay closed")  # Debug print
                main_frame.Show()  # Ensure the main frame is shown again
                evt.Skip()  # Allow the close event to propagate

            overlay.Bind(wx.EVT_CLOSE, restore_main_frame)

        except Exception as e:
            wx.MessageBox(f"Error opening overlay: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            self.GetParent().Show()  # Ensure the main frame is shown even if an error occurs





    def on_coordinates_selected(self, pil_image, thumbnail, coordinates):
        """Handle the selection and add new coordinates."""
        if not coordinates:
            wx.MessageBox("No valid coordinates found.", "Error", wx.OK | wx.ICON_ERROR)
            return

        self.current_coordinates = coordinates  # Store the selected coordinates

        # Create a unique label
        new_label = f"Coordinates {len(self.thumbnail_scroll_panel.sizer.GetChildren()) + 1}"

        # Add thumbnail to the scroll panel
        toggle_button = self.thumbnail_scroll_panel.add_thumbnail_button(thumbnail, label=new_label)

        # Automatically toggle the newly created button
        if toggle_button:
            # Ensure the toggle button is activated
            toggle_button.button.SetValue(True)  # Programmatically set the toggle to "on"
            toggle_button.on_toggle()  # Call the toggle handler to ensure UI updates

        # Store the selected coordinates in the coordinates list
        if not hasattr(self, 'coordinates_list'):
            self.coordinates_list = {}
        self.coordinates_list[new_label] = self.current_coordinates

        # Update the status bar
        self.GetParent().status_bar.SetStatusText(f"Added and toggled new coordinates as '{new_label}'")











    def _add_thumbnail_button(self, thumbnail, label="Thumbnail"):
        """Add a thumbnail button to the scrollable panel."""
        bitmap = wx.Bitmap.FromBuffer(thumbnail.width, thumbnail.height, thumbnail.tobytes())
        self.thumbnail_scroll_panel.add_thumbnail_button(bitmap, label)


    def _add_thumbnail_button(self, thumbnail, label="Thumbnail"):
        """Add a ThumbnailToggleButton with a thumbnail to the thumbnail sizer."""
        # Convert PIL image to wx.Bitmap
        bitmap = wx.Bitmap.FromBuffer(thumbnail.width, thumbnail.height, thumbnail.tobytes())

        # Create an instance of ThumbnailToggleButton
        toggle_button = ThumbnailToggleButton(self, bitmap=bitmap, label=label)

        # Add the toggle button container to the thumbnail sizer
        self.thumbnail_sizer.Add(toggle_button, 0, wx.EXPAND | wx.ALL, 5)
        self.Layout()  # Refresh the layout to display the new button






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
        """Take screenshots for all toggled thumbnail buttons and display them in a single scrollable panel."""
        # Clear the coordinates list box for the new group
        self.coordinates_listbox.Clear()

        if not hasattr(self, 'coordinates_list') or not self.coordinates_list:
            wx.MessageBox("No coordinates defined!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Identify toggled thumbnail buttons
        toggled_buttons = []
        for child in self.thumbnail_scroll_panel.sizer.GetChildren():
            button_panel = child.GetWindow()
            if isinstance(button_panel, ThumbnailToggleButton):
                if button_panel.button.GetValue():  # Check if toggled
                    toggled_buttons.append(button_panel.label)

        if not toggled_buttons:
            wx.MessageBox("No toggled thumbnail buttons found!", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        # Generate a group name for this screenshot pass
        group_name = f"Group {len(self.screenshot_groups) + 1}"

        # Add a new group entry in the group list
        self.add_group(group_name)

        # Ensure the scrollable panel exists for the group
        if not hasattr(self, 'single_screenshot_tab') or self.single_screenshot_tab is None:
            # Create a new scrollable tab
            self.single_screenshot_tab = wx.ScrolledWindow(self.notebook)
            self.single_screenshot_tab.SetScrollRate(10, 10)
            self.single_screenshot_tab_sizer = wx.BoxSizer(wx.VERTICAL)
            self.single_screenshot_tab.SetSizer(self.single_screenshot_tab_sizer)
            self.notebook.AddPage(self.single_screenshot_tab, f"Single Screenshots ({group_name})")
        else:
            # Clear the existing content safely
            for child in self.single_screenshot_tab_sizer.GetChildren():
                child.GetWindow().Destroy()
            self.single_screenshot_tab_sizer.Clear()

        # Add new screenshots to the scrollable panel and populate coordinates list
        self.coordinates_listbox.Clear()  # Clear for new group
        for i, label in enumerate(toggled_buttons, start=1):
            coordinates = self.coordinates_list.get(label)
            if coordinates:
                bitmap = self.take_screenshot(coordinates, return_bitmap=True)

                # Add screenshot to the scrollable panel
                canvas = wx.StaticBitmap(self.single_screenshot_tab, bitmap=bitmap)
                self.single_screenshot_tab_sizer.Add(canvas, 0, wx.EXPAND | wx.ALL, 5)

                # Add the screenshot to the group
                if group_name in self.screenshot_groups:
                    self.screenshot_groups[group_name].append(bitmap)
                else:
                    self.screenshot_groups[group_name] = [bitmap]

                # Add an entry to the coordinates listbox
                self.coordinates_listbox.Append(f"coord_{i} ({label})")

        # Refresh the scrollable panel layout
        self.single_screenshot_tab.Layout()
        self.single_screenshot_tab.FitInside()

        # Set the tab with screenshots as the active tab
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)

        # Update the status bar
        self.GetParent().status_bar.SetStatusText(
            f"Captured {len(toggled_buttons)} screenshots in group '{group_name}'."
        )













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
        """Handle group selection from the list and display all screenshots for the group in one scrollable tab."""
        selected_group = self.group_list.GetStringSelection()
        if not selected_group:
            return

        self.current_group = selected_group

        # Clear the tabs in the notebook
        self.clear_tabs()

        # Ensure the scrollable panel exists for the group
        group_tab = wx.ScrolledWindow(self.notebook)
        group_tab.SetScrollRate(10, 10)
        group_tab_sizer = wx.BoxSizer(wx.VERTICAL)
        group_tab.SetSizer(group_tab_sizer)

        # Add screenshots for the selected group
        if selected_group in self.screenshot_groups:
            for bitmap in self.screenshot_groups[selected_group]:
                # Add each screenshot to the scrollable panel
                canvas = wx.StaticBitmap(group_tab, bitmap=bitmap)
                group_tab_sizer.Add(canvas, 0, wx.EXPAND | wx.ALL, 5)

        # Add the group tab to the notebook
        self.notebook.AddPage(group_tab, f"Group: {selected_group}")
        group_tab.Layout()
        group_tab.FitInside()

        # Set the new tab as the active tab
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)

        # Update the coordinates list for the selected group
        self.coordinates_listbox.Clear()
        if selected_group in self.screenshot_groups:
            for i, _ in enumerate(self.screenshot_groups[selected_group], start=1):
                self.coordinates_listbox.Append(f"coord_{i}")

        # Update the status bar with the selected group
        self.GetParent().status_bar.SetStatusText(f"Selected group: '{selected_group}'")



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
            raise e
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

    def _show_coordinates_frame(self, pil_image, thumbnail):
        # Ensure the CoordinatesFrame exists
        if not self.coordinates_frame:
            wx.MessageBox("CoordinatesFrame is not available!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Add thumbnail to the left-side button area
        self.coordinates_frame.panel.add_thumbnail_button(thumbnail, label="Full Screenshot")

        # Update the status bar or perform additional actions if needed
        self.coordinates_frame.status_bar.SetStatusText("Full screenshot captured.")


    def show_monitor_selection_dialog(self):
        """Show dialog to select a monitor."""
        dialog = MonitorSelectionDialog(None)
        dialog.CenterOnScreen()
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            # Correctly retrieve the selected monitor index as an integer
            selected_monitor = dialog.radio_box.GetSelection() + 1  # Monitors in mss start from 1
            dialog.Destroy()
            print(f"Selected Monitor: {selected_monitor}")
            self.show_overlay(selected_monitor)
        else:
            dialog.Destroy()
            self.ExitMainLoop()

    def show_overlay(self, monitor_index):
        """Open the overlay on the selected monitor."""
        try:
            print("Opening overlay...")
            if self.coordinates_frame is None:
                self.coordinates_frame = CoordinatesFrame(coordinates=(0, 0, 1920, 1080),  # Default resolution
                                                        callback=self.show_monitor_selection_dialog,
                                                        parent=None)
                self.coordinates_frame.Hide()

            self.overlay = ScreenshotOverlay(
                callback=self.handle_full_screenshot,  # Pass the callback
                monitor_index=monitor_index,           # Pass the monitor index
                coordinates_frame=self.coordinates_frame,  # Pass the coordinates_frame
                parent=None,
                style=wx.NO_BORDER,
            )
            self.overlay.Show()
        except Exception as e:
            wx.MessageBox(f"Error opening overlay: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            raise e








    def handle_full_screenshot(self, pil_image, thumbnail, coordinates):
        """Handle the full screenshot, including coordinates, and update the UI."""
        if self.coordinates_frame is None:
            wx.MessageBox("CoordinatesFrame is not available!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Call the on_coordinates_selected method directly to handle the thumbnail addition
        if hasattr(self.coordinates_frame.panel, 'on_coordinates_selected'):
            self.coordinates_frame.panel.on_coordinates_selected(pil_image, thumbnail, coordinates)















if __name__ == "__main__":
    app = ScreenshotApp()


    app.MainLoop()
