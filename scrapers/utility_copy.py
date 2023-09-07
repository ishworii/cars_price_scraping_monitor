from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import smtplib
from email.message import EmailMessage
import random
import logging


# define some universal funtions for extraction
def xpath_finder(driver, xpath, many=False):
    if many:
        try:
            element = driver.find_elements(By.XPATH, xpath)
            return element
        except NoSuchElementException:
            return None
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element
    except NoSuchElementException:
        return None


def css_finder(driver, css, many=False):
    if many:
        try:
            element = driver.find_elements(By.CSS_SELECTOR, css)
            return element
        except NoSuchElementException:
            return None
    try:
        element = driver.find_element(By.CSS_SELECTOR, css)
        return element
    except NoSuchElementException:
        return None


def scroll_down_page(driver, speed):
    current_scroll_position, new_height = 0, 1
    while current_scroll_position <= new_height:
        current_scroll_position += speed
        driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
        new_height = driver.execute_script("return document.body.scrollHeight")

def get_row_html(listings):
    # Sort the listings by year in descending order
    sorted_listings = sorted(listings, key=lambda l: (l['model'].split()[0], -int(l['year'])))

    rows_html = ""
    for listing in sorted_listings:
        row_html = f"""
        <td><a href="{listing['details']}"><img src="{listing['thumbnail']}" width="100"></a></td>
        <td><strong>{listing['year']}</strong></td>
        <td><strong>{listing['make']}</strong></td>
        <td><strong>{listing['model']}</strong></td>
        <td><strong>${listing['buy_now_price']}</strong></td>
        <td>${listing.get('old_price', 'N/A')}</td>
        <td>{listing['location']}</td>
        <td>{listing['damage']}</td>
        <td>{listing.get('loss', 'N/A')}</td>
        <td>{listing['title']}</td>
        """

        rows_html += f"<tr>{row_html}</tr>"

    return rows_html

def email_template(listings):
    # Get the rows
    rows_html = get_row_html(listings)

    # Standard table header
    header_html = """
    <tr>
        <th>Thumbnail</th>
        <th>Year</th>
        <th>Make</th>
        <th>Model</th>
        <th>Buy Now Price</th>
        <th>Old Price</th>
        <th>Location</th>
        <th>Damage</th>
        <th>Loss</th>
        <th>Title</th>
    </tr>
    """

    email_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            border: 1px solid #dddddd;
        }}
        th, td {{
            border: 1px solid #dddddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
    </style>
    </head>
    <body>
    <table>
        {header_html}
        {rows_html}
    </table>
    </body>
    </html>
    """

    return email_html


def send_email(
    subject,
    message,
    recipient_email,
    sender_email,
    sender_password,
    smtp_server,
    smtp_port,
    logger,
):
    """
    Sends an email.

    :param subject: The email subject
    :param message: The email content
    :param recipient_email: The recipient's email address
    """
    msg = EmailMessage()
    msg.set_content(message, subtype="html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            logger.info(f"Email sent successfully with subject {subject}")

    except Exception as e:
        logger.info(f"Failed to send email: {e}")


def get_random_proxy(proxy_list, logger):
    if not proxy_list:
        logger.warning(f"The proxy server list is empty,not using any proxy")
        return None

    proxy_server = random.choice(proxy_list)
    logger.info(f"Select random proxy server {proxy_server} for this run...")
    return proxy_server


def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    # Prevent adding multiple handlers
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(level)

    return logger
