import os
import json
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

def add_row_to_csv(file_path, data):
    """
    Adds new rows to the next of the last row in a CSV file.

    Parameters:
    - file_path: str, path to the CSV file
    - data_list: list of dict, a list where each dictionary has keys as column names and values as the data for a new row
    """
    try:
        with open(file_path, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
            if os.stat(file_path).st_size == 0:
                writer.writeheader()  # Write header if the file is empty
            writer.writerows(data)
    except Exception as e:
        print("Error writing to CSV:", e)


def read_phone_numbers_from_csv(file_path):
    """
    Read phone numbers from a CSV file.

    Parameters:
    - file_path: str, path to the CSV file

    Returns:
    - phone_numbers: list, list of phone numbers
    """
    phone_numbers = []
    try:
        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                phone_numbers.append(row['Phone Number'])
    except FileNotFoundError:
        pass  # Ignore if the file doesn't exist
    except Exception as e:
        print("Error reading from CSV:", e)
    
    return phone_numbers

# Load username and password from config.json
with open('config.json', 'r') as f:
    config = json.load(f)
    username = config.get('username', '')
    password = config.get('password', '')
while True:
    try:
        # Check if the CSV file exists
        filename = f"{username}.csv"
        if not os.path.exists(filename):
            # Create the CSV file with column headers
            with open(filename, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['DateTime', 'Phone Number', 'Price'])

        # Replace 'phone.csv' with the actual file path if it's in a different location

        phone_array = read_phone_numbers_from_csv(filename)
        
        print("current scraped phone numbers :", phone_array)

        # Set options for headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1200")


        driver = webdriver.Chrome(options=options)

        # Navigate to the URL
        baseURL = 'https://www.vodacom.co.za/cloud/digital/login'
        driver.get(baseURL)

        # Accept all Cookies
        accept_cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_cookies_button.click()

        time.sleep(5)
        # Find the input elements by their IDs
        username_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.NAME, 'username'))
        )
        password_input = driver.find_element(By.NAME, 'password')

        # Fill in the input fields
        username_input.send_keys(username)
        password_input.send_keys(password)

        # Find the NEXT button and wait until it becomes clickable
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and @class='btn btnRed']"))
        )

        # Click on the NEXT button
        next_button.click()

        # Wait for the page to load
        time.sleep(5)

        # Navigate to the next URL
        nextURL = 'https://www.vodacom.co.za/cloud/mobile/detailed-balances'
        driver.get(nextURL)

        # Wait for the page to load
        time.sleep(10)

        # Find the parent div with class 'products-dropdown'
        parent_div = driver.find_element(By.CLASS_NAME, 'products-dropdown')

        # Wait for the page to load
        time.sleep(10)

        # Find all <div class="moreDetails"> elements within the parent div
        more_details_divs = parent_div.find_elements(By.XPATH, ".//div[@class='moreDetails']")

        # Click on the first moreDetails div
        more_details_divs[0].click()

        # Wait for a brief moment
        time.sleep(10)

        # Find all p tags with class 'displayContext'
        p_tags = driver.find_elements(By.CLASS_NAME, 'displayContext')

        # Store p tag values in an array
        p_tag_values = [p_tag.text for p_tag in p_tags]

        if(len(phone_array) == len(p_tag_values)): 
            print("Scraping is finished!")
            break
   
        # Click on the first moreDetails div
        more_details_divs[0].click()

        # Wait for a brief moment
        time.sleep(10)

        # Create an empty list to store data
        data = []

        print(p_tag_values)

        # Iterate over each p tag value and extract the balance
        for p_tag_value in p_tag_values:
            if p_tag_value in phone_array:
                print(f"--->{p_tag_value}")
                continue
            data = []
                    # Counter for the number of iterations
            iteration_count = 0

            # Maximum number of iterations before exiting the program
            max_iterations = 10

            while(iteration_count < max_iterations):
                try:
                    # Click on the first moreDetails div
                    more_details_divs[0].click()

                    # Wait for a brief moment
                    time.sleep(3)

                    # Locate the specific p tag element based on its value
                    p_tag_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//p[@class='displayContext' and text()='{p_tag_value}']"))
                    )

                    # Click on the p tag element
                    p_tag_element.click()

                    # Wait for a brief moment
                    time.sleep(3)

                    # Wait for the div element to become visible
                    total_div = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "bundle-container__header-total"))
                    )

                    # Get the text content of the div
                    total_text = total_div.text

                    # Extract the numerical value from the text
                    total_value = total_text.split()[1]

                    # Get current date and time
                    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Append data to the list
                    data.append({'DateTime': current_datetime, 'Phone Number': f'{p_tag_value}', 'Price': total_value})
                    # Print the values
                    print(f"DateTime: {current_datetime}, Phone Number: {f':{p_tag_value}'}, Price: {total_value}")

                    add_row_to_csv(filename, data)
                    break
                except Exception as e:
                    iteration_count = iteration_count + 1
                    # If there's an error, continue to the next iteration
                    print("Error:", e)
                    print("repeating:", iteration_count)
                    continue
                
            if(iteration_count >= max_iterations):
                print(f"Issued Phone Number: {p_tag_value}")
                break
    except Exception as e:
        print("outest level Error:", e)
        # Close the browser
        driver.quit()
        time.sleep(10)
        continue
    # Close the browser
    driver.quit()

    time.sleep(10)
