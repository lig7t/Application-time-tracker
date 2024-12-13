import time
import psutil
import json
import os
import subprocess
import threading
from datetime import datetime
from tkinter import Tk, Label, Button, Listbox, MULTIPLE, Entry, Toplevel, messagebox

PATH_FILE = "app_paths.json"
RUNTIME_FILE = "app_runtimes.json"
# tracking = False  # Tracking starts when explicitly enabled
tracking_flag = {"running": False}

# def load_json(file_path):
#     """Load data from a JSON file."""
#     if os.path.exists(file_path):
#         with open(file_path, "r") as file:
#             return json.load(file)
#     return {}

def load_json(file_path):
    """Load data from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                # If JSON is malformed, return empty dict
                return {}
    return {}

def save_json(data, file_path):
    """Save data to a JSON file."""
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

# Initialize runtime for a new application
def initialize_runtime_for_new_app(app_name):
    """Initialize runtime for a newly added app with time 0."""
    runtime_data = load_json(RUNTIME_FILE)
    path_data = load_json(PATH_FILE)
    if app_name in path_data:
        if app_name not in runtime_data.lower():
            runtime_data[app_name] = 0  # Initialize with 0 runtime
            save_json(runtime_data, RUNTIME_FILE)
    else:
        messagebox.showwarning("Invalid Application", f"'{app_name}' is not a valid application.")

# Update the runtime for a specific application
def update_runtime(app_name, time_increment):
    """Update the runtime for the specified application in minutes."""
    runtime_data = load_json(RUNTIME_FILE)
    if app_name in runtime_data:
        runtime_data[app_name] += time_increment # Convert seconds to minutes
    else:
        runtime_data[app_name] = time_increment # Initialize if not already present
    save_json(runtime_data, RUNTIME_FILE)

# reset the runtime for a specific application
def reset_application_runtime(app_name, app_paths, listbox):
    """Reset the runtime for the specified application."""
    runtime_data = load_json(RUNTIME_FILE)
    if app_name in runtime_data:
        runtime_data[app_name] = 0.0  # Convert seconds to minutes
    else:
        messagebox.showwarning("Runtime Reset Not Running", "Specified application does not exists.")
    save_json(runtime_data, RUNTIME_FILE)
    refresh_listbox(listbox, app_paths)  # refresh the Listbox with current data

# Get runtime for a specific application
def get_runtime(app_name):
    """Get the runtime for a specific application in hours (rounded to nearest 0.5)."""
    runtime_data = load_json(RUNTIME_FILE)
    time = runtime_data.get(app_name)
    return convert_time(time)  # Convert minutes to hours

def convert_time(time):
    """Convert minutes to hours and round to the nearest 0.5 hours."""
    if time is None:
        return "0s"
        
    seconds = round(float(time), 1)
    seconds_str = str(seconds) + "s"
    minutes = round(float(time) / 60, 1)
    minutes_str = str(minutes) + "m"
    hours = minutes / 60
    rounded_hours = round(hours * 2) / 2
    hours_str = str(rounded_hours) + "h"
    
    if minutes >= 1:
        return minutes_str
    if hours >= 1:
        return hours_str
    return seconds_str

# def show_popup(app_name, runtime):
    """Display a pop-up when the application closes."""
    root = Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo(
        "Application Closed",
        f"'{app_name}' has been closed.\nSession runtime: {runtime:.2f} seconds."
    )
    root.destroy()

def validate_applications_paths(app_paths):
    """Validate application paths for correct format and existence."""
    invalid_apps = []
    for app_name, app_path in app_paths.items():
        exe_name = str(app_name) + ".exe" # Extract the executable name from the path
      # print(str(exe_name))
        if not (str(f"/{app_path}")+str(f"/{exe_name}")):
            invalid_apps.append(app_name)

    if invalid_apps:
        invalid_list = "\n".join(invalid_apps)
        messagebox.showwarning(
            "Validation Error",
            f"The following applications have invalid paths:\n{invalid_list}"
        )
    else:
        messagebox.showinfo("Validation Success", "All application paths are valid.")

def validate_running_applications(app_paths):
    """Check if any application in the provided paths is currently running."""
    running_apps = []
    for app_name, app_path in app_paths.items():
        exe_name = str(app_name) + ".exe" # Extract the executable name from the path
        if any(proc.name().lower() == exe_name.lower() for proc in psutil.process_iter(['name'])):
            running_apps.append(app_name)

    if running_apps:
        running_apps_str = "\n".join(running_apps)
        messagebox.showinfo("Validation Result", f"The following applications are running:\n\n{running_apps_str}")
    else:
        messagebox.showinfo("Validation Result", "No applications from the provided paths are currently running.")

def track_applications(app_names, exec_path):
    """Track the specified applications and record runtime."""
    def track():
        runtime_data = load_json(RUNTIME_FILE)
        start_time = None

        while tracking_flag["running"]:
            if not exec_path:
                continue

            app_name = app_names  # Get the single selected app
            proc_name = str(app_name) + ".exe"
            is_running = any(proc.name().lower() == proc_name.lower() for proc in psutil.process_iter(['name']))

            # print(f"{app_name} started.")
            if is_running:
                if start_time is None:
                    start_time = time.time()
                    # print("Started tracking time")
                    
                else:
                    current_elapsed = time.time() - start_time
                    update_runtime(app_name, 0.01)  # Update by 1 second
                    # print(f"Updated runtime: {round(float(current_elapsed),1)}s")
            elif start_time is not None:
                elapsed_time = time.time() - start_time
                update_runtime(app_name, elapsed_time)
                start_time = None

                # Show popup when an app closes
                messagebox.showinfo("Application Closed", f"{app_name} has been closed. Runtime updated.")
        time.sleep(1)  # Avoid excessive CPU usage

    # Run tracking in a separate thread
    # Start tracking in a separate thread to avoid blocking the GUI
    tracking_flag["running"] = True
    tracking_thread = threading.Thread(target=track, daemon=True)
    tracking_thread.start()

# def stop_tracking(listbox, app_paths):
#     """Stop tracking applications."""
#     if tracking_flag["running"]:
#         tracking_flag["running"] = False
#         # Ensure valid JSON data exists before refresh
#         try:
#             refresh_listbox(listbox, app_paths)
#         except json.JSONDecodeError:
#             # Initialize empty runtime data if file is corrupted
#             save_json({}, RUNTIME_FILE)
#             refresh_listbox(listbox, app_paths)
#         messagebox.showinfo("Tracking Stopped", "Application tracking has been stopped.")
#     else:
#         messagebox.showwarning("Tracking Not Running", "No application tracking is currently active.")

def stop_tracking(listbox, app_paths):
    """Stop tracking applications."""
    if tracking_flag["running"]:
        tracking_flag["running"] = False
        # Save current runtime data before refresh
        # save_json({}, RUNTIME_FILE)  # Reset to empty if corrupted
        refresh_listbox(listbox, app_paths)
        messagebox.showinfo("Tracking Stopped", "Application tracking has been stopped.")
    else:
        messagebox.showwarning("Tracking Not Running", "No application tracking is currently active.")

def add_application_gui(listbox, app_paths):
    """GUI for adding a new application to app_paths.json."""
    def save_new_application():
        app_name = app_name_entry.get().strip()
        app_path = app_path_entry.get().strip().replace("\\", "/")

        if not app_name or not app_path:
            messagebox.showwarning("Input Error", "Both fields must be filled out.")
            return

        if app_name in app_paths:
            messagebox.showwarning("Duplicate Error", f"'{app_name}' already exists.")
            return

        app_paths[app_name] = app_path
        save_json(app_paths, PATH_FILE)
        messagebox.showinfo("Success", f"'{app_name}' has been added successfully.")
        add_app_window.destroy()
        refresh_listbox(listbox, app_paths)  # refresh the Listbox with current data

    add_app_window = Toplevel()
    add_app_window.title("Add New Application")

    Label(add_app_window, text="Application Name:").pack(pady=5)
    app_name_entry = Entry(add_app_window, width=50)
    app_name_entry.pack(pady=5)

    Label(add_app_window, text="Application Path:").pack(pady=5)
    app_path_entry = Entry(add_app_window, width=50)
    app_path_entry.pack(pady=5)

    Button(add_app_window, text="Add Application", command=save_new_application).pack(pady=10)

def open_file(file_path):
    """Opens a file in the default system editor."""
    try:
        subprocess.Popen(["notepad", file_path] if os.name == "nt" else ["open", file_path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file: {e}")

def refresh_listbox(listbox, app_paths):
    """Refresh the Listbox with the application name and runtime."""
    listbox.delete(0, 'end')
    for app_name, app_path in app_paths.items():
        app_runtime = get_runtime(app_name)  # Get runtime in hours
        listbox.insert('end', f"{app_name} - {app_runtime}")

def edit_application_gui(main_listbox):
    """GUI for editing an existing application's name and path."""
    app_paths = load_json(PATH_FILE)
    if not app_paths:
        messagebox.showwarning("No Applications", "No applications found to edit.")
        return

    def update_application():
        selected_indices = listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Selection Error", "Please select an application to update.")
            return

        old_name = listbox.get(selected_indices[0])
        new_name = app_name_entry.get().strip()
        new_path = app_path_entry.get().strip().replace("\\", "/")

        if not new_name or not new_path:
            messagebox.showwarning("Input Error", "Both fields must be filled out.")
            return

        if new_name != old_name and new_name in app_paths:
            messagebox.showwarning("Duplicate Error", f"'{new_name}' already exists.")
            return

        del app_paths[old_name]
        app_paths[new_name] = new_path
        save_json(app_paths, PATH_FILE)
        messagebox.showinfo("Success", f"'{old_name}' has been updated to '{new_name}'.")
        refresh_listbox(listbox, app_paths)  # Refresh the Listbox in the Edit Application window
        refresh_listbox(main_listbox, app_paths)  # Refresh the Listbox in the main Application Tracker window
        edit_app_window.destroy()

    def populate_fields(event):
        """Populate fields with selected application's data."""
        listbox_name = listbox.get(listbox.curselection())
        selected_name = listbox_name.split()[0]
        app_name_entry.delete(0, "end")
        app_name_entry.insert(0, selected_name)
        app_path_entry.delete(0, "end")
        app_path_entry.insert(0, app_paths[selected_name])

    edit_app_window = Toplevel()
    edit_app_window.title("Edit Application")

    Label(edit_app_window, text="Select an application to edit:").pack(pady=5)
    listbox = Listbox(edit_app_window, selectmode="single", width=50, height=15)
    refresh_listbox(listbox, app_paths)  # Populate the Listbox with current data
    listbox.pack(pady=5)
    listbox.bind("<<ListboxSelect>>", populate_fields)

    Label(edit_app_window, text="New Application Name:").pack(pady=5)
    app_name_entry = Entry(edit_app_window, width=50)
    app_name_entry.pack(pady=5)

    Label(edit_app_window, text="New Application Path:").pack(pady=5)
    app_path_entry = Entry(edit_app_window, width=50)
    app_path_entry.pack(pady=5)

    Button(edit_app_window, text="Update Application", command=update_application).pack(pady=10)

def select_applications():
    """Display a GUI for selecting applications to track."""
    app_paths = load_json(PATH_FILE)
    if not app_paths:
        print(f"No applications found in '{PATH_FILE}'. Add paths to the file.")
        return

    def start_tracking():
        listbox_name = [listbox.get(i) for i in listbox.curselection()]
        selected_app = str(listbox_name).split()[0].strip("[ ] '")
        exec_path = app_paths.get(selected_app)
        if selected_app:
            track_applications(selected_app, exec_path)
        else:
            messagebox.showwarning("Selection Error", "Please select at least one application to track.")
    
    def reset_runtime():
        listbox_name = [listbox.get(i) for i in listbox.curselection()]
        selected_app = str(listbox_name).split()[0].strip("[ ] '")
        exec_path = app_paths.get(selected_app)
        exec2_path = os.path.basename(selected_app)
        if selected_app:
            reset_application_runtime(selected_app, app_paths, listbox)
        else:
            messagebox.showwarning("Selection Error", "Please select at least one application to track.")

    def add_application():
        add_application_gui(listbox, app_paths)

    root = Tk()
    root.title("Application Tracker")

    Label(root, text="Select applications to track:").pack(pady=10)

    listbox = Listbox(root, selectmode="single", width=50, height=15)
    # refresh_listbox()  # Populate the Listbox with current data and runtime
    refresh_listbox(listbox, app_paths)  # Populate the Listbox with current data
    listbox.pack(pady=10)

    Button(root, text="Start Tracking", command=start_tracking).pack(pady=5)
    Button(root, text="Stop Tracking", command=lambda:stop_tracking(listbox, app_paths)).pack(pady=5)
    Button(root, text="Add New Application", command=add_application).pack(pady=5)
    Button(root, text="Edit Application", command=lambda: edit_application_gui(listbox)).pack(pady=5)
    Button(root, text="Validate Running Applications", command=lambda: validate_running_applications(app_paths)).pack(pady=5)
    Button(root, text="Validate Applications Paths", command=lambda: validate_applications_paths(app_paths)).pack(pady=5)
    Button(root, text="Open Path File", command=lambda: open_file(PATH_FILE)).pack(pady=5)
    Button(root, text="Open Runtime File", command=lambda: open_file(RUNTIME_FILE)).pack(pady=5)
    Button(root, text="reset Application Runtime", command=reset_runtime).pack(pady=5)

    root.mainloop()


# if __name__ == "__main__":
    # if not os.path.exists(PATH_FILE):
    #     save_json({}, PATH_FILE)
select_applications()
