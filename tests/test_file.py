import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class TestFile():
  def setup_method(self, method):
    self.driver = webdriver.Firefox()
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
    self.driver.get("http://localhost:8888/lab")
    self.driver.implicitly_wait(10)

    WebDriverWait(self.driver, 20).until(
      expected_conditions.presence_of_element_located((By.XPATH, '//*[text()="File"]'))
    )

    # Wait for splash screen to go away
    time.sleep(3)

    self.driver.set_window_size(1230, 709)
    self.vars["window_handles"] = self.driver.window_handles
    
    # Make sure that Help menu is present, click it
    elem = self.driver.find_element_by_xpath('//div[@class="lm-MenuBar-itemLabel p-MenuBar-itemLabel" and text()="Help"]')
    assert elem is not None
    elem.click()

    # Make sure NERSC Resources menu is present, click it
    elem = self.driver.find_element_by_xpath('//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="NERSC Resources"]')
    assert elem is not None
    elem.click()

    # Make sure NERSC Technical Documentation option is present, click it
    elem = self.driver.find_element_by_xpath('//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="NERSC Technical Documentation"]')
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
    self.driver.find_element_by_xpath('//div[@class="lm-MenuBar-itemLabel p-MenuBar-itemLabel" and text()="Help"]').click()
    self.driver.find_element_by_xpath('//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="NERSC Resources"]').click()

    # Make sure JupyterHub Documentation option is present, click it
    elem = self.driver.find_element_by_xpath('//div[@class="lm-Menu-itemLabel p-Menu-itemLabel" and text()="JupyterHub Documentation"]')
    assert elem is not None
    self.vars["window_handles"] = self.driver.window_handles
    elem.click()

    # Make sure JupyterHub Documentation opens to correct website
    self.vars["newWindow"] = self.wait_for_window(2000)
    self.driver.switch_to.window(self.vars["newWindow"])
    url = self.driver.current_url
    assert url == 'https://jupyterhub.readthedocs.io/en/stable/'
