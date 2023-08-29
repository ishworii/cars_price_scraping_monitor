from time import sleep
from .utility import *
import undetected_chromedriver as uc


logger = setup_logger("copart_logger", "copart.log")


def change_results_to_100(driver):
    button = xpath_finder(driver, "//span[@id='pr_id_6_label']")
    if not button:
        logger.warning("Button to change the items per page to 100 not found...")
        return
    button.click()

    limit_button = xpath_finder(driver, "//li[@aria-label=100]")
    if not limit_button:
        logger.warning("100 not found in the dropdown list...")
    limit_button.click()
    sleep(2)


def extract_details_from_page(driver):
    data = []
    # find each row
    rows = xpath_finder(
        driver, "//tr[@class='p-element p-selectable-row ng-star-inserted']", many=True
    )
    if not rows:
        logger.warning("Data rows not found...")
        return

    for each_row in rows:
        year_make_model = css_finder(
            each_row, "span.search_result_lot_detail.ng-star-inserted"
        )
        if not year_make_model:
            logger.warning("Year Make Model not found...")
            year_make_model = ""
            year, make, model = "", "", ""
        else:
            year_make_model = year_make_model.text.strip()
            year_make_model_list = year_make_model.split(" ")
            year = year_make_model_list[0]
            make = year_make_model_list[1]
            model = " ".join(year_make_model_list[2::])

        damage = css_finder(
            each_row, ".search_result_condition_block.ng-star-inserted .p-mt-2 span"
        )
        if not damage:
            logger.warning("Damage not found...")
            damage = ""
        else:
            damage = damage.text.strip()

        price = css_finder(
            each_row, "span.button-buyitnow.p-d-flex.p-align-center span.currencyAmount"
        )
        if not price:
            logger.warning("Price not found...")
            price = ""
        else:
            price = price.text.strip()
            price = price.split("$")[-1]

        location = css_finder(
            each_row,
            "span.search_result_yard_location_label.blue-heading.p-d-flex.p-cursor-pointer.p-bold",
        )
        if not location:
            logger.warning("Location not found...")
            location = ""
        else:
            location = location.text.strip()

        title = css_finder(each_row, "span[title]")
        if not title:
            logger.warning("Title not found...")
            title = ""
        else:
            title = title.text.strip()

        thumbnail = css_finder(each_row, "img[alt='Lot Image']")
        if not thumbnail:
            logger.warning("Thumbnail not found...")
            thumbnail = ""
        else:
            thumbnail = thumbnail.get_attribute("src")

        tmp = {
            "year_make_model": year_make_model,
            "year": year,
            "make": make,
            "model": model,
            "damage": damage,
            "buy_now_price": price,
            "location": location,
            "title": title,
            "thumbnail": thumbnail,
            "source": "copart",
            "loss": "",
        }
        data.append(tmp)
    return data


def number_of_vehicles(driver):
    results_header = xpath_finder(driver, "//search-results-header//span[@class]")
    results = 0
    if results_header:
        results = results_header.text.strip()
    return results


def extract_all_data(url, headless=False, proxy_server=None):
    # add default chrome options
    options = uc.ChromeOptions()

    # # Avoiding detection

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if headless:
        # Set up in headless mode
        options.add_argument("--headless")

    if proxy_server:
        options.add_argument(f"--proxy-server={proxy_server}")

    driver = uc.Chrome(options=options)
    driver.get(url)
    sleep(10)

    res = []
    current_count = 1
    total_results = number_of_vehicles(driver)
    logger.info(f"For this run {total_results} number of vehicles found...")
    change_results_to_100(driver)
    while True:
        scroll_down_page(driver, speed=35)
        data = extract_details_from_page(driver)
        if not data:
            logger.warning("Not data found on the website...")
        else:
            logger.info(f"Extracted data from {current_count} page...")
            res.extend(data)
        current_count += 1
        # check if next button is clickable, if it is click else break
        next_button = css_finder(
            driver, "button.p-paginator-next.p-paginator-element.p-link"
        )
        if next_button:
            if next_button.get_attribute("disabled"):
                break
            else:
                driver.execute_script("arguments[0].click();", next_button)

        sleep(3)
    driver.quit()
    return res
