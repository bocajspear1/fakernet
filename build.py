import sys
sys.stdout.write("Hello there\n")
sys.stdout.flush()
from lib.module_manager import ModuleManager
sys.stdout.write("Hello again\n")
sys.stdout.flush()

if __name__ == "__main__":
    manager = ModuleManager()
    sys.stdout.write("Loading\n")
    sys.stdout.flush()
    manager.load()
    sys.stdout.write("Loading Done\n")
    sys.stdout.flush()

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
