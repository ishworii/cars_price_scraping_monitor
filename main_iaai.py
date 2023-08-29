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

    for item in data:
        with get_db_session() as session:
            listing = (
                session.query(CarListing)
                .filter_by(
                    year_make_model=item["year_make_model"],
                    source=item["source"],
                    damage=item["damage"],
                    loss=item["loss"],
                    location=item["location"],
                    title=item["title"],
                    thumbnail=item["thumbnail"],
                )
                .first()
            )

            # If listing doesn't exist, add to DB and store for email notification
            if not listing:
                print(f"Adding {item['year_make_model']} from {item['source']} to db")
                item["old_price"] = 0
                new_entry = CarListing(**item)
                session.add(new_entry)
                session.commit()

                new_listings.append(item)

            else:
                print(
                    f"entry found for {item['year_make_model']} from {item['source']},checking for price change."
                )
                # If the price has changed, store the data for email notification
                if listing.buy_now_price != float(item["buy_now_price"]):
                    updated_listings.append(
                        {
                            "thumbnail": listing.thumbnail,
                            "source": listing.source,
                            "year": listing.year,
                            "make": listing.make,
                            "model": listing.model,
                            "buy_now_price": item["buy_now_price"],  # New price
                            "old_price": str(listing.buy_now_price),  # Old price
                            "location": listing.location,
                            "damage": listing.damage,
                            "loss": listing.loss,
                            "title": listing.title,
                        }
                    )

                    listing.price = float(item["buy_now_price"])

                # Update the other columns regardless of price change
                listing.year = item["year"]
                listing.make = item["make"]
                listing.model = item["model"]
                listing.damage = item["damage"]
                listing.location = item["location"]
                listing.title = item["title"]
                listing.loss = item["loss"]
                listing.thumbnail = item["thumbnail"]

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
    scraped_data = iaai.extract_all_data(
        url=IAAI_URL, headless=True, proxy_server=proxy_server
    )

    process_scraped_data(scraped_data)


if __name__ == "__main__":
    main()
