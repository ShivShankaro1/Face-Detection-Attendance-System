import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import pyodbc
from datetime import datetime

# Database connection config


DB_CONNECTION_STRING = (
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=localhost\\SQLEXPRESS02;'
    'Database=master;'
    'Trusted_Connection=yes;'
)

def run_entry():
    subprocess.Popen(["python", "entry.py"])  # Adjust if filename is different

def run_exit():
    subprocess.Popen(["python", "exit.py"])  # Adjust if filename is different

def view_attendance():
    # Create new window
    view_window = tk.Toplevel(root)
    view_window.title("Attendance Records")
    view_window.geometry("800x400")

    tree = ttk.Treeview(view_window)
    tree['columns'] = ("LogID", "RollNo", "EntryTime", "ExitTime")

    tree.column("#0", width=0, stretch=tk.NO)
    tree.column("LogID", anchor=tk.CENTER, width=80)
    tree.column("RollNo", anchor=tk.CENTER, width=180)
    tree.column("EntryTime", anchor=tk.CENTER, width=250)
    tree.column("ExitTime", anchor=tk.CENTER, width=250)

    tree.heading("LogID", text="Log ID", anchor=tk.CENTER)
    tree.heading("RollNo", text="Roll No", anchor=tk.CENTER)
    tree.heading("EntryTime", text="Entry Time", anchor=tk.CENTER)
    tree.heading("ExitTime", text="Exit Time", anchor=tk.CENTER)

    tree.pack(pady=20, fill=tk.BOTH, expand=True)

    try:
        connection = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = connection.cursor()
        cursor.execute("SELECT LogID, RollNo, EntryDetectionTime, ExitDetectionTime FROM AttendanceTable ORDER BY LogID DESC")
        records = cursor.fetchall()

        for row in records:
            log_id = row[0]
            roll_no = row[1]
            entry_time = row[2].strftime("%Y-%m-%d %H:%M:%S") if row[2] else ""
            exit_time = row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else ""
            tree.insert("", "end", values=(log_id, roll_no, entry_time, exit_time))

        connection.close()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))


# MAIN UI
root = tk.Tk()
root.title("Attendance System")
root.geometry("400x250")

label = tk.Label(root, text="Mark Your Presence", font=("Arial", 16))
label.pack(pady=10)

btn_entry = tk.Button(root, text="Punch In", width=25, height=2, command=run_entry, bg="#4CAF50", fg="white")
btn_entry.pack(pady=10)
btn_exit = tk.Button(root, text="Punch Out", width=25, height=2, command=run_exit, bg="#F44336", fg="white")
btn_exit.pack(pady=10)

btn_view = tk.Button(root, text="View Attendance", width=25, height=2, command=view_attendance, bg="#2196F3", fg="white")
btn_view.pack(pady=10)

root.mainloop()
