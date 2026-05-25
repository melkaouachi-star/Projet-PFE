"""Static catalogs used by the synthetic banking simulator."""
from __future__ import annotations

COUNTRY_CITIES = {
    "Morocco": [
        ("Casablanca", 33.5731, -7.5898),
        ("Rabat", 34.0209, -6.8416),
        ("Marrakesh", 31.6295, -7.9811),
    ],
    "United States": [
        ("New York", 40.7128, -74.0060),
        ("San Francisco", 37.7749, -122.4194),
        ("Chicago", 41.8781, -87.6298),
    ],
    "United Kingdom": [
        ("London", 51.5072, -0.1276),
        ("Manchester", 53.4808, -2.2426),
    ],
    "France": [
        ("Paris", 48.8566, 2.3522),
        ("Lyon", 45.7640, 4.8357),
    ],
    "Germany": [
        ("Berlin", 52.5200, 13.4050),
        ("Frankfurt", 50.1109, 8.6821),
    ],
    "Spain": [
        ("Madrid", 40.4168, -3.7038),
        ("Barcelona", 41.3874, 2.1686),
    ],
    "Canada": [
        ("Toronto", 43.6532, -79.3832),
        ("Montreal", 45.5019, -73.5674),
    ],
    "Brazil": [
        ("Sao Paulo", -23.5558, -46.6396),
        ("Rio de Janeiro", -22.9068, -43.1729),
    ],
    "Nigeria": [
        ("Lagos", 6.5244, 3.3792),
        ("Abuja", 9.0765, 7.3986),
    ],
    "Russia": [
        ("Moscow", 55.7558, 37.6173),
        ("Saint Petersburg", 59.9311, 30.3609),
    ],
    "China": [
        ("Shanghai", 31.2304, 121.4737),
        ("Shenzhen", 22.5431, 114.0579),
    ],
    "United Arab Emirates": [
        ("Dubai", 25.2048, 55.2708),
        ("Abu Dhabi", 24.4539, 54.3773),
    ],
    "Singapore": [
        ("Singapore", 1.3521, 103.8198),
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

