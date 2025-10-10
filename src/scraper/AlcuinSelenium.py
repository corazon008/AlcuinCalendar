import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium import webdriver
from bs4 import BeautifulSoup

from utils.VARS import USERS_FILE
from utils.ICalWriter import ICalWriter
from utils.UserManager import UserManager
from utils import utils


class AlcuinSelenium:
    """
    Selenium-based scraper for fetching student calendar data from the Alcuin ESAIP portal.

    Each instance handles one user session:
    - Logs into the ESAIP Alcuin portal.
    - Navigates to the agenda page.
    - Extracts events and writes them to an .ics file.
    """

    def __init__(self, token: str, username: str, password: str, headless: bool = False):
        """
        Initialize a Selenium WebDriver (preferably remote, fallback to local).

        :param token: Unique token for the user (used for file naming).
        :param username: ESAIP username.
        :param password: ESAIP password.
        :param headless: Whether to run the browser in headless mode.
        """
        self.token = token
        self.username = username
        self.password = password

        # --- Logging setup ---
        self.logger = logging.getLogger(f"AlcuinSelenium[{username}]")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # --- Try to connect to Selenium Grid / Remote WebDriver ---
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("--headless")

        selenium_url = os.getenv("SELENIUM_URL")
        try:
            self.driver = webdriver.Remote(
                command_executor=selenium_url,
                options=options
            )
            self.logger.info(f"Connected to remote Selenium server at {selenium_url}")
        except Exception as e:
            self.logger.warning(f"Remote WebDriver connection failed: {e}. Falling back to local Firefox.")
            self.driver = webdriver.Firefox(options=options)

        self.driver.implicitly_wait(10)
        self.driver.get("https://esaip.alcuin.com/OpDotNet/Noyau/Login.aspx?")
        self.logger.info("Browser initialized and login page loaded")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    def get_calendar(self) -> None:
        """
        Main method to retrieve and store the user's calendar.
        """
        try:
            self.__login()
            self.__go_to_agenda()
            self.__scrape_agenda()
            self.logger.info("Calendar successfully scraped and saved")
        except Exception as e:
            self.logger.error(f"Failed to retrieve calendar: {e}", exc_info=True)
        finally:
            self.close()

    # ----------------------------------------------------------------------
    # Internal helper methods
    # ----------------------------------------------------------------------

    def __login(self) -> None:
        """Perform user authentication on the Alcuin login page."""
        self.logger.info("Starting login sequence")

        wait = WebDriverWait(self.driver, 10)
        login_field = wait.until(EC.presence_of_element_located((By.ID, "UcAuthentification1_UcLogin1_txtLogin")))
        password_field = self.driver.find_element(By.ID, "UcAuthentification1_UcLogin1_txtPassword")

        login_field.clear()
        login_field.send_keys(self.username)
        password_field.clear()
        password_field.send_keys(self.password)

        time.sleep(1)  # Let the inputs register (site is a bit slow)
        self.driver.find_element(By.ID, "UcAuthentification1_UcLogin1_btnEntrer").click()

        self.logger.info("Login submitted successfully")

    def __go_to_agenda(self) -> None:
        """Navigate from the main page to the student's agenda view."""
        self.logger.info("Navigating to the agenda page")

        # The agenda is loaded via a JavaScript redirection inside frames
        utils.retry(
            self.driver.execute_script,
            retries=5,
            delay=2,
            script=(
                "window.parent.content.location = "
                "'/OpDotnet/commun/Login/aspxtoasp.aspx?"
                "url=/Eplug/Agenda/Agenda.asp?IdApplication=190&TypeAcces=Utilisateur&IdLien=649';"
            )
        )

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "/html/frameset/frameset/frame[3]"))

        select = Select(self.driver.find_element(By.XPATH,
                                                 """/html/body/form/div/table[1]/tbody/tr/td/div/table/tbody/tr[4]/td[1]/select"""))
        #select.select_by_visible_text("Tableau")
        select.select_by_index(len(select.options)-1)

        self.logger.info("Agenda page loaded")

    def __scrape_agenda(self) -> None:
        """Extract events for multiple months and save to .ics."""
        self.logger.info("Scraping agenda data")

        icalwriter = ICalWriter()

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "/html/frameset/frameset/frame[3]"))

        for month_index in range(4):  # scrape current + 3 months
            self.logger.info(f"Scraping month {month_index + 1}/4")

            table = self.driver.find_element(By.XPATH, "/html/body/form/div/table[2]/tbody/tr/td/div/table/tbody/tr[2]/td/table/tbody")
            soup = BeautifulSoup(table.get_attribute("innerHTML"), "html.parser")
            rows = soup.find_all("tr")

            for row in rows[1:]:  # skip header
                cells = row.find_all("td")
                icalwriter.add_event_from_cells(cells)

            if month_index < 3:
                self.__next_month()
                time.sleep(2)

        icalwriter.write_to_file(self.token)
        self.logger.info("Agenda scraping completed and .ics file written")

    def __next_month(self) -> None:
        """Move to the next month using Alcuin's JavaScript navigation."""
        self.driver.execute_script("SelDat(document.formul.CurDat,null,'MovDat');return false;")
        self.driver.execute_script("SelMoiSui();")
        self.driver.execute_script("SetSelDat();")
        self.logger.debug("Moved to next month")

    def close(self) -> None:
        """Close the Selenium WebDriver cleanly."""
        try:
            self.driver.quit()
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.warning(f"Failed to close the driver cleanly: {e}")

# ----------------------------------------------------------------------
# CLI usage for manual testing
# ----------------------------------------------------------------------

if __name__ == "__main__":
    users = UserManager()
    for token in users.list_tokens():
        user = users.get_user(token)
        username, password = user["username"], user["password"]

        scraper = AlcuinSelenium(token, username, password, headless=False)
        scraper.get_calendar()
