import sys
from lib.module_manager import ModuleManager

if __name__ == "__main__":
    manager = ModuleManager()
    manager.load()

    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        if module_name not in manager.list_modules():
            print("Invalid module")
            sys.exit(1)
        else:
            print("Trying to build {}".format(module_name))
            manager[module_name].build()
            print("Building complete!")
    else:
        print("Building all modules")
        manager.build_all()
        print("Building complete!")
