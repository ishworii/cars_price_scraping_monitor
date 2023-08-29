from database.db_setup import init_db, get_db_session
from database.models import CarListing
from sqlalchemy import create_engine
from sqlalchemy import inspect
import json
from settings import *
from scrapers import iaai, utility

logger = utility.setup_logger("iaai_logger", "iaai.log")

engine = create_engine(DATABASE_URL)


def table_exists():
    """Check if the CarListing table exists in the database."""
    inspector = inspect(engine)
    return CarListing.__tablename__ in inspector.get_table_names()


def process_scraped_data(data):
    updated_listings = []
    new_listings = []

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

            if not listing:
                logger.info(
                    f"Adding {item['year_make_model']} from {item['source']} to db"
                )
                item["old_price"] = 0
                new_entry = CarListing(**item)
                session.add(new_entry)
                new_listings.append(item)
            else:
                old_price = listing.buy_now_price
                new_price = float(item["buy_now_price"])

                # Update all attributes, even if they haven't changed
                for key, value in item.items():
                    setattr(listing, key, value)

                # Special handling for price changes
                if old_price != new_price:
                    updated_listings.append(
                        {
                            "thumbnail": listing.thumbnail,
                            "source": listing.source,
                            "year": listing.year,
                            "make": listing.make,
                            "model": listing.model,
                            "buy_now_price": new_price,
                            "old_price": old_price,
                            "location": listing.location,
                            "damage": listing.damage,
                            "title": listing.title,
                            "loss": listing.loss,
                            "details": listing.details,
                        }
                    )
                    logger.info(f"Updating db with new price")

            session.commit()

    # Email for new listings
    if new_listings:
        new_listings_content = utility.email_template(new_listings, "iaai", "new")
        utility.send_email(
            subject="New Listings IAAI",
            message=new_listings_content,
            recipient_email=SENDER_EMAIL,
            sender_email=SENDER_EMAIL,
            sender_password=SENDER_PASSWORD,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            logger=logger,
        )

    # Email for price updates
    if updated_listings:
        updated_prices_content = utility.email_template(
            updated_listings, "iaii", "update"
        )
        utility.send_email(
            subject="Price Updates IAII",
            message=updated_prices_content,
            recipient_email=SENDER_EMAIL,
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

    proxy_server = utility.get_random_proxy(PROXY_LIST, logger)
    # scraped_data = iaai.extract_all_data(
    #     url=IAAI_URL, headless=True, proxy_server=proxy_server
    # )
    # with open("iaai_scraped.json", "w") as file:
    #     json.dump(scraped_data, file)
    with open("iaai_scraped.json", "r") as file:
        scraped_data = json.load(file)

    process_scraped_data(scraped_data)


if __name__ == "__main__":
    main()
