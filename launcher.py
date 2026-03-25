#!/usr/bin/env python
"""
Cruise Logs Application Launcher
A modern GUI launcher for Cruise_Logs Streamlit applications
"""

import customtkinter as ctk
import subprocess
import sys
import os
import threading
from pathlib import Path

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"


class CruiseLogsLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Cruise Logs - Application Launcher")
        self.geometry("800x600")

        # Center window on screen
        self.center_window()

        # Set minimum window size
        self.minsize(700, 500)

        # Store running processes
        self.processes = {}

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Create header
        self.create_header()

        # Create main button frame
        self.create_button_frame()

        # Create status bar
        self.create_status_bar()

        # Create footer
        self.create_footer()

        # Protocol for window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = 800
        height = 600
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
            text="🚢 Cruise Logs Management System",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(0, 5))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Select an application to launch",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack()

    def create_button_frame(self):
        """Create the main button grid"""
        # Main container
        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.grid(row=1, column=0, padx=40, pady=20, sticky="nsew")
        button_container.grid_rowconfigure((0, 1, 2), weight=1)
        button_container.grid_columnconfigure((0, 1), weight=1)

        # Application definitions
        apps = [
            {
                "name": "Cruise Form",
                "icon": "🚢",
                "file": "cruise_form.py",
                "description": "Main cruise information",
                "color": "#1f538d"
            },
            {
                "name": "Deployment Form",
                "icon": "⬇️",
                "file": "dep_form_JSON.py",
                "description": "Mooring deployments",
                "color": "#2d5f8d"
            },
            {
                "name": "Recovery Form",
                "icon": "⬆️",
                "file": "rec_form_JSON.py",
                "description": "Mooring recoveries",
                "color": "#3d6f9d"
            },
            {
                "name": "Repair Form",
                "icon": "🔧",
                "file": "repair_form_JSON.py",
                "description": "Equipment repairs",
                "color": "#4d7fad"
            },
            {
                "name": "ADCP Deployment",
                "icon": "📡",
                "file": "adcp_dep_form.py",
                "description": "ADCP deployment records",
                "color": "#2d7f5f"
            },
            {
                "name": "ADCP Recovery",
                "icon": "📥",
                "file": "adcp_rec_form.py",
                "description": "ADCP recovery records",
                "color": "#3d8f6f"
            }
        ]

        # Create buttons in grid
        for idx, app in enumerate(apps):
            row = idx // 2
            col = idx % 2
            self.create_app_button(button_container, app, row, col)

    def create_app_button(self, parent, app, row, col):
        """Create an individual application button"""
        # Button frame
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        # Main button
        button = ctk.CTkButton(
            button_frame,
            text=f"{app['icon']}\n{app['name']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=100,
            corner_radius=10,
            command=lambda a=app: self.launch_app(a),
            hover_color=app['color']
        )
        button.pack(fill="both", expand=True)

        # Description label
        desc_label = ctk.CTkLabel(
            button_frame,
            text=app['description'],
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        desc_label.pack(pady=(5, 0))

    def create_status_bar(self):
        """Create the status bar"""
        self.status_frame = ctk.CTkFrame(self, height=40)
        self.status_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)

    def create_footer(self):
        """Create the footer with additional options"""
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Theme toggle
        theme_button = ctk.CTkButton(
            footer_frame,
            text="🌙 Toggle Theme",
            width=150,
            command=self.toggle_theme
        )
        theme_button.pack(side="left", padx=5)

        # Close all button
        close_all_button = ctk.CTkButton(
            footer_frame,
            text="❌ Close All Apps",
            width=150,
            command=self.close_all_apps,
            fg_color="red",
            hover_color="darkred"
        )
        close_all_button.pack(side="left", padx=5)

        # Exit button
        exit_button = ctk.CTkButton(
            footer_frame,
            text="Exit Launcher",
            width=150,
            command=self.on_closing,
            fg_color="gray",
            hover_color="darkgray"
        )
        exit_button.pack(side="right", padx=5)

    def launch_app(self, app):
        """Launch a Streamlit application"""
        app_name = app['name']
        app_file = app['file']

        # Check if file exists
        if not os.path.exists(app_file):
            self.update_status(f"❌ Error: {app_file} not found!", error=True)
            return

        # Check if already running
        if app_name in self.processes:
            self.update_status(f"⚠️  {app_name} is already running", warning=True)
            return

        # Launch in a separate thread
        thread = threading.Thread(target=self._launch_streamlit, args=(app_name, app_file))
        thread.daemon = True
        thread.start()

    def _launch_streamlit(self, app_name, app_file):
        """Launch Streamlit in a subprocess"""
        try:
            self.update_status(f"🚀 Launching {app_name}...")

            # Launch streamlit
            process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", app_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )

            # Store process
            self.processes[app_name] = process

            self.update_status(f"✅ {app_name} launched successfully!")

        except Exception as e:
            self.update_status(f"❌ Error launching {app_name}: {str(e)}", error=True)

    def close_all_apps(self):
        """Close all running Streamlit applications"""
        if not self.processes:
            self.update_status("No applications running")
            return

        count = len(self.processes)
        for app_name, process in list(self.processes.items()):
            try:
                process.terminate()
                process.wait(timeout=3)
            except:
                process.kill()
            del self.processes[app_name]

        self.update_status(f"✅ Closed {count} application(s)")

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.update_status(f"🎨 Theme changed to {new_mode}")

    def update_status(self, message, error=False, warning=False):
        """Update the status bar message"""
        if error:
            self.status_label.configure(text=message, text_color="red")
        elif warning:
            self.status_label.configure(text=message, text_color="orange")
        else:
            self.status_label.configure(text=message, text_color="green")

        # Reset to default after 5 seconds
        self.after(5000, lambda: self.status_label.configure(text="Ready", text_color="white"))

    def on_closing(self):
        """Handle window close event"""
        if self.processes:
            # Ask for confirmation
            from tkinter import messagebox
            if messagebox.askyesno(
                "Close Launcher",
                f"{len(self.processes)} application(s) are still running.\nClose them all and exit?"
            ):
                self.close_all_apps()
                self.destroy()
        else:
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

    # Check if we're in the right directory
    if not os.path.exists("cruise_form.py"):
        print("Warning: cruise_form.py not found in current directory.")
        print("Make sure you're running this from the Cruise_Logs directory.")

    # Create and run the application
    app = CruiseLogsLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
