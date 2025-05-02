import os
import re
import time
import dns.resolver  # For DNS MX record validation
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor

# Generate unique and creative keywords based on the base keyword and country
def generate_keywords(base_keyword, country="", max_count=10000):
    """Generates exactly `max_count` unique variations of the base keyword."""
    try:
        # Base variations for keyword generation
        base_variations = [
            f'"{base_keyword}" AND "contact information" {country}',
            f'"{base_keyword}" AND "email directory" {country}',
            f'"{base_keyword}" AND "official email" {country}',
            f'"{base_keyword}" AND "corporate email address" {country}',
            f'"{base_keyword}" AND "business contact" {country}',
            f'"{base_keyword}" AND "professional email address" {country}',
            f'"{base_keyword}" AND "customer service email" {country}',
            f'"{base_keyword}" AND "executive email" {country}',
            f'"{base_keyword}" AND "team email" {country}',
            f'"{base_keyword}" AND "general inquiries email" {country}',
            f'"{base_keyword}" AND "HR contact email" {country}',
            f'"{base_keyword}" AND "support email" {country}',
            f'"{base_keyword}" AND "CEO email address" {country}',
            f'"{base_keyword}" AND "LinkedIn email" {country}',
            f'"{base_keyword}" AND "company email address" {country}',
            f'"{base_keyword}" AND "department email" {country}',
            f'"{base_keyword}" AND "sales email" {country}',
            f'"{base_keyword}" AND "marketing email" {country}',
            f'"{base_keyword}" AND "IT support email" {country}',
            f'"{base_keyword}" AND "press contact email" {country}',
            f'"{base_keyword} services" AND "email contact" {country}',
            f'"{base_keyword} team" AND "email address" {country}',
            f'"{base_keyword} support" AND "contact email" {country}',
            f'"{base_keyword} inquiries" AND "email" {country}',
            f'"{base_keyword} department" AND "email contact" {country}',
            f'"{base_keyword} staff" AND "email directory" {country}',
            f'"{base_keyword} management" AND "email address" {country}',
            f'"{base_keyword} operations" AND "contact email" {country}',
            f'"{base_keyword} executives" AND "email contact" {country}',
            f'"{base_keyword}" AND "customer inquiries" {country}',
            f'"{base_keyword}" AND "contact us" {country}',
            f'"{base_keyword}" AND "reach out" {country}',
            f'"{base_keyword}" AND "get in touch" {country}',
            f'"{base_keyword}" AND "email support" {country}',
            f'"{base_keyword}" AND "contact details" {country}',
            f'"{base_keyword}" AND "email help" {country}',
            f'"{base_keyword}" AND "contact email address" {country}',
            f'"{base_keyword}" AND "business inquiries" {country}',
            f'"{base_keyword}" AND "contact directory" {country}'
        ]

        # Use a set to ensure uniqueness
        unique_keywords = set(base_variations)

        # Expand the set until we reach max_count
        while len(unique_keywords) < max_count:
            for variation in base_variations:
                if len(unique_keywords) >= max_count:
                    break
                unique_keywords.add(f"{variation} {len(unique_keywords)}")

        # Return exactly `max_count` keywords
        return list(unique_keywords)[:max_count]
    except Exception as e:
        print(f"[ERROR] Error generating keywords: {e}")
        return []

# Save generated keywords to a file
def save_keywords_to_file(keywords, file_path="k.txt"):
    """Saves the generated keywords to a file."""
    try:
        with open(file_path, "w") as file:
            for keyword in keywords:
                file.write(keyword + "\n")
        print(f"[INFO] {len(keywords)} unique keywords saved to {file_path}")
    except Exception as e:
        print(f"[ERROR] Error saving keywords to {file_path}: {e}")

# Remove a processed keyword from the file
def remove_keyword_from_file(keyword, file_path="k.txt"):
    """Removes a keyword from the file after it has been searched."""
    try:
        with open(file_path, "r") as file:
            keywords = file.readlines()
        keywords = [k.strip() for k in keywords if k.strip() != keyword]
        with open(file_path, "w") as file:
            file.writelines(f"{k}\n" for k in keywords)
        print(f"[INFO] Removed keyword: {keyword}")
    except Exception as e:
        print(f"[ERROR] Error removing keyword {keyword} from {file_path}: {e}")

# Save a valid email to the appropriate file
def save_email_to_file(email, file_path, saved_emails):
    """Saves a single email to the specified file if it's not already saved."""
    if email not in saved_emails:
        try:
            with open(file_path, "a", buffering=1) as file:  # Open file with line buffering
                file.write(email + "\n")
                file.flush()  # Ensure the email is written to the file immediately
            saved_emails.add(email)
            print(f"[SAVED] {email} -> {file_path}")
        except Exception as e:
            print(f"[ERROR] Error saving email {email}: {e}")

# Extract emails from the page source using regex
def extract_emails_from_page_source(page_source):
    """Extracts emails from the page source using regex."""
    try:
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(email_pattern, page_source)
    except Exception as e:
        print(f"[ERROR] Error extracting emails: {e}")
        return []

# Validate email domains using DNS MX records
def check_email_with_dns(email):
    """Checks if the email domain has valid MX records."""
    try:
        domain = email.split("@")[-1]
        mx_records = dns.resolver.resolve(domain, "MX")
        for record in mx_records:
            if "outlook.com" in str(record.exchange):
                return "outlook"
        return "other"
    except dns.resolver.NXDOMAIN:
        print(f"[INVALID] Domain does not exist: {email}")
        return None
    except dns.resolver.NoAnswer:
        print(f"[INVALID] No MX records found for: {email}")
        return None
    except dns.exception.Timeout:
        print(f"[INVALID] DNS query timed out for: {email}")
        return None
    except Exception as e:
        print(f"[ERROR] Error checking DNS for {email}: {e}")
        return None

# Search Bing for emails using a keyword
def search_emails(keyword, saved_emails):
    """Searches Bing for the given keyword and extracts emails."""
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set up the WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)

        try:
            # Open Bing
            driver.get("https://www.bing.com")

            # Handle pop-ups (e.g., Accept Cookies)
            try:
                accept_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Agree')]"))
                )
                accept_button.click()
            except Exception:
                pass

            # Search for the keyword
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)

            print(f"[SEARCHING] {keyword}")

            # Wait for results to load
            time.sleep(3)

            # Scroll and extract emails
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                page_source = driver.page_source
                emails = extract_emails_from_page_source(page_source)

                # Save valid emails after DNS check
                for email in emails:
                    dns_status = check_email_with_dns(email)
                    if dns_status == "outlook":
                        save_email_to_file(email, "outlook.txt", saved_emails)
                    elif dns_status == "other":
                        save_email_to_file(email, "e.txt", saved_emails)

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

        finally:
            driver.quit()

    except Exception as e:
        print(f"[ERROR] Error during search for keyword '{keyword}': {e}")

# Process multiple keywords in parallel
def process_keywords_in_parallel(keywords, saved_emails, max_threads=5):
    """Processes multiple keywords in parallel using threads."""
    with ThreadPoolExecutor(max_threads) as executor:
        for keyword in keywords:
            executor.submit(search_emails, keyword, saved_emails)
            remove_keyword_from_file(keyword)

# Main function
def main():
    """Main function to generate keywords, save them, and perform searches."""
    saved_emails = set()
    if os.path.exists("outlook.txt"):
        with open("outlook.txt", "r") as file:
            saved_emails.update(line.strip() for line in file)
    if os.path.exists("e.txt"):
        with open("e.txt", "r") as file:
            saved_emails.update(line.strip() for line in file)

    base_keyword = input("Enter the base keyword: ")
    country = input("Enter the country (optional): ").strip()

    keywords = generate_keywords(base_keyword, country=country, max_count=10000)
    save_keywords_to_file(keywords, "k.txt")

    while True:
        try:
            with open("k.txt", "r") as file:
                keywords = [line.strip() for line in file if line.strip()]

            if not keywords:
                print("[INFO] No more keywords to process. Exiting...")
                break

            process_keywords_in_parallel(keywords[:5], saved_emails, max_threads=5)

        except Exception as e:
            print(f"[ERROR] Error during processing: {e}")

if __name__ == "__main__":
    main()