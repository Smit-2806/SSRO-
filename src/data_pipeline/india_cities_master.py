"""
india_cities_master.py
Single source of truth for all CPCB-monitored Indian cities.
All downstream pipelines import INDIA_CITIES from this module.
"""

INDIA_CITIES = [
    # --- NORTH INDIA ---
    {"city": "Delhi",           "state": "Delhi",               "zone": "North",       "lat": 28.6139, "lon": 77.2090},
    {"city": "Faridabad",       "state": "Haryana",             "zone": "North",       "lat": 28.4089, "lon": 77.3178},
    {"city": "Gurgaon",         "state": "Haryana",             "zone": "North",       "lat": 28.4595, "lon": 77.0266},
    {"city": "Noida",           "state": "Uttar Pradesh",       "zone": "North",       "lat": 28.5355, "lon": 77.3910},
    {"city": "Ghaziabad",       "state": "Uttar Pradesh",       "zone": "North",       "lat": 28.6692, "lon": 77.4538},
    {"city": "Lucknow",         "state": "Uttar Pradesh",       "zone": "North",       "lat": 26.8467, "lon": 80.9462},
    {"city": "Kanpur",          "state": "Uttar Pradesh",       "zone": "North",       "lat": 26.4499, "lon": 80.3319},
    {"city": "Agra",            "state": "Uttar Pradesh",       "zone": "North",       "lat": 27.1767, "lon": 78.0081},
    {"city": "Varanasi",        "state": "Uttar Pradesh",       "zone": "North",       "lat": 25.3176, "lon": 82.9739},
    {"city": "Allahabad",       "state": "Uttar Pradesh",       "zone": "North",       "lat": 25.4358, "lon": 81.8463},
    {"city": "Meerut",          "state": "Uttar Pradesh",       "zone": "North",       "lat": 28.9845, "lon": 77.7064},
    {"city": "Moradabad",       "state": "Uttar Pradesh",       "zone": "North",       "lat": 28.8386, "lon": 78.7733},
    {"city": "Bareilly",        "state": "Uttar Pradesh",       "zone": "North",       "lat": 28.3670, "lon": 79.4304},
    {"city": "Jodhpur",         "state": "Rajasthan",           "zone": "North",       "lat": 26.2389, "lon": 73.0243},
    {"city": "Jaipur",          "state": "Rajasthan",           "zone": "North",       "lat": 26.9124, "lon": 75.7873},
    {"city": "Udaipur",         "state": "Rajasthan",           "zone": "North",       "lat": 24.5854, "lon": 73.7125},
    {"city": "Kota",            "state": "Rajasthan",           "zone": "North",       "lat": 25.2138, "lon": 75.8648},
    {"city": "Ajmer",           "state": "Rajasthan",           "zone": "North",       "lat": 26.4499, "lon": 74.6399},
    {"city": "Chandigarh",      "state": "Chandigarh",          "zone": "North",       "lat": 30.7333, "lon": 76.7794},
    {"city": "Amritsar",        "state": "Punjab",              "zone": "North",       "lat": 31.6340, "lon": 74.8723},
    {"city": "Ludhiana",        "state": "Punjab",              "zone": "North",       "lat": 30.9010, "lon": 75.8573},
    {"city": "Patiala",         "state": "Punjab",              "zone": "North",       "lat": 30.3398, "lon": 76.3869},
    {"city": "Jalandhar",       "state": "Punjab",              "zone": "North",       "lat": 31.3260, "lon": 75.5762},
    {"city": "Bathinda",        "state": "Punjab",              "zone": "North",       "lat": 30.2110, "lon": 74.9455},
    {"city": "Ambala",          "state": "Haryana",             "zone": "North",       "lat": 30.3752, "lon": 76.7821},
    {"city": "Hisar",           "state": "Haryana",             "zone": "North",       "lat": 29.1492, "lon": 75.7217},
    {"city": "Rohtak",          "state": "Haryana",             "zone": "North",       "lat": 28.8955, "lon": 76.6066},
    {"city": "Panipat",         "state": "Haryana",             "zone": "North",       "lat": 29.3909, "lon": 76.9635},
    {"city": "Dehradun",        "state": "Uttarakhand",         "zone": "North",       "lat": 30.3165, "lon": 78.0322},
    {"city": "Haridwar",        "state": "Uttarakhand",         "zone": "North",       "lat": 29.9457, "lon": 78.1642},
    # --- EAST INDIA ---
    {"city": "Kolkata",         "state": "West Bengal",         "zone": "East",        "lat": 22.5726, "lon": 88.3639},
    {"city": "Howrah",          "state": "West Bengal",         "zone": "East",        "lat": 22.5958, "lon": 88.2636},
    {"city": "Asansol",         "state": "West Bengal",         "zone": "East",        "lat": 23.6888, "lon": 86.9661},
    {"city": "Durgapur",        "state": "West Bengal",         "zone": "East",        "lat": 23.5204, "lon": 87.3119},
    {"city": "Patna",           "state": "Bihar",               "zone": "East",        "lat": 25.5941, "lon": 85.1376},
    {"city": "Gaya",            "state": "Bihar",               "zone": "East",        "lat": 24.7955, "lon": 85.0002},
    {"city": "Muzaffarpur",     "state": "Bihar",               "zone": "East",        "lat": 26.1209, "lon": 85.3647},
    {"city": "Bhubaneswar",     "state": "Odisha",              "zone": "East",        "lat": 20.2961, "lon": 85.8245},
    {"city": "Rourkela",        "state": "Odisha",              "zone": "East",        "lat": 22.2604, "lon": 84.8536},
    {"city": "Talcher",         "state": "Odisha",              "zone": "East",        "lat": 20.9503, "lon": 85.2274},
    {"city": "Ranchi",          "state": "Jharkhand",           "zone": "East",        "lat": 23.3441, "lon": 85.3096},
    {"city": "Jamshedpur",      "state": "Jharkhand",           "zone": "East",        "lat": 22.8046, "lon": 86.2029},
    {"city": "Dhanbad",         "state": "Jharkhand",           "zone": "East",        "lat": 23.7957, "lon": 86.4304},
    {"city": "Guwahati",        "state": "Assam",               "zone": "East",        "lat": 26.1445, "lon": 91.7362},
    # --- WEST INDIA ---
    {"city": "Mumbai",          "state": "Maharashtra",         "zone": "West",        "lat": 19.0760, "lon": 72.8777},
    {"city": "Pune",            "state": "Maharashtra",         "zone": "West",        "lat": 18.5204, "lon": 73.8567},
    {"city": "Nagpur",          "state": "Maharashtra",         "zone": "West",        "lat": 21.1458, "lon": 79.0882},
    {"city": "Nashik",          "state": "Maharashtra",         "zone": "West",        "lat": 19.9975, "lon": 73.7898},
    {"city": "Aurangabad",      "state": "Maharashtra",         "zone": "West",        "lat": 19.8762, "lon": 75.3433},
    {"city": "Solapur",         "state": "Maharashtra",         "zone": "West",        "lat": 17.6805, "lon": 75.9064},
    {"city": "Kolhapur",        "state": "Maharashtra",         "zone": "West",        "lat": 16.7050, "lon": 74.2433},
    {"city": "Navi Mumbai",     "state": "Maharashtra",         "zone": "West",        "lat": 19.0330, "lon": 73.0297},
    {"city": "Ahmedabad",       "state": "Gujarat",             "zone": "West",        "lat": 23.0225, "lon": 72.5714},
    {"city": "Surat",           "state": "Gujarat",             "zone": "West",        "lat": 21.1702, "lon": 72.8311},
    {"city": "Vadodara",        "state": "Gujarat",             "zone": "West",        "lat": 22.3072, "lon": 73.1812},
    {"city": "Rajkot",          "state": "Gujarat",             "zone": "West",        "lat": 22.3039, "lon": 70.8022},
    {"city": "Gandhinagar",     "state": "Gujarat",             "zone": "West",        "lat": 23.2156, "lon": 72.6369},
    {"city": "Bhopal",          "state": "Madhya Pradesh",      "zone": "West",        "lat": 23.2599, "lon": 77.4126},
    {"city": "Indore",          "state": "Madhya Pradesh",      "zone": "West",        "lat": 22.7196, "lon": 75.8577},
    {"city": "Jabalpur",        "state": "Madhya Pradesh",      "zone": "West",        "lat": 23.1815, "lon": 79.9864},
    {"city": "Gwalior",         "state": "Madhya Pradesh",      "zone": "West",        "lat": 26.2183, "lon": 78.1828},
    {"city": "Raipur",          "state": "Chhattisgarh",        "zone": "West",        "lat": 21.2514, "lon": 81.6296},
    {"city": "Bilaspur",        "state": "Chhattisgarh",        "zone": "West",        "lat": 22.0796, "lon": 82.1391},
    {"city": "Korba",           "state": "Chhattisgarh",        "zone": "West",        "lat": 22.3595, "lon": 82.7501},
    # --- SOUTH INDIA ---
    {"city": "Chennai",         "state": "Tamil Nadu",          "zone": "South",       "lat": 13.0827, "lon": 80.2707},
    {"city": "Coimbatore",      "state": "Tamil Nadu",          "zone": "South",       "lat": 11.0168, "lon": 76.9558},
    {"city": "Madurai",         "state": "Tamil Nadu",          "zone": "South",       "lat": 9.9252,  "lon": 78.1198},
    {"city": "Tiruchirappalli", "state": "Tamil Nadu",          "zone": "South",       "lat": 10.7905, "lon": 78.7047},
    {"city": "Salem",           "state": "Tamil Nadu",          "zone": "South",       "lat": 11.6643, "lon": 78.1460},
    {"city": "Tiruppur",        "state": "Tamil Nadu",          "zone": "South",       "lat": 11.1085, "lon": 77.3411},
    {"city": "Bangalore",       "state": "Karnataka",           "zone": "South",       "lat": 12.9716, "lon": 77.5946},
    {"city": "Mysore",          "state": "Karnataka",           "zone": "South",       "lat": 12.2958, "lon": 76.6394},
    {"city": "Hubli-Dharwad",   "state": "Karnataka",           "zone": "South",       "lat": 15.3647, "lon": 75.1240},
    {"city": "Mangalore",       "state": "Karnataka",           "zone": "South",       "lat": 12.9141, "lon": 74.8560},
    {"city": "Belagavi",        "state": "Karnataka",           "zone": "South",       "lat": 15.8497, "lon": 74.4977},
    {"city": "Hyderabad",       "state": "Telangana",           "zone": "South",       "lat": 17.3850, "lon": 78.4867},
    {"city": "Warangal",        "state": "Telangana",           "zone": "South",       "lat": 17.9689, "lon": 79.5941},
    {"city": "Visakhapatnam",   "state": "Andhra Pradesh",      "zone": "South",       "lat": 17.6868, "lon": 83.2185},
    {"city": "Vijayawada",      "state": "Andhra Pradesh",      "zone": "South",       "lat": 16.5062, "lon": 80.6480},
    {"city": "Guntur",          "state": "Andhra Pradesh",      "zone": "South",       "lat": 16.3067, "lon": 80.4365},
    {"city": "Kochi",           "state": "Kerala",              "zone": "South",       "lat": 9.9312,  "lon": 76.2673},
    {"city": "Thiruvananthapuram", "state": "Kerala",           "zone": "South",       "lat": 8.5241,  "lon": 76.9366},
    {"city": "Kozhikode",       "state": "Kerala",              "zone": "South",       "lat": 11.2588, "lon": 75.7804},
]

# Quick lookup helpers
CITY_COORD_MAP = {c["city"]: (c["lat"], c["lon"]) for c in INDIA_CITIES}
CITY_NAMES = [c["city"] for c in INDIA_CITIES]

# Legacy 5-city subset (for backward compatibility checks)
LEGACY_CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Hyderabad"]

if __name__ == "__main__":
    import pandas as pd
    df = pd.DataFrame(INDIA_CITIES)
    print(f"Total cities: {len(df)}")
    print(df.groupby("zone")["city"].count().to_string())
    print("\nSample (first 5):")
    print(df.head().to_string())
