from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import WordCompleter

from lib.module_manager import ModuleManager
import lib.validate
import lib.prompt_builder as prompt_builder

manager = ModuleManager()
manager.load()

base_net = None
dns_ip = None

# Check for init
if manager['init'].init_needed:


    base_net = prompt_builder.prompt_get_network(premessage="Welcome to FakerNet, it appears we need to do some setup...\n\nPlease enter the initial network allocation. The main DNS server will be hosted here.")

    err, result = manager['netreserve'].run("add_network", net_addr=base_net, description="The central network for Fakernet. Hosts central DNS server and other critical services.")
    if err is None:
        done = True
        print("Network: " + base_net)
    else:
        print(err)

    print("\nEnter the IP of the main DNS server. This will be the resolver for your FakerNet instance.")
    print("You will need to point all systems to this DNS server for things to work.")

    dns_ip = prompt_builder.prompt_get_ip_in_network(base_net)

    if dns_ip is not None:
        err, result = manager['ipreserve'].run("add_ip", ip=dns_ip, description="Central DNS server")
        if err is None:
            done = True
            print("DNS IP: " + dns_ip)
        else:
            print(err)

    



modules_loaded = manager.list_modules()
completer = WordCompleter(modules_loaded)

def main():
    session = PromptSession()

    running = True
    while running:
        try:
            text = session.prompt('> ', completer=completer)
            
        except KeyboardInterrupt:
            running = False
        except EOFError:
            break
        else:
            if text == 'exit':
                running = False
            elif text in modules_loaded:
                module = manager[text]
                print(module.__FUNCS__)
    print('GoodBye!')

if __name__ == '__main__':
    main()