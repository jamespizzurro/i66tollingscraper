import csv
import os
from time import sleep

import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

previous_meridiem = None

# set up selenium

path_to_chromedriver = os.path.dirname(os.path.abspath(__file__)) + "/chromedriver/2.33/linux64/chromedriver"
os.environ['webdriver.chrome.driver'] = path_to_chromedriver
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = "/opt/google/chrome/google-chrome"
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_experimental_option('mobileEmulation', {'deviceName': 'Nexus 5'})
driver = webdriver.Chrome(executable_path=path_to_chromedriver, chrome_options=chrome_options)
wait = WebDriverWait(driver, 5)

while True:
    now = datetime.datetime.now()
    meridiem = "AM" if now.hour < 12 else "PM"

    if not previous_meridiem or meridiem != previous_meridiem:
        # visit VDOT's toll calculator website, go to its current toll estimate page

        driver.get("https://vai66tolls.com/")
        current_toll_estimate_button = driver.find_element(By.CSS_SELECTOR, '.nav-icon.calc')
        current_toll_estimate_button.click()

        # select appropriate direction

        if meridiem == "AM":
            eastbound_button = wait.until(expected_conditions.element_to_be_clickable((By.ID, 'ebDirBtn')))
            sleep(1)
            eastbound_button.click()
        else:
            westbound_button = wait.until(expected_conditions.element_to_be_clickable((By.ID, 'wbDirBtn')))
            sleep(1)
            westbound_button.click()

        # select appropriate entry point

        entry_select = Select(wait.until(expected_conditions.element_to_be_clickable((By.ID, 'ddlEntryInterch'))))

        if meridiem == "AM":
            # select westbound-most entry point
            entry_select.select_by_visible_text("I-66 West")
        else:
            # select eastbound-most entry point
            entry_select.select_by_visible_text("Washington")

        entry_submit_button = driver.find_element(By.ID, 'btnUpdateBeginSel')
        entry_submit_button.click()

        # select appropriate exit point

        exit_select = Select(wait.until(expected_conditions.element_to_be_clickable((By.ID, 'ddlExitInterch'))))

        if meridiem == "AM":
            # select eastbound-most exit point
            exit_select.select_by_visible_text("Washington")
        else:
            # select westbound-most exit point
            exit_select.select_by_visible_text("I-66 West")

        exit_submit_button = driver.find_element(By.ID, 'btnUpdateEndSel')
        exit_submit_button.click()
    else:
        refresh_button = wait.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'refresh-btn')))
        refresh_button.click()

    # fetch toll amount, log and save

    sleep(1)
    toll_amount_element = wait.until(expected_conditions.element_to_be_clickable((By.ID, 'spanTollAmt')))
    toll_amount = toll_amount_element.text

    if toll_amount != "No toll for this trip":
        date_string = now.strftime('%Y-%m-%d %I:%M %p')
        print(f"{date_string},{toll_amount}")
        with open("toll_data.csv", 'a') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([date_string, toll_amount])

    # prepare to refresh and try again

    previous_meridiem = meridiem

    t = datetime.datetime.utcnow()
    sleeptime = 60 - (t.second + t.microsecond/1000000.0)
    sleep(sleeptime)

driver.close()
