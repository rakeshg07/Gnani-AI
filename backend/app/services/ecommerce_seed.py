"""MongoDB Seeder for Indian E-Commerce catalog, categories, demo customer, and demo orders."""
from datetime import datetime, timezone, timedelta
from typing import Any
from app.core.logging import logger
from app.core.security import hash_password


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def seed_ecommerce_data(db: Any) -> None:
    """Populates initial realistic e-commerce data into MongoDB if collections are empty."""
    if db.products.count_documents({}) > 0:
        logger.info("MongoDB catalog already populated. Skipping duplicate seeding.")
        return

    logger.info("Seeding initial VoiceIQ India e-commerce catalog and demo customer into MongoDB...")

    # 1. Categories
    categories = [
        {
            "_id": "electronics",
            "id": "electronics",
            "name": "Electronics & Gadgets",
            "slug": "electronics",
            "icon": "Smartphone",
            "description": "Smartphones, wireless earbuds, smartwatches, and audio tech",
        },
        {
            "_id": "appliances",
            "id": "appliances",
            "name": "Home & Kitchen",
            "slug": "appliances",
            "icon": "Home",
            "description": "Mixer grinders, air fryers, ceiling fans, and personal care",
        },
        {
            "_id": "fashion",
            "id": "fashion",
            "name": "Fashion & Apparel",
            "slug": "fashion",
            "icon": "Shirt",
            "description": "Ethnic wear, kurtis, casual shirts, and modern Indian apparel",
        },
        {
            "_id": "accessories",
            "id": "accessories",
            "name": "Bags & Watches",
            "slug": "accessories",
            "icon": "Watch",
            "description": "Premium wristwatches, backpacks, travel rucksacks, and sunglasses",
        },
    ]
    db.categories.insert_many(categories)

    # 2. Products
    products = [
        {
            "_id": "prod_boat_earbuds",
            "id": "prod_boat_earbuds",
            "title": "boAt Nirvana Ion ANC True Wireless Earbuds (Crystal Bionic Sound, 120H Playtime)",
            "slug": "boat-nirvana-ion-anc-earbuds",
            "category_id": "electronics",
            "price": 1999.0,
            "original_price": 4990.0,
            "rating": 4.5,
            "reviews_count": 1840,
            "stock": 45,
            "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
            "badge": "Bestseller",
            "description": "Experience ultimate acoustic immersion with Active Noise Cancellation up to 32dB, Hi-Fi DSP, 120 hours of total playback, and quad mics with ENx technology for crystal-clear calls.",
            "specifications": {
                "Battery Playtime": "120 Hours Total (24H per charge)",
                "Noise Cancellation": "Active Noise Cancellation up to 32dB",
                "Bluetooth Version": "v5.2",
                "Water Resistance": "IPX4 Sweat & Splash Resistant",
                "Charging": "Type-C Fast Charge (10 min = 5 hours)",
                "Warranty": "1 Year Manufacturer Warranty",
            },
            "return_window_days": 7,
            "is_featured": True,
            "created_at": get_utc_now(),
        },
        {
            "_id": "prod_oneplus_nord",
            "id": "prod_oneplus_nord",
            "title": "OnePlus Nord CE4 5G (Dark Chrome, 8GB RAM, 128GB Storage, 100W SuperVOOC)",
            "slug": "oneplus-nord-ce4-5g",
            "category_id": "electronics",
            "price": 24999.0,
            "original_price": 27999.0,
            "rating": 4.6,
            "reviews_count": 3210,
            "stock": 20,
            "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80",
            "badge": "Top Rated",
            "description": "Powered by Snapdragon 7 Gen 3, a massive 5500mAh battery with 100W ultra-fast charging, and a stunning 120Hz Fluid AMOLED display with Aqua Touch technology.",
            "specifications": {
                "Display": "6.7 inch FHD+ 120Hz AMOLED",
                "Processor": "Qualcomm Snapdragon 7 Gen 3 (4nm)",
                "Rear Camera": "50MP Sony LYT-600 with OIS + 8MP Ultra-wide",
                "Front Camera": "16MP Selfie",
                "Battery": "5500 mAh with 100W SuperVOOC adapter included",
                "OS": "OxygenOS 14 based on Android 14",
            },
            "return_window_days": 7,
            "is_featured": True,
            "created_at": get_utc_now(),
        },
        {
            "_id": "prod_noise_smartwatch",
            "id": "prod_noise_smartwatch",
            "title": "Noise ColorFit Pro 5 Smartwatch (1.85 AMOLED Display, BT Calling, SOS, Metallic Finish)",
            "slug": "noise-colorfit-pro-5-smartwatch",
            "category_id": "electronics",
            "price": 3499.0,
            "original_price": 7999.0,
            "rating": 4.4,
            "reviews_count": 940,
            "stock": 30,
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80",
            "badge": "Deal of the Day",
            "description": "Sleek AMOLED dial with 60Hz refresh rate, single-chip Bluetooth calling with TruSync, rapid SOS dialer, and 100+ sports modes with health suite monitoring.",
            "specifications": {
                "Display": "1.85 inch AMOLED (600 nits brightness)",
                "Calling": "Bluetooth Calling with built-in mic & speaker",
                "Battery Life": "Up to 7 Days typical usage",
                "Health Monitoring": "24/7 Heart Rate, SpO2, Sleep Tracker, Stress",
                "Water Protection": "IP68 Water & Dust Resistant",
            },
            "return_window_days": 7,
            "is_featured": False,
            "created_at": get_utc_now(),
        },
        {
            "_id": "prod_sony_headphones",
            "id": "prod_sony_headphones",
            "title": "Sony WH-1000XM4 Wireless Industry Leading Noise Canceling Headphones (Silver)",
            "slug": "sony-wh-1000xm4-headphones",
            "category_id": "electronics",
            "price": 19990.0,
            "original_price": 29990.0,
            "rating": 4.8,
            "reviews_count": 4580,
            "stock": 12,
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
            "badge": "Premium Choice",
            "description": "The gold standard of noise cancellation with Dual Noise Sensor technology, edge-AI music upscaling, Speak-to-Chat, and 30-hour battery life with quick charge.",
            "specifications": {
                "Noise Cancelling": "HD Noise Cancelling Processor QN1",
                "Battery Life": "30 Hours with ANC On",
                "Audio Codecs": "LDAC, AAC, SBC",
                "Multipoint": "Connects to two devices simultaneously",
                "Mic": "5 built-in microphones with advanced audio signal processing",
            },
            "return_window_days": 7,
            "is_featured": True,
            "created_at": get_utc_now(),
        },
        # Home & Kitchen
        {
            "_id": "prod_preethi_mixer",
            "id": "prod_preethi_mixer",
            "title": "Preethi Zodiac MG-218 750-Watt Mixer Grinder with 5 Jars (Includes Master Chef Plus Jar)",
            "slug": "preethi-zodiac-mixer-grinder",
            "category_id": "appliances",
            "price": 7899.0,
            "original_price": 11250.0,
            "rating": 4.5,
            "reviews_count": 1230,
            "stock": 15,
            "image_url": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=600&auto=format&fit=crop&q=80",
            "badge": "Kitchen Bestseller",
            "description": "India's beloved all-in-one kitchen robot: kneads atta in 1 minute, chops vegetables with precision, grates, slices, extracts citrus juice, and grinds traditional idli batter effortlessly.",
            "specifications": {
                "Motor Power": "750 Watts Vega W5 Motor with 5-year warranty",
                "Jars": "5 Jars (Master Chef+, 3-in-1 Insta Fresh, 1.5L Wet, 1.0L Dry, 0.5L Chutney)",
                "Safety": "Overload Protector and Tri-mate Nylon Couplers",
                "Blade Material": "Machine-ground Stainless Steel Blades",
            },
            "return_window_days": 10,
            "is_featured": True,
            "created_at": get_utc_now(),
        },
        {
            "_id": "prod_philips_airfryer",
            "id": "prod_philips_airfryer",
            "title": "Philips Digital Air Fryer HD9252/90 (90% Less Fat, Rapid Air Tech, 4.1L Capacity)",
            "slug": "philips-digital-air-fryer",
            "category_id": "appliances",
            "price": 8299.0,
            "original_price": 12995.0,
            "rating": 4.7,
            "reviews_count": 2150,
            "stock": 22,
            "image_url": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=600&auto=format&fit=crop&q=80",
            "badge": "Healthy Choice",
            "description": "Crispy on the outside, tender on the inside with Patented Rapid Air starfish design. Cook samosas, fries, paneer tikka, and cakes with up to 90% less oil.",
            "specifications": {
                "Capacity": "4.1 Litres (0.8 kg basket)",
                "Presets": "7 One-touch touchscreen presets",
                "Keep Warm": "Up to 30 minutes Keep Warm function",
                "Dishwasher Safe": "Removable QuickClean basket",
            },
            "return_window_days": 10,
            "is_featured": False,
            "created_at": get_utc_now(),
        },
        {
            "_id": "prod_havells_fan",
            "id": "prod_havells_fan",
            "title": "Havells Glaze 1200mm Decorative BLDC Ceiling Fan with Remote (Save 65% Electricity)",
            "slug": "havells-glaze-bldc-ceiling-fan",
            "category_id": "appliances",
            "price": 3199.0,
            "original_price": 5490.0,
            "rating": 4.3,
            "reviews_count": 520,
            "stock": 35,
            "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=600&auto=format&fit=crop&q=80",
            "badge": "Eco Friendly",
            "description": "Super energy-efficient BLDC motor consuming only 28W at peak speed. Elegant dual-tone trims, aerodynamic wide blades, and RF remote control.",
            "specifications": {
                "Sweep": "1200 mm (48 inch)",
                "Motor": "Eco-friendly BLDC Motor (28W)",
                "Air Delivery": "220 CMM",
                "Speed": "350 RPM",
                "Control": "Smart Remote with Timer and Sleep mode",
            },
            "return_window_days": 10,
            "is_featured": False,
            "created_at": get_utc_now(),
        },
        # Fashion & Apparel
        {
            "_id": "prod_festive_kurti",
            "id": "prod_festive_kurti",
            "title": "W for Woman Women Maroon Silk Blend Embroidered A-Line Festive Kurti with Dupatta",
            "slug": "w-woman-maroon-silk-festive-kurti",
            "category_id": "fashion",
            "price": 2299.0,
            "original_price": 4599.0,
            "rating": 4.4,
            "reviews_count": 670,
            "stock": 40,
            "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&auto=format&fit=crop&q=80",
            "badge": "Festive Trend",
            "description": "Graceful zari embroidery on rich chanderi silk blend fabric, paired with an organza printed dupatta. Perfect for festive celebrations, weddings, and family gatherings.",
            "specifications": {
                "Fabric": "Chanderi Silk Blend (Kurti) & Organza (Dupatta)",
                "Fit": "Regular A-Line Silhouette",
                "Length": "Calf Length (46 inches)",
                "Care": "Dry Clean Recommended",
                "Occasion": "Festive, Wedding Guest, Celebration",
            },
            "return_window_days": 14,
            "is_featured": True,
            "created_at": get_utc_now(),
        },
        {
            "_id": "prod_linen_shirt",
            "id": "prod_linen_shirt",
            "title": "Louis Philippe Men Regular Fit Pure Linen Casual Full-Sleeve Shirt (Sky Blue)",
            "slug": "louis-philippe-pure-linen-shirt",
            "category_id": "fashion",
            "price": 2799.0,
            "original_price": 3999.0,
            "rating": 4.6,
            "reviews_count": 810,
            "stock": 25,
            "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&auto=format&fit=crop&q=80",
            "badge": "Top Seller",
            "description": "Crafted from premium 100% French linen flax for unmatched breathability and a luxurious textured finish. Tailored with a smart semi-cutaway collar.",
            "specifications": {
                "Material": "100% Pure Flax Linen",
                "Sleeve": "Full Sleeve with adjustable barrel cuffs",
                "Collar": "Semi-Cutaway Collar",
                "Fit": "Classic Regular Fit",
            },
            "return_window_days": 14,
            "is_featured": False,
            "created_at": get_utc_now(),
        },
        # Accessories
        {
            "_id": "prod_titan_watch",
            "id": "prod_titan_watch",
            "title": "Titan Octane Analog Blue Dial Men Chronograph Watch (Stainless Steel Strap)",
            "slug": "titan-octane-chronograph-watch",
            "category_id": "accessories",
            "price": 7995.0,
            "original_price": 9995.0,
            "rating": 4.7,
            "reviews_count": 1450,
            "stock": 18,
            "image_url": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&auto=format&fit=crop&q=80",
            "badge": "Customer Favorite",
            "description": "Dynamic sunray blue chronograph dial with tachymeter scale, precision quartz movement, durable mineral glass, and solid stainless steel oyster bracelet.",
            "specifications": {
                "Case Diameter": "44 mm",
                "Water Resistance": "100 Meters (10 ATM)",
                "Glass": "Scratch-resistant Mineral Glass",
                "Movement": "Japanese Quartz Chronograph",
                "Warranty": "24 Months International Warranty",
            },
            "return_window_days": 7,
            "is_featured": True,
            "created_at": get_utc_now(),
        },
        {
            "_id": "prod_american_tourister",
            "id": "prod_american_tourister",
            "title": "American Tourister 32L Casual Laptop Backpack (3 Compartments, Water Repellent)",
            "slug": "american-tourister-laptop-backpack",
            "category_id": "accessories",
            "price": 1499.0,
            "original_price": 3100.0,
            "rating": 4.5,
            "reviews_count": 3890,
            "stock": 60,
            "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80",
            "badge": "Value Pick",
            "description": "Ergonomically designed for students and working professionals. Features dedicated 15.6-inch laptop cradle, rain cover pocket, mesh organizer, and Tractum suspension straps.",
            "specifications": {
                "Capacity": "32 Litres",
                "Laptop Compatibility": "Up to 15.6 inches",
                "Material": "Heavy-duty 600D Dobby Polyester",
                "Compartments": "3 Full Compartments + 1 Quick Access Front Pocket",
            },
            "return_window_days": 7,
            "is_featured": False,
            "created_at": get_utc_now(),
        },
    ]
    db.products.insert_many(products)

    # 3. Demo User / Customer
    demo_user = {
        "_id": "cust_demo_001",
        "id": "cust_demo_001",
        "name": "Rahul Sharma",
        "email": "demo@voiceiq.in",
        "phone": "+91 98450 12345",
        "password_hash": hash_password("VoiceIQ@2026"),
        "address_line": "Flat 402, Skyline Residency, 12th Main, Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
        "created_at": get_utc_now(),
    }
    db.users.update_one({"_id": demo_user["_id"]}, {"$set": demo_user}, upsert=True)
    db.customers.update_one({"_id": demo_user["_id"]}, {"$set": demo_user}, upsert=True)

    # 4. Demo Cart
    demo_cart = {
        "_id": "cart_demo_001",
        "id": "cart_demo_001",
        "customer_id": "cust_demo_001",
        "created_at": get_utc_now(),
        "updated_at": get_utc_now(),
        "items": [
            {
                "id": "item_cart_001",
                "product_id": "prod_american_tourister",
                "quantity": 1,
                "unit_price": 1499.0,
            }
        ],
    }
    db.carts.update_one({"_id": demo_cart["_id"]}, {"$set": demo_cart}, upsert=True)

    # 5. Realistic Demo Orders
    now = get_utc_now()
    two_days_ago = now - timedelta(days=2)

    order_1 = {
        "_id": "VIQ-89214",
        "id": "VIQ-89214",
        "customer_id": "cust_demo_001",
        "status": "shipped",
        "subtotal": 1999.0,
        "shipping_fee": 0.0,
        "tax_amount": 99.95,
        "total_amount": 2098.95,
        "payment_method": "UPI (Google Pay)",
        "payment_status": "completed",
        "shipping_address": {
            "name": "Rahul Sharma",
            "phone": "+91 98450 12345",
            "address_line": "Flat 402, Skyline Residency, 12th Main, Indiranagar",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560038",
        },
        "tracking_number": "DEL90182412IN",
        "carrier": "Delhivery Express",
        "expected_delivery": now + timedelta(days=1, hours=4),
        "tracking_events": [
            {
                "status": "ordered",
                "title": "Order Placed",
                "timestamp": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                "location": "Bengaluru Hub",
                "description": "Order confirmed and verified.",
            },
            {
                "status": "processing",
                "title": "Packed & Dispatched",
                "timestamp": (now - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M"),
                "location": "Hosur Fulfillment Center",
                "description": "Package handed over to logistics partner Delhivery.",
            },
            {
                "status": "shipped",
                "title": "In Transit to Destination Facility",
                "timestamp": (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
                "location": "Electronic City Sorting Hub",
                "description": "In transit. On track for on-time delivery.",
            },
        ],
        "created_at": now - timedelta(days=1),
        "items": [
            {
                "id": "item_ord_001",
                "order_id": "VIQ-89214",
                "product_id": "prod_boat_earbuds",
                "product_title": "boAt Nirvana Ion ANC True Wireless Earbuds",
                "product_image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
                "unit_price": 1999.0,
                "quantity": 1,
                "total_price": 1999.0,
            }
        ],
    }

    order_2 = {
        "_id": "VIQ-73910",
        "id": "VIQ-73910",
        "customer_id": "cust_demo_001",
        "status": "delivered",
        "subtotal": 7995.0,
        "shipping_fee": 0.0,
        "tax_amount": 399.75,
        "total_amount": 8394.75,
        "payment_method": "HDFC Credit Card (Simulated)",
        "payment_status": "completed",
        "shipping_address": {
            "name": "Rahul Sharma",
            "phone": "+91 98450 12345",
            "address_line": "Flat 402, Skyline Residency, 12th Main, Indiranagar",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560038",
        },
        "tracking_number": "BLU77491023IN",
        "carrier": "Blue Dart",
        "expected_delivery": two_days_ago,
        "delivered_at": two_days_ago,
        "tracking_events": [
            {
                "status": "ordered",
                "title": "Order Placed",
                "timestamp": (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M"),
                "location": "Mumbai Warehouse",
                "description": "Payment authorized.",
            },
            {
                "status": "shipped",
                "title": "Dispatched via Air",
                "timestamp": (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
                "location": "Kempegowda Int'l Airport Hub",
                "description": "Package reached local facility.",
            },
            {
                "status": "delivered",
                "title": "Delivered to Customer",
                "timestamp": two_days_ago.strftime("%Y-%m-%d %H:%M"),
                "location": "Indiranagar, Bengaluru",
                "description": "Package handed directly to customer Rahul Sharma.",
            },
        ],
        "created_at": now - timedelta(days=4),
        "items": [
            {
                "id": "item_ord_002",
                "order_id": "VIQ-73910",
                "product_id": "prod_titan_watch",
                "product_title": "Titan Octane Analog Blue Dial Men Chronograph Watch",
                "product_image": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&auto=format&fit=crop&q=80",
                "unit_price": 7995.0,
                "quantity": 1,
                "total_price": 7995.0,
            }
        ],
    }

    two_hours_ago = now - timedelta(hours=2)
    order_3 = {
        "_id": "VIQ-41052",
        "id": "VIQ-41052",
        "customer_id": "cust_demo_001",
        "status": "processing",
        "subtotal": 7899.0,
        "shipping_fee": 0.0,
        "tax_amount": 394.95,
        "total_amount": 8293.95,
        "payment_method": "UPI (PhonePe)",
        "payment_status": "completed",
        "shipping_address": {
            "name": "Rahul Sharma",
            "phone": "+91 98450 12345",
            "address_line": "Flat 402, Skyline Residency, 12th Main, Indiranagar",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560038",
        },
        "tracking_number": "EKP19283741IN",
        "carrier": "Ekart Logistics",
        "expected_delivery": now + timedelta(days=3),
        "tracking_events": [
            {
                "status": "ordered",
                "title": "Order Confirmed",
                "timestamp": two_hours_ago.strftime("%Y-%m-%d %H:%M"),
                "location": "Bengaluru Central Hub",
                "description": "Seller has received the order and is preparing the package.",
            }
        ],
        "created_at": two_hours_ago,
        "items": [
            {
                "id": "item_ord_003",
                "order_id": "VIQ-41052",
                "product_id": "prod_preethi_mixer",
                "product_title": "Preethi Zodiac MG-218 750-Watt Mixer Grinder with 5 Jars",
                "product_image": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=600&auto=format&fit=crop&q=80",
                "unit_price": 7899.0,
                "quantity": 1,
                "total_price": 7899.0,
            }
        ],
    }

    db.orders.update_one({"_id": order_1["_id"]}, {"$set": order_1}, upsert=True)
    db.orders.update_one({"_id": order_2["_id"]}, {"$set": order_2}, upsert=True)
    db.orders.update_one({"_id": order_3["_id"]}, {"$set": order_3}, upsert=True)

    logger.info("Successfully seeded VoiceIQ India MongoDB database (categories, products, demo user, orders).")
