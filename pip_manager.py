from pip._internal import main as pipmain

LEFT_TO_INSTALL = 0

def install(package):
    pipmain(['install', package])


def import_module(module):
    global LEFT_TO_INSTALL

    try:
        __import__(module)
        LEFT_TO_INSTALL -= 1
    except ModuleNotFoundError as e:
        install(module)
        LEFT_TO_INSTALL -= 1
        __import__(module)


def install_missing(*modules):
    LEFT_TO_INSTALL = len(modules)
    for m in modules:
        import_module(m)