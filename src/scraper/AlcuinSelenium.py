import json
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from bs4 import BeautifulSoup

from utils.VARS import USERS_FILE
from utils.ICalWriter import ICalWriter
from utils.UserManager import UserManager
from utils import utils


class AlcuinSelenium:
    def __init__(self, token: str, username: str, password: str, headless: bool = False):
        # try to connect to the firefox server
        try :
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            self.driver = webdriver.Remote(
                command_executor=os.getenv("SELENIUM_URL"),
                options=options
            )
        except Exception as e:
            print(f"Failed to connect to remote webdriver: {e}. Falling back to local Firefox driver.")
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            self.driver = webdriver.Firefox(options=options)

        #self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)
        self.driver.get("https://esaip.alcuin.com/OpDotNet/Noyau/Login.aspx?")
        self.username = username
        self.password = password
        self.token = token

    def get_calendar(self) -> None:
        """Main function to get the calendar"""
        self.__login()
        self.__go_to_agenda()
        self.__scrap_agenda()
        self.close()

    def __login(self):
        print("Begin login")
        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_txtLogin"]""").send_keys(
            self.username)
        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_txtPassword"]""").send_keys(
            self.password)
        time.sleep(1)

        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_btnEntrer"]""").click()
        print("End of login")

    def __go_to_agenda(self):
        print("Begin go to agenda")
        utils.retry(self.driver.execute_script, 5, 2,
            """window.parent.content.location = '/OpDotnet/commun/Login/aspxtoasp.aspx?url=/Eplug/Agenda/Agenda.asp?IdApplication=190&TypeAcces=Utilisateur&IdLien=649';""")

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, """/html/frameset/frameset/frame[3]"""))

        select = Select(self.driver.find_element(By.XPATH,
                                                 """/html/body/form/div/table[1]/tbody/tr/td/div/table/tbody/tr[4]/td[1]/select"""))
        select.select_by_visible_text("Tableau")

        print("End of go to agenda")

    def __scrap_agenda(self) -> None:
        print("Begin scrap agenda")
        icalwriter = ICalWriter()

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "/html/frameset/frameset/frame[3]"))

        table = self.driver.find_element(By.XPATH,
                                         """/html/body/form/div/table[2]/tbody/tr/td/div/table/tbody/tr[2]/td/table/tbody""")
        soup = BeautifulSoup(table.get_attribute('innerHTML'), 'html.parser')
        rows = soup.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            icalwriter.add_event_from_cells(cells)

        for _ in range(3):
            self.__next_month()
            while soup == BeautifulSoup(self.driver.find_element(By.XPATH,
                                                                 """/html/body/form/div/table[2]/tbody/tr/td/div/table/tbody/tr[2]/td/table/tbody""").get_attribute(
                'innerHTML'), 'html.parser'):
                time.sleep(1)
            table = self.driver.find_element(By.XPATH,
                                             """/html/body/form/div/table[2]/tbody/tr/td/div/table/tbody/tr[2]/td/table/tbody""")
            soup = BeautifulSoup(table.get_attribute('innerHTML'), 'html.parser')
            rows = soup.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all('td')
                icalwriter.add_event_from_cells(cells)

        icalwriter.write_to_file(self.token)
        print("End of scrap agenda")

    def __next_month(self):
        self.driver.execute_script("SelDat(document.formul.CurDat,null,'MovDat');return false;")
        self.driver.execute_script("SelMoiSui();")
        self.driver.execute_script("SetSelDat();")

    def close(self):
        try :
            self.driver.quit()
        except Exception as e:
            print(f"Failed to close the driver: {e}")


if __name__ == '__main__':
    users = UserManager()

    for token in users.list_tokens():
        username = users.get_user(token)['username']
        password = users.get_user(token)['password']
        print(f'Getting calendar for {username}')
        alcuin = AlcuinSelenium(token, username, password, headless=False)
        alcuin.get_calendar()
