from database.db_setup import get_db_session, init_db
from database.db_setup import init_db, get_db_session
from database.models import CarListing
from sqlalchemy import create_engine
from sqlalchemy import inspect
from settings import *
from scrapers import copart, utility

logger = utility.setup_logger("copart_logger", "copart.log")


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
                    location=item["location"],
                    title=item["title"],
                    thumbnail=item["thumbnail"],
                )
                .first()
            )

            # If listing doesn't exist, add to DB and store for email notification
            if not listing:
                logger.info(
                    f"Adding {item['year_make_model']} from {item['source']} to db"
                )
                item["old_price"] = 0
                new_entry = CarListing(**item)
                session.add(new_entry)
                session.commit()

                new_listings.append(item)

            else:
                logger.info(
                    f"entry found for {item['year_make_model']} from {item['source']},checking for price change."
                )
                # If the price has changed, store the data for email notification
                if listing.buy_now_price != float(item["buy_now_price"]):
                    logger.info(f"Updating db with new price")
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
                            "title": listing.title,
                        }
                    )

                    listing.price = float(item["buy_now_price"])

                # Update the other columns regardless of price change
                logger.info(f"Updating db with newly scraped data")
                listing.year = item["year"]
                listing.make = item["make"]
                listing.model = item["model"]
                listing.damage = item["damage"]
                listing.location = item["location"]
                listing.title = item["title"]
                listing.thumbnail = item["thumbnail"]

                session.commit()

    # Email for new listings
    if new_listings:
        new_listings_content = utility.email_template(new_listings, "copart", "new")
        utility.send_email(
            subject="New Listings Copart",
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
            updated_listings, "copart", "update"
        )
        utility.send_email(
            subject="Price Updates Copart",
            message=updated_prices_content,
            recipient_email=SENDER_EMAIL,
            sender_email=SENDER_EMAIL,
            sender_password=SENDER_EMAIL,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            logger=logger,
        )


def main():
    if not table_exists():
        logger.info("Creating car_listing table...")
        init_db(logger)

    proxy_server = utility.get_random_proxy(PROXY_LIST, logger)
    scraped_copart = copart.extract_all_data(
        url=COPART_URL, headless=True, proxy_server=proxy_server
    )

    process_scraped_data(scraped_copart)


if __name__ == "__main__":
    main()
