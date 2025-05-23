from rich.console import Console
import utils
console = Console()
ascii1 = ""
ascii2 = ""
with open(utils.get_local_file("MAINPAGE.txt"), "r", encoding="utf-8") as f:
    ascii1 = f.read()

with open(utils.get_local_file("ascii-art.txt"), "r", encoding="utf-8") as f:
    ascii2 = f.read()

console.print("\n\n\n", ascii2, sep = "")

import rich
import os
import sys
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm
from rich.pager import Pager
from rich.progress import Progress
import json
import codecs
import keyboard
import time
import tomllib
import extract


import load_model

keyboard.press('f11')

# --- HELPER FUNCTIONS ---

clear = lambda *_, **__: os.system('cls || clear')

# --- INITIALIZE FILES ---

if not os.path.exists(utils.get_local_file("config.json")):
    with open(utils.get_local_file("config.json"), "w") as f:
        json.dump({"allocated_CPU": 90, "device": "cpu", "models": []}, f)

if not os.path.exists(utils.get_local_file("state.json")):
    with open(utils.get_local_file("state.json"), "w") as f:
        json.dump({"passed_setup": False, "license_version": -1, "licenses": False}, f)

# ------------------------

with open(utils.get_local_file("data.toml"), "rb") as f:
    globaldata = tomllib.load(f)

def get_config():
    with open(utils.get_local_file("config.json"), "r") as f:
        return json.load(f)

def get_state():
    with open(utils.get_local_file("state.json"), "r") as f:
        return json.load(f)

def save_config(data: dict):
    with open(utils.get_local_file("config.json"), "w") as f:
        json.dump(data, f)

def save_state(data: dict):
    with open(utils.get_local_file("state.json"), "w") as f:
        json.dump(data, f)

licenses = []

with open(utils.get_local_file("licenses", "llama_3.2.txt"), "r", encoding="utf-8") as f:
    licenses.append(codecs.decode(f.read(), "unicode_escape"))

with open(utils.get_local_file("licenses", "program.txt"), "r", encoding="utf-8") as f:
    licenses.append(codecs.decode(f.read(), "unicode_escape"))

def license(l: int = 0):
    clear()

    global licenses, pager

    console.rule("[green]AlphaLearn | Licenses", characters = "=")
    console.print(Markdown(licenses[l]))

    while True:
        accepted = Confirm.ask("[ ] I accept.", default=False)

        if accepted:
            console.print("[bold green]✔ Terms accepted. Thank you![/]")
            break
        else:
            console.print("[bold red]✖ You must accept to proceed.[/]")

def accept_licenses():
    global licenses, console

    for i in range(len(licenses)):
        license(i)

def setup():
    resources = 90
    console.print("Press SPACE to finish.")
    with Progress() as p:
        t = p.add_task("[cyan] How much of your cpu can we use? (100%) [/cyan]", total = 100)
        p.advance(t, 90)
        while not keyboard.is_pressed("space"):
            if keyboard.is_pressed("left"):
                p.update(t, advance = -5)
                resources -= 5
                time.sleep(0.1)
            elif keyboard.is_pressed("right"):
                p.update(t, advance = 5)
                resources += 5
                time.sleep(0.1)
            else:
                time.sleep(0.05)
        p.stop_task(t)
    

    return resources

def download() -> bool:
    global console
    extract.provide_console(console)
    r = extract.extract_models()
    return r

def main():
    clear()
    if get_state()['license_version'] != globaldata['license']['version']:
        data = get_state()
        data['licenses'] = False
        save_state(data)
    
    if not get_state()['licenses']:
        accept_licenses()
        data = get_state()

        with open(utils.get_local_file("state.json"), "w") as f:
            data['licenses'] = True
            data['license_version'] = globaldata['license']['version']
            json.dump(data, f)

    if not get_state()['passed_setup']:
        data = get_config()
        state = get_state()

        clear()
        console.rule("AlphaLearn | Setup", characters = "=")
        console.print(f"[bold green]\n{ascii1}\n[/]")

        resources = setup()
        with open(utils.get_local_file("config.json"), "w") as f:
            data['allocated_CPU'] = resources; json.dump(data, f)

        with open(utils.get_local_file("state.json"), "w") as f:
            state['passed_setup'] = True; json.dump(state, f)

    clear()

    console.rule("AlphaLearn | Models", characters = "=")
    console.print(f"[bold green]\n{ascii1}\n[/]")

    if 'llama' not in get_config()['models']:
        status = download()
        if not status:
            console.print("[bold red]✖ Failed to download model. Please try again later.[/]")
            time.sleep(5)
            sys.exit(1)
        config = get_config()
        config['models'].append('llama')
        save_config(config)

    # ------- START CHATTING -------
    clear()
    console.rule("AlphaLearn", characters = "=")
    console.print(f"[bold green]\n{ascii1}\n[/]")
    console.print("Type [bold blue]\\[setup][/] to change settings.")
    pipe = load_model.get_model(utils.get_local_file("models", "llama", "Llama-3.2-3B-Instruct"))
    conversation = [{"role": "system", "content": "You are a helpful assistant. You are to answer any question provided by the user, as long as it does not break any rules set in the license."},
        {"role": "license", "content": licenses[0]},
    {"role": "license", "content": licenses[1]}]
    # Update message based on whether GPU is available
    device_info = "[bold green]GPU[/]" if load_model.is_using_gpu() else "[dim]CPU[/]"
    console.print(f"AlphaLearn - Chat with AI models completely offline\n(Using {device_info} for computations)\nType [bold blue]\\[setup][/] to change settings. Press [bold red]CTRL+C[/] to exit.")
    while True:
        worker_percent = get_config()['allocated_CPU']
        num_workers = load_model.get_workers(worker_percent)
        print(f"Using {num_workers} workers ({worker_percent}% of CPU)")

        rinput = console.input("[bold blue]>>[/][bold]")
        if rinput == '[setup]':
            data = get_config()
            state = get_state()

            clear()

            resources = setup()
            with open(utils.get_local_file("config.json"), "w") as f:
                data['allocated_CPU'] = resources; json.dump(data, f)

            with open(utils.get_local_file("state.json"), "w") as f:
                state['passed_setup'] = True; json.dump(state, f)

            clear()

            console.rule("AlphaLearn", characters = "=")
            console.print(f"[bold green]\n{ascii1}\n[/]")
            # Update message based on whether GPU is available
            device_info = "[bold green]GPU[/]" if load_model.is_using_gpu() else "[dim]CPU[/]"
            console.print(f"AlphaLearn - Chat with AI models completely offline\n(Using {device_info} for computations)\nType [bold blue]\\[setup][/] to change settings. Press [bold red]CTRL+C[/] to exit.")
            continue
        conversation.append({"role": "user", "content": rinput})
        response_data = load_model.generate_response(conversation, pipe, num_workers)
        console.print(Markdown(response_data[1], code_theme="stata-light", inline_code_theme="algol"), overflow='fold')
        conversation = response_data[0]

if __name__ == "__main__":
    main()
