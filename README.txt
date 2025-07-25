README.txt
=========================================

Project: iCapital Careers Page Web Scraper
Role: Data Analyst (Python Web Scraping) Assessment

Overview:
---------
This Python script automates the extraction of job listings from the iCapital careers page (https://icapital.com/careers/). It is designed to apply specific filters (Department: All Departments, Office: CA ON - Toronto, Employment Type: Full-time) and then collect the Job Title, Location, and Full Role Description for each matching job. The script outputs the extracted data into a JSON file.

Prerequisites:
--------------
To run this script, you need:
1.  **Python 3.x** installed on your system.
2.  **Playwright Python library:** Install it using pip:
    ```bash
    pip install playwright
    ```
3.  **Playwright browser binaries:** After installing the library, install the necessary browser binaries (Chromium, Firefox, WebKit) for Playwright:
    ```bash
    playwright install
    ```

How to Run the Script:
----------------------
1.  Save the provided Python code as `scrap.py` (or any other `.py` filename).
2.  Open your terminal or command prompt.
3.  Navigate to the directory where you saved `scrap.py`.
4.  Run the script using the command:
    ```bash
    python scrap.py
    ```
5.  The script will print progress messages to the console. Upon completion, the extracted job data will be printed to the console and saved in a file named `icapital_filtered_jobs.json` in the same directory.

Filtering Logic:
----------------
The script attempts to apply filters using a multi-pronged approach to ensure robustness:

1.  **UI Interaction (Primary Method - Methods 1-4):**
    * The script first tries to simulate human clicks on the `selectpicker` dropdowns for "Department," "Offices," and "Employment Type."
    * It uses **index-based selection** (e.g., Department: index 0, Offices: index 1, Employment Type: index 1) to select the desired options, as the underlying `value` attributes are non-human-readable internal IDs.
    * A robust clicking strategy is employed, attempting four different methods sequentially if one fails:
        * **Method 1 (Standard Playwright Click with Scrolling):** Playwright's default click, enhanced with scrolling to avoid sticky header obstructions.
        * **Method 2 (JavaScript Click):** Direct JavaScript execution to trigger the click.
        * **Method 3 (Force Click):** Playwright attempts the click even if actionability checks (e.g., element obscured) fail.
        * **Method 4 (Coordinate Click):** Clicks at calculated pixel coordinates as a last resort.

2.  **Direct URL Navigation (Fallback Method - Method B):**
    * If all UI interaction methods (Methods 1-4) fail to successfully apply the filters, the script falls back to directly navigating to a pre-constructed URL: `https://icapital.com/careers/?office=CA%20ON%20-%20Toronto&emp_type=Full-time`.
    * This method bypasses all UI interaction for filtering and relies on the website's ability to process filters directly via URL parameters.

Challenges Encountered & Addressed:
-----------------------------------
Developing this scraper involved overcoming several common web scraping challenges:

* **UI Element Obstruction:** A persistent header/menu often covered filter dropdowns. This was addressed by programmatically scrolling the page to ensure elements were clear before clicking.
* **Cookie Consent Banner:** A cookie banner appeared on page load, blocking interactions and causing "strict mode violation" errors due to ambiguous selectors. This was resolved by implementing specific selectors and a robust attempt to click and dismiss the banner.
* **Dynamic Content & Actionability:** The website's dynamic nature required careful waiting for elements to be fully loaded, visible, and interactive before attempting clicks or data extraction.
* **Flaky UI Interactions:** The `selectpicker` library's custom UI could be inconsistent. This led to the multi-method clicking strategy (Methods 1-4) to ensure that even if one click approach failed, others would be attempted.
* **Bot Detection Considerations:** Throughout development, care was taken to consider how each interaction method might appear to bot detection systems. The multi-method approach prioritizes human-like interactions (Method 1) and only escalates to riskier, less human-like methods (JS click, force click, coordinate click) if necessary. The direct URL navigation (Method B) serves as a highly robust fallback, acknowledging its different bot detection profile.

Output Format:
--------------
The script produces a JSON array of objects, where each object represents a job listing with the following keys:
* `Job title`: The title of the job.
* `Location`: The geographical location of the job.
* `Role description`: The full description of the job role.

Example Output Structure:
```json
[
  {
    "Job title": "Example Job Title 1",
    "Location": "CA ON - Toronto",
    "Role description": "This is the full description for job 1..."
  },
  {
    "Job title": "Example Job Title 2",
    "Location": "CA ON - Toronto",
    "Role description": "This is the full description for job 2..."
  }
]

Contact:
For any questions or further clarification, please feel free to contact Gregory Buna at gregorybuna@gmail.com.

================