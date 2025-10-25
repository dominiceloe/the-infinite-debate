"""
Citation validation system for Primary Text links.

Validates links from persona markdown files and database records based on:
1. URL accessibility (HTTP 200 OK)
2. Source trustworthiness (whitelist check)
3. Content verification (author/title mentions)
4. Citation format correctness
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


class TrustedSources:
    """Whitelist of trusted academic and public domain sources."""

    HIGHLY_TRUSTED = {
        'www.gutenberg.org': 'Project Gutenberg',
        'gutenberg.org': 'Project Gutenberg',
        'classics.mit.edu': 'MIT Internet Classics Archive',
        'www.perseus.tufts.edu': 'Perseus Digital Library',
        'perseus.tufts.edu': 'Perseus Digital Library',
        'www.sacred-texts.com': 'Sacred Texts Archive',
        'sacred-texts.com': 'Sacred Texts Archive',
        'archive.org': 'Internet Archive',
        'www.archive.org': 'Internet Archive',
        'plato.stanford.edu': 'Stanford Encyclopedia of Philosophy',
        'iep.utm.edu': 'Internet Encyclopedia of Philosophy',
        'www.iep.utm.edu': 'Internet Encyclopedia of Philosophy',
        'ccel.org': 'Christian Classics Ethereal Library',
        'www.ccel.org': 'Christian Classics Ethereal Library',
    }

    MODERATELY_TRUSTED = {
        'en.wikipedia.org': 'Wikipedia',
        'www.cambridge.org': 'Cambridge University Press',
        'cambridge.org': 'Cambridge University Press',
        'www.bbc.co.uk': 'BBC',
        'bbc.co.uk': 'BBC',
        'philosophybites.com': 'Philosophy Bites',
        'www.philosophybites.com': 'Philosophy Bites',
        'historyofphilosophy.net': 'History of Philosophy Without Any Gaps',
    }

    @classmethod
    def get_trust_level(cls, domain: str) -> Tuple[str, int]:
        """
        Get trust level for a domain.

        Returns:
            Tuple of (source_name, trust_score)
            trust_score: 100 (highly trusted), 75 (moderately trusted), 0 (unknown)
        """
        if domain in cls.HIGHLY_TRUSTED:
            return (cls.HIGHLY_TRUSTED[domain], 100)
        elif domain in cls.MODERATELY_TRUSTED:
            return (cls.MODERATELY_TRUSTED[domain], 75)
        else:
            return ('Unknown Source', 0)


class URLAccessibilityChecker:
    """Checks if URLs are accessible via HTTP request."""

    def __init__(self, timeout: int = 10, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (philosophical-debates-validator/1.0)'
        })

    def check(self, url: str) -> Dict[str, any]:
        """
        Check if URL is accessible.

        Returns:
            {
                'accessible': bool,
                'status_code': int,
                'response_time': float,
                'error': str (if failed)
            }
        """
        result = {
            'accessible': False,
            'status_code': None,
            'response_time': None,
            'error': None
        }

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                response = self.session.head(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response_time = time.time() - start_time

                # Some sites don't support HEAD, try GET
                if response.status_code == 405:
                    start_time = time.time()
                    response = self.session.get(
                        url,
                        timeout=self.timeout,
                        allow_redirects=True
                    )
                    response_time = time.time() - start_time

                result['status_code'] = response.status_code
                result['response_time'] = response_time
                result['accessible'] = 200 <= response.status_code < 400

                if result['accessible']:
                    return result

            except requests.exceptions.Timeout:
                result['error'] = f'Timeout after {self.timeout}s'
            except requests.exceptions.ConnectionError:
                result['error'] = 'Connection failed'
            except requests.exceptions.TooManyRedirects:
                result['error'] = 'Too many redirects'
            except Exception as e:
                result['error'] = f'Unexpected error: {str(e)}'

            # Wait before retry
            if attempt < self.max_retries - 1:
                time.sleep(1)

        return result


class SourceTrustworthinessChecker:
    """Validates source domains against trusted whitelist."""

    def check(self, url: str) -> Dict[str, any]:
        """
        Check source trustworthiness.

        Returns:
            {
                'trusted': bool,
                'trust_score': int (0-100),
                'source_name': str,
                'domain': str
            }
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove 'www.' for comparison
            domain_clean = domain.replace('www.', '')

            source_name, trust_score = TrustedSources.get_trust_level(domain)

            return {
                'trusted': trust_score > 0,
                'trust_score': trust_score,
                'source_name': source_name,
                'domain': domain
            }
        except Exception as e:
            return {
                'trusted': False,
                'trust_score': 0,
                'source_name': 'Invalid URL',
                'domain': None,
                'error': str(e)
            }


class ContentVerifier:
    """Verifies that linked content actually contains the claimed text."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (philosophical-debates-validator/1.0)'
        })

    def check(
        self,
        url: str,
        title: Optional[str] = None,
        author: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Verify content matches title/author.

        Returns:
            {
                'verified': bool,
                'title_found': bool,
                'author_found': bool,
                'confidence': int (0-100),
                'error': str (if failed)
            }
        """
        result = {
            'verified': False,
            'title_found': False,
            'author_found': False,
            'confidence': 0,
            'error': None
        }

        # Skip verification if no title/author provided
        if not title and not author:
            result['error'] = 'No title or author provided for verification'
            return result

        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                result['error'] = f'HTTP {response.status_code}'
                return result

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract text content (title, meta tags, body)
            page_text = ''

            # Check title tag
            if soup.title:
                page_text += soup.title.string or ''

            # Check meta tags
            for meta in soup.find_all('meta'):
                page_text += meta.get('content', '') + ' '

            # Check h1/h2 headers
            for header in soup.find_all(['h1', 'h2', 'h3']):
                page_text += header.get_text() + ' '

            # Check first 5000 characters of body
            body = soup.find('body')
            if body:
                page_text += body.get_text()[:5000]

            page_text = page_text.lower()

            # Check for title
            if title:
                title_variations = [
                    title.lower(),
                    title.lower().replace('the ', ''),
                    re.sub(r'[^\w\s]', '', title.lower())
                ]
                result['title_found'] = any(
                    variant in page_text for variant in title_variations
                )
            else:
                result['title_found'] = None  # Not checked

            # Check for author
            if author:
                author_variations = [
                    author.lower(),
                    author.lower().split()[-1],  # Last name
                    re.sub(r'[^\w\s]', '', author.lower())
                ]
                result['author_found'] = any(
                    variant in page_text for variant in author_variations
                )
            else:
                result['author_found'] = None  # Not checked

            # Calculate confidence
            checks = []
            if result['title_found'] is not None:
                checks.append(result['title_found'])
            if result['author_found'] is not None:
                checks.append(result['author_found'])

            if checks:
                result['confidence'] = int((sum(checks) / len(checks)) * 100)
                result['verified'] = result['confidence'] >= 50

            return result

        except requests.exceptions.Timeout:
            result['error'] = 'Timeout during content fetch'
        except Exception as e:
            result['error'] = f'Content verification failed: {str(e)}'

        return result


class CitationFormatChecker:
    """Validates citation format in markdown."""

    # Markdown link pattern: [text](url)
    MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')

    # Common citation patterns
    PATTERNS = {
        'markdown_link': MARKDOWN_LINK_PATTERN,
        'bare_url': re.compile(r'https?://[^\s]+'),
        'wikipedia': re.compile(r'\*\*Wikipedia:\*\*\s+(https?://[^\s]+)'),
        'stanford': re.compile(r'\*\*Stanford[^:]*:\*\*\s+(https?://[^\s]+)'),
    }

    def check(self, citation_text: str, url: str) -> Dict[str, any]:
        """
        Check citation format.

        Returns:
            {
                'valid_format': bool,
                'format_type': str,
                'has_title': bool,
                'has_source_label': bool,
                'score': int (0-100)
            }
        """
        result = {
            'valid_format': False,
            'format_type': None,
            'has_title': False,
            'has_source_label': False,
            'score': 0
        }

        # Check for markdown link format [Title](URL)
        markdown_match = self.PATTERNS['markdown_link'].search(citation_text)
        if markdown_match:
            link_text, link_url = markdown_match.groups()
            if link_url.strip() == url.strip():
                result['valid_format'] = True
                result['format_type'] = 'markdown_link'
                result['has_title'] = len(link_text.strip()) > 0
                result['score'] = 100
                return result

        # Check for labeled citations (Wikipedia:, Stanford:, etc.)
        for label, pattern in [
            ('wikipedia', self.PATTERNS['wikipedia']),
            ('stanford', self.PATTERNS['stanford'])
        ]:
            match = pattern.search(citation_text)
            if match and url in match.group(1):
                result['valid_format'] = True
                result['format_type'] = f'{label}_labeled'
                result['has_source_label'] = True
                result['score'] = 75
                return result

        # Check for bare URL
        if url in citation_text:
            result['valid_format'] = True
            result['format_type'] = 'bare_url'
            result['score'] = 50
            return result

        return result


class CitationValidator:
    """Main orchestrator for citation validation."""

    def __init__(self):
        self.accessibility_checker = URLAccessibilityChecker()
        self.trustworthiness_checker = SourceTrustworthinessChecker()
        self.content_verifier = ContentVerifier()
        self.format_checker = CitationFormatChecker()

    def validate(
        self,
        url: str,
        citation_text: str = '',
        title: Optional[str] = None,
        author: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Run full validation pipeline on a citation.

        Returns:
            {
                'url': str,
                'overall_score': int (0-100),
                'status': str (valid/broken/suspicious),
                'accessibility': dict,
                'trustworthiness': dict,
                'content_verification': dict,
                'format': dict,
                'recommendations': list
            }
        """
        # Run all checks
        accessibility = self.accessibility_checker.check(url)
        trustworthiness = self.trustworthiness_checker.check(url)
        format_check = self.format_checker.check(citation_text, url)

        # Only verify content if URL is accessible
        if accessibility['accessible']:
            content = self.content_verifier.check(url, title, author)
        else:
            content = {
                'verified': False,
                'error': 'URL not accessible'
            }

        # Calculate overall score (weighted average)
        scores = {
            'accessibility': 100 if accessibility['accessible'] else 0,
            'trustworthiness': trustworthiness['trust_score'],
            'content': content.get('confidence', 0),
            'format': format_check['score']
        }

        # Weights: accessibility is critical, others are important
        weights = {
            'accessibility': 0.4,
            'trustworthiness': 0.3,
            'content': 0.2,
            'format': 0.1
        }

        overall_score = sum(
            scores[key] * weights[key] for key in scores
        )

        # Determine status
        if overall_score >= 75:
            status = 'valid'
        elif accessibility['accessible']:
            status = 'suspicious'
        else:
            status = 'broken'

        # Generate recommendations
        recommendations = []

        if not accessibility['accessible']:
            recommendations.append(
                f"❌ URL inaccessible: {accessibility.get('error', 'Unknown error')}"
            )

        if trustworthiness['trust_score'] == 0:
            recommendations.append(
                f"⚠️ Untrusted source: {trustworthiness['domain']}"
            )

        if not content.get('verified') and accessibility['accessible']:
            recommendations.append(
                "⚠️ Content verification failed - may not match claimed title/author"
            )

        if format_check['score'] < 75:
            recommendations.append(
                "ℹ️ Consider using proper markdown format: [Title](URL)"
            )

        return {
            'url': url,
            'overall_score': int(overall_score),
            'status': status,
            'accessibility': accessibility,
            'trustworthiness': trustworthiness,
            'content_verification': content,
            'format': format_check,
            'recommendations': recommendations
        }
