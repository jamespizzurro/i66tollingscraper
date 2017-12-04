import csv
import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

toll_data = {}
target_num_hours = 8
target_num_minutes = 59
target_meridiem = 'AM'

# set up selenium

path_to_chromedriver = os.path.dirname(os.path.abspath(__file__)) + "/chromedriver/2.33/linux64/chromedriver"
os.environ['webdriver.chrome.driver'] = path_to_chromedriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option('mobileEmulation', {'deviceName': 'Nexus 5'})
driver = webdriver.Chrome(executable_path=path_to_chromedriver, chrome_options=chrome_options)
wait = WebDriverWait(driver, 5)

# visit VDOT's toll calculator website, go to its historical data page

driver.get("https://vai66tolls.com/")
historical_estimate_button = driver.find_element(By.CSS_SELECTOR, '.nav-icon.historical')
historical_estimate_button.click()

should_continue_scraping = True
while should_continue_scraping:
    # select appropriate direction

    if target_meridiem.upper() == 'AM':
        eastbound_button = wait.until(expected_conditions.element_to_be_clickable((By.ID, 'ebDirBtn')))
        sleep(1)
        eastbound_button.click()
    else:
        westbound_button = wait.until(expected_conditions.element_to_be_clickable((By.ID, 'wbDirBtn')))
        sleep(1)
        westbound_button.click()

    # select appropriate entry point

    entry_select = Select(wait.until(expected_conditions.element_to_be_clickable((By.ID, 'ddlEntryInterch'))))

    if target_meridiem.upper() == 'AM':
        # select westbound-most entry point
        entry_select.select_by_visible_text("I-66 West")
    else:
        # select eastbound-most entry point
        entry_select.select_by_visible_text("Washington")

    entry_submit_button = driver.find_element(By.ID, 'btnUpdateBeginSel')
    entry_submit_button.click()

    # select the appropriate time

    time_input = wait.until(expected_conditions.element_to_be_clickable((By.ID, 'timepicker')))
    time_input.click()

    up_buttons = driver.find_elements(By.CLASS_NAME, 'wickedpicker__controls__control-up')
    down_buttons = driver.find_elements(By.CLASS_NAME, 'wickedpicker__controls__control-down')

    meridiem_display = driver.find_element(By.CLASS_NAME, 'wickedpicker__controls__control--meridiem')
    meridiem = meridiem_display.text
    while meridiem.upper() != target_meridiem.upper():
        # initial_timepicker_value = time_input.get_attribute('value')

        meridiem_up_button = up_buttons[2]
        meridiem_up_button.click()

        # new_timepicker_value = time_input.get_attribute('value')
        # while new_timepicker_value == initial_timepicker_value:
        #     continue

        meridiem = meridiem_display.text

    hours_display = driver.find_element(By.CLASS_NAME, 'wickedpicker__controls__control--hours')
    num_hours = int(hours_display.text)
    while num_hours != target_num_hours:
        # initial_timepicker_value = time_input.get_attribute('value')

        if num_hours < target_num_hours:
            hour_up_button = up_buttons[0]
            hour_up_button.click()
        elif num_hours > target_num_hours:
            hour_down_button = down_buttons[0]
            hour_down_button.click()

        # new_timepicker_value = time_input.get_attribute('value')
        # while new_timepicker_value == initial_timepicker_value:
        #     continue

        num_hours = int(hours_display.text)

    minutes_display = driver.find_element(By.CLASS_NAME, 'wickedpicker__controls__control--minutes')
    num_minutes = int(minutes_display.text)
    while num_minutes != target_num_minutes:
        # initial_timepicker_value = time_input.get_attribute('value')

        if num_minutes < target_num_minutes:
            minute_up_button = up_buttons[1]
            minute_up_button.click()
        elif num_minutes > target_num_minutes:
            minute_down_button = down_buttons[1]
            minute_down_button.click()

        # new_timepicker_value = time_input.get_attribute('value')
        # while new_timepicker_value == initial_timepicker_value:
        #     continue

        num_minutes = int(minutes_display.text)

    time_submit_button = driver.find_element(By.ID, 'selectDateBtn')
    time_submit_button.click()

    # select appropriate exit point

    exit_select = Select(wait.until(expected_conditions.element_to_be_clickable((By.ID, 'ddlExitInterch'))))

    if target_meridiem.upper() == 'AM':
        # select eastbound-most exit point
        exit_select.select_by_visible_text("Washington")
    else:
        # select westbound-most exit point
        exit_select.select_by_visible_text("I-66 West")

    exit_submit_button = driver.find_element(By.ID, 'btnUpdateEndSel')
    exit_submit_button.click()

    # fetch toll amount

    sleep(1)
    toll_amount_element = wait.until(expected_conditions.element_to_be_clickable((By.ID, 'spanTollAmt')))
    toll_amount = toll_amount_element.text

    # continue scraping, if necessary

    if toll_amount == "No toll for this trip":
        if meridiem.upper() == 'AM':
            target_num_hours = 3
            target_num_minutes = 0
            target_meridiem = 'PM'

            # TODO: temporarily avoid scraping data for PM rush
            should_continue_scraping = False
            continue
        else:
            # we're done parsing!
            should_continue_scraping = False
            continue
    else:
        # log and save toll fare
        num_minutes_string = str(num_minutes)
        if len(num_minutes_string) == 1:
            num_minutes_string = f"0{num_minutes_string}"
        print(f"{num_hours}:{num_minutes_string} {meridiem.lower()},{toll_amount}")
        toll_data[f"{num_hours}:{num_minutes_string} {meridiem.lower()}"] = toll_amount

        if num_minutes == 59:
            target_num_hours += 1
            target_num_minutes = 0
        else:
            target_num_minutes += 1

    restart_button = wait.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'reset-btn')))
    restart_button.click()

driver.close()

# dump the results to CSV

with open("toll_data.csv", 'w') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in toll_data.items():
        writer.writerow([key, value])
