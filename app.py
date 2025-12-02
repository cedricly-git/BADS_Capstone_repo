import streamlit as st
import pandas as pd
import numpy as np
import pickle
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

MODEL_NAME = "CatBoost Regression"
MODEL_R2 = 0.3652
MODEL_RMSE = 684.56

# Page configuration
st.set_page_config(
    page_title="Uber Eats Demand Forecast",
    page_icon="🍔",
    layout="wide"
)

# Title and description
st.title("🍔 Uber Eats Search Forecast Dashboard")
st.markdown("""
This dashboard provides **7-day forecasts** of estimated daily searches for Uber Eats based on weather forecasts.
Since searches are highly correlated with actual orders, these forecasts help predict expected Uber Eats demand.
""")

# Sidebar for information
with st.sidebar:
    st.header("📊 About")
    st.markdown(
        f"""**Model**: {MODEL_NAME}  
**Performance**: R² = {MODEL_R2:.4f}, RMSE = {MODEL_RMSE:.2f}  
**Features**: Weather, temporal patterns, and historical trends

**Data Source**:  
- Weather: Open-Meteo API (Switzerland, population-weighted)  
- Historical: Uber Eats search data
"""
    )
    
    st.header("🔍 Key Insights")
    st.markdown("""
    - **Weather Impact**: Temperature and precipitation significantly affect demand
    - **Weekly Patterns**: Weekends show different demand patterns
    - **Seasonal Trends**: Monthly variations captured through cyclical encoding
    - **Historical Context**: Previous day and week patterns are strong predictors
    """)

@st.cache_data
def load_historical_data():
    """Load historical search data and calculate statistics"""
    try:
        url = "https://raw.githubusercontent.com/cedricly-git/BADS_Capstone_repo/main/Data/ubereats+time_related_vars.csv"
        df = pd.read_csv(url, engine='python')
        df['Day'] = pd.to_datetime(df['Day'])
        df = df.sort_values('Day').reset_index(drop=True)
        
        searches = df['estimated_daily_searches'].values
        
        # Calculate statistics
        stats = {
            'mean': float(np.mean(searches)),
            'median': float(np.median(searches)),
            'std': float(np.std(searches)),
            'p25': float(np.percentile(searches, 25)),
            'p50': float(np.percentile(searches, 50)),
            'p75': float(np.percentile(searches, 75)),
            'p90': float(np.percentile(searches, 90)),
            'p95': float(np.percentile(searches, 95)),
            'min': float(np.min(searches)),
            'max': float(np.max(searches)),
            'data': df  # Keep full dataframe for comparisons
        }
        
        return stats
    except Exception as e:
        st.warning(f"Could not load historical data: {e}. Using defaults.")
        return {
            'mean': 2000.0,
            'median': 2000.0,
            'std': 500.0,
            'p25': 1500.0,
            'p50': 2000.0,
            'p75': 2500.0,
            'p90': 3000.0,
            'p95': 3500.0,
            'min': 1000.0,
            'max': 4000.0,
            'data': None
        }

@st.cache_data
def get_last_known_search_value():
    """Get the last known search value from CSV for initial lag features"""
    try:
        # Use URL with engine='python' to avoid pandas/numpy compatibility issues
        url = "https://raw.githubusercontent.com/cedricly-git/BADS_Capstone_repo/main/Data/ubereats+time_related_vars.csv"
        df = pd.read_csv(url, engine='python')
        df['Day'] = pd.to_datetime(df['Day'])
        df = df.sort_values('Day').reset_index(drop=True)
        # Return the last known search value and date
        last_row = df.iloc[-1]
        return {
            'last_date': last_row['Day'],
            'last_search_value': float(last_row['estimated_daily_searches']),
            'last_7days_ago_value': float(df.iloc[-7]['estimated_daily_searches']) if len(df) >= 7 else float(last_row['estimated_daily_searches'])
        }
    except Exception as e:
        st.warning(f"Could not load last known search value: {e}. Using default.")
        return {
            'last_date': None,
            'last_search_value': 2000.0,  # Default fallback
            'last_7days_ago_value': 2000.0
        }

@st.cache_data
def fetch_historical_weather(days=14):
    """Fetch historical weather for the last N days"""
    cities = {
        "Zurich": {"lat": 47.3769, "lon": 8.5417, "pop": 436551},
        "Geneva": {"lat": 46.2044, "lon": 6.1432, "pop": 209061},
        "Basel": {"lat": 47.5596, "lon": 7.5886, "pop": 177571},
        "Lausanne": {"lat": 46.5197, "lon": 6.6323, "pop": 144873},
        "Bern": {"lat": 46.9481, "lon": 7.4474, "pop": 137995},
        "Winterthur": {"lat": 47.5056, "lon": 8.7247, "pop": 120376},
        "Lucerne": {"lat": 47.0502, "lon": 8.3064, "pop": 86234},
        "St. Gallen": {"lat": 47.4245, "lon": 9.3767, "pop": 78863},
        "Lugano": {"lat": 46.0101, "lon": 8.9600, "pop": 63629},
        "Biel": {"lat": 47.1404, "lon": 7.2471, "pop": 56896}
    }
    
    total_pop = sum(city["pop"] for city in cities.values())
    city_weights = {name: city["pop"] / total_pop for name, city in cities.items()}
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    weather_data = []
    
    with st.spinner("Fetching historical weather data..."):
        for city, coords in cities.items():
            try:
                url = (
                    f"https://archive-api.open-meteo.com/v1/archive?"
                    f"latitude={coords['lat']}&longitude={coords['lon']}"
                    f"&start_date={start_date.strftime('%Y-%m-%d')}"
                    f"&end_date={end_date.strftime('%Y-%m-%d')}"
                    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Europe/Zurich"
                )
                response = requests.get(url, timeout=10)
                data = response.json()
                
                for i, date in enumerate(data['daily']['time']):
                    weather_data.append({
                        "Day": datetime.strptime(date, "%Y-%m-%d"),
                        "City": city,
                        "Temp_Max": float(data['daily']['temperature_2m_max'][i]),  # Convert to Python float
                        "Temp_Min": float(data['daily']['temperature_2m_min'][i]),  # Convert to Python float
                        "Precipitation": float(data['daily']['precipitation_sum'][i]),  # Convert to Python float
                        "pop_weight": float(city_weights[city])  # Convert to Python float
                    })
            except Exception as e:
                continue
    
    if not weather_data:
        return None
    
    # Convert to DataFrame with explicit type handling to avoid numpy conversion issues
    try:
        # Try standard method first
        weather_df = pd.DataFrame(weather_data)
    except Exception as e:
        # Fallback: build DataFrame column by column (most robust method)
        st.warning(f"DataFrame creation issue in historical weather, using column-by-column method: {e}")
        try:
            # Extract columns separately to avoid numpy array issues
            days = [row["Day"] for row in weather_data]
            cities = [str(row["City"]) for row in weather_data]
            temp_max = [float(row["Temp_Max"]) for row in weather_data]
            temp_min = [float(row["Temp_Min"]) for row in weather_data]
            precip = [float(row["Precipitation"]) for row in weather_data]
            weights = [float(row["pop_weight"]) for row in weather_data]
            
            weather_df = pd.DataFrame({
                'Day': days,
                'City': cities,
                'Temp_Max': temp_max,
                'Temp_Min': temp_min,
                'Precipitation': precip,
                'pop_weight': weights
            })
        except Exception as e2:
            st.error(f"All DataFrame creation methods failed for historical weather: {e2}")
            return None
    
    weather_avg = weather_df.groupby('Day').apply(
        lambda x: pd.Series({
            'Temp_Max': float((x['Temp_Max'] * x['pop_weight']).sum()),
            'Temp_Min': float((x['Temp_Min'] * x['pop_weight']).sum()),
            'Precipitation': float((x['Precipitation'] * x['pop_weight']).sum())
        })
    ).reset_index()
    
    return weather_avg

@st.cache_data
def fetch_weather_forecast(days=7):
    """
    Fetch weather forecast for the next N days from Open-Meteo API
    Uses population-weighted average across top 10 Swiss cities
    """
    cities = {
        "Zurich": {"lat": 47.3769, "lon": 8.5417, "pop": 436551},
        "Geneva": {"lat": 46.2044, "lon": 6.1432, "pop": 209061},
        "Basel": {"lat": 47.5596, "lon": 7.5886, "pop": 177571},
        "Lausanne": {"lat": 46.5197, "lon": 6.6323, "pop": 144873},
        "Bern": {"lat": 46.9481, "lon": 7.4474, "pop": 137995},
        "Winterthur": {"lat": 47.5056, "lon": 8.7247, "pop": 120376},
        "Lucerne": {"lat": 47.0502, "lon": 8.3064, "pop": 86234},
        "St. Gallen": {"lat": 47.4245, "lon": 9.3767, "pop": 78863},
        "Lugano": {"lat": 46.0101, "lon": 8.9600, "pop": 63629},
        "Biel": {"lat": 47.1404, "lon": 7.2471, "pop": 56896}
    }
    
    # Calculate population weights
    total_pop = sum(city["pop"] for city in cities.values())
    city_weights = {name: city["pop"] / total_pop for name, city in cities.items()}
    
    weather_data = []
    
    with st.spinner("Fetching weather forecasts..."):
        for city, coords in cities.items():
            try:
                url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={coords['lat']}&longitude={coords['lon']}"
                    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
                    f"&timezone=Europe/Zurich&forecast_days={days}"
                )
                response = requests.get(url, timeout=10)
                data = response.json()
                
                for i, date in enumerate(data['daily']['time']):
                    weather_data.append({
                        "Day": datetime.strptime(date, "%Y-%m-%d"),
                        "City": city,
                        "Temp_Max": float(data['daily']['temperature_2m_max'][i]),  # Convert to Python float
                        "Temp_Min": float(data['daily']['temperature_2m_min'][i]),  # Convert to Python float
                        "Precipitation": float(data['daily']['precipitation_sum'][i]),  # Convert to Python float
                        "pop_weight": float(city_weights[city])  # Convert to Python float
                    })
            except Exception as e:
                st.warning(f"Error fetching data for {city}: {e}")
                continue
    
    if not weather_data:
        return None
    
    # Convert to DataFrame with explicit type handling to avoid numpy conversion issues
    try:
        # Try standard method first
        weather_df = pd.DataFrame(weather_data)
    except Exception as e:
        # Fallback: build DataFrame column by column (most robust method)
        st.warning(f"DataFrame creation issue, using column-by-column method: {e}")
        try:
            # Extract columns separately to avoid numpy array issues
            days = [row["Day"] for row in weather_data]
            cities = [str(row["City"]) for row in weather_data]
            temp_max = [float(row["Temp_Max"]) for row in weather_data]
            temp_min = [float(row["Temp_Min"]) for row in weather_data]
            precip = [float(row["Precipitation"]) for row in weather_data]
            weights = [float(row["pop_weight"]) for row in weather_data]
            
            weather_df = pd.DataFrame({
                'Day': days,
                'City': cities,
                'Temp_Max': temp_max,
                'Temp_Min': temp_min,
                'Precipitation': precip,
                'pop_weight': weights
            })
        except Exception as e2:
            st.error(f"All DataFrame creation methods failed: {e2}")
            return None
    
    # Calculate population-weighted average
    weather_avg = weather_df.groupby('Day').apply(
        lambda x: pd.Series({
            'Temp_Max': float((x['Temp_Max'] * x['pop_weight']).sum()),
            'Temp_Min': float((x['Temp_Min'] * x['pop_weight']).sum()),
            'Precipitation': float((x['Precipitation'] * x['pop_weight']).sum())
        })
    ).reset_index()
    
    return weather_avg

def create_temporal_features(df):
    """Create temporal features from Day column"""
    df = df.copy()
    df['dayofweek'] = df['Day'].dt.weekday
    df['month_num'] = df['Day'].dt.month
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    df['is_holiday'] = 0  # Simplified - could add holiday calendar
    
    # Cyclical encoding
    df['dayofweek_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['dayofweek_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * df['month_num'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month_num'] / 12)
    
    return df

def create_weather_features(df):
    """Create weather-derived features"""
    df = df.copy()
    df['temp_range'] = df['Temp_Max'] - df['Temp_Min']
    df['temp_comfort'] = (df['Temp_Max'] + df['Temp_Min']) / 2
    df['precip_binary'] = (df['Precipitation'] > 0).astype(int)
    df['precip_heavy'] = (df['Precipitation'] > 10).astype(int)
    df['Temp_Max_squared'] = df['Temp_Max'] ** 2
    
    # Interaction features
    df['Temp_Max_weekend'] = df['Temp_Max'] * df['is_weekend']
    df['Precipitation_weekend'] = df['Precipitation'] * df['is_weekend']
    df['temp_comfort_weekend'] = df['temp_comfort'] * df['is_weekend']
    
    return df

def prepare_forecast_features(weather_forecast, historical_weather, last_search_info):
    """
    Prepare features for forecasting.
    Uses only weather data - search lag features will be filled with predictions/fallbacks.
    """
    # Start with historical weather (last 14 days) for weather lag features
    if historical_weather is not None:
        hist_df = historical_weather.copy()
        hist_df['Day'] = pd.to_datetime(hist_df['Day'])
        hist_df['estimated_daily_searches'] = np.nan  # Not needed for weather lags
    else:
        # Fallback: use forecast weather for historical (not ideal but works)
        st.warning("⚠️ Could not fetch historical weather. Using forecast data as fallback.")
        if len(weather_forecast) > 0:
            hist_df = weather_forecast.iloc[0:1].copy()
            hist_df = pd.concat([hist_df] * 14, ignore_index=True)  # Repeat for 14 days
            hist_df['estimated_daily_searches'] = np.nan
        else:
            st.error("❌ No weather data available!")
            return None, None
    
    # Create full dataframe with historical + forecast
    forecast_df = weather_forecast.copy()
    forecast_df['estimated_daily_searches'] = np.nan  # Will be filled with predictions
    
    # Combine historical and forecast
    full_df = pd.concat([hist_df, forecast_df], ignore_index=True)
    full_df = full_df.sort_values('Day').reset_index(drop=True)
    
    # Create temporal features
    full_df = create_temporal_features(full_df)
    
    # Create weather features
    full_df = create_weather_features(full_df)
    
    # Create weather lag features (these are the important ones)
    full_df['Temp_Max_lag1'] = full_df['Temp_Max'].shift(1)
    full_df['Temp_Min_lag1'] = full_df['Temp_Min'].shift(1)
    full_df['Precipitation_lag1'] = full_df['Precipitation'].shift(1)
    
    full_df['Temp_Max_lag7'] = full_df['Temp_Max'].shift(7)
    full_df['Temp_Min_lag7'] = full_df['Temp_Min'].shift(7)
    full_df['Precipitation_lag7'] = full_df['Precipitation'].shift(7)
    
    # Initialize search lag features with fallback values
    # For historical rows, use the last known value
    # For forecast rows, initialize with last known value (will be updated during prediction)
    full_df['estimated_daily_searches_lag1'] = last_search_info['last_search_value']
    full_df['estimated_daily_searches_lag7'] = last_search_info['last_7days_ago_value']
    
    # For the first forecast day, lag1 should be the last known value (already set above)
    # For lag7, we need to check if we have data 7 days before the first forecast day
    # Since we don't have real search data, we'll use the fallback value and update during prediction
    
    # Rolling averages (using center=False for forward-looking)
    full_df['Temp_Max_7d'] = full_df['Temp_Max'].rolling(window=7, min_periods=1).mean()
    full_df['Precipitation_7d'] = full_df['Precipitation'].rolling(window=7, min_periods=1).mean()
    
    # Extract only forecast rows
    forecast_start_idx = len(hist_df)
    forecast_features = full_df.iloc[forecast_start_idx:].copy()
    
    return forecast_features, full_df

def make_predictions(model, forecast_features, full_df, historical_len):
    """
    Make predictions iteratively, using previous predictions for search lag features.
    Weather lag features are already calculated from historical weather data.
    """
    # Define feature order (must match training)
    feature_order = [
        'is_weekend', 'is_holiday', 'dayofweek_sin', 'dayofweek_cos', 
        'month_sin', 'month_cos',
        'Temp_Max', 'Temp_Min', 'Precipitation', 'temp_range', 'temp_comfort',
        'precip_binary', 'precip_heavy',
        'Temp_Max_lag1', 'Temp_Min_lag1', 'Precipitation_lag1', 'estimated_daily_searches_lag1',
        'estimated_daily_searches_lag7',
        'Temp_Max_lag7', 'Temp_Min_lag7', 'Precipitation_lag7',
        'Temp_Max_7d', 'Precipitation_7d',
        'Temp_Max_squared',
        'Temp_Max_weekend', 'Precipitation_weekend', 'temp_comfort_weekend'
    ]
    
    predictions = []
    
    for i in range(len(forecast_features)):
        # Get current row index in full_df
        idx = historical_len + i
        
        # Get current row features
        row = full_df.iloc[idx:idx+1].copy()
        
        # Prepare feature vector - keep as DataFrame to preserve categorical types
        # Handle NaN values by forward filling
        X = row[feature_order].ffill().fillna(0)
        
        # Ensure categorical features are integers (not floats) for CatBoost
        categorical_features = ['is_weekend', 'is_holiday', 'precip_binary', 'precip_heavy']
        for cat_feat in categorical_features:
            if cat_feat in X.columns:
                X[cat_feat] = X[cat_feat].astype(int)
        
        # Make prediction - pass DataFrame directly to CatBoost (it handles DataFrames correctly)
        pred = model.predict(X)[0]
        predictions.append(pred)
        
        # Update the full_df with this prediction
        full_df.loc[idx, 'estimated_daily_searches'] = pred
        
        # Update search lag features for next rows (weather lags are already set from historical data)
        if idx + 1 < len(full_df):
            # Update search lag1 for next day (use current prediction)
            full_df.loc[idx + 1, 'estimated_daily_searches_lag1'] = pred
        
        # Update search lag7 features (for 7 days ahead)
        if idx + 7 < len(full_df):
            full_df.loc[idx + 7, 'estimated_daily_searches_lag7'] = pred
        
        # Update rolling averages for next rows (weather rolling averages are already calculated)
        # No need to recalculate as they're based on weather which is already known
    
    return predictions

def categorize_demand(searches, historical_stats):
    """
    Categorize demand level based on historical percentiles
    and provide base recommendations (demand-focused) for
    delivery platforms and restaurants.

    Weather- and holiday-specific refinements are added later
    in the display logic.
    """
    if searches >= historical_stats['p90']:
        rec_platform_base = (
            "Demand is expected to be **much higher than on a normal day**. "
            "Plan significantly more active riders (e.g. +20–30% vs a "
            "typical day), ensure enough budget for boosts/surges, and "
            "closely monitor delivery times and service quality."
        )
        rec_restaurant_base = (
            "Prepare for a **very busy service** compared with a typical day. "
            "Add extra kitchen staff for peak periods, simplify the menu if "
            "needed, and pre-prepare your best-selling dishes to avoid "
            "bottlenecks and stock-outs."
        )
        return {
            "level": "CRITICAL",
            "priority": "Critical",
            "rec_platform_base": rec_platform_base,
            "rec_restaurant_base": rec_restaurant_base,
            "color": "red",
            "icon": "🔴",
        }

    elif searches >= historical_stats["p75"]:
        rec_platform_base = (
            "Demand should be **above average**. Schedule a few additional "
            "riders (e.g. +10–15%), and consider moderate incentives during "
            "the main peak periods."
        )
        rec_restaurant_base = (
            "Expect a **busy but manageable** service. Slightly increase "
            "kitchen staffing and make sure you have enough stock of your "
            "core dishes so you don’t run out at peak time."
        )
        return {
            "level": "HIGH",
            "priority": "High",
            "rec_platform_base": rec_platform_base,
            "rec_restaurant_base": rec_restaurant_base,
            "color": "orange",
            "icon": "🟠",
        }

    elif searches <= historical_stats["p25"]:
        rec_platform_base = (
            "Demand is likely to be **below normal**. No need to push for "
            "maximum volume; you can keep incentives low and focus on "
            "targeted marketing or retention campaigns."
        )
        rec_restaurant_base = (
            "Expect a **quieter day** than usual. Avoid over-staffing and be "
            "careful with fresh-product orders to keep waste under control. "
            "If you want more volume, use small promotions rather than large "
            "stock increases."
        )
        return {
            "level": "LOW",
            "priority": "Low",
            "rec_platform_base": rec_platform_base,
            "rec_restaurant_base": rec_restaurant_base,
            "color": "blue",
            "icon": "🔵",
        }

    else:
        rec_platform_base = (
            "Demand is expected to be **close to a typical day**. Keep your "
            "usual number of active riders and standard incentive schemes, "
            "but monitor the forecast in case local events change the picture."
        )
        rec_restaurant_base = (
            "Plan for a **normal service**. Maintain your standard staffing "
            "and stock levels and treat this as a baseline week to compare "
            "with future high- or low-demand periods."
        )
        return {
            "level": "NORMAL",
            "priority": "Normal",
            "rec_platform_base": rec_platform_base,
            "rec_restaurant_base": rec_restaurant_base,
            "color": "green",
            "icon": "🟢",
        }

def build_weather_adjustment_paragraphs(row):
    """
    Build additional paragraphs for delivery platforms and restaurants
    that take into account weather (and, if available, holidays).

    Returns:
        (platform_weather_text, restaurant_weather_text)
    """
    temp_max = row["Temp_Max"]
    temp_min = row["Temp_Min"]
    precip = row["Precipitation"]
    avg_temp = (temp_max + temp_min) / 2

    is_holiday = False
    if hasattr(row, "index") and "is_holiday" in row.index:
        try:
            is_holiday = bool(row["is_holiday"])
        except Exception:
            is_holiday = False

    platform_parts = []
    restaurant_parts = []

    if precip >= 5 and avg_temp <= 10:
        platform_parts.append(
            "Because the day is **cold and rainy**, deliveries are likely to "
            "take longer than on a dry day. Plan for slightly longer ETAs and "
            "consider concentrating riders in dense urban areas."
        )
        restaurant_parts.append(
            "Cold and rainy conditions usually mean fewer guests on the "
            "terrace and more people ordering from home. You can rely more "
            "on delivery and indoor seating and focus on warm, comforting dishes."
        )

    elif precip >= 5 and avg_temp > 10:
        platform_parts.append(
            "With **rainy but relatively mild** weather, people are less "
            "inclined to go out to eat, which tends to support delivery "
            "demand, especially in the evening."
        )
        restaurant_parts.append(
            "Rain will reduce terrace usage, so expect more indoor and "
            "delivery orders. Make sure your indoor capacity and packaging "
            "for delivery orders are well prepared."
        )

    elif precip < 1 and avg_temp >= 25:
        platform_parts.append(
            "On **very warm, dry** days, people may spend more time outside "
            "during the day and order more in the late evening when it is "
            "cooler. Expect demand to be more concentrated in the evening."
        )
        restaurant_parts.append(
            "Hot weather can mean fewer people at lunch but more activity in "
            "the evening. For stocks, expect more **cold and refreshing dishes** "
            "(salads, cold drinks, ice cream) and relatively fewer heavy hot dishes."
        )

    elif precip < 1 and 10 < avg_temp < 25:
        platform_parts.append(
            "The weather is **mild and dry**, which is fairly neutral for "
            "delivery. Demand will be driven more by day of week and events "
            "than by weather alone."
        )
        restaurant_parts.append(
            "Mild and dry conditions mean terrace usage is attractive but not "
            "extreme. Stocks can follow normal patterns without strong weather-driven shifts."
        )

    elif avg_temp <= 10 and precip < 5:
        platform_parts.append(
            "It will be **cold**, even if not very rainy. People are more "
            "likely to stay at home, which can support delivery demand, "
            "especially in the evening."
        )
        restaurant_parts.append(
            "Cold weather reduces terrace usage and increases the appeal of "
            "hot, comforting dishes. Make sure you have enough ingredients "
            "for your main warm meals."
        )

    else:
        platform_parts.append(
            "Weather conditions are relatively **neutral**. Use the forecast "
            "mainly as a guide vs the historical average and adjust based on "
            "local events or promotions."
        )
        restaurant_parts.append(
            "From a stock and staffing point of view, the weather does not "
            "require strong adjustments beyond what the demand level already suggests."
        )

    if is_holiday:
        platform_parts.append(
            "Since this is a **public holiday**, traffic patterns can be "
            "irregular and certain areas may be busier. Drivers in cars or "
            "scooters should anticipate possible traffic around shopping and "
            "leisure areas."
        )

    platform_text = " ".join(platform_parts)
    restaurant_text = " ".join(restaurant_parts)

    return platform_text, restaurant_text


# Main app logic
def main():
    # Load model
    model_path = Path('notebooks/models/catboost.pkl')
    if not model_path.exists():
        st.error("❌ Model file not found! Please ensure the model is trained and saved.")
        st.stop()
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Get last known search value for initial lag features
    last_search_info = get_last_known_search_value()
    
    # Load historical statistics for comparison and recommendations
    historical_stats = load_historical_data()
    
    # Fetch weather forecast and historical weather
    weather_forecast = fetch_weather_forecast(days=7)
    if weather_forecast is None:
        st.error("❌ Could not fetch weather forecast!")
        st.stop()
    
    historical_weather = fetch_historical_weather(days=14)
    
    # Prepare features (only needs weather data now)
    forecast_features, full_df = prepare_forecast_features(weather_forecast, historical_weather, last_search_info)
    
    if forecast_features is None:
        st.error("❌ Could not prepare forecast features!")
        st.stop()
    
    # Make predictions
    with st.spinner("Generating forecasts..."):
        # Calculate historical length (number of historical weather days)
        historical_len = len(historical_weather) if historical_weather is not None else 14
        predictions = make_predictions(model, forecast_features, full_df, historical_len)
    
    # Create results dataframe
    results_df = forecast_features[['Day', 'Temp_Max', 'Temp_Min', 'Precipitation']].copy()
    results_df['Predicted_Searches'] = predictions
    results_df['Weekday'] = results_df['Day'].dt.day_name()
    results_df['Is_Weekend'] = results_df['Day'].dt.weekday >= 5
    
    # Add demand categorization for each day
    results_df['Demand_Category'] = results_df['Predicted_Searches'].apply(
        lambda x: categorize_demand(x, historical_stats)
    )
    
    # Calculate week statistics
    week_avg = results_df['Predicted_Searches'].mean()
    week_total = results_df['Predicted_Searches'].sum()
    week_vs_historical = ((week_avg - historical_stats['mean']) / historical_stats['mean']) * 100
    
    # Executive Summary
    st.header("📊 Executive Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Week Average", 
            f"{int(week_avg):,}",
            delta=f"{week_vs_historical:+.1f}% vs historical"
        )
    with col2:
        st.metric(
            "Total Expected Searches", 
            f"{int(week_total):,}",
            delta=f"{int(week_total - (historical_stats['mean'] * 7)):+,}"
        )
    with col3:
        high_demand_days = len(results_df[results_df['Predicted_Searches'] >= historical_stats['p75']])
        st.metric("High Demand Days", f"{high_demand_days}", delta=f"out of 7 days")
    with col4:
        peak_day = results_df.loc[results_df['Predicted_Searches'].idxmax()]
        st.metric("Peak Day", peak_day['Day'].strftime('%b %d'), 
                 delta=f"{int(peak_day['Predicted_Searches']):,} searches")
    
    # Week assessment
    if week_vs_historical > 15:
        assessment = "🔴 **Above Average Week** - Prepare for elevated demand"
        assessment_color = "red"
    elif week_vs_historical < -15:
        assessment = "🔵 **Below Average Week** - Consider promotional strategies"
        assessment_color = "blue"
    else:
        assessment = "🟢 **Normal Week** - Standard operations"
        assessment_color = "green"
    
        st.info(
        f"**Week Assessment**: {assessment}\n\n"
        f"This week's average demand ({int(week_avg):,} searches/day) is "
        f"**{abs(week_vs_historical):.1f}%** "
        f"{'above' if week_vs_historical > 0 else 'below'} the historical average "
        f"({int(historical_stats['mean']):,} searches/day)."
    )


    st.subheader("🤔 How reliable is this forecast?")
    model_uncertainty_text = (
        f"Our forecasting model (currently **{MODEL_NAME}**) explains about "
        f"**{MODEL_R2 * 100:.1f}%** of the day-to-day variation in historical "
        "Uber Eats search volume (R²).  \n"
        "That is decent for human behaviour data, but it also means there is "
        "**still a lot of unexplained variability**.\n\n"
        "- Use the forecasts as **directional signals** (higher or lower than usual), "
        "not as exact numbers.  \n"
        "- Focus on the **percentage differences** vs the historical average and the "
        "**demand categories** (LOW / NORMAL / HIGH / CRITICAL) when planning staffing "
        "and stock.  \n"
        f"- An RMSE of about **{MODEL_RMSE:,.0f} searches** means that on a single day, "
        "the true value can easily be a few hundred searches above or below the forecast.  \n"
        "- Keep a **safety buffer** in rider and kitchen capacity on HIGH and CRITICAL days, "
        "and avoid cutting too aggressively on LOW days."
    )
    st.markdown(model_uncertainty_text)

    # Display results
    st.header("📈 7-Day Forecast")
    
    # Main visualization
    fig = go.Figure()
    
    # Add historical average reference line
    fig.add_hline(
        y=historical_stats['mean'],
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Historical Average ({int(historical_stats['mean']):,})",
        annotation_position="right"
    )
    
    # Add percentile reference lines
    fig.add_hline(
        y=historical_stats['p75'],
        line_dash="dot",
        line_color="orange",
        opacity=0.5,
        annotation_text=f"75th Percentile ({int(historical_stats['p75']):,})",
        annotation_position="right"
    )
    
    fig.add_hline(
        y=historical_stats['p25'],
        line_dash="dot",
        line_color="blue",
        opacity=0.5,
        annotation_text=f"25th Percentile ({int(historical_stats['p25']):,})",
        annotation_position="right"
    )
    
    # Add forecast line
    fig.add_trace(go.Scatter(
        x=results_df['Day'],
        y=results_df['Predicted_Searches'],
        mode='lines+markers',
        name='Forecasted Searches',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title='7-Day Forecast: Estimated Daily Searches (with Historical Context)',
        xaxis_title='Date',
        yaxis_title='Estimated Daily Searches',
        yaxis=dict(range=[0, None]),  # Start y-axis at 0 for more realistic visualization
        hovermode='x unified',
        height=500,
        template='plotly_white',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader("📋 Detailed Forecast Table")
    display_df = results_df[['Day', 'Weekday', 'Temp_Max', 'Temp_Min', 'Precipitation', 
                             'Predicted_Searches']].copy()
    
    # Convert Day to string - use list comprehension to ensure pure Python strings
    display_df['Day'] = [str(d.date()) for d in display_df['Day']]
    display_df['Temp_Max'] = display_df['Temp_Max'].round(1)
    display_df['Temp_Min'] = display_df['Temp_Min'].round(1)
    display_df['Precipitation'] = display_df['Precipitation'].round(1)
    display_df['Predicted_Searches'] = display_df['Predicted_Searches'].round(0).astype(int)
    
    # Rename columns
    display_df.columns = ['Date', 'Weekday', 'Max Temp (°C)', 'Min Temp (°C)', 
                          'Precipitation (mm)', 'Expected Searches']
    
    # Use st.table() with fallback to HTML table if Arrow conversion issues persist
    try:
        st.table(display_df.style.hide_index())
    except Exception:
        # Ultimate fallback: display as markdown table
        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Historical Comparison Chart
    st.subheader("📊 Historical Comparison")
    
    fig_compare = go.Figure()
    
    # Add historical average bar
    fig_compare.add_trace(go.Bar(
        x=['Historical Average'],
        y=[historical_stats['mean']],
        name='Historical Average',
        marker_color='lightgray',
        text=[f"{int(historical_stats['mean']):,}"],
        textposition='auto'
    ))
    
    # Add forecast week average bar
    fig_compare.add_trace(go.Bar(
        x=['This Week Forecast'],
        y=[week_avg],
        name='This Week Forecast',
        marker_color='#1f77b4',
        text=[f"{int(week_avg):,}"],
        textposition='auto'
    ))
    
    fig_compare.update_layout(
        title='Forecast vs Historical Average',
        yaxis_title='Average Daily Searches',
        height=300,
        template='plotly_white',
        showlegend=False
    )
    
    st.plotly_chart(fig_compare, use_container_width=True)
    
    # Business insights with threshold-based recommendations
    st.header("💡 Daily Recommendations")
    
    # Sort days by demand level for better presentation
    results_sorted = results_df.sort_values('Predicted_Searches', ascending=False)
    
    # Show top 3 days needing attention
    st.subheader("🎯 Priority Days")
    
    cols = st.columns(3)
    for idx, (col, (_, day_row)) in enumerate(zip(cols, results_sorted.head(3).iterrows())):
        category = day_row["Demand_Category"]
        platform_weather, restaurant_weather = build_weather_adjustment_paragraphs(day_row)
        
        with col:
            st.markdown(
                f"**{category['icon']} {day_row['Day'].strftime('%A, %b %d')}**"
            )
            st.markdown(
                f"**Expected**: {int(day_row['Predicted_Searches']):,} searches  "
            )
            st.markdown(
                f"**Level**: {category['level']} ({category['priority']} Priority)"
            )
            st.markdown("**🚚 Platform (summary):**")
            st.markdown(category["rec_platform_base"])
            st.markdown("**🍽 Restaurant (summary):**")
            st.markdown(category["rec_restaurant_base"])
            st.markdown(
                f"*Weather: {day_row['Temp_Max']:.1f}°C / {day_row['Temp_Min']:.1f}°C, "
                f"{day_row['Precipitation']:.1f}mm*"
            )
    
    # Detailed day-by-day recommendations
    st.subheader("📅 Complete Week Breakdown")
    
    for _, day_row in results_df.iterrows():
        category = day_row["Demand_Category"]
        percentile = None
        if day_row["Predicted_Searches"] >= historical_stats["p90"]:
            percentile = "90th+"
        elif day_row["Predicted_Searches"] >= historical_stats["p75"]:
            percentile = "75th-90th"
        elif day_row["Predicted_Searches"] <= historical_stats["p25"]:
            percentile = "25th or below"
        else:
            percentile = "25th-75th"
    
        with st.expander(
            f"{category['icon']} {day_row['Day'].strftime('%A, %B %d')} - "
            f"{category['level']} Demand ({int(day_row['Predicted_Searches']):,} searches)"
        ):
            col1, col2 = st.columns(2)
    
            with col1:
                st.metric(
                    "Expected Searches",
                    f"{int(day_row['Predicted_Searches']):,}",
                    delta=f"{percentile} percentile",
                )
                st.metric(
                    "vs Historical Avg",
                    f"{((day_row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean'] * 100):+.1f}%",
                    delta=f"{int(day_row['Predicted_Searches'] - historical_stats['mean']):+,}",
                )
    
            with col2:
                st.write("**Weather Conditions:**")
                st.write(f"- Max Temp: {day_row['Temp_Max']:.1f}°C")
                st.write(f"- Min Temp: {day_row['Temp_Min']:.1f}°C")
                st.write(f"- Precipitation: {day_row['Precipitation']:.1f}mm")
    
            
            platform_weather, restaurant_weather = build_weather_adjustment_paragraphs(day_row)
    
            st.markdown("**🚚 Recommendation for delivery platforms:**")
            st.markdown(
                category["rec_platform_base"] + "\n\n" + platform_weather
            )
    
            st.markdown("**🍽 Recommendation for restaurants:**")
            st.markdown(
                category["rec_restaurant_base"] + "\n\n" + restaurant_weather
            )



    
    # Download button
    st.download_button(
        label="📥 Download Forecast Data (CSV)",
        data=display_df.to_csv(index=False),
        file_name=f"uber_eats_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
