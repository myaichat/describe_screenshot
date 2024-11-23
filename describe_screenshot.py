import wx
import os, time
import threading
import keyboard  # For global hotkeys
from PIL import Image

import wx.html2 
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)
from include.Controls import MonitorSelectionDialog, ScreenshotOverlay,  ThumbnailScrollPanel, ThumbnailToggleButton


import base64
import io
class WebViewPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create a splitter window
        self.splitter = wx.SplitterWindow(self)

        # Create the WebView as the top pane
        self.webview = wx.html2.WebView.New(self.splitter)
        self.webview.SetPage("<html><body></body></html>", "")  # Initialize with an empty HTML page

        # Bind mouse enter/leave events to the WebView
        self.webview.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter_webview)
        self.webview.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave_webview)

        # Create a panel with a button and multiline text control as the bottom pane
        self.button_panel = wx.Panel(self.splitter)
        button_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Add the multiline text control
        self.prompt_text_ctrl = wx.TextCtrl(self.button_panel, style=wx.TE_MULTILINE)
        self.prompt_text_ctrl.SetValue("Describe this image")
        button_panel_sizer.Add(self.prompt_text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Add the button sizer for vertical arrangement
        button_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add the "Ask Model" button
        label = "Ask Model"
        text_width, text_height = self.button_panel.GetTextExtent(label)  # Get the label dimensions
        padding = 20  # Add padding to ensure square shape
        button_size = max(text_width, text_height) + padding  # Determine square size based on label size

        self.ask_model_button = wx.Button(self.button_panel, label=label, size=(button_size, button_size))
        self.ask_model_button.SetBackgroundColour(wx.Colour(144, 238, 144))  # Light green color
        self.ask_model_button.Bind(wx.EVT_BUTTON, self.on_ask_model_button_click)  # Bind button click logic
        button_sizer.Add(self.ask_model_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # Add the collapse/expand button
        self.collapse_button = wx.Button(self.button_panel, label="Collapse")
        self.collapse_button.Bind(wx.EVT_BUTTON, self.on_collapse_button_click)  # Bind collapse/expand logic
        button_sizer.Add(self.collapse_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        button_panel_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.button_panel.SetSizer(button_panel_sizer)
        # Bind mouse enter/leave events to the button panel
        self.button_panel.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter_button_panel)
        self.button_panel.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave_panel)

        # Split the WebView and the button panel horizontally
        self.splitter.SplitHorizontally(self.webview, self.button_panel)

        # Adjust sash position and behavior
        self.splitter.SetSashGravity(0.9)  # Allocate 90% of the space to the WebView initially
        self.splitter.SetMinimumPaneSize(50)  # Allow collapsing to a minimal height
        wx.CallAfter(self.splitter.SetSashPosition, int(self.GetSize().y * 0.9))  # Dynamically set the sash position

        # Add the splitter to the main panel's sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

        # Track the collapsed state
        self.is_collapsed = False
        wx.CallAfter(self.on_collapse_button_click, None)
    def on_ask_model_button_click(self, event):
        print("on_ask_model_button_click")

    def on_collapse_button_click(self, event):
        print ("on_collapse_button_click", self.is_collapsed)  
        """Toggle collapsing or expanding the button panel."""
        if self.is_collapsed:
            # Expand the button panel
            self.splitter.SetSashPosition(int(self.GetSize().y / 2))  # Restore to half space
            self.collapse_button.SetLabel("Collapse")
            #self.is_collapsed = False
        else:
            # Collapse the button panel to its minimum height
            self.splitter.SetSashPosition(self.GetSize().y - 50)  # Set sash to near-bottom
            self.collapse_button.SetLabel("Expand")
            #self.is_collapsed = True

        # Toggle the collapsed state
        self.is_collapsed = not self.is_collapsed

    def on_mouse_enter_webview(self, event):
        """Handle mouse entering the WebView."""
        print("Mouse entered WebView.", self.is_collapsed)
        if not self.is_collapsed:
            self.on_collapse_button_click(None)  # Expand WebView
        event.Skip()

    def on_mouse_leave_webview(self, event):
        """Handle mouse leaving the WebView."""
        print("Mouse left WebView.", self.is_collapsed)
        event.Skip()

    def on_mouse_enter_button_panel(self, event):
        """Handle mouse entering the bottom button panel."""
        print("Mouse entered Bottom Panel.", self.is_collapsed)
        if self.is_collapsed:
            self.on_collapse_button_click(None)  # Collapse WebView and expand Bottom Panel
        event.Skip()

    def on_mouse_leave_panel(self, event):
        """Handle mouse leaving the bottom button panel."""
        # Get the mouse position in screen coordinates
        mouse_position = wx.GetMouseState()
        mouse_screen_point = wx.Point(mouse_position.x, mouse_position.y)

        # Get the screen rectangle of the button panel
        panel_screen_rect = self.button_panel.GetScreenRect()

        # Check if the mouse is still inside the panel or any of its children
        if panel_screen_rect.Contains(mouse_screen_point):
            return  # Do nothing if the mouse is still within the panel or its children

        # Otherwise, trigger the collapse
        print("Mouse left Bottom Panel.", self.is_collapsed)
        if not self.is_collapsed:
            self.on_collapse_button_click(None)  # Collapse WebView and expand Bottom Panel        
        event.Skip()









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
        add_coordinates_button = wx.Button(self, label="Add New \nCoordinates")
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
        if 1:
            s_vbox = wx.BoxSizer(wx.HORIZONTAL)
            screenshot_btn = wx.Button(self, label="Take \nScreenshot")
            screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_single_screenshot())

            s_vbox.Add(screenshot_btn, flag=wx.ALL, border=5)
            
            self.show_webview_btn =show_webview_btn= wx.Button(self, label="Hide Webview")
            show_webview_btn.Bind(wx.EVT_BUTTON, self.on_show_webview)

            s_vbox.Add(show_webview_btn, flag=wx.ALL, border=5)
            button_vbox.Add(s_vbox, flag=wx.ALL, border=5)

        if 1:
            g_vbox = wx.BoxSizer(wx.HORIZONTAL)
            group_screenshot_btn = wx.Button(self, label="Take Group \nScreenshot")
            group_screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_group_screenshot())
            g_vbox.Add(group_screenshot_btn, flag=wx.ALL, border=5)

            end_group_btn = wx.Button(self, label="End \nGroup")
            end_group_btn.Bind(wx.EVT_BUTTON, lambda evt: self.end_group())
            g_vbox.Add(end_group_btn, flag=wx.ALL, border=5)
            button_vbox.Add(g_vbox, flag=wx.ALL, border=5)
        if 1:
            h_vbox = wx.BoxSizer(wx.HORIZONTAL)

            coord_btn = wx.Button(self, label="Update \nCoordinates")
            coord_btn.Bind(wx.EVT_BUTTON, self.open_overlay)
            h_vbox.Add(coord_btn, flag=wx.ALL, border=5)

            save_btn = wx.Button(self, label="Save \nScreenshot")
            save_btn.Bind(wx.EVT_BUTTON, self.save_screenshot)
            h_vbox.Add(save_btn, flag=wx.ALL, border=5)
            button_vbox.Add(h_vbox, flag=wx.ALL, border=5)

        left_vbox.Add(button_vbox, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        main_hbox.Add(left_vbox, 0, wx.EXPAND | wx.ALL, 5)
        if 1:
    # Main horizontal layout with splitter
            self.splitter = wx.SplitterWindow(self)

            # Left panel for the notebook
            self.notebook_panel = wx.Panel(self.splitter)
            notebook_sizer = wx.BoxSizer(wx.VERTICAL)

            self.notebook = wx.Notebook(self.notebook_panel)
            self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_notebook_page_changed)
            notebook_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

            self.notebook_panel.SetSizer(notebook_sizer)
            # Right panel for WebView
            self.webview_panel = WebViewPanel(self.splitter)


            # Configure splitter
            self.splitter.SplitVertically(self.notebook_panel, self.webview_panel)

            # Set the sash position to ensure WebView is visible initially
            #self.splitter.SetSashPosition(int(self.GetSize().x -50), redraw=True)  # Allocate 50% to both
            self.splitter.SetMinimumPaneSize(150)
            self.splitter.Layout() 

            # Set the initial button state
            self.show_webview_btn.SetLabel("Show Webview")

            # Set the initial button state
            
            self.show_webview_btn.Bind(wx.EVT_BUTTON, self.on_show_webview)          

            # Configure splitter
            #self.splitter.SplitVertically(self.notebook_panel, self.webview_panel)
            #self.splitter.SetSashGravity(1)  # Allocate more space to the notebook
            #self.splitter.SetMinimumPaneSize(200)
            self.Bind(wx.EVT_SIZE, self.on_size) # Allocate 75% to the notebook
            #wx.CallAfter(self.on_show_webview,wx.CommandEvent())
            #wx.CallAfter(wx.PostEvent,self.show_webview_btn, wx.CommandEvent(wx.wxEVT_BUTTON))
            #self.on_show_webview(button=self.show_webview_btn)




        main_hbox.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_hbox)
    def on_size(self, event):
        """Adjust the sash position after the panel is resized."""
        self.splitter.SetSashPosition(int(self.GetSize().x * 0.75))  # Allocate 75% to the notebook
        self.Unbind(wx.EVT_SIZE)  # Unbind to avoid repeated adjustments
        event.Skip()

    def on_show_webview(self, event=None, button=None):
        """Toggle the splitter sash position and update the button label."""
        if not button:  # Use the button reference if provided
            button = event.GetEventObject() if event else self.show_webview_btn

        current_label = button.GetLabel()
        total_width = self.GetSize().x

        # Determine the new sash position based on the current label
        if current_label == "Show Webview":
            # Move sash to allocate more space to WebView
            new_position = 150  # Minimal space for notebook
            button.SetLabel("Hide Webview")
            self.GetParent().status_bar.SetStatusText("WebView panel shown.")
        else:
            # Move sash to allocate more space to the notebook
            new_position = total_width - 150  # Minimal space for WebView
            button.SetLabel("Show Webview")
            self.GetParent().status_bar.SetStatusText("WebView panel minimized.")

        # Adjust the sash position
        self.splitter.SetSashPosition(new_position, redraw=True)
        self.splitter.Layout()
        self.Layout()



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
        wx.CallAfter(self.take_single_screenshot)







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
        main_frame = self.GetParent()  # Reference to the main frame

        # Hide the main frame
        main_frame.Hide()
        main_frame.Iconize(True)
        time.sleep(0.15)  
        wx.Yield()
        #wx.CallLater(100, self.take_delayed_screenshot,main_frame)  # Delayed screenshot capture
        #wx.CallAfter(self.take_delayed_screenshot,main_frame)  # Delayed screenshot capture
        #def take_delayed_screenshot(self,main_frame): 
        try:        
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
                    #main_frame.Hide()
                    wx.Yield() 
                    bitmap = self.take_screenshot(coordinates, return_bitmap=True)
                    if 1:
                        base64_image = self.bitmap_to_base64(bitmap)

                        # Update the WebView to display the image
                        self.update_webview_with_image(base64_image)
                        
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

        finally:
            self.show_frame(main_frame)  # Show the main frame again

    def bitmap_to_base64(self, bitmap):
        """Convert a wx.Bitmap to a base64-encoded PNG image."""
        image = bitmap.ConvertToImage()
        stream = io.BytesIO()
        image.SaveFile(stream, wx.BITMAP_TYPE_PNG)
        base64_image = base64.b64encode(stream.getvalue()).decode('utf-8')
        return base64_image
    def update_webview_with_image(self, base64_image):
        """Update the WebView with the base64 image, placed in the bottom-left corner with a label."""
        html_content = f"""
        <html>
            <body style="margin: 0; padding: 0; height: 100%; display: flex; flex-direction: column; justify-content: flex-end;">
                <div style="position: absolute; bottom: 0; left: 0; margin: 10px;">
                    <div style="font-family: Arial, sans-serif; font-size: 14px; color: black; margin-bottom: 5px;">
                        Screenshot:
                    </div>
                    <img src="data:image/png;base64,{base64_image}" alt="Screenshot" 
                        style="width: 150px; height: auto; border: 1px solid black;">
                </div>
            </body>
        </html>
        """
        self.webview_panel.webview.SetPage(html_content, "")

        
    def show_frame(self,main_frame):

        # Show the main frame again
             
        main_frame.Iconize(False)
        main_frame.Show()
        wx.Yield()  # Allow UI to process the show event






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

        self.SetTitle("Multi Area Screenshot")
        self.SetSize((1800, 1200))

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
        """Trigger the screenshot action."""
        if self.coordinates_frame:
            wx.CallAfter(self.coordinates_frame.panel.take_single_screenshot)
        else:
            wx.MessageBox("CoordinatesFrame is not available!", "Error", wx.OK | wx.ICON_ERROR)


    def start_or_add_to_group(self):
        """Start a new group or add to the current group."""
        wx.CallAfter(self.add_to_group)

    def end_group(self):
        """End the grouping and process the screenshots in the group."""
        wx.CallAfter(self.process_group)


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
