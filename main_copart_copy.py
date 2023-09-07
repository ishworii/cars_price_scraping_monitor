from database.db_setup import get_db_session, init_db
from database.db_setup import init_db, get_db_session
from database.models import CarListing
from sqlalchemy import create_engine
from sqlalchemy import inspect
from settings import *
from scrapers import copart_copy, utility_copy
import json

logger = utility_copy.setup_logger("copart_logger", "copart.log")


engine = create_engine(DATABASE_URL)


def table_exists():
    """Check if the CarListing table exists in the database."""
    inspector = inspect(engine)
    return CarListing.__tablename__ in inspector.get_table_names()

def matches_filters(item, filters):
    for key, condition in filters.items():
        if key == 'custom':
            if not condition(item):
                return False
        else:
            if not condition(item.get(key, None)):
                return False
    return True

def process_scraped_data(data):
    # Define your special filters here
    special_filters = [
        {
            "name": "BMW 2013+ < $10,000",
            "criteria": {
                "make": lambda make: make == 'BMW',
                "year": lambda year: int(year) > 2013,
                "buy_now_price": lambda price: float(price) < 10000
            },
            "listings": []
        },
        {
            "name": "Audi 2012+ < $10,000",
            "criteria": {
                "make": lambda make: make == 'AUDI',
                "year": lambda year: int(year) > 2012,
                "buy_now_price": lambda price: float(price) < 10000
            },
            "listings": []
        },
        {
            "name": "VW 2012+ < $10,000",
            "criteria": {
                "make": lambda make: make == 'VOLKSWAGEN',
                "year": lambda year: int(year) > 2012,
                "buy_now_price": lambda price: float(price) < 10000
            },
            "listings": []
        },
        {
            "name": "MB 2010+ < $10,000",
            "criteria": {
                "make": lambda make: make == 'MERCEDES-BENZ',
                "year": lambda year: int(year) > 2010,
                "buy_now_price": lambda price: float(price) < 10000
            },
            "listings": []
        },
        {
            "name": "Porsche and Special",
            "criteria": {
                "custom": lambda item: (
                    item.get('make') in ['PORSCHE', 'LAMBORGHINI', 'FERRARI', 'MCLAREN']
                    or
                    item.get('model') in ['M3', 'M5', 'M6', 'EUROVAN', 'R8']
                ),
                "buy_now_price": lambda price: float(price) < 20000
            },
            "listings": []
        }
        # Add more filter dictionaries here as needed
    ]

    # Open a single session for all the database operations
    with get_db_session() as session:
        for item in data:
            listing = (
                session.query(CarListing)
                .filter_by(
                    year_make_model=item["year_make_model"],
                    source=item["source"],
                    damage=item["damage"],
                    location=item["location"],
                    title=item["title"],
                    thumbnail=item["thumbnail"],
                )
                .first()
            )

            changed = False  # Flag to track if this item should be added

            if not listing:
                changed = True  # New listing
                logger.info(
                    f"Adding {item['year_make_model']} from {item['source']} to db"
                )
                item["old_price"] = 0
                new_entry = CarListing(**item)
                session.add(new_entry)
            else:
                old_price = listing.buy_now_price
                new_price = float(item["buy_now_price"])

                # Update all attributes, even if they haven't changed
                for key, value in item.items():
                    setattr(listing, key, value)

                # Special handling for price changes
                if old_price != new_price:
                    changed = True  # Updated listing
                    logger.info(f"Updating {item['year_make_model']} from {item['source']} with new price")
                    listing.old_price = old_price  # Update the old_price attribute
                item["old_price"] = old_price  # Update the item dictionary with the old price
                    
            if changed:
                # Check listings against special filters
                for special_filter in special_filters:
                    if matches_filters(item, special_filter["criteria"]):
                        special_filter["listings"].append(item)

            session.commit()

    # Prepare and send emails for listings that match special filters
    for special_filter in special_filters:
        if special_filter["listings"]:
            special_content = utility_copy.email_template(special_filter["listings"])
            utility_copy.send_email(
                subject=f"Copart - {special_filter['name']}",
                message=special_content,
                recipient_email=RECIPIENT_EMAIL,
                sender_email=SENDER_EMAIL,
                sender_password=SENDER_PASSWORD,
                smtp_server=SMTP_SERVER,
                smtp_port=SMTP_PORT,
                logger=logger,
            )


def main():
    if not table_exists():
        logger.info("Creating car_listing table...")
        init_db(logger)

    proxy_server = utility_copy.get_random_proxy(PROXY_LIST, logger)
    scraped_copart = copart_copy.extract_all_data(
        url=COPART_URL, headless=True, proxy_server=proxy_server
    )
    process_scraped_data(scraped_copart)


if __name__ == "__main__":
    main()
