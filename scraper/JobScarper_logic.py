from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import os

DEFAULT_TIME_OUT = 30


def setup_driver(logger):
    logger("Updating the Chrome WebDriver...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.implicitly_wait(DEFAULT_TIME_OUT)
        logger("WebDriver Installed .")
        return driver
    except Exception as e:
        logger(f" Failure during driver installation: {e}", 'error')
        return None


def login_to_site(driver, username, password, job_title, job_location, logger):

    LOGIN_URL = "https://www.drushim.co.il"
    logger(f"2. Connection to {LOGIN_URL} ...")

    try:
        driver.get(LOGIN_URL)

        login_button_main = WebDriverWait(driver, DEFAULT_TIME_OUT).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'התחברות')]"))
        )
        login_button_main.click()


        username_input = WebDriverWait(driver, DEFAULT_TIME_OUT).until(
            EC.presence_of_element_located((By.ID, "email-login-field"))
        )
        username_input.send_keys(username)
        password_input = driver.find_element(By.ID, "password-login-field")
        password_input.send_keys(password)

        login_button = driver.find_element(By.XPATH, "//*[contains(text(), 'כניסה')]")
        login_button.click()
        logger("Connected successfully!.")


        logger(f"3. Search for : '{job_title}' at '{job_location}'...")
        job_search_input = driver.find_element(By.ID, "input-274")
        location_search_input = driver.find_element(By.ID, "input-280")

        job_search_input.clear()
        job_search_input.send_keys(job_title)

        location_search_input.clear()
        location_search_input.send_keys(job_location)
        location_search_input.send_keys(Keys.TAB)

        search_button = WebDriverWait(driver, timeout=DEFAULT_TIME_OUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#search-input-wrpper button[type='submit']"))
        )
        search_button.click()

        WebDriverWait(driver, DEFAULT_TIME_OUT).until_not(
            EC.url_to_be(LOGIN_URL)
        )
        return True

    except TimeoutException:
        logger("Timeout:", 'error')
        return False
    except NoSuchElementException as e:
        logger(f"🛑 NoSuchElement: {e}", 'error')
        return False
    except Exception as e:
        logger(f"Failed to search/connect {e}", 'error')
        return False


def scrape_jobs_for_export(driver, limit, logger):

    logger(f"4. Starting the scraping for  {limit} Job titles...")
    job_data_list = []

    for i in range(limit):
        try:
            job_card = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"div[data-cy='job-item{i}']"))
            )

            logger(f"  - Exporting the  {i + 1} Element...")


            link_element = job_card.find_element(By.TAG_NAME, "a")
            relative_link = link_element.get_attribute("href")


            job_title_element = job_card.find_element(By.CSS_SELECTOR, "span.job-url.primary--text")
            job_title_headline = job_title_element.text.strip()


            company_element = job_card.find_element(By.CSS_SELECTOR, "span.font-weight-medium.bidi")
            company_name = company_element.text.strip()

            job_data_list.append({
                "שם המשרה": job_title_headline,
                "שם החברה": company_name,
                "קישור": relative_link
            })

        except TimeoutException:
            logger(f"Time Exception data-cy='job-item{i} not found .")
            break
        except NoSuchElementException as e:
            logger(f"No such element {i + 1}: {e}.")
            continue

    logger(f"✅ Successfully {len(job_data_list)} .")
    return job_data_list


def write_jobs_to_csv(jobs_data, filename, logger):

    if not jobs_data:
        logger("5. Empty Job List ")
        return

    logger(f"5. Writing to CSV: {filename}...")

    fieldnames_keys = ['שם המשרה', 'שם החברה', 'קישור']
    header_display_names = ['Job Title', 'Company Name', 'Job Link']

    file_exists = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames_keys)

            if not file_exists or os.path.getsize(filename) == 0:
                writer.writerow(dict(zip(fieldnames_keys, header_display_names)))

            writer.writerows(jobs_data)

        logger(f"Saved at {filename}")

    except Exception as e:
        logger(f"🛑Error while writing CSV: {e}", 'error')
        if jobs_data:
            logger(f"DEBUG: Founded Keys: {list(jobs_data[0].keys())}")