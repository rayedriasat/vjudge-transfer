"""
Vjudge Contest Solution Transfer Tool

This script automates the process of transferring solutions between Vjudge programming contests.
It can copy solutions from one contest and submit them to another contest, with options to:
- Load contest data
- Copy solutions from source contest
- Submit solutions to target contest
- Save solutions as local files
"""

import string
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, WebDriverException

# User Configuration
username = "thercube"  # Your Vjudge username / target username whose code you wanna fetch or save in local directory
password = ""  # Your Vjudge password (Optional if already logged in
# or don't wanna login, you can manually open the chrome-test/chrome.exe and login)

# File and Contest Settings
codeFolderPath = "E:\\S17bootcamp\\"  # Path to save code files
old_contest_url = "https://vjudge.net/contest/613268"  # Source contest URL
new_contest_url = "https://vjudge.net/contest/658660"  # Target contest URL
start_from = "A"  # Start copying from this problem (optional)
stop_at = "J"  # Stop at this problem (optional)
S = 8  # Sleep duration for page loads (in seconds) Increase if slow internet or getting captcha
# U can decrease S if u are only copying but not submitting
# Copying code or in other words downloading code to local directory is easy and fast

# Storage for contest data
old_contest_data = {}  # Stores data from source contest
new_contest_data = {}  # Stores data from target contest


def save_as_cpp_file():
    """
    Save solutions as local .cpp files.

    Creates a file for each problem using the format:
    {problem_id}_{sanitized_title}.cpp

    Checks for existing files to avoid duplicates.
    """
    translation_table = str.maketrans(" -", "__", "()")
    flag = False
    for key in old_contest_data.keys():
        # Control which problems to process
        if not flag and key != start_from:
            continue
        if key == start_from:
            flag = True
        if key == stop_at:
            break

        # Generate the file path with sanitized title
        file_path = f"{codeFolderPath}{key}_{old_contest_data[key]['Title'].translate(translation_table).rstrip(string.punctuation + '_')}.cpp"

        # Check for existing solution
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                existing_content = file.read()
                if old_contest_data[key]["code"] in existing_content:
                    print(f"Code already exists for {key}. Skipping append.")
                    continue

        # Save new solution
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(old_contest_data[key]["code"])
            print(f"Code pasted for {key}")


def setup_driver():
    """
    Initialize and configure the Chrome WebDriver.

    Uses local Chrome with custom user profile to maintain login state.
    """
    global driver
    try:
        options = Options()
        # Use the bundled Chrome from chrome-win64 directory
        chrome_path = os.path.join(os.getcwd(), "chrome-win64", "chrome.exe")
        options.binary_location = chrome_path

        # run chrome-win64\chrome.exe to login manually
        # data is stored in C:\Users\<your_pc_username>\AppData\Local\Google\Chrome for Testing\User Data
        user_data_dir = (
            r"C:\Users\ASUS\AppData\Local\Google\Chrome for Testing\User Data"
        )
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        # Add necessary Chrome options for stability
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")

        # Use the bundled ChromeDriver
        chromedriver_path = os.path.join(
            os.getcwd(), "chromedriver-win64", "chromedriver.exe"
        )
        service = Service(chromedriver_path)

        driver = webdriver.Chrome(service=service, options=options)
        return True
    except WebDriverException as e:
        print(f"Failed to setup Chrome driver: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error during driver setup: {str(e)}")
        return False


def get_datadict(contest_url) -> dict:
    """
    Fetch problem data from a contest URL.

    Args:
        contest_url: URL of the Vjudge contest

    Returns:
        dict: Dictionary containing problem data indexed by problem ID
    """
    global driver
    driver.get(contest_url + "#overview")
    table = driver.find_element(By.ID, "contest-problems")
    headers = [header.text for header in table.find_elements(By.XPATH, ".//thead//th")]
    data_dict = {}
    for row in table.find_elements(By.XPATH, ".//tbody//tr"):
        cells = row.find_elements(By.XPATH, ".//td")
        row_data = {headers[i]: cells[i].text for i in range(len(headers))}
        row_data["Link"] = contest_url + f"#problem/{row_data['#']}"
        row_data["sol_link"] = contest_url + f"#status/{username}/{row_data['#']}/1/"
        data_dict[row_data["#"]] = row_data

    return data_dict


def login():
    """
    Log into Vjudge account.

    Note: Requires password to be set before calling.
    """
    global driver, username, password
    driver.get("https://vjudge.net/")
    time.sleep(S)
    login_button = driver.find_element(By.CLASS_NAME, "login")
    login_button.click()
    time.sleep(S)
    driver.find_element(By.ID, "login-username").send_keys(username)
    driver.find_element(By.ID, "login-password").send_keys(password)
    driver.find_element(By.ID, "login-password").send_keys(Keys.RETURN)
    time.sleep(S)


def copy_code():
    """
    Copy solutions from the old contest.

    Fetches solution code for each problem and stores it in old_contest_data.
    Saves progress to soldata.json after each successful copy.
    """
    global driver, start_from, old_contest_data, stop_at

    flag = False
    try:
        for key in old_contest_data.keys():
            # Control which problems to process
            if not flag and key != start_from:
                continue
            if key == start_from:
                flag = True
            if key == stop_at:
                break
            if "code" in old_contest_data[key]:
                print(f"skipped copying {key}")
                continue

            link = old_contest_data[key]["sol_link"]
            driver.get(link)
            time.sleep(S / 5)
            try:
                # View solution
                view_solution_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "view-solution"))
                )
                view_solution_button.click()
                time.sleep(S / 5)

                # Get code content
                code_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "code-content"))
                )
                old_contest_data[key]["code"] = code_element.text
                print(f"solutions saved for {key} {old_contest_data[key]['Title']}")

                # Close solution modal
                cross_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "#solutionModal .modal-header button.close a")
                    )
                )
                time.sleep(S / 5)
                cross_button.click()
                time.sleep(S / 5)

            except TimeoutException:
                print(f"Solve not found for {link}: {key}")
                continue
    finally:
        # Save progress
        with open("soldata.json", "w", encoding="utf-8") as data:
            json.dump(old_contest_data, data, indent=4)


def select_language():
    """
    Select appropriate programming language for submission.

    Tries to select C++ language variant from a list of preferences.
    Falls back to other C++ versions if preferred version not available.
    """
    global driver
    dropdown = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "submit-language"))
    )
    select = Select(dropdown)
    preferences = [
        "C++ 20 (gcc 12.2)",
        "cpp20",
        "cpp",
        "C++ 20 (gnu 10.2)",
        "GNU G++17 7.3.0",
        "C++14 (gcc 8.3)",
        "C++ (gcc 8.3)",
        "C++11 5.3.0",
        "C (GCC 9.2.1)",
        "C (gcc 6.3)",
        "ANSI C 5.3.0",
        "GNU GCC C11 5.1.0",
        "c",
    ]
    options = [option.text for option in select.options]

    for pref in preferences:
        for option in options:
            if pref in option:
                select.select_by_visible_text(option)
                print(f"Selected language: {option}")
                return
    print("None of the preferred languages were found.")


def submit_code():
    """
    ### Use at your own risk ###
    ### Isn't ethical to submit solutions without understanding the problem and code ###
    ### also don't abuse the server by submitting problems that you know u can solve ###

    Submit solutions to the new contest.

    Matches problems between contests by title and submits solutions.
    Handles navigation and submission process for each problem.
    """
    global driver, start_from, old_contest_data, new_contest_data, stop_at

    flag = False
    for key in new_contest_data.keys():
        # Control which problems to process
        if not flag and key != start_from:
            continue
        if key == start_from:
            flag = True
        if key == stop_at:
            break

        code = old_contest_data[key].get("code")
        if code is None:
            continue
        link = new_contest_data[key]["Link"]

        # Verify matching problems
        if old_contest_data[key]["Title"] == new_contest_data[key]["Title"]:
            driver.get(link)
            time.sleep(S)

            # Open submit form
            submit_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "problem-submit"))
            )
            submit_button.click()
            time.sleep(S)
            select_language()
            time.sleep(S)

            # Submit solution
            driver.find_element(By.ID, "submit-solution").send_keys(code)
            time.sleep(S)
            driver.find_element(By.ID, "btn-submit").click()
            time.sleep(S)
            print(f"{key} submitted")

            # Close submit modal
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "#solutionModal .modal-header .close a .fa-close")
                )
            )
            close_button.click()
            time.sleep(S)
        else:
            print(
                f"{key}\nold title={old_contest_data[key]['Title']}\nnew title={new_contest_data[key]['Title']}"
            )
            time.sleep(S)


def load_data():
    """
    Load contest data from cache or fetch from Vjudge.

    Attempts to load from JSON files first, fetches from web if not found.
    """
    global old_contest_data, new_contest_data

    try:
        with open("soldata.json", "r", encoding="utf-8") as file:
            old_contest_data = json.load(file)
    except FileNotFoundError:
        old_contest_data = get_datadict(old_contest_url)
        with open("soldata.json", "w", encoding="utf-8") as data:
            json.dump(old_contest_data, data, indent=4)

    try:
        with open("newdata.json", "r", encoding="utf-8") as file:
            new_contest_data = json.load(file)
    except FileNotFoundError:
        new_contest_data = get_datadict(new_contest_url)
        with open("newdata.json", "w", encoding="utf-8") as data:
            json.dump(new_contest_data, data, indent=4)


# Main execution
if __name__ == "__main__":
    try:
        if not setup_driver():
            print("Failed to initialize Chrome driver. Exiting...")
            exit(1)

        # Add a small delay after driver setup
        time.sleep(2)

        load_data()
        copy_code()
        save_as_cpp_file()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"Error closing driver: {str(e)}")
