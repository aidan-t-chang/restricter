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
import firebase_admin
from firebase_admin import credentials, db
import uuid

cred = credentials.Certificate("rcconfig.json")
firebase_admin.initialize_app(cred, {'databaseURL': "https://restricter-connector-default-rtdb.firebaseio.com/"})
ref = db.reference()

class RestricterDesktop:
    def __init__(self):
        self.desktop_id = self.get_or_create_desktop_id()
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
                            # desktop_id {uid, desktop_id, cmd_value}
                            ref.set({
                                desktop_id: {
                                    "uid" : -1,
                                    "cmd_value" : -1,
                                    "connected" : False
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
                    "connected" : False
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
            text="📋 Copy ID", 
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
    
    def show_status(self, message, color="black"):
        self.status_label.config(text=f"Status: {message}", foreground=color)
        self.root.after(3000, lambda: self.status_label.config(
            text="Status: Ready for connection", foreground="orange"
        ))
    
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