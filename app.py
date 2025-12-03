import streamlit as st
import pandas as pd
import numpy as np
import pickle
import requests
import random
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from io import StringIO
import urllib.parse
import warnings
warnings.filterwarnings('ignore')

MODEL_NAME = "CatBoost Regression"
MODEL_R2 = 0.3652
MODEL_RMSE = 684.56

# Page configuration
st.set_page_config(
    page_title="Uber Eats Demand Forecast",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
def inject_custom_css():
    st.markdown("""
    <style>
    /* Main app styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9) !important;
        font-size: 1.1rem;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Landing page cards */
    .role-card {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        text-align: center;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        cursor: pointer;
    }
    
    .role-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    
    .role-card .icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .role-card h3 {
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    
    .role-card p {
        color: #718096;
        font-size: 0.95rem;
    }
    
    /* Animated background for landing */
    .landing-bg {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        padding: 3rem;
        border-radius: 25px;
        margin: 2rem 0;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Stats highlight */
    .stat-highlight {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        display: inline-block;
        font-weight: bold;
    }
    
    /* Calendar heatmap cell */
    .calendar-day {
        padding: 0.8rem;
        border-radius: 8px;
        text-align: center;
        margin: 2px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Progress bars */
    .demand-bar {
        height: 8px;
        border-radius: 4px;
        background: #e2e8f0;
        overflow: hidden;
    }
    
    .demand-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    
    /* Weather icons */
    .weather-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    
    .weather-sunny { background: #fef3c7; color: #d97706; }
    .weather-rainy { background: #dbeafe; color: #2563eb; }
    .weather-cold { background: #e0e7ff; color: #4f46e5; }
    
    /* Sidebar improvements */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Animated number counter effect */
    @keyframes countUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animated-metric {
        animation: countUp 0.5s ease-out forwards;
    }
    
    /* Feature cards */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    .feature-card h4 {
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    /* Recommendation box */
    .recommendation-box {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-left: 4px solid #0ea5e9;
        padding: 1.5rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
    }
    
    /* Alert styles */
    .alert-critical { border-left-color: #ef4444; background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); }
    .alert-high { border-left-color: #f97316; background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); }
    .alert-normal { border-left-color: #22c55e; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); }
    .alert-low { border-left-color: #3b82f6; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for user type selection
if 'user_type_selected' not in st.session_state:
    st.session_state.user_type_selected = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def show_landing_page():
    """Display the enhanced welcome/landing page with role selection"""
    inject_custom_css()
    
    # Animated header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div class="landing-bg">
            <h1 style="color: white; font-size: 3.5rem; margin-bottom: 0.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
                🍔 Uber Eats Demand Forecast
            </h1>
            <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem; max-width: 600px; margin: 0 auto;">
                AI-powered 7-day demand predictions for Switzerland with weather-based insights
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Features showcase
    st.markdown("<br>", unsafe_allow_html=True)
    
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    
    with feat_col1:
        st.markdown("""
        <div class="feature-card" style="text-align: center; min-height: 140px;">
            <div style="font-size: 2.5rem;">📊</div>
            <h4>Smart Forecasting</h4>
            <p style="color: #64748b; font-size: 0.9rem;">Machine learning predictions based on weather & historical patterns</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col2:
        st.markdown("""
        <div class="feature-card" style="text-align: center; min-height: 140px;">
            <div style="font-size: 2.5rem;">🎯</div>
            <h4>Tailored Insights</h4>
            <p style="color: #64748b; font-size: 0.9rem;">Personalized recommendations for your specific business needs</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col3:
        st.markdown("""
        <div class="feature-card" style="text-align: center; min-height: 140px;">
            <div style="font-size: 2.5rem;">⚡</div>
            <h4>Actionable Tools</h4>
            <p style="color: #64748b; font-size: 0.9rem;">Planning calculators, communication tools & more</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Role selection with enhanced cards
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #1e293b;">👤 Select Your Role</h2>
        <p style="color: #64748b;">Choose your perspective to get personalized forecasts and recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="role-card" style="min-height: 220px;">
            <div class="icon">🍽️</div>
            <h3>Restaurant Owner</h3>
            <p>Optimize inventory, staffing, and prep schedules</p>
            <br>
            <div style="color: #667eea; font-weight: 600;">Features:</div>
            <p style="font-size: 0.85rem;">✓ Inventory planner<br>✓ Staff scheduler<br>✓ Demand insights</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🍽️ I'm a Restaurant", use_container_width=True, type="primary", key="btn_restaurant"):
            st.session_state.user_type = "🍽️ Restaurant"
            st.session_state.user_type_selected = True
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="role-card" style="min-height: 220px;">
            <div class="icon">🚚</div>
            <h3>Delivery Platform</h3>
            <p>Plan rider allocation and driver communications</p>
            <br>
            <div style="color: #667eea; font-weight: 600;">Features:</div>
            <p style="font-size: 0.85rem;">✓ Rider calculator<br>✓ Driver messaging<br>✓ Fleet planning</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚚 I'm a Delivery Platform", use_container_width=True, type="primary", key="btn_platform"):
            st.session_state.user_type = "🚚 Delivery Platform"
            st.session_state.user_type_selected = True
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="role-card" style="min-height: 220px;">
            <div class="icon">🚴</div>
            <h3>Delivery Driver</h3>
            <p>Find the best days to work and maximize earnings</p>
            <br>
            <div style="color: #667eea; font-weight: 600;">Features:</div>
            <p style="font-size: 0.85rem;">✓ Earnings forecast<br>✓ Weather prep<br>✓ Schedule optimizer</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚴 I'm a Delivery Driver", use_container_width=True, type="primary", key="btn_driver"):
            st.session_state.user_type = "🚴 Delivery Driver"
            st.session_state.user_type_selected = True
            st.rerun()

def show_main_dashboard():
    """Display the main dashboard"""
    inject_custom_css()
    
    # Enhanced header with gradient
    if st.session_state.user_type == "🍽️ Restaurant":
        role_emoji = "🍽️"
        role_name = "Restaurant"
    elif st.session_state.user_type == "🚚 Delivery Platform":
        role_emoji = "🚚"
        role_name = "Delivery Platform"
    else:
        role_emoji = "🚴"
        role_name = "Delivery Driver"
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🍔 Uber Eats Demand Forecast</h1>
        <p>{role_emoji} Viewing as <strong>{role_name}</strong> • 📅 Week of {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Apply dark mode if enabled
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
                .stApp { background-color: #0f172a; color: #e2e8f0; }
                .stMarkdown, .stText, p, span, label, h1, h2, h3, h4, h5, h6 { color: #e2e8f0 !important; }
                .stMetric label, .stMetric [data-testid="stMetricValue"] { color: #e2e8f0 !important; }
                [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%); }
                .feature-card, .metric-card, .role-card { background: #1e293b; border-color: #334155; }
                .feature-card h4, .feature-card p { color: #e2e8f0 !important; }
            </style>
        """, unsafe_allow_html=True)

# Sidebar for information (always visible when on main dashboard)
def show_sidebar():
    with st.sidebar:
        st.header("👤 Your Role")
        # Allow changing role from sidebar
        role_options = ["🍽️ Restaurant", "🚚 Delivery Platform", "🚴 Delivery Driver"]
        current_index = role_options.index(st.session_state.user_type) if st.session_state.user_type in role_options else 0
        new_user_type = st.radio(
            "Switch role:",
            options=role_options,
            index=current_index,
            key="sidebar_user_type"
        )
        # Update if changed
        if new_user_type != st.session_state.user_type:
            st.session_state.user_type = new_user_type
            st.rerun()
        
        st.markdown("---")
        
        st.header("📊 About")
        st.markdown("""**Data**: Switzerland  
**Weather**: Open-Meteo API  
**Updated**: Weekly forecasts""")
        
        st.header("💡 Quick Tips")
        if st.session_state.user_type == "🍽️ Restaurant":
            st.markdown("""
- 🌧️ **Rain = More delivery orders** - stock up on takeaway packaging
- 📅 **Weekends differ** - Friday & Sunday are typically busier
- ❄️ **Cold weather** - comfort food orders increase
- 🔴 **HIGH days** - prep extra, schedule more staff
            """)
        elif st.session_state.user_type == "🚚 Delivery Platform":
            st.markdown("""
- 🚴 **Rider surge** - plan 20% buffer on HIGH days
- 🌧️ **Bad weather** - expect longer ETAs, notify drivers
            """)
        else:  # Driver
            st.markdown("""
- 🔥 **HOT days** - more orders, better tips
- 🌧️ **Rain days** - fewer drivers online = more orders for you
- 📱 **Be strategic** - work fewer but busier days
            """)
        
        st.markdown("---")
        if st.button("🔄 Back to Welcome Screen"):
            st.session_state.user_type_selected = False
            st.session_state.user_type = None
            st.rerun()

@st.cache_data
def load_historical_data():
    """Load historical search data and calculate statistics"""
    try:
        url = "https://raw.githubusercontent.com/cedricly-git/BADS_Capstone_repo/main/Data/ubereats+time_related_vars.csv"
        # Use requests to fetch data (handles SSL better on macOS)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text), engine='python')
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
        url = "https://raw.githubusercontent.com/cedricly-git/BADS_Capstone_repo/main/Data/ubereats+time_related_vars.csv"
        # Use requests to fetch data (handles SSL better on macOS)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text), engine='python')
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
    # Check if user has selected their role
    if not st.session_state.user_type_selected:
        show_landing_page()
        return
    
    # Show main dashboard
    show_main_dashboard()
    show_sidebar()
    
    # Get user type from session state
    user_type = st.session_state.user_type
    
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
    typical_week_total = historical_stats['mean'] * 7
    
    # Calculate additional metrics for both user types
    peak_day = results_df.loc[results_df['Predicted_Searches'].idxmax()]
    peak_vs_normal = ((peak_day['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
    
    # High/Critical demand days (>= 75th percentile)
    high_critical_days = len(results_df[results_df['Predicted_Searches'] >= historical_stats['p75']])
    
    # Weather-related metrics
    # Delivery-favoring weather: rainy (precip > 1mm) OR cold (avg temp < 10°C)
    results_df['avg_temp'] = (results_df['Temp_Max'] + results_df['Temp_Min']) / 2
    delivery_weather_days = len(results_df[
        (results_df['Precipitation'] > 1) | (results_df['avg_temp'] < 10)
    ])
    
    # Weather disruption risk: heavy rain (>5mm) OR very cold (<5°C) with precipitation
    weather_disruption_days = len(results_df[
        (results_df['Precipitation'] > 5) | 
        ((results_df['avg_temp'] < 5) & (results_df['Precipitation'] > 0))
    ])
    
    # Previous week comparison (if historical data available)
    prev_week_total = None
    prev_week_change = None
    if historical_stats['data'] is not None:
        hist_df = historical_stats['data']
        # Get last 7 days from historical data
        if len(hist_df) >= 7:
            prev_week_total = hist_df.tail(7)['estimated_daily_searches'].sum()
            prev_week_change = ((week_total - prev_week_total) / prev_week_total) * 100
    
    # Executive Summary
    st.header("📊 Executive Summary")
    
    if user_type == "🍽️ Restaurant":
        # Restaurant-specific metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📈 Avg Daily Demand", 
                f"{int(week_avg):,}",
                delta=f"{week_vs_historical:+.1f}% vs normal",
                help="How busy the upcoming week is compared to a typical day"
            )
        
        with col2:
            st.metric(
                "🔥 Busiest Day", 
                peak_day['Day'].strftime('%A, %b %d'),
                delta=f"+{peak_vs_normal:.0f}% vs normal",
                help="Your heaviest delivery day this week"
            )
        
        with col3:
            st.metric(
                "👨‍🍳 Intense Kitchen Days", 
                f"{high_critical_days}",
                delta="days to prep extra",
                help="Days requiring extra prep, staff, or simplified menu"
            )
        
        col4, col5 = st.columns(2)
        
        with col4:
            st.metric(
                "🌧️ Delivery-Favoring Weather", 
                f"{delivery_weather_days}",
                delta="days (rain/cold)",
                help="Days where weather pushes people to order from home"
            )
        
        with col5:
            if prev_week_total is not None:
                st.metric(
                    "📊 vs Previous Week", 
                    f"{int(week_total):,}",
                    delta=f"{prev_week_change:+.1f}% ({int(week_total - prev_week_total):+,})",
                    help="This week's total searches vs previous week"
                )
            else:
                st.metric(
                    "📊 Weekly Total", 
                    f"{int(week_total):,}",
                    delta=f"{((week_total - typical_week_total) / typical_week_total * 100):+.1f}% vs typical",
                    help="Total expected searches this week"
                )
    
    elif user_type == "🚚 Delivery Platform":
        # Platform-specific metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "📦 Total Weekly Volume", 
                f"{int(week_total):,}",
                delta=f"{((week_total - typical_week_total) / typical_week_total * 100):+.1f}% vs typical week",
                help="Overall search volume for the coming week"
            )
        
        with col2:
            st.metric(
                "🚴 Peak Search Day", 
                peak_day['Day'].strftime('%A, %b %d'),
                delta=f"+{peak_vs_normal:.0f}% vs normal ({int(peak_day['Predicted_Searches']):,})",
                help="Highest volume day - proxy for rider load"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.metric(
                "⚡ High/Critical Days", 
                f"{high_critical_days}",
                delta="days needing more fleet",
                help="Days that may need more riders, incentives, tighter ETA monitoring"
            )
        
        with col4:
            st.metric(
                "⚠️ Weather Risk Days", 
                f"{weather_disruption_days}",
                delta="days with ETA risk",
                help="Days where ETAs and rider comfort are at risk due to bad weather"
            )
    
    else:  # Delivery Driver
        # Driver-specific metrics - focused on earnings potential
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Week opportunity score (based on demand vs average)
            opportunity_score = "🔥 Hot" if week_vs_historical > 10 else "✅ Good" if week_vs_historical > -5 else "😐 Slow"
            st.metric(
                "💰 Week Outlook", 
                opportunity_score,
                delta=f"{week_vs_historical:+.1f}% vs typical",
                help="Overall earning opportunity this week"
            )
        
        with col2:
            st.metric(
                "⭐ Best Day to Work", 
                peak_day['Day'].strftime('%A'),
                delta=f"+{peak_vs_normal:.0f}% demand",
                help="Day with highest search volume = best earning potential"
            )
        
        with col3:
            st.metric(
                "📈 High Demand Days", 
                f"{high_critical_days}",
                delta="priority days",
                help="Number of days with above-average search demand"
            )
        
        col4, col5 = st.columns(2)
        
        with col4:
            # Good weather days for riding
            good_weather_days = 7 - weather_disruption_days
            st.metric(
                "☀️ Nice Weather Days", 
                f"{good_weather_days}",
                delta="comfortable riding",
                help="Days with good conditions for deliveries"
            )
        
        with col5:
            st.metric(
                "⚠️ Gear Up Days", 
                f"{weather_disruption_days}",
                delta="rain/cold expected",
                help="Days where you'll need rain gear or warm clothes"
            )
    
    # ============== QUICK ACTIONS - Role-specific summary ==============
    
    # Get best and worst days
    best_day = results_df.loc[results_df['Predicted_Searches'].idxmax()]
    worst_day = results_df.loc[results_df['Predicted_Searches'].idxmin()]
    rainy_days = results_df[results_df['Precipitation'] > 3]
    cold_days = results_df[results_df['avg_temp'] < 8]
    
    # Get TODAY's data
    today = datetime.now().date()
    today_data = results_df[results_df['Day'].dt.date == today]
    tomorrow_data = results_df[results_df['Day'].dt.date == today + pd.Timedelta(days=1)]
    
    if user_type == "🍽️ Restaurant":
        # ===== TODAY'S FOCUS FOR RESTAURANTS =====
        st.markdown("### 📍 Today's Focus")
        
        if not today_data.empty:
            today_row = today_data.iloc[0]
            today_category = today_row['Demand_Category']
            today_pct = ((today_row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
            
            # Determine today's action
            if today_category['level'] in ['CRITICAL', 'HIGH']:
                today_status = "🔴 BUSY DAY"
                today_color = "#ef4444"
                today_actions = ["✓ Call in extra kitchen staff", "✓ Prep 20% more ingredients", "✓ Check takeaway packaging stock"]
            elif today_category['level'] == 'NORMAL':
                today_status = "🟢 NORMAL DAY"
                today_color = "#22c55e"
                today_actions = ["✓ Standard prep levels", "✓ Regular staffing", "✓ Focus on quality"]
            else:
                today_status = "🔵 QUIET DAY"
                today_color = "#3b82f6"
                today_actions = ["✓ Consider a flash promotion", "✓ Use slower time for deep prep", "✓ Train new staff"]
            
            # Weather considerations
            if today_row['Precipitation'] > 3:
                today_actions.append("☔ Rain expected - expect more delivery orders")
            if today_row['avg_temp'] < 8:
                today_actions.append("❄️ Cold weather - comfort food will sell well")
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {today_color}22 0%, {today_color}11 100%); border: 2px solid {today_color}; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <span style="font-size: 1.5rem; font-weight: bold; color: {today_color};">{today_status}</span>
                        <span style="margin-left: 1rem; color: #64748b;">({today_pct:+.0f}% vs average)</span>
                    </div>
                    <div style="text-align: right;">
                        <span>🌡️ {today_row['Temp_Max']:.0f}°/{today_row['Temp_Min']:.0f}°</span>
                        <span style="margin-left: 0.5rem;">💧 {today_row['Precipitation']:.1f}mm</span>
                    </div>
                </div>
                <div style="color: #374151;">
                    {'<br>'.join(today_actions)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📅 Today's forecast will appear when the day arrives.")
        
        # ===== WEEKLY OVERVIEW FOR RESTAURANTS =====
        st.markdown("### 📋 This Week's Prep Plan")
        
        # Promotion suggestions for slow days
        slow_days = results_df.nsmallest(2, 'Predicted_Searches')
        promo_suggestions = [
            "🎉 2-for-1 desserts", "🍕 Free delivery over CHF 30", "⏰ Happy hour pricing",
            "🎁 Loyalty double points", "📱 App-exclusive discount", "🥗 New menu tasting"
        ]
        random.seed(42)  # Consistent suggestions
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <strong>🔥 Busiest Day:</strong> {best_day['Day'].strftime('%A')}<br>
                    <span style="font-size: 0.9rem; color: #78350f;">+{int(((best_day['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100)}% demand expected</span>
                </div>
                <div>
                    <strong>👨‍🍳 High-Demand Days:</strong> {high_critical_days}<br>
                    <span style="font-size: 0.9rem; color: #78350f;">Order extra stock for these days</span>
                </div>
                <div>
                    <strong>📉 Promotion Days:</strong> {slow_days.iloc[0]['Day'].strftime('%a')}, {slow_days.iloc[1]['Day'].strftime('%a')}<br>
                    <span style="font-size: 0.9rem; color: #78350f;">Suggested: {random.choice(promo_suggestions)}</span>
                </div>
                <div>
                    <strong>🌧️ Delivery Weather:</strong> {delivery_weather_days} days<br>
                    <span style="font-size: 0.9rem; color: #78350f;">{'Stock takeaway packaging!' if delivery_weather_days > 0 else 'Balanced dine-in/delivery'}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    elif user_type == "🚚 Delivery Platform":
        # ===== OPERATIONS DASHBOARD FOR PLATFORMS =====
        st.markdown("### 🎯 Operations Dashboard")
        
        # Calculate surge recommendations
        surge_days = []
        sla_risk_days = []
        for _, row in results_df.iterrows():
            pct = ((row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
            if pct > 20:
                surge_days.append((row['Day'].strftime('%a'), 'HIGH', '#ef4444'))
            elif pct > 10:
                surge_days.append((row['Day'].strftime('%a'), 'MEDIUM', '#f59e0b'))
            
            # SLA risk = high demand + bad weather
            if row['Precipitation'] > 3 or (pct > 15 and row['avg_temp'] < 5):
                sla_risk_days.append(row['Day'].strftime('%A'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 1.2rem; border-radius: 12px; height: 100%;">
                <h4 style="margin: 0 0 0.8rem 0; color: #92400e;">💰 Surge Pricing Recommendations</h4>
            """, unsafe_allow_html=True)
            
            if surge_days:
                for day, level, color in surge_days:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.3rem 0;">
                        <span>{day}</span>
                        <span style="background: {color}; color: white; padding: 0.1rem 0.5rem; border-radius: 8px; font-size: 0.8rem;">{level}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #78350f;'>No surge needed this week</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 1.2rem; border-radius: 12px; height: 100%;">
                <h4 style="margin: 0 0 0.8rem 0; color: #991b1b;">⚠️ SLA Risk Days</h4>
                <p style="color: #7f1d1d; margin: 0; font-size: 0.95rem;">
                    {', '.join(sla_risk_days) if sla_risk_days else 'No high-risk days identified'}
                </p>
                <p style="color: #991b1b; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                    {'→ Increase ETA buffers, notify drivers early' if sla_risk_days else '→ Standard operations expected'}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Operations Checklist
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
            <h4 style="margin: 0 0 1rem 0; color: #1e40af;">📋 Weekly Operations Checklist</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <strong>🚴 Fleet Scaling:</strong> {best_day['Day'].strftime('%A')}<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">→ +30% riders, activate incentives</span>
                </div>
                <div>
                    <strong>📊 Weekly Searches:</strong> ~{int(week_total):,}<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">→ Use Rider Calculator tab to estimate orders</span>
                </div>
                <div>
                    <strong>⚡ Critical Days:</strong> {high_critical_days}<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">→ Pre-position riders, monitor queues</span>
                </div>
                <div>
                    <strong>🌧️ Weather Risk:</strong> {weather_disruption_days} days<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">→ {'Send gear reminders to drivers' if weather_disruption_days > 0 else 'No action needed'}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:  # Delivery Driver
        # ===== SHOULD I WORK TODAY? - DRIVER'S MAIN QUESTION =====
        st.markdown("### 📍 Should I Work Today?")
        
        if not today_data.empty:
            today_row = today_data.iloc[0]
            today_pct = ((today_row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
            
            # Simple traffic light decision
            if today_pct > 15:
                decision = "🟢 YES! High demand today"
                decision_color = "#22c55e"
                decision_bg = "#dcfce7"
                earning_boost = "+20-30%"
                advice = "Great day to maximize your hours!"
            elif today_pct > 0:
                decision = "🟡 GOOD - Above average day"
                decision_color = "#f59e0b"
                decision_bg = "#fef3c7"
                earning_boost = "+10-15%"
                advice = "Good day to work - expect steady demand throughout."
            elif today_pct > -10:
                decision = "🟠 OK - Average day"
                decision_color = "#f97316"
                decision_bg = "#ffedd5"
                earning_boost = "Normal"
                advice = "Average day - may want to limit your hours."
            else:
                decision = "🔴 SLOW - Below average"
                decision_color = "#ef4444"
                decision_bg = "#fee2e2"
                earning_boost = "-10-15%"
                advice = "Maybe take the day off? Tomorrow might be better."
            
            # Weather impact
            weather_note = ""
            if today_row['Precipitation'] > 5:
                weather_note = "🌧️ Heavy rain - fewer drivers online = more orders for YOU! (bring gear)"
                decision = "🟢 YES! Rain day bonus"
                decision_color = "#22c55e"
                decision_bg = "#dcfce7"
            elif today_row['Precipitation'] > 2:
                weather_note = "🌦️ Light rain expected - bring a jacket"
            elif today_row['avg_temp'] < 5:
                weather_note = "❄️ Cold day - dress warm, thermal layers recommended"
            
            st.markdown(f"""
            <div style="background: {decision_bg}; border: 3px solid {decision_color}; padding: 2rem; border-radius: 16px; text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; font-weight: bold; color: {decision_color}; margin-bottom: 0.5rem;">
                    {decision}
                </div>
                <div style="font-size: 1.1rem; color: #374151; margin-bottom: 0.5rem;">
                    Earnings potential: <strong>{earning_boost}</strong> vs average
                </div>
                <div style="font-size: 0.95rem; color: #6b7280;">
                    💡 {advice}
                </div>
                {f'<div style="margin-top: 0.8rem; padding: 0.5rem; background: rgba(0,0,0,0.05); border-radius: 8px; font-size: 0.9rem;">{weather_note}</div>' if weather_note else ''}
            </div>
            """, unsafe_allow_html=True)
            
            # Quick peek at tomorrow
            if not tomorrow_data.empty:
                tmrw = tomorrow_data.iloc[0]
                tmrw_pct = ((tmrw['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
                tmrw_status = "🔥 HOT" if tmrw_pct > 15 else "✅ Good" if tmrw_pct > 0 else "😐 Average" if tmrw_pct > -10 else "📉 Slow"
                st.markdown(f"**Tomorrow ({tmrw['Day'].strftime('%A')}):** {tmrw_status} ({tmrw_pct:+.0f}%)")
        else:
            st.info("📅 Today's forecast will appear when the day arrives. Check the weekly view below!")
        
        st.markdown("---")
        
        # ===== WEEKLY SUMMARY FOR DRIVERS =====
        st.markdown("### 📋 Your Week at a Glance")
        
        # Calculate driver-specific weekly stats
        top_3_earning_days = results_df.nlargest(3, 'Predicted_Searches')
        worst_day = results_df.nsmallest(1, 'Predicted_Searches').iloc[0]
        rainy_bonus_days = len(results_df[results_df['Precipitation'] > 3])
        cold_days = len(results_df[results_df['avg_temp'] < 5])
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <strong>🔥 Best Day to Work:</strong> {best_day['Day'].strftime('%A')}<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">+{int(((best_day['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100)}% above average demand</span>
                </div>
                <div>
                    <strong>📈 High Demand Days:</strong> {high_critical_days}<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">Best days to maximize earnings</span>
                </div>
                <div>
                    <strong>📉 Slowest Day:</strong> {worst_day['Day'].strftime('%A')}<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">Consider taking this day off</span>
                </div>
                <div>
                    <strong>🌧️ Rain Bonus Days:</strong> {rainy_bonus_days}<br>
                    <span style="font-size: 0.9rem; color: #1e3a8a;">{'Fewer drivers = more orders for you!' if rainy_bonus_days > 0 else 'No rainy days expected'}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ===== WEEKLY OVERVIEW FOR DRIVERS - SIMPLER =====
        st.markdown("### 📅 Best Days This Week")
        
        # Best 3 days to work
        top_3_days = results_df.nlargest(3, 'Predicted_Searches')
        
        # Create simple visual ranking
        for rank, (_, row) in enumerate(top_3_days.iterrows(), 1):
            pct = ((row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
            
            # Weather icon
            if row['Precipitation'] > 3:
                weather_icon = "🌧️"
            elif row['avg_temp'] < 8:
                weather_icon = "❄️"
            else:
                weather_icon = "☀️"
            
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 0.8rem 1rem; border-radius: 10px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.2rem;">{medal}</span>
                    <strong style="margin-left: 0.5rem;">{row['Day'].strftime('%A, %b %d')}</strong>
                </div>
                <div>
                    <span style="color: #22c55e; font-weight: bold;">+{pct:.0f}%</span>
                    <span style="margin-left: 0.8rem;">{weather_icon} {row['Temp_Max']:.0f}°</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============== TABBED INTERFACE ==============
    if user_type == "🍽️ Restaurant":
        tab1, tab2, tab3 = st.tabs(["📈 Forecast Overview", "📦 Inventory Planner", "👥 Staff Scheduler"])
    elif user_type == "🚚 Delivery Platform":
        tab1, tab2, tab3 = st.tabs(["📈 Forecast Overview", "🚴 Rider Calculator", "📨 Driver Comms"])
    else:  # Delivery Driver
        tab1, tab2, tab3 = st.tabs(["💰 Earnings Forecast", "🌤️ Weather Prep", "📅 Schedule Planner"])
    
    # ============== TAB 1: FORECAST OVERVIEW ==============
    with tab1:
        # Different headers based on role
        if user_type == "🚴 Delivery Driver":
            st.subheader("💰 When to Work This Week")
        elif user_type == "🍽️ Restaurant":
            st.subheader("🗓️ Expected Demand This Week")
        else:
            st.subheader("🗓️ 7-Day Demand Forecast")
        
        # Create visual cards for each day
        cols = st.columns(7)
        for idx, (_, row) in enumerate(results_df.iterrows()):
            category = row['Demand_Category']
            pct_vs_avg = ((row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
            
            # Color based on demand level
            color_map = {
                'CRITICAL': '#ef4444',
                'HIGH': '#f97316', 
                'NORMAL': '#22c55e',
                'LOW': '#3b82f6'
            }
            bg_color = color_map.get(category['level'], '#22c55e')
            
            # Weather icon
            if row['Precipitation'] > 5:
                weather_icon = "🌧️"
            elif row['Precipitation'] > 1:
                weather_icon = "🌦️"
            elif row['avg_temp'] < 5:
                weather_icon = "❄️"
            elif row['avg_temp'] > 25:
                weather_icon = "☀️"
            else:
                weather_icon = "⛅"
            
            with cols[idx]:
                if user_type == "🚴 Delivery Driver":
                    # Driver-focused: show earning potential, not numbers
                    if pct_vs_avg > 15:
                        earning_label = "🔥 HOT"
                    elif pct_vs_avg > 0:
                        earning_label = "✅ GOOD"
                    elif pct_vs_avg > -10:
                        earning_label = "😐 OK"
                    else:
                        earning_label = "📉 SLOW"
                    
                    st.markdown(f"""
                    <div style="background: {bg_color}; color: white; padding: 0.8rem; border-radius: 12px; text-align: center;">
                        <div style="font-weight: bold;">{row['Day'].strftime('%a')}</div>
                        <div style="font-size: 0.75rem; opacity: 0.9;">{row['Day'].strftime('%b %d')}</div>
                        <div style="font-size: 1rem; font-weight: bold; margin: 0.3rem 0;">{earning_label}</div>
                        <div style="font-size: 1.2rem;">{weather_icon}</div>
                        <div style="font-size: 0.7rem;">{row['Temp_Max']:.0f}°/{row['Temp_Min']:.0f}°</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif user_type == "🍽️ Restaurant":
                    # Restaurant-focused: show busy level and action
                    if category['level'] == 'CRITICAL':
                        action_label = "VERY BUSY"
                    elif category['level'] == 'HIGH':
                        action_label = "BUSY"
                    elif category['level'] == 'NORMAL':
                        action_label = "NORMAL"
                    else:
                        action_label = "QUIET"
                    
                    st.markdown(f"""
                    <div style="background: {bg_color}; color: white; padding: 0.8rem; border-radius: 12px; text-align: center;">
                        <div style="font-weight: bold;">{row['Day'].strftime('%a')}</div>
                        <div style="font-size: 0.75rem; opacity: 0.9;">{row['Day'].strftime('%b %d')}</div>
                        <div style="font-size: 0.9rem; font-weight: bold; margin: 0.3rem 0;">{action_label}</div>
                        <div style="font-size: 1.2rem;">{weather_icon}</div>
                        <div style="font-size: 0.7rem;">{row['Temp_Max']:.0f}°/{row['Temp_Min']:.0f}°</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Platform: show actual numbers
                    st.markdown(f"""
                    <div style="background: {bg_color}; color: white; padding: 0.8rem; border-radius: 12px; text-align: center;">
                        <div style="font-weight: bold;">{row['Day'].strftime('%a')}</div>
                        <div style="font-size: 0.75rem; opacity: 0.9;">{row['Day'].strftime('%b %d')}</div>
                        <div style="font-size: 1.4rem; font-weight: bold; margin: 0.3rem 0;">{int(row['Predicted_Searches']):,}</div>
                        <div style="font-size: 1.2rem;">{weather_icon}</div>
                        <div style="font-size: 0.7rem;">{row['Temp_Max']:.0f}°/{row['Temp_Min']:.0f}°</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Trend chart - different views for different roles
        if user_type == "🚴 Delivery Driver":
            # For drivers, show a simpler "earning potential" bar chart
            st.subheader("📊 Daily Earning Potential")
            
            # User input for base hourly rate
            base_hourly = st.number_input(
                "Your average hourly earnings (CHF)", 
                value=20, 
                min_value=10, 
                max_value=50, 
                step=1,
                help="Your typical earnings per hour of active delivery. This varies by city, time of day, and platform. Check your recent payouts to estimate."
            )
            
            # Calculate relative earnings (normalized to average)
            earning_multipliers = []
            for _, row in results_df.iterrows():
                pct = ((row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
                multiplier = 1 + (pct / 100)
                # Add rain bonus
                if row['Precipitation'] > 5:
                    multiplier *= 1.15  # 15% bonus for rain days
                earning_multipliers.append(multiplier)
            estimated_hourly = [base_hourly * m for m in earning_multipliers]
            
            colors = ['#22c55e' if e > base_hourly * 1.1 else '#f59e0b' if e > base_hourly else '#94a3b8' for e in estimated_hourly]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=results_df['Day'].dt.strftime('%a'),
                    y=estimated_hourly,
                    marker_color=colors,
                    text=[f'CHF {e:.0f}/h' for e in estimated_hourly],
                    textposition='outside'
                )
            ])
            
            fig.add_hline(y=base_hourly, line_dash="dash", line_color="#94a3b8", 
                         annotation_text="Average", annotation_position="right")
            
            fig.update_layout(
                height=280,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="",
                yaxis_title="Est. CHF/hour",
                template='plotly_white',
                showlegend=False,
                yaxis=dict(range=[0, max(estimated_hourly) * 1.2])
            )
        else:
            # For restaurants and platforms, keep the line chart
            chart_title = "📈 Demand Trend"
            st.subheader(chart_title)
            fig = go.Figure()
            
            # Add area fill
            fig.add_trace(go.Scatter(
                x=results_df['Day'],
                y=results_df['Predicted_Searches'],
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)',
                line=dict(color='#667eea', width=3),
                mode='lines+markers',
                marker=dict(size=10, color='#667eea'),
                name='Forecast'
            ))
            
            # Add historical average line
            fig.add_hline(
                y=historical_stats['mean'],
                line_dash="dash",
                line_color="#94a3b8",
                annotation_text=f"Avg: {int(historical_stats['mean']):,}",
                annotation_position="right"
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="",
                yaxis_title="Searches",
                template='plotly_white',
                showlegend=False
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Day-by-day details (expandable)
        if user_type == "🚴 Delivery Driver":
            st.subheader("📋 Daily Breakdown")
            for _, day_row in results_df.iterrows():
                category = day_row["Demand_Category"]
                pct_vs_avg = ((day_row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
                
                # Earning potential indicator
                if pct_vs_avg > 15:
                    earning_indicator = "🔥 High earnings"
                    earning_color = "#22c55e"
                elif pct_vs_avg > 0:
                    earning_indicator = "✅ Good earnings"
                    earning_color = "#3b82f6"
                elif pct_vs_avg > -10:
                    earning_indicator = "😐 Average"
                    earning_color = "#f59e0b"
                else:
                    earning_indicator = "📉 Slow day"
                    earning_color = "#94a3b8"
                
                # Weather icon
                if day_row['Precipitation'] > 5:
                    weather_tip = "🌧️ Rain gear needed!"
                elif day_row['Precipitation'] > 1:
                    weather_tip = "🌦️ Light rain possible"
                elif day_row['avg_temp'] < 5:
                    weather_tip = "❄️ Dress warm!"
                elif day_row['avg_temp'] > 25:
                    weather_tip = "☀️ Stay hydrated!"
                else:
                    weather_tip = "⛅ Nice conditions"
                
                with st.expander(f"{category['icon']} {day_row['Day'].strftime('%A, %b %d')} — {earning_indicator} ({pct_vs_avg:+.0f}%)"):
                    st.markdown(f"""
                    **💰 Earning Potential:** {earning_indicator}  
                    **🌡️ Weather:** {day_row['Temp_Max']:.0f}°C / {day_row['Temp_Min']:.0f}°C • {day_row['Precipitation']:.1f}mm  
                    **💡 Tip:** {weather_tip}
                    """)
        else:
            st.subheader("📋 Daily Details & Recommendations")
            for _, day_row in results_df.iterrows():
                category = day_row["Demand_Category"]
                pct_vs_avg = ((day_row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
                
                with st.expander(f"{category['icon']} {day_row['Day'].strftime('%A, %b %d')} — {int(day_row['Predicted_Searches']):,} searches ({pct_vs_avg:+.0f}%)"):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.markdown(f"""
                        **Weather**  
                        🌡️ {day_row['Temp_Max']:.0f}°C / {day_row['Temp_Min']:.0f}°C  
                        💧 {day_row['Precipitation']:.1f}mm
                        """)
                    with col2:
                        platform_weather, restaurant_weather = build_weather_adjustment_paragraphs(day_row)
                        if user_type == "🚚 Delivery Platform":
                            st.markdown(f"**💡 Recommendation:** {category['rec_platform_base']}")
                        else:
                            st.markdown(f"**💡 Recommendation:** {category['rec_restaurant_base']}")
    
    # ============== TAB 2: PLANNING TOOLS / WEATHER PREP ==============
    with tab2:
        if user_type == "🍽️ Restaurant":
            # INVENTORY PLANNER
            st.subheader("📦 Inventory Planner")
            st.markdown("Plan your ingredient orders based on expected demand levels.")
            
            st.markdown("**Configure your baseline:**")
            inv_col1, inv_col2 = st.columns(2)
            with inv_col1:
                baseline_covers = st.number_input("Average daily covers (normal day)", value=100, min_value=10, max_value=1000)
                avg_items_per_order = st.number_input("Average items per order", value=2.5, min_value=1.0, max_value=10.0, step=0.5)
            with inv_col2:
                safety_buffer = st.slider("Safety buffer %", 0, 50, 15, help="Extra stock percentage to account for unexpected demand spikes or higher-than-forecasted orders. Higher buffer = less risk of running out, but more potential waste.")
                waste_tolerance = st.slider("Acceptable waste %", 0, 20, 5)
            
            st.markdown("---")
            st.markdown("**📊 Recommended Order Quantities:**")
            
            # Calculate order recommendations
            order_cols = st.columns(7)
            total_weekly_items = 0
            
            for idx, (_, row) in enumerate(results_df.iterrows()):
                category = row['Demand_Category']
                demand_multiplier = {
                    'CRITICAL': 1.3,
                    'HIGH': 1.15,
                    'NORMAL': 1.0,
                    'LOW': 0.85
                }.get(category['level'], 1.0)
                
                expected_covers = baseline_covers * demand_multiplier
                expected_items = expected_covers * avg_items_per_order
                with_buffer = expected_items * (1 + safety_buffer/100)
                total_weekly_items += with_buffer
                
                with order_cols[idx]:
                    st.markdown(f"""
                    <div style="background: #f8fafc; padding: 0.8rem; border-radius: 10px; text-align: center;">
                        <div style="font-weight: bold; font-size: 0.85rem;">{row['Day'].strftime('%a')}</div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: #667eea;">{int(with_buffer)}</div>
                        <div style="font-size: 0.7rem; color: #64748b;">items needed</div>
                        <div style="font-size: 0.7rem; color: {'#ef4444' if category['level'] == 'CRITICAL' else '#22c55e'};">{category['level'].lower()}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
                <h4 style="color: white; margin: 0;">📦 Weekly Total: {int(total_weekly_items):,} items</h4>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">With {safety_buffer}% safety buffer included</p>
            </div>
            """, unsafe_allow_html=True)
        
        elif user_type == "🚴 Delivery Driver":
            # WEATHER PREP for Drivers
            st.subheader("🌤️ Weather Preparation Guide")
            st.markdown("Plan your gear and clothing for the week ahead.")
            
            # Weather summary cards
            st.markdown("**📅 Daily Weather & Gear:**")
            
            for _, row in results_df.iterrows():
                avg_temp = row['avg_temp']
                precip = row['Precipitation']
                
                # Determine gear recommendations
                gear_items = []
                weather_status = ""
                status_color = "#22c55e"
                
                if precip > 5:
                    weather_status = "🌧️ Rainy"
                    status_color = "#3b82f6"
                    gear_items = ["🧥 Waterproof jacket", "👖 Rain pants", "🧤 Waterproof gloves", "👟 Waterproof shoes"]
                elif precip > 1:
                    weather_status = "🌦️ Light rain"
                    status_color = "#60a5fa"
                    gear_items = ["🧥 Light rain jacket", "🎒 Bag cover"]
                elif avg_temp < 5:
                    weather_status = "❄️ Cold"
                    status_color = "#8b5cf6"
                    gear_items = ["🧥 Warm jacket", "🧤 Insulated gloves", "🧣 Scarf/neck warmer", "🎿 Thermal layers"]
                elif avg_temp < 10:
                    weather_status = "🌬️ Cool"
                    status_color = "#a78bfa"
                    gear_items = ["🧥 Light jacket", "🧤 Light gloves"]
                elif avg_temp > 25:
                    weather_status = "☀️ Hot"
                    status_color = "#f59e0b"
                    gear_items = ["🧢 Cap/hat", "🕶️ Sunglasses", "💧 Extra water", "🧴 Sunscreen"]
                else:
                    weather_status = "⛅ Pleasant"
                    status_color = "#22c55e"
                    gear_items = ["👕 Comfortable clothes", "🧢 Optional cap"]
                
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 4px solid {status_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{row['Day'].strftime('%A, %b %d')}</strong>
                            <span style="background: {status_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 10px; margin-left: 0.5rem; font-size: 0.8rem;">{weather_status}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 1.1rem;">🌡️ {row['Temp_Max']:.0f}°/{row['Temp_Min']:.0f}°</span>
                            <span style="margin-left: 0.5rem;">💧 {precip:.1f}mm</span>
                        </div>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #64748b;">
                        <strong>Gear:</strong> {' • '.join(gear_items)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Weekly gear checklist
            st.markdown("---")
            st.markdown("**🎒 Weekly Gear Checklist:**")
            
            all_gear = set()
            rainy_days = len(results_df[results_df['Precipitation'] > 1])
            cold_days = len(results_df[results_df['avg_temp'] < 10])
            hot_days = len(results_df[results_df['avg_temp'] > 25])
            
            checklist_items = ["✅ Phone & charger", "✅ Delivery bag", "✅ Phone mount"]
            if rainy_days > 0:
                checklist_items.extend(["✅ Rain jacket", "✅ Bag rain cover"])
            if cold_days > 0:
                checklist_items.extend(["✅ Warm gloves", "✅ Thermal layers"])
            if hot_days > 0:
                checklist_items.extend(["✅ Sunscreen", "✅ Extra water bottle"])
            
            col1, col2 = st.columns(2)
            with col1:
                for item in checklist_items[:len(checklist_items)//2 + 1]:
                    st.markdown(item)
            with col2:
                for item in checklist_items[len(checklist_items)//2 + 1:]:
                    st.markdown(item)
        
        else:
            # RIDER CALCULATOR for Delivery Platform
            st.subheader("🚴 Rider Allocation Calculator")
            st.markdown("Plan your fleet size based on expected demand.")
            
            st.markdown("**Configure your parameters:**")
            rider_col1, rider_col2 = st.columns(2)
            with rider_col1:
                deliveries_per_rider_hour = st.number_input("Deliveries per rider per hour", value=2.5, min_value=1.0, max_value=5.0, step=0.5)
                search_to_order_rate = st.slider("Search to order conversion %", 1, 20, 8, help="Percentage of searches that convert to actual orders. Varies by market, time of day, and platform. Check your analytics for your specific conversion rate.")
                peak_hours_per_day = st.number_input("Peak hours per day", value=4, min_value=2, max_value=8)
            with rider_col2:
                rider_utilization = st.slider("Target rider utilization %", 50, 95, 75, help="Percentage of a rider's time spent actively delivering (vs idle/waiting). Higher utilization = more efficient but less flexibility for demand spikes. Typical range: 70-80%.")
                surge_buffer = st.slider("Surge buffer %", 0, 50, 20, help="Extra rider capacity percentage to handle unexpected demand surges, order batching delays, or weather-related slowdowns. Higher buffer = better coverage but higher costs.")
            
            st.markdown("---")
            st.markdown("**🚴 Recommended Rider Count by Day:**")
            
            rider_cols = st.columns(7)
            for idx, (_, row) in enumerate(results_df.iterrows()):
                category = row['Demand_Category']
                
                # Calculate expected orders
                expected_orders = row['Predicted_Searches'] * (search_to_order_rate / 100)
                # Orders per peak hour
                orders_per_hour = expected_orders / peak_hours_per_day
                # Base riders needed
                base_riders = orders_per_hour / (deliveries_per_rider_hour * (rider_utilization / 100))
                # With surge buffer
                recommended_riders = base_riders * (1 + surge_buffer / 100)
                
                with rider_cols[idx]:
                    rider_color = '#ef4444' if recommended_riders > 50 else '#f97316' if recommended_riders > 30 else '#22c55e'
                    st.markdown(f"""
                    <div style="background: #f8fafc; padding: 0.8rem; border-radius: 10px; text-align: center;">
                        <div style="font-weight: bold; font-size: 0.85rem;">{row['Day'].strftime('%a')}</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: {rider_color};">{int(recommended_riders)}</div>
                        <div style="font-size: 0.7rem; color: #64748b;">riders needed</div>
                        <div style="font-size: 0.65rem; color: #94a3b8;">~{int(expected_orders)} orders (from searches)</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Summary
            total_rider_hours = sum([
                (row['Predicted_Searches'] * search_to_order_rate / 100 / deliveries_per_rider_hour) * peak_hours_per_day * (1 + surge_buffer/100)
                for _, row in results_df.iterrows()
            ])
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
                <h4 style="color: white; margin: 0;">📊 Weekly Summary</h4>
                <p style="margin: 0.5rem 0 0 0;">Total rider-hours needed: <strong>{int(total_rider_hours):,}</strong></p>
                <p style="margin: 0.3rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">Based on {search_to_order_rate}% conversion rate and {rider_utilization}% utilization</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ============== TAB 3: COMMUNICATIONS / STAFF ==============
    with tab3:
        if user_type == "🍽️ Restaurant":
            # STAFF SCHEDULER
            st.subheader("👥 Staff Scheduler")
            st.markdown("Plan your kitchen and service staff based on expected demand.")
            
            st.markdown("**Your staff configuration:**")
            staff_col1, staff_col2 = st.columns(2)
            with staff_col1:
                baseline_kitchen = st.number_input("Baseline kitchen staff (normal day)", value=3, min_value=1, max_value=20)
                baseline_service = st.number_input("Baseline service staff (normal day)", value=2, min_value=0, max_value=20)
            with staff_col2:
                shift_length = st.number_input("Average shift length (hours)", value=6, min_value=4, max_value=12)
                hourly_rate = st.number_input("Average hourly rate (CHF)", value=25, min_value=15, max_value=60)
            
            st.markdown("---")
            st.markdown("**📅 Recommended Staffing Schedule:**")
            
            weekly_labor_cost = 0
            for _, row in results_df.iterrows():
                category = row['Demand_Category']
                
                staff_multiplier = {
                    'CRITICAL': 1.5,
                    'HIGH': 1.25,
                    'NORMAL': 1.0,
                    'LOW': 0.8
                }.get(category['level'], 1.0)
                
                rec_kitchen = max(1, int(baseline_kitchen * staff_multiplier))
                rec_service = max(0, int(baseline_service * staff_multiplier))
                day_cost = (rec_kitchen + rec_service) * shift_length * hourly_rate
                weekly_labor_cost += day_cost
                
                level_colors = {
                    'CRITICAL': '#fee2e2',
                    'HIGH': '#ffedd5',
                    'NORMAL': '#dcfce7',
                    'LOW': '#dbeafe'
                }
                bg_color = level_colors.get(category['level'], '#dcfce7')
                
                st.markdown(f"""
                <div style="background: {bg_color}; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{row['Day'].strftime('%A, %b %d')}</strong>
                        <span style="margin-left: 0.5rem; font-size: 0.8rem; color: #64748b;">({category['level']})</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="margin-right: 1rem;">👨‍🍳 Kitchen: <strong>{rec_kitchen}</strong></span>
                        <span>🍽️ Service: <strong>{rec_service}</strong></span>
                        <span style="margin-left: 1rem; color: #64748b;">~CHF {int(day_cost)}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
                <h4 style="color: white; margin: 0;">💰 Estimated Weekly Labor Cost: CHF {int(weekly_labor_cost):,}</h4>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Based on {shift_length}h shifts at CHF {hourly_rate}/hour average</p>
            </div>
            """, unsafe_allow_html=True)
        
        elif user_type == "🚴 Delivery Driver":
            # SCHEDULE PLANNER for Drivers - SIMPLIFIED
            st.subheader("📅 Your Optimal Week")
            st.markdown("Here's how to maximize earnings based on demand forecasts.")
            
            # User inputs for earnings calculation
            st.markdown("**Your delivery stats:**")
            earning_col1, earning_col2 = st.columns(2)
            with earning_col1:
                avg_earning_per_delivery = st.number_input(
                    "Average earning per delivery (CHF)", 
                    value=8.0, 
                    min_value=3.0, 
                    max_value=25.0, 
                    step=0.5,
                    help="Your typical payout per completed delivery, including base pay and tips. Check your recent deliveries to calculate your average."
                )
                deliveries_per_hour = st.number_input(
                    "Deliveries per hour", 
                    value=2.5, 
                    min_value=1.0, 
                    max_value=5.0, 
                    step=0.5,
                    help="How many deliveries you typically complete per hour of active work. Depends on your area density and speed."
                )
            with earning_col2:
                target_weekly_hours = st.select_slider(
                    "Target weekly hours",
                    options=[10, 15, 20, 25, 30, 35, 40],
                    value=25,
                    help="How many total hours you want to work this week. We'll distribute them across the best days."
                )
                st.metric("Est. hourly rate", f"CHF {avg_earning_per_delivery * deliveries_per_hour:.0f}/h")
            
            st.markdown("---")
            
            # Calculate daily recommendations
            daily_scores = []
            for _, row in results_df.iterrows():
                pct_vs_avg = ((row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
                # Rain bonus for drivers (fewer drivers = more orders per driver)
                weather_bonus = 0
                if row['Precipitation'] > 5:
                    weather_bonus = 10  # Rain is actually GOOD for drivers
                score = pct_vs_avg + weather_bonus
                daily_scores.append({'day': row['Day'], 'score': score, 'row': row, 'pct': pct_vs_avg})
            
            # Sort by score
            daily_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Distribute hours based on ranking
            remaining_hours = target_weekly_hours
            schedule = {}
            
            for i, item in enumerate(daily_scores):
                if remaining_hours <= 0:
                    schedule[item['day']] = 0
                elif i < 2:  # Top 2 days get more hours
                    hours = min(8, remaining_hours)
                    schedule[item['day']] = hours
                    remaining_hours -= hours
                elif i < 5:  # Middle days
                    hours = min(4, remaining_hours)
                    schedule[item['day']] = hours
                    remaining_hours -= hours
                else:  # Lower priority days
                    hours = min(2, remaining_hours)
                    schedule[item['day']] = hours
                    remaining_hours -= hours
            
            total_projected_earnings = 0
            
            for _, row in results_df.iterrows():
                hours = schedule.get(row['Day'], 0)
                category = row['Demand_Category']
                pct_vs_avg = ((row['Predicted_Searches'] - historical_stats['mean']) / historical_stats['mean']) * 100
                
                # Estimate earnings
                daily_earnings = hours * deliveries_per_hour * avg_earning_per_delivery
                total_projected_earnings += daily_earnings
                
                # Priority indicator
                if hours >= 6:
                    priority = "⭐ Priority"
                    priority_color = "#22c55e"
                elif hours >= 3:
                    priority = "✅ Recommended"
                    priority_color = "#3b82f6"
                elif hours > 0:
                    priority = "📝 Optional"
                    priority_color = "#f59e0b"
                else:
                    priority = "❌ Skip"
                    priority_color = "#94a3b8"
                
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 4px solid {priority_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{row['Day'].strftime('%A, %b %d')}</strong>
                            <span style="background: {priority_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 10px; margin-left: 0.5rem; font-size: 0.75rem;">{priority}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 1.1rem; font-weight: bold; color: #667eea;">{hours:.0f}h</span>
                            <span style="margin-left: 0.5rem; color: #64748b;">~CHF {daily_earnings:.0f}</span>
                        </div>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.3rem;">
                        Demand: {pct_vs_avg:+.0f}% • {category['level']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
                <h4 style="color: white; margin: 0;">💰 Projected Weekly Earnings: ~CHF {int(total_projected_earnings):,}</h4>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Based on {target_weekly_hours}h at {deliveries_per_hour} deliveries/hour</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
        
        else:
            # DRIVER COMMUNICATION for Platforms
            
            # Get top 3 busiest days
            top_days = results_df.nlargest(3, 'Predicted_Searches')
            top_day = top_days.iloc[0]
            
            # Determine weather warnings for top days
            weather_warnings = []
            for _, day in top_days.iterrows():
                if day['Precipitation'] > 5:
                    weather_warnings.append(f"🌧️ {day['Day'].strftime('%A')}: Rain expected - gear up!")
                elif day['avg_temp'] < 5:
                    weather_warnings.append(f"❄️ {day['Day'].strftime('%A')}: Cold day - dress warm!")
            
            st.markdown("**Generate ready-to-send messages to motivate your drivers on high-demand days.**")
            
            # Message customization
            msg_col1, msg_col2 = st.columns(2)
            
            with msg_col1:
                message_tone = st.selectbox(
                    "Message tone:",
                    ["🎯 Motivational", "📋 Professional", "🚀 Energetic"],
                    key="message_tone"
                )
            
            with msg_col2:
                message_format = st.selectbox(
                    "Message format:",
                    ["📧 Email (detailed)", "💬 SMS (short)", "📱 Push notification"],
                    key="message_format"
                )
            
            # Generate message based on selections
            busy_days_list = ", ".join([d['Day'].strftime('%A') for _, d in top_days.iterrows()])
            peak_day_name = top_day['Day'].strftime('%A, %B %d')
            peak_uplift = int(peak_vs_normal)
            
            if message_tone == "🎯 Motivational":
                tone_opener = "Great opportunity this week! 💪"
                tone_cta = "Don't miss out on these peak earning days!"
            elif message_tone == "📋 Professional":
                tone_opener = "Weekly forecast update:"
                tone_cta = "Plan your schedule accordingly for optimal earnings."
            else:  # Energetic
                tone_opener = "🔥 Big week ahead!"
                tone_cta = "Get ready to crush it! 🚴‍♂️💨"
            
            if message_format == "📧 Email (detailed)":
                message = f"""Subject: 📊 This Week's Delivery Forecast - Maximize Your Earnings!

Hi Driver,

{tone_opener}

📈 **High Demand Days**: {busy_days_list}
🏆 **Peak Day**: {peak_day_name} (+{peak_uplift}% above normal)
📦 **Weekly Volume**: {int(week_total):,} expected searches ({week_vs_historical:+.0f}% vs typical)

{"**Weather Alerts:**" + chr(10) + chr(10).join(weather_warnings) if weather_warnings else "☀️ No severe weather expected this week."}

💡 **Tip**: Being online during peak hours on {top_day['Day'].strftime('%A')} could mean higher earnings and potential bonuses!

{tone_cta}

Happy delivering! 🚴
Your Platform Team"""

            elif message_format == "💬 SMS (short)":
                message = f"""📊 Week Forecast: {busy_days_list} = busy days! 
🏆 Peak: {top_day['Day'].strftime('%A')} (+{peak_uplift}%)
{weather_warnings[0] if weather_warnings else "☀️ Good weather expected"}
{tone_cta}"""

            else:  # Push notification
                message = f"""🔔 {tone_opener} {top_day['Day'].strftime('%A')} is {peak_uplift}% busier than usual. Go online to maximize earnings! 💰"""
            
            # Display generated message
            st.text_area(
                "Generated message:",
                value=message,
                height=300 if message_format == "📧 Email (detailed)" else 120,
                key="driver_message"
            )
            
            # Download as text option
            st.download_button(
                label="📋 Download as Text File",
                data=message,
                file_name="driver_message.txt",
                mime="text/plain"
            )
            
            # Email sending section - Simple with Resend API
            st.markdown("---")
            st.markdown("### 📧 Send to Drivers")
            
            recipient_email = st.text_input(
                "📬 Enter recipient email:",
                placeholder="drivers@yourcompany.com",
                key="driver_email_input"
            )
            
            if st.button("📤 Send Email", use_container_width=True, type="primary", key="send_email_btn"):
                if not recipient_email:
                    st.error("❌ Please enter an email address.")
                elif "@" not in recipient_email:
                    st.error("❌ Please enter a valid email address.")
                else:
                    with st.spinner("Sending email..."):
                        try:
                            # Resend API
                            RESEND_API_KEY = "re_Crn4XSXd_GD4WfLvaDU8opd8wVLf3KxoR"
                            
                            # Clean message for email (remove markdown)
                            plain_message = message.replace('**', '').replace('*', '')
                            
                            response = requests.post(
                                "https://api.resend.com/emails",
                                headers={
                                    "Authorization": f"Bearer {RESEND_API_KEY}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "from": "Uber Eats Forecast <onboarding@resend.dev>",
                                    "to": [recipient_email],
                                    "subject": "📊 This Week's Delivery Forecast - Maximize Your Earnings!",
                                    "text": plain_message
                                },
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                st.success(f"✅ Email sent successfully to **{recipient_email}**!")
                                st.balloons()
                            else:
                                error_msg = response.json().get('message', 'Unknown error')
                                st.error(f"❌ Failed to send email: {error_msg}")
                                
                        except requests.exceptions.Timeout:
                            st.error("❌ Request timed out. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

    # ============== FOOTER SECTION ==============
    st.markdown("---")
    
    # Role-specific tips and download
    if user_type == "🍽️ Restaurant":
        st.info("💡 **Pro Tip:** Check the forecast every Monday morning to plan your week's inventory order and staff schedule. Weather changes can shift demand by 15-20%.")
    elif user_type == "🚚 Delivery Platform":
        st.info("💡 **Pro Tip:** Share the driver communication tool with your ops team. Pre-scheduling riders based on forecast reduces wait times and improves customer satisfaction.")
    else:
        st.info("💡 **Pro Tip:** Check the forecast on Sunday evening to plan your week. Working high-demand days (🔥 HOT) can increase your weekly earnings by 20-30%.")
    
    # Download option for platform users only (they need data exports)
    if user_type == "🚚 Delivery Platform":
        display_df = results_df[['Day', 'Weekday', 'Temp_Max', 'Temp_Min', 'Precipitation', 
                                 'Predicted_Searches']].copy()
        display_df['Day'] = [str(d.date()) for d in display_df['Day']]
        display_df['Temp_Max'] = display_df['Temp_Max'].round(1)
        display_df['Temp_Min'] = display_df['Temp_Min'].round(1)
        display_df['Precipitation'] = display_df['Precipitation'].round(1)
        display_df['Predicted_Searches'] = display_df['Predicted_Searches'].round(0).astype(int)
        display_df.columns = ['Date', 'Weekday', 'Max Temp (°C)', 'Min Temp (°C)', 
                              'Precipitation (mm)', 'Expected Searches']
        
        st.download_button(
            label="📥 Download Forecast Data (CSV)",
            data=display_df.to_csv(index=False),
            file_name=f"uber_eats_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
