"""
FortifAI Scanner Router
Provides API endpoints for URL scanning and security analysis
Integrated from SubVeil project
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import tempfile
import os

from backend.api.scanner.url_extractor import URLExtractor
from backend.api.scanner.deep_scanner import DeepScanner
from backend.api.scanner.network_analyzer import NetworkAnalyzer, TrafficAnalyzer

router = APIRouter()


# Request/Response Models
class URLRequest(BaseModel):
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com"
            }
        }


class BatchURLRequest(BaseModel):
    urls: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "urls": ["https://example.com", "https://google.com"]
            }
        }


class URLExtractionResponse(BaseModel):
    success: bool
    url: str
    data: Optional[dict] = None
    error: Optional[str] = None


class DeepScanResponse(BaseModel):
    success: bool
    target: Optional[str] = None
    hostname: Optional[str] = None
    scan_time: Optional[str] = None
    security_score: Optional[int] = None
    security_grade: Optional[str] = None
    ssl_analysis: Optional[dict] = None
    security_headers: Optional[dict] = None
    dns_records: Optional[dict] = None
    technology: Optional[dict] = None
    open_ports: Optional[dict] = None
    redirect_chain: Optional[dict] = None
    findings: Optional[list] = None
    error: Optional[str] = None


# URL Extraction Endpoints
@router.post("/extract", response_model=URLExtractionResponse, summary="Extract URL Information")
async def extract_url_info(request: URLRequest):
    """
    Extract comprehensive information from a URL including:
    - Protocol, domain, subdomain, TLD
    - Port, path, query parameters
    - IP address resolution
    - WHOIS data and domain intelligence
    - Trust score and risk assessment
    """
    url = request.url.strip()
    
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://', 'ftp://')):
        url = 'https://' + url
    
    extractor = URLExtractor(url)
    info = extractor.extract_all_info()
    
    if info:
        return {
            "success": True,
            "url": url,
            "data": info
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid URL format")


@router.post("/extract-batch", summary="Extract Multiple URLs")
async def extract_batch_urls(request: BatchURLRequest):
    """
    Extract information from multiple URLs at once.
    Returns results for each URL with success/failure status.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    results = []
    
    for url in request.urls:
        url = url.strip()
        if not url:
            continue
            
        # Add scheme if missing
        if not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'https://' + url
        
        extractor = URLExtractor(url)
        info = extractor.extract_all_info()
        
        if info:
            results.append({
                "url": url,
                "success": True,
                "data": info
            })
        else:
            results.append({
                "url": url,
                "success": False,
                "error": "Invalid URL format"
            })
    
    return {
        "success": True,
        "total": len(results),
        "successful": len([r for r in results if r["success"]]),
        "failed": len([r for r in results if not r["success"]]),
        "results": results
    }


# Deep Scan Endpoints
@router.post("/deep-scan", response_model=DeepScanResponse, summary="Deep Security Scan")
async def deep_scan_url(request: URLRequest):
    """
    Perform a comprehensive security scan of a URL including:
    - SSL/TLS certificate analysis
    - Security headers check
    - DNS records lookup
    - Technology detection (CMS, frameworks, libraries)
    - Common port scanning
    - Redirect chain analysis
    - Overall security score and grade
    """
    url = request.url.strip()
    
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    scanner = DeepScanner(url)
    results = scanner.scan_all()
    
    return results


@router.post("/quick-scan", summary="Quick Security Check")
async def quick_scan_url(request: URLRequest):
    """
    Perform a quick security check - only SSL and security headers.
    Faster than deep-scan for quick assessments.
    """
    url = request.url.strip()
    
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    scanner = DeepScanner(url)
    
    # Only perform quick checks
    ssl_result = scanner._analyze_ssl()
    headers_result = scanner._analyze_security_headers()
    
    # Calculate quick score
    score = 0
    if ssl_result.get('enabled'):
        score += 40
        if ssl_result.get('valid'):
            score += 20
    
    present_headers = headers_result.get('present_count', 0)
    score += min(present_headers * 5, 40)
    
    grade = 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D' if score >= 20 else 'F'
    
    return {
        "success": True,
        "url": url,
        "quick_score": score,
        "grade": grade,
        "ssl": {
            "enabled": ssl_result.get('enabled', False),
            "valid": ssl_result.get('valid', False),
            "expires": ssl_result.get('expires'),
            "issuer": ssl_result.get('issuer')
        },
        "security_headers": {
            "present_count": present_headers,
            "total": headers_result.get('total_headers', 8),
            "score_percentage": headers_result.get('score', 0)
        }
    }


# Network Analysis Endpoints
@router.post("/analyze-pcap", summary="Analyze PCAP File")
async def analyze_pcap_file(file: UploadFile = File(...)):
    """
    Upload and analyze a PCAP network capture file.
    Returns protocol distribution, port statistics, and IP address analysis.
    
    Requires pyshark to be installed on the server.
    """
    if not NetworkAnalyzer.is_available():
        raise HTTPException(
            status_code=503, 
            detail="PCAP analysis is not available. pyshark is not installed."
        )
    
    # Validate file type
    if not file.filename.lower().endswith(('.pcap', '.pcapng', '.cap')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PCAP file."
        )
    
    # Read file content
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    if len(content) > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB")
    
    # Analyze
    analyzer = NetworkAnalyzer()
    result = await analyzer.analyze_pcap_async(content, file.filename)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Analysis failed'))
    
    # Add threat analysis
    traffic_analyzer = TrafficAnalyzer()
    threat_analysis = traffic_analyzer.analyze_traffic_patterns(
        result.get('ip_counts', {}),
        result.get('port_counts', {})
    )
    result['threat_analysis'] = threat_analysis
    
    return result


@router.get("/pcap-status", summary="Check PCAP Analysis Availability")
async def check_pcap_status():
    """
    Check if PCAP analysis is available on this server.
    """
    return {
        "available": NetworkAnalyzer.is_available(),
        "message": "PCAP analysis is available" if NetworkAnalyzer.is_available() 
                   else "pyshark is not installed. Install with: pip install pyshark"
    }


# Utility Endpoints
@router.get("/capabilities", summary="List Scanner Capabilities")
async def list_capabilities():
    """
    List all available scanner capabilities and features.
    """
    return {
        "scanner_version": "1.0.0",
        "integrated_from": "SubVeil",
        "capabilities": {
            "url_extraction": {
                "enabled": True,
                "features": [
                    "Protocol detection",
                    "Domain parsing",
                    "Subdomain extraction",
                    "TLD identification",
                    "Query parameter parsing",
                    "IP resolution",
                    "WHOIS lookup",
                    "Domain age analysis",
                    "Trust score calculation"
                ]
            },
            "deep_scan": {
                "enabled": True,
                "features": [
                    "SSL/TLS certificate analysis",
                    "Security headers check",
                    "DNS records lookup",
                    "Technology detection",
                    "Port scanning",
                    "Redirect chain analysis",
                    "Security scoring"
                ]
            },
            "network_analysis": {
                "enabled": NetworkAnalyzer.is_available(),
                "features": [
                    "PCAP file parsing",
                    "Protocol statistics",
                    "Port analysis",
                    "IP traffic analysis",
                    "Threat pattern detection"
                ]
            }
        }
    }
