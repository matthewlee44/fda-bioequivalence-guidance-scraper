# All code in this file written by Henry Chu (henrymchu)

# Standard Python imports
import collections
import datetime
import os
import string
import sys

# Third Party imports
import requests
import pandas

# Constants
PSG_GENERIC_DRUG_DEVELOPMENT_URL = \
    'https://www.fda.gov/drugs/guidances-drugs/product-specific-guidances-generic-drug-development'

PSG_WITH_LETTER_URL_FORMATTER = \
    'https://www.accessdata.fda.gov/scripts/cder/psg/index.cfm?event=Home.Letter&searchLetter={letter}#letterSearchBar'

PDF_URL_KEY = 'URL'
RLD_KEY = 'RLD or RS Number'
DATE_RECOMMENDED_KEY = 'Date Recommended'


def main():
    # Set up a working directory where downloaded PDFs will be saved
    directory_name = create_output_directory()

    # Read in input RLD file
    if len(sys.argv) < 2:
        print('An input RLD identifiers file is required to use this script.')
        return
    rld_search_numbers = get_rld_search_numbers()

    # Identify the "content current as of" year and month
    current_year, current_month = get_content_current_year_and_month()
    if current_year is None or current_month is None:
        raise Exception('Could not identify content current year and month.')

    current_updated_date = datetime.date(year=current_year, month=current_month, day=1)
    print('Content current year: {}'.format(current_year))
    print('Content current month: {}'.format(current_month))

    # Set up a variable to see if we have already downloaded a PDF for a specific RLD
    downloaded_rld_pdfs = collections.defaultdict(bool)
    rld_type_counter = collections.defaultdict(int)
    rld_type_lists = collections.defaultdict(list)

    # Retrieve all of the active ingredients and put them into a list
    active_ingredients = []
    for letter in string.ascii_uppercase:
        print('Looking at active ingredients beginning with {}'.format(letter))
        psg_tables = pandas.io.html.read_html(io=PSG_WITH_LETTER_URL_FORMATTER.format(letter=letter),
                                              attrs={'class': 'drugTable'})

        for psg_table in psg_tables:
            active_ingredients += psg_table.to_dict('records')

    # Download PDFs for active ingredients that have been recently updated
    for active_ingredient in active_ingredients:
        is_of_interest, rld_type = \
            ai_is_of_interest(active_ingredient=active_ingredient, current_content_updated_date=current_updated_date,
                              rld_search_numbers=rld_search_numbers)

        rld_type_counter[rld_type] += 1
        rld_type_lists[rld_type].append(active_ingredient.get(RLD_KEY))

        if is_of_interest:
            download_specific_guidance_pdf(active_ingredient=active_ingredient, write_directory=directory_name,
                                           downloaded_rld_pdfs=downloaded_rld_pdfs)

    print('\nRLD int count: {}'.format(rld_type_counter['int']))
    print('RLD string count: {}'.format(rld_type_counter['str']))
    print('RLD other count: {}'.format(rld_type_counter['other']))

    print('\nRLD int list: {}'.format(rld_type_lists['int']))
    print('\nRLD string list: {}'.format(rld_type_lists['str']))
    print('RLD other list: {}'.format(rld_type_lists['other']))


def create_output_directory():
    """Creates an output directory to save NDA PDF files to.

    Returns:
        directory_name: str

    Notes:
        1. This method will create a new directory in the location of this script.
        2. The format of the directory name will be YYYY-MM-DD-run-{INT}.
        3. If YYYY-MM-DD-run-1 is already an existing directory, YYYY-MM-DD-run-2 will be created.
    """
    today = datetime.date.today()
    year = today.year
    month = today.month
    day = today.day
    run_number = 1

    directory_name = '{}-{:02d}-{:02d}-run-1'.format(year, month, day)
    if not os.path.isdir(directory_name):
        os.mkdir(directory_name)
    else:
        while os.path.isdir(directory_name):
            run_number += 1
            directory_name = '{}-{:02d}-{:02d}-run-{}'.format(year, month, day, run_number)
        os.mkdir(directory_name)

    print('Created working directory: {}'.format(directory_name))
    return directory_name


def get_rld_search_numbers():
    """Retrieves list of RLD numbers from input text file.

    Returns:
        rld_search_numbers: list of str
    """
    rld_file_name = sys.argv[1]
    rld_search_numbers = []
    with open(rld_file_name, 'r') as fp:
        for line in fp.readlines():
            rld_search_numbers.append(line.strip())
    return rld_search_numbers


def get_content_current_year_and_month():
    """Identifies the content current year and month from product guidance web page.

    Returns:
        year: int
        month: int

    Notes:
        1. This method relies on the website have a very specific structure.  If the
           website changes the method may start to always return None, None.
    """
    response = requests.get(PSG_GENERIC_DRUG_DEVELOPMENT_URL)
    resp_text = response.text
    year = month = None

    try:
        chunks_part_1 = resp_text.split('Content current as of')
        chunks_part_2 = chunks_part_1[1].split('</time>')
        chunks_part_3 = chunks_part_2[0].split('">')
        chunks_part_4 = chunks_part_3[1].split('="')
        iso_datetime = chunks_part_4[1]
        year_month_day_and_time = iso_datetime.split('T')
        year, month, _ = year_month_day_and_time[0].split('-')
        year = int(year)
        month = int(month)
    except ValueError:
        print('Failed to get content current year and month')
    except IndexError:
        print('Failed to get content current year and month')

    return year, month


def ai_is_of_interest(active_ingredient, current_content_updated_date, rld_search_numbers):
    """Identifies if an active ingredient is of interest for specific guidance PDF download.

    Args:
        :param active_ingredient: dict
        :param current_content_updated_date: datetime.date
        :param rld_search_numbers: list or str

    Returns:
        is_of_interest: bool
        rld_arg_type: str
    """
    is_of_interest = False
    rld_values = []
    rld_value = active_ingredient.get(RLD_KEY)

    # RLD values maybe a single number value or multiple numbers separated by spaces
    if isinstance(rld_value, int):
        rld_arg_type = 'int'
    elif isinstance(rld_value, str):
        rld_arg_type = 'str'
    else:
        rld_arg_type = 'other'

    if isinstance(rld_value, str) and ' ' in rld_value:
        for rld in rld_value.split(' '):
            cleaned_rld = rld.strip()
            rld_values.append(cleaned_rld)
    else:
        rld_values = [str(rld_value)]

    for rld_value in rld_values:
        if rld_value in rld_search_numbers:
            is_of_interest = True

    if is_of_interest is False:
        return is_of_interest, rld_arg_type

    unparsed_month_year = active_ingredient.get(DATE_RECOMMENDED_KEY)
    month, year = unparsed_month_year.split('/')
    ai_updated_date = datetime.date(year=int(year), month=int(month), day=1)
    if ai_updated_date >= current_content_updated_date:
        is_of_interest = True

    return is_of_interest, rld_arg_type


def download_specific_guidance_pdf(active_ingredient, write_directory, downloaded_rld_pdfs):
    """Saves a single active ingredient specific guidance PDF file.

    Args:
        :param active_ingredient: dict
        :param write_directory: str
        :param downloaded_rld_pdfs: collections.defaultdict

    Notes:
        1. A PDF file will be downloaded and saved in the directory specified.
    """
    rld_value = active_ingredient.get(RLD_KEY)
    if downloaded_rld_pdfs[rld_value] is False:
        pdf_url = active_ingredient.get(PDF_URL_KEY)
        filename = pdf_url.split('/')[-1]
        response = requests.get(active_ingredient.get(PDF_URL_KEY))
        with open('{}/{}'.format(write_directory, filename), 'wb') as f:
            f.write(response.content)
        downloaded_rld_pdfs[rld_value] = True
        print('Created {0}/{1} PDF file'.format(write_directory, filename))


if __name__ == '__main__':
    main()
