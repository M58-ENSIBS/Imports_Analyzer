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
    return parser.parse_args()


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




import os
import re

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

    
    
    for root, dirs, files in os.walk(path):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                source_code = f.read()
                for suspect in suspect_imports:
                    if suspect in source_code:
                        print("================================"
                              "================================")
                        print("\033[1;31;40mSuspect import '{}' found in file {}!\033[0;37;40m".format(suspect, file))
                        print("================================"
                              "================================")
                        for line in source_code.splitlines():
                            line_str = line.strip()
                            start_index = line_str.find(suspect)
                            while start_index != -1:
                                end_index = start_index + len(suspect)
                                if (start_index == 0 or not line_str[start_index - 1].isalpha()) and \
                                   (end_index == len(line_str) or not line_str[end_index].isalpha()):
                                    print("\033[32mTrue Positives (Lines n°" + str(source_code.count('\n', 0, source_code.find(line_str))) + "): \033[0m" + line_str.replace(suspect, "\033[1;31;40m{}\033[0;37;40m".format(suspect)))
                                    break
                                else:
                                    print("False Positives: " + line_str)
                                start_index = line_str.find(suspect, end_index)

                        print("================================"
                              "================================")
                        print("\n")
                        break






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
    print("")

    if args.delete_red_flag:
        print("\033[32m[+] All red flag imports have been deleted\033[0m")
    if args.requirement:
        print("\033[32m[+] A requirement.txt file has been created\033[0m")
    if args.restriction_level == 1 or args.restriction_level == 2 or args.restriction_level == 3:
        print("\033[32m[+] All source code has been dumped in folder named SourceCode\033[0m")






if __name__ == "__main__":
    main()




