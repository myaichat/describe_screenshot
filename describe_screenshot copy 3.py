import wx
import os, time
import threading
import keyboard  # For global hotkeys
from PIL import Image
from pprint import pprint as pp
import wx.html2 
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)
from include.Controls import MonitorSelectionDialog, ScreenshotOverlay,  ThumbnailScrollPanel, ThumbnailToggleButton
from include.Controls import ModelSelectionNotebook

import sys
#sys.setrecursionlimit(10000)

import  openai
import base64
import io 

#MODEL='gpt-4o-mini'
client=openai.OpenAI()
conversation_history=[]

is_mock=False
is_autoexec=True
def describe_screenshot(prompt, model, image_data, append_callback=None, history=False, mock=False, request_id=1):
    global conversation_history, client
    print(f"describe_screenshot: prompt={prompt}, model={model}, image_data={len(image_data)}, history={history}, mock={mock}, request_id={request_id}")
    print("Conversation history length:", len(conversation_history))

    try:
        ch = conversation_history if history else []
      
        if 1:

            if request_id == 1:
                if not image_data:
                    ch.append({"role": "user", "content": prompt})
                else:
                    ch.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                        ]
                    })
            else:
                # For subsequent requests, just append the prompt
                ch.append({"role": "user", "content": prompt})


        if mock:
            # Simulated response for debugging purposes
            assistant_response = r"""
RecursionError: maximum recursion depth exceeded
(myenv) PS C:\Users\alex_\aichat\describe_screenshot>
(myenv) PS C:\Users\alex_\aichat\describe_screenshot> ^C
(myenv) PS C:\Users\alex_\aichat\describe_screenshot> ^C
(myenv) PS C:\Users\alex_\aichat\describe_screenshot> python .\describe_screenshot.py
Initializing App
(myenv) PS C:\Users\alex_\aichat\describe_screenshot> ^C
(myenv) PS C:\Users\alex_\aichat\describe_screenshot> python .\describe_screenshot.py

"""         
            for line in assistant_response.splitlines():
                for word in line.split():
                    if append_callback:
                        wx.CallAfter(append_callback, f'{word} ', is_streaming=True)
                    time.sleep(0.02)
                wx.CallAfter(append_callback, 'new line \n', is_streaming=True)
        else:
            # Real API call
            pp(ch)
            response = client.chat.completions.create(
                model=model,
                messages=ch,
                stream=True
            )

            assistant_response = ""
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    print(content, end="")
                    if content:
                        assistant_response += content
                        if append_callback:
                            wx.CallAfter(append_callback, content, is_streaming=True)

            # Always append the assistant's response to conversation history when in history mode
        if history:
            ch.append({"role": "assistant", "content": assistant_response})

    except Exception as e:
        print(f"Error in describe_screenshot: {e}")
        if append_callback:
            append_callback(f"Error: {str(e)}", is_streaming=False)
        raise

    finally:
        #client.close()
        #wx.CallAfter(self.webview_panel.ask_model_button.Enable)
        pass





import base64
import io
class WebViewPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Initialize member variables
        self.active_threads = []
        self.is_collapsed = False
        self.image_data = None
        self.request_counter = 0  # Add a counter for request IDs
        self.processing = False  # Add a flag to track processing state
        self.auto_scroll = True

        # Create a splitter window
        self.splitter = wx.SplitterWindow(self)

        # Create the WebView as the top pane
        self.webview = wx.html2.WebView.New(self.splitter)

        # Bind mouse enter/leave events to the WebView
        self.webview.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter_webview)
        self.webview.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave_webview)

        # Create a panel with a button and multiline text control as the bottom pane
        self.button_panel = wx.Panel(self.splitter)
        button_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Add the multiline text control
        self.prompt_text_ctrl = wx.TextCtrl(self.button_panel, style=wx.TE_MULTILINE)
        self.prompt_text_ctrl.SetValue("Describe this image")
        self.prompt_text_ctrl.Bind(wx.EVT_CHAR_HOOK, self.on_text_ctrl_key)

        button_panel_sizer.Add(self.prompt_text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Add the button sizer for vertical arrangement
        button_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add spacer at the top
        #button_sizer.AddStretchSpacer(1)

        # Add the collapse/expand button at the very top
        if 1:
            top_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.collapse_button = wx.Button(self.button_panel, label="Collapse")
            self.collapse_button.Bind(wx.EVT_BUTTON, self.on_collapse_button_click)
            top_sizer.Add(self.collapse_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

            # Add the "Auto-Scroll" toggle button in the middle
            self.auto_scroll_button = wx.ToggleButton(self.button_panel, label="Auto-Scroll: ON")
            self.auto_scroll_button.SetValue(True)  # Default: ON
            self.auto_scroll_button.Bind(wx.EVT_TOGGLEBUTTON, self.toggle_auto_scroll)
            top_sizer.Add(self.auto_scroll_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        button_sizer.Add(top_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        
        
        

        self.notebook = ModelSelectionNotebook(self.button_panel)
        button_sizer.Add(self.notebook, 0, wx.EXPAND | wx.ALL, 5)  
        toggle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if 1:
            self.history_button = wx.ToggleButton(self.button_panel, label="History: ON")
            self.history_button.SetValue(True)  # Default: ON
            self.history_button.Bind(wx.EVT_TOGGLEBUTTON, self.toggle_history)
            toggle_sizer.Add(self.history_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)     

        if 1:
            self.mock_button = wx.ToggleButton(self.button_panel, label="Mock: ON")
            self.mock_button.SetValue(is_mock)  # Default: ON
            self.mock_button.Bind(wx.EVT_TOGGLEBUTTON, self.toggle_mock)
            toggle_sizer.Add(self.mock_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)                     
        button_sizer.Add(toggle_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)  
        # Add another spacer
        button_sizer.AddStretchSpacer(1)



        # Add the "Ask Model" button at the very bottom
        label = "Ask Model"
        text_width, text_height = self.button_panel.GetTextExtent(label)  # Get the label dimensions
        padding = 20  # Add padding to ensure square shape
        button_size = max(text_width, text_height) + padding  # Determine square size based on label size

        self.ask_model_button = wx.Button(self.button_panel, label=label, size=(button_size, button_size))
        self.ask_model_button.SetBackgroundColour(wx.Colour(144, 238, 144))  # Light green color
        self.ask_model_button.Bind(wx.EVT_BUTTON, self.on_ask_model_button_click)
        button_sizer.Add(self.ask_model_button, 0, wx.EXPAND  | wx.ALL, 5)


        # Add the button sizer to the button panel
        button_panel_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.button_panel.SetSizer(button_panel_sizer)

        # Bind mouse events to the button panel
        self.button_panel.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter_button_panel)
        self.button_panel.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave_panel)

        # Split the WebView and the button panel horizontally
        self.splitter.SplitHorizontally(self.webview, self.button_panel)

        # Adjust sash position and behavior
        self.splitter.SetSashGravity(0.9)
        self.splitter.SetMinimumPaneSize(50)
        wx.CallAfter(self.splitter.SetSashPosition, int(self.GetSize().y * 0.9))

        # Add the splitter to the main panel's sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

        # Initialize content and collapse state
        wx.CallAfter(self.on_collapse_button_click, None)
        self.set_initial_content()
        #self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        #self.webview.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # Set focus handler
        #self.webview.Bind(wx.EVT_SET_FOCUS, self.on_webview_focus)
        self.was_reset=False

    def _on_webview_focus(self, event):
        print("WebView received focus")
        event.Skip()
        
    def _on_key_down(self, event):
        print(f"Key pressed: {event.GetKeyCode()}")
        if event.ControlDown() and event.GetKeyCode() == ord('V'):
            print("Ctrl+V detected")
            wx.CallAfter(self.handle_clipboard_paste)
        event.Skip()

            
    def _on_text_ctrl_key(self, event):
        """Handle keyboard events in the prompt text control."""
        # Check for Alt+Enter
        key_code = event.GetKeyCode()
        
        # Check for Alt+Enter
        if event.ControlDown() and key_code == ord('V'):
            self.handle_clipboard_paste()
        elif event.AltDown() and key_code == wx.WXK_RETURN:
            if self.ask_model_button.IsEnabled():
                self.on_ask_model_button_click(None)
        # Check for Ctrl+A
        elif event.ControlDown() and key_code == ord('A'):
            # Reset button state and processing flag
            #self.reset_state()
            wx.CallAfter(self.reset_state)


        else:
            event.Skip()  # Process other keys normally

    def on_text_ctrl_key(self, event):
        """Handle keyboard events in the prompt text control."""
        key_code = event.GetKeyCode()
        
        if event.ControlDown() and key_code == ord('V'):
            self.handle_clipboard_paste()
        elif event.AltDown() and key_code == wx.WXK_RETURN:
            if self.ask_model_button.IsEnabled():
                self.on_ask_model_button_click(None)
        # Remove Ctrl+A handler as it's interfering with the flow
        # elif event.ControlDown() and key_code == ord('A'):
        #     wx.CallAfter(self.reset_state)
        else:
            event.Skip()

    def handle_clipboard_paste(self):
        """Process clipboard data when Ctrl+V is pressed."""
        global conversation_history
        print("Handling paste")
        
        if not wx.TheClipboard.Open():
            print("Failed to open clipboard")
            return
        def on_loaded(evt):
            
            if hasattr(self, 'image_data') and self.image_data:
                js_script = """
                    (function() {
                        try {
                            addSnapshot('%s');
                        } catch (error) {
                            console.error('Error adding image:', error);
                        }
                    })();
                """ % self.image_data
                new_webview.RunScript(js_script)   
                          
        try:
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_BITMAP)):
                print("Bitmap data found")
                bitmap_data = wx.BitmapDataObject()
                success = wx.TheClipboard.GetData(bitmap_data)
                
                if success:
                    print("Got bitmap data")
                    bitmap = bitmap_data.GetBitmap()
                    
                    # Convert bitmap to base64
                    image = bitmap.ConvertToImage()
                    stream = io.BytesIO()
                    image.SaveFile(stream, wx.BITMAP_TYPE_PNG)
                    self.image_data=base64_image = base64.b64encode(stream.getvalue()).decode('utf-8')
                    
                    # Reset conversation history and request counter
                    conversation_history = []
                    self.request_counter = 0
                    
                    # Create new WebView before destroying old one
                    new_webview = wx.html2.WebView.New(self.splitter)
                    #new_webview.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter_webview)
                    #new_webview.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave_webview)
                    new_webview.Bind(wx.html2.EVT_WEBVIEW_LOADED, on_loaded)   
                    # Replace old WebView with new one
                    old_webview = self.webview
                    self.webview = new_webview
                    self.splitter.ReplaceWindow(old_webview, new_webview)
                    old_webview.Destroy()
                    
                    # Set content in new WebView
                    self.set_initial_content()
                    
                    # Add image after WebView is ready
                    #wx.CallAfter(self.add_image_as_log_entry, base64_image)
                    
                else:
                    print("Failed to get bitmap data")
            else:
                print("No bitmap data in clipboard")
        finally:
            wx.TheClipboard.Close()

    def reset_state(self):
        """Reset the WebView state with improved handling of real API calls."""
        try:
            print("Resetting state")
            self.was_reset = False
            self.processing = False
            self.ask_model_button.Enable()
            self.active_threads = [t for t in self.active_threads if t.is_alive()]
            
            # Create new WebView
            new_webview = wx.html2.WebView.New(self.splitter)
            new_webview.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter_webview)
            new_webview.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave_webview)
            
            # Create an event to track when loading is complete
            loading_complete = threading.Event()
            
            def on_loaded(evt):
                try:
                    if hasattr(self, 'image_data') and self.image_data:
                        js_script = """
                            (function() {
                                try {
                                    addSnapshot('%s');
                                } catch (error) {
                                    console.error('Error adding image:', error);
                                }
                            })();
                        """ % self.image_data
                        new_webview.RunScript(js_script)
                        
                        if 'conversation_history' in globals():
                            for entry in conversation_history:
                                if entry['role'] == 'user':
                                    content = entry['content']
                                    if isinstance(content, str):
                                        self.add_user_message_to_webview(new_webview, content)
                                    elif isinstance(content, list):
                                        for item in content:
                                            if item['type'] == 'text':
                                                self.add_user_message_to_webview(new_webview, item['text'])
                                elif entry['role'] == 'assistant':
                                    self.add_assistant_message_to_webview(new_webview, entry['content'])
                finally:
                    self.was_reset = True
                    loading_complete.set()
                    
            new_webview.Bind(wx.html2.EVT_WEBVIEW_LOADED, on_loaded)
            
            # Set content and wait for loading
            self.set_initial_content(new_webview)
            
            # Wait for loading with timeout
            def wait_for_loading():
                if loading_complete.wait(timeout=5.0):  # 5 second timeout
                    wx.CallAfter(self._complete_reset, new_webview)
                else:
                    print("WARNING: WebView loading timed out")
                    wx.CallAfter(self._complete_reset, new_webview)
            
            # Start waiting thread
            loading_thread = threading.Thread(target=wait_for_loading)
            loading_thread.daemon = True
            loading_thread.start()
            
        except Exception as e:
            print(f"Error in reset_state: {e}")
            raise
    def _complete_reset(self, new_webview):
        """Complete the reset process after WebView is loaded."""
        try:
            # Replace old WebView with new one
            old_webview = self.webview
            self.webview = new_webview
            self.splitter.ReplaceWindow(old_webview, new_webview)
            old_webview.Destroy()
            
            self.prompt_text_ctrl.SetValue("Describe this image")
            print("Reset completed", self.was_reset)
            
            parent_frame = self.GetParent().GetParent().GetParent()
            if hasattr(parent_frame, 'status_bar'):
                parent_frame.panel.update_status(0, f"Processing state and content reset, {self.was_reset}")
        except Exception as e:
            print(f"Error in _complete_reset: {e}")
            raise
    def add_user_message_to_webview(self, webview, message):
        """Add user message to specific WebView instance."""
        escaped_message = (message.replace('\\', '\\\\')
                                .replace("'", "\\'")
                                .replace('"', '\\"')
                                .replace('\n', '\\n')
                                .replace('\r', '\\r')
                                .replace('\t', '\\t'))
        
        js_script = f"""
            (function() {{
                try {{
                    var table = document.getElementById('log-container');
                    if (!table) return;
                    var userRow = document.createElement('tr');
                    userRow.id = 'user-{self.request_counter}';
                    var userCell = document.createElement('td');
                    var userPrompt = document.createElement('div');
                    userPrompt.className = 'user-prompt';
                    userPrompt.textContent = `{escaped_message}`;
                    userCell.appendChild(userPrompt);
                    userRow.appendChild(userCell);
                    table.appendChild(userRow);
                    if ({str(self.auto_scroll).lower()}) {{
                        table.scrollTop = table.scrollHeight;
                    }}
                }} catch (error) {{
                    console.error('Error adding user message:', error);
                }}
            }})();
        """
        webview.RunScript(js_script)

    def add_assistant_message_to_webview(self, webview, message):
        """Add assistant message to specific WebView instance."""
        escaped_message = (message.replace('\\', '\\\\')
                                .replace("'", r"\'")
                                .replace('"', r'\"')
                                .replace('\n', r'\n')
                                .replace('\r', r'\r')
                                .replace('\t', r'\t'))
        
        js_script = f"""
            (function() {{
                try {{
                    var table = document.getElementById('log-container');
                    if (!table) return;
                    var responseRow = document.createElement('tr');
                    responseRow.id = 'response-{self.request_counter}';
                    var responseCell = document.createElement('td');
                    var responseDiv = document.createElement('div');
                    responseDiv.className = 'model-response';
                    responseDiv.textContent = "{escaped_message}";
                    responseCell.appendChild(responseDiv);
                    responseRow.appendChild(responseCell);
                    table.appendChild(responseRow);
                    if ({str(self.auto_scroll).lower()}) {{
                        table.scrollTop = table.scrollHeight;
                    }}
                }} catch (error) {{
                    console.error('Error adding assistant message:', error);
                }}
            }})();
        """
        webview.RunScript(js_script)


    def toggle_mock(self, event):
        if self.mock_button.GetValue():
            self.mock_button.SetLabel("Mock: ON")
            #self.image_data=None

        else:
            self.mock_button.SetLabel("Mock: OFF")  
            #self.reset_webview()
            #self.request_counter = 0  
                        
    def toggle_history(self, event):
        if self.history_button.GetValue():
            self.history_button.SetLabel("History: ON")
            #self.image_data=None

        else:
            self.history_button.SetLabel("History: OFF")  
            self.reset_webview()
            self.request_counter = 0  
    def reset_webview(self):
        e()
        global conversation_history
        conversation_history = []
        """Clear WebView content and re-add the thumbnail."""
        # Reset WebView content
        self.set_initial_content()  # Reload the initial content

        if self.image_data:
            # Re-add the thumbnail to the WebView
            self.add_image_as_log_entry(self.image_data)
        else:
            print("No image data available to re-add as thumbnail.")            

    def toggle_auto_scroll(self, event):
        """Toggle auto-scroll on or off."""
        self.auto_scroll = self.auto_scroll_button.GetValue()
        self.auto_scroll_button.SetLabel(f"Auto-Scroll: {'ON' if self.auto_scroll else 'OFF'}")




    def _stream_model_response(self, user_message, request_id):
        """Handle streaming responses with improved state management."""
        try:
            # Only proceed if we're not already processing
            if self.processing:
                return
                
            history = self.history_button.GetValue()
            if not history and not self.image_data:
                wx.CallAfter(wx.MessageBox,
                            "No image data found to send to the model.",
                            "Error",
                            wx.OK | wx.ICON_ERROR)
                return

            def append_callback(content, is_streaming):
                if content:
                    # Use CallAfter to ensure thread safety
                    wx.CallAfter(self._append_response, request_id, content, is_streaming)

            model = self.notebook.get_selected_models()['OpenAI']
            mock = self.mock_button.GetValue()
            
            # Clear existing conversation if not in history mode
            if not history:
                global conversation_history
                conversation_history = []
                
            # Process the response
            describe_screenshot(
                user_message, 
                model, 
                self.image_data, 
                append_callback=append_callback,
                history=history,
                mock=mock,
                request_id=request_id
            )

        except Exception as e:
            print(f"Error in _stream_model_response for request {request_id}: {e}")
            wx.CallAfter(self._append_response,
                        request_id,
                        f"\n\nError: {str(e)}",
                        False)
        finally:
            current_thread = threading.current_thread()
            if current_thread in self.active_threads:
                wx.CallAfter(self._remove_thread, current_thread)
                wx.CallAfter(self.ask_model_button.Enable)
                self.processing = False

    def _remove_thread(self, thread):
        """Safely remove a thread from active threads."""
        try:
            if thread in self.active_threads:
                self.active_threads.remove(thread)
                print(f"Thread {thread.name} removed. Active threads: {len(self.active_threads)}")
        except Exception as e:
            print(f"Error removing thread: {e}")


    def _create_log_entry(self, user_message, request_id):
        """Creates a new log entry with styled user prompt."""
        try:
            safe_message = user_message.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')

            js_script = f"""
                (function() {{
                    var table = document.getElementById('log-container');
                    if (!table) return;

                    // Create a styled user message row
                    var userRow = document.createElement('tr');
                    userRow.id = 'user-{request_id}';
                    var userCell = document.createElement('td');
                    var userPrompt = document.createElement('div');
                    userPrompt.className = 'user-prompt';
                    userPrompt.textContent = 'User #{request_id}: {safe_message}';
                    userCell.appendChild(userPrompt);
                    userRow.appendChild(userCell);
                    table.appendChild(userRow);

                    // Create a model response row with styling
                    var responseRow = document.createElement('tr');
                    responseRow.id = 'response-{request_id}';
                    var responseCell = document.createElement('td');
                    var responseDiv = document.createElement('div');
                    responseDiv.className = 'model-response';
                    responseCell.appendChild(responseDiv);
                    responseRow.appendChild(responseCell);
                    table.appendChild(responseRow);

                    // Auto-scroll if enabled
                    if ({str(self.auto_scroll).lower()}) {{
                        table.scrollTop = table.scrollHeight;
                    }}
                }})();
            """
            self.webview.RunScript(js_script)

        except Exception as e:
            print(f"Error creating log entry: {e}")


    def _append_response(self, request_id, content, is_streaming):
        """Safely append response content with improved error handling."""
        if not content:
            return

        try:
            if "<script>" in content:
                raise Exception("Invalid content detected!")

            escaped_content = (content
                .replace('\\', '\\\\')
                .replace("'", r"\'")
                .replace('"', r'\"')
                .replace('\n', r'\n')
                .replace('\t', r'\t'))

            js_code = f"""
                try {{
                    var responseRow = document.getElementById("response-{request_id}");
                    if (responseRow) {{
                        var responseDiv = responseRow.querySelector(".model-response");
                        if (responseDiv) {{
                            responseDiv.textContent += "{escaped_content}";
                            if (!{str(is_streaming).lower()}) {{
                                formatCodeBlocks(responseDiv);
                            }}
                        }}
                        if ({str(self.auto_scroll).lower()}) {{
                            responseRow.scrollIntoView({{behavior: "smooth", block: "end"}});
                        }}
                    }}
                }} catch (error) {{
                    console.error("Error in _append_response:", error);
                }}
            """
            self.webview.RunScript(js_code)

        except Exception as e:
            print(f"Error appending response: {e}")
            if not isinstance(e, RecursionError):
                wx.CallAfter(wx.MessageBox,
                    f"Error appending response: {str(e)}",
                    "Error",
                    wx.OK | wx.ICON_ERROR)
 
            
    def on_ask_model_button_click(self, event):
        """Handle ask model button click with improved debug logging."""
        print("-------------------------on_ask_model_button_click")
        if self.processing:
            print("Already processing - ignoring request")
            return

        try:
            # Reset any stale state
            self.processing = False
            self.ask_model_button.Enable()
            
            user_message = self.prompt_text_ctrl.GetValue().strip()
            if not user_message:
                wx.MessageBox("Please enter a prompt before asking the model.", 
                            "Input Required", 
                            wx.OK | wx.ICON_WARNING)
                return

            # Set processing state
            print("Setting processing state")
            self.processing = True
            self.ask_model_button.Disable()

            # Create new request
            self.request_counter += 1 
            request_id = self.request_counter
            print(f"Creating request {request_id}")
            
            # Create log entry
            wx.CallAfter(self._create_log_entry, user_message, request_id)
            
            # Start thread after log entry is created
            def start_thread():
                thread = threading.Thread(
                    target=self._stream_model_response,
                    args=(user_message, request_id),
                    daemon=True,
                    name=f"ModelThread-{request_id}"
                )
                self.active_threads = [t for t in self.active_threads if t.is_alive()]
                self.active_threads.append(thread)
                print(f"Starting thread for request {request_id}")
                thread.start()
                
            wx.CallAfter(start_thread)

        except Exception as e:
            print(f"Error in ask_model_button_click: {e}")
            self.processing = False
            self.ask_model_button.Enable()
            wx.MessageBox(f"Error: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)


    def _stream_model_response(self, user_message, request_id):
        """Handle streaming responses with improved error handling."""
        print(f"Entering _stream_model_response for request {request_id}")
        try:
            history = self.history_button.GetValue()
            mock = self.mock_button.GetValue()
            
            print(f"Request {request_id} - History: {history}, Mock: {mock}")
            
            if not history and not self.image_data:
                print(f"Request {request_id} - No image data available")
                wx.CallAfter(wx.MessageBox,
                            "No image data found to send to the model.",
                            "Error",
                            wx.OK | wx.ICON_ERROR)
                return

            def append_callback(content, is_streaming):
                if content:
                    print(f"Appending content for request {request_id}")
                    wx.CallAfter(self._append_response, request_id, content, is_streaming)

            model = self.notebook.get_selected_models()['OpenAI']
            print(f"Making API call for request {request_id} with model {model}")
            
            # Always clear conversation history for new requests
            global conversation_history
            if not history:
                print(f"Request {request_id} - Clearing conversation history")
                conversation_history = []
                
            describe_screenshot(
                user_message, 
                model, 
                self.image_data, 
                append_callback=append_callback,
                history=history,
                mock=mock,
                request_id=request_id
            )

        except Exception as e:
            print(f"Error in _stream_model_response for request {request_id}: {e}")
            wx.CallAfter(self._append_response,
                        request_id,
                        f"\n\nError: {str(e)}",
                        False)
        finally:
            print(f"Completing request {request_id}")
            def cleanup():
                print(f"Cleaning up request {request_id}")
                current_thread = threading.current_thread()
                if current_thread in self.active_threads:
                    self._remove_thread(current_thread)
                self.processing = False
                self.ask_model_button.Enable()
                
            wx.CallAfter(cleanup)

    def _create_log_entry(self, user_message, request_id):
        """Creates a new log entry with debug output."""
        print(f"Creating log entry for request {request_id}")
        try:
            safe_message = user_message.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')

            js_script = f"""
                (function() {{
                    var table = document.getElementById('log-container');
                    if (!table) {{
                        console.error('Log container not found');
                        return;
                    }}

                    // Create user message row
                    var userRow = document.createElement('tr');
                    userRow.id = 'user-{request_id}';
                    var userCell = document.createElement('td');
                    var userPrompt = document.createElement('div');
                    userPrompt.className = 'user-prompt';
                    userPrompt.textContent = 'User #{request_id}: {safe_message}';
                    userCell.appendChild(userPrompt);
                    userRow.appendChild(userCell);
                    table.appendChild(userRow);

                    // Create response row
                    var responseRow = document.createElement('tr');
                    responseRow.id = 'response-{request_id}';
                    var responseCell = document.createElement('td');
                    var responseDiv = document.createElement('div');
                    responseDiv.className = 'model-response';
                    responseCell.appendChild(responseDiv);
                    responseRow.appendChild(responseCell);
                    table.appendChild(responseRow);

                    if ({str(self.auto_scroll).lower()}) {{
                        table.scrollTop = table.scrollHeight;
                    }}
                }})();
            """
            print(f"Running script for request {request_id}")
            self.webview.RunScript(js_script)

        except Exception as e:
            print(f"Error creating log entry for request {request_id}: {e}")

    def add_image_as_log_entry(self, base64_image):
        self.image_data = base64_image  
        """Add an image to the snapshot container at the top of the WebView."""
        js_script = """
            (function() {
                try {
                    // Add the image to the snapshot container at the top
                    addSnapshot('%s');
                } catch (error) {
                    console.error('Error adding image:', error);
                }
            })();
        """ % base64_image
        self.webview.RunScript(js_script)


    def on_collapse_button_click(self, event):
       
        print ("on_collapse_button_click", self.is_collapsed, self.processing)  
        """Toggle collapsing or expanding the button panel."""
        if self.is_collapsed:
            # Expand the button panel
            self.splitter.SetSashPosition(int(self.GetSize().y / 3*2))  # Restore to half space
            self.collapse_button.SetLabel("Collapse")
            #self.is_collapsed = False
        else:
            # Collapse the button panel to its minimum height
            self.splitter.SetSashPosition(self.GetSize().y - 100)  # Set sash to near-bottom
            self.collapse_button.SetLabel("Expand")
            #self.is_collapsed = True

        # Toggle the collapsed state
        self.is_collapsed = not self.is_collapsed

    def on_mouse_enter_webview(self, event):
        """Handle mouse entering the WebView."""
        print("Mouse entered WebView.", self.is_collapsed)
        if  self.processing:
            print("on_mouse_enter_webview disabled due to current state.")
            return  
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
        if  self.processing:
            print("on_mouse_enter_button_panel disabled due to current state.")
            return
        if self.is_collapsed:
            self.on_collapse_button_click(None)  # Collapse WebView and expand Bottom Panel
        event.Skip()

    def on_mouse_leave_panel(self, event):
        """Handle mouse leaving the bottom button panel."""
        # Exit early if "Ask Model" is disabled or streaming is active
        if  self.processing:
            print("on_mouse_leave_panel disabled due to current state.")
            return

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


    def set_initial_content(self, webview = None):
        if not webview:
            webview = self.webview
        initial_html = """
        <html>
        <head>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #2d2d2d;
            }

            #snapshot-container {
                padding: 16px;
                border-bottom: 1px solid #e5e7eb;
                background-color: #f9fafb;
            }

            #log-container {
                padding: 16px;
                max-height: calc(100vh - 150px);
                overflow-y: auto;
            }

            #snapshot-label {
                margin: 0 0 8px 0;
                font-weight: 600;
                color: #374151;
            }

            .snapshot-image {
                max-width: 150px;
                height: auto;
                margin: 4px 0;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
            }

           .user-prompt {
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                color: white;
                padding: 12px 16px;
                border-radius: 8px;
                margin: 8px 0;  /* Reduced from 16px to 8px */
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            .model-response {
                position: relative;
                padding: 16px;
                margin: 8px 0;  /* Reduced from 16px to 8px */
                border-left: 4px solid #2563eb;
                background-color: #f8fafc;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 13px;
                white-space: break-spaces;
                word-wrap: break-word;
                tab-size: 4;
                -moz-tab-size: 4;
            }

            .model-response pre {
                margin: 12px 0;
                padding: 16px;
                border-radius: 6px;
                background-color: #1e293b;
                color: #e2e8f0;
                overflow-x: auto;
                white-space: pre;
            }

            .model-response code {
                font-family: inherit;
                tab-size: 4;
                -moz-tab-size: 4;
            }

            table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
            }

            td {
                padding: 4px 8px;  /* Reduced top/bottom padding from 8px to 4px */
                vertical-align: top;
            }

            /* Add spacing between response groups instead */
            tr + tr {
                margin-top: 16px;
            }


            .code-block {
                position: relative;
                margin: 16px 0;
                background-color: #1e293b;
                border-radius: 6px;
                overflow: hidden;
            }

            .code-block pre {
                margin: 0;
                padding: 16px;
                overflow-x: auto;
            }
        </style>
        </head>
        <body>
            <div id="snapshot-container">
                <div id="snapshot-label">Recent Snapshots:</div>
                <div id="snapshot-images"></div>
            </div>

            <table id="log-container">
            </table>

            <script>
                function addSnapshot(base64Image) {
                    const snapshotImages = document.getElementById('snapshot-images');
                    const img = document.createElement('img');
                    img.src = 'data:image/png;base64,' + base64Image;
                    img.className = 'snapshot-image';
                    img.loading = 'lazy';
                    snapshotImages.insertBefore(img, snapshotImages.firstChild);
                }

                function formatCodeBlocks(element) {
                    const text = element.textContent;
                    const lines = text.split('\\n');
                    
                    // Check if this looks like a code block
                    const hasIndentation = lines.some(line => line.startsWith('    ') || line.startsWith('\\t'));
                    const hasCodeMarkers = text.includes('```') || (text.includes('def ') && text.includes('return'));
                    
                    if (hasIndentation || hasCodeMarkers) {
                        const codeBlock = document.createElement('div');
                        codeBlock.className = 'code-block';
                        const pre = document.createElement('pre');
                        pre.textContent = text;
                        codeBlock.appendChild(pre);
                        element.innerHTML = '';
                        element.appendChild(codeBlock);
                    }
                }

                // Handle text selection events
                document.addEventListener('mouseup', function() {
                    const selectedText = window.getSelection().toString();
                    if (selectedText) {
                        window.location.href = 'app://selection?text=' + encodeURIComponent(selectedText);
                    }
                });

                document.addEventListener('contextmenu', function(event) {
                    const selectedText = window.getSelection().toString();
                    event.preventDefault();
                    if (selectedText) {
                        window.location.href = 'app://selection?text=' + encodeURIComponent(selectedText);
                    } else {
                        window.location.href = 'app://show_back_menu';
                    }
                });
            </script>
        </body>
        </html>
        """
        webview.SetPage(initial_html, "")



class ControlPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(ControlPanel, self).__init__(parent, *args, **kwargs)
        hpanel=self
        main_hbox = wx.BoxSizer(wx.HORIZONTAL)
        hpanel.SetSizer(main_hbox)          
        

        # Left side vertical sizer for thumbnails and buttons
        thumbnail_vbox = wx.BoxSizer(wx.VERTICAL)

        # Scrollable thumbnail panel at the top
        self.thumbnail_scroll_panel = ThumbnailScrollPanel(hpanel, size=(150, 200))
        thumbnail_vbox.Add(self.thumbnail_scroll_panel, 0, wx.EXPAND | wx.ALL, 5)

        # Add New Coordinates button directly under thumbnail panel
        add_coordinates_button = wx.Button(hpanel, label="Add New\nCoordinates")
        add_coordinates_button.Bind(wx.EVT_BUTTON, self.add_new_coordinates)
        thumbnail_vbox.Add(add_coordinates_button, 0, wx.EXPAND | wx.ALL, 5)

        # Add stretchable space between top and bottom buttons
        thumbnail_vbox.AddStretchSpacer(1)

        # Bottom buttons section
        bottom_buttons_vbox = wx.BoxSizer(wx.VERTICAL)

        # Create and add bottom buttons
        screenshot_btn = wx.Button(hpanel, label="Take\nScreenshot")
        screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_single_screenshot())
        bottom_buttons_vbox.Add(screenshot_btn, 0, wx.EXPAND | wx.ALL, 2)

        self.group_screenshot_btn=group_screenshot_btn = wx.Button(hpanel, label="Take Group\nScreenshot")
        group_screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_group_screenshot())
        bottom_buttons_vbox.Add(group_screenshot_btn, 0, wx.EXPAND | wx.ALL, 2)

        end_group_btn = wx.Button(hpanel, label="End\nGroup")
        end_group_btn.Bind(wx.EVT_BUTTON, lambda evt: self.end_group())
        bottom_buttons_vbox.Add(end_group_btn, 0, wx.EXPAND | wx.ALL, 2)

        self.coord_btn =coord_btn= wx.Button(hpanel, label="Update\nCoordinates")
        #coord_btn.Bind(wx.EVT_BUTTON, self.open_overlay)
        bottom_buttons_vbox.Add(coord_btn, 0, wx.EXPAND | wx.ALL, 2)

        self.save_btn=save_btn = wx.Button(hpanel, label="Save\nScreenshot")
        #save_btn.Bind(wx.EVT_BUTTON, self.save_screenshot)
        bottom_buttons_vbox.Add(save_btn, 0, wx.EXPAND | wx.ALL, 2)

        self.show_webview_btn = wx.Button(hpanel, label="Hide Webview")
        #self.show_webview_btn.Bind(wx.EVT_BUTTON, self.on_show_webview)
        #hpanel.show_webview_btn.Bind(wx.EVT_BUTTON, self.on_show_webview)  
        bottom_buttons_vbox.Add(self.show_webview_btn, 0, wx.EXPAND | wx.ALL, 2)

        # Add bottom buttons section to main vertical sizer
        thumbnail_vbox.Add(bottom_buttons_vbox, 0, wx.EXPAND | wx.ALL, 5)

        # Add the left side to main horizontal sizer
        main_hbox.Add(thumbnail_vbox, 0, wx.EXPAND | wx.ALL, 5)

        # Create the middle section with group and coordinates lists
        left_vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.group_list = wx.ListBox(hpanel, style=wx.LB_SINGLE)
        self.group_list.Bind(wx.EVT_LISTBOX, self.on_group_selected)
        left_vbox.Add(self.group_list, 1, wx.EXPAND | wx.ALL, 5)

        self.coordinates_listbox = wx.ListBox(hpanel, style=wx.LB_SINGLE)
        self.coordinates_listbox.Bind(wx.EVT_LISTBOX, self.on_coordinates_listbox_selection)
        left_vbox.Add(self.coordinates_listbox, 1, wx.EXPAND | wx.ALL, 5)

        main_hbox.Add(left_vbox, 0, wx.EXPAND | wx.ALL, 5)
        self.show_webview_btn.SetLabel("Show Webview")
        self.screenshot_groups = {}
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
        self.update_status(0,f"Selected group: '{selected_group}'")
    def end_group(self):
        """End the current group and finalize it."""
        if self.current_group:
            screenshots = len(self.screenshot_groups.get(self.current_group, []))
            # Update the status bar with the group completion message
            self.update_status(0,
                f"Group '{self.current_group}' finalized with {screenshots} screenshots!"
            )
            self.current_group = None
        else:
            # Update the status bar with an error message
            self.update_status(0,"No group is currently active.")

    def on_coordinates_selected(self, pil_image, thumbnail, coordinates):
        """Handle the selection and add new coordinates."""
        if not coordinates:
            wx.MessageBox("No valid coordinates found.", "Error", wx.OK | wx.ICON_ERROR)
            return

        self.current_coordinates = coordinates  # Store the selected coordinates

        # Create a unique label
        new_label = f"Coordinates {len(self.thumbnail_scroll_panel.sizer.GetChildren()) + 1}"

        # Add thumbnail to the scroll panel
        toggle_button = self.thumbnail_scroll_panel.add_thumbnail_button(pil_image, thumbnail, label=new_label)

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
        self.update_status(0,f"Added and toggled new coordinates as '{new_label}'")
        wx.CallAfter(self.take_single_screenshot)

    def take_single_screenshot(self):
        global is_autoexec
        """Take screenshots for all toggled thumbnail buttons and display them in a single scrollable panel."""
        # Clear the coordinates list box for the new group
        main_frame = self.GetParent().GetParent().GetParent().GetParent()  # Reference to the main frame
        coord_panel=self.GetParent().GetParent().GetParent()
        notebook=coord_panel.notebook
        webview_panel=coord_panel.webview_panel
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
                self.single_screenshot_tab = wx.ScrolledWindow(notebook)
                self.single_screenshot_tab.SetScrollRate(10, 10)
                self.single_screenshot_tab_sizer = wx.BoxSizer(wx.VERTICAL)
                self.single_screenshot_tab.SetSizer(self.single_screenshot_tab_sizer)
                notebook.AddPage(self.single_screenshot_tab, f"Single Screenshots ({group_name})")
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
                        webview_panel.add_image_as_log_entry(base64_image)
                        
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
            notebook.SetSelection(notebook.GetPageCount() - 1)

            # Update the status bar
            self.update_status(0,
                f"Captured {len(toggled_buttons)} screenshots in group '{group_name}'."
            )

        finally:
            self.show_frame(main_frame)  # Show the main frame again

        #webview_panel = self.webview_panel
        assert webview_panel is not None, "WebViewPanel is not available!"
        assert webview_panel.webview is not None, "WebView is not available!"
        assert webview_panel.image_data is not None , "Image data is not available!"
        #self.trigger_image_description(pil_image, thumbnail, coordinates)
        # At the end of the try block, right after self.show_frame(main_frame):

        if is_autoexec:
            wx.CallAfter(webview_panel.on_ask_model_button_click, None)
    def bitmap_to_base64(self, bitmap):
        """Convert a wx.Bitmap to a base64-encoded PNG image."""
        image = bitmap.ConvertToImage()
        stream = io.BytesIO()
        image.SaveFile(stream, wx.BITMAP_TYPE_PNG)
        base64_image = base64.b64encode(stream.getvalue()).decode('utf-8')
        return base64_image            
    def show_frame(self,main_frame):

        # Show the main frame again
             
        main_frame.Iconize(False)
        main_frame.Show()
        wx.Yield()  # Allow UI to process the show event




                        
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
            self.update_status(0,f"Scrolled to coordinate {selected_index + 1}")


    def update_status(self, field, message):
        self.GetParent().GetParent().GetParent().update_status(field, message)
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
        parent_frame.panel.update_status(0,
            f"Added screenshot to '{self.current_group}'. Total: {len(self.screenshot_groups[self.current_group])}"
        )
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
    def add_group(self, group_name):
        
        self.update_status(2, f"Current Group: {group_name}")        
        """Add a new screenshot group."""
        if group_name in self.screenshot_groups:
            # Avoid duplicate groups
            self.update_status(0,f"Group '{group_name}' already exists.")
            return

        # Create a new group and add it to the list
        self.screenshot_groups[group_name] = []
        self.add_list_item(group_name)
        self.current_group = group_name

        # Update the status bar
        self.update_status(0,f"Started new group: '{group_name}'")            
    def add_list_item(self, item_name):
        """Add an item to the group list."""
        self.group_list.Append(item_name)
        self.group_list.SetSelection(self.group_list.GetCount() - 1)
class CoordinatesPanel(wx.Panel):
    def __init__(self, parent, coordinates, callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.coordinates = coordinates
        self.callback = callback
        
        self.current_group = None
        self.current_coordinates = None

        # Main horizontal sizer for overall layout
        # Main horizontal layout with splitter
        self.hsplitter = wx.SplitterWindow(self)

        self.vsplitter = wx.SplitterWindow(self.hsplitter)
        self.hpanel=hpanel=ControlPanel(self.vsplitter)
    
        if 1:

            # Set the initial button state
            

            # Set the initial button state
            
                    
            hpanel.coord_btn.Bind(wx.EVT_BUTTON, self.open_overlay)
            hpanel.save_btn.Bind(wx.EVT_BUTTON, self.save_screenshot)
            hpanel.show_webview_btn.Bind(wx.EVT_BUTTON, self.on_show_webview)  
            #hpanel.group_screenshot_btn.Bind(wx.EVT_BUTTON, lambda evt: self.take_group_screenshot())

            self.Bind(wx.EVT_SIZE, self.on_size) # Allocate 75% to the notebook

        if 1:


            # Left panel for the notebook
            self.notebook_panel = wx.Panel(self.vsplitter)
            notebook_sizer = wx.BoxSizer(wx.VERTICAL)

            self.notebook = wx.Notebook(self.notebook_panel)
            self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_notebook_page_changed)
            notebook_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

            self.notebook_panel.SetSizer(notebook_sizer)
            # Right panel for WebView

        if 1:
            # Configure splitter
            self.vsplitter.SplitHorizontally(hpanel, self.notebook_panel)

            # Set the sash position to ensure WebView is visible initially
            self.vsplitter.SetSashPosition(550, redraw=True)  # Allocate 50% to both
            #self.splitter.SetMinimumPaneSize(int(self.GetSize().x-150)) 
            self.vsplitter.Layout() 

        if 1:
            self.webview_panel = WebViewPanel(self.hsplitter)
            self.hsplitter.SplitVertically(self.vsplitter, self.webview_panel)
            # Set the sash position to ensure WebView is visible initially
            self.hsplitter.SetSashPosition(550, redraw=True)  # Allocate 50% to both
            #self.splitter.SetMinimumPaneSize(int(self.GetSize().x-150)) 
            self.hsplitter.Layout()             

        main_vbox   = wx.BoxSizer(wx.VERTICAL)
        main_vbox.Add(self.hsplitter, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_vbox)


    def on_show_webview(self, event=None, button=None):
        """Toggle the splitter sash position and update the button label."""
        if not button:  # Use the button reference if provided
            button = event.GetEventObject() if event else self.hpanel.show_webview_btn

        current_label = button.GetLabel()
        total_width = self.GetSize().x

        # Determine the new sash position based on the current label
        if current_label == "Show Webview":
            # Move sash to allocate more space to WebView
            new_position = 150  # Minimal space for notebook
            button.SetLabel("Hide Webview")
            self.update_status(0,"WebView panel shown.")
        else:
            # Move sash to allocate more space to the notebook
            new_position = total_width - 150  # Minimal space for WebView
            button.SetLabel("Show Webview")
            self.update_status(0,"WebView panel minimized.")

        # Adjust the sash position
        self.hsplitter.SetSashPosition(new_position, redraw=True)
        self.hsplitter.Layout()
        self.Layout()
    def open_overlay(self, event):
        self.Hide()
        self.callback()        
    def on_size(self, event):
        """Adjust the sash position after the panel is resized."""
        self.hsplitter.SetSashPosition(int(self.GetSize().x * 0.75))  # Allocate 75% to the notebook
        self.Unbind(wx.EVT_SIZE)  # Unbind to avoid repeated adjustments
        event.Skip()







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
            #self.GetParent().status_bar.SetStatusText(f"All screenshots in group '{selected_group}' saved to {group_dir}")
            self.update_status(0, "Screenshots saved successfully!")
        else:
            #wx.MessageBox("Save operation cancelled.", "Info", wx.OK | wx.ICON_INFORMATION)
            self.update_status(0,"Save operation cancelled.")











    def update_coordinates(self, new_coordinates):
        self.coordinates = new_coordinates


    def update_status(self, field, message):
        status_bar=self.GetParent().status_bar
        """Update a specific field in the status bar."""
        if 0 <= field < status_bar.GetFieldsCount():
            status_bar.SetStatusText(message, field)





class CoordinatesFrame(wx.Frame):
    def __init__(self, coordinates, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize coordinates
        self.coordinates = coordinates  # Set coordinates here
        self.callback = callback
        self.screenshot_bitmap = None
        self.canvas_size = (700, 600)  # Fixed canvas size

        self.SetTitle("Multi Area Screenshot")
        self.SetSize((1800, 1800))

        # Add the CoordinatesPanel
        self.panel = CoordinatesPanel(self, coordinates, callback)
        self.Center()

        # Add a status bar
        self.status_bar = self.CreateStatusBar(3)
        self.status_bar.SetStatusWidths([-2, -1, -1])
        self.status_bar.SetStatusText("Ready")  # Default message
        self.status_bar.SetStatusText("Ready", 0)  # Default message for field 0
        self.status_bar.SetStatusText("Monitor: Not Selected", 1)
        self.status_bar.SetStatusText("No Active Group", 2)        



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
            self.coordinates_frame.panel.update_status(0,
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
        self.coordinates_frame.panel.update_status(0,"Full screenshot captured.")


    def show_monitor_selection_dialog(self):
        global is_mock, is_autoexec
        dialog = MonitorSelectionDialog(None)
        dialog.CenterOnScreen()
        if dialog.ShowModal() == wx.ID_OK:
            selected_monitor = dialog.radio_box.GetSelection() + 1
            global is_mock
            is_mock = dialog.get_mock_state()
            is_autoexec = dialog.get_auto_execute()
            dialog.Destroy()
            print(f"Selected Monitor: {selected_monitor}, Mock Mode: {is_mock}")
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
        if hasattr(self.coordinates_frame.panel.hpanel, 'on_coordinates_selected'):
            self.coordinates_frame.panel.hpanel.on_coordinates_selected(pil_image, thumbnail, coordinates)


        











if __name__ == "__main__":
    app = ScreenshotApp()


    app.MainLoop()