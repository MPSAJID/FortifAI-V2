"""
Deep Scanner Module for FortifAI
Performs comprehensive security analysis of URLs including:
- SSL Certificate Analysis
- HTTP Security Headers Check
- DNS Records Lookup
- Technology Detection
- Port Scanning
- Redirect Chain Analysis

Originally from SubVeil - Integrated into FortifAI Security Platform
"""

import ssl
import socket
import requests
from urllib.parse import urlparse, urljoin, urlunparse
from datetime import datetime
import concurrent.futures
import re

# Suppress SSL warnings for scanning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DeepScanner:
    """Performs deep security scanning of URLs"""
    
    def __init__(self, url: str):
        self.url = url
        self.parsed = urlparse(url)
        self.hostname = self.parsed.hostname
        self.results = {}
        
    def scan_all(self) -> dict:
        """Perform all deep scanning operations"""
        if not self.hostname:
            return {'success': False, 'error': 'Invalid URL'}
        
        try:
            # Run scans in parallel for speed
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                ssl_future = executor.submit(self._analyze_ssl)
                headers_future = executor.submit(self._analyze_security_headers)
                dns_future = executor.submit(self._analyze_dns)
                tech_future = executor.submit(self._detect_technology)
                ports_future = executor.submit(self._scan_common_ports)
                redirect_future = executor.submit(self._analyze_redirects)
            
            self.results = {
                'success': True,
                'target': self.url,
                'hostname': self.hostname,
                'scan_time': datetime.now().isoformat(),
                'ssl_analysis': ssl_future.result(),
                'security_headers': headers_future.result(),
                'dns_records': dns_future.result(),
                'technology': tech_future.result(),
                'open_ports': ports_future.result(),
                'redirect_chain': redirect_future.result(),
                'security_score': 0,
                'security_grade': 'F',
                'findings': []
            }
            
            self._calculate_security_score()
            
            return self.results
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _analyze_ssl(self) -> dict:
        """Analyze SSL/TLS certificate"""
        result = {
            'enabled': False,
            'valid': False,
            'issuer': None,
            'subject': None,
            'expires': None,
            'days_until_expiry': None,
            'protocol': None,
            'cipher': None,
            'certificate_chain': []
        }
        
        if self.parsed.scheme != 'https':
            result['error'] = 'Not an HTTPS URL'
            return result
        
        cert_data = None
        cipher = None
        version = None
        is_valid = False
        
        try:
            context = ssl.create_default_context()
            conn = context.wrap_socket(
                socket.socket(socket.AF_INET),
                server_hostname=self.hostname
            )
            conn.settimeout(10)
            conn.connect((self.hostname, 443))
            
            cert_data = conn.getpeercert()
            cipher = conn.cipher()
            version = conn.version()
            is_valid = True
            conn.close()
            
        except ssl.SSLCertVerificationError:
            is_valid = False
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                conn = context.wrap_socket(
                    socket.socket(socket.AF_INET),
                    server_hostname=self.hostname
                )
                conn.settimeout(10)
                conn.connect((self.hostname, 443))
                
                cert_binary = conn.getpeercert(binary_form=True)
                cipher = conn.cipher()
                version = conn.version()
                conn.close()
                
                if cert_binary:
                    try:
                        from cryptography import x509
                        from cryptography.hazmat.backends import default_backend
                        
                        cert_obj = x509.load_der_x509_certificate(cert_binary, default_backend())
                        
                        issuer_str = cert_obj.issuer.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)
                        issuer_name = issuer_str[0].value if issuer_str else 'Unknown'
                        
                        subject_str = cert_obj.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
                        subject_name = subject_str[0].value if subject_str else 'Unknown'
                        
                        expiry_date = cert_obj.not_valid_after_utc if hasattr(cert_obj, 'not_valid_after_utc') else cert_obj.not_valid_after
                        days_until_expiry = (expiry_date.replace(tzinfo=None) - datetime.now()).days
                        
                        return {
                            'enabled': True,
                            'valid': False,
                            'issuer': issuer_name,
                            'subject': subject_name,
                            'expires': expiry_date.strftime('%Y-%m-%d'),
                            'days_until_expiry': days_until_expiry,
                            'protocol': version or 'Unknown',
                            'cipher': cipher[0] if cipher else 'Unknown',
                            'key_exchange': cipher[1] if cipher and len(cipher) > 1 else None,
                            'san': []
                        }
                        
                    except ImportError:
                        result['enabled'] = True
                        result['valid'] = False
                        result['protocol'] = version
                        result['cipher'] = cipher[0] if cipher else None
                        result['error'] = 'Certificate details unavailable'
                        return result
                        
            except Exception as e:
                result['enabled'] = True
                result['valid'] = False
                result['error'] = f'SSL connection failed: {str(e)}'
                return result
                
        except socket.timeout:
            result['error'] = 'Connection timeout'
            return result
        except socket.gaierror:
            result['error'] = 'DNS resolution failed'
            return result
        except Exception as e:
            result['error'] = f'Connection error: {str(e)}'
            return result
        
        if cert_data:
            subject = dict(x[0] for x in cert_data.get('subject', []))
            issuer = dict(x[0] for x in cert_data.get('issuer', []))
            
            not_after = cert_data.get('notAfter')
            expiry_date = None
            days_until_expiry = None
            
            if not_after:
                try:
                    expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (expiry_date - datetime.now()).days
                except:
                    pass
            
            result = {
                'enabled': True,
                'valid': is_valid,
                'issuer': issuer.get('organizationName', issuer.get('commonName', 'Unknown')),
                'subject': subject.get('commonName', 'Unknown'),
                'expires': expiry_date.strftime('%Y-%m-%d') if expiry_date else 'Unknown',
                'days_until_expiry': days_until_expiry,
                'protocol': version or 'Unknown',
                'cipher': cipher[0] if cipher else 'Unknown',
                'key_exchange': cipher[1] if cipher and len(cipher) > 1 else None,
                'san': cert_data.get('subjectAltName', [])
            }
        
        return result
    
    def _analyze_security_headers(self) -> dict:
        """Analyze HTTP security headers"""
        headers_check = {
            'Strict-Transport-Security': {
                'present': False,
                'value': None,
                'recommendation': 'Enable HSTS to force HTTPS connections'
            },
            'Content-Security-Policy': {
                'present': False,
                'value': None,
                'recommendation': 'Implement CSP to prevent XSS attacks'
            },
            'X-Frame-Options': {
                'present': False,
                'value': None,
                'recommendation': 'Set to DENY or SAMEORIGIN to prevent clickjacking'
            },
            'X-Content-Type-Options': {
                'present': False,
                'value': None,
                'recommendation': 'Set to nosniff to prevent MIME sniffing'
            },
            'X-XSS-Protection': {
                'present': False,
                'value': None,
                'recommendation': 'Enable XSS filter (legacy browsers)'
            },
            'Referrer-Policy': {
                'present': False,
                'value': None,
                'recommendation': 'Control referrer information sent with requests'
            },
            'Permissions-Policy': {
                'present': False,
                'value': None,
                'recommendation': 'Control browser features and APIs'
            },
            'X-Permitted-Cross-Domain-Policies': {
                'present': False,
                'value': None,
                'recommendation': 'Restrict Adobe Flash/PDF cross-domain requests'
            }
        }
        
        result = {
            'headers': headers_check,
            'score': 0,
            'total_headers': len(headers_check),
            'present_count': 0,
            'server': None,
            'powered_by': None,
            'cookies_secure': None
        }
        
        try:
            response = requests.get(self.url, timeout=10, allow_redirects=True, verify=False)
            resp_headers = response.headers
            
            for header_name in headers_check:
                if header_name in resp_headers:
                    headers_check[header_name]['present'] = True
                    headers_check[header_name]['value'] = resp_headers[header_name][:100]
                    result['present_count'] += 1
            
            result['score'] = int((result['present_count'] / result['total_headers']) * 100)
            result['server'] = resp_headers.get('Server', 'Not disclosed')
            result['powered_by'] = resp_headers.get('X-Powered-By', 'Not disclosed')
            
            cookies = response.cookies
            if cookies:
                secure_cookies = all(c.secure for c in cookies)
                result['cookies_secure'] = secure_cookies
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_dns(self) -> dict:
        """Analyze DNS records"""
        result = {
            'a_records': [],
            'aaaa_records': [],
            'mx_records': [],
            'txt_records': [],
            'ns_records': [],
            'cname': None
        }
        
        try:
            hostname_parts = self.hostname.split('.')
            if len(hostname_parts) > 2:
                base_domain = '.'.join(hostname_parts[-2:])
            else:
                base_domain = self.hostname
            
            # A Records (IPv4)
            try:
                a_records = socket.getaddrinfo(self.hostname, None, socket.AF_INET)
                result['a_records'] = list(set(r[4][0] for r in a_records))
            except:
                pass
            
            # AAAA Records (IPv6)
            try:
                aaaa_records = socket.getaddrinfo(self.hostname, None, socket.AF_INET6)
                result['aaaa_records'] = list(set(r[4][0] for r in aaaa_records))
            except:
                pass
            
            try:
                import dns.resolver
                
                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 5
                
                # MX Records
                try:
                    mx = resolver.resolve(base_domain, 'MX')
                    result['mx_records'] = [str(r.exchange).rstrip('.') for r in mx][:5]
                except:
                    pass
                
                # TXT Records
                try:
                    txt = resolver.resolve(self.hostname, 'TXT')
                    result['txt_records'] = [str(r).strip('"')[:100] for r in txt][:5]
                except:
                    pass
                
                # NS Records
                try:
                    ns = resolver.resolve(base_domain, 'NS')
                    result['ns_records'] = [str(r).rstrip('.') for r in ns][:5]
                except:
                    pass
                    
            except ImportError:
                result['error'] = 'dnspython not installed'
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _detect_technology(self) -> dict:
        """Detect server technology and frameworks"""
        result = {
            'server': None,
            'framework': None,
            'cms': None,
            'javascript_libraries': [],
            'cdn': None,
            'analytics': [],
            'detected': []
        }
        
        try:
            response = requests.get(self.url, timeout=10, allow_redirects=True, verify=False)
            headers = response.headers
            html = response.text.lower()
            
            result['server'] = headers.get('Server', 'Unknown')
            
            powered_by = headers.get('X-Powered-By', '')
            if powered_by:
                result['framework'] = powered_by
                result['detected'].append(f"Framework: {powered_by}")
            
            # CMS Detection
            cms_signatures = {
                'wordpress': ['wp-content', 'wp-includes', 'wordpress'],
                'drupal': ['drupal', 'sites/default'],
                'joomla': ['joomla', '/components/com_'],
                'shopify': ['shopify', 'cdn.shopify.com'],
                'wix': ['wix.com', 'wixstatic.com'],
                'squarespace': ['squarespace'],
                'magento': ['magento', 'mage'],
                'ghost': ['ghost.io', 'ghost-frontend']
            }
            
            for cms, signatures in cms_signatures.items():
                if any(sig in html for sig in signatures):
                    result['cms'] = cms.capitalize()
                    result['detected'].append(f"CMS: {cms.capitalize()}")
                    break
            
            # JavaScript Library Detection
            js_signatures = {
                'jQuery': ['jquery', 'jquery.min.js'],
                'React': ['react', 'reactdom'],
                'Vue.js': ['vue.js', 'vuejs'],
                'Angular': ['angular', 'ng-app'],
                'Bootstrap': ['bootstrap'],
                'Tailwind': ['tailwind'],
                'Next.js': ['_next/', 'nextjs']
            }
            
            for lib, signatures in js_signatures.items():
                if any(sig in html for sig in signatures):
                    result['javascript_libraries'].append(lib)
                    result['detected'].append(f"JS: {lib}")
            
            # CDN Detection
            cdn_signatures = {
                'Cloudflare': ['cloudflare', 'cf-ray'],
                'AWS CloudFront': ['cloudfront.net', 'x-amz'],
                'Akamai': ['akamai', 'akamaized'],
                'Fastly': ['fastly'],
                'Vercel': ['vercel', 'zeit']
            }
            
            for cdn, signatures in cdn_signatures.items():
                header_str = str(headers).lower()
                if any(sig in html or sig in header_str for sig in signatures):
                    result['cdn'] = cdn
                    result['detected'].append(f"CDN: {cdn}")
                    break
            
            # Analytics Detection
            analytics_signatures = {
                'Google Analytics': ['google-analytics', 'gtag', 'ga.js', 'analytics.js'],
                'Google Tag Manager': ['googletagmanager'],
                'Facebook Pixel': ['fbq', 'facebook.net/en_US/fbevents'],
                'Hotjar': ['hotjar'],
                'Mixpanel': ['mixpanel']
            }
            
            for tool, signatures in analytics_signatures.items():
                if any(sig in html for sig in signatures):
                    result['analytics'].append(tool)
                    result['detected'].append(f"Analytics: {tool}")
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _scan_common_ports(self) -> dict:
        """Scan common ports"""
        common_ports = {
            21: 'FTP',
            22: 'SSH',
            23: 'Telnet',
            25: 'SMTP',
            53: 'DNS',
            80: 'HTTP',
            110: 'POP3',
            143: 'IMAP',
            443: 'HTTPS',
            445: 'SMB',
            993: 'IMAPS',
            995: 'POP3S',
            3306: 'MySQL',
            3389: 'RDP',
            5432: 'PostgreSQL',
            8080: 'HTTP-Alt',
            8443: 'HTTPS-Alt'
        }
        
        result = {
            'open_ports': [],
            'closed_ports': [],
            'scanned': len(common_ports)
        }
        
        def check_port(port_info):
            port, service = port_info
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                conn_result = sock.connect_ex((self.hostname, port))
                sock.close()
                
                if conn_result == 0:
                    return {'port': port, 'service': service, 'status': 'open'}
                return {'port': port, 'service': service, 'status': 'closed'}
            except:
                return {'port': port, 'service': service, 'status': 'filtered'}
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = executor.map(check_port, common_ports.items())
                
                for port_result in futures:
                    if port_result['status'] == 'open':
                        result['open_ports'].append(port_result)
                    else:
                        result['closed_ports'].append(port_result)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_redirects(self) -> dict:
        """Analyze redirect chain"""
        result = {
            'has_redirects': False,
            'chain': [],
            'final_url': self.url,
            'count': 0,
            'https_upgrade': False
        }
        
        try:
            session = requests.Session()
            current_url = self.url
            visited_urls = set()
            max_redirects = 20
            
            while len(result['chain']) < max_redirects:
                if current_url in visited_urls:
                    break
                visited_urls.add(current_url)
                
                try:
                    response = session.get(
                        current_url, 
                        timeout=10, 
                        allow_redirects=False, 
                        verify=False,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get('Location', '')
                        
                        if location:
                            if location.startswith('/'):
                                parsed = urlparse(current_url)
                                location = urlunparse((parsed.scheme, parsed.netloc, location, '', '', ''))
                            elif not location.startswith(('http://', 'https://')):
                                location = urljoin(current_url, location)
                            
                            result['chain'].append({
                                'url': current_url,
                                'status_code': response.status_code,
                                'redirects_to': location
                            })
                            
                            current_url = location
                        else:
                            break
                    else:
                        result['final_url'] = current_url
                        break
                        
                except requests.exceptions.TooManyRedirects:
                    result['error'] = 'Too many redirects'
                    break
                except requests.exceptions.RequestException as e:
                    result['error'] = str(e)
                    break
            
            result['count'] = len(result['chain'])
            result['has_redirects'] = result['count'] > 0
            
            if self.url.startswith('http://') and result['final_url'].startswith('https://'):
                result['https_upgrade'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _calculate_security_score(self):
        """Calculate overall security score based on all findings"""
        score = 0
        findings = []
        
        # SSL Analysis (35 points max)
        ssl_result = self.results.get('ssl_analysis', {})
        if ssl_result.get('enabled'):
            score += 15
            findings.append({'type': 'success', 'message': 'HTTPS/SSL enabled'})
            
            if ssl_result.get('valid'):
                score += 15
                findings.append({'type': 'success', 'message': 'Valid SSL certificate'})
                
                days = ssl_result.get('days_until_expiry')
                if days is not None:
                    if days > 30:
                        score += 5
                        findings.append({'type': 'success', 'message': f'Certificate expires in {days} days'})
                    elif days > 0:
                        score += 3
                        findings.append({'type': 'warning', 'message': f'Certificate expires soon ({days} days)'})
                    else:
                        findings.append({'type': 'danger', 'message': 'Certificate expired'})
                else:
                    score += 5
            else:
                findings.append({'type': 'warning', 'message': 'SSL certificate validation issue'})
        else:
            findings.append({'type': 'danger', 'message': 'No SSL/HTTPS enabled'})
        
        # Security Headers (25 points max)
        headers = self.results.get('security_headers', {})
        present_count = headers.get('present_count', 0)
        
        if present_count >= 6:
            score += 25
            findings.append({'type': 'success', 'message': f'Excellent security headers ({present_count}/8)'})
        elif present_count >= 4:
            score += 20
            findings.append({'type': 'success', 'message': f'Good security headers ({present_count}/8)'})
        elif present_count >= 2:
            score += 15
            findings.append({'type': 'warning', 'message': f'Basic security headers ({present_count}/8)'})
        elif present_count >= 1:
            score += 10
            findings.append({'type': 'warning', 'message': f'Minimal security headers ({present_count}/8)'})
        else:
            score += 5
            findings.append({'type': 'danger', 'message': 'Missing security headers'})
        
        # Port Security (15 points max)
        ports = self.results.get('open_ports', {})
        open_ports = ports.get('open_ports', [])
        
        risky_ports = [21, 22, 23, 25, 3306, 3389, 5432]
        risky_open = [p for p in open_ports if p['port'] in risky_ports]
        
        if not risky_open:
            score += 15
            findings.append({'type': 'success', 'message': 'No risky ports exposed'})
        elif len(risky_open) == 1:
            score += 10
            findings.append({'type': 'warning', 'message': f"Port {risky_open[0]['port']} ({risky_open[0]['service']}) is open"})
        else:
            score += 5
            findings.append({'type': 'danger', 'message': f'{len(risky_open)} risky ports are open'})
        
        # HTTPS/Redirect Analysis (15 points max)
        redirects = self.results.get('redirect_chain', {})
        if self.parsed.scheme == 'https':
            score += 15
            findings.append({'type': 'success', 'message': 'Using HTTPS directly'})
        elif redirects.get('https_upgrade'):
            score += 12
            findings.append({'type': 'success', 'message': 'HTTP to HTTPS redirect enabled'})
        else:
            findings.append({'type': 'warning', 'message': 'No HTTPS redirect detected'})
        
        # Technology (10 points)
        tech = self.results.get('technology', {})
        score += 10
        
        if tech.get('server') and tech.get('server') != 'Unknown':
            findings.append({'type': 'info', 'message': f"Server: {tech.get('server')}"})
        
        if tech.get('cdn'):
            findings.append({'type': 'success', 'message': f"CDN detected: {tech.get('cdn')}"})
        
        self.results['security_score'] = min(score, 100)
        
        if score >= 85:
            self.results['security_grade'] = 'A+'
        elif score >= 75:
            self.results['security_grade'] = 'A'
        elif score >= 65:
            self.results['security_grade'] = 'B'
        elif score >= 55:
            self.results['security_grade'] = 'C'
        elif score >= 45:
            self.results['security_grade'] = 'D'
        else:
            self.results['security_grade'] = 'F'
        
        self.results['findings'] = findings
