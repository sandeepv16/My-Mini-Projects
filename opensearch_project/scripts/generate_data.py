import json
import random
from faker import Faker
import uuid
from datetime import datetime, timedelta
import os

# Initialize Faker
fake = Faker()

def generate_product():
    """Generate a random product"""
    # Define categories and brands
    categories = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Sports", "Beauty"]
    electronics_brands = ["Samsung", "Apple", "Sony", "LG", "Dell", "HP", "Asus"]
    clothing_brands = ["Nike", "Adidas", "H&M", "Zara", "Levis", "Gap", "Uniqlo"]
    home_brands = ["IKEA", "Crate & Barrel", "West Elm", "Pottery Barn", "Wayfair"]
    book_publishers = ["Penguin", "HarperCollins", "Random House", "Scholastic", "Simon & Schuster"]
    sports_brands = ["Nike", "Adidas", "Under Armour", "Puma", "Reebok", "Wilson", "Spalding"]
    beauty_brands = ["L'Oreal", "Maybelline", "MAC", "Estee Lauder", "Clinique", "Neutrogena"]

    # Select a random category
    category = random.choice(categories)

    # Select a brand based on the category
    if category == "Electronics":
        brand = random.choice(electronics_brands)
        name = f"{brand} {fake.word().title()} {random.choice(['Pro', 'Ultra', 'Max', 'Lite', ''])}"
        description = fake.paragraph(nb_sentences=4) + f"\n\nThis premium {category.lower()} product from {brand} offers high quality and performance."
        price = round(random.uniform(100, 2000), 2)
    elif category == "Clothing":
        brand = random.choice(clothing_brands)
        clothing_items = ["Shirt", "Pants", "Jacket", "Dress", "Socks", "Hat", "Sweater"]
        name = f"{brand} {random.choice(clothing_items)} {fake.color_name().title()}"
        description = fake.paragraph(nb_sentences=3) + f"\n\nA stylish {category.lower()} item from {brand}."
        price = round(random.uniform(15, 150), 2)
    elif category == "Home & Kitchen":
        brand = random.choice(home_brands)
        home_items = ["Chair", "Table", "Lamp", "Rug", "Sofa", "Bed", "Desk", "Cabinet"]
        name = f"{brand} {random.choice(home_items)} {fake.word().title()}"
        description = fake.paragraph(nb_sentences=3) + f"\n\nBeautiful {category.lower()} item for your home by {brand}."
        price = round(random.uniform(40, 800), 2)
    elif category == "Books":
        brand = random.choice(book_publishers)
        name = fake.catch_phrase()
        description = fake.paragraph(nb_sentences=5) + f"\n\nPublished by {brand}."
        price = round(random.uniform(5, 35), 2)
    elif category == "Sports":
        brand = random.choice(sports_brands)
        sports_items = ["Ball", "Racket", "Shoes", "Jersey", "Gloves", "Helmet", "Bat"]
        name = f"{brand} {random.choice(sports_items)} {fake.word().title()}"
        description = fake.paragraph(nb_sentences=3) + f"\n\nQuality sports equipment from {brand}."
        price = round(random.uniform(20, 200), 2)
    else:  # Beauty
        brand = random.choice(beauty_brands)
        beauty_items = ["Lipstick", "Foundation", "Mascara", "Cream", "Serum", "Shampoo"]
        name = f"{brand} {random.choice(beauty_items)} {fake.word().title()}"
        description = fake.paragraph(nb_sentences=3) + f"\n\nPremium beauty product by {brand}."
        price = round(random.uniform(10, 80), 2)

    # Generate random date within the last year
    created_at = (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()

    # Create the product
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "brand": brand,
        "in_stock": random.random() > 0.2,  # 80% chance of being in stock
        "created_at": created_at
    }

def generate_products(count=200):
    """Generate a list of random products"""
    return [generate_product() for _ in range(count)]

def save_to_file(products, filename='data/product_data.json'):
    """Save generated products to a JSON file"""
    # Create the data directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w') as f:
        json.dump(products, f, indent=2)

    print(f"Generated {len(products)} products and saved to {filename}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate sample product data')
    parser.add_argument('--count', type=int, default=200, help='Number of products to generate')
    parser.add_argument('--output', type=str, default='data/product_data.json', help='Output file path')

    args = parser.parse_args()

    products = generate_products(args.count)
    save_to_file(products, args.output)
