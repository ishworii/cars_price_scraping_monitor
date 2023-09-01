from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import smtplib
from email.message import EmailMessage
import random
import logging


# Universal function to find elements by XPath with optional wait time
def xpath_finder(driver, xpath, many=False, wait_time=10):
    try:
        if many:
            elements = WebDriverWait(driver, wait_time).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
            return elements
        else:
            element = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
    except (NoSuchElementException, TimeoutException):
        return None


# Universal function to find elements by CSS Selector with optional wait time
def css_finder(driver, css, many=False, wait_time=10):
    try:
        if many:
            elements = WebDriverWait(driver, wait_time).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, css))
            )
            return elements
        else:
            element = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css))
            )
            return element
    except (NoSuchElementException, TimeoutException):
        return None


def scroll_down_page(driver, speed):
    current_scroll_position, new_height = 0, 1
    while current_scroll_position <= new_height:
        current_scroll_position += speed
        driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
        new_height = driver.execute_script("return document.body.scrollHeight")


def get_row_html(listing, source, status):
    if source == "iaii" and status == "new":
        row = f"""
        <tr>
            <a href="{listing['details']}"><img src="{listing['thumbnail']}" width="100"></a></td>
            <td>{listing['year']}</td>
            <td>{listing['make']}</td>
            <td>{listing['model']}</td>
            <td>${listing['buy_now_price']}</td>
            <td>{listing['location']}</td>
            <td>{listing['damage']}</td>
            <td>{listing['loss']}</td>
            <td>{listing['title']}</td>
        </tr>
        """

        table_html = f"""
        <tr>
            <th>Thumbnail</th>
            <th>Year</th>
            <th>Make</th>
            <th>Model</th>
            <th>Buy Now Price</th>
            <th>Location</th>
            <th>Damage</th>
            <th>Loss</th>
            <th>Title</th>
        </tr>
        """
    elif source == "iaii" and status == "update":
        row = f"""
        <tr>
            <a href="{listing['details']}"><img src="{listing['thumbnail']}" width="100"></a></td>
            <td>{listing['year']}</td>
            <td>{listing['make']}</td>
            <td>{listing['model']}</td>
            <td>${listing['buy_now_price']}</td>
            <td>${listing['old_price']}</td>
            <td>{listing['location']}</td>
            <td>{listing['damage']}</td>
            <td>{listing['loss']}</td>
            <td>{listing['title']}</td>
        </tr>
        """

        table_html = f"""
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

    elif source == "copart" and status == "new":
        row = f"""
        <tr>
            <a href="{listing['details']}"><img src="{listing['thumbnail']}" width="100"></a></td>
            <td>{listing['year']}</td>
            <td>{listing['make']}</td>
            <td>{listing['model']}</td>
            <td>${listing['buy_now_price']}</td>
            <td>{listing['location']}</td>
            <td>{listing['damage']}</td>
            <td>{listing['title']}</td>
        </tr>
        """
        table_html = f"""
        <tr>
            <th>Thumbnail</th>
            <th>Year</th>
            <th>Make</th>
            <th>Model</th>
            <th>Buy Now Price</th>
            <th>Location</th>
            <th>Damage</th>
            <th>Title</th>
        </tr>
        """
    else:
        row = f"""
        <tr>
            <td>
            <a href="{listing['details']}"><img src="{listing['thumbnail']}" width="100"></a></td>
            <td>{listing['year']}</td>
            <td>{listing['make']}</td>
            <td>{listing['model']}</td>
            <td>${listing['buy_now_price']}</td>
            <td>${listing['old_price']}</td>
            <td>{listing['location']}</td>
            <td>{listing['damage']}</td>
            <td>{listing['title']}</td>
        </tr>
        """
        table_html = f"""
        <tr>
            <th>Thumbnail</th>
            <th>Year</th>
            <th>Make</th>
            <th>Model</th>
            <th>Buy Now Price</th>
            <th>Old Price </th>
            <th>Location</th>
            <th>Damage</th>
            <th>Title</th>
        </tr>
        """
    return row, table_html


def email_template(listings, source, status):
    rows_html = ""

    for listing in listings:
        row, table_html = get_row_html(listing, source, status)
        rows_html += row

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
        {table_html}
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
