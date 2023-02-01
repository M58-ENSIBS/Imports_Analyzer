import os
import re  
import inspect
import pkg_resources
import importlib
import argparse
import pyfiglet
import time


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--restriction_level', type=int, choices=[1, 2, 3], 
                        help='Level of restriction of the program: 1=> Dump source code of red print imports, 2 => orange and red prints imports, 3 => all imports')
    parser.add_argument('-r', '--requirement', action='store_true',
                        help='Create a requirement.txt file with all the import found in the project')
    parser.add_argument('-b', '--ascii_art', action='store_true',
                        help='Add a complete ascii-art view of the program')
    parser.add_argument('-s', '--delete_red_flag', action='store_true',
                        help='Delete all red flag import in files')
    return parser.parse_args()


def get_imports(path):
    """Return a list of all imported modules in a folder full of python files"""
    imports = []
    for folder, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(folder, file), 'r') as f:
                    file_imports = []
                    for line in f:
                        match = re.match(r'import\s(\w+)', line)
                        if match:
                            file_imports.append(match.group(1))
                    imports.append((file_imports, folder, file))
    return imports


def get_versions(modules):
    """Return the version of each module"""
    versions = {}
    for module in modules:
        try:
            package = pkg_resources.get_distribution(module)
            versions[module] = package.version
        except pkg_resources.DistributionNotFound:
            versions[module] = None
    return versions

def build_requirement_file(modules):
    """Create a requirement.txt file with all the import found in the project"""
    versions = get_versions(modules)
    with open('requirements.txt', 'w') as f:
        for module, version in versions.items():
            if version:
                f.write(f"{module}=={version}")



# Create a function which delete all module which are 'ModuleNotFoundError'
def delete_module_not_found(modules):
    """Delete all module which are 'ModuleNotFoundError'"""
    for module in modules:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            modules.remove(module)
    return modules


def get_source_code(module):
    """Write the source code of concerned module in folder named SourceCode and call source_import_xxxx.txt"""
    with open(f"SourceCode/source_import_{module}.txt", 'w') as f:
        f.write(inspect.getsource(importlib.import_module(module)))



def main():
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
        for module in modules:
            try:
                importlib.import_module(module)
            except ModuleNotFoundError:
                get_source_code(module)
    elif args.restriction_level == 2:
        for module in modules:
            try:
                importlib.import_module(module)
            except ModuleNotFoundError:
                get_source_code(module)
            except:
                get_source_code(module)
    elif args.restriction_level == 3:
        for module in modules:
            get_source_code(module)
    if args.delete_red_flag:
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
        ascii_banner = pyfiglet.figlet_format("Import Anal by M58-")
        print(ascii_banner)
        time.sleep(2)




    prev_root = ''
    for file_imports, folder, file in result:
        if prev_root != folder:
            print(f"\n{folder}:")
            print("|--" + file)
        else:
            print("|--" + file)
        for module in file_imports:
            try:
                module_version = importlib.import_module(module).__version__
                print(f"|   |-- Import {module} \033[32m({module_version})\033[0m")
            except ModuleNotFoundError:
                print(f"|   |-- Import {module} \033[31m(Module not found - Can be deleted by using -s / --delete_red_flag)\033[0m")
            except:
                print(f"|   |-- Import {module} \033[33m(No version information available)\033[0m")
        prev_root = folder
        

if __name__ == "__main__":
    main()
