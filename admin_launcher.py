#!/usr/bin/env python
"""
Cruise Logs Admin Launcher
Password-protected administrative tools for database management
"""

import customtkinter as ctk
import subprocess
import sys
import os
import threading
from pathlib import Path
import hashlib

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Password configuration
# Default password is "admin123" - Change the hash below to set a new password
# To generate a new hash: hashlib.sha256("your_password".encode()).hexdigest()
PASSWORD_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # admin123


class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Admin Authentication")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)

        self.password = None
        self.authenticated = False

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="🔐 Administrator Access Required",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))

        # Info label
        info_label = ctk.CTkLabel(
            self,
            text="Please enter the administrator password:",
            font=ctk.CTkFont(size=12)
        )
        info_label.pack(pady=(0, 20))

        # Password entry
        self.password_entry = ctk.CTkEntry(
            self,
            width=300,
            placeholder_text="Enter password",
            show="●"
        )
        self.password_entry.pack(pady=10)
        self.password_entry.bind("<Return>", lambda e: self.check_password())
        self.password_entry.focus()

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        # OK button
        ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            width=120,
            command=self.check_password
        )
        ok_button.pack(side="left", padx=5)

        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            command=self.cancel,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_button.pack(side="left", padx=5)

        # Error label (hidden initially)
        self.error_label = ctk.CTkLabel(
            self,
            text="",
            text_color="red",
            font=ctk.CTkFont(size=11)
        )
        self.error_label.pack()

        # Force geometry update and center after all widgets are created
        self.update_idletasks()
        width = 400
        height = 200
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Ensure dialog is visible and focused
        self.grab_set()
        self.focus_force()
        self.lift()

    def check_password(self):
        """Verify the entered password"""
        entered_password = self.password_entry.get()
        entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()

        if entered_hash == PASSWORD_HASH:
            self.authenticated = True
            self.destroy()
        else:
            self.error_label.configure(text="❌ Incorrect password. Please try again.")
            self.password_entry.delete(0, 'end')
            self.password_entry.focus()

    def cancel(self):
        """Cancel authentication"""
        self.authenticated = False
        self.destroy()


class AdminLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Cruise Logs - Admin Tools")
        self.geometry("900x700")

        # Center window on screen
        self.center_window()

        # Set minimum window size
        self.minsize(800, 600)

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Create header
        self.create_header()

        # Create main button frame
        self.create_button_frame()

        # Create output display
        self.create_output_display()

        # Create footer
        self.create_footer()

        # Protocol for window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = 900
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_header(self):
        """Create the header section"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔐 Admin Tools - Database Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 5))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Import data and manage database tables",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack()

        # Warning
        warning_label = ctk.CTkLabel(
            header_frame,
            text="⚠️ Caution: These tools modify the database directly",
            font=ctk.CTkFont(size=11),
            text_color="orange"
        )
        warning_label.pack(pady=(5, 0))

    def create_button_frame(self):
        """Create the main button grid"""
        # Main container
        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.grid(row=1, column=0, padx=40, pady=20, sticky="nsew")
        button_container.grid_rowconfigure((0, 1), weight=1)
        button_container.grid_columnconfigure((0, 1, 2), weight=1)

        # Import script definitions
        import_scripts = [
            {
                "name": "Import Deployment",
                "icon": "⬇️",
                "file": "import_dep.py",
                "description": "Import deployment XML",
                "color": "#2d5f8d",
                "requires_file": True,
                "file_ext": ".xml"
            },
            {
                "name": "Import Recovery",
                "icon": "⬆️",
                "file": "import_rec.py",
                "description": "Import recovery XML",
                "color": "#3d6f9d",
                "requires_file": True,
                "file_ext": ".xml"
            },
            {
                "name": "Import Repair",
                "icon": "🔧",
                "file": "import_repair.py",
                "description": "Import repair XML",
                "color": "#4d7fad",
                "requires_file": True,
                "file_ext": ".xml"
            },
            {
                "name": "Import ADCP Deploy",
                "icon": "📡",
                "file": "import_adcp_dep.py",
                "description": "Import ADCP deployment",
                "color": "#2d7f5f",
                "requires_file": True,
                "file_ext": ".xml"
            },
            {
                "name": "Import ADCP Recovery",
                "icon": "📥",
                "file": "import_adcp_rec.py",
                "description": "Import ADCP recovery",
                "color": "#3d8f6f",
                "requires_file": True,
                "file_ext": ".xml"
            },
            {
                "name": "Import Releases",
                "icon": "🔍",
                "file": "import_release_inventory.py",
                "description": "Import Equipment.xls",
                "color": "#8d6f3d",
                "requires_file": False
            },
            {
                "name": "Import Nylon",
                "icon": "🧵",
                "file": "import_nylon_inventory.py",
                "description": "Import nylon spools",
                "color": "#9d7f4d",
                "requires_file": False
            }
        ]

        # Create buttons in grid (3 columns)
        for idx, script in enumerate(import_scripts):
            row = idx // 3
            col = idx % 3
            self.create_import_button(button_container, script, row, col)

    def create_import_button(self, parent, script, row, col):
        """Create an individual import button"""
        # Button frame
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Main button
        button = ctk.CTkButton(
            button_frame,
            text=f"{script['icon']}\n{script['name']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=80,
            corner_radius=10,
            command=lambda s=script: self.run_import(s),
            hover_color=script['color']
        )
        button.pack(fill="both", expand=True)

        # Description label
        desc_label = ctk.CTkLabel(
            button_frame,
            text=script['description'],
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        desc_label.pack(pady=(5, 0))

    def create_output_display(self):
        """Create the output console display"""
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # Label
        output_label = ctk.CTkLabel(
            output_frame,
            text="📋 Output Console",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        output_label.pack(fill="x", padx=10, pady=(10, 5))

        # Text widget for output
        self.output_text = ctk.CTkTextbox(
            output_frame,
            height=200,
            font=ctk.CTkFont(family="Courier", size=10)
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial message
        self.log_output("Ready. Select an import tool above to begin.\n")

    def create_footer(self):
        """Create the footer with controls"""
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Clear output button
        clear_button = ctk.CTkButton(
            footer_frame,
            text="🗑️ Clear Output",
            width=150,
            command=self.clear_output
        )
        clear_button.pack(side="left", padx=5)

        # Theme toggle
        theme_button = ctk.CTkButton(
            footer_frame,
            text="🌙 Toggle Theme",
            width=150,
            command=self.toggle_theme
        )
        theme_button.pack(side="left", padx=5)

        # Exit button
        exit_button = ctk.CTkButton(
            footer_frame,
            text="Exit",
            width=150,
            command=self.on_closing,
            fg_color="gray",
            hover_color="darkgray"
        )
        exit_button.pack(side="right", padx=5)

    def run_import(self, script):
        """Run an import script"""
        script_name = script['name']
        script_file = script['file']

        # Check if file exists
        if not os.path.exists(script_file):
            self.log_output(f"❌ Error: {script_file} not found!\n", error=True)
            return

        # Check if we need to select an XML file
        xml_file = None
        if script.get('requires_file', False):
            from tkinter import filedialog
            xml_file = filedialog.askopenfilename(
                title=f"Select XML file for {script_name}",
                filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
            )
            if not xml_file:
                self.log_output(f"⚠️ Import cancelled - no file selected\n", warning=True)
                return

        # Run in a separate thread
        thread = threading.Thread(
            target=self._run_import_thread,
            args=(script_name, script_file, xml_file)
        )
        thread.daemon = True
        thread.start()

    def _run_import_thread(self, script_name, script_file, xml_file=None):
        """Run import script in a background thread"""
        try:
            self.log_output(f"\n{'='*60}\n")
            self.log_output(f"🚀 Running: {script_name}\n")
            if xml_file:
                self.log_output(f"📁 File: {xml_file}\n")
            self.log_output(f"{'='*60}\n")

            # Build command
            cmd = [sys.executable, script_file]
            if xml_file:
                cmd.append(xml_file)

            # Run the import script
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Read output line by line
            for line in process.stdout:
                self.log_output(line)

            # Wait for completion
            return_code = process.wait()

            if return_code == 0:
                self.log_output(f"\n✅ {script_name} completed successfully!\n", success=True)
            else:
                self.log_output(f"\n❌ {script_name} failed with error code {return_code}\n", error=True)

        except Exception as e:
            self.log_output(f"\n❌ Error running {script_name}: {str(e)}\n", error=True)

    def log_output(self, message, error=False, warning=False, success=False):
        """Add message to output console"""
        self.output_text.insert("end", message)
        self.output_text.see("end")
        self.output_text.update()

    def clear_output(self):
        """Clear the output console"""
        self.output_text.delete("1.0", "end")
        self.log_output("Output cleared.\n")

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def on_closing(self):
        """Handle window close event"""
        self.destroy()


def main():
    """Main entry point"""
    # Check if customtkinter is installed
    try:
        import customtkinter
    except ImportError:
        print("Error: customtkinter is not installed.")
        print("Install it with: pip install customtkinter")
        sys.exit(1)

    # Create the admin launcher but keep it hidden
    app = AdminLauncher()
    app.withdraw()  # Hide the main window initially

    # Show password dialog
    password_dialog = PasswordDialog(app)
    app.wait_window(password_dialog)

    # Check if authenticated
    if not password_dialog.authenticated:
        print("Authentication cancelled.")
        app.destroy()
        sys.exit(0)

    # Authentication successful - show the main window
    app.deiconify()
    app.mainloop()


if __name__ == "__main__":
    main()
