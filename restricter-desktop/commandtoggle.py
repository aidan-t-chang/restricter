import subprocess
import uuid
import xml.etree.ElementTree as ET
import winreg
import os
import xml.etree.ElementTree as ET

defaults = """
<AppLockerPolicy Version="1">
    <RuleCollection Type="Exe" EnforcementMode="NotConfigured">
        <FilePublisherRule Id="46652a30-5fad-467d-9950-b73c36c60327" Name="Signed by O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePublisherCondition PublisherName="O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" ProductName="*" BinaryName="*">
                    <BinaryVersionRange LowSection="*" HighSection="*"/>
                </FilePublisherCondition>
            </Conditions>
        </FilePublisherRule>
        <FilePublisherRule Id="6206f54d-9c04-4edf-9c11-0b316f8a3d08" Name="MICROSOFT® WINDOWS® OPERATING SYSTEM, from O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePublisherCondition PublisherName="O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" ProductName="MICROSOFT® WINDOWS® OPERATING SYSTEM" BinaryName="*">
                    <BinaryVersionRange LowSection="*" HighSection="*"/>
                </FilePublisherCondition>
            </Conditions>
        </FilePublisherRule>
        <FilePathRule Id="8ce8c67f-cc8a-4c9b-9a97-9a1003d523c0" Name="%SYSTEM32%\\*" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePathCondition Path="%SYSTEM32%\\*"/>
            </Conditions>
        </FilePathRule>
        <FilePathRule Id="ad051e01-8fed-4125-83a1-b34d805ccdc9" Name="%WINDIR%\\*" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePathCondition Path="%WINDIR%\\*"/>
            </Conditions>
        </FilePathRule>
        <FilePathRule Id="c0dc9913-0ece-468d-930f-e17350f370c7" Name="%PROGRAMFILES%\\Google\\*" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePathCondition Path="%PROGRAMFILES%\\Google\\*"/>
            </Conditions>
        </FilePathRule>
        <FilePathRule Id="c2a197c1-e462-4071-920b-cdb8001be0f9" Name="%PROGRAMFILES%\\Microsoft\\Edge\\*" Description="" UserOrGroupSid="S-1-1-0" Action="Deny">
            <Conditions>
                <FilePathCondition Path="%PROGRAMFILES%\\Microsoft\\Edge\\*"/>
            </Conditions>
        </FilePathRule>
    </RuleCollection>
    <RuleCollection Type="Msi" EnforcementMode="NotConfigured">
        <FilePathRule Id="b9af7461-1b0e-41b1-bce5-42b50efeeb23" Name="*" Description="" UserOrGroupSid="S-1-1-0" Action="Deny">
            <Conditions>
                <FilePathCondition Path="*"/>
            </Conditions>
        </FilePathRule>
    </RuleCollection>
    <RuleCollection Type="Script" EnforcementMode="NotConfigured"/>
    <RuleCollection Type="Dll" EnforcementMode="NotConfigured"/>
    <RuleCollection Type="Appx" EnforcementMode="NotConfigured">
        <FilePublisherRule Id="a9e18c21-ff8f-43cf-b9fc-db40eed693ba" Name="(Default Rule) All signed packaged apps" Description="Allows members of the Everyone group to run packaged apps that are signed." UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePublisherCondition PublisherName="*" ProductName="*" BinaryName="*">
                    <BinaryVersionRange LowSection="0.0.0.0" HighSection="*"/>
                </FilePublisherCondition>
            </Conditions>
        </FilePublisherRule>
    </RuleCollection>
</AppLockerPolicy>
"""

noten = """
<AppLockerPolicy Version="1">
</AppLockerPolicy>
"""


with open("defaults.xml", "w", encoding="utf-8") as file:
    file.write(defaults)

with open("noten.xml", "w", encoding="utf-8") as file:
    file.write(noten)

# Create the WindowsStore key if it doesn't exist
# if (!(Test-Path 'HKLM:\SOFTWARE\Policies\Microsoft\WindowsStore')) {
#     New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\WindowsStore' -Force | Out-Null
# }
# Set the RemoveWindowsStore DWORD value to 1 to disable the Store
# Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\WindowsStore" -Name "RemoveWindowsStore" -Value 1 -Force 
# write-host "Microsoft Store has been disabled."


def r(cmd):
    completed = subprocess.run(["powershell", "-Command", cmd], shell=True)
    return completed

def r_string(cmd):
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, shell=True)
    return completed

def run(cmd):
    result = r(cmd)
    print(f"Errors: {result.stderr}")

def enable_xmlcommands(pwsVariableName, xmlFile, filePath):
    # Combine all commands with semicolons
    combined_cmd = f"""
    ${pwsVariableName} = @'
        {xmlFile}
    '@;
    ${pwsVariableName} | Out-File -FilePath '{filePath}' -Encoding UTF8;
    Set-AppLockerPolicy -XmlPolicy '{filePath}'
    """
    return r(combined_cmd)

def disable_xmlcommands(whoDunnit):
    entire_cmd = f"""
    $current = Get-AppLockerPolicy  -Effective
    $current | Export-AppLockerPolicy -Path "C:\\temp\\current_policy.xml"
    $policyXML = Get-Content "C:\\temp\\current_policy.xml"
    $rulesToRemove = $policyXML.AppLockerPolicy.RuleCollection.FilePathRule | Where-Object {{$_.Name -like "{whoDunnit}"}}
    foreach ($rule in $rulesToRemove) {{
        $rule.ParentNode.RemoveChild($rule)
    }}
    $policyXML.Save("C:\\temp\\modified_policy.xml")
    Set-AppLockerPolicy -XmlPolicy "C:\\temp\\modified_policy.xml"
    """

    return r(entire_cmd)

def appLockerPolicyExists(filePath):
    checker = r(f"Test-AppLockerPolicy -Path '{filePath}' -User $env:USERNAME")
    return True if checker else False # test-applockerpolicy usually returns nothing if there is no policy


def add_file_path_rule(xml_file, file_path, action="Deny", name="*", description=""):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    rule_id = str(uuid.uuid4())
    
    file_path_rules = root.find('.//RuleCollection[@Type="Path"]')
    if file_path_rules is None:
        file_path_rules = ET.SubElement(root, 'RuleCollection')
        file_path_rules.set('Type', 'Path')
        file_path_rules.set('EnforcementMode', 'Enabled')
    
    rule = ET.SubElement(file_path_rules, 'FilePathRule')
    rule.set('Id', rule_id)
    rule.set('Name', name)
    rule.set('Description', description)
    rule.set('UserOrGroupSid', 'S-1-1-0')
    rule.set('Action', action)
    
    conditions = ET.SubElement(rule, 'Conditions')
    file_path_condition = ET.SubElement(conditions, 'FilePathCondition')
    file_path_condition.set('Path', file_path)
    
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return rule_id


def remove_file_path_rule_by_path(xml_file, target_path):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    removed_rules = []
    
    for rule_collection in root.findall('.//RuleCollection[@Type="Path"]'):
        for rule in rule_collection.findall('FilePathRule'):
            condition = rule.find('.//FilePathCondition')
            if condition is not None and condition.get('Path') == target_path:
                removed_rules.append({
                    'id': rule.get('Id'),
                    'path': condition.get('Path'),
                    'action': rule.get('Action')
                })
                rule_collection.remove(rule)
    
    if removed_rules:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        print(f"Removed {len(removed_rules)} rule(s) for path: {target_path}")
        return removed_rules
    else:
        print(f"No rules found for path: {target_path}")
        return []


def save_pretty_xml_string(xml_string, out_path):
    try:
        import xml.dom.minidom as md
        pretty = md.parseString(xml_string).toprettyxml(indent="  ")
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(pretty)
        print(f"Saved pretty XML to {out_path}")
    except Exception as e:
        print(f"Failed to pretty-save XML to {out_path}: {e}")
        # fallback to raw write
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(xml_string)
        print(f"Saved raw XML to {out_path}")


def get_installed_apps_registry():
    """Get installed apps from Windows Registry"""
    apps = []
    
    # Registry paths where installed programs are listed
    registry_paths = [
        r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
        r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"  # 32-bit apps on 64-bit Windows
    ]
    
    for reg_path in registry_paths:
        try:
            # Open registry key
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            
            # Enumerate all subkeys
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    
                    app_info = {}
                    
                    # Get app information
                    try:
                        display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        app_info['name'] = display_name
                    except FileNotFoundError:
                        i += 1
                        continue
                    
                    # Get additional info if available
                    try:
                        install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                        app_info['install_location'] = install_location
                    except FileNotFoundError:
                        app_info['install_location'] = None
                    
                    try:
                        version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                        app_info['version'] = version
                    except FileNotFoundError:
                        app_info['version'] = None
                    
                    try:
                        publisher, _ = winreg.QueryValueEx(subkey, "Publisher")
                        app_info['publisher'] = publisher
                    except FileNotFoundError:
                        app_info['publisher'] = None
                    
                    try:
                        install_date, _ = winreg.QueryValueEx(subkey, "InstallDate")
                        app_info['install_date'] = install_date
                    except FileNotFoundError:
                        app_info['install_date'] = None
                    
                    apps.append(app_info)
                    winreg.CloseKey(subkey)
                    i += 1
                    
                except OSError:
                    break
            
            winreg.CloseKey(key)
            
        except Exception as e:
            print(f"Error reading registry path {reg_path}: {e}")
    
    return apps

def add_rule_file_path(xml_source, rule_path=None, action="Allow", name=None, description="", write_back=False):
    """Add a FilePathRule to an AppLocker XML.

    xml_source: either a path to an XML file or an XML string.
    rule_path: the file path to use in the FilePathCondition (e.g. "%PROGRAMFILES%\\MyApp\\*").
    action: "Allow" or "Deny".
    name: optional rule name. Defaults to the rule_path value.
    description: optional description.
    write_back: if True and xml_source is a file path, the modified XML will be written back to disk.

    Returns the new rule Id and the modified XML string.
    """
    # Determine if xml_source is a file path (exists) or raw XML string
    is_file = False
    if isinstance(xml_source, str) and os.path.exists(xml_source):
        is_file = True
        tree = ET.parse(xml_source)
        root = tree.getroot()
    else:
        root = ET.fromstring(xml_source)
        tree = ET.ElementTree(root)

    if not rule_path:
        raise ValueError("rule_path must be provided (e.g. %PROGRAMFILES%\\MyApp\\*)")

    rule_id = str(uuid.uuid4())
    rule_name = name if name else rule_path

    # Find a RuleCollection appropriate for FilePathRule entries. Prefer an existing RuleCollection with Type="Exe" or Type="Path".
    rule_collection = None
    for rc in root.findall('RuleCollection'):
        rc_type = rc.get('Type', '').lower()
        if rc_type in ('exe', 'path'):
            rule_collection = rc
            break

    # If none found, append to the first RuleCollection (fallback)
    if rule_collection is None:
        rule_collection = root.find('RuleCollection')
        if rule_collection is None:
            # create a RuleCollection of type Path
            rule_collection = ET.SubElement(root, 'RuleCollection')
            rule_collection.set('Type', 'Path')
            rule_collection.set('EnforcementMode', 'Enabled')

    new_rule = ET.SubElement(rule_collection, 'FilePathRule')
    new_rule.set('Id', rule_id)
    new_rule.set('Name', rule_name)
    new_rule.set('Description', description)
    new_rule.set('UserOrGroupSid', 'S-1-1-0')
    new_rule.set('Action', action)

    conditions = ET.SubElement(new_rule, 'Conditions')
    file_path_condition = ET.SubElement(conditions, 'FilePathCondition')
    file_path_condition.set('Path', rule_path)

    # Optionally write back to file if xml_source was a filename and write_back requested
    xml_str = ET.tostring(root, encoding='utf-8')
    if is_file and write_back:
        tree.write(xml_source, encoding='utf-8', xml_declaration=True)

    return rule_id, xml_str.decode('utf-8')

contStatement = True

while contStatement:
    inp = input()
    if inp.lower() == "q" or inp.lower() == "quit":
        contStatement = False
    inp = int(inp)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_dir = os.path.join(current_dir, "defaults.xml")
    noten_dir = os.path.join(current_dir, "noten.xml")
    reg_dir = os.path.join(current_dir, "regxml.xml")

   
   # input 1: toggle Microsoft Edge
    if inp == 1:
        if appLockerPolicyExists("C:\\Program Files (x86)\\Microsoft"):
            remove_file_path_rule_by_path(defaults, "C:\\Program Files (x86)\\Microsoft")
        else:
            add_file_path_rule(defaults, "C:\\Program Files (x86)\\Microsoft")
    # input 2: google chrome in its entirety
    elif inp == 2:
        if appLockerPolicyExists("C:\\Program Files\\Google\\Chrome\\Application"):
            remove_file_path_rule_by_path(defaults, "C:\\Program Files\\Google\\Chrome\\Application")
        else:
            add_file_path_rule(defaults, "C:\\Program Files\\Google\\Chrome\\Application")
    # input 3: command prompt (completely functional)
    elif inp == 3:
        # if the windows\system path does not exist, create it. if it does exist, don't do anything
        test = r_string("if (!(Test-Path \"HKCU:\\Software\\Policies\\Microsoft\\Windows\\System\")) {New-Item -Path \"HKCU:\\Software\\Policies\\Microsoft\\Windows\\System\" -Force | Out-Null}")
        test2 = r_string("(Get-ItemProperty -Path \"HKCU:\\Software\\Policies\\Microsoft\\Windows\\System\").DisableCMD")
        out = test2.stdout if test2.stdout else "2"
        out = out.strip()[0] # make the output of test2 one char (the actual number that we want)
        print("test2: ", out)
        if out == "0": # command prompt is enabled
            print("command prompt is enabled: disabling")
            r("Set-ItemProperty -Path \"HKCU:\\Software\\Policies\\Microsoft\\Windows\\System\" -Name \"DisableCMD\" -Value 2 -Force")
        elif out == "2": # windows store is disabled
            print("command prompt is disabled; now enabling")
            r("Set-ItemProperty -Path \"HKCU:\\Software\\Policies\\Microsoft\\Windows\\System\" -Name \"DisableCMD\" -Value 0 -Force")
    # input 4: total lockdown (only allow the applocker defaults basically)
    elif inp == 4:
        # create new file first that only contains defaults?
        # turn the enforcement on
        start_changes = r("Start-Service -Name AppIDSvc")
        # get the beginning of the file path
        # set applocker policy
        maybe = r_string("(Get-AppLockerPolicy -Effective).RuleCollections")
        if maybe.stdout == "": # no policies effective right now
            pws_command = f"Set-AppLockerPolicy -XmlPolicy \"{full_dir}\""
            res = r(pws_command)
            print("No policies effective, turned on AppLocker")
        else:
            check = f"Set-AppLockerPolicy -XmlPolicy \"{noten_dir}\""
            checker = r(check)
            print("Restriction active, turned off")
        print("command 4 has run")
    # input 5: block/unblock the registry editor using New-AppLockerPolicy
    elif inp == 5:
        # output an xml formatted version of the applocker policy
        regedit_xml = r("Get-ChildItem C:\\Windows\\regedit.exe | Get-AppLockerFileInformation | New-AppLockerPolicy -RuleType Path -AllowWindows -User Everyone -Xml > regxml.xml")
        with open("regxml.xml", "w", encoding="utf-8") as file:
            old = file
            # no attribute "replace"
            old.replace("Allow", "Deny")
            file.write(old)
        reg_command = f"Set-AppLockerPolicy -XmlPolicy \"{reg_dir}\""
        print("Turned on")
    elif inp == 0:
        contStatement = False

