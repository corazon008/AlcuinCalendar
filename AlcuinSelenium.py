import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from bs4 import BeautifulSoup
import platform

from VARS import SECRETS_FOLDER
from ICalWriter import ICalWriter


class AlcuinSelenium:
    def __init__(self, token:str, username:str, password:str, headless=False):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)
        self.driver.get("https://esaip.alcuin.com/OpDotNet/Noyau/Login.aspx?")
        self.username = username
        self.password = password
        self.token = token

    def GetCalendar(self) -> None:
        self.login()
        self.goToAgenda()
        self.close()

    def login(self):
        print("login")
        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_txtLogin"]""").send_keys(self.username)
        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_txtPassword"]""").send_keys(self.password)
        time.sleep(1)

        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_btnEntrer"]""").click()
        print("End of login")

    def goToAgenda(self):
        print("goToAgenda")
        self.driver.execute_script("""window.parent.content.location = '/OpDotnet/commun/Login/aspxtoasp.aspx?url=/Eplug/Agenda/Agenda.asp?IdApplication=190&TypeAcces=Utilisateur&IdLien=649';""")

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, """/html/frameset/frameset/frame[3]"""))

        select = Select(self.driver.find_element(By.XPATH, """/html/body/form/div/table[1]/tbody/tr/td/div/table/tbody/tr[4]/td[1]/select"""))
        select.select_by_visible_text("Tableau")

        print("End of goToAgenda")

    def ScrapAgenda(self)->None:
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
            self.nextMonth()
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

    def nextMonth(self):
        self.driver.execute_script("SelDat(document.formul.CurDat,null,'MovDat');return false;")
        self.driver.execute_script("SelMoiSui();")
        self.driver.execute_script("SetSelDat();")

    def close(self):
        self.driver.close()

if __name__ == '__main__':
    with open(f"{SECRETS_FOLDER}/login.txt", "r") as file:
        apikey, username, password = file.read().split(" ")
    alcuin = AlcuinSelenium(apikey, username, password, headless=False)
    alcuin.login()
    alcuin.goToAgenda()
    alcuin.ScrapAgenda()
    alcuin.close()
    