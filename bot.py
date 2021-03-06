import sys
from pyrogram import Client, MessageHandler, CallbackQueryHandler, RawUpdateHandler, UserStatusHandler, Filters
from os import path, listdir, execl
from termcolor import cprint as print
from configparser import ConfigParser, ExtendedInterpolation
from config import *
from importlib import import_module, reload as r

rp = path.dirname(path.realpath(__file__))
api = Client(token, api_id, api_hash, workdir=path.join(rp, 'data'))
cli = Client('{}-{}'.format(api_id, api_hash), api_id, api_hash, workdir=path.join(rp, 'data'))


def base_direction():
    return path.dirname(sys.modules['__main__'].__file__)


def create_config():
    print('\t>> Creating Config...', 'cyan')
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.add_section('Plugins')
    for i in plugins_dir_list():
        config['Plugins'][i] = 'enabled'
    with open(path.join(rp, 'data', 'config.ini'), 'w') as file:
        config.write(file)


def enable_plugins():
    result = set()
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(path.join(rp, 'data', 'config.ini'))
    result.clear()
    for plug in config['Plugins']:
        if config.get('Plugins', plug) == 'enabled':
            result.add(plug)
    return result


def update_config_plugins():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(path.join(rp, 'data', 'config.ini'))
    config.set('Plugins', 'plugins', 'enabled')
    for plug in config['Plugins']:
        if plug not in plugins_dir_list():
            config.remove_option('Plugins', plug)
    for plug in plugins_dir_list():
        if plug not in config['Plugins']:
            config['Plugins'][plug] = 'enabled'
    with open(path.join(rp, 'data', 'config.ini'), 'w') as file:
        config.write(file)


def check_config():
    print('\nChecking Config...', 'green')
    config = ConfigParser(interpolation=ExtendedInterpolation())
    if not path.exists(path.join(rp, 'data', 'config.ini')):
        create_config()
    update_config_plugins()
    config.read(path.join(rp, 'data', 'config.ini'))
    if 'Plugins' not in config.sections():
        print('#! ["Plugins"] not in config sections. !#', 'red')
    print('Done!', 'magenta')


def plugins_dir_list():
    return [plug.rstrip('.py').strip() for plug in listdir(path.join(rp, 'plugins')) if
            plug.endswith(('.py', '.pyc')) and plug.endswith('.py')]


def plugin_load():
    groups = dict(
        msg=0,
        callback=0,
        update=0,
        status=0,
    )
    for plugin in enable_plugins():
        plugin_import = import_module('plugins.{}'.format(plugin))

        def add_handler_by_type(types: str, handler_method):
            if types in plugin_import.returns:
                function = plugin_import.returns.get(types).get('func')
                filters = plugin_import.returns.get(types).get('filters')
                performer = plugin_import.returns.get(types).get('performer')
                print('{} -> {}.{}'.format(plugin, performer, types))
                if performer == 'api':
                    app = api
                elif performer == 'cli':
                    app = cli
                else:
                    if types == 'msg':
                        app = api or cli
                    elif types == 'callback':
                        app = api
                    else:
                        app = cli
                if types == 'update':
                    handler = handler_method(function)
                else:
                    handler = handler_method(function, filters)
                try:
                    app.add_handler(
                        handler,
                        groups.get(types)
                    )
                    groups[types] += 1
                except:
                    pass

        add_handler_by_type('msg', MessageHandler)
        add_handler_by_type('callback', CallbackQueryHandler)
        add_handler_by_type('update', RawUpdateHandler)
        add_handler_by_type('status', UserStatusHandler)


def reload():
    r(sys)
    python = sys.executable
    execl(python, python, *sys.argv)


def start(**kwargs: Client):
    if ('api' not in kwargs) and ('cli' not in kwargs):
        print('App Is Not Set', 'red')
        return
    if 'api' in kwargs:
        app = kwargs['api']
        if app.is_started:
            app.stop()
        app.start()
    if 'cli' in kwargs:
        app = kwargs['cli']
        if app.is_started:
            app.stop()
        app.start()


def main():
    check_config()
    enable_plugins()
    plugin_load()
    start(api=api, cli=cli)


if __name__ == '__main__':
    main()
