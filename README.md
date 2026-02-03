# Oakland RAP Scraper and Data Cleaning Pipeline

This project provides a two-step data pipeline to scrape Rent Adjustment Program (RAP) data from the Oakland website and then clean and harmonize the scraped data.

## Project Structure

The project is organized into the following directories:

*   `01-scraper/`: Contains the web scraping script (`rap_scrape.py`).
*   `02-cleaning/`: Contains the data cleaning and harmonization script (`clean_data.py`).
*   `codebooks/`: Stores CSV files used for data harmonization (e.g., `tenant_codebook.csv`, `landlord_codebook.csv`).
*   `data/raw/`: Where the raw, scraped data is saved.
*   `data/cleaned/`: Where the cleaned and harmonized data is saved.

## Setup

This project uses `poetry` for dependency management.

1.  **Install Poetry (if you haven't already):**
    ```bash
    pip install poetry
    ```
2.  **Install Project Dependencies:**
    Navigate to the project's root directory and run:
    ```bash
    poetry install
    ```
3.  **Install ChromeDriver:**
    The scraper uses Selenium, which requires a ChromeDriver executable. Ensure you have a ChromeDriver version compatible with your Chrome browser installed and accessible in your system's PATH, or specify its location in `01-scraper/rap_scrape.py`.

## Usage

### Step 1: Run the Scraper

The scraper (`01-scraper/rap_scrape.py`) navigates the Oakland RAP website and extracts raw case data.

To run the scraper:

1.  **Open `01-scraper/rap_scrape.py`** in a text editor.
2.  **Adjust the `start_date` and `end_date` variables** to define the scraping period.
    ```python
    start_date = '01-01-2025' # Example: January 1, 2025
    end_date = '11-01-2025'   # Example: November 1, 2025
    ```
3.  **Execute the script** from the project's root directory:
    ```bash
    poetry run python 01-scraper/rap_scrape.py
    ```
    The raw data will be saved as a CSV file in the `data/raw/` directory (e.g., `data_01012025_11012025.csv`).

### Step 2: Run the Data Cleaner

The cleaning script (`02-cleaning/clean_data.py`) processes the raw data, harmonizes it, and saves a cleaned version.

**To clean the latest scraped file (default behavior):**

Simply run the script from the project's root directory:

```bash
poetry run python 02-cleaning/clean_data.py
```

The script will automatically identify the most recently created raw data file in `data/raw/` and process it.

**To clean a specific file:**

You can specify an input file using the `--file` argument:

```bash
poetry run python 02-cleaning/clean_data.py --file ./data/raw/data_01012010_12312014.csv
```

Replace `./data/raw/data_01012010_12312014.csv` with the actual path to the raw data file you wish to clean.

The cleaned data will be saved as a CSV file in the `data/cleaned/` directory (e.g., `cleaned_data_01012025_11012025.csv`).

## Troubleshooting

*   **`selenium.common.exceptions.InvalidSessionIdException`**: This error often occurs if the browser window controlled by Selenium is closed unexpectedly, or if the computer goes to sleep during a long scrape. The scraper is designed to catch this and save any data scraped up to that point. You may need to restart the scrape.
*   **`selenium.common.exceptions.NoSuchElementException`**: This error can appear in the logs when the scraper attempts to find an element (like a "Landlord Grounds" table) that is not present on a particular case's detail page. This is often expected behavior, as not all cases will have all possible data fields. The script is designed to handle these cases gracefully by recording `NaN` for missing data.
*   **`petition_number` type**: The `petition_number` is extracted as a string to preserve any leading zeros or non-numeric characters. The cleaning script ensures it remains a string type.
