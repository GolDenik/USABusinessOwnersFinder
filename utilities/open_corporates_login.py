import time

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


class OpenCorporatesLogin:

    @staticmethod
    def login(email: str, password: str, driver: WebDriver) -> bool:

        try:
            driver.get('https://opencorporates.com/users/sign_in')

            time.sleep(10)

            driver.find_element(By.ID, 'user_email').send_keys(email)
            driver.find_element(By.ID, 'user_password').send_keys(password)

            driver.find_element(By.XPATH, '//button[@name="submit"]').click()

            return True

        except Exception as e:
            print("An exception appeared while signing in to OpenCorporates with following credentials"
                  f" \nEmail: {email}\nPassword: {password}\n\nException: " + str(e))
            return False
