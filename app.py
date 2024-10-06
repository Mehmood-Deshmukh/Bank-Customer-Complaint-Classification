import streamlit as st
import pandas as pd
import pickle

# Load pre-trained Logistic Regression model
with open('logistic_regression_model.pkl', 'rb') as model_file:
    lr_model = pickle.load(model_file)

# Load the vectorizer used during training
with open('vectorizer.pkl', 'rb') as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)

# Initialize session state for complaints
if 'complaints' not in st.session_state:
    st.session_state.complaints = []

# Define departments (queues)
departments = ['credit_card', 'credit_reporting', 'debt_collection', 'mortgages_and_loans', 'retail_banking']

# Title of the application
st.title("Customer Complaint Classification")

# Customer input section
st.header("Submit a Complaint")
complaint = st.text_area("Enter your complaint here:")

if st.button("Submit"):
    if complaint:
        # Vectorize the complaint for prediction
        inputs = vectorizer.transform([complaint]) 

        # Classify the complaint
        prediction = lr_model.predict(inputs)[0]
        
        if isinstance(prediction, str):
            try:
                prediction = departments.index(prediction) 
            except ValueError:
                st.error("Prediction string not found in departments.")
        
        department = departments[prediction] 

        # Save the complaint with the classified department in session state
        st.session_state.complaints.append({'complaint': complaint, 'department': department})
        
        st.success(f"Your complaint has been submitted and classified under: **{department.replace('_', ' ').title()}**")

    else:
        st.error("Please enter a complaint before submitting.")

# Admin section to view complaints
st.header("Admin View")
if st.button("Show Complaints"):
    if st.session_state.complaints:
        # Organize complaints by department
        dept_complaints = {dept: [] for dept in departments}
        for complaint in st.session_state.complaints:
            dept_complaints[complaint['department']].append(complaint['complaint'])
        
        for dept, comps in dept_complaints.items():
            # Add some styling for the department title
            st.markdown(f"<h5 style='color: #4CAF50;'>{dept.replace('_', ' ').title()}</h5>", unsafe_allow_html=True)
            # Display each complaint in a styled box
            for comp in comps:
                st.markdown(f"<div style='background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px 0;'>{comp}</div>", unsafe_allow_html=True)
    else:
        st.write("No complaints submitted yet.")
