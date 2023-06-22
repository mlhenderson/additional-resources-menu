import enum

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# This test assumes that overrides.json is set to the following information:
_defaults = {
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


class LinkMovement(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()


class TestAdditionalResourcesMenu():
    help_menu_xpath = '//div[@class="lm-MenuBar-itemLabel" and text()="Help"]'
    settings_menu_xpath = '//div[@class="lm-MenuBar-itemLabel" and text()="Settings"]'
    settings_editor_xpath = \
        '//div[@id="jp-mainmenu-settings"]//div[@class="lm-Menu-itemLabel" and text()="Settings Editor"]'
    settings_editor_plugin_xpath = '//div[@data-id="additional-resources-menu:plugin"]'
    open_in_jupyter_checkbox_xpath = \
        '//input[@id="jp-SettingsEditor-additional-resources-menu:plugin_open-in-jupyter"]'
    open_in_jupyter_checkbox_css = \
        r'input#jp-SettingsEditor-additional-resources-menu\:plugin_open-in-jupyter'

    def setup_method(self, method):
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)
        self.windows = {}
        self.link_settings = {}

        # open JupyerLab and wait for splash screen to go away
        self.driver.get("http://localhost:8888")
        wait = WebDriverWait(self.driver, 10)
        wait.until(
            expected_conditions.visibility_of_element_located((By.XPATH, self.help_menu_xpath)))
        wait.until_not(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, 'div#main-logo')))

    def teardown_method(self, method):
        try:
            self.reset_settings()
            self.driver.implicitly_wait(1)
        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            self.driver.close()
            self.driver.quit()

    def reset_settings(self):
        self.open_settings_editor()
        try:
            elem = self.driver.find_element(By.CSS_SELECTOR, 'button.jp-RestoreButton')
            if elem is None:
                return
            wait = WebDriverWait(self.driver, 10, 0.25)
            wait.until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button.jp-RestoreButton'))).click()
            wait.until(
                expected_conditions.invisibility_of_element_located(
                    (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        except NoSuchElementException as e:
            print(e)
        except TimeoutException as e:
            print(e)
        finally:
            self.close_settings_editor()

    def is_settings_editor_plugin_visible(self):
        try:
            editor_tab = self.driver.find_element(By.CSS_SELECTOR, 'div#setting-editor')
            if editor_tab is not None:
                plugin_view = self.driver.find_element(
                    By.CSS_SELECTOR, r"#jp-SettingsEditor-additional-resources-menu\:plugin")
                if plugin_view is None:
                    # make sure plugin settings have been selected
                    self.driver.find_element(self.settings_editor_plugin_xpath).click()
            return True
        except NoSuchElementException as e:
            return False

    def open_settings_editor(self):
        if self.is_settings_editor_plugin_visible():
            return

        wait = WebDriverWait(self.driver, 10)
        # self.driver.switch_to.default_content()
        done = False
        while not done:
            try:
                wait.until(
                    expected_conditions.element_to_be_clickable(
                        (By.XPATH, self.settings_menu_xpath))).click()
                wait.until(
                    expected_conditions.visibility_of_element_located(
                        (By.ID, 'jp-mainmenu-settings')))
                break
            except TimeoutException as e:
                pass
        # open the settings menu
        wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, self.settings_editor_xpath))).click()
        # make sure settings menu overlay has disappeared to not obscure settings tab
        wait.until_not(
            expected_conditions.visibility_of_element_located(
                (By.ID, 'jp-mainmenu-settings')))
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, "div#setting-editor")))
        # select the settings editor menu item for this plugin
        wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, self.settings_editor_plugin_xpath))
            ).click()
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, r'#jp-SettingsEditor-additional-resources-menu\:plugin')))

    def close_settings_editor(self):
        try:
            elem = self.driver.find_element(By.XPATH, '//div[@class="lm-TabBar-tabLabel" and text()="Settings"]')
            # right click to get close tab item
            ActionChains(self.driver) \
                .context_click(elem) \
                .release(elem) \
                .perform()
            WebDriverWait(self.driver, 10, 0.1).until(
                expected_conditions.visibility_of_element_located(
                    (By.XPATH, '//div[@class="lm-Menu-itemLabel" and text()="Close Tab"]'))).click()
        except Exception as e:
            print("Close settings editor: {}".format(e))

    def reload_page(self):
        self.driver.refresh()
        WebDriverWait(self.driver, 30, 0.25).until(
            expected_conditions.visibility_of_element_located((By.XPATH, self.help_menu_xpath)))
        WebDriverWait(self.driver, 10, 0.25).until_not(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, 'div#main-logo')))

    def add_link(self, name=None, url=None):
        self.open_settings_editor()
        elem = self.driver.find_elements(
            By.CSS_SELECTOR,
            r'#jp-SettingsEditor-additional-resources-menu\:plugin button'
            )[-1]
        assert elem is not None
        elem.click()
        link_form = self.driver.find_elements(
            By.CSS_SELECTOR,
            r'#jp-SettingsEditor-additional-resources-menu\:plugin .array-item'
            )
        num_links = len(link_form)

        if name is not None:
            elem = link_form[-1].find_element(
                By.CSS_SELECTOR,
                fr'#jp-SettingsEditor-additional-resources-menu\:plugin_links_{num_links - 1}_name')
            elem.clear()
            elem.send_keys(name)
        if url is not None:
            elem = link_form[-1].find_element(
                By.CSS_SELECTOR,
                fr'#jp-SettingsEditor-additional-resources-menu\:plugin_links_{num_links - 1}_url')
            elem.clear()
            elem.send_keys(url)
        self.close_settings_editor()

    def remove_link(self, index=None):
        self.open_settings_editor()

        buttons = self.driver.find_elements(
            By.CSS_SELECTOR,
            fr'#jp-SettingsEditor-additional-resources-menu\:plugin .array-item'
            )[index].find_elements(By.TAG_NAME, 'button')
        assert buttons is not None
        for b in buttons:
            if b.text == "Remove":
                b.click()
                break
        self.close_settings_editor()

    def move_link(self, index=None, direction=None):
        self.open_settings_editor()
        items = self.driver.find_elements(
            By.XPATH,
            f'//fieldset[@id="jp-SettingsEditor-additional-resources-menu:plugin"]//div[@class="array-item"]'
            )
        assert items is not None
        if direction == LinkMovement.UP:
            move_button = items[index].find_element(By.XPATH, '//button and text()="Move up"')
        elif direction == LinkMovement.DOWN:
            move_button = items[index].find_element(By.XPATH, '//button and text()="Move down"')
        else:
            raise Exception("Unknown direction {}".format(direction))
        assert move_button is not None
        move_button.click()
        self.close_settings_editor()

    def update_link(self, index=None, name=None, url=None):
        self.open_settings_editor()

        entry = {
            "name": name,
            "url": url
            }

        for input in entry.keys():
            if entry[input] is not None:
                elem = self.driver.find_element(
                    By.CSS_SELECTOR, fr'#jp-SettingsEditor-additional-resources-menu\:plugin_links_{index}_{input}')
                assert elem is not None
                elem.clear()
                elem.click()
                elem.send_keys(entry[input])
        self.close_settings_editor()

    def set_menu_title(self, title=None):
        self.open_settings_editor()
        menu_title = WebDriverWait(self.driver, 10, 0.25).until(
            expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, r'#jp-SettingsEditor-additional-resources-menu\:plugin_menu-title')))
        assert menu_title is not None
        menu_title.clear()
        menu_title.send_keys(title)
        self.close_settings_editor()

    def setOpenInJupyter(self, checked=False):
        """Visit the plugin settings and set the checkbox value for open in jupyter to 'checked'"""
        self.open_settings_editor()

        # get the open in jupyter checkbox element
        elem = self.driver.find_element(
            By.CSS_SELECTOR,
            self.open_in_jupyter_checkbox_css
            )
        assert elem is not None
        checkbox = elem

        if checkbox.is_selected() != checked:
            checkbox.click()
        self.close_settings_editor()

    def get_menu_link_element(self, el):
        wait = WebDriverWait(self.driver, 30)
        """Given a name, url dict, find and return the appropriate submenu link"""
        wait.until(
            expected_conditions.element_to_be_clickable((By.XPATH, self.help_menu_xpath))).click()
        # Make sure menu-title is present, click it
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH,
                 '//div[@class="lm-Menu-itemLabel" and text()="{}"]'.format(
                     _defaults["additional-resources-menu:plugin"]["menu-title"])))).click()
        # Make sure name option is present, return it
        elem = wait.until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, '//div[@class="lm-Menu-itemLabel" and text()="{}"]'.format(el['name']))))
        assert elem is not None
        return elem

    def assert_browser_open_url(self, link=None, url=None):
        """Verify that a given url from a submenu link is opened in a browser tab"""
        link.click()
        window_url = self.driver.current_url
        WebDriverWait(self.driver, 10, 0.25).until(
            expected_conditions.number_of_windows_to_be(2)
            )
        for wh in self.driver.window_handles:
            if wh != self.windows["root"]:
                self.windows["newWindow"] = wh
                self.driver.switch_to.window(wh)
                WebDriverWait(self.driver, 10).until(expected_conditions.url_contains(url))
                window_url = self.driver.current_url
                break
        # the window will add an ending slash to the url
        assert window_url.startswith(url)
        # close the tab or window
        self.driver.close()
        # Go back to JupyterLab main
        self.driver.switch_to.window(self.windows["root"])

    def assert_jupyter_open_url(self, el):
        iframe_xpath = '//iframe[@src="{}"]'.format(el['url'])
        """Verify that a given url from a submenu link is opened in a jupyter tab"""
        elem = WebDriverWait(self.driver, 10).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, iframe_xpath)))
        assert elem is not None

    def test_menu_links(self):
        print("test_menu_links")
        """For each submenu link, verify that it opens correctly in a browser tab and in a jupyter tab"""
        try:
            self.windows["root"] = self.driver.current_window_handle
            # Test links open in a browser tab
            self.setOpenInJupyter(False)
            for el in _defaults["additional-resources-menu:plugin"]['links']:
                elem = self.get_menu_link_element(el)
                self.assert_browser_open_url(elem, el['url'])

            # Test links open in a jupyter tab
            self.setOpenInJupyter(True)
            for el in _defaults["additional-resources-menu:plugin"]['links']:
                elem = self.get_menu_link_element(el)
                elem.click()
                self.assert_jupyter_open_url(el)
        except Exception as e:
            self.driver.save_screenshot('Exception_menu_links.png')
            raise

    def test_settings_add_link(self):
        print("test_settings_add_link")
        try:
            test_link = {"name": "wikipedia", "url": "https://wikipedia.org"}
            self.add_link(**test_link)
            self.reload_page()
            self.get_menu_link_element(test_link)
        except Exception as e:
            self.driver.save_screenshot('Exception_add_link.png')
            raise

    def test_settings_remove_link(self):
        print("test_settings_remove_link")
        try:
            self.remove_link(0)
            self.reload_page()
            # test that a different link exists
            submenu_elem = self.get_menu_link_element(_defaults["additional-resources-menu:plugin"]['links'][1])
            assert submenu_elem is not None
            # test that the removed link is not found
            try:
                self.get_menu_link_element(_defaults["additional-resources-menu:plugin"]['links'][0])
            except (NoSuchElementException, TimeoutException) as e:
                pass
        except Exception as e:
            self.driver.save_screenshot('Exception_remove_link.png')
            raise

    def test_settings_update_link(self):
        print("test_settings_update_link")
        try:
            hub_link = {
                'name': 'JupyterHub Test',
                'url': _defaults["additional-resources-menu:plugin"]['links'][3]['url']
                }
            self.update_link(3, name=hub_link["name"])
            self.reload_page()
            WebDriverWait(self.driver, 10, 0.25).until(
                expected_conditions.visibility_of_element_located((By.XPATH, self.help_menu_xpath)))
            self.get_menu_link_element(hub_link)
        except Exception as e:
            self.driver.save_screenshot('Exception_update_link.png')
            raise

    def test_settings_update_menu_title(self):
        print("test_settings_update_menu_title")
        try:
            title = "Menu Title Test"
            self.set_menu_title(title)
            self.reload_page()
            WebDriverWait(self.driver, 30, 0.25).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, self.help_menu_xpath)
                    )
                ).click()
            elem = WebDriverWait(self.driver, 10, 0.25).until(
                expected_conditions.visibility_of_element_located(
                    (By.XPATH, f'//div[@class="lm-Menu-itemLabel" and text()="{title}"]')))
            assert elem is not None
        except Exception as e:
            self.driver.save_screenshot('Exception_update_menu_title.png')
            raise
