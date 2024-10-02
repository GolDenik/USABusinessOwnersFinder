import logging
import pandas as pd
from services.usa_business_owners_scraper import USABusinessOwnersScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_excel(file_path):
    """Reads an Excel file into a pandas DataFrame."""
    return pd.read_excel(file_path)


def find_business_owners_data(usa_company_name) -> str:
    """Processes a business name and returns some information."""
    # Replace this with actual processing logic
    logging.info(f"Scrapping the owners for the company, named: {usa_company_name}...")
    business_owners_data = USABusinessOwnersScraper().scrape_the_owners(usa_company_name).data
    logging.info(f"Scrapping the owners for the company, named: {usa_company_name} - FINISHED")
    return business_owners_data


def fill_in_business_owners_data(df):
    """Processes the DataFrame and adds a new column with processed information."""
    df['Contact Name'] = df['Business Name'].apply(find_business_owners_data)
    return df


def save_to_excel(df, output_file_path):
    """Saves the DataFrame to an Excel file."""
    df.to_excel(output_file_path, index=False)


def main():
    # File paths
    input_file_path = 'companies.xlsx'
    output_file_path = 'updated-companies.xlsx'

    # Read the Excel file
    logging.info(f"Reading Excel file... File path: {input_file_path}")
    df = read_excel(input_file_path)
    logging.info("Reading Excel file - FINISHED")

    # Prepare the Scrapper
    currently_scrapped_states = ["Illinois"]
    logging.info(f"Preparing the Scrapper... Currently Scrapped States: {currently_scrapped_states}")
    USABusinessOwnersScraper.set_currently_scrapped_state(currently_scrapped_states)
    logging.info("Preparing the Scrapper - FINISHED")

    # Process the data
    logging.info("Filling the business owners data...")
    df = fill_in_business_owners_data(df)
    logging.info("Filling the business owners data - FINISHED")

    # Save the processed data to a new Excel file
    logging.info(f"Saving the processed data to a new Excel file... File path: {output_file_path}")
    save_to_excel(df, output_file_path)
    logging.info("Saving the processed data to a new Excel file - FINISHED")

    print("Processing completed. Check the output file.")


if __name__ == "__main__":
    main()

