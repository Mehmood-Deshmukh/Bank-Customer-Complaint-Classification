import streamlit as st
import pickle
import sqlite3
from datetime import datetime

# Load the model and vectorizer
with open('./Pickle Files/model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)
with open('./Pickle Files/vectorizer.pkl', 'rb') as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)

# Create a connection to the SQLite database
conn = sqlite3.connect('complaints.db')
c = conn.cursor()

# Create the tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS complaints
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id TEXT,
              complaint TEXT,
              department TEXT,
              timestamp DATETIME)''')

c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT)''')
conn.commit()

# List of departments
departments = ['credit_card', 'credit_reporting', 'debt_collection', 'mortgages_and_loans', 'retail_banking']

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

def verify_login(username, password):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, True
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    if result:
        return result[0], False
    return None, False

def register_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def save_complaint(user_id, complaint, department):
    timestamp = datetime.now().isoformat()  
    c.execute("INSERT INTO complaints (user_id, complaint, department, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, complaint, department, timestamp))
    conn.commit()

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            user_id, is_admin = verify_login(username, password)
            if user_id is not None:
                st.session_state.user_id = user_id
                st.session_state.is_admin = is_admin
                st.session_state.page = 'admin' if is_admin else 'customer'
                st.rerun()
            else:
                st.error("Invalid credentials")
    with col2:
        if st.button("Register"):
            st.session_state.page = 'register'
            st.rerun()

def register_page():
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Register"):
        if register_user(username, password):
            st.success("Registration successful! Please login.")
            st.session_state.page = 'login'
            st.rerun()
        else:
            st.error("Username already exists")
    if st.button("Back to Login"):
        st.session_state.page = 'login'
        st.rerun()

def customer_page():
    if not st.session_state.user_id or st.session_state.is_admin:
        st.error("Unauthorized access. Please login as a customer.")
        st.session_state.page = 'login'
        st.rerun()

    st.title("Customer Complaint Classification")
    st.header("Submit a Complaint")
    complaint = st.text_area("Enter your complaint here:")
    if st.button("Submit Complaint"):
        if complaint:
            inputs = vectorizer.transform([complaint])
            prediction = model.predict(inputs)[0]
            department = prediction if isinstance(prediction, str) else departments[prediction]
            save_complaint(st.session_state.user_id, complaint, department)
            st.success(f"Your complaint has been classified under: **{department.replace('_', ' ').title()}**")
        else:
            st.error("Please enter a complaint.")
    if st.button("Logout"):
        st.session_state.page = 'login'
        st.session_state.user_id = None
        st.session_state.is_admin = False
        st.rerun()
    
    st.header("Your Past Complaints")
    past_complaints = c.execute("SELECT * FROM complaints WHERE user_id=? ORDER BY timestamp DESC", (st.session_state.user_id,)).fetchall()
    if past_complaints:
        for complaint in past_complaints:
            formatted_date = datetime.fromisoformat(complaint[4]).strftime("%Y-%m-%d %H:%M:%S")
            with st.expander(f"Complaint on {formatted_date}"):
                st.write(f"**Department:** {complaint[3].replace('_', ' ').title()}")
                st.write(f"**Complaint:** {complaint[2]}")
    else:
        st.info("You haven't submitted any complaints yet.")

def admin_page():
    if not st.session_state.is_admin:
        st.error("Unauthorized access. Please login as an admin.")
        st.session_state.page = 'login'
        st.rerun()

    st.title("Admin Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_complaints = c.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        st.metric("Total Complaints", total_complaints)
    with col2:
        total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        st.metric("Total Users", total_users)
    with col3:
        departments_count = c.execute("SELECT COUNT(DISTINCT department) FROM complaints").fetchone()[0]
        st.metric("Active Departments", departments_count)

    st.header("Complaint Overview")
    dept_counts = c.execute("SELECT department, COUNT(*) FROM complaints GROUP BY department").fetchall()
    dept_data = {dept: count for dept, count in dept_counts}
    
    dept_data = {dept.replace('_', ' ').title(): count for dept, count in dept_data.items()}
    st.bar_chart(dept_data)
    

    st.header("Recent Complaints")
    complaints = c.execute("SELECT * FROM complaints ORDER BY timestamp DESC LIMIT 3").fetchall()
    if complaints:
        for complaint in complaints:
            formatted_date = datetime.fromisoformat(complaint[4]).strftime("%Y-%m-%d %H:%M:%S")
            with st.expander(f"Complaint ID: {complaint[0]} - {complaint[3].replace('_', ' ').title()}"):
                st.write(f"**User ID:** {complaint[1]}")
                st.write(f"**Complaint:** {complaint[2]}")
                st.write(f"**Department:** {complaint[3].replace('_', ' ').title()}")
                st.write(f"**Timestamp:** {formatted_date}")
    else:
        st.info("No complaints submitted yet.")

    st.header("Department-wise Complaints Queue")
    for dept in departments:
        with st.expander(f"{dept.replace('_', ' ').title()} Queue"):
            dept_complaints = c.execute("SELECT * FROM complaints WHERE department=? ORDER BY timestamp DESC LIMIT 5", (dept,)).fetchall()
            if dept_complaints:
                for complaint in dept_complaints:
                    formatted_date = datetime.fromisoformat(complaint[4]).strftime("%Y-%m-%d %H:%M:%S")
                    st.write(f"**Complaint ID:** {complaint[0]}")
                    st.write(f"**User ID:** {complaint[1]}")
                    st.write(f"**Complaint:** {complaint[2]}")
                    st.write(f"**Timestamp:** {formatted_date}")
                    st.write('---')
            else:
                st.info(f"No complaints in the {dept.replace('_', ' ').title()} queue.")

    if st.button("Logout"):
        st.session_state.page = 'login'
        st.session_state.user_id = None
        st.session_state.is_admin = False
        st.rerun()

def main():
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'register':
        register_page()
    elif st.session_state.page == 'customer':
        customer_page()
    elif st.session_state.page == 'admin':
        admin_page()

if __name__ == "__main__":
    main()
