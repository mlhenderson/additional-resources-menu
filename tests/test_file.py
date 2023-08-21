import enum
import json
import os
import shutil
import sys
import time
from copy import deepcopy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException
)


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

    _settings_defaults = {
        'additional-resources-menu:plugin': {
            'menu-title': 'Additional Resources',
            'open-in-jupyter': False,
            'rank': 10,
            'links': []}}

    def setup_method(self, method):
        self.options = Options()
        self.options.add_argument('--headless')
        self.driver = webdriver.Firefox(options=self.options)
        self.default_settings = True
        self.windows = {}
        self.test_link = {'name': 'wikipedia', 'url': 'https://wikipedia.org'}

        test_file_path = os.path.abspath(__file__)
        self.example_overrides = os.path.abspath(
            os.path.join(test_file_path, '../../example_overrides.json'))
        self.overrides_copy_path = os.path.abspath(
            os.path.join(sys.executable, '../../etc/jupyter/labconfig/'))
        self._defaults = self._settings_defaults
        self._override_defaults = json.load(open(self.example_overrides, 'r'))
        self.current_settings = deepcopy(self._settings_defaults)
        self.remove_overrides_file()
        # open JupyterLab and wait for splash screen to go away
        self.driver.get('http://localhost:8888')
        self.wait_for_page_load()
        self.driver.implicitly_wait(1)

    def teardown_method(self, method):
        try:
            self.remove_overrides_file()
            self.reload_page()
            if not self.default_settings:
                self.reset_settings()
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            try:
                # this should clean up any temp files/folders and stop the browser
                self.driver.quit()
                self.driver.service.stop()
            except Exception:
                pass

    def add_overrides_file(self):
        os.makedirs(self.overrides_copy_path, exist_ok=True)
        dest = os.path.abspath(os.path.join(self.overrides_copy_path, 'default_setting_overrides.json'))
        shutil.copyfile(self.example_overrides, dest)
        self._defaults = self._override_defaults
        if self.default_settings:
            self.current_settings = deepcopy(self._override_defaults)
        time.sleep(5)

    def remove_overrides_file(self):
        if os.path.exists(self.overrides_copy_path):
            shutil.rmtree(self.overrides_copy_path)
        self._defaults = self._settings_defaults
        if self.default_settings:
            self.current_settings = deepcopy(self._settings_defaults)
        time.sleep(5)

    def reset_settings(self):
        self.open_settings_editor()
        if not self.default_settings:
            try:
                wait = WebDriverWait(self.driver, 10)
                restore_button = wait.until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
                wait.until(
                    expected_conditions.element_to_be_clickable(restore_button)).click()
                wait.until_not(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
            except (TimeoutException, NoSuchElementException):
                import traceback
                traceback.print_exc()
            finally:
                self.default_settings = True
                self.current_settings = deepcopy(self._defaults)
        self.close_settings_editor()

    def is_settings_editor_plugin_visible(self):
        try:
            editor_tab = self.driver.find_element(By.CSS_SELECTOR, 'div#setting-editor')
            if editor_tab is not None:
                plugin_view = self.driver.find_element(
                    By.CSS_SELECTOR, r'#jp-SettingsEditor-additional-resources-menu\:plugin')
                if plugin_view is None:
                    # make sure plugin settings have been selected
                    self.driver.find_element(self.settings_editor_plugin_xpath).click()
            return True
        except NoSuchElementException:
            return False

    def open_settings_editor(self):
        if self.is_settings_editor_plugin_visible():
            return
        wait = WebDriverWait(self.driver, 10)
        wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, self.settings_menu_xpath))).click()
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.ID, 'jp-mainmenu-settings')))
        wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, self.settings_editor_xpath))).click()
        # make sure settings menu overlay has disappeared to not obscure settings tab
        wait.until_not(
            expected_conditions.visibility_of_element_located(
                (By.ID, 'jp-mainmenu-settings')))
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, 'div#setting-editor')))
        # select the settings editor menu item for this plugin
        wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, self.settings_editor_plugin_xpath))
            ).click()
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, r'#jp-SettingsEditor-additional-resources-menu\:plugin')))

    def close_settings_editor(self):
        time.sleep(5)
        elem = self.driver.find_element(
            By.XPATH,
            '//div[@class="lm-TabBar-tabLabel" and text()="Settings"]/following-sibling::div')
        elem.click()
        # wait for the tab to disappear
        WebDriverWait(self.driver, 30).until_not(
            expected_conditions.presence_of_element_located(
                (By.XPATH, '//div[@class="lm-TabBar-tabLabel" and text()="Settings"]')))

    def wait_for_page_load(self):
        wait = WebDriverWait(self.driver, 60)
        # now wait for the main logo to appear and disappear
        try:
            self.driver.find_element(By.ID, 'main-logo')
            wait.until_not(
                expected_conditions.presence_of_element_located(
                    (By.ID, 'main-logo')))
        except:
            pass
        # now make sure that certain elements are visible to indicate the UI is ready
        wait.until(
            expected_conditions.presence_of_element_located(
                (By.ID, 'modal-command-palette')))
        wait.until(
            expected_conditions.visibility_of_element_located((By.XPATH, self.help_menu_xpath)))
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.ID, 'jp-left-stack')))
        try:
            self.driver.find_element(By.ID, 'main-logo')
            wait.until_not(
                expected_conditions.presence_of_element_located(
                    (By.ID, 'main-logo')))
        except:
            pass

    def reload_page(self):
        self.driver.refresh()
        self.wait_for_page_load()

    def add_link(self, name=None, url=None):
        self.open_settings_editor()
        elem = self.driver.find_elements(
            By.CSS_SELECTOR,
            r'#jp-SettingsEditor-additional-resources-menu\:plugin button'
            )[-1]
        assert elem.text == 'Add'
        elem.click()
        link_form = self.driver.find_elements(
            By.CSS_SELECTOR,
            r'#jp-SettingsEditor-additional-resources-menu\:plugin .array-item'
            )
        num_links = len(link_form)

        if name is None and url is None:
            raise Exception('name and url must be provided')

        entry = {'name': name, 'url': url}
        name_elem = link_form[-1].find_element(
            By.ID,
            fr'jp-SettingsEditor-additional-resources-menu\:plugin_links_{num_links - 1}_name')
        name_elem.clear()
        name_elem.send_keys(name)
        url_elem = link_form[-1].find_element(
            By.ID,
            fr'jp-SettingsEditor-additional-resources-menu\:plugin_links_{num_links - 1}_url')
        url_elem.clear()
        url_elem.send_keys(url)
        self.driver.find_element(By.ID, r'jp-SettingsEditor-additional-resources-menu\:plugin').click()
        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        self.current_settings['additional-resources-menu:plugin']['links'].append(entry)
        self.default_settings = False
        self.close_settings_editor()

    def remove_link(self, index=None):
        self.open_settings_editor()
        buttons = self.driver.find_elements(
            By.CSS_SELECTOR,
            fr'#jp-SettingsEditor-additional-resources-menu\:plugin .array-item'
            )[index].find_elements(By.TAG_NAME, 'button')
        for b in buttons:
            if b.text == 'Remove':
                b.click()
                break
        WebDriverWait(self.driver, 30).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        self.current_settings['additional-resources-menu:plugin']['links'].pop(index)
        self.default_settings = False
        self.close_settings_editor()

    def move_link(self, index=None, direction=None):
        self.open_settings_editor()
        try:
            elem = self.driver.find_elements(
                By.CSS_SELECTOR,
                fr'#jp-SettingsEditor-additional-resources-menu\:plugin .array-item'
                )[index]
            name = (elem.find_element(
                By.ID,
                fr'jp-SettingsEditor-additional-resources-menu\:plugin_links_{index}_name')
                    .get_attribute('value'))
            url = (elem.find_element(
                By.ID,
                fr'jp-SettingsEditor-additional-resources-menu\:plugin_links_{index}_url')
                   .get_attribute('value'))
            buttons = elem.find_elements(By.TAG_NAME, 'button')

            if direction == LinkMovement.UP:
                if index == 0:
                    raise Exception('Unable to move first link UP')
                insert_index = index - 1
                button_text = 'Move up'
            elif direction == LinkMovement.DOWN:
                if index == len(self.current_settings['additional-resources-menu:plugin']['links']) - 1:
                    raise Exception('Unable to move last link DOWN')
                insert_index = index + 1
                button_text = 'Move down'
            else:
                raise Exception('Unknown direction {}'.format(direction))

            for b in buttons:
                if b.text == button_text:
                    b.click()
                    break

            # make sure the values match
            elem = self.driver.find_elements(
                By.CSS_SELECTOR,
                fr'#jp-SettingsEditor-additional-resources-menu\:plugin .array-item'
                )[insert_index]
            assert (name == elem.find_element(
                By.ID,
                fr'jp-SettingsEditor-additional-resources-menu\:plugin_links_{insert_index}_name')
                    .get_attribute('value'))
            assert (url == elem.find_element(
                By.ID,
                fr'jp-SettingsEditor-additional-resources-menu\:plugin_links_{insert_index}_url')
                    .get_attribute('value'))

            tmp = self.current_settings['additional-resources-menu:plugin']['links'].pop(index)
            self.current_settings['additional-resources-menu:plugin']['links'].insert(insert_index, tmp)

            if self.current_settings['additional-resources-menu:plugin']['links'] != \
                    self._defaults['additional-resources-menu:plugin']['links']:
                self.default_settings = False
                WebDriverWait(self.driver, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        except Exception:
            raise
        finally:
            self.close_settings_editor()

    def update_link(self, index=None, name=None, url=None):
        self.open_settings_editor()

        entry = {
            'name': name,
            'url': url
            }

        for k in ['name', 'url']:
            if entry[k] is not None:
                elem = self.driver.find_element(
                    By.ID, fr'jp-SettingsEditor-additional-resources-menu\:plugin_links_{index}_{k}')
                elem.clear()
                elem.click()
                elem.send_keys(entry[k])
                self.current_settings['additional-resources-menu:plugin']['links'][index][k] = entry[k]
                if entry[k] != self._defaults['additional-resources-menu:plugin']['links'][index][k]:
                    WebDriverWait(self.driver, 10).until(
                        expected_conditions.presence_of_element_located(
                            (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        self.default_settings = False
        self.close_settings_editor()

    def set_menu_title(self, title=None):
        """Visit the plugin settings and set the menu-title"""
        self.open_settings_editor()
        menu_title = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable(
                (By.ID, r'jp-SettingsEditor-additional-resources-menu\:plugin_menu-title')))
        menu_title.clear()
        menu_title.click()
        menu_title.send_keys(title)
        self.current_settings['additional-resources-menu:plugin']['menu-title'] = title
        if title != self._defaults['additional-resources-menu:plugin']['menu-title']:
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        self.default_settings = False
        self.close_settings_editor()

    def get_open_in_jupyter(self):
        """Visit the plugin settings and set the checkbox value for open in jupyter to 'checked'"""
        self.open_settings_editor()

        # get the open in jupyter checkbox element
        checkbox = self.driver.find_element(
            By.CSS_SELECTOR,
            self.open_in_jupyter_checkbox_css
            )
        out = checkbox.is_selected()
        self.close_settings_editor()
        return out

    def set_open_in_jupyter(self, checked=False):
        """Visit the plugin settings and set the checkbox value for open in jupyter to 'checked'"""
        self.open_settings_editor()

        # get the open in jupyter checkbox element
        checkbox = self.driver.find_element(
            By.CSS_SELECTOR,
            self.open_in_jupyter_checkbox_css
            )

        if checkbox.is_selected() != checked:
            checkbox.click()
        if checked != self._defaults['additional-resources-menu:plugin']['open-in-jupyter']:
            self.default_settings = False
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        else:
            self.default_settings = True
        self.current_settings['additional-resources-menu:plugin']['open-in-jupyter'] = checked
        self.close_settings_editor()

    def get_rank(self):
        """Visit the plugin settings and set the rank value"""
        self.open_settings_editor()

        # get the rank element
        rank_input = self.driver.find_element(
            By.ID,
            'jp-SettingsEditor-additional-resources-menu:plugin_rank'
            )
        last_rank = int(rank_input.get_attribute('value'))
        self.close_settings_editor()
        return last_rank

    def set_rank(self, value=100):
        """Visit the plugin settings and set the rank value"""
        self.open_settings_editor()

        # get the rank element
        rank_input = self.driver.find_element(
            By.ID,
            'jp-SettingsEditor-additional-resources-menu:plugin_rank'
            )
        rank_input.click()
        if self._defaults['additional-resources-menu:plugin']['rank'] != value:
            rank_input.clear()
            rank_input.send_keys(str(value))
            self.current_settings['additional-resources-menu:plugin']['rank'] = value
            self.default_settings = False
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button.jp-RestoreButton')))
        self.close_settings_editor()

    def get_menu_labels(self):
        """Return labels for submenu links"""
        wait = WebDriverWait(self.driver, 10)
        help_menu = self.driver.find_element(By.XPATH, self.help_menu_xpath)
        wait.until(
            expected_conditions.element_to_be_clickable(help_menu)).click()
        overlay = wait.until(
            expected_conditions.visibility_of_element_located((By.ID, 'jp-mainmenu-help')))
        help_menu_labels = overlay.find_elements(By.CSS_SELECTOR, '.lm-Menu-itemLabel')
        out_menu_labels = []
        for x in help_menu_labels:
            if len(x.text) > 0:
                out_menu_labels.append(x.text)
        self.driver.find_element(By.CSS_SELECTOR, 'div.jp-Toolbar-spacer').click()
        wait.until_not(
            expected_conditions.visibility_of_element_located((By.ID, 'jp-mainmenu-help')))
        return out_menu_labels

    def open_submenu(self):
        """Click the appropriate submenu link"""
        wait = WebDriverWait(self.driver, 10)
        help_menu = self.driver.find_element(By.XPATH, self.help_menu_xpath)
        wait.until(
            expected_conditions.element_to_be_clickable(help_menu)).click()
        overlay = wait.until(
            expected_conditions.visibility_of_element_located((By.ID, 'jp-mainmenu-help')))
        help_menu_labels = overlay.find_elements(By.CSS_SELECTOR, '.lm-Menu-itemLabel')
        for x in help_menu_labels:
            if x.text == self.current_settings['additional-resources-menu:plugin']['menu-title']:
                ar_menu = x
                break
        else:
            raise NoSuchElementException(
                self.current_settings['additional-resources-menu:plugin']['menu-title'])
        ar_menu.click()

    def get_links_labels(self):
        self.open_submenu()
        wait = WebDriverWait(self.driver, 10)
        # Make sure name option is present, return it
        labels = self.driver.find_elements(By.CSS_SELECTOR, 'div.lm-Menu-itemLabel')
        link_labels = []
        for x in labels:
            if len(x.text) > 0:
                link_labels.append(x.text)
        self.driver.find_element(By.CSS_SELECTOR, 'div.jp-Toolbar-spacer').click()
        wait.until_not(
            expected_conditions.visibility_of_element_located((By.ID, 'jp-mainmenu-help')))
        return link_labels

    def find_menu_link_element(self, el):
        self.open_submenu()
        wait = WebDriverWait(self.driver, 10)
        # Make sure name option is present, return it
        labels = self.driver.find_elements(By.CSS_SELECTOR, 'div.lm-Menu-itemLabel')
        found = False
        for x in labels:
            if x.text == el['name']:
                found = True
                break
        self.driver.find_element(By.CSS_SELECTOR, 'div.jp-Toolbar-spacer').click()
        wait.until_not(
            expected_conditions.visibility_of_element_located((By.ID, 'jp-mainmenu-help')))
        return found

    def click_menu_link_element(self, el):
        self.open_submenu()
        # Make sure name option is present, return it
        labels = self.driver.find_elements(By.CSS_SELECTOR, 'div.lm-Menu-itemLabel')
        for x in labels:
            if x.text == el['name']:
                x.click()
                return

    def assert_browser_open_url(self, link=None):
        """Verify that a given url from a submenu link is opened in a browser tab"""
        window_url = self.driver.current_url
        window_handles = self.driver.window_handles
        self.click_menu_link_element(link)
        WebDriverWait(self.driver, 30).until(
            expected_conditions.number_of_windows_to_be(len(window_handles) + 1)
            )
        for wh in self.driver.window_handles:
            if wh != self.windows['root']:
                self.windows['newWindow'] = wh
                self.driver.switch_to.window(wh)
                WebDriverWait(self.driver, 10).until(expected_conditions.url_contains(link['url']))
                window_url = self.driver.current_url
                break
        # the window will add an ending slash to the url
        assert window_url.startswith(link['url'])
        # close the tab or window
        self.driver.close()
        # Go back to JupyterLab main
        self.driver.switch_to.window(self.windows['root'])

    def assert_jupyter_open_url(self, link=None):
        """Verify that a given url from a submenu link is opened in a JupyterLab tab"""
        self.click_menu_link_element(link)
        iframe_xpath = '//iframe[@src="{}"]'.format(link['url'])
        """Verify that a given url from a submenu link is opened in a jupyter tab"""
        WebDriverWait(self.driver, 30).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, iframe_xpath)))
        # close tab
        elem = self.driver.find_element(
            By.XPATH, '//div[@class="lm-TabBar-tabLabel" and text()="{}"]/following-sibling::div'.format(link['name']))
        elem.click()
        WebDriverWait(self.driver, 30).until_not(
            expected_conditions.presence_of_element_located(
                (By.XPATH, '//div[@class="lm-TabBar-tabLabel" and text()="{}"]'.format(link['name']))))

    def test_open_menu_links(self):
        """For each submenu link, verify that it opens correctly in a browser tab and in a jupyter tab.
           This tests the functionality of open-in-jupyter and that the submenu links are present and valid."""
        try:
            self.add_overrides_file()
            self.reload_page()
            self.windows['root'] = self.driver.current_window_handle
            # Test links open in a browser tab
            self.set_open_in_jupyter(False)
            for el in self._defaults['additional-resources-menu:plugin']['links']:
                self.assert_browser_open_url(el)
            # Test links open in a jupyter tab
            self.set_open_in_jupyter(True)
            for el in self._defaults['additional-resources-menu:plugin']['links']:
                self.assert_jupyter_open_url(el)
        except Exception:
            self.driver.save_screenshot('Exception_open_menu_links.png')
            raise

    def test_settings_add_link(self):
        """Starting with no default links, add a link and verify that it appears in the submenu"""
        try:
            self.add_link(**self.test_link)
            self.reload_page()
            assert self.find_menu_link_element(self.test_link)
        except Exception:
            self.driver.save_screenshot('Exception_add_link.png')
            raise

    def test_settings_remove_link(self):
        """Starting with an overrides config, remove the first link and check that the link is not displayed"""
        try:
            self.add_overrides_file()
            self.reload_page()
            self.remove_link(0)
            self.reload_page()
            # test that a different link exists
            assert self.find_menu_link_element(self._defaults['additional-resources-menu:plugin']['links'][1])
            # test that the removed link is not found
            assert not self.find_menu_link_element(self._defaults['additional-resources-menu:plugin']['links'][0])
        except Exception:
            self.driver.save_screenshot('Exception_remove_link.png')
            raise

    def test_settings_update_link(self):
        """Starting with an overrides config, update a link name and check that the display changes"""
        try:
            self.add_overrides_file()
            self.reload_page()
            hub_link = {
                'name': 'JupyterHub Test',
                'url': self._defaults['additional-resources-menu:plugin']['links'][3]['url']
                }
            self.update_link(3, name=hub_link['name'])
            self.reload_page()
            WebDriverWait(self.driver, 10).until(
                expected_conditions.visibility_of_element_located((By.XPATH, self.help_menu_xpath)))
            assert self.find_menu_link_element(hub_link)
        except Exception:
            self.driver.save_screenshot('Exception_update_link.png')
            raise

    def test_settings_update_menu_title(self):
        """Starting with a default config, change the menu title and check that the new title is displayed"""
        try:
            title = 'Menu Title Test'
            self.set_menu_title(title)
            self.reload_page()
            labels = self.get_menu_labels()
            assert title in labels
        except Exception:
            self.driver.save_screenshot('Exception_update_menu_title.png')
            raise

    def test_overrides_remove_link(self):
        """Starting with an overrides config:
           - remove the first link, check that it is gone
           - reset settings, check that all links are present
           - remove the overrides to return to defaults, check that link is not found"""
        try:
            self.add_overrides_file()
            self.reload_page()
            for link in self._defaults['additional-resources-menu:plugin']['links']:
                assert self.find_menu_link_element(link)
            removed_link = self._defaults['additional-resources-menu:plugin']['links'][0]
            self.remove_link(0)
            # refresh until link is gone
            self.reload_page()
            assert self.find_menu_link_element(self._defaults['additional-resources-menu:plugin']['links'][1])
            # test that the removed link is not found
            assert not self.find_menu_link_element(removed_link)
            # restore defaults and check that the link comes back
            self.reset_settings()
            self.reload_page()
            for link in self._defaults['additional-resources-menu:plugin']['links']:
                assert self.find_menu_link_element(link)
            # reload the original defaults
            self.remove_overrides_file()
            self.reload_page()
            # the link should stay gone
            assert not self.find_menu_link_element(removed_link)
        except Exception:
            self.driver.save_screenshot('Exception_overrides_remove_link.png')
            raise

    def test_overrides_add_link(self):
        """Starting with an overrides config:
           - add another link, check that the new link displays
           - remove overrides, check that the link is still there"""
        try:
            self.add_overrides_file()
            self.reload_page()
            for link in self._defaults['additional-resources-menu:plugin']['links']:
                assert self.find_menu_link_element(link)
            self.add_link(**self.test_link)
            self.reload_page()
            assert self.find_menu_link_element(self.test_link)
            # removing overrides only resets the defaults, but does not change settings if user modified
            self.remove_overrides_file()
            self.reload_page()
            # still expect to find the link
            assert self.find_menu_link_element(self.test_link)
        except Exception:
            self.driver.save_screenshot('Exception_overrides_add_link.png')
            raise

    def test_overrides_remove_then_add_link(self):
        """Starting with an overrides config:
           - Remove all links
           - Add a new link
           - Check that new link displays
           - Remove overrides
           - Check that new link still displays"""
        try:
            self.add_overrides_file()
            self.reload_page()
            for link in self._defaults['additional-resources-menu:plugin']['links']:
                self.remove_link(0)
                self.reload_page()
                try:
                    self.find_menu_link_element(link)
                except TimeoutException as e:
                    pass
            self.add_link(**self.test_link)
            self.reload_page()
            assert self.find_menu_link_element(self.test_link)
            self.remove_overrides_file()
            self.reload_page()
            assert self.find_menu_link_element(self.test_link)
        except Exception:
            self.driver.save_screenshot('Exception_overrides_remove_then_add_link.png')
            raise

    def test_overrides_update_link(self):
        """Starting with an overrides config:
           - Update one of the link names
           - Check that the new name displays
           - Remove the overrides
           - Check that the new name still displays"""
        try:
            self.add_overrides_file()
            self.reload_page()
            for link in self._defaults['additional-resources-menu:plugin']['links']:
                assert self.find_menu_link_element(link)
            hub_link = {
                'name': 'JupyterHub Test',
                'url': self._defaults['additional-resources-menu:plugin']['links'][3]['url']
                }
            self.update_link(3, name=hub_link['name'])
            self.reload_page()
            assert self.find_menu_link_element(hub_link)
            self.remove_overrides_file()
            self.reload_page()
            assert self.find_menu_link_element(hub_link)
        except Exception:
            self.driver.save_screenshot('Exception_overrides_update_link.png')
            raise

    def test_overrides_move_link(self):
        """Starting with an overrides config:
           - Move the top link to the bottom, after each move verify the change
           - Move the same link from bottom back to top, after each move verify the change
           - Verify that the last position is the same as the start position"""
        try:
            self.add_overrides_file()
            self.reload_page()
            original_labels = self.get_links_labels()
            moving_link = self._defaults['additional-resources-menu:plugin']['links'][0]['name']
            assert original_labels[-4] == moving_link
            # move the first link from the top to the bottom
            self.move_link(0, LinkMovement.DOWN)
            self.reload_page()
            labels = self.get_links_labels()
            assert labels[-3] == moving_link
            self.move_link(1, LinkMovement.DOWN)
            self.reload_page()
            labels = self.get_links_labels()
            assert labels[-2] == moving_link
            self.move_link(2, LinkMovement.DOWN)
            self.reload_page()
            labels = self.get_links_labels()
            assert labels[-1] == moving_link
            # now move the same link back to the top
            self.move_link(3, LinkMovement.UP)
            self.reload_page()
            labels = self.get_links_labels()
            assert labels[-2] == moving_link
            self.move_link(2, LinkMovement.UP)
            self.reload_page()
            labels = self.get_links_labels()
            assert labels[-3] == moving_link
            self.move_link(1, LinkMovement.UP)
            self.reload_page()
            final_labels = self.get_links_labels()
            assert original_labels == final_labels
        except Exception:
            self.driver.save_screenshot('Exception_overrides_move_link.png')
            raise

    def test_overrides_open_in_jupyter(self):
        """Store the current state of open-in-jupyter, and test changes"""
        try:
            start_open = self.get_open_in_jupyter()
            self.add_overrides_file()
            self.reload_page()
            overrides_open = self.get_open_in_jupyter()
            assert overrides_open == start_open
            self.set_open_in_jupyter(True)
            updated_open = self.get_open_in_jupyter()
            assert updated_open is True
            self.remove_overrides_file()
            self.reload_page()
            last_open = self.get_open_in_jupyter()
            assert last_open == updated_open
        except Exception:
            self.driver.save_screenshot('Exception_overrides_open_in_jupyter.png')
            raise

    def test_overrides_rank(self):
        """Starting with an overrides config:
           - update rank
           - check that the setting was applied
           - remove overrides and check that updated rank value stays"""
        try:
            self.add_overrides_file()
            self.reload_page()
            self.set_rank(-1)
            updated_rank = self.get_rank()
            self.remove_overrides_file()
            self.reload_page()
            rank = self.get_rank()
            assert rank == updated_rank
        except Exception:
            self.driver.save_screenshot('Exception_overrides_rank.png')
            raise

    def test_overrides_menu_title(self):
        """Verify that changes to the menu title take effect and are consistent across defaults and overrides"""
        try:
            default_title = self._settings_defaults['additional-resources-menu:plugin']['menu-title']
            overrides_title = self._override_defaults['additional-resources-menu:plugin']['menu-title']
            title = 'Menu Title Test'
            labels = self.get_menu_labels()
            assert default_title in labels
            assert overrides_title not in labels
            assert title not in labels
            self.add_overrides_file()
            self.reload_page()
            labels = self.get_menu_labels()
            assert default_title not in labels
            assert overrides_title in labels
            assert title not in labels
            self.set_menu_title(title)
            self.reload_page()
            labels = self.get_menu_labels()
            assert default_title not in labels
            assert overrides_title not in labels
            assert title in labels
            self.remove_overrides_file()
            self.reload_page()
            labels = self.get_menu_labels()
            assert default_title not in labels
            assert overrides_title not in labels
            assert title in labels
        except Exception:
            self.driver.save_screenshot('Exception_overrides_menu_title.png')
            raise
