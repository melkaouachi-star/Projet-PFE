"""Static catalogs used by the synthetic banking simulator."""
from __future__ import annotations

COUNTRY_CITIES = {
    "Morocco": [
        ("Casablanca", 33.5731, -7.5898),
        ("Rabat", 34.0209, -6.8416),
        ("Marrakesh", 31.6295, -7.9811),
        ("Fes", 34.0181, -5.0078),
        ("Tangier", 35.7595, -5.8340),
        ("Agadir", 30.4278, -9.5981),
    ],
    "United States": [
        ("New York", 40.7128, -74.0060),
        ("San Francisco", 37.7749, -122.4194),
        ("Chicago", 41.8781, -87.6298),
        ("Los Angeles", 34.0522, -118.2437),
        ("Miami", 25.7617, -80.1918),
        ("Dallas", 32.7767, -96.7970),
    ],
    "United Kingdom": [
        ("London", 51.5072, -0.1276),
        ("Manchester", 53.4808, -2.2426),
        ("Birmingham", 52.4862, -1.8904),
        ("Edinburgh", 55.9533, -3.1883),
    ],
    "France": [
        ("Paris", 48.8566, 2.3522),
        ("Lyon", 45.7640, 4.8357),
        ("Marseille", 43.2965, 5.3698),
        ("Toulouse", 43.6047, 1.4442),
    ],
    "Germany": [
        ("Berlin", 52.5200, 13.4050),
        ("Frankfurt", 50.1109, 8.6821),
        ("Munich", 48.1351, 11.5820),
        ("Hamburg", 53.5511, 9.9937),
    ],
    "Spain": [
        ("Madrid", 40.4168, -3.7038),
        ("Barcelona", 41.3874, 2.1686),
        ("Valencia", 39.4699, -0.3763),
        ("Seville", 37.3891, -5.9845),
    ],
    "Canada": [
        ("Toronto", 43.6532, -79.3832),
        ("Montreal", 45.5019, -73.5674),
        ("Vancouver", 49.2827, -123.1207),
        ("Calgary", 51.0447, -114.0719),
    ],
    "Brazil": [
        ("Sao Paulo", -23.5558, -46.6396),
        ("Rio de Janeiro", -22.9068, -43.1729),
        ("Brasilia", -15.7939, -47.8828),
        ("Salvador", -12.9777, -38.5016),
    ],
    "Nigeria": [
        ("Lagos", 6.5244, 3.3792),
        ("Abuja", 9.0765, 7.3986),
        ("Kano", 12.0022, 8.5920),
        ("Port Harcourt", 4.8156, 7.0498),
    ],
    "Russia": [
        ("Moscow", 55.7558, 37.6173),
        ("Saint Petersburg", 59.9311, 30.3609),
        ("Novosibirsk", 55.0084, 82.9357),
        ("Yekaterinburg", 56.8389, 60.6057),
    ],
    "China": [
        ("Shanghai", 31.2304, 121.4737),
        ("Shenzhen", 22.5431, 114.0579),
        ("Beijing", 39.9042, 116.4074),
        ("Guangzhou", 23.1291, 113.2644),
    ],
    "United Arab Emirates": [
        ("Dubai", 25.2048, 55.2708),
        ("Abu Dhabi", 24.4539, 54.3773),
        ("Sharjah", 25.3463, 55.4209),
    ],
    "Singapore": [
        ("Singapore", 1.3521, 103.8198),
    ],
    "Japan": [
        ("Tokyo", 35.6762, 139.6503),
        ("Osaka", 34.6937, 135.5023),
        ("Yokohama", 35.4437, 139.6380),
    ],
    "India": [
        ("Mumbai", 19.0760, 72.8777),
        ("Delhi", 28.7041, 77.1025),
        ("Bengaluru", 12.9716, 77.5946),
    ],
    "Australia": [
        ("Sydney", -33.8688, 151.2093),
        ("Melbourne", -37.8136, 144.9631),
        ("Brisbane", -27.4698, 153.0251),
    ],
    "South Africa": [
        ("Johannesburg", -26.2041, 28.0473),
        ("Cape Town", -33.9249, 18.4241),
        ("Durban", -29.8587, 31.0218),
    ],
    "Egypt": [
        ("Cairo", 30.0444, 31.2357),
        ("Alexandria", 31.2001, 29.9187),
        ("Giza", 30.0131, 31.2089),
    ],
    "Turkey": [
        ("Istanbul", 41.0082, 28.9784),
        ("Ankara", 39.9334, 32.8597),
        ("Izmir", 38.4237, 27.1428),
    ],
    "Italy": [
        ("Rome", 41.9028, 12.4964),
        ("Milan", 45.4642, 9.1900),
        ("Naples", 40.8518, 14.2681),
    ],
    "Netherlands": [
        ("Amsterdam", 52.3676, 4.9041),
        ("Rotterdam", 51.9244, 4.4777),
        ("The Hague", 52.0705, 4.3007),
    ],
    "Switzerland": [
        ("Zurich", 47.3769, 8.5417),
        ("Geneva", 46.2044, 6.1432),
        ("Basel", 47.5596, 7.5886),
    ],
    "Saudi Arabia": [
        ("Riyadh", 24.7136, 46.6753),
        ("Jeddah", 21.4858, 39.1925),
        ("Dammam", 26.4207, 50.0888),
    ],
    "Qatar": [
        ("Doha", 25.2854, 51.5310),
        ("Al Rayyan", 25.2919, 51.4244),
    ],
    "Mexico": [
        ("Mexico City", 19.4326, -99.1332),
        ("Guadalajara", 20.6597, -103.3496),
        ("Monterrey", 25.6866, -100.3161),
    ],
    "Argentina": [
        ("Buenos Aires", -34.6037, -58.3816),
        ("Cordoba", -31.4201, -64.1888),
        ("Rosario", -32.9442, -60.6505),
    ],
    "South Korea": [
        ("Seoul", 37.5665, 126.9780),
        ("Busan", 35.1796, 129.0756),
        ("Incheon", 37.4563, 126.7052),
    ],
    "Indonesia": [
        ("Jakarta", -6.2088, 106.8456),
        ("Surabaya", -7.2575, 112.7521),
        ("Bandung", -6.9175, 107.6191),
    ],
    "Malaysia": [
        ("Kuala Lumpur", 3.1390, 101.6869),
        ("George Town", 5.4141, 100.3288),
        ("Johor Bahru", 1.4927, 103.7414),
    ],
    "Thailand": [
        ("Bangkok", 13.7563, 100.5018),
        ("Chiang Mai", 18.7883, 98.9853),
        ("Phuket", 7.8804, 98.3923),
    ],
    "Kenya": [
        ("Nairobi", -1.2921, 36.8219),
        ("Mombasa", -4.0435, 39.6682),
        ("Kisumu", -0.0917, 34.7680),
    ],
    "Senegal": [
        ("Dakar", 14.7167, -17.4677),
        ("Thies", 14.7910, -16.9256),
        ("Saint-Louis", 16.0326, -16.4818),
    ],
    "Ivory Coast": [
        ("Abidjan", 5.3600, -4.0083),
        ("Yamoussoukro", 6.8276, -5.2893),
        ("Bouake", 7.6906, -5.0391),
    ],
    "Ghana": [
        ("Accra", 5.6037, -0.1870),
        ("Kumasi", 6.6666, -1.6163),
        ("Tamale", 9.4075, -0.8533),
    ],
    "Portugal": [
        ("Lisbon", 38.7223, -9.1393),
        ("Porto", 41.1579, -8.6291),
        ("Braga", 41.5454, -8.4265),
    ],
    "Belgium": [
        ("Brussels", 50.8503, 4.3517),
        ("Antwerp", 51.2194, 4.4025),
        ("Ghent", 51.0543, 3.7174),
    ],
}

CURRENCY_BY_COUNTRY = {
    "Morocco": "MAD",
    "United States": "USD",
    "United Kingdom": "GBP",
    "France": "EUR",
    "Germany": "EUR",
    "Spain": "EUR",
    "Canada": "CAD",
    "Brazil": "BRL",
    "Nigeria": "NGN",
    "Russia": "RUB",
    "China": "CNY",
    "United Arab Emirates": "AED",
    "Singapore": "SGD",
    "Japan": "JPY",
    "India": "INR",
    "Australia": "AUD",
    "South Africa": "ZAR",
    "Egypt": "EGP",
    "Turkey": "TRY",
    "Italy": "EUR",
    "Netherlands": "EUR",
    "Switzerland": "CHF",
    "Saudi Arabia": "SAR",
    "Qatar": "QAR",
    "Mexico": "MXN",
    "Argentina": "ARS",
    "South Korea": "KRW",
    "Indonesia": "IDR",
    "Malaysia": "MYR",
    "Thailand": "THB",
    "Kenya": "KES",
    "Senegal": "XOF",
    "Ivory Coast": "XOF",
    "Ghana": "GHS",
    "Portugal": "EUR",
    "Belgium": "EUR",
}

MERCHANTS = {
    "Groceries": ["Carrefour Market", "Marjane", "Whole Foods", "Tesco Express"],
    "Restaurant": ["Le Comptoir", "Pret A Manger", "Shake Shack", "Nobu"],
    "Fuel": ["Shell", "TotalEnergies", "BP Station", "Afriquia"],
    "Electronics": ["Apple Store", "MediaMarkt", "Best Buy", "Fnac"],
    "Travel": ["Booking.com", "Royal Air Maroc", "Delta Airlines", "Eurostar"],
    "Luxury Goods": ["Cartier", "Louis Vuitton", "Rolex Boutique", "Gucci"],
    "Crypto Exchange": ["CoinBridge", "BitNova", "Atlas Crypto"],
    "Gambling": ["LuckySpin Casino", "FastOdds", "BetStorm"],
    "Gift Cards": ["GiftHub", "CardMall", "VoucherNet"],
    "ATM Withdrawal": ["Bank ATM", "Airport ATM", "Metro ATM"],
    "Healthcare": ["City Clinic", "PharmaPlus", "HealthCare One"],
    "Utilities": ["Orange", "Lydec", "Vodafone", "EDF"],
}

BEHAVIOR_PATTERNS = {
    "daily_retail": ["Groceries", "Restaurant", "Fuel", "Utilities"],
    "digital_native": ["Electronics", "Restaurant", "Travel", "Crypto Exchange"],
    "travel_heavy": ["Travel", "Restaurant", "Luxury Goods", "Fuel"],
    "family_household": ["Groceries", "Healthcare", "Utilities", "Fuel"],
    "business_owner": ["Travel", "Electronics", "Restaurant", "ATM Withdrawal"],
    "fraudster_profile": ["Gift Cards", "Crypto Exchange", "Gambling", "Luxury Goods"],
}

FIRST_NAMES = [
    "Adam", "Amina", "Amir", "Aya", "Daniel", "Elena", "Fatima", "Hassan",
    "Imane", "John", "Leila", "Lina", "Maria", "Mehdi", "Nadia", "Noah",
    "Omar", "Sara", "Sofia", "Youssef",
]

LAST_NAMES = [
    "Alaoui", "Bennani", "Brown", "Cohen", "Diallo", "Dubois", "El Fassi",
    "Garcia", "Johnson", "Khan", "Martin", "Nguyen", "Patel", "Rossi",
    "Smith", "Taylor", "Williams", "Zhang",
]

BROWSERS = ["Chrome", "Safari", "Edge", "Firefox", "Mobile Safari", "Samsung Internet"]
OPERATING_SYSTEMS = ["Windows", "macOS", "iOS", "Android", "Linux"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "Mobile Wallet", "Bank Transfer", "Virtual Card"]
CARD_TYPES = ["Visa Credit", "Visa Debit", "Mastercard Credit", "Mastercard Debit", "Prepaid", "Virtual"]

SCENARIOS = [
    "high_amount",
    "night_transaction",
    "foreign_country",
    "impossible_travel",
    "rapid_transaction_burst",
    "stolen_card_behavior",
    "bot_generated_fraud",
    "multiple_transactions_different_ips",
    "account_takeover",
    "anomalous_spending_pattern",
]

