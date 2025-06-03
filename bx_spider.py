#!/usr/bin/env python3
"""
Bx-Spider - Website Builder Detector and Crawler
A tool to crawl and scan websites
"""

import asyncio
import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import argparse
import sys, os
from typing import List, Set, Optional
import time
import random
from tqdm.asyncio import tqdm
import threading
from colorama import Fore, init
import re

# Initialize Colorama
init(autoreset=True)

# Colors for terminal text
B = Fore.BLUE
W = Fore.WHITE
R = Fore.RED
G = Fore.GREEN
Y = Fore.YELLOW
ungu    =   "\033[1;95m"


def banner():
    print(rf"""
                  {Y}    /      \
                  {Y} \  {G}\  {Y},,  {G}/  {Y}/
                  {G}  '-.`\()/`.-'
{Y}-={G}[ {R}bx{W}-{Y}spider {G}]{Y}=- {G} .--_'(  )'_--.
{W}───────────────── {Y}/ {G}/` /{W}`""`{G}\ `\ {Y}\
                  {G} |  |  {R}><  {G}|  |
                  {Y} \  {G}\      /  {Y}/
                  {G}     '.__.'
""")

def clear_terminal():
    """
    Membersihkan terminal untuk semua OS (Windows, Linux, macOS)
    """
    try:
        # Windows
        if os.name == 'nt':
            os.system('cls')
        # Linux/macOS
        else:
            os.system('clear')
    except Exception as e:
        print(f"{R}Gagal membersihkan terminal: {e}{W}")


class BxSpider:
    def __init__(self, timeout: int = 10, max_redirects: int = 5):
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.wix_sites: List[dict] = []
        self.wordpress_sites: List[dict] = []
        self.no_template_sites: List[dict] = []
        self.scanned_urls: Set[str] = set()
        self.user_agents: List[str] = []
        self._load_user_agents()
        
        # Counters untuk real-time display
        self.wix_count = 0
        self.wordpress_count = 0
        self.no_template_count = 0
        self.total_scanned = 0
        self.lock = threading.Lock()
        self.pbar = None
        self.timer_task = None
        
    def _load_user_agents(self):
        """Memuat user agents dari file user-agents.txt"""
        try:
            with open('user-agents.txt', 'r', encoding='utf-8') as f:
                self.user_agents = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"{ungu}[{W}INFO{ungu}] {W}Berhasil memuat {G}{len(self.user_agents)} user agents")
        except FileNotFoundError:
            print("[ERROR] File user-agents.txt tidak ditemukan")
            # Default user agent jika file tidak ada
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ]
        except Exception as e:
            print(f"[ERROR] Gagal membaca file user-agents.txt: {str(e)}")
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ]
    
    def _get_random_user_agent(self) -> str:
        """Mendapatkan user agent secara random"""
        return random.choice(self.user_agents)
    

    def _update_progress_description(self):
        """Update progress bar description dengan counter real-time"""
        if self.pbar:
            postfix_str = f"{ungu}Wix{W}: {G}{self.wix_count} {Y}| {ungu}WordPress{W}: {G}{self.wordpress_count} {Y}| {ungu}NoTemplate{W}: {G}{self.no_template_count}{W}"
            self.pbar.set_postfix_str(postfix_str)

    async def _timer_updater(self):
        """Update progress bar setiap detik untuk menampilkan waktu yang berjalan"""
        while self.pbar and not self.pbar.disable:
            await asyncio.sleep(0.1)  # Update setiap 100ms untuk smooth animation
            if self.pbar:
                self.pbar.refresh()

    async def check_single_url(self, client: httpx.AsyncClient, url: str) -> Optional[dict]:
        """Check single URL with comprehensive error handling"""
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            if url in self.scanned_urls:
                return None
                
            self.scanned_urls.add(url)
            
            # Gunakan user agent random untuk setiap request
            headers = {"User-Agent": self._get_random_user_agent()}
            response = await client.get(url, headers=headers)
            
            # ✅ CHECK SPECIFIC STATUS CODES BEFORE raise_for_status()
            if response.status_code == 404:
                result = {
                    'url': url,
                    'status_code': 404,
                    'platform': 'Error',
                    'indicator': 'Website tidak ditemukan (404 Not Found)',
                    'title': 'Page Not Found',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with self.lock:
                    self.no_template_sites.append(result)
                    self.no_template_count += 1
                    self._update_progress_description()
                
                return result
            
            elif response.status_code == 403:
                result = {
                    'url': url,
                    'status_code': 403,
                    'platform': 'Protected',
                    'indicator': 'Akses ditolak (403 Forbidden) - Website mungkin diblokir atau dilindungi',
                    'title': 'Access Forbidden',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with self.lock:
                    self.no_template_sites.append(result)
                    self.no_template_count += 1
                    self._update_progress_description()
                
                return result
            
            elif response.status_code == 401:
                result = {
                    'url': url,
                    'status_code': 401,
                    'platform': 'Protected',
                    'indicator': 'Memerlukan autentikasi (401 Unauthorized)',
                    'title': 'Authentication Required',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with self.lock:
                    self.no_template_sites.append(result)
                    self.no_template_count += 1
                    self._update_progress_description()
                
                return result
            
            elif response.status_code == 429:
                result = {
                    'url': url,
                    'status_code': 429,
                    'platform': 'Protected',
                    'indicator': 'Rate limit exceeded (429 Too Many Requests) - Website membatasi akses',
                    'title': 'Rate Limited',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with self.lock:
                    self.no_template_sites.append(result)
                    self.no_template_count += 1
                    self._update_progress_description()
                
                return result
            
            elif response.status_code >= 500:
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'platform': 'Error',
                    'indicator': f'Server error ({response.status_code}) - Website mengalami masalah server',
                    'title': 'Server Error',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with self.lock:
                    self.no_template_sites.append(result)
                    self.no_template_count += 1
                    self._update_progress_description()
                
                return result
            
            elif response.status_code == 202:
                # Parse content untuk cek apakah benar-benar protected
                try:
                    parser = HTMLParser(response.text)
                    
                    # Check for WordPress first
                    comment_form_comment = parser.css_first('.comment-form-comment')
                    commentform_id = parser.css_first('#commentform')
                    
                    if comment_form_comment and commentform_id:
                        result = {
                            'url': url,
                            'status_code': 202,
                            'platform': 'WordPress',
                            'indicator': 'WordPress dengan status 202 (comment-form-comment + commentform)',
                            'title': self._get_title(parser),
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        with self.lock:
                            self.wordpress_sites.append(result)
                            self.wordpress_count += 1
                            self._update_progress_description()
                        
                        return result
                    
                    # Check for Wix
                    meta_tags = parser.css('meta[name="generator"]')
                    for meta in meta_tags:
                        content = meta.attributes.get('content', '').lower()
                        if 'wix.com' in content:
                            result = {
                                'url': url,
                                'status_code': 202,
                                'platform': 'Wix',
                                'indicator': f'Wix dengan status 202 ({meta.attributes.get("content")})',
                                'title': self._get_title(parser),
                                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            with self.lock:
                                self.wix_sites.append(result)
                                self.wix_count += 1
                                self._update_progress_description()
                            
                            return result
                    
                    # Jika 202 tapi bukan Wix/WordPress, masuk Protected
                    result = {
                        'url': url,
                        'status_code': 202,
                        'platform': 'Protected',
                        'indicator': 'Protected (202) - Website membatasi akses',
                        'title': self._get_title(parser),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    with self.lock:
                        self.no_template_sites.append(result)
                        self.no_template_count += 1
                        self._update_progress_description()
                    
                    return result
                    
                except Exception:
                    # Jika gagal parse, tetap anggap protected
                    result = {
                        'url': url,
                        'status_code': 202,
                        'platform': 'Protected',
                        'indicator': 'Status 202 - Tidak dapat menganalisis content',
                        'title': 'Unknown',
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    with self.lock:
                        self.no_template_sites.append(result)
                        self.no_template_count += 1
                        self._update_progress_description()
                    
                    return result
            
            # ✅ UNTUK STATUS 200 DAN LAINNYA, LANJUTKAN NORMAL PROCESSING
            response.raise_for_status()  # Ini akan raise jika ada error lain
            
            # Parse HTML untuk status sukses
            parser = HTMLParser(response.text)
            
            # Check for WordPress
            comment_form_comment = parser.css_first('.comment-form-comment')
            commentform_id = parser.css_first('#commentform')
            
            if comment_form_comment and commentform_id:
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'platform': 'WordPress',
                    'indicator': 'comment-form-comment class DAN commentform ID ditemukan',
                    'title': self._get_title(parser),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with self.lock:
                    self.wordpress_sites.append(result)
                    self.wordpress_count += 1
                    self._update_progress_description()
                
                return result
            
            # Check for Wix
            meta_tags = parser.css('meta[name="generator"]')
            
            for meta in meta_tags:
                content = meta.attributes.get('content', '').lower()
                if 'wix.com' in content:
                    result = {
                        'url': url,
                        'status_code': response.status_code,
                        'platform': 'Wix',
                        'indicator': meta.attributes.get('content'),
                        'title': self._get_title(parser),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    with self.lock:
                        self.wix_sites.append(result)
                        self.wix_count += 1
                        self._update_progress_description()
                    
                    return result
            
            # No template detected
            result = {
                'url': url,
                'status_code': response.status_code,
                'platform': 'NoTemplate',
                'indicator': 'Tidak terdeteksi sebagai Wix atau WordPress',
                'title': self._get_title(parser),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with self.lock:
                self.no_template_sites.append(result)
                self.no_template_count += 1
                self._update_progress_description()
            
            return result
            
        except httpx.HTTPStatusError as e:
            # ✅ HANDLE HTTP STATUS ERRORS YANG TIDAK TERTANGKAP DI ATAS
            status_code = e.response.status_code if e.response else 0
            
            if status_code == 404:
                platform = 'Error'
                indicator = 'Website tidak ditemukan (404 Not Found)'
            elif status_code == 403:
                platform = 'Protected'
                indicator = 'Akses ditolak (403 Forbidden)'
            elif status_code == 401:
                platform = 'Protected'
                indicator = 'Memerlukan autentikasi (401 Unauthorized)'
            elif status_code == 429:
                platform = 'Protected'
                indicator = 'Rate limit exceeded (429 Too Many Requests)'
            elif status_code >= 500:
                platform = 'Error'
                indicator = f'Server error ({status_code})'
            else:
                platform = 'Error'
                indicator = f'HTTP Error ({status_code})'
            
            result = {
                'url': url,
                'status_code': status_code,
                'platform': platform,
                'indicator': indicator,
                'title': 'Error',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with self.lock:
                self.no_template_sites.append(result)
                self.no_template_count += 1
                self._update_progress_description()
            
            return result
            
        except httpx.RequestError as e:
            # ✅ HANDLE NETWORK ERRORS (DNS, Connection, Timeout, etc.)
            result = {
                'url': url,
                'status_code': 0,
                'platform': 'Error',
                'indicator': f'Network error: {str(e)[:100]}',
                'title': 'Connection Error',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with self.lock:
                self.no_template_sites.append(result)
                self.no_template_count += 1
                self._update_progress_description()
            
            return result
            
        except Exception as e:
            # ✅ HANDLE UNEXPECTED ERRORS
            result = {
                'url': url,
                'status_code': 0,
                'platform': 'Error',
                'indicator': f'Unexpected error: {str(e)[:100]}',
                'title': 'Unknown Error',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with self.lock:
                self.no_template_sites.append(result)
                self.no_template_count += 1
                self._update_progress_description()
            
            return result
            
        finally:
            if self.pbar:
                self.pbar.update(1)
    
    def _get_title(self, parser: HTMLParser) -> str:
        """Extract page title"""
        title_tag = parser.css_first('title')
        return title_tag.text().strip() if title_tag else "Tidak ada judul"
    
    async def scan_urls(self, urls: List[str], concurrent_limit: int = 10):
        """Scan multiple URLs concurrently with progress bar"""
        semaphore = asyncio.Semaphore(concurrent_limit)
        self.pbar = tqdm(
            total=len(urls),
            unit="url",
            postfix="Wix: 0 | WordPress: 0 | NoTemplate: 0", 
            colour='green',
            dynamic_ncols=True,
            smoothing=0.3,
            mininterval=0.1,
            maxinterval=0.5,
            miniters=1
        )
                
        # Start timer updater untuk waktu yang berjalan
        self.timer_task = asyncio.create_task(self._timer_updater())
        
        async def scan_with_semaphore(client: httpx.AsyncClient, url: str):
            async with semaphore:
                return await self.check_single_url(client, url)
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=self.max_redirects
            ) as client:
                tasks = [scan_with_semaphore(client, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # Stop timer dan close progress bar
            if self.timer_task:
                self.timer_task.cancel()
                try:
                    await self.timer_task
                except asyncio.CancelledError:
                    pass
            
            if self.pbar:
                self.pbar.close()
    
    def print_results(self):
        """Print comprehensive scan results with detailed statistics"""
    
        # ✅ CATEGORIZE RESULTS
        protected_sites = [site for site in self.no_template_sites if site['platform'] == 'Protected']
        error_sites = [site for site in self.no_template_sites if site['platform'] == 'Error']
        regular_no_template = [site for site in self.no_template_sites if site['platform'] == 'NoTemplate']
    
        print("\n" + "═"*60)
        print(f"🕷️  {G}HASIL PEMINDAIAN BX-SPIDER COMPREHENSIVE")
        print("═"*60)
        print(f"📊 Total URL yang dipindai: {len(self.scanned_urls)}")
        print(f"🎯 Situs Wix ditemukan: {len(self.wix_sites)}{W}")
        print(f"🎯 Situs WordPress ditemukan: {len(self.wordpress_sites)}{W}")
        print(f"🛡️ Situs Protected: {len(protected_sites)}{W}")
        print(f"❌ Situs Error: {len(error_sites)}{W}")
        print(f"🔍 Situs Platform Lain: {len(regular_no_template)}{W}")
    
        # ✅ DETAILED BREAKDOWN
        if protected_sites:
            print(f"\n{Y}🛡️  PROTECTED SITES BREAKDOWN:{W}")
            status_breakdown = {}
            for site in protected_sites:
                status = site['status_code']
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
            for status, count in sorted(status_breakdown.items()):
                status_name = {
                    202: "Accepted/Maintenance",
                    403: "Forbidden/Blocked", 
                    401: "Authentication Required",
                    429: "Rate Limited"
                }.get(status, f"Status {status}")
                print(f"  {W}├─ {Y}{status}{W}: {Y}{count} sites ({W}{status_name}{Y}){W}")
    
        if error_sites:
            print(f"\n{R}❌ ERROR SITES BREAKDOWN:{W}")
            error_breakdown = {}
            for site in error_sites:
                status = site['status_code']
                error_breakdown[status] = error_breakdown.get(status, 0) + 1
        
            for status, count in sorted(error_breakdown.items()):
                status_name = {
                    0: "Network/DNS Error",
                    404: "Not Found",
                    500: "Internal Server Error",
                    502: "Bad Gateway", 
                    503: "Service Unavailable",
                    504: "Gateway Timeout"
                }.get(status, f"Error {status}")
                print(f"  {R}├─ {status}: {count} sites ({status_name}){W}")
    
        print("="*70)
    
        # ✅ DETAILED RESULTS
        if self.wix_sites:
            print(f"\n{G}🎯 SITUS WIX {W}{len(self.wix_sites)}:{W}")
            for i, site in enumerate(self.wix_sites, 1):
                print(f"  [{i}] {site['url']} | Status: {G}{site['status_code']}")

        if self.wordpress_sites:
            print(f"\n{G}🎯 SITUS WORDPRESS {W}{len(self.wordpress_sites)}:{W}")
            for i, site in enumerate(self.wordpress_sites, 1):
                print(f"  [{i}] {site['url']} | Status: {G}{site['status_code']}")

        if protected_sites:
            print(f"\n{Y}🛡️  SITUS PROTECTED {W}{len(protected_sites)}:{W}")
            for i, site in enumerate(protected_sites, 1):
                print(f"  [{i}] {site['url']} | Status: {Y}{site['status_code']} {W}| {site['indicator'][:50]}...")

        if error_sites:
            print(f"\n{R}❌ SITUS ERROR {W}{len(error_sites)}:{W}")
            for i, site in enumerate(error_sites, 1):
                print(f"  [{i}] {site['url']} | Status: {R}{site['status_code']} {W}| {site['indicator'][:50]}...")

        if regular_no_template:
            print(f"\n{ungu}🔍 SITUS PLATFORM LAIN {W}{len(regular_no_template)}:{W}")
            for i, site in enumerate(regular_no_template, 1):
                print(f"  [{i}] {site['url']} | Status: {ungu}{site['status_code']}")

        if not self.wix_sites and not self.wordpress_sites and not self.no_template_sites:
            print(f"\n{R}❌ Tidak ada situs yang berhasil dipindai.{W}")

    def save_results(self, output_file: str = None):
        """Save results with enhanced categorization"""
        try:
            # ✅ CATEGORIZE RESULTS
            protected_sites = [site for site in self.no_template_sites if site['platform'] == 'Protected']
            error_sites = [site for site in self.no_template_sites if site['platform'] == 'Error']
            regular_no_template = [site for site in self.no_template_sites if site['platform'] == 'NoTemplate']
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("BX-SPIDER COMPREHENSIVE SCAN RESULTS\n")
                    f.write("="*50 + "\n\n")
                    
                    # Wix Sites
                    if self.wix_sites:
                        f.write("WIX SITES:\n")
                        f.write("-"*20 + "\n")
                        for site in self.wix_sites:
                            f.write(f"{site['url']}\n")
                        f.write("\n")
                    
                    # WordPress Sites
                    if self.wordpress_sites:
                        f.write("WORDPRESS SITES:\n")
                        f.write("-"*20 + "\n")
                        for site in self.wordpress_sites:
                            f.write(f"{site['url']}\n")
                        f.write("\n")
                    
                    # Protected Sites (202, 403, 401, 429)
                    if protected_sites:
                        f.write("PROTECTED SITES (Security/Access Issues):\n")
                        f.write("-"*45 + "\n")
                        for site in protected_sites:
                            f.write(f"{site['url']}\n")
                        f.write("\n")
                    
                    # Error Sites (404, 5xx, Network errors)
                    if error_sites:
                        f.write("ERROR SITES (Not Found/Server Issues):\n")
                        f.write("-"*45 + "\n")
                        for site in error_sites:
                            f.write(f"{site['url']}\n")
                        f.write("\n")
                    
                    # Regular No Template Sites
                    if regular_no_template:
                        f.write("NO TEMPLATE SITES (Other Platforms):\n")
                        f.write("-"*35 + "\n")
                        for site in regular_no_template:
                            f.write(f"{site['url']}\n")
            
                print(f"\n{G}[{W}INFO{G}] Semua hasil disimpan ke {W}{output_file}{W}")
            
            else:
                # ✅ SAVE TO SEPARATE FILES WITH ENHANCED CATEGORIZATION
            
                # Save Wix results
                if self.wix_sites:
                    with open("wix_sites.txt", 'w', encoding='utf-8') as f:
                        f.write("Bx-Spider - Website Wix.com\n")
                        f.write("="*30 + "\n\n")
                        for site in self.wix_sites:
                            f.write(f"{site['url']}\n")
                    print(f"\n{W}[{G}INFO{W}] {len(self.wix_sites)} Wix sites {Y}→ {G}wix_sites.txt{W}")
            
                # Save WordPress results
                if self.wordpress_sites:
                    with open("wordpress.txt", 'w', encoding='utf-8') as f:
                        f.write("Bx-Spider - Website WordPress\n")
                        f.write("="*30 + "\n\n")
                        for site in self.wordpress_sites:
                            f.write(f"{site['url']}\n")
                    print(f"{W}[{G}INFO{W}] {len(self.wordpress_sites)} WordPress sites{Y} → {G}wordpress.txt{W}")
            
                # ✅ SAVE PROTECTED SITES (202, 403, 401, 429)
                if protected_sites:
                    with open("protected_sites.txt", 'w', encoding='utf-8') as f:
                        f.write("Bx-Spider - Protected/Restricted Websites\n")
                        f.write("Status: 202, 403, 401, 429\n")
                        f.write("="*40 + "\n\n")
                    
                        # Group by status code
                        status_groups = {}
                        for site in protected_sites:
                            status = site['status_code']
                            if status not in status_groups:
                                status_groups[status] = []
                            status_groups[status].append(site)
                    
                        for status_code in sorted(status_groups.keys()):
                            f.write(f"--- STATUS {status_code} ---\n")
                            for site in status_groups[status_code]:
                                f.write(f"{site['url']}\n")
                            f.write("\n")
                
                    print(f"{W}[{G}INFO{W}] {len(protected_sites)} Protected sites {Y}→ {G}protected_sites.txt{W}")
                
                    # Print breakdown
                    status_breakdown = {}
                    for site in protected_sites:
                        status = site['status_code']
                        status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                    for status, count in sorted(status_breakdown.items()):
                        status_name = {
                            202: "Accepted/Maintenance",
                            403: "Forbidden", 
                            401: "Unauthorized",
                            429: "Rate Limited"
                        }.get(status, f"Status {status}")
                        print(f"  {W}├─ {Y}{status}{W}: {Y}{count} sites ({W}{status_name}{Y}){W}")
            
                # ✅ SAVE ERROR SITES (404, 5xx, Network errors)
                if error_sites:
                    with open("error_sites.txt", 'w', encoding='utf-8') as f:
                        f.write("Bx-Spider - Error/Unreachable Websites\n")
                        f.write("Status: 404, 5xx, Network errors\n")
                        f.write("="*40 + "\n\n")
                    
                        # Group by error type
                        error_groups = {}
                        for site in error_sites:
                            status = site['status_code']
                            if status not in error_groups:
                                error_groups[status] = []
                            error_groups[status].append(site)
                    
                        for status_code in sorted(error_groups.keys()):
                            if status_code == 0:
                                f.write("--- NETWORK ERRORS ---\n")
                            else:
                                f.write(f"--- STATUS {status_code} ---\n")
                        
                            for site in error_groups[status_code]:
                                f.write(f"{site['url']}\n")
                            f.write("\n")
                
                    print(f"{W}[{G}INFO{W}] {len(error_sites)} Error sites {Y}→ {G}error_sites.txt{W}")
                
                    # Print breakdown
                    error_breakdown = {}
                    for site in error_sites:
                        status = site['status_code']
                        error_breakdown[status] = error_breakdown.get(status, 0) + 1
                
                    for status, count in sorted(error_breakdown.items()):
                        status_name = {
                            0: "Network/DNS Error",
                            404: "Not Found",
                            500: "Internal Server Error",
                            502: "Bad Gateway",
                            503: "Service Unavailable",
                            504: "Gateway Timeout"
                        }.get(status, f"Error {status}")
                        print(f"  {R}├─ {status}: {count} sites ({status_name}){W}")
            
                # Save regular NoTemplate results
                if regular_no_template:
                    with open("no_template.txt", 'w', encoding='utf-8') as f:
                        f.write("Bx-Spider - Other Platform Websites\n")
                        f.write("="*35 + "\n\n")
                        for site in regular_no_template:
                            f.write(f"{site['url']}\n")
                    print(f"{W}[{G}INFO{W}] {len(regular_no_template)} Other sites {Y}→ {G}no_template.txt{W}")
                
        except Exception as e:
            print(f"{R}[ERROR] Gagal menyimpan hasil: {str(e)}{W}")


def load_urls_from_file(filename: str) -> List[str]:
    """Load URLs from text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return urls
    except FileNotFoundError:
        print(f"[ERROR] File tidak ditemukan: {filename}")
        return []
    except Exception as e:
        print(f"[ERROR] Gagal membaca file {filename}: {str(e)}")
        return []

async def main():
    parser = argparse.ArgumentParser(
        description="Bx-Spider - tools crawling website",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python bx_spider.py -u example.com
  python bx_spider.py -f urls.txt
  python bx_spider.py -u example.com -o results.txt -c 20
        """
    )
    
    parser.add_argument('-u', '--urls', nargs='+', help='URL yang akan dipindai')
    parser.add_argument('-f', '--file', help='File berisi URL (satu per baris)')
    parser.add_argument('-o', '--output', help='File output untuk hasil Wix')
    parser.add_argument('-c', '--concurrent', type=int, default=10, help='Jumlah request bersamaan (default: 10)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Timeout request dalam detik per ulrs (default: 10)')
    
    args = parser.parse_args()
    
    # Collect URLs
    urls = []
    if args.urls:
        urls.extend(args.urls)
    if args.file:
        urls.extend(load_urls_from_file(args.file))
    
    if not urls:
        print("[ERROR] Tidak ada URL yang diberikan. Gunakan opsi -u atau -f.")
        parser.print_help()
        sys.exit(1)
    
    # Initialize spider
    spider = BxSpider(timeout=args.timeout)
    
    print(f"{ungu}[{W}INFO{ungu}] {W}Memulai Crawler Bx-Spider")
    print(f"{ungu}[{W}INFO{ungu}] {W}URL yang akan dipindai: {G}{len(urls)}")
    print(f"{ungu}[{W}INFO{ungu}] {W}Request bersamaan: {G}{args.concurrent}")
    print(f"{ungu}[{W}INFO{ungu}] {W}Timeout: {G}{args.timeout}s")
    print(f"{ungu}{"─" *37}")

    
    # Start scanning
    start_time = time.time()
    await spider.scan_urls(urls, concurrent_limit=args.concurrent)
    end_time = time.time()
    
    # Print results
    spider.print_results()
    print(f"{G}\nCrawling selesai dalam {end_time - start_time:.2f} detik")
    
    # Save results
    if args.output or spider.wix_sites or spider.wordpress_sites or spider.no_template_sites:
        spider.save_results(args.output)

if __name__ == "__main__":
    try:
        clear_terminal()
        banner()
        print(f"{ungu}{'═'*37}{W}")
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n[INFO] Pemindaian dihentikan oleh pengguna")
        sys.exit(0)
