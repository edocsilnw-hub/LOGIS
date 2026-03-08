# routes/routes.py

import importlib
import pkgutil
import routes


def register_routes(app, ctx):
    """
    Auto-discovers and loads all route modules inside /routes
    including subfolders (plugins, personas, admin, etc).
    """

    print("--- DISCOVERING ROUTES ---")

    def load_package(package):
        for module in pkgutil.iter_modules(package.__path__):

            if module.name == "routes":
                continue

            name = module.name
            module_path = f"{package.__name__}.{name}"

            try:
                mod = importlib.import_module(module_path)

                for attr in dir(mod):
                    if attr.startswith("register_"):
                        func = getattr(mod, attr)

                        if callable(func):
                            func(app, ctx)
                            print(f"Loaded routes: {module_path}.{attr}")

            except Exception as e:
                print(f"[ROUTE LOAD ERROR] {module_path}: {e}")

    # load main routes folder
    load_package(routes)

    # load subfolders automatically
    for submodule in pkgutil.iter_modules(routes.__path__):
        if submodule.ispkg:
            package = importlib.import_module(f"routes.{submodule.name}")
            load_package(package)

    print("--- ROUTES REGISTERED ---")