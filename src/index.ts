import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILabShell,
  ILayoutRestorer
} from '@jupyterlab/application';
import { MainAreaWidget, WidgetTracker } from '@jupyterlab/apputils';
import { URLExt } from '@jupyterlab/coreutils';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ITranslator } from '@jupyterlab/translation';
import { IFrame } from '@jupyterlab/ui-components';
import { Menu } from '@lumino/widgets';

const PLUGIN_ID = 'additional-resources-menu:plugin';
const CSS_CLASS = 'jp-additional-resources-menu';
const OPEN_COMMAND = 'additional-resources-menu:open';

/**
 * Initialization data for the help-menu extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [IMainMenu, ISettingRegistry, ITranslator],
  optional: [ILabShell, ILayoutRestorer],
  activate: (
    app: JupyterFrontEnd,
    mainMenu: IMainMenu,
    settingRegistry: ISettingRegistry,
    translator: ITranslator,
    labShell: ILabShell | null,
    restorer: ILayoutRestorer | null
  ) => {
    console.log(`JupyterLab extension ${PLUGIN_ID} is activated!`);

    const { commands, shell } = app;
    // create the menu that will be added to the help menu
    const additionalResourcesMenu: Menu = new Menu({ commands });
    const namespace = 'additional-resources-menu';
    const trans = translator.load('jupyterlab');
    const tracker = new WidgetTracker<MainAreaWidget<IFrame>>({ namespace });
    let links: any[] = [];
    let openInJupyter = false;
    let tabs = 0;
    let rank = 0;

    if (restorer) {
      // Try to restore any trackers
      void restorer.restore(tracker, {
        command: OPEN_COMMAND,
        args: widget => ({
          naame: widget.title.label,
          url: widget.content.url
        }),
        name: () => namespace
      });
    }

    function loadSetting(setting: ISettingRegistry.ISettings): void {
      links = setting.get('links').composite as any;
      if (links) {
        // parse the settings, filter out any invalid links, translate text
        links = links
          .filter(element => {
            try {
              URLExt.parse(element.url);
            } catch (e) {
              console.error(`Error parsing URL: ${element.url}`);
              return false;
            }
            return true;
          })
          .map(element => {
            return { name: trans.__(element.name), url: element.url };
          });
      }
      additionalResourcesMenu.title.label = setting.get('menu-title')
        .composite as string;
      openInJupyter = setting.get('open-in-jupyter').composite as boolean;
      rank = setting.get('rank').composite as number;
    }

    function newHelpResourceWidget(
      name: string,
      url: string
    ): MainAreaWidget<IFrame> {
      const content = new IFrame({ sandbox: ['allow-scripts', 'allow-forms'] });
      content.url = url;
      content.addClass(CSS_CLASS);
      content.title.label = name;
      content.id = `${namespace}-${tabs}`;
      tabs += 1;
      const widget = new MainAreaWidget({ content });
      widget.addClass(CSS_CLASS);
      return widget;
    }

    commands.addCommand(OPEN_COMMAND, {
      label: args => args['name'] as string,
      caption: args => args['name'] as string,
      execute: args => {
        const name = args['name'] as string;
        const url = args['url'] as string;
        const mixedContent =
          window.location.protocol === 'https:' &&
          URLExt.parse(url).protocol !== 'https:';
        // if we should open in jupyter tab, try to do so, otherwise use window.open()
        if (openInJupyter && !mixedContent) {
          // use widget to open in new Jupyter tab
          const widget = newHelpResourceWidget(name, url);
          void tracker.add(widget);
          shell.add(widget, 'main');
          return widget;
        } else {
          window.open(url);
        }
      }
    });

    Promise.all([settingRegistry.load(PLUGIN_ID), app.restored])
      .then(([setting]) => {
        if (setting) {
          // read the current settings
          loadSetting(setting);

          // pick up setting changes
          setting.changed.connect(loadSetting);

          links.forEach(element => {
            additionalResourcesMenu.addItem({
              command: OPEN_COMMAND,
              args: element
            });
          });

          // add additional resources menu as a submenu of the help menu
          mainMenu.helpMenu.addGroup(
            [
              {
                type: 'submenu' as Menu.ItemType,
                submenu: additionalResourcesMenu
              }
            ],
            rank
          );
        }
      })
      .catch(error => {
        console.error(`${PLUGIN_ID} No links are set in overrides.json`);
        console.error(error.message);
        try {
          console.trace(error);
        } catch (e) {
          console.error('trace not available');
        }
      });
  }
};
export default extension;
