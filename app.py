from flask import Flask,render_template,request,flash,redirect,session
import mysql.connector
import os
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
app.secret_key=os.urandom(24)

conn =mysql.connector.connect(host="localhost",user="root",password="",database="commodity")
cursor = conn.cursor()

data = pd.read_csv("csvFiles/AgriCommodityData.csv")

with open("Agrimodel.pkl", "rb") as model_file:
    loaded_model, label_encoder_commodity, label_encoder_brand = pickle.load(model_file)

@app.route('/')
def LginPage():
    return render_template("login.html")

@app.route('/registratiion')
def RegistrationPage():
    return render_template("registratiion.html")

@app.route('/AgriCommodity')
def Home():
    if 'email' in session:
        return render_template("AgriCommodity.html")
    else:
        return redirect('/')


@app.route('/login_validation', methods=['POST'])
def LoginVald():
    email=request.form.get('email')
    password=request.form.get('password')
    cursor.execute("""SELECT * FROM `login_page_db` WHERE `email` LIKE '{}' AND `password` LIKE '{}'"""
                   .format(email,password))
    users=cursor.fetchall()
    if len(users)>0:
        session['email']=users[0][0]
        return render_template('AgriCommodity.html')
    else:
        flash('Invalid email or password. Please try again.', 'error')
        return redirect('/')


@app.route('/add_user',methods=["POST"])
def add_user():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    cursor.execute("""INSERT INTO `login_page_db`(`id`, `name`, `email`, `password`) VALUES (NULL,'{}','{}','{}')""".format(name,email,password))
    conn.commit()
    flash('Registered successfully!', 'success')
    return redirect('/AgriCommodity')

@app.route('/logout')
def logout():
    session.pop('email')
    flash('Logout successful!', 'success')
    return redirect('/')

unique_brand_to_image_url = data.drop_duplicates(subset='Brand Name').set_index('Brand Name')['Image_url'].to_dict()
@app.route('/Agripredict', methods=['POST'])
def predict():
    try:
        commodity = request.form['commodity']
        brand_name = request.form['brand_name']
        quantity = float(request.form['quantity'])

        input_commodity_encoded = label_encoder_commodity.transform([commodity])[0]
        input_brand_encoded = label_encoder_brand.transform([brand_name])[0]

        input_feature = np.array([[input_commodity_encoded, input_brand_encoded, quantity]])

        image_url_img = unique_brand_to_image_url.get(brand_name,'Image_url')

        predicted_price = loaded_model.predict(input_feature)[0]

        formatted_predicted_price = "{:.2f}".format(predicted_price)


        unique_brand_names = data[data['Commodity'] == commodity]['Brand Name'].unique()
        lower_price_brands = []
        higher_price_brands = []

        for brand in unique_brand_names:
            input_brand_encoded = label_encoder_brand.transform([brand])[0]
            input_commodity_encoded = label_encoder_commodity.transform([commodity])[0]

            input_feature = np.array([[input_commodity_encoded, input_brand_encoded, quantity]])
            predicted_priced = loaded_model.predict(input_feature)[0]
            predicted_priced_formatted = "{:.2f}".format(predicted_priced)
            image_url = unique_brand_to_image_url.get(brand, 'Image_url')


            if predicted_priced < predicted_price:
                Price_Low = predicted_priced - predicted_price
                price_low = "{:.2f}".format(Price_Low)
                lower_price_brands.append([brand, quantity, predicted_priced_formatted, image_url,price_low])

            elif predicted_priced == predicted_price:
                continue
            else:
                Price_High = - predicted_price + predicted_priced
                price_high = "{:.2f}".format(Price_High)
                higher_price_brands.append([brand, quantity, predicted_priced_formatted, image_url,price_high])

        return render_template(
            "AgriCommodity.html",
            commodity=commodity,
            brand_name=brand_name,
            quantity=quantity,
            image_url_img =image_url_img,
            prediction=formatted_predicted_price,
            lower_price_brands=lower_price_brands,
            higher_price_brands=higher_price_brands
        )

    except Exception as e:
        return render_template("AgriCommodity.html", error=str(e))

@app.route('/GenerateReport', methods=['POST'])
def generate_report():
    try:
        commodity = request.form['commodity']
        if isinstance(commodity, str):
            brand_names = data[data['Commodity'] == commodity]['Brand Name'].unique()
            brand_quantities = {}

            for brand in brand_names:
                brand_data = data[(data['Commodity'] == commodity) & (data['Brand Name'] == brand)]
                unique_quantities = brand_data['Quantity'].unique()
                total_count = brand_data['Total_Count'].sum()
                quantity_sold_high = brand_data['Total_Count'].max()
                quantity_max_count = brand_data[brand_data['Total_Count'] == quantity_sold_high]['Quantity'].iloc[0]
                brand_quantities[brand] = {
                    'Unique_Quantities': unique_quantities,
                    'Total_Count': total_count,
                    'quantity_sold_high':quantity_sold_high,
                    'quantity_max_count':quantity_max_count}

                brand_names = list(brand_quantities.keys())
                highest_total_counts = [brand_quantities[brand]['Total_Count'] for brand in brand_names]

                plt.figure(figsize=(16, 9))
                custom_colors = ['red', 'green', 'blue', 'orange', 'purple']
                plt.bar(brand_names, highest_total_counts, color=custom_colors)
                plt.title("Total Count for Top Brands")
                plt.xlabel("Brand Name")
                plt.ylabel("Highest Brand Count")
                plt.savefig('static/total_count_chart.png')

            return render_template('AgriCommodity.html',
                                   commodity=commodity,
                                   brand_quantities=brand_quantities)
        else:
            return "Invalid commodity value."
    except Exception as e:
        return render_template("AgriCommodity.html", error=str(e))

if __name__ == '__main__':
    app.run(debug=True)


