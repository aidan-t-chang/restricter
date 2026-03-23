import uuid
import hashlib
import platform
import random
import string
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import importlib.util
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("rcconfig.json")
firebase_admin.initialize_app(cred, {'databaseURL': "https://restricter-connector-default-rtdb.firebaseio.com/"})
ref = db.reference()

# Load ai-commandtoggle.py (hyphen in filename prevents normal import)
_ct_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-commandtoggle.py")
_spec = importlib.util.spec_from_file_location("ai_commandtoggle", _ct_path)
ct = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ct)

COMMANDS = {
    1: ct.toggle_edge,
    2: ct.toggle_chrome,
    3: ct.toggle_cmd,
    4: ct.toggle_total_lockdown,
    5: ct.toggle_regedit,
    6: ct.toggle_msi_installer,
    7: ct.toggle_microsoft_store,
}

class RestricterDesktop:
    def __init__(self):
        self.desktop_id = self.get_or_create_desktop_id()
        self.last_rolling_code = 0
        self.setup_gui()

    def generate_desktop_id(self):
        characters = string.ascii_uppercase + string.digits
        safe_characters = ''.join(c for c in characters if c not in '01IO')
        return ''.join(random.choices(safe_characters, k=8))
    
    def generate_desktop_id_from_machine(self):
        machine_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
        hash_object = hashlib.md5(machine_info.encode())
        hex_dig = hash_object.hexdigest()
        raw_id = hex_dig[:8].upper()
        readable_id = raw_id.replace('0', 'Z').replace('1', 'Y')
        return readable_id
    
    def generate_desktop_id_uuid(self):
        uuid_str = str(uuid.uuid4()).replace('-', '').upper()
        raw_id = uuid_str[:8]
        readable_id = raw_id.replace('0', 'Z').replace('1', 'Y').replace('O', 'P').replace('I', 'J')
        return readable_id
    
    def get_or_create_desktop_id(self):
        config_file = "restricter_config.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    desktop_id = config.get('desktop_id')
                    if desktop_id and len(desktop_id) == 8:
                        try: 
                            ref.set({
                                # last toggle allows for checking whether to update and run the script
                                # rolling code allows checking for toggles/running same command twice
                                desktop_id: {
                                    "uid" : -1,
                                    "cmd_value" : -1,
                                    "connected" : False,
                                    "rolling_code" : 0,
                                    "applications" : [], # not entirely sure what these would be stored as
                                }
                            })
                            print(f"successfully saved to database {desktop_id}")
                        except Exception as e:
                            print(f"failed to update the database: {e}")       
                        return desktop_id
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # use the desktop id as the key in the firebase rtdb
        desktop_id = self.generate_desktop_id()

        config = {
            'desktop_id': desktop_id,
            'created_at': time.time(),
            'machine_name': platform.node(),
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")

        try: 
            ref.set({
                desktop_id: {
                    "uid" : -1,
                    "cmd_value" : -1,
                    "connected" : False,
                    "rolling_code" : 0,
                } 
            })
            print(f"config file didn't exist. successfully saved to database {desktop_id}")
        except Exception as e:
            print(f"failed to update the database: {e}")       

        return desktop_id
    
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Restricter Desktop")
        self.root.geometry("750x600")
        self.root.resizable(False, False)
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(
            main_frame, 
            text="Restricter Desktop", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        id_frame = ttk.LabelFrame(main_frame, text="Your Desktop ID", padding="15")
        id_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.id_label = ttk.Label(
            id_frame, 
            text=self.desktop_id, 
            font=("Courier", 24, "bold"), 
            foreground="blue"
        )
        self.id_label.pack(pady=10)
        
        copy_button = ttk.Button(
            id_frame, 
            text="Copy ID", 
            command=self.copy_id
        )
        copy_button.pack(pady=5)

        # Status & actions box
        status_frame = ttk.LabelFrame(main_frame, text="Status & Actions", padding="15")
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(
            status_frame,
            text="Status: Ready for connection",
            foreground="orange"
        )
        self.status_label.pack(anchor="w")

        regenerate_button = ttk.Button(
            status_frame,
            text="Generate New ID",
            command=self.regenerate_id
        )
        regenerate_button.pack(pady=(10, 5), anchor="w")

        unrestrict_button = ttk.Button(
            status_frame,
            text="Unrestrict Everything (Emergency)",
            command=self.unrestrict_everything
        )
        unrestrict_button.pack(pady=(5, 5), anchor="w")

        # Instructions box now placed AFTER status/actions
        instructions_frame = ttk.LabelFrame(main_frame, text="How to Connect", padding="15")
        instructions_frame.pack(fill=tk.X, pady=(15, 0))

        instructions_text = """1. Open the Restricter mobile app
    2. Sign in to your account
    3. Tap the computer icon (red/green button)
    4. Enter the Desktop ID shown above
    5. Give your desktop a name
    6. Tap 'Connect'

    Your desktop will then receive commands from your mobile app."""

        instructions_label = ttk.Label(
            instructions_frame,
            text=instructions_text,
            justify=tk.LEFT,
            wraplength=400
        )
        instructions_label.pack(anchor="w")

        self.poll_connection_status()
        self.check_cmd_value()
        threading.Thread(target=self._publish_dynamic_apps, daemon=True).start()
    
    def copy_id(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.desktop_id)
            self.show_status("Desktop ID copied to clipboard!", "green")
        except Exception as e:
            self.show_status(f"Error copying: {e}", "red")
    
    def regenerate_id(self):
        if messagebox.askyesno("Regenerate ID", 
                             "Are you sure you want to generate a new Desktop ID?\n\n"
                             "This will disconnect any existing mobile app connections."):

            # delete old desktop id from the database
            old_desktop_id = self.desktop_id
            try:
                ref.child(old_desktop_id).delete()
                print(f"Successfully deleted old desktop ID from database: {old_desktop_id}")
            except Exception as e:
                print(f"Warning: Could not delete old ID from database: {e}")
            
            try:
                if os.path.exists("restricter_config.json"):
                    os.remove("restricter_config.json")
            except Exception as e:
                print(f"Warning: Could not remove config file: {e}")
            
            self.desktop_id = self.get_or_create_desktop_id()
            self.id_label.config(text=self.desktop_id)
            self.show_status("New Desktop ID generated!", "green")

    def unrestrict_everything(self):
        if not messagebox.askyesno("Emergency Unrestrict", 
                                   "This will remove ALL AppLocker restrictions and re-enable Command Prompt.\n\n"
                                   "Are you sure you want to proceed?"):
            return
    
    def show_status(self, message, color="black"):
        self.status_label.config(text=f"Status: {message}", foreground=color)
        self.root.after(3000, lambda: self.status_label.config(
            text="Status: Ready for connection", foreground="orange"
        ))

    def check_connection(self):
        try:
            connected = ref.child(self.desktop_id).child("connected").get()
            return bool(connected)
        except Exception as e:
            print(f"Error checking connection status: {e}")
            return False

    def poll_connection_status(self):
        connected = self.check_connection()
        if connected:
            self.status_label.config(text="Status: Connected to mobile app", foreground="green")
        else:
            self.status_label.config(text="Status: Waiting for mobile app", foreground="orange")
        
        # check every 5 seconds
        self.root.after(5000, self.poll_connection_status)

    def check_cmd_value(self):
        new_cmd_value = ref.child(self.desktop_id).child('cmd_value').get()
        new_rolling_code = ref.child(self.desktop_id).child('rolling_code').get()

        if self.last_rolling_code != new_rolling_code:
            print(f'rolling code updated. new cmd value: {new_cmd_value}')
            self.last_rolling_code = new_rolling_code
            threading.Thread(
                target=self._dispatch_command,
                args=(new_cmd_value,),
                daemon=True,
            ).start()

        self.root.after(1000, self.check_cmd_value)

    def _publish_dynamic_apps(self):
        """Scan installed apps and publish the list to Firebase."""
        try:
            apps = ct.get_installed_apps()
            app_list = [{"name": a["name"], "exe": a["exe"]} for a in apps]
            ref.child(self.desktop_id).child("dynamic_apps").set(app_list)
            print(f"Published {len(app_list)} dynamic apps to Firebase")
        except Exception as e:
            print(f"Error publishing dynamic apps: {e}")

    def _dispatch_command(self, cmd_value):
        try:
            if cmd_value == 9:
                app_exe = ref.child(self.desktop_id).child('app_exe').get()
                if app_exe:
                    ct.ifeo_toggle(app_exe, app_exe)
                    self.root.after(0, lambda: self.show_status(f"Toggled {app_exe}", "blue"))
                else:
                    print("cmd_value=9 received but no app_exe set in database")
            else:
                handler = COMMANDS.get(cmd_value)
                if handler:
                    handler()
                    self.root.after(0, lambda: self.show_status(f"Command {cmd_value} executed", "blue"))
                else:
                    print(f"Unknown cmd_value: {cmd_value}")
        except Exception as e:
            print(f"Error dispatching command {cmd_value}: {e}")
         
    
    def run(self):
        print(f"Restricter Desktop starting...")
        print(f"Desktop ID: {self.desktop_id}")
        print(f"Machine: {platform.node()}")
        
        self.root.mainloop()

def main():
    try:
        app = RestricterDesktop()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")

main()