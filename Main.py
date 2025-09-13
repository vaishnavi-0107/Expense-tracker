import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
import speech_recognition as sr
import cv2
import pytesseract
import sqlite3
import re
from datetime import datetime
from tkcalendar import DateEntry
from sklearn.linear_model import LinearRegression
import numpy as np

🔹 Set the path to Tesseract (Update this path if needed)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

🔹 Set up SQLite database

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
category TEXT,
subcategory TEXT,
amount REAL,
payment_method TEXT)''')
conn.commit()

🔹 Expanded Expense Categories and Subcategories

categories = {
"Food": ["Groceries", "Dining Out", "Snacks", "Coffee", "Takeout"],
"Housing": ["Rent", "Utilities", "Maintenance", "Mortgage", "Property Tax"],
"Transport": ["Fuel", "Public Transport", "Taxi", "Car Loan", "Parking Fees"],
"Entertainment": ["Movies", "Games", "Concerts", "Streaming Services", "Books"],
"Health": ["Doctor", "Medicine", "Gym", "Insurance", "Therapy"],
"Shopping": ["Clothing", "Electronics", "Accessories", "Home Decor", "Gifts"],
"Education": ["Tuition", "Books", "Online Courses", "School Fees", "Stationery"],
"Bills": ["Electricity", "Water", "Internet", "Phone Bill", "Cable TV"],
"Travel": ["Flights", "Hotels", "Food", "Tours", "Transport"],
"Investments": ["Stocks", "Mutual Funds", "Cryptocurrency", "Real Estate", "Bonds"],
"Insurance": ["Health", "Car", "Home", "Life", "Travel"],
"Miscellaneous": ["Charity", "Donations", "Personal Care", "Pet Supplies", "Others"]
}

def update_subcategories(event):
selected_category = category_var.get()
subcategory_dropdown['values'] = categories.get(selected_category, [])
subcategory_var.set('')

def add_expense():
date = date_entry.get_date().strftime("%Y-%m-%d")
category = category_var.get()
subcategory = subcategory_var.get()
amount = amount_entry.get()
payment_method = payment_method_entry.get()

if not category or not subcategory or not amount or not payment_method:  
    messagebox.showerror("Error", "Please fill all fields!")  
    return  

try:  
    amount = float(amount)  
    cursor.execute("INSERT INTO expenses (date, category, subcategory, amount, payment_method) VALUES (?, ?, ?, ?, ?)",  
                   (date, category, subcategory, amount, payment_method))  
    conn.commit()  
    messagebox.showinfo("Success", "Expense added successfully!")  
except ValueError:  
    messagebox.showerror("Error", "Amount must be a number!")

def add_expense_voice():
recognizer = sr.Recognizer()
with sr.Microphone() as source:
messagebox.showinfo("Voice Input", "Speak your expense in the format: Category, Subcategory, Amount, Payment Method")
try:
audio = recognizer.listen(source)
text = recognizer.recognize_google(audio)
parts = text.split()
if len(parts) >= 4:
category_var.set(parts[0])
subcategory_var.set(parts[1])
amount_entry.delete(0, tk.END)
amount_entry.insert(0, parts[2])
payment_method_entry.delete(0, tk.END)
payment_method_entry.insert(0, " ".join(parts[3:]))
add_expense()
else:
messagebox.showerror("Error", "Invalid format. Try again.")
except sr.UnknownValueError:
messagebox.showerror("Error", "Could not understand your speech. Try again.")

def scan_receipt():
file_path = filedialog.askopenfilename(filetypes=[("Image Files", ".png;.jpg;*.jpeg")])
if not file_path:
return

try:  
    # 🔹 Load image and convert to grayscale  
    image = cv2.imread(file_path)  
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]  

    # 🔹 Perform OCR  
    text = pytesseract.image_to_string(gray)  

    # 🔹 Extract amount using regex  
    amounts = re.findall(r'\d+\.\d+', text)  
    amounts = [float(a) for a in amounts]  

    if amounts:  
        detected_amount = max(amounts)  
        amount_entry.delete(0, tk.END)  
        amount_entry.insert(0, str(detected_amount))  
        messagebox.showinfo("Success", f"Receipt scanned successfully! Amount detected: {detected_amount}")  
    else:  
        messagebox.showerror("Error", "Could not detect amount from the receipt.")  

except Exception as e:  
    messagebox.showerror("Error", f"Receipt scanning failed: {e}")

def show_expenses():
top = tk.Toplevel()
top.title("View Expenses")
cursor.execute("SELECT * FROM expenses")
records = cursor.fetchall()
text = tk.Text(top, wrap=tk.WORD)
for record in records:
text.insert(tk.END, str(record) + "\n")
text.pack()

def show_charts():
df = pd.read_sql("SELECT * FROM expenses", conn)
if df.empty:
messagebox.showinfo("Info", "No data available for charts.")
return

category_totals = df.groupby("category")["amount"].sum()  
plt.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%', startangle=140)  
plt.title("Category-wise Expense Distribution")  
plt.show()

def predict_future_expenses():
df = pd.read_sql("SELECT date, amount FROM expenses", conn)
if df.empty:
messagebox.showinfo("Info", "No data available for prediction.")
return

try:  
    df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')  
    df.dropna(subset=['date'], inplace=True)  # Remove invalid dates  

    df['days_since_start'] = (df['date'] - df['date'].min()).dt.days  
    X = df[['days_since_start']]  
    y = df['amount']  

    model = LinearRegression()  
    model.fit(X, y)  

    future_days = [[X.max().values[0] + 30]]  # Predict 30 days ahead  
    future_amount = model.predict(future_days)  

    messagebox.showinfo("Prediction", f"Estimated expenses for next month: ${future_amount[0]:.2f}")  

except Exception as e:  
    messagebox.showerror("Error", f"Prediction failed: {e}")

🔹 Create main Tkinter window

root = tk.Tk()
root.title("AI-Based Expense Tracker")
root.geometry("500x650")

tk.Label(root, text="Date:").pack()
date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
date_entry.pack()

tk.Label(root, text="Category:").pack()
category_var = tk.StringVar()
category_dropdown = ttk.Combobox(root, textvariable=category_var, values=list(categories.keys()))
category_dropdown.pack()
category_dropdown.bind("<<ComboboxSelected>>", update_subcategories)

tk.Label(root, text="Subcategory:").pack()
subcategory_var = tk.StringVar()
subcategory_dropdown = ttk.Combobox(root, textvariable=subcategory_var)
subcategory_dropdown.pack()

tk.Label(root, text="Amount:").pack()
amount_entry = tk.Entry(root)
amount_entry.pack()

tk.Label(root, text="Payment Method:").pack()
payment_method_entry = tk.Entry(root)
payment_method_entry.pack()

tk.Button(root, text="Add Expense", command=add_expense).pack(pady=5)
tk.Button(root, text="Add via Voice", command=add_expense_voice).pack(pady=5)
tk.Button(root, text="Scan Receipt", command=scan_receipt).pack(pady=5)
tk.Button(root, text="View Expenses", command=show_expenses).pack(pady=5)
tk.Button(root, text="Show Charts", command=show_charts).pack(pady=5)
tk.Button(root, text="Predict Future Expenses", command=predict_future_expenses).pack(pady=5)

root.mainloop()
conn.close() give this coding as zip file
