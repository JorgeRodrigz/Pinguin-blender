import subprocess
import sys

def uninstall_module(module_name):
    subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall',module_name])

subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
subprocess.check_call([sys.executable, '-m', 'pip', 'cache', 'purge'])

# Example usage
#uninstall_module('Pillow')
#uninstall_module('opencv-python')