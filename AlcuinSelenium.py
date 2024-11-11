import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from bs4 import BeautifulSoup
import platform

from VARS import SECRETS_FOLDER
from WriteCalendar import WriteCalendar


class AlcuinSelenium:
    def __init__(self, api:str, username:str, password:str, headless=False):
        if platform.system() == "Windows":
            try:
                options = webdriver.ChromeOptions()
                if headless:
                    options.add_argument('headless')
                self.driver = webdriver.Chrome(options=options)
            except:
                options = webdriver.FirefoxOptions()
                if headless:
                    options.add_argument('--headless')
                self.driver = webdriver.Firefox(options=options)

        else:
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        self.driver.implicitly_wait(10)
        self.driver.get("https://esaip.alcuin.com/OpDotNet/Noyau/Login.aspx?")
        self.username = username
        self.password = password
        self.api = api

    def GetCalendar(self) -> str:
        self.login()
        self.goToAgenda()
        calendar = self.ScrapAgenda()
        self.close()
        return calendar

    def login(self):
        print("login")
        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_txtLogin"]""").send_keys(self.username)
        self.driver.find_element(By.XPATH, """//*[@id="UcAuthentification1_UcLogin1_txtPassword"]""").send_keys(self.password)

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
        writeCalendar = WriteCalendar()
        writeCalendar.beginWriting(self.api)

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "/html/frameset/frameset/frame[3]"))

        table = self.driver.find_element(By.XPATH,
                                         """/html/body/form/div/table[2]/tbody/tr/td/div/table/tbody/tr[2]/td/table/tbody""")
        soup = BeautifulSoup(table.get_attribute('innerHTML'), 'html.parser')
        rows = soup.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            writeCalendar.writeEventWithTD(cells)

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
                writeCalendar.writeEventWithTD(cells)

        writeCalendar.endWriting()

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
    