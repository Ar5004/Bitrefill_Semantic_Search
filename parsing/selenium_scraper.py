import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup directories for saving HTML
base_dir = 'bitrefill_data'
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

def save_html(html_content, file_name):
    folder_path = base_dir
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

# Initialize the browser with undetected_chromedriver
options = uc.ChromeOptions()
#options.add_argument("--headless")  # Remove this if you want to see the browser
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = uc.Chrome(options=options)

wait = WebDriverWait(driver, 10)

try:
    # Navigate to the website
    driver.get('https://www.bitrefill.com/mx/en/gift-cards/')
    time.sleep(2)

    # Click on "Load More" until it's not clickable
    while True:
        try:
            # Refine the button locator to target by class name
            load_more_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(@class, "_button_15954_1") and contains(@class, "_primary_15954_76")]')
            ))
            ActionChains(driver).move_to_element(load_more_button).perform()
            load_more_button.click()
            time.sleep(2)  # Allow the page to load
        except Exception as e:
            print("No more 'Load More' button or an error occurred:", e)
            break

    # Collect all links containing "/gift-cards/"
    gift_card_links = driver.find_elements(By.XPATH, '//a[contains(@href, "/gift-cards/") and contains(@class, "_wrapper_1q4b9_1")]')
    visited_links = set()

    links = []
    for link in gift_card_links:
        try:
            links.append(link.get_attribute('href'))
        except:
            continue

    for href in links:
        print(href)
        if href and href not in visited_links:
            visited_links.add(href)
            driver.get(href)
            time.sleep(5)  # Wait for the page to load
            
            # Save the page's HTML
            html_content = driver.page_source
            card_name = href.split("/")[-2]  # Use the last part of the URL as folder name
            save_html(html_content, file_name=card_name)

finally:
    driver.quit()

print("Scraping completed. HTML saved in:", base_dir)
