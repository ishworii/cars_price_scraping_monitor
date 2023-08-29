from time import sleep
import undetected_chromedriver as uc
import re
from .utility import *

logger = setup_logger("iaai_logger", "iaai.log")


def handle_feedback_popup(driver):
    iframe_element = xpath_finder(
        driver, "//iframe[@title='Invitation to provide feedback']"
    )
    if not iframe_element:
        return
    driver.switch_to.frame(iframe_element)

    button = xpath_finder(driver, "//button[contains(.,'Not Right Now')]")
    if button:
        logger.info("Feedback pop-up detected, clicking on not right now...")
        button.click()
        sleep(1)

    driver.switch_to.default_content()


def accept_cookies(driver):
    accept_button = css_finder(driver, "button[id='onetrust-accept-btn-handler']")
    if accept_button:
        logger.info("Accept cookies button detected, clicking on Accept All Cookies.")
        accept_button.click()


def extract_details_from_page(driver):
    data = []
    # find all divs containing data row
    divs = xpath_finder(
        driver,
        "//div[@class='table-body border-l border-r']/div[@class='table-row table-row-border']",
        many=True,
    )
    if not divs:
        logger.warning("Data rows not found...")
        return

    for each_div in divs:
        thumbnail = css_finder(each_div, "img[aria-label='image']")
        if not thumbnail:
            logger.info("Thumbnail not found..")
            thumbnail = ""
        else:
            thumbnail = thumbnail.get_attribute("data-src")

        year_make_model = css_finder(each_div, ".table-cell.table-cell--heading h4 a")
        if not year_make_model:
            logger.warning("year_make_model not found...")
            year_make_model = ""
            year, make, model = "", "", ""
        else:
            year_make_model = year_make_model.text.strip()
            year_make_model_list = year_make_model.split(" ")
            year = year_make_model_list[0]
            make = year_make_model_list[1]
            model = " ".join(year_make_model_list[2::])

        damage = css_finder(each_div, "span[title*='Primary Damage']")
        if not damage:
            logger.warning("Damage not found...")
            damage = ""
        else:
            damage = damage.text.strip()

        buy_now_price = xpath_finder(
            each_div,
            './/span[contains(@class, "data-list__value") and contains(@class, "data-list__value--action") and contains(text(), "Buy Now")]',
        )
        if not buy_now_price:
            logger.warning("buy now price not found..")
        else:
            buy_now_price = buy_now_price.text.strip()
            pattern = r"\$([\d,]+) USD"

            match = re.search(pattern, buy_now_price)
            if match:
                buy_now_price = match.group(1).replace(",", "")

        location = css_finder(each_div, "span[title*='Branch'] a")
        if not location:
            logger.warning("Location not found...")
            location = ""
        else:
            location = location.text.strip()

        title = css_finder(each_div, "span[title*='Title/Sale Doc']")
        if not title:
            logger.warning("Title not found...")
            title = ""
        else:
            title = title.text.strip()

        loss = css_finder(each_div, "span[title*='Loss']")
        if not loss:
            logger.warning("Loss not found...")
            loss = ""
        else:
            loss = loss.text.strip()

        details = css_finder(each_div, "h4.heading-7.rtl-disabled a")
        if not details:
            logger.warning("Details link not found...")
        else:
            details = details.get_attribute("href")

        # aggregate data to a dictionary
        tmp = {
            "year_make_model": year_make_model,
            "year": year,
            "make": make,
            "model": model,
            "damage": damage,
            "buy_now_price": buy_now_price,
            "location": location,
            "title": title,
            "loss": loss,
            "thumbnail": thumbnail,
            "details": details,
            "source": "iaai",
        }
        data.append(tmp)

    return data


def number_of_vehicles(driver):
    total_results = css_finder(driver, "lable[id='headerTotalAmount']")
    if total_results:
        total_results = total_results.text
        total_results = total_results.split(" ")[0].replace(",", "")
        total_results = int(total_results)
        return total_results
    else:
        logger.warning("total_results not found...")
        return 0


def click_on_next(driver):
    next_button = css_finder(driver, "button.btn-next")
    if next_button:
        if next_button.get_attribute("disabled"):
            return None
        else:
            driver.execute_script("arguments[0].click();", next_button)
        sleep(2)
    else:
        logger.warning("Next Button not found...")


# def change_limit_to_25(driver, total_results):
#     # change the limit and navigate to correct page
#     dropdown = css_finder(driver, "a[id='pageSizeHeader']")
#     if not dropdown:
#         logger.warning("Dropdown button not found...")
#         return
#     dropdown.click()
#     # find 25
#     limit_25 = xpath_finder(driver, "//div[@class='dropdown open']//a[contains(.,25)]")
#     if not limit_25:
#         logger.warning("25 items per page not found in dropdown...")
#         return
#     limit_25.click()
#     sleep(2)

#     # navigate to correct page
#     page_to_navigate = (total_results // 100) * 4 + 1
#     page_to_navigate = str(page_to_navigate)
#     visible_pages = css_finder(driver, "button[aria-label='Page number']", many=True)
#     if visible_pages:
#         visible_pages_list = [x.text.strip() for x in visible_pages]
#     while page_to_navigate not in visible_pages_list:
#         # click on >> until the required page is visible.
#         next_10 = css_finder(driver, "button.btn-last.btn-next-10")
#         if next_10:
#             next_10.click()
#             sleep(2)
#     # now we have page to navigate in visible_pages.
#     for each_page in visible_pages:
#         if each_page.text == page_to_navigate:
#             each_page.click()
#             break


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
    sleep(3)

    accept_cookies(driver)

    res = []
    current_count = 1
    total_results = number_of_vehicles(driver)
    total_pages = total_results // 25
    logger.info(f"For this run {total_results} number of vehicles found...")
    while current_count <= total_pages:
        scroll_down_page(driver, speed=25)
        handle_feedback_popup(driver)
        data = extract_details_from_page(driver)
        if not data:
            logger.warning("Not data found on the website...")
        else:
            logger.info(f"Extracted data from {current_count} page...")
            res.extend(data)
        current_count += 1
        # check if next button is clickable, if it is click else break
        click_on_next(driver)
        sleep(3)
    driver.quit()
    return res
