# Import python libraries
import string
import pandas

# Import constants and functions common to the project
from common import PDF_URL_KEY, PSG_GENERIC_DRUG_DEVELOPMENT_URL, PSG_WITH_LETTER_URL_FORMATTER, create_output_directory, download_single_pdf

# Code adapted from main code in find_updated_ais.py
def main():
    # Set up a working directory where downloaded PDFs will be saved
    directory_name = create_output_directory()

    # Retrieve all of the active ingredients and put them into a list
    active_ingredients = []
    for letter in string.ascii_uppercase:
        print('Looking at active ingredients beginning with {}'.format(letter))
        # Read in all HTML tables with the class drugTable
        psg_tables = pandas.io.html.read_html(io=PSG_WITH_LETTER_URL_FORMATTER.format(letter=letter),
                                              attrs={'class': 'drugTable'})

        # Add first HTML table on letter search page to list (contains all of the active ingredients for that search letter)
        active_ingredients += psg_tables[0].to_dict('records')

    # Download PDFs for active ingredients that have been recently updated
    for active_ingredient in active_ingredients:
        url = active_ingredient.get(PDF_URL_KEY)
        print(f"Downloading from {url}")
        download_single_pdf(url, write_directory=directory_name)

if __name__ == '__main__':
    main()
