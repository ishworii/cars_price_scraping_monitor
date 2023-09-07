from database.db_setup import init_db, get_db_session
from database.models import CarListing
from sqlalchemy import create_engine
from sqlalchemy import inspect
import json
from settings import *
from scrapers import iaai_copy, utility_copy

logger = utility_copy.setup_logger("iaai_logger", "iaai.log")

engine = create_engine(DATABASE_URL)
logger.info("Engine created with DATABASE_URL.")


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
    logger.info("Processing scraped data.")
    # Define your special filters here (adjust as needed)
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

    with get_db_session() as session:
        logger.info("Opened DB session.")
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

            changed = False

            if not listing:
                changed = True
                logger.info(f"Adding {item['year_make_model']} from {item['source']} to db")
                item["old_price"] = 0
                new_entry = CarListing(**item)
                session.add(new_entry)
            else:
                old_price = listing.buy_now_price
                new_price = float(item["buy_now_price"])

                for key, value in item.items():
                    setattr(listing, key, value)

                if old_price != new_price:
                    changed = True
                    logger.info(f"Updating {item['year_make_model']} from {item['source']} with new price")
                    listing.old_price = old_price
                item["old_price"] = old_price

            if changed:
                for special_filter in special_filters:
                    if matches_filters(item, special_filter["criteria"]):
                        special_filter["listings"].append(item)

            session.commit()
            #logger.info("Finished processing items in scraped data.")

    for special_filter in special_filters:
        if special_filter["listings"]:
            logger.info(f"Preparing email for filter: {special_filter['name']}.")
            special_content = utility_copy.email_template(special_filter["listings"])
            utility_copy.send_email(
                subject=f"IAAI - {special_filter['name']}",
                message=special_content,
                recipient_email=RECIPIENT_EMAIL,
                sender_email=SENDER_EMAIL,
                sender_password=SENDER_PASSWORD,
                smtp_server=SMTP_SERVER,
                smtp_port=SMTP_PORT,
                logger=logger,
            )
            logger.info(f"Email sent for filter: {special_filter['name']}.")
    logger.info("Finished processing all scraped data.")

def main():
    logger.info("Main function started.")
    if not table_exists():
        logger.info("Creating car_listing table...")
        init_db(logger)

    proxy_server = utility_copy.get_random_proxy(PROXY_LIST, logger)
    logger.info(f"Using proxy: {proxy_server}")
    scraped_data = iaai_copy.extract_all_data(
        url=IAAI_URL, headless=True, proxy_server=proxy_server
    )
    logger.info(f"Scraped {len(scraped_data)} items from IAAI.")
    process_scraped_data(scraped_data)
    #logger.info("Main function finished.")

if __name__ == "__main__":
    #logger.info("Script started.")
    main()
    #logger.info("Script finished.")