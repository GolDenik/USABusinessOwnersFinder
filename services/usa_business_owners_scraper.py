from __future__ import annotations
import time
import logging
import re
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from models.models import USABusinessOwners
from settings import BASE_OPEN_CORPORATES_URL
from utilities.open_corporates_login import OpenCorporatesLogin
from settings import HEADLESS, USER_AGENT
from selenium import webdriver


class USABusinessOwnersScraper:
    driver: WebDriver = None
    currently_scrapped_states: list[str] = []
    empty_owners: USABusinessOwners = USABusinessOwners("")

    @staticmethod
    def set_currently_scrapped_state(new_states: list[str]):
        USABusinessOwnersScraper.currently_scrapped_states = new_states

    @staticmethod
    def initialize_tools_if_not_yet_initialized():
        """Initializes the WebDriver if it hasn't been initialized yet."""
        if USABusinessOwnersScraper.driver is None:
            logging.debug("Initializing the WebDriver and logging into OpenCorporates...")

            # Initialize the WebDriver here
            options = webdriver.ChromeOptions()

            # Disabling the blink features related to automation to prevent detection
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Setting the user-agent for the web browser to mimic a specific client
            options.add_argument(f"user-agent={USER_AGENT}")

            # Hiding useless logging
            options.add_argument("--log-level=3")

            # Checking if the browser should run in headless mode (without GUI)
            if HEADLESS:
                options.add_argument("--headless")

            USABusinessOwnersScraper.driver = webdriver.Chrome(options=options)
            logging.debug("WebDriver initialization is FINISHED")

            # Logins into OpenCorporate website
            email = "denikgolibroda@gmail.com"
            password = "wX&L8yETXFrEYXd"

            if not OpenCorporatesLogin().login(email, password, USABusinessOwnersScraper.driver):
                raise RuntimeError(
                    "An exception appeared while logging into OpenCorporates with the following credentials"
                    f"\nEmail: {email}\nPassword: {password}\n")

            logging.debug(f"Logging into OpenCorporates is FINISHED."
                         f"\n Credentials used: Email: {email} / Password: {password}")

    @staticmethod
    def search_url(company_name: str) -> str:
        return (
            f"{BASE_OPEN_CORPORATES_URL}companies?q={company_name.replace(' ', '+').replace('&', '%26') + "&utf8=✓"}"
        )

    @staticmethod
    def prepare_text_for_the_comparison(text: str) -> str:
        # 1) - Make the texts lowercase
        first_modified_version_text = text.lower()

        # 2) Remove "inactive" word, in case the company is shown as inactive in OpenCorporates search result
        second_modified_version_text = first_modified_version_text.replace("inactive", "")

        # 3) Remove "and" in both
        third_modified_version_text = second_modified_version_text.replace("and", "")

        # 4) - Remove business entity abbreviations like "LLC", "CO", "INC".
        business_entity_abbreviations = ["llc", "co", "inc"]

        fourth_modified_version_text = third_modified_version_text

        for abbreviation in business_entity_abbreviations:
            fourth_modified_version_text = fourth_modified_version_text.replace(abbreviation, "")

        # 5) - Remove all the characters, except letters
        final_modified_version_text = re.sub(r'[^a-zA-Z]', '', fourth_modified_version_text)

        return final_modified_version_text

    @staticmethod
    def compare_the_comparable_texts(comparable_found_block_text, comparable_searched_company_name):
        # Check if the company name matches
        company_names_match = (comparable_found_block_text.startswith(comparable_searched_company_name)
                               or comparable_searched_company_name in comparable_found_block_text)

        # Check if the found company contains the currently scrapped state
        found_company_text_contains_correct_state = any(re.sub(r'\s', '', state).lower() in comparable_found_block_text
                                                        for state in USABusinessOwnersScraper.currently_scrapped_states)

        return company_names_match & found_company_text_contains_correct_state

    @staticmethod
    def compare_found_block_text_with_searched(found_block_text: str, searched_company_name: str) -> bool:
        """Preparation for comparison of both: searched & found texts"""

        comparable_found_block_text = (USABusinessOwnersScraper
                                       .prepare_text_for_the_comparison(found_block_text))
        comparable_searched_company_name = (USABusinessOwnersScraper
                                            .prepare_text_for_the_comparison(searched_company_name))

        """Actual Comparison of searched & found texts"""

        return USABusinessOwnersScraper.compare_the_comparable_texts(comparable_found_block_text, comparable_searched_company_name)

    @staticmethod
    def extract_link_from_company_block(company_block: WebElement) -> WebElement | None:
        try:
            logging.debug(f"Extracting the link from a proper company block..."
                         f"\nCompany block text: {company_block.text.strip()}")

            extracted_link = company_block.find_element(By.CLASS_NAME, "company_search_result")
            logging.debug("Extracting the link from a company block is successfully FINISHED")
            return extracted_link
        except NoSuchElementException:
            logging.exception(f"Couldn't extract the link from a company block and returning None..."
                         f"\nCompany block text: {company_block.text.strip()}")
            return None

    @staticmethod
    def find_proper_company_link_from_search_result(search_result: list[WebElement],
                                                    searched_company_name: str) -> WebElement | None:
        logging.debug(f"Looking for a proper company block from a search result..."
                     f"\nSearched company name: {searched_company_name}")
        for company_block in search_result:
            found_company_block_text = company_block.text.strip()
            if USABusinessOwnersScraper.compare_found_block_text_with_searched(found_company_block_text, searched_company_name):
                logging.debug(f"FOUND a proper company block for searched company name: {searched_company_name}"
                             f"\nFound company block: {company_block.text.strip()}")
                return USABusinessOwnersScraper.extract_link_from_company_block(company_block)

        logging.exception(f"No matching company block is found for a searched company, named: {searched_company_name}"
                     f"\nReturning None...")
        return None

    def extract_business_owners_from_company_link(self, proper_company_link: WebElement) -> USABusinessOwners:
        if proper_company_link is None:
            return USABusinessOwnersScraper.empty_owners

        logging.debug(f"Clicking on a proper company link..."
                     f"\nProper company link: {proper_company_link.text.strip()}")
        proper_company_link.click()
        time.sleep(5)

        try:
            logging.debug("Looking for business owners blocks...")
            owners_blocks = self.driver.find_elements(By.CLASS_NAME, "attribute_item")
            logging.debug("Looking for business owners blocks is successfully FINISHED")
        except NoSuchElementException:
            logging.exception("Couldn't find any business owners blocks...\nReturning empty owners...")
            return USABusinessOwnersScraper.empty_owners

        owners_data = ""

        logging.debug("Scrapping the business owners data from business owners blocks...")
        for owner_block in owners_blocks:
            owners_data = owner_block.text.strip() if owners_data == "" \
                else owners_data + f"\n{owner_block.text.strip()}"
        logging.debug("Scrapping the business owners data from business owners blocks is FINISHED.")

        owners_data = re.sub(r'\d+', '', owners_data).strip()

        return USABusinessOwners(owners_data)

    def scrape_the_owners(self, searched_company_name) -> USABusinessOwners:
        USABusinessOwnersScraper.initialize_tools_if_not_yet_initialized()

        logging.debug(f"Creating a search url, based on company name... Company name: {searched_company_name}")

        created_search_url = self.search_url(searched_company_name)

        logging.debug(f"Creating a search url for: {searched_company_name} is FINISHED."
                     f"\n Created url: {created_search_url}")

        self.driver.get(created_search_url)
        time.sleep(5)

        try:
            logging.debug(f"Looking for company blocks by created search url...\nSearch url: {created_search_url}")
            search_result = self.driver.find_elements(By.CLASS_NAME, "company")
            logging.debug(f"Looking for company blocks by created search url is successfully FINISHED."
                         f"\nSearch url: {created_search_url}")
        except NoSuchElementException:
            logging.exception(f"Did not find company blocks by created search url.\nSearch url: {created_search_url}")
            return USABusinessOwnersScraper.empty_owners

        proper_company_link = (USABusinessOwnersScraper
                               .find_proper_company_link_from_search_result(search_result, searched_company_name))

        return self.extract_business_owners_from_company_link(proper_company_link)

