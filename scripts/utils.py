import sys
import os


def _set_paths():

    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the target directory relative to the current script
    target_dir = os.path.join(current_dir, '../')
    # Add the target directory to sys.path
    sys.path.append(target_dir)
    
# Helper to load YAML configurations
def load_yaml(filepath):
    try:
        with open(filepath, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

# Initialize configuration
def setup_config(config_path):
    print(f"Setting up configuration from: {config_path}")
    config = ConfigManager("arbitrum")
    config.set_config(filepath=config_path)
    print("Configuration setup complete.")
    return config
    
# Function to download and extract TA-Lib based on the OS
def download_ta_lib():
    print("Detecting operating system...")
    if sys.platform.startswith("linux"):
        print("Operating system: Linux")
        base_url = "https://anaconda.org/conda-forge/libta-lib/0.4.0/download/linux-64/"
        ta_lib_url = "https://anaconda.org/conda-forge/ta-lib/0.4.19/download/linux-64/"
    elif sys.platform == "darwin":
        print("Operating system: MacOS")
        base_url = "https://anaconda.org/conda-forge/libta-lib/0.4.0/download/osx-64/"
        ta_lib_url = "https://anaconda.org/conda-forge/ta-lib/0.4.19/download/osx-64/"
    elif sys.platform.startswith("win"):
        print("Operating system: Windows")
        print("Windows installation not supported via script. Use a binary distribution.")
        sys.exit(1)
    else:
        print(f"Unsupported platform: {sys.platform}")
        sys.exit(1)

    base_path = "/usr/lib/x86_64-linux-gnu/"
    python_path = "/usr/local/lib/python3.10/dist-packages/"

    # Download and extract TA-Lib base library
    lib_url = base_url + "libta-lib-0.4.0-h166bdaf_1.tar.bz2"
    download_and_extract(lib_url, base_path)

    # Download and extract Python wrapper for TA-Lib
    talib_url = ta_lib_url + "ta-lib-0.4.19-py310hde88566_4.tar.bz2"
    download_and_extract(talib_url, os.path.join(python_path, "talib"), strip_components=3)

    print("TA-Lib libraries downloaded and extracted.")

# Helper function for downloading and extracting files
def download_and_extract(url, extract_path, strip_components=1):
    print(f"Downloading from {url}...")
    curl_command = [
        "curl", "-L", url
    ]
    tar_command = [
        "tar", "xj", "-C", extract_path, "--strip-components", str(strip_components)
    ]
    try:
        curl = subprocess.Popen(curl_command, stdout=subprocess.PIPE)
        subprocess.run(tar_command, stdin=curl.stdout, check=True)
        curl.stdout.close()
        print(f"Extracted to {extract_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during download or extraction: {e}")
        sys.exit(1)
