# Most of the code here as noted below is adopted from the find_updated_ai.py file written by Henry Chu
# It's been copied into this file because it's useful for tasks outside of that file

# Python imports
import os
import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# Constants (from find_updated_ai.py)
PSG_GENERIC_DRUG_DEVELOPMENT_URL = \
    'https://www.fda.gov/drugs/guidances-drugs/product-specific-guidances-generic-drug-development'

PSG_WITH_LETTER_URL_FORMATTER = \
    'https://www.accessdata.fda.gov/scripts/cder/psg/index.cfm?event=Home.Letter&searchLetter={letter}#letterSearchBar'

PDF_URL_KEY = 'URL'
RLD_KEY = 'RLD or RS Number'
DATE_RECOMMENDED_KEY = 'Date Recommended'

# From find_updated_ai.py
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


# Adapted from code in find_updated_ai.py
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

# Code from initial project files refactored out into its own function -- download_single_pdf
#        filename = pdf_url.split('/')[-1]
#        response = requests.get(active_ingredient.get(PDF_URL_KEY))
#        with open('{}/{}'.format(write_directory, filename), 'wb') as f:
#            f.write(response.content)

# New code calling the function that was created from prior code
        download_single_pdf(pdf_url, write_directory)

        downloaded_rld_pdfs[rld_value] = True
        print('Created {0}/{1} PDF file'.format(write_directory, filename))


def download_single_pdf(url, write_directory):
    """Saves a single PDF file given a url and the name of the directory to write to.

    Args:
        :param url: str
        :param write_directory: str

    Notes:
        1. A PDF file will be downloaded and saved in the directory specified.
    """
    # Get requests session with retry capability
    http = http_session()

    # Pull filename from url
    filename = url.split('/')[-1]

    # Make http request
    # Code from: https://www.nylas.com/blog/use-python-requests-module-rest-apis/#handle-errors-with-python-requests
    try:
        response = http.get(url, timeout=5)
        # Write pdf to file if request successful
        with open('{}/{}'.format(write_directory, filename), 'wb') as f:
            print(f"Writing to file: {write_directory}/{filename}")
            f.write(response.content)
    except requests.exceptions.HTTPError as errh:
        print(errh)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
    except requests.exceptions.Timeout as errt:
        print(errt)
    except requests.exceptions.RequestException as err:
        print(err)



# Code adapted from: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
def http_session():
    # Instantiate an adapter with Retry object
    adapter = HTTPAdapter(max_retries=Retry(total = 5, backoff_factor=1))

    # Instantiate session
    http = requests.Session()

    # Add hook raising an exception for certain HTTP response codes
    assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
    http.hooks["response"] = [assert_status_hook]

    # Mount sessions with adapter
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    # Return session
    return http