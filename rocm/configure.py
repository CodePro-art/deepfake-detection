# Function to add ROCm to PATH
import os
import platform
import subprocess
    
def add_rocm_to_path():
    current_path = os.environ.get('PATH', '')

    if platform.system() == 'Linux' and 'Ubuntu' in platform.version():
        # Adding /opt/rocm-6.1.3/bin to PATH
        rocm_paths = ['/opt/rocm-6.1.3/bin']
        for rocm_path in rocm_paths:
            if rocm_path not in current_path:
                os.environ['PATH'] += f':{rocm_path}'
                print(f'Added {rocm_path} to PATH')
    

# Function to check if a package is installed
def is_package_installed(package_name):
    try:
        result = subprocess.run(['dpkg', '-l', package_name], check=True, capture_output=True, text=True)
        return package_name in result.stdout
    except subprocess.CalledProcessError:
        return False

# Function to install a package
def install_package(package_name):
    try:
        subprocess.run(['sudo', 'apt', 'install', '-y', package_name], check=True)
        print(f'{package_name} installed successfully.')
    except subprocess.CalledProcessError as e:
        print(f'Failed to install {package_name}: {e}')

# Function to check if a package is installed and print its version
def check_package_version(package_name):
    try:
        result = subprocess.run(['dpkg', '-s', package_name], check=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith('Version:'):
                print(f'{package_name} version: {line.split(":")[1].strip()}')
                return True
        return False
    except subprocess.CalledProcessError:
        return False
    
# Function to check if a package is installed and print its version
def install_ocl_icd():
    # Check if ocl-icd is installed and print its version
    if not check_package_version('ocl-icd-libopencl1'):
        print('ocl-icd is not installed. Installing ocl-icd...')
        install_package('ocl-icd-libopencl1')

# def install_khronos_icd():
    # Check if khronos-ocl-icd is installed and print its version
    if not check_package_version('opencl-headers'):
        print('Khronos OpenCL ICD Loader is not installed. Installing Khronos OpenCL ICD Loader...')
        install_package('opencl-headers') 

def install_clinfo():
    # Check if clinfo is installed, if not, install it
    if not is_package_installed('clinfo'):
        print('clinfo is not installed. Installing clinfo...')
        install_package('clinfo')
        
# Function to add LD_LIBRARY_PATH
def add_ld_library_path():
    ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
    rocm_ld_lib_path = '/opt/rocm/lib:/usr/lib/x86_64-linux-gnu'
    if rocm_ld_lib_path not in ld_library_path:
        os.environ['LD_LIBRARY_PATH'] = f'{rocm_ld_lib_path}:{ld_library_path}'
        print(f'Set LD_LIBRARY_PATH to {os.environ["LD_LIBRARY_PATH"]}')
    else:
        print(f'LD_LIBRARY_PATH already includes {rocm_ld_lib_path}')

# Function to run rocminfo to get the ROCm information
def rocminfo():
    rocminfo_command = ['sudo', '/opt/rocm-6.1.3/bin/rocminfo']
    try:
        print('\nRUN: rocminfo\n')
        result = subprocess.run(rocminfo_command, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f'Failed to run rocminfo: {e}')

# Function to run clinfo to get the OpenCL information
def clinfo():
    clinfo_command = ['sudo', 'clinfo', '-l']

    # Run clinfo to verify OpenCL setup
    try:
        print('\nRUN: clinfo\n')
        clinfo_result = subprocess.run(clinfo_command, check=True, capture_output=True, text=True)
        print(clinfo_result.stdout)
    except subprocess.CalledProcessError as e:
        print(f'Failed to run clinfo: {e}')
        
# Function to run rocm-msi
def rocm_smi():
    rocm_smi_command = ['sudo', 'rocm-smi']
    try:
        print('\nRUN: rocm-smi\n')
        result = subprocess.run(rocm_smi_command, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f'Failed to run clinfo: {e}')
        
# Function to check if the user is in the groups 
def check_user_in_groups():
    user = os.getenv('USER')
    groups_to_check = ["render", "video"]
    
    try:
        # Get the current groups of the user
        result = subprocess.run(['groups', user], capture_output=True, text=True, check=True)
        user_groups = result.stdout.strip().split(':')[-1].split()
        
        for group in groups_to_check:
            if group not in user_groups:
                print(f"User {user} is not in the {group} group. Adding to {group} group.")
                subprocess.run(['sudo', 'usermod', '-aG', group, user], check=True)
            else:
                print(f"User {user} is already in the {group} group.")
                
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
