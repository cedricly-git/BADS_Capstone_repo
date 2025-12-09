# BADS Capstone: Delivery Demand Predictor

### Optimizing Food Delivery Operations using Google Search Trends

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B)
![Status](https://img.shields.io/badge/Status-Completed-success)

## 📌 Executive Summary
This project aims to help restaurants and food delivery platforms (like UberEats) optimize their operations by predicting daily demand. 

In the absence of proprietary order data, we engineered a novel approach using **Google Search Volume** as a proxy for consumer demand. By analyzing search trends alongside external factors like weather and holidays, our Streamlit application provides actionable insights for staffing, inventory management, and order preparation.

<img width="1493" height="834" alt="app_main_screen" src="https://github.com/user-attachments/assets/93b3c169-050b-4db8-8e95-69a18edd30fc" />
<img width="1495" height="879" alt="app_option_screen" src="https://github.com/user-attachments/assets/b5103ffa-17eb-42d6-ae8c-d94a5ed26582" />


## 🎯 Business Goal
The primary objective is to smooth the volatility of food delivery logistics. By predicting demand spikes, our tool helps stakeholders:
* **Optimize Staffing:** Schedule couriers and kitchen staff efficiently during predicted peaks.
* **Manage Stock:** Reduce food waste by anticipating lower-demand days.
* **Improve Service:** Decrease wait times during high-volume periods.

## 📊 Data Engineering & Sources
One of the core challenges, and major learning outcomes of this project was the construction of a custom dataset from scratch. Instead of using a pre-made Kaggle dataset, we performed extensive **Data Engineering**:

1.  **Demand Proxy (Target Variable):** We scraped daily search data for 'UberEats' and related delivery keywords over the past 2 years, specifically gathering the relative search volume from Google Trends and the absolute search volume (which is granularized and thus not representative of daily variations) from Semrush.
2.  **External Features:**
    * **Weather API:** Integrated precipitation and temperature data to analyze the "rainy day delivery" hypothesis.
    * **Temporal Features:** Engineered features for day-of-the-week, seasonality, and public holidays.

*Note: Building this pipeline was complex. Aligning disparate time-series data (weather vs. search trends) required significant cleaning and synchronization.*

## ⚙️ Methodology & Tech Stack
We approached this as a regression problem, aiming to predict the volume of search traffic.

### Tech Stack
* **Language:** Python
* **Data Manipulation:** Pandas, NumPy
* **Scraping/APIs:** Requests, PyTrends (or specific scraping library used)
* **Modeling:** Scikit-Learn, LinearRegression, CatBoost
* **Visualization:** Plotly
* **App Framework:** Streamlit

### Model Selection
We experimented with multiple algorithms, narrowing our focus to:
* **Linear Regression:** For baseline performance and interpretability.
* **CatBoost Regressor:** To capture non-linear relationships and handle categorical features effectively.

Both models yielded comparable results, and the final application allows users to interact with the predictions derived from these experiments.
<img width="1489" height="989" alt="image" src="https://github.com/user-attachments/assets/2b4cf895-c123-4a22-b2c1-795a9a77bce2" />
<img width="1490" height="590" alt="image" src="https://github.com/user-attachments/assets/a9bda3c3-c546-4b3a-b2c9-1a570cdebed7" />

## 📉 Results & Limitations
Our final model achieved an $R^2$ of **0.365**.

While this metric indicates that our model explains approximately 36.5% of the variance in search volume, it provides critical learning points regarding the use of proxy data in business analytics:

* **The "Proxy Gap":** The moderate score highlights the distinction between *intent* (Google Search) and *action* (placing an order). Many users open the UberEats app directly without searching on Google, which is data we cannot access publicly.
* **Key Drivers Identified:** Despite the predictive limitations, the model successfully isolated statistically significant drivers. We confirmed that **precipitation**, **low temperatures**, and **holidays** have a measurable positive impact on interest.
* **Business Value:** Even with an $R^2$ of 0.365, the directional insights allow us to provide solid, logic-based recommendations for staffing up during specific weather events and calendar days.
<img width="1590" height="590" alt="image" src="https://github.com/user-attachments/assets/c47a6220-1999-40a8-8a57-be868314bf69" />



**Future Improvements:**
To bridge the gap in unexplained variance, future iterations would benefit from:
1.  **Internal App Data:** Access to actual order logs rather than search trends.
2.  **Marketing Data:** Incorporating ad spend and push notification schedules, which likely drive the remaining "unexplained" spikes in demand.

## 🚀 How to Run the App
The application is built with Streamlit and requires a local Python environment.

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/BADS_Capstone_repo.git](https://github.com/yourusername/BADS_Capstone_repo.git)
    cd BADS_Capstone_repo
    ```

2.  **Install requirements**
    Make sure you have Python installed. Then run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**
    ```bash
    streamlit run app.py
    ```
    The app should open automatically in your default browser at `http://localhost:8501`.

## 👥 Contributors
* Leonardo Gonnelli
* Gaspard Simonetta
* Barnabé Cusnir
* Cédric Ly

---
*Created for the Business Analytics and Data Science Capstone Class.*
