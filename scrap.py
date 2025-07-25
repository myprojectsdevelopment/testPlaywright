from playwright.sync_api import sync_playwright
import json
import re
import os
from pathlib import Path
import time

def scrape_icapital_jobs(url="https://icapital.com/careers/"):
    """
    Navigates to the iCapital Careers page, applies specified filters by simulating UI clicks
    using option index, and extracts job title, location, and full role description into a JSON output.
    Includes fallback methods for applying filters.
    """
    job_data = []

    current_script_dir = Path(__file__).parent
    user_data_dir = current_script_dir / "playwright_user_data"
    user_data_dir.mkdir(parents=True, exist_ok=True) # Create the directory if it doesn't exist

    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False # KEEP THIS AS False FOR NOW TO DEBUG
        )
        page = browser_context.new_page()

        print(f"Navigating to: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_load_state('networkidle')
            print("Page loaded successfully.")
            time.sleep(1) # Small delay to ensure initial rendering is complete
        except Exception as e:
            print(f"Error navigating to the page: {e}")
            browser_context.close()
            return json.dumps({"error": f"Failed to load page: {e}"}, indent=4)

        # --- Attempt to handle cookie consent or other overlays (if any) ---
        print("Checking for and dismissing overlays...")
        try:
            accept_button_selectors = [
                'button[data-tag="accept-button"]',
                'button:has-text("Accept All")',
                'button:has-text("Accept Cookies")',
                'button[aria-label="Accept cookies"]',
                '#onetrust-accept-btn-handler',
                '.cc-btn.cc-allow',
                'button[data-qa="accept-cookies"]',
                'div[role="dialog"] button:has-text("Accept")',
                'div[role="dialog"] button:has-text("Got it")',
                'div[role="dialog"] button:has-text("Agree")'
            ]
            for selector in accept_button_selectors:
                locator = page.locator(selector)
                if locator.is_visible():
                    print(f"  - Found potential overlay button: {selector}. Attempting to click...")
                    try:
                        locator.click(timeout=5000)
                        page.wait_for_load_state('networkidle')
                        print("  - Overlay dismissed (hopefully).")
                        break
                    except Exception as click_e:
                        print(f"  - Failed to click overlay button '{selector}': {click_e}. Trying next selector.")
        except Exception as e:
            print(f"  - No immediate overlay found or failed to dismiss: {e}")
        
        time.sleep(1) # Small pause after dismissing overlay, allowing filters to render if hidden by overlay

        # --- Define select_bootstrap_option_by_index function (nested for scope) ---
        def select_bootstrap_option_by_index(select_id, option_index, expected_label=None):
            if not (0 <= option_index <= 99):
                raise ValueError(f"Option index {option_index} is outside the allowed range of 0 to 99.")

            dropdown_button_selector = f'button[data-id="{select_id}"]'
            print(f"  - Clicking dropdown button for '{select_id}'...")
            
            button_locator = page.locator(dropdown_button_selector)
            clicked_successfully = False

            # --- Method 1: Standard Playwright Click with Scrolling ---
            print(f"    Attempting Method 1 (Standard Click with Scrolling) for '{select_id}'...")
            try:
                button_locator.scroll_into_view_if_needed()
                page.evaluate("window.scrollBy(0, 100);") # Scroll down for sticky headers
                time.sleep(0.5) # Give scroll time
                button_locator.wait_for(state='visible', timeout=5000)
                button_locator.wait_for(state='enabled', timeout=5000)
                button_locator.click(timeout=5000)
                clicked_successfully = True
                print(f"    Method 1 successful for '{select_id}'.")
            except Exception as e:
                print(f"    Method 1 failed for '{select_id}': {e}")
            
            if not clicked_successfully:
                # --- Method 2: JavaScript Click ---
                print(f"    Attempting Method 2 (JavaScript Click) for '{select_id}'...")
                try:
                    page.evaluate(f'document.querySelector("{dropdown_button_selector}").click()')
                    clicked_successfully = True
                    print(f"    Method 2 successful for '{select_id}'.")
                except Exception as e_js:
                    print(f"    Method 2 failed for '{select_id}': {e_js}")

            if not clicked_successfully:
                # --- Method 3: Force Click ---
                print(f"    Attempting Method 3 (Force Click) for '{select_id}'...")
                try:
                    button_locator.click(force=True, timeout=5000) # Force click
                    clicked_successfully = True
                    print(f"    Method 3 successful for '{select_id}'.")
                except Exception as e_force:
                    print(f"    Method 3 failed for '{select_id}': {e_force}")

            if not clicked_successfully:
                # --- Method 4: Coordinate Click (Last Resort) ---
                print(f"    Attempting Method 4 (Coordinate Click) for '{select_id}'...")
                try:
                    bbox = button_locator.bounding_box()
                    if bbox:
                        page.mouse.click(bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2)
                        clicked_successfully = True
                        print(f"    Method 4 successful for '{select_id}'.")
                    else:
                        raise Exception("Could not get bounding box for coordinate click.")
                except Exception as e_coord:
                    print(f"    Method 4 failed for '{select_id}': {e_coord}")

            if not clicked_successfully:
                raise Exception(f"All click methods failed for '{select_id}' dropdown button.")

            # After a successful click (by any method), verify dropdown opens
            try:
                page.wait_for_selector(f'div.inner.open', state='visible', timeout=10000)
                print(f"  - Dropdown for '{select_id}' opened after trying click methods.")
            except Exception as e:
                raise Exception(f"Dropdown for '{select_id}' did not open after button click: {e}")

            option_list_selector = f'div.inner.open ul.dropdown-menu.inner li'
            all_options = page.locator(option_list_selector).all()

            if option_index >= len(all_options) or option_index < 0:
                raise IndexError(f"Option index {option_index} out of bounds for '{select_id}' dropdown (has {len(all_options)} options).")

            target_option_locator = all_options[option_index].locator('a')

            current_label = target_option_locator.text_content().strip()
            if expected_label and current_label != expected_label.strip():
                print(f"  Warning: Expected label '{expected_label}' at index {option_index} but found '{current_label}' for '{select_id}'. Proceeding with index anyway.")

            print(f"  - Attempting to select index {option_index} ('{current_label}') within '{select_id}'...")
            try:
                target_option_locator.scroll_into_view_if_needed()
                target_option_locator.wait_for(state='visible', timeout=10000)
                target_option_locator.click(timeout=10000)
                print(f"  - Selected index {option_index} ('{current_label}') for '{select_id}'.")
                page.wait_for_load_state('networkidle', timeout=15000)
            except Exception as e:
                raise Exception(f"Failed to select option at index {option_index} for '{select_id}': {e}")
        # --- End of select_bootstrap_option_by_index function ---


        # --- Main Filter Application Logic ---
        filters_applied_successfully = False

        # --- Try Method A: Apply Filters via UI Interaction ---
        print("\n--- Attempting Method A: Apply Filters via UI Interaction ---")
        try:
            # Ensure filter elements are visible before attempting UI clicks
            page.wait_for_selector('div.filter-box', state='visible', timeout=20000)
            print("Filter box is visible. Now waiting for specific filter buttons.")
            page.wait_for_selector('button[data-id="filter_dep"]', state='visible', timeout=20000)
            print("Department filter button is visible.")

            select_bootstrap_option_by_index('filter_dep', 0, 'All Departments')
            select_bootstrap_option_by_index('filter_office', 1, 'CA ON - Toronto')
            select_bootstrap_option_by_index('filter_emp_type', 1, 'Full-time')

            page.wait_for_selector('div.all_jobs', state='visible', timeout=15000)
            print("Filters applied via UI. Waiting for job listings to update...")
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check for jobs or no jobs after UI filtering
            try:
                page.wait_for_selector('div.job:visible', state='visible', timeout=15000)
            except Exception:
                if page.locator('div.nojob:visible').count() > 0:
                    print("No job listings found for the applied filters (via UI).")
                else:
                    raise # Re-raise if neither job nor nojob found

            page.wait_for_load_state('networkidle', timeout=15000)
            print("Job listings updated via UI and ready for scraping.")
            filters_applied_successfully = True

        except Exception as e:
            print(f"Method A (UI interaction) failed: {e}")
            print("\n--- Attempting Method B: Direct URL Navigation (Fallback) ---")
            
            direct_filtered_url = "https://icapital.com/careers/?office=CA%20ON%20-%20Toronto&emp_type=Full-time"
            try:
                print(f"Navigating directly to: {direct_filtered_url}")
                page.goto(direct_filtered_url, wait_until="domcontentloaded")
                page.wait_for_load_state('networkidle')
                print("Direct filtered URL loaded successfully.")

                # Check for job listings after direct navigation
                page.wait_for_selector('div.all_jobs', state='visible', timeout=15000)
                print("Direct URL: Job container visible. Checking for jobs...")
                page.wait_for_load_state('networkidle', timeout=15000)
                
                try:
                    page.wait_for_selector('div.job:visible', state='visible', timeout=15000)
                except Exception:
                    if page.locator('div.nojob:visible').count() > 0:
                        print("Direct URL: No job listings found for the filters in the URL.")
                        filters_applied_successfully = True # Filtering was successful, even if 0 jobs
                    else:
                        raise # Re-raise if neither job nor nojob found, indicating a deeper issue with URL loading
                
                if not page.locator('div.nojob:visible').count() > 0: # Only set true if actual jobs found or nojob not present
                    print("Direct URL: Job listings found and ready for scraping.")
                    filters_applied_successfully = True

            except Exception as direct_e:
                print(f"Method B (Direct URL Navigation) failed: {direct_e}")
                browser_context.close()
                return json.dumps({"error": f"Failed to apply filters using any method (UI or Direct URL). Last error: {direct_e}"}, indent=4)

        # If filters were not applied successfully by any method, exit.
        if not filters_applied_successfully:
             browser_context.close()
             return json.dumps({"error": "Failed to apply filters using any method. Check logs for details."}, indent=4)


        # --- Extract Data ---
        print("\nExtracting job data...")
        job_elements = page.locator('div.job:visible').all()

        if not job_elements:
            print("No visible job listings found after applying filters.")
        else:
            print(f"Found {len(job_elements)} visible job listings.")

        for i, job_element in enumerate(job_elements):
            try:
                job_title_locator = job_element.locator('h2.job_title')
                job_title = job_title_locator.text_content().strip()

                location_locator = job_element.locator('div.display_location')
                location_text = location_locator.text_content().strip()
                location = re.sub(r'\s+', ' ', location_text.replace('Location:', '').strip()).strip()

                role_description = "N/A (Could not extract or link not found)"

                read_full_description_link = job_element.locator('a.job_read_full')

                if read_full_description_link.is_visible() and read_full_description_link.is_enabled():
                    try:
                        read_full_description_link.click()
                        job_description_content_locator = job_element.locator('div.job_description div.display_description')
                        job_description_content_locator.wait_for(state='visible', timeout=5000)
                        role_description = job_description_content_locator.text_content().strip()
                        role_description = re.sub(r'\s+', ' ', role_description).strip()
                        read_full_description_link.click()
                        job_description_content_locator.wait_for(state='hidden', timeout=5000)

                    except Exception as desc_e:
                        print(f"  Warning: Could not click 'Read Full Description' or extract description for '{job_title}': {desc_e}")
                        role_description = "N/A (Error extracting full description)"
                else:
                    try:
                        job_description_content_locator = job_element.locator('div.job_description div.display_description:visible')
                        if job_description_content_locator.count() > 0:
                             role_description = job_description_content_locator.text_content().strip()
                             role_description = re.sub(r'\s+', ' ', role_description).strip()
                    except Exception:
                        pass

                job_data.append({
                    "Job title": job_title,
                    "Location": location,
                    "Role description": role_description
                })
                print(f"  - Extracted: '{job_title}' at '{location}'")

            except Exception as e:
                print(f"  Error extracting data from job listing {i+1}: {e}")
                job_data.append({
                    "Job title": "Error: Could not extract",
                    "Location": "Error: Could not extract",
                    "Role description": f"Error: {e}"
                })

        browser_context.close()
    return json.dumps(job_data, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    output_json = scrape_icapital_jobs()
    print("\n--- Final JSON Output ---")
    print(output_json)

    file_name = "icapital_filtered_jobs.json"
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(output_json)
    print(f"\nData saved to {file_name}")