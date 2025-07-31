import streamlit as st
import pandas as pd 
import openai
import datetime
from dotenv import load_dotenv
import os
from io import BytesIO
import requests
from api_urls import ENDPOINTS

load_dotenv()
api_key=os.getenv("OPENAI_API_KEY")



# ------------------ LOGIN HANDLER ------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "data" not in st.session_state:  # to store API response data
    st.session_state.data = None
if st.session_state.logged_in:
    user_id = st.session_state.data["user"]["id"]  # ✅ Access ID
    st.write("User ID:", user_id)

def login():
    st.title("🔐 Login to Access Expense Tracker (AYS)")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            LOGIN_URL = ENDPOINTS["login"]
            headers = {
                "Content-Type": "application/json",
            }
            response = requests.post(LOGIN_URL, json={"username": username, "password": password}, headers=headers)
            data = response.json()
            print(data)
            if data.get("flag") == True:
                st.success("✅ Login successful!")
                st.session_state.logged_in = True
                st.session_state.user = data.get("user")
                st.session_state.data = data 
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        except Exception as e:
            st.error(f"Error connecting to API: {e}")


# ------------------ MAIN EXPENSE TRACKER ------------------

def show_expense_tracker():
    st.title("💸 AI-Powered Expense Tracker")

    if "expenses" not in st.session_state:
        st.session_state.expenses = []

    def categorize_item(item_name):
        prompt = f"What category does the following fall into: '{item_name}'? Use short category names like Food, Rent, Travel, Entertainment, Utilities, etc."
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            return "Unknown"

    with st.form("expense_form", clear_on_submit=True):
        item = st.text_input("Enter item name")
        price = st.number_input("Enter item price", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Expense")

        if submitted and item:
            category = categorize_item(item)
            headers = {
                "Content-Type": "application/json",
            }
        
            response = requests.post(ENDPOINTS["addExpense"],json={"item":item, "price":price, "category":category, "userId":user_id} ,headers=headers)
            if response.status_code == 200:
                
                st.session_state.expenses.append({
                    "Item": item,
                    "Price": price,
                    "Category": category,
                    "Date": datetime.date.today().strftime('%Y-%m-%d')
                })
                st.success(f"Added: {item} - ₹{price:.2f} - Category: {category}")
            else:
                st.error("Error adding expense to the backend")
                return

    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        st.subheader("🧾 Your Expenses")
        st.dataframe(df, use_container_width=True)

        total = df["Price"].sum()
        st.markdown(f"### 🧮 Total: ₹{total:.2f}")

        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Expenses')
            worksheet = writer.sheets['Expenses']
            worksheet.write(len(df) + 1, 0, 'Total')
            worksheet.write(len(df) + 1, 1, total)
            writer.close()
            return output.getvalue()

        excel_data = to_excel(df)

        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name="expense_tracker.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

# ------------------ ROUTER ------------------

if not st.session_state.logged_in:
    login()
else:
    show_expense_tracker()