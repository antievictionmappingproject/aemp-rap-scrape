from datetime import date
import time
import numpy as np
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Confines the scrape to the input date range.
# Smaller date ranges improve performance; this website is extremely laggy.
def SetContext(driver, # a selenium webdriver instance
               start_date, # a string, in "mm-dd-yyyy" format
               end_date):  # a string, in "mm-dd-yyyy" format
    
    # clear the start date field and input the new value
    start_xp = """//input[@placeholder='Start Date']"""
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, start_xp))).clear()
    driver.find_element(By.XPATH, start_xp).send_keys(start_date)

    # clear the end date field and input the new value
    end_xp = """//input[@placeholder='End Date']"""
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, end_xp))).clear()
    driver.find_element(By.XPATH, end_xp).send_keys(end_date)

    
def ParseTable(driver, table_xpath):
    """
    Parses a table and returns a list of dictionaries, where each dictionary represents a row.
    """
    table_data = []
    try:
        table = driver.find_element(By.XPATH, table_xpath)
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 0:
                row_data = {}
                for i, cell in enumerate(cells):
                    row_data[f"col_{i+1}"] = cell.text
                table_data.append(row_data)
    except Exception as e:
        print(f"Error parsing table with XPath {table_xpath}: {e}")
    return table_data


# Iterates through the 25 entries displayed on a given page of the database, fetching data for each.
# Returns the scraped data in a pandas dataframe.
def ParsePage(driver, # a selenium webdriver instance
              xpath_dict): # a dictionary of column shortnames and xpath strings corresponding to the associated data
    
    # the entries use the same base xpath, with variations in the 2-digit number following '_ctl,' which ranges from 03-28
    raw_selector = """//*[@id="wt89_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_wtCaseDataTable_ctl{}_wt171"]"""
    entries = ['0' + s if len(s) == 1 else s for s in [str(s) for s in np.arange(3,28,1)]]
    entries = [raw_selector.format(s) for s in entries]
        
    # define a dictionary in which to house the raw data
    raw_data = {}
    for item in xpath_dict.keys(): # for each of the column names
        raw_data[item] = [] # assign an empty list

    # for each of entry links
    for ct, entry in enumerate(entries):
        print(f"Attempting to process entry {ct+1} with XPath: {entry}")
        try: # when there's a clickable entry
            element = driver.find_element(By.XPATH, entry)
            driver.execute_script("arguments[0].click();", element) # click it
            print('entry {}'.format(ct))
        except:
            return pd.DataFrame(raw_data) # when there's not, it means there are fewer than 25 on the page, which means we should just return what we've got

        # after clicking the link
        for item in xpath_dict.keys():
            if item in ["grounds_tenant", "grounds_landlord", "case_progress"]:
                table_data = ParseTable(driver, xpath_dict[item])
                raw_data[item].append(table_data)
                print(f"{item}: {table_data}")
            else:
                try: # when the element exists
                     # (they don't always, btw –– there aren't landlord excuses in tenant complaints or tenant problem descriptions in landlord filings)
                    element = driver.find_element(By.XPATH, xpath_dict[item]).text # retrieve the text
                    print(f"{item}: {element}") # print it so you can see what's going on in the terminal if something breaks
                    raw_data[item].append(element) # and append it to the dictionary
                except: # when it doesn't exist
                    raw_data[item].append(np.nan) # return a nan

        driver.back() # go back in the browser – this method of navigation saves our place in the pages
        
    return pd.DataFrame(raw_data) # when done iterating through, return the scraped data as a dataframe



# Tries to turn the page and returns a boolean describing the status of the scrape (TRUE for done, FALSE for not) at position 1.
def TurnPage(driver): # a selenium webdriver instance
    
    # xcode selector for the "next page" button
    click_next = """//*[@id="wt89_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_RichWidgets_wt98_block_wt28"]"""
    
    try: # if we can click the "next page" button
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, click_next))).click() # do it
        return False # and let us know that we've still got records to scrape
    except: # if we can't click the "next page" button
        return True # let us know we've reached the end.



# Relevant XPATH
xpath_dict = dict(
    header = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt188_block_wtColumn1"]/div/div[2]/span""",
    apn = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt146_block_wtColumn2"]/div/div[2]""",
    address = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt146_block_wtColumn1"]/div/div[2]""",
    hearing_officer = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt189_block_wtColumn1"]/div[2]""",
    program_analyst = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt189_block_wtColumn2"]/div[2]""",
    petition_type = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt188_block_wtColumn2"]/div/div[2]""",
    date_filed = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt188_block_wtColumn3"]/div/div[2]""",
    hearing_date = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt16_block_wtColumn1"]/div[2]""",
    mediation_date = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt16_block_wtColumn2"]/div/div[2]""",
    appeal_hearing_date = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_OutSystemsUIWeb_wt16_block_wtColumn3"]/div[2]""",
    case_progress = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_wtCaseActivityStatusTable"]""",
    grounds_tenant = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_wtTenantPetitionGroundsTable"]""",
    grounds_landlord = """//*[@id="wt101_OutSystemsUIWeb_wt10_block_wtContent_wtMainContent_wtOwnerPetitionReasonsTable"]"""
    
)

# Instantiate the webdriver instance
url = 'https://apps.oaklandca.gov/rappetitions/SearchCases.aspx'

driver = webdriver.Chrome()
driver.get(url)

# Limit to the search period and give the page enough time to process that.
start_date = '09-01-2025'
end_date = '11-01-2025'
SetContext(driver, start_date, end_date)
time.sleep(5)

# Store each page in a list
pages = [] # store the records from each page in dataframes in this list; we will concatenate them at the end
done = False # track whether or not we're done scraping
counter = 1 # what page are we on?

# while we're not finished
while done == False:
        
    print('\n\nPARSING PAGE {}.'.format(counter)) # what page are we on
    page = ParsePage(driver, xpath_dict) # get the data
    pages.append(page) # add the data to the list
    
    done = TurnPage(driver) # turn the page and update the status (are we done or not?)
    counter += 1 # add to the counter for our own edification
    
print("Done scraping!") # yeehaw

# Concatenate the pages
output_data = pd.concat(pages) # join the dataframe for each page
output_data['date_scraped'] = date.today()

# Export the data
filename = './data_{}_{}.csv'.format(''.join([s for s in start_date if s != '-']),
                                     ''.join([s for s in end_date if s != '-']))
output_data.to_csv(filename, index=False)
print('{} records scraped.'.format(output_data.shape[0]))

# All done!
driver.quit()
