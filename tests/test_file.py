import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options

# This test file assumes that overrides.json is set to the following information:
'''
{
    "additional-resources-menu:plugin": {
        "menu-title": "NERSC Resources",
        "links": [
            {
                "name": "NERSC Technical Documentation",
                "url": "https://docs.nersc.gov"
              },
              {
                "name": "NERSC Jupyter Documentation",
                "url": "https://docs.nersc.gov/services/jupyter"
              },
              {
                "name": "JupyterLab Documentation",
                "url": "https://jupyterlab.readthedocs.io/en/stable/"
              },
              {
                "name": "JupyterHub Documentation",
                "url": "https://jupyterhub.readthedocs.io/en/stable"
              }
        ]
    }
}
'''

class TestFile():
  def setup_method(self, method):
    options = Options()
    options.add_argument("--headless")
    self.driver = webdriver.Firefox(options=options)
    self.vars = {}
  
  def teardown_method(self, method):
    self.driver.quit()
  
  def wait_for_window(self, timeout = 2):
    time.sleep(round(timeout / 1000))
    wh_now = self.driver.window_handles
    wh_then = self.vars["window_handles"]
    if len(wh_now) > len(wh_then):
      return set(wh_now).difference(set(wh_then)).pop()
  
  def test_file(self):
    # open JupyerLab and wait for splash screen to go away
    self.driver.get("http://localhost:8888")
    self.driver.implicitly_wait(10)

    # Give 60 seconds for the user to login
    WebDriverWait(self.driver, 60).until(
      expected_conditions.presence_of_element_located(
        (By.XPATH, '//div[@class="lm-MenuBar-itemLabel p-MenuBar-itemLabel" and text()="File"]'))
    )

    # Wait for splash screen to go away
    time.sleep(3)

    self.vars["window_handles"] = self.driver.window_handles
    
    # Make sure that Help menu is present, click it
    elem = self.driver.find_element(
      By.XPATH, '//div[@class="lm-MenuBar-itemLabel p-MenuBar-itemLabel" and text()="Help"]')
    assert elem is not None
    elem.click()

    # Make sure NERSC Resources menu is present, click it
    elem = self.driver.find_element(
      By.XPATH, '//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="NERSC Resources"]')
    assert elem is not None
    elem.click()

    # Make sure NERSC Technical Documentation option is present, click it
    elem = self.driver.find_element(
      By.XPATH, '//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="NERSC Technical Documentation"]')
    assert elem is not None

    # Make sure NERSC Technical Documentation opens to correct website
    self.vars["root"] = self.driver.current_window_handle
    self.vars["window_handles"] = self.driver.window_handles
    elem.click()
    self.vars["newWindow"] = self.wait_for_window(2000)
    self.driver.switch_to.window(self.vars["newWindow"])
    url = self.driver.current_url
    assert url == 'https://docs.nersc.gov/'

    # Go back to JupyterLab and go to NERSC Resources menu
    self.driver.switch_to.window(self.vars["root"])
    self.driver.find_element(
      By.XPATH, '//div[@class="lm-MenuBar-itemLabel p-MenuBar-itemLabel" and text()="Help"]').click()
    self.driver.find_element(
      By.XPATH, '//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="NERSC Resources"]').click()

    # Make sure JupyterHub Documentation option is present, click it
    elem = self.driver.find_element(
      By.XPATH, '//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="JupyterHub Documentation"]')
    assert elem is not None
    self.vars["window_handles"] = self.driver.window_handles
    elem.click()

    # Make sure JupyterHub Documentation opens to correct website
    self.vars["newWindow"] = self.wait_for_window(2000)
    self.driver.switch_to.window(self.vars["newWindow"])
    url = self.driver.current_url
    assert url == 'https://jupyterhub.readthedocs.io/en/stable/'
