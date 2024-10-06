from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer  # or TfidfVectorizer
import pickle

app = Flask(__name__)

with open('logistic_regression_model.pkl', 'rb') as model_file:
    lr_model = pickle.load(model_file)


with open('vectorizer.pkl', 'rb') as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)


complaints = []

departments = ['credit_card', 'credit_reporting', 'debt_collection', 'mortgages_and_loans', 'retail_banking']


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/customer', methods=['GET', 'POST'])
def customer():
    if request.method == 'POST':
        complaint = request.form['complaint']
        inputs = vectorizer.transform([complaint]) 

        prediction = lr_model.predict(inputs)[0]
        
        print(f"Prediction: {prediction}") 

        if isinstance(prediction, str):

            try:
                prediction = departments.index(prediction) 
            except ValueError:
                return "Prediction string not found in departments."


        department = departments[prediction] 

        complaints.append({'complaint': complaint, 'department': department})

        return redirect(url_for('thank_you'))
    return render_template('customer.html')


@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/admin')
def admin():

    dept_complaints = {dept: [] for dept in departments}
    for complaint in complaints:
        dept_complaints[complaint['department']].append(complaint['complaint'])

    return render_template('admin.html', complaints=dept_complaints)

if __name__ == '__main__':
    app.run(debug=True)
