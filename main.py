import os
from pathlib import Path
from shutil import rmtree, copy, copytree, which
import plistlib
import requests
from urllib.parse import urlparse
import zipfile
import sys
import subprocess
import tempfile
import platform
import argparse
import glob

from utils.copy import Copy
from utils.downloader import DpkgDeb, Ldid
from utils.hash import Hash, LdidHash

""" Functions """
def cmd_in_path(args, cmd):
    if args.debug:
        print(f"[DEBUG] Checking if command {cmd} is in PATH...")
    
    if cmd == "ldid":
        if is_ios():
            if is_dpkg_installed("ldid"):
                if args.debug:
                    print(f"[DEBUG] ldid is installed via dpkg")
                    
                return True
            else:
                print("[-] ldid is required on iOS, but it is not installed. Please install it from Procursus.")
                exit(1)
            
        try:
            ldid_out = subprocess.check_output(["ldid"], stderr=subprocess)
            if "procursus" not in ldid_out.decode("utf-8"):
                return False
                
                if args.debug:
                    print(f"[DEBUG] ldid installed is not from Procursus... skipping.")
            else:
                if args.debug:
                    print(f"[DEBUG] ldid installed is from Procursus!")
                        
                return True
        except:
            return False
            
            if args.debug:
                print(f"[DEBUG] ldid is not in PATH... skipping.")
    
    try:
        which_cmd = subprocess.check_output(["which", f"{cmd}"], stderr=subprocess.STDOUT)
    except:
        return False
    
    return True
    
    # if not f"{cmd} not found" in subprocess.run(f"which {cmd}".split(), capture_output=True, text=True).stdout:
    #     return True
        
    #return which(cmd) is not None
    
def is_macos():
    if platform.machine().startswith("i"):
        return False
    
    return sys.platform == "darwin"

def is_linux():
    return sys.platform == "linux"

def is_ios():
    if not sys.platform == "darwin":
        return False
    
    return platform.machine().startswith("i")

def is_dpkg_installed(pkg):
    return (os.system("dpkg -s " + pkg + "> /dev/null 2>&1")) == 0
    

""" Main Function """
def main(args):
    print(f"IPA Permasigner | Version {subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('ascii').strip()}-{subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()}")
    print("Program created by Nebula | Original scripts created by zhuowei | CoreTrust bypass by Linus Henze")
    print()
    
    # Check if script is running on Windows, if so, fail
    if sys.platform == "windows":
        print("[-] Script must be ran on macOS or Linux.")
        exit(1)
        
    # Check if codesign is added on Linux
    if args.codesign:
        if is_linux():
            print("[-] You cannot use codesign on Linux, remove the argument and it'll use ldid instead.")
            exit(1)
        
    # Auto download ldid
    if not cmd_in_path(args, "ldid"):
        if Path(f"{os.getcwd()}/ldid").exists():
            if is_linux() and platform.machine() == "x86_64":
                if args.debug:
                    print(f"[DEBUG] On Linux x86_64, ldid not found...")
                    
                if not LdidHash.check_linux_64(args):
                    print("[*] ldid is outdated or malformed, downloading latest version...")
                    os.remove(f"{os.getcwd()}/ldid")
                    Ldid.download_linux_64()
            elif is_linux() and platform.machine() == "aarch64":
                if args.debug:
                    print(f"[DEBUG] On Linux aarch64, ldid not found...")
                    
                if not LdidHash.check_linux_arm64(args):
                    print("[*] ldid is outdated or malformed, downloading latest version...")
                    os.remove(f"{os.getcwd()}/ldid")
                    Ldid.download_linux_arm64()
            elif is_macos() and platform.machine() == "x86_64":
                if args.debug:
                    print(f"[DEBUG] On macOS x86_64, ldid not found...")
                    
                if not LdidHash.check_macos_64(args):
                    print("[*] ldid is outdated or malformed, downloading latest version...")
                    os.remove(f"{os.getcwd()}/ldid")
                    Ldid.download_macos_64()
            elif is_macos() and platform.machine() == "arm64":
                if args.debug:
                    print(f"[DEBUG] On macOS arm64, ldid not found...")
                    
                if not LdidHash.check_macos_arm64(args):
                    print("[*] ldid is outdated or malformed, downloading latest version...")
                    os.remove(f"{os.getcwd()}/ldid")
                    Ldid.download_macos_arm64()
        else:
            print("[*] ldid not found, downloading.")
            if is_linux() and platform.machine() == "x86_64":
                Ldid.download_linux_64(args)
            elif is_linux() and platform.machine() == "aarch64":
                Ldid.download_linux_arm64(args)
            elif is_macos() and platform.machine() == "x86_64":
                Ldid.download_macos_64(args)
            elif is_macos() and platform.machine() == "arm64":
                Ldid.download_macos_arm64(args)
            
    # Auto download dpkg-deb on Linux
    if not cmd_in_path(args, "dpkg-deb") and is_linux():
        if not Path(f"{os.getcwd()}/dpkg-deb").exists():
            if platform.machine() == "x86_64":
                if args.debug:
                    print(f"[DEBUG] On Linux x86_64, dpkg-deb not found...")
                    
                print("[*] dpkg-deb not found, downloading.")
                DpkgDeb.download_linux_64(args)
                print()
            elif platform.machine() == "aarch64":
                if args.debug:
                    print(f"[DEBUG] On Linux aarch64, dpkg-deb not found...")
                    
                print("[*] dpkg-deb not found, downloading.")
                DpkgDeb.download_linux_arm64(args)
                print()
                
    if is_macos():
        try:
            which_dpkg = subprocess.check_output(["which", "dpkg"], stderr=subprocess.STDOUT)
        except:
            if args.debug:
                print(f"[DEBUG] On macOS x86_64, dpkg-deb not found...")
            print("[-] dpkg is not installed and is required on macOS. Install it though brew or Procursus to continue.")
            exit(1)
    
    # Prompt the user if they'd like to use an external IPA or a local IPA
    if not (args.url or args.path):
        option = input("[?] Would you like to use an IPA stored on the web, or on your system? [external, local] ")
        option = option.lower()

    global out_deb_name
    
    with tempfile.TemporaryDirectory() as tmpfolder:
        print("[*] Created temporary directory.")
        print()
        
        # If the user's choice is external, download an IPA
        # Otherwise, copy the IPA to the temporary directory
        if args.url:
            url = args.url
            
            if not os.path.splitext(urlparse(url).path)[1] == ".ipa":
                print("[-] URL provided is not an IPA, make sure to provide a direct link.")
                exit(1)
            
            res = requests.get(url, stream=True)
            
            try:
                if res.status_code == 200:
                    print(f"[*] Downloading file...")
                    
                    with open(f"{tmpfolder}/app.ipa", "wb") as f:
                        f.write(res.content)
                else:
                    print(f"[-] URL provided is not reachable. Status code: {res.status_code}")
                    exit(1)
            except requests.exceptions.RequestException as err:
                print(f"[-] URL provided is not reachable. Error: {err}")
                exit(1)
        elif args.path:
            path = args.path
            
            if path.strip()[-1] == " ":
                path = path.strip()[:-1]
            
            if Path(path).exists():
                copy(path, f"{tmpfolder}/app.ipa")
            else:
                print("[-] That file does not exist! Make sure you're using a direct path to the IPA file.")
                exit(1)
        elif option == "external":
            url = input("[?] Paste in the *direct* path to an IPA online: ")
            
            if not os.path.splitext(urlparse(url).path)[1] == ".ipa":
                print("[-] URL provided is not an IPA, make sure to provide a direct link.")
                exit(1)
            
            res = requests.get(url, stream=True)
            
            try:
                if res.status_code == 200:
                    print(f"[*] Downloading file...")
                    
                    with open(f"{tmpfolder}/app.ipa", "wb") as f:
                        f.write(res.content)
                else:
                    print(f"[-] URL provided is not reachable. Status code: {res.status_code}")
                    exit(1)
            except requests.exceptions.RequestException as err:
                print(f"[-] URL provided is not reachable. Error: {err}")
                exit(1)  
        elif option == "local":
            path = input("[?] Paste in the path to an IPA in your file system: ")
            
            if path.strip()[-1] == " ":
                path = path.strip()[:-1]
            
            if Path(path).exists():
                copy(path, f"{tmpfolder}/app.ipa")
            else:
                print("[-] That file does not exist! Make sure you're using a direct path to the IPA file.")
                exit(1)
        else:
            print("[-] That is not a valid option!")
            exit(1)
        print()
        
        # Unzip the IPA file
        print("[*] Unzipping IPA...")
        with zipfile.ZipFile(f"{tmpfolder}/app.ipa", 'r') as f:
            os.makedirs(f"{tmpfolder}/app", exist_ok=False)
            f.extractall(f"{tmpfolder}/app")
        print()
            
        # Read data from the plist
        print("[*] Reading plist...")
        global folder, app_name, app_bundle, app_version, app_min_ios, app_author, app_executable
        
        if Path(f"{tmpfolder}/app/Payload").exists():
            for fname in os.listdir(path=f"{tmpfolder}/app/Payload"):
                if fname.endswith(".app"):
                    folder = fname
            print("Found plist!")
        else:
            print("[-] IPA is not valid!")
            exit(1)
            
        if Path(f"{tmpfolder}/app/Payload/{folder}/Info.plist").exists():
            with open(f"{tmpfolder}/app/Payload/{folder}/Info.plist", 'rb') as f:
                info = plistlib.load(f)
                app_name = info["CFBundleName"]
                app_bundle = info["CFBundleIdentifier"]
                app_version = info["CFBundleShortVersionString"]
                app_min_ios = info["MinimumOSVersion"]
                app_author = app_bundle.split(".")[1]
                if info["CFBundleExecutable"]:
                    app_executable = info["CFBundleExecutable"]
                    print("Executable found.")
                else:
                    app_executable = None
                    print("No executable found.")
                print("Found information about the app!")
        print()
        
        # Get the deb file ready
        print("[*] Preparing deb file...")
        print("Making directories...")
        os.makedirs(f"{tmpfolder}/deb/Applications", exist_ok=False)
        os.makedirs(f"{tmpfolder}/deb/DEBIAN", exist_ok=False)
        print("Copying deb file scripts and control...")
        Copy.copy_postrm(f"{tmpfolder}/deb/DEBIAN/postrm", app_name)
        Copy.copy_postinst(f"{tmpfolder}/deb/DEBIAN/postinst", app_name)
        Copy.copy_control(f"{tmpfolder}/deb/DEBIAN/control", app_name, app_bundle, app_version, app_min_ios, app_author)
        print("Copying app files...")
        copytree(f"{tmpfolder}/app/Payload/{folder}", f"{tmpfolder}/deb/Applications/{folder}")
        print("Changing deb file scripts permissions...")
        subprocess.run(f"chmod 0755 {tmpfolder}/deb/DEBIAN/postrm".split(), stdout=subprocess.DEVNULL)
        subprocess.run(f"chmod 0755 {tmpfolder}/deb/DEBIAN/postinst".split(), stdout=subprocess.DEVNULL)
        if app_executable is not None:
            print("Changing app executable permissions...")
            full_path = f"'{tmpfolder}/deb/Applications/{folder}/{app_executable}'"
            os.system("chmod 0755 " + full_path)
        print()
        
        # Sign the app
        print("[*] Signing app...")
        Copy.copy_entitlements(f"{tmpfolder}/entitlements.plist", app_bundle)
        if args.codesign:
            print("Signing with codesign as it was specified...")
            subprocess.run(f"security import ./dev_certificate.p12 -P password -A".split(), stdout=subprocess.DEVNULL)
            full_path = f"'{tmpfolder}/deb/Applications/{folder}'"
            frameworks_path = f"{tmpfolder}/deb/Applications/{folder}/Frameworks"
            
            os.system(f"codesign -s 'We Do A Little Trolling iPhone OS Application Signing' --force --deep --preserve-metadata=entitlements '{full_path}'")
            
            if Path(frameworks_path).exists():
                if args.debug:
                    print("[DEBUG] Frameworks path exists")
                    
                for file in os.listdir(frameworks_path):
                    if file.endswith(".dylib"):
                        print(f"Signing dylib {file}...")
                        os.system(f"codesign -s 'We Do A Little Trolling iPhone OS Application Signing' --force --deep '{frameworks_path}/{file}'")
                        
                for fname in glob.glob(frameworks_path + '/*.framework'):
                    for filename in os.listdir(fname):
                        path = os.path.join(fname, filename)
                        if filename == os.path.basename(fname).replace(".framework", ""):
                            print(f"Signing framework executable {filename}...")
                            if args.debug:
                                print(
                                    f"[DEBUG] Running command: codesign -s 'We Do A Little Trolling iPhone OS Application Signing'",
                                    "--force --deep {path}")
                                subprocess.Popen(
                                    ['codesign', '-s', "'We Do A Little Trolling iPhone OS Application Signing'",
                                     '--force', '--deep', f'{path}'])
        else:
            print("Signing with ldid...")
            full_path = f"'{tmpfolder}/deb/Applications/{folder}'"
            frameworks_path = f"{tmpfolder}/deb/Applications/{folder}/Frameworks"
            if cmd_in_path(args, "ldid"):
                if args.debug:
                    print(f"[DEBUG] Running command: ldid -S{tmpfolder}/entitlements.plist -M -Kdev_certificate.p12 '{full_path}'")
            
                os.system(f"ldid -S{tmpfolder}/entitlements.plist -M -Kdev_certificate.p12 '{full_path}'")
            else:
                subprocess.run("chmod +x ldid".split(), stdout=subprocess.DEVNULL)
                if args.debug:
                    print(f"[DEBUG] Running command: ./ldid -S{tmpfolder}/entitlements.plist -M -Kdev_certificate.p12 '{full_path}'")
                
                os.system(f"./ldid -S{tmpfolder}/entitlements.plist -M -Kdev_certificate.p12 '{full_path}'")
            
            if Path(frameworks_path).exists():
                if args.debug:
                    print("[DEBUG] Frameworks path exists")
                    
                for file in os.listdir(frameworks_path):
                    if file.endswith(".dylib"):
                        print(f"Signing dylib {file}...")
                        if cmd_in_path(args, "ldid"):
                            if args.debug:
                                print(f"[DEBUG] Running command: ldid -Kdev_certificate.p12 '{frameworks_path}/{file}'")
                                
                            os.system(f"ldid -Kdev_certificate.p12 '{frameworks_path}/{file}'")
                        else:
                            if args.debug:
                                print(f"[DEBUG] Running command: ./ldid -Kdev_certificate.p12 '{frameworks_path}/{file}'")
                                
                            os.system(f"./ldid -Kdev_certificate.p12 '{frameworks_path}/{file}'")
                        
                for fname in glob.glob(frameworks_path + '/*.framework'):
                    for filename in os.listdir(fname):
                        path = os.path.join(fname, filename)
                        if filename == os.path.basename(fname).replace(".framework", ""):
                            print(f"Signing framework executable {filename}...")
                            if cmd_in_path(args, "ldid"):
                                if args.debug:
                                    print(f"[DEBUG] Running command: ldid -Kdev_certificate.p12 {path}")
                                subprocess.Popen(['ldid', '-Kdev_certificate.p12', f'{path}'])
                            else:
                                if args.debug:
                                    print(f"[DEBUG] Running command: ./ldid -Kdev_certificate.p12 {path}")
                                subprocess.Popen(['./ldid', '-Kdev_certificate.p12', f'{path}'])
        print()

        # Package the deb file
        print("[*] Packaging the deb file...")
        os.makedirs("output", exist_ok=True)
        if Path(f"output/{app_name}.deb").exists():
            os.remove(f"output/{app_name}.deb")
            
        out_deb_name = app_name.replace(' ', '')

        if cmd_in_path(args, "dpkg-deb"):
            if args.debug:
                print(f"[DEBUG] Running command: dpkg-deb -Zxz --root-owner-group -b {tmpfolder}/deb output/{app_name.replace(' ', '')}.deb")
                
            subprocess.run(f"dpkg-deb -Zxz --root-owner-group -b {tmpfolder}/deb output/{app_name.replace(' ', '')}.deb".split(), stdout=subprocess.DEVNULL)
        else:
            if args.debug:
                print(f"[DEBUG] Running command: ./dpkg-deb -Zxz --root-owner-group -b {tmpfolder}/deb output/{app_name.replace(' ', '')}.deb")
            
            subprocess.run(f"./dpkg-deb -Zxz --root-owner-group -b {tmpfolder}/deb output/{app_name.replace(' ', '')}.deb".split(), stdout=subprocess.DEVNULL)

    # Done!!!
    print()
    print("[*] We are finished!")
    print("[*] Copy the newly created deb from the output folder to your jailbroken iDevice and install it!")
    print("[*] The app will continue to work when rebooted to stock.")
    print(f"[*] Output file: output/{out_deb_name}.deb")
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--codesign', action='store_true', help="uses codesign instead of ldid.")
    parser.add_argument('-d', '--debug', action='store_true', help="shows some debug info, only useful for testing.")
    parser.add_argument('-u', '--url', type=str, help="the direct URL of the IPA to be signed.")
    parser.add_argument('-p', '--path', type=str, help="the direct local path of the IPA to be signed.")
    args = parser.parse_args()
    
    main(args)

