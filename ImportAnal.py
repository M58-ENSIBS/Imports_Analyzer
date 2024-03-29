__author__ = 'M58'
__version__ = '1.0.0'
__date__ = '02.02.2023'
__license__ = 'MIT'


#~~~~~~~~~~~~~~~~
# Import Section
#~~~~~~~~~~~~~~~~


import os
import re  
import inspect
import pkg_resources
import importlib
import argparse
import pyfiglet
import sys
import warnings
from typing import List
import shutil
from colorama import Fore, Style
import requests
import networkx as nx
import matplotlib.pyplot as plt

def parse_arguments():
    """Parse the arguments of the program

    Returns:
        _type_: argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--restriction_level', type=int, choices=[1, 2, 3], 
                        help='Level of restriction of the program')
    parser.add_argument('-r', '--requirement', action='store_true',
                        help='Create a requirement.txt file with all the import found in the project')
    parser.add_argument('-b', '--ascii_art', action='store_true',
                        help='Print banner of the program')
    parser.add_argument('-s', '--delete_red_flag', action='store_true',
                        help='Delete all red flag import in files')
    parser.add_argument('-a', '--analyze_sources', action='store_true',
                        help='Analyze the source code of the project')
    parser.add_argument('-p', '--request_pypi', action='store_true',
                        help='Search the import on pypi')
    parser.add_argument('-g', '--graph', action='store_true',
                        help='Generate a graph of the project')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {version}'.format(version=__version__),
                        help='Print the version of the program')
    
                        
    return parser.parse_args()


def request_pypi(modules: list) -> None:
    """Search the import on pypi

    Args:
        modules (list): list of modules

    Returns:
        _type_: None
    """
    not_found_modules = []
    nativ_modules_python = []
    # Add every nativ module present by nature
    for module in sys.builtin_module_names:
        nativ_modules_python.append(module)

    
    print("Checking on both get_distribution and pypi...")
    for module in modules:
        try:
            package = pkg_resources.get_distribution(module)
        except pkg_resources.DistributionNotFound:
            not_found_modules.append(module)        

    for module in not_found_modules:
        try:
            url = "https://pypi.org/project/{module}/".format(module=module)
            r = requests.get(url)
            if r.status_code == 200:
                pass
            else:
                if module in nativ_modules_python:
                    print(f"\033[32m{module.ljust(30)} is a nativ module")
                    # Remove this import from the list
                    modules.remove(module)
                else:
                    print(f"\033[31m{module.ljust(30)} is not found on both get_distribution and pypi.org")
        except:
            print(f"\033[31mERROR: {module.ljust(30)}")


def get_imports(path: str) -> list:
    """Returns a list of import paths   

    Args:
        path: path of the project

    Returns:
        _type_: list
    """

    imports = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    file_imports = []
                    for line in f:
                        match = re.match(r'import\s(\w+)', line)
                        if match:
                            file_imports.append(match.group(1))
                        match = re.match(r'from\s(\w+)\simport\s\*', line)
                        if match:
                            file_imports.append(match.group(1))
                    imports.append((file_imports, root, file))
    return imports


def get_versions(modules: list) -> dict:
    """Get the version of all the modules

    Args:
        modules (list): list of modules

    Returns:
        _type_: dict
    """
    versions = {}
    for module in modules:
        try:
            package = pkg_resources.get_distribution(module)
            versions[module] = package.version
        except pkg_resources.DistributionNotFound:
            versions[module] = None
    return versions

def build_requirement_file(modules: list) -> None:
    """Build a requirement.txt file with all the modules and their versions

    Args:
        modules (list): list of modules

    Returns:
        _type_: None
    """
    versions = get_versions(modules)
    modules_with_versions = [(module, version) for module, version in versions.items() if version]
    modules_without_versions = [(module, version) for module, version in versions.items() if not version]
    
    sorted_modules_with_versions = sorted(modules_with_versions, key=lambda x: x[0])
    sorted_modules_without_versions = sorted(modules_without_versions, key=lambda x: x[0])
    
    with open('requirements.txt', 'w') as f:
        for module, version in sorted_modules_with_versions:
            f.write(f"{module}=={version}\n")
        for module, version in sorted_modules_without_versions:
            f.write(f"{module}\n")




def delete_module_not_found(modules: List[str]) -> List[str]:
    """Delete all module which are 'ModuleNotFoundError'

    Args:
        modules (List[str]): list of modules

    Returns:
        List[str]: list of modules
    """
    for module in modules:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            modules.remove(module)
    return modules


def get_source_code(module: str) -> None:
    """Get the source code of a module

    Args:
        module (str): module name

    Returns:
        _type_: None
    """
    if module in sys.builtin_module_names:
        print(f"{module} is a built-in module")
        return

    os.makedirs("SourceCode", exist_ok=True)
    source_file = f"SourceCode/source_import_{module}.txt"
    try:
        with open(source_file, 'w') as f:
            f.write(inspect.getsource(importlib.import_module(module)))

    except OSError:
        print(f"Cannot write source code of {module} to {source_file}")

    except TypeError:
        print("\n")
        print("=====================================================")
        print(f"/!\ Cannot get source code of {module}")
        print("=====================================================")
        with open(source_file, 'w') as f:
            f.write("Careful, the source code of this module is not available.")


def analyze_source_code(path: str) -> None:
    """Analyze the source code of the project

    Args:
        path (str): path of the project

    Returns:
        _type_: None
    """
    suspect_imports = ['eval', 'exec', 'pickle', 'marshal', 'shelve', 'os.system', 'subprocess', 'socket', 'requests',
                       'urllib.request', 'urllib.parse', 'urllib.error', 'urllib.robotparser', 'http.client',
                       'ftplib', 'poplib', 'imaplib', 'nntplib', 'smtplib', 'smtpd', 'telnetlib', 'uuid', 'hashlib',
                       'hmac', 'secrets', 'ssl', 'py_compile', 'compileall', 'dis', 'pickletools', 'codecs', 'encodings',
                       'zipimport', 'pkgutil', 'modulefinder', 'runpy', 'imp', 'importlib', 'bash', 'sh', 'zsh', 'csh',
                          'tcsh', 'pwsh', 'powershell', 'cmd', 'mshta', 'rundll32', 'regsvr32', 'regasm', 'wscript',
                            'cscript', 'msbuild', 'msxsl', 'msdeploy', 'msdt', 'msiexec', 'mshta', 'msxsl', 'msdeploy',
                            'msdt', 'msiexec', 'regsvr32', 'regasm', 'wscript', 'cscript', 'msbuild', 'msxsl', 'msdeploy'
    ]
    lines_less_100 = []

    with open("report.html", "w") as outfile:
        outfile.write("<html>")
        outfile.write("<head>")
        outfile.write("<title>Report ANAL</title>")
        outfile.write("<style>")
        outfile.write("table, th, td {")
        outfile.write("border: 1px solid black;")
        outfile.write("border-collapse: collapse;")
        outfile.write("}")
        outfile.write("</style>")
        outfile.write("</head>")
        outfile.write("<body>")
        outfile.write("<h1>Detection Report</h1>")
        outfile.write("<div>")
        outfile.write("<h2>Summary</h2>")
        outfile.write("<ul>")
        for root, dirs, files in os.walk(path):
            for file in files:
                # Print every file present in the report, print only the name of the file (not source_import_xxx.txt)
                # Regex to keep only the name of the file
                if re.search(r"source_import_(.*).txt", file):
                    file = file.replace("source_import_", "")
                    file = file.replace(".txt", "")
                outfile.write(f"<li>{file}</li>")
                # Create anchor to full end of the report

        outfile.write("</ul>")
        outfile.write(f"<a href='#end' style='color: inherit;'>↳ End of the report</a>")
        outfile.write("</div>")
        outfile.write("<table>")
        outfile.write("<thead>")
        outfile.write("<tr>")
        outfile.write("<th>File Name</th>")
        outfile.write("<th>Suspect Import</th>")
        outfile.write("<th>Type</th>")
        outfile.write("<th>Line Number</th>")
        outfile.write("<th>Line Content</th>")
        outfile.write("</tr>")
        outfile.write("</thead>")
        outfile.write("<tbody>")

        for root, dirs, files in os.walk(path):
            for file in files:
                with open(os.path.join(root, file), 'r') as f:
                    source_code = f.read()
                    lines = source_code.splitlines()
                    if len(lines) < 100:
                        lines_less_100.append(file)
                    for suspect in suspect_imports:
                        if suspect in source_code:
                            outfile.write("<tr>")
                            outfile.write("<td><a href='{}'>{}</a></td>".format(os.path.join(root, file), file))
                            outfile.write("<td>{}</td>".format(suspect))
                            outfile.write("<td colspan='3' style='background-color: yellow;'>Found suspect import</td>")
                            outfile.write("</tr>")

                            for line in source_code.splitlines():
                                line_str = line.strip()
                                start_index = line_str.find(suspect)
                                while start_index != -1:
                                    end_index = start_index + len(suspect)
                                    if (start_index == 0 or not line_str[start_index - 1].isalpha()) and \
                                    (end_index == len(line_str) or not line_str[end_index].isalpha()):
                                        outfile.write("<tr>")
                                        outfile.write("<td></td>")
                                        outfile.write("<td></td>")
                                        outfile.write("<td style='color: green;'>True Positive</td>")
                                        outfile.write("<td>{}</td>".format(source_code.count('\n', 0, source_code.find(line_str))))
                                        outfile.write("<td>{}</td>".format(line_str.replace(suspect, "<span style='color: red;'>{}</span>".format(suspect))))
                                        outfile.write("</tr>")
                                    else:
                                        outfile.write("<tr>")
                                        outfile.write("<td></td>")
                                        outfile.write("<td></td>")
                                        outfile.write("<td style='color: red;'>False Positive</td>")
                                        outfile.write("<td>{}</td>".format(source_code.count('\n', 0, source_code.find(line_str))))
                                        outfile.write("<td>{}</td>".format(line_str.replace(suspect, "<span style='color: red;'>{}</span>".format(suspect))))
                                        outfile.write("</tr>")
                                    start_index = line_str.find(suspect, end_index)
                                    
            outfile.write("</tbody>\n")
            outfile.write("</table>\n")

            if lines_less_100:
                outfile.write("<div>\n")
                outfile.write("<h3 style='color: red;'>NOTA</h3>\n")
                outfile.write("<p>Some of the source files have less than 100 lines, it's possible it's a hand-made script.</p>\n")
                outfile.write("<ul>\n")
                for file in lines_less_100:
                    outfile.write("<li>{}</li>\n".format(file))
                outfile.write("</ul>\n")
                outfile.write("</div>\n")

            number_of_unique_suspect_imports = len(suspect_imports)

            number_files = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    number_files += 1

            number_true_positives = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    with open(os.path.join(root, file), 'r') as f:
                        source_code = f.read()
                        for suspect in suspect_imports:
                            if suspect in source_code:
                                for line in source_code.splitlines():
                                    line_str = line.strip()
                                    start_index = line_str.find(suspect)
                                    while start_index != -1:
                                        end_index = start_index + len(suspect)
                                        if (start_index == 0 or not line_str[start_index - 1].isalpha()) and \
                                        (end_index == len(line_str) or not line_str[end_index].isalpha()):
                                            number_true_positives += 1
                                        start_index = line_str.find(suspect, end_index)

            outfile.write("<div>\n")
            outfile.write("<h3>Recap of the analysis</h3>\n")
            outfile.write("<p> The scanned folder has {} files and {} true positives.</p>\n".format(number_files, number_true_positives))
            outfile.write("</body>\n")
            outfile.write("<div id='end'>\n")
            outfile.write("</html>\n")

            print("Report generated in report.html")

def main():
    """ Main
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(pyfiglet.figlet_format("Import_Anal_M58", font="slant", width=100))
    warnings.filterwarnings("ignore", category=pkg_resources.PkgResourcesDeprecationWarning)    
    args = parse_arguments()
    path = os.path.dirname(os.path.abspath(__file__)) 
    result = get_imports(path)
    modules = []
    for file_imports, folder, file in result:
        for module in file_imports:
            modules.append(module)
    modules = delete_module_not_found(modules)
    if args.requirement:
        build_requirement_file(modules)
    
    if args.restriction_level == 1:
        print("Deleting SourceCode folder ...")
        if os.path.exists("SourceCode"):
            shutil.rmtree("SourceCode")
        os.mkdir("SourceCode")
        print("\n")
        print("=====================================================")
        print(f"\033[33m\033[1mThe module {module} has beed dodged because it doesn't exist\033[0m")
        print("=====================================================")
        for module in modules:
            try:
                importlib.import_module(module)
            except ModuleNotFoundError:
                get_source_code(module)
                
    if args.restriction_level == 2:
        print("Deleting SourceCode folder ...")
        if os.path.exists("SourceCode"):
            shutil.rmtree("SourceCode")
        os.mkdir("SourceCode")
        versions = get_versions(modules)
        modules_with_versions = [(module, version) for module, version in versions.items() if version]
        modules_without_versions = [(module, version) for module, version in versions.items() if not version]
        for module, version in modules_without_versions:
            if module in sys.builtin_module_names:
                continue
            print("Found red flag import (" + module + ") in " + file)
            try:
                importlib.import_module(module)
                print("Check passed for module: " + module)
            except ModuleNotFoundError:
                print("Module not installed: " + module)
            if module in modules_with_versions:
                continue
            else:
                if module in sys.builtin_module_names:
                    continue
                else:
                    get_source_code(module)
                    print("Check passed for module: " + module)

    if args.restriction_level == 3:
        print("Deleting SourceCode folder ...")
        if os.path.exists("SourceCode"):
            shutil.rmtree("SourceCode")
        os.mkdir("SourceCode")
        for module in modules:
            if module in sys.builtin_module_names:
                continue
            else:
                get_source_code(module)

    if args.delete_red_flag:
        print("Deleting SourceCode folder ...")
        if os.path.exists("SourceCode"):
            shutil.rmtree("SourceCode")
        os.mkdir("SourceCode")
        for file_imports, folder, file in result:
            for module in file_imports:
                try:
                    importlib.import_module(module)
                except ModuleNotFoundError:
                    with open(os.path.join(folder, file), 'r') as f:
                        lines = f.readlines()
                    with open(os.path.join(folder, file), 'w') as f:
                        for line in lines:
                            if f"import {module}" not in line:
                                f.write(line)
                except:
                    with open(os.path.join(folder, file), 'r') as f:
                        lines = f.readlines()
                    with open(os.path.join(folder, file), 'w') as f:
                        for line in lines:
                            if f"import {module}" not in line:
                                f.write(line)
    if args.ascii_art:
        ascii_banner = pyfiglet.figlet_format("Import Anal by M58")
        print(ascii_banner)
        exit(0)

    if args.analyze_sources:
        analyze_source_code("SourceCode")
        exit(0)
        

    if args.graph:
        G = nx.Graph()

        def generate_arborescence(current_folder):
            """function to generate the arborescence of the folder

            Args:
                current_folder (str): the current folder
            """
            list_files_folders = os.listdir(current_folder)

            for file_folder in list_files_folders:
                full_path = os.path.join(current_folder, file_folder)

                if os.path.isfile(full_path):
                    G.add_node(full_path)
                    G.add_edge(current_folder, full_path)
                else:
                    G.add_node(full_path, is_folder=True)
                    G.add_edge(current_folder, full_path)

                    generate_arborescence(full_path)

            
            for node in G.nodes():
                node_name = os.path.basename(node)
                for other_node in G.nodes():
                    other_node_name = os.path.basename(other_node)
                    if node_name == other_node_name and node != other_node:
                        G.add_edge(node, other_node)


        current_folder = "."
        generate_arborescence(current_folder)


        pos = nx.spring_layout(G)


        fig, ax = plt.subplots()


        node_colors = []
        for node in G.nodes:
            if node == current_folder:
                node_colors.append("lightyellow")
            elif G.nodes[node].get("is_folder"):
                node_colors.append("lightgreen")
            else:
                node_colors.append("lightblue")


        node_labels = {node: os.path.basename(node) for node in G.nodes}

        nx.draw(G, pos, with_labels=True, labels=node_labels, node_color=node_colors, node_size=500)


        dragging = False
        node_to_drag = None
        offset_x = 0.0
        offset_y = 0.0


        def on_press(event):
            """Function called when a mouse button is pressed.

            Args:
                event (matplotlib.backend_bases.MouseEvent): The event.
            """
            global dragging, node_to_drag, offset_x, offset_y

            if event.inaxes is not None:
                x, y = event.xdata, event.ydata
                for node, (pos_x, pos_y) in pos.items():
                    if (x - pos_x) ** 2 + (y - pos_y) ** 2 < 0.03:
                        dragging = True
                        node_to_drag = node
                        offset_x = pos_x - x
                        offset_y = pos_y - y
                        break


        def on_motion(event):
            """Function called when a mouse button is pressed and the mouse is moved.

            Args:
                event (matplotlib.backend_bases.MouseEvent): The event.
            """
            global dragging, node_to_drag

            if dragging and event.inaxes is not None:
                pos[node_to_drag] = (event.xdata + offset_x, event.ydata + offset_y)
                plt.cla()
                nx.draw(G, pos, with_labels=True, labels=node_labels, node_color=node_colors, node_size=500)
                plt.draw()


        def on_release(event):
            global dragging, node_to_drag

            if dragging:
                dragging = False
                node_to_drag = None


        fig.canvas.mpl_connect('button_press_event', on_press)
        fig.canvas.mpl_connect('motion_notify_event', on_motion)
        fig.canvas.mpl_connect('button_release_event', on_release)


        plt.show()


    if args.request_pypi:
        request_pypi(modules)
        exit(0)

    prev_root = ''
    for file_imports, folder, file in result:
        if prev_root != folder:
            print(f"\n{folder}:")
            print("|--" + file)
        else:
            print("|--" + file)
        if not file_imports:
            print("|   |-- \033[32mNo imports found in this file\033[0m")
        for module in file_imports:
            try:
                module_version = importlib.import_module(module).__version__
                print(f"|   |-- Import {module} \033[32m({module_version})\033[0m")
            except ModuleNotFoundError:
                print(f"|   |-- Import {module} \033[31m(Module not found - Can be deleted by using -s / --delete_red_flag)\033[0m")
            except:
                print(f"|   |-- Import {module} \033[33m(No version information available)\033[0m")
        prev_root = folder
        
    print("--------------------------------")
    print("\n")

    print("\033[1m As asked by your arguments, the program will now:\033[0m")
    if args.restriction_level == 1:
        print("     - Dump source code of red print imports")
    elif args.restriction_level == 2:
        print("     - Dump source code of orange and red print imports")
    elif args.restriction_level == 3:
        print("     - Dump source code of all imports")
    if args.requirement:
        print("     - Create a requirement.txt file with all the import found in the project")
    if args.delete_red_flag:
        print("     - Delete all red flag import in files")
    if args.ascii_art:
        print("     - Add a complete ascii-art view of the program")
    if args.request_pypi:
        print("     - Request the pypi.org to get all the information about the modules")
    print("")

    if args.delete_red_flag:
        print("\033[32m[+] All red flag imports have been deleted\033[0m")
    if args.requirement:
        print("\033[32m[+] A requirement.txt file has been created\033[0m")
    if args.restriction_level == 1 or args.restriction_level == 2 or args.restriction_level == 3:
        print("\033[32m[+] All source code has been dumped in folder named SourceCode\033[0m")

if __name__ == "__main__":
    main()
