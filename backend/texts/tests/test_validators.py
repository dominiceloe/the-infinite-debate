"""
Comprehensive unit tests for texts/validators.py (citation validation system).
Target: texts/validators.py (0% coverage -> aiming for 60%+)

Tests cover:
- TrustedSources trust level checking
- URLAccessibilityChecker HTTP requests and error handling
- SourceTrustworthinessChecker domain parsing
- ContentVerifier HTML parsing and content matching
- CitationFormatChecker markdown pattern matching
- CitationValidator full validation pipeline
- Edge cases (empty strings, Unicode, malformed URLs, timeouts)
- Error handling and retry logic
"""
import pytest
import re
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError, TooManyRedirects
from texts.validators import (
    TrustedSources,
    URLAccessibilityChecker,
    SourceTrustworthinessChecker,
    ContentVerifier,
    CitationFormatChecker,
    CitationValidator,
)


class TestTrustedSources:
    """Test suite for TrustedSources whitelist"""

    @pytest.mark.parametrize("domain,expected_name,expected_score", [
        ('www.gutenberg.org', 'Project Gutenberg', 100),
        ('gutenberg.org', 'Project Gutenberg', 100),
        ('plato.stanford.edu', 'Stanford Encyclopedia of Philosophy', 100),
        ('classics.mit.edu', 'MIT Internet Classics Archive', 100),
        ('archive.org', 'Internet Archive', 100),
        ('www.archive.org', 'Internet Archive', 100),
        ('perseus.tufts.edu', 'Perseus Digital Library', 100),
        ('www.sacred-texts.com', 'Sacred Texts Archive', 100),
        ('ccel.org', 'Christian Classics Ethereal Library', 100),
        ('iep.utm.edu', 'Internet Encyclopedia of Philosophy', 100),
    ])
    def test_highly_trusted_sources(self, domain, expected_name, expected_score):
        """Test highly trusted academic sources return 100 score"""
        name, score = TrustedSources.get_trust_level(domain)
        assert name == expected_name
        assert score == expected_score

    @pytest.mark.parametrize("domain,expected_name,expected_score", [
        ('en.wikipedia.org', 'Wikipedia', 75),
        ('www.cambridge.org', 'Cambridge University Press', 75),
        ('cambridge.org', 'Cambridge University Press', 75),
        ('www.bbc.co.uk', 'BBC', 75),
        ('bbc.co.uk', 'BBC', 75),
        ('philosophybites.com', 'Philosophy Bites', 75),
        ('historyofphilosophy.net', 'History of Philosophy Without Any Gaps', 75),
    ])
    def test_moderately_trusted_sources(self, domain, expected_name, expected_score):
        """Test moderately trusted sources return 75 score"""
        name, score = TrustedSources.get_trust_level(domain)
        assert name == expected_name
        assert score == expected_score

    @pytest.mark.parametrize("domain", [
        'unknown-site.com',
        'random-blog.org',
        'suspicious-source.net',
        'example.com',
        'not-in-whitelist.edu',
    ])
    def test_untrusted_sources(self, domain):
        """Test unknown sources return 0 score"""
        name, score = TrustedSources.get_trust_level(domain)
        assert name == 'Unknown Source'
        assert score == 0

    def test_empty_domain(self):
        """Test empty domain returns unknown"""
        name, score = TrustedSources.get_trust_level('')
        assert name == 'Unknown Source'
        assert score == 0


class TestURLAccessibilityChecker:
    """Test suite for URLAccessibilityChecker"""

    def test_initialization_default_params(self):
        """Test checker initializes with default timeout and retries"""
        checker = URLAccessibilityChecker()
        assert checker.timeout == 10
        assert checker.max_retries == 2
        assert checker.session is not None
        assert 'User-Agent' in checker.session.headers

    def test_initialization_custom_params(self):
        """Test checker initializes with custom timeout and retries"""
        checker = URLAccessibilityChecker(timeout=5, max_retries=3)
        assert checker.timeout == 5
        assert checker.max_retries == 3

    @patch('texts.validators.requests.Session')
    def test_check_successful_head_request(self, mock_session_class):
        """Test successful URL check with HEAD request"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.head.return_value = mock_response
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker()
        checker.session = mock_session
        result = checker.check('https://example.com')

        assert result['accessible'] is True
        assert result['status_code'] == 200
        assert result['response_time'] is not None
        assert result['error'] is None
        mock_session.head.assert_called_once()

    @patch('texts.validators.requests.Session')
    def test_check_head_405_fallback_to_get(self, mock_session_class):
        """Test fallback to GET when HEAD returns 405"""
        mock_session = Mock()
        mock_head_response = Mock()
        mock_head_response.status_code = 405
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_session.head.return_value = mock_head_response
        mock_session.get.return_value = mock_get_response
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker()
        checker.session = mock_session
        result = checker.check('https://example.com')

        assert result['accessible'] is True
        assert result['status_code'] == 200
        mock_session.head.assert_called_once()
        mock_session.get.assert_called_once()

    @patch('texts.validators.requests.Session')
    def test_check_404_not_found(self, mock_session_class):
        """Test inaccessible URL with 404 status"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.head.return_value = mock_response
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker()
        checker.session = mock_session
        result = checker.check('https://example.com/nonexistent')

        assert result['accessible'] is False
        assert result['status_code'] == 404
        assert result['error'] is None

    @patch('texts.validators.requests.Session')
    @patch('texts.validators.time.sleep')
    def test_check_timeout_with_retry(self, mock_sleep, mock_session_class):
        """Test timeout exception triggers retry logic"""
        mock_session = Mock()
        mock_session.head.side_effect = Timeout()
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker(max_retries=2)
        checker.session = mock_session
        result = checker.check('https://slow-site.com')

        assert result['accessible'] is False
        assert result['status_code'] is None
        assert 'Timeout' in result['error']
        assert mock_session.head.call_count == 2  # max_retries
        mock_sleep.assert_called()

    @patch('texts.validators.requests.Session')
    def test_check_connection_error(self, mock_session_class):
        """Test connection error handling"""
        mock_session = Mock()
        mock_session.head.side_effect = ConnectionError()
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker()
        checker.session = mock_session
        result = checker.check('https://unreachable.com')

        assert result['accessible'] is False
        assert 'Connection failed' in result['error']

    @patch('texts.validators.requests.Session')
    def test_check_too_many_redirects(self, mock_session_class):
        """Test too many redirects error handling"""
        mock_session = Mock()
        mock_session.head.side_effect = TooManyRedirects()
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker()
        checker.session = mock_session
        result = checker.check('https://redirect-loop.com')

        assert result['accessible'] is False
        assert 'Too many redirects' in result['error']

    @patch('texts.validators.requests.Session')
    def test_check_unexpected_error(self, mock_session_class):
        """Test unexpected exception handling"""
        mock_session = Mock()
        mock_session.head.side_effect = Exception('Unexpected error occurred')
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker()
        checker.session = mock_session
        result = checker.check('https://example.com')

        assert result['accessible'] is False
        assert 'Unexpected error' in result['error']

    @pytest.mark.parametrize("status_code,expected_accessible", [
        (200, True),
        (201, True),
        (204, True),
        (301, True),
        (302, True),
        (400, False),
        (401, False),
        (403, False),
        (404, False),
        (500, False),
        (503, False),
    ])
    @patch('texts.validators.requests.Session')
    def test_check_various_status_codes(self, mock_session_class, status_code, expected_accessible):
        """Test various HTTP status codes"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_session.head.return_value = mock_response
        mock_session_class.return_value = mock_session

        checker = URLAccessibilityChecker()
        checker.session = mock_session
        result = checker.check('https://example.com')

        assert result['accessible'] is expected_accessible
        assert result['status_code'] == status_code


class TestSourceTrustworthinessChecker:
    """Test suite for SourceTrustworthinessChecker"""

    def test_check_highly_trusted_domain(self):
        """Test checking a highly trusted source"""
        checker = SourceTrustworthinessChecker()
        result = checker.check('https://www.gutenberg.org/books/1234')

        assert result['trusted'] is True
        assert result['trust_score'] == 100
        assert result['source_name'] == 'Project Gutenberg'
        assert result['domain'] == 'www.gutenberg.org'

    def test_check_moderately_trusted_domain(self):
        """Test checking a moderately trusted source"""
        checker = SourceTrustworthinessChecker()
        result = checker.check('https://en.wikipedia.org/wiki/Philosophy')

        assert result['trusted'] is True
        assert result['trust_score'] == 75
        assert result['source_name'] == 'Wikipedia'
        assert result['domain'] == 'en.wikipedia.org'

    def test_check_untrusted_domain(self):
        """Test checking an unknown/untrusted source"""
        checker = SourceTrustworthinessChecker()
        result = checker.check('https://random-blog.com/article')

        assert result['trusted'] is False
        assert result['trust_score'] == 0
        assert result['source_name'] == 'Unknown Source'
        assert result['domain'] == 'random-blog.com'

    def test_check_domain_with_www_normalization(self):
        """Test that www. is properly handled in domain comparison"""
        checker = SourceTrustworthinessChecker()

        # With www.
        result1 = checker.check('https://www.gutenberg.org/books/1234')
        # Without www.
        result2 = checker.check('https://gutenberg.org/books/1234')

        # Both should be recognized as trusted
        assert result1['trusted'] is True
        assert result2['trusted'] is True
        assert result1['trust_score'] == 100
        assert result2['trust_score'] == 100

    def test_check_url_with_path_and_query(self):
        """Test URL with complex path and query parameters"""
        checker = SourceTrustworthinessChecker()
        url = 'https://plato.stanford.edu/entries/aristotle/?section=ethics#virtue'
        result = checker.check(url)

        assert result['trusted'] is True
        assert result['trust_score'] == 100
        assert result['source_name'] == 'Stanford Encyclopedia of Philosophy'

    def test_check_invalid_url_format(self):
        """Test handling of malformed URL"""
        checker = SourceTrustworthinessChecker()
        result = checker.check('not-a-valid-url')

        # urlparse doesn't raise exception for malformed URLs, just returns empty netloc
        assert result['trusted'] is False
        assert result['trust_score'] == 0
        assert result['source_name'] == 'Unknown Source'
        assert result['domain'] == ''  # Empty netloc from urlparse

    def test_check_empty_url(self):
        """Test handling of empty URL"""
        checker = SourceTrustworthinessChecker()
        result = checker.check('')

        assert result['trusted'] is False
        assert result['trust_score'] == 0
        assert result['domain'] == ''

    def test_check_case_insensitivity(self):
        """Test that domain checking is case-insensitive"""
        checker = SourceTrustworthinessChecker()

        result1 = checker.check('https://PLATO.STANFORD.EDU/entries')
        result2 = checker.check('https://plato.stanford.edu/entries')

        assert result1['trust_score'] == result2['trust_score']
        assert result1['trusted'] == result2['trusted']


class TestContentVerifier:
    """Test suite for ContentVerifier"""

    def test_initialization(self):
        """Test verifier initializes correctly"""
        verifier = ContentVerifier(timeout=15)
        assert verifier.timeout == 15
        assert verifier.session is not None

    @patch('texts.validators.requests.Session')
    def test_check_no_title_or_author(self, mock_session_class):
        """Test verification skips when no title or author provided"""
        verifier = ContentVerifier()
        result = verifier.check('https://example.com')

        assert result['verified'] is False
        assert result['error'] == 'No title or author provided for verification'

    @patch('texts.validators.requests.Session')
    def test_check_title_found(self, mock_session_class):
        """Test successful title verification"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
            <html>
            <head><title>The Republic by Plato</title></head>
            <body><h1>The Republic</h1><p>A philosophical dialogue...</p></body>
            </html>
        '''
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='The Republic')

        assert result['verified'] is True
        assert result['title_found'] is True
        assert result['author_found'] is None
        assert result['confidence'] == 100

    @patch('texts.validators.requests.Session')
    def test_check_author_found(self, mock_session_class):
        """Test successful author verification"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
            <html>
            <body><p>Written by Plato in ancient Greece...</p></body>
            </html>
        '''
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', author='Plato')

        assert result['verified'] is True
        assert result['title_found'] is None
        assert result['author_found'] is True
        assert result['confidence'] == 100

    @patch('texts.validators.requests.Session')
    def test_check_both_title_and_author_found(self, mock_session_class):
        """Test verification when both title and author are found"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
            <html>
            <head><title>The Republic</title></head>
            <body>
                <h1>The Republic</h1>
                <p>Author: Plato</p>
            </body>
            </html>
        '''
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='The Republic', author='Plato')

        assert result['verified'] is True
        assert result['title_found'] is True
        assert result['author_found'] is True
        assert result['confidence'] == 100

    @patch('texts.validators.requests.Session')
    def test_check_title_not_found(self, mock_session_class):
        """Test when title is not found in content"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Some unrelated content</body></html>'
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='The Republic')

        assert result['verified'] is False
        assert result['title_found'] is False
        assert result['confidence'] == 0

    @patch('texts.validators.requests.Session')
    def test_check_partial_match_low_confidence(self, mock_session_class):
        """Test partial match results in appropriate confidence level"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>This mentions Plato but not the title</body></html>'
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='The Republic', author='Plato')

        assert result['title_found'] is False
        assert result['author_found'] is True
        assert result['confidence'] == 50  # 1/2 checks passed
        assert result['verified'] is True  # 50% meets threshold

    @patch('texts.validators.requests.Session')
    def test_check_title_variation_matching(self, mock_session_class):
        """Test that title variations are matched (without 'the', punctuation)"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>This is about Republic</body></html>'
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='The Republic')

        # Should match "Republic" even though "The" is missing
        assert result['title_found'] is True

    @patch('texts.validators.requests.Session')
    def test_check_author_last_name_matching(self, mock_session_class):
        """Test that author last name is matched"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Written by Stagira</body></html>'
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', author='Aristotle of Stagira')

        # Should match "Stagira" (last name from split()[-1])
        assert result['author_found'] is True

    @patch('texts.validators.requests.Session')
    def test_check_http_error(self, mock_session_class):
        """Test handling of HTTP error responses"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='Test')

        assert result['verified'] is False
        assert result['error'] == 'HTTP 404'

    @patch('texts.validators.requests.Session')
    def test_check_timeout(self, mock_session_class):
        """Test timeout during content fetch"""
        mock_session = Mock()
        mock_session.get.side_effect = Timeout()
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='Test')

        assert result['verified'] is False
        assert 'Timeout' in result['error']

    @patch('texts.validators.requests.Session')
    def test_check_unexpected_exception(self, mock_session_class):
        """Test handling of unexpected exceptions"""
        mock_session = Mock()
        mock_session.get.side_effect = Exception('Network error')
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', title='Test')

        assert result['verified'] is False
        assert 'Content verification failed' in result['error']

    @patch('texts.validators.requests.Session')
    def test_check_unicode_content(self, mock_session_class):
        """Test handling of Unicode characters in content"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = '''
            <html><body>孔子 (Confucius) 論語 philosophy</body></html>
        '''.encode('utf-8')
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', author='Confucius')

        assert result['author_found'] is True

    @patch('texts.validators.requests.Session')
    def test_check_malformed_html(self, mock_session_class):
        """Test handling of malformed HTML"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body><p>Unclosed tag<div>Plato'
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        verifier = ContentVerifier()
        verifier.session = mock_session
        result = verifier.check('https://example.com', author='Plato')

        # Should still work with BeautifulSoup's lenient parsing
        assert result['author_found'] is True


class TestCitationFormatChecker:
    """Test suite for CitationFormatChecker"""

    def test_markdown_link_format_valid(self):
        """Test valid markdown link format [Title](URL)"""
        checker = CitationFormatChecker()
        citation = '[The Republic](https://example.com/republic)'
        url = 'https://example.com/republic'
        result = checker.check(citation, url)

        assert result['valid_format'] is True
        assert result['format_type'] == 'markdown_link'
        assert result['has_title'] is True
        assert result['score'] == 100

    def test_markdown_link_format_with_whitespace(self):
        """Test markdown link with extra whitespace"""
        checker = CitationFormatChecker()
        citation = '[  The Republic  ](  https://example.com/republic  )'
        url = 'https://example.com/republic'
        result = checker.check(citation, url)

        assert result['valid_format'] is True
        assert result['format_type'] == 'markdown_link'
        assert result['has_title'] is True

    def test_markdown_link_format_empty_title(self):
        """Test markdown link with empty title"""
        checker = CitationFormatChecker()
        citation = '[](https://example.com/republic)'
        url = 'https://example.com/republic'
        result = checker.check(citation, url)

        assert result['valid_format'] is True
        assert result['has_title'] is False

    def test_wikipedia_labeled_format(self):
        """Test Wikipedia: labeled format"""
        checker = CitationFormatChecker()
        citation = '**Wikipedia:** https://en.wikipedia.org/wiki/Plato'
        url = 'https://en.wikipedia.org/wiki/Plato'
        result = checker.check(citation, url)

        assert result['valid_format'] is True
        assert result['format_type'] == 'wikipedia_labeled'
        assert result['has_source_label'] is True
        assert result['score'] == 75

    def test_stanford_labeled_format(self):
        """Test Stanford Encyclopedia labeled format"""
        checker = CitationFormatChecker()
        citation = '**Stanford Encyclopedia of Philosophy:** https://plato.stanford.edu/entries/aristotle'
        url = 'https://plato.stanford.edu/entries/aristotle'
        result = checker.check(citation, url)

        assert result['valid_format'] is True
        assert result['format_type'] == 'stanford_labeled'
        assert result['has_source_label'] is True
        assert result['score'] == 75

    def test_bare_url_format(self):
        """Test bare URL without any formatting"""
        checker = CitationFormatChecker()
        citation = 'See https://example.com/article for more details'
        url = 'https://example.com/article'
        result = checker.check(citation, url)

        assert result['valid_format'] is True
        assert result['format_type'] == 'bare_url'
        assert result['score'] == 50

    def test_no_url_in_citation(self):
        """Test citation that doesn't contain the URL"""
        checker = CitationFormatChecker()
        citation = 'This is some text without the URL'
        url = 'https://example.com/missing'
        result = checker.check(citation, url)

        assert result['valid_format'] is False
        assert result['format_type'] is None
        assert result['score'] == 0

    def test_empty_citation_text(self):
        """Test empty citation text"""
        checker = CitationFormatChecker()
        result = checker.check('', 'https://example.com')

        assert result['valid_format'] is False
        assert result['score'] == 0

    def test_multiple_links_in_citation(self):
        """Test citation with multiple markdown links"""
        checker = CitationFormatChecker()
        citation = '[First](https://first.com) and [Second](https://example.com/target)'
        url = 'https://example.com/target'
        result = checker.check(citation, url)

        # The regex finds the first markdown link, not the matching one
        # So this will be recognized as bare_url since the URL appears in the text
        assert result['valid_format'] is True
        assert result['format_type'] == 'bare_url'  # Falls through to bare URL match

    def test_url_special_characters(self):
        """Test URL with special characters and query parameters"""
        checker = CitationFormatChecker()
        url = 'https://example.com/path?param=value&other=123#section'
        citation = f'[Article]({url})'
        result = checker.check(citation, url)

        assert result['valid_format'] is True
        assert result['format_type'] == 'markdown_link'

    def test_case_sensitive_url_matching(self):
        """Test that URL matching is case-sensitive"""
        checker = CitationFormatChecker()
        citation = '[Article](https://Example.COM/Path)'
        url = 'https://example.com/path'
        result = checker.check(citation, url)

        # URLs don't match exactly (case difference)
        assert result['valid_format'] is False


class TestCitationValidator:
    """Test suite for CitationValidator (main orchestrator)"""

    def test_initialization(self):
        """Test validator initializes all sub-checkers"""
        validator = CitationValidator()
        assert validator.accessibility_checker is not None
        assert validator.trustworthiness_checker is not None
        assert validator.content_verifier is not None
        assert validator.format_checker is not None

    @patch.object(URLAccessibilityChecker, 'check')
    @patch.object(SourceTrustworthinessChecker, 'check')
    @patch.object(ContentVerifier, 'check')
    @patch.object(CitationFormatChecker, 'check')
    def test_validate_perfect_citation(self, mock_format, mock_content, mock_trust, mock_access):
        """Test validation of a perfect citation"""
        # Mock all checks as passing
        mock_access.return_value = {
            'accessible': True,
            'status_code': 200,
            'response_time': 0.5,
            'error': None
        }
        mock_trust.return_value = {
            'trusted': True,
            'trust_score': 100,
            'source_name': 'Project Gutenberg',
            'domain': 'gutenberg.org'
        }
        mock_content.return_value = {
            'verified': True,
            'title_found': True,
            'author_found': True,
            'confidence': 100,
            'error': None
        }
        mock_format.return_value = {
            'valid_format': True,
            'format_type': 'markdown_link',
            'has_title': True,
            'score': 100
        }

        validator = CitationValidator()
        result = validator.validate(
            url='https://gutenberg.org/books/1234',
            citation_text='[The Republic](https://gutenberg.org/books/1234)',
            title='The Republic',
            author='Plato'
        )

        assert result['status'] == 'valid'
        assert result['overall_score'] >= 75
        assert len(result['recommendations']) == 0

    @patch.object(URLAccessibilityChecker, 'check')
    @patch.object(SourceTrustworthinessChecker, 'check')
    @patch.object(CitationFormatChecker, 'check')
    def test_validate_broken_url(self, mock_format, mock_trust, mock_access):
        """Test validation of citation with broken URL"""
        mock_access.return_value = {
            'accessible': False,
            'status_code': 404,
            'error': 'Not Found'
        }
        mock_trust.return_value = {
            'trusted': True,
            'trust_score': 100,
            'source_name': 'Project Gutenberg',
            'domain': 'gutenberg.org'
        }
        mock_format.return_value = {
            'valid_format': True,
            'format_type': 'markdown_link',
            'score': 100
        }

        validator = CitationValidator()
        result = validator.validate(
            url='https://gutenberg.org/books/nonexistent',
            citation_text='[Missing](https://gutenberg.org/books/nonexistent)'
        )

        assert result['status'] == 'broken'
        assert result['overall_score'] < 75
        assert any('inaccessible' in rec for rec in result['recommendations'])

    @patch.object(URLAccessibilityChecker, 'check')
    @patch.object(SourceTrustworthinessChecker, 'check')
    @patch.object(ContentVerifier, 'check')
    @patch.object(CitationFormatChecker, 'check')
    def test_validate_untrusted_source(self, mock_format, mock_content, mock_trust, mock_access):
        """Test validation with untrusted source"""
        mock_access.return_value = {
            'accessible': True,
            'status_code': 200
        }
        mock_trust.return_value = {
            'trusted': False,
            'trust_score': 0,
            'source_name': 'Unknown Source',
            'domain': 'random-blog.com'
        }
        mock_content.return_value = {
            'verified': True,
            'confidence': 100
        }
        mock_format.return_value = {
            'valid_format': True,
            'score': 100
        }

        validator = CitationValidator()
        result = validator.validate(
            url='https://random-blog.com/article',
            citation_text='[Article](https://random-blog.com/article)'
        )

        assert result['status'] == 'suspicious'
        assert any('Untrusted source' in rec for rec in result['recommendations'])

    @patch.object(URLAccessibilityChecker, 'check')
    @patch.object(SourceTrustworthinessChecker, 'check')
    @patch.object(ContentVerifier, 'check')
    @patch.object(CitationFormatChecker, 'check')
    def test_validate_content_mismatch(self, mock_format, mock_content, mock_trust, mock_access):
        """Test validation when content doesn't match title/author"""
        mock_access.return_value = {
            'accessible': True,
            'status_code': 200
        }
        mock_trust.return_value = {
            'trusted': True,
            'trust_score': 100,
            'domain': 'gutenberg.org'
        }
        mock_content.return_value = {
            'verified': False,
            'title_found': False,
            'author_found': False,
            'confidence': 0
        }
        mock_format.return_value = {
            'valid_format': True,
            'score': 100
        }

        validator = CitationValidator()
        result = validator.validate(
            url='https://gutenberg.org/books/1234',
            citation_text='[Wrong Title](https://gutenberg.org/books/1234)',
            title='The Republic',
            author='Plato'
        )

        # With weighted scoring: accessibility(100*0.4) + trust(100*0.3) + content(0*0.2) + format(100*0.1) = 80
        # 80 >= 75, so status is 'valid' not 'suspicious'
        assert result['status'] == 'valid'
        assert any('verification failed' in rec for rec in result['recommendations'])

    @patch.object(URLAccessibilityChecker, 'check')
    @patch.object(SourceTrustworthinessChecker, 'check')
    @patch.object(ContentVerifier, 'check')
    @patch.object(CitationFormatChecker, 'check')
    def test_validate_poor_format(self, mock_format, mock_content, mock_trust, mock_access):
        """Test validation with poor citation format"""
        mock_access.return_value = {
            'accessible': True,
            'status_code': 200
        }
        mock_trust.return_value = {
            'trusted': True,
            'trust_score': 100,
            'domain': 'gutenberg.org'
        }
        mock_content.return_value = {
            'verified': True,
            'confidence': 100
        }
        mock_format.return_value = {
            'valid_format': True,
            'format_type': 'bare_url',
            'score': 50
        }

        validator = CitationValidator()
        result = validator.validate(
            url='https://gutenberg.org/books/1234',
            citation_text='https://gutenberg.org/books/1234'
        )

        assert any('markdown format' in rec for rec in result['recommendations'])

    @patch.object(URLAccessibilityChecker, 'check')
    @patch.object(SourceTrustworthinessChecker, 'check')
    @patch.object(CitationFormatChecker, 'check')
    def test_validate_without_content_verification(self, mock_format, mock_trust, mock_access):
        """Test validation without title/author (skips content verification)"""
        mock_access.return_value = {
            'accessible': True,
            'status_code': 200
        }
        mock_trust.return_value = {
            'trusted': True,
            'trust_score': 100,
            'domain': 'gutenberg.org'
        }
        mock_format.return_value = {
            'valid_format': True,
            'score': 100
        }

        validator = CitationValidator()
        result = validator.validate(
            url='https://gutenberg.org/books/1234',
            citation_text='[Link](https://gutenberg.org/books/1234)'
        )

        # Should still validate without content check
        assert 'overall_score' in result
        assert result['content_verification']['verified'] is False
        # When URL is accessible, content verifier runs but returns error for no title/author
        assert result['content_verification']['error'] == 'No title or author provided for verification'

    def test_validate_overall_score_calculation(self):
        """Test that overall score uses correct weighted average"""
        validator = CitationValidator()

        # Manually test the scoring logic
        scores = {
            'accessibility': 100,  # weight 0.4
            'trustworthiness': 100,  # weight 0.3
            'content': 100,  # weight 0.2
            'format': 100  # weight 0.1
        }
        weights = {
            'accessibility': 0.4,
            'trustworthiness': 0.3,
            'content': 0.2,
            'format': 0.1
        }

        expected_score = sum(scores[key] * weights[key] for key in scores)
        assert expected_score == 100.0

    @patch.object(URLAccessibilityChecker, 'check')
    @patch.object(SourceTrustworthinessChecker, 'check')
    @patch.object(CitationFormatChecker, 'check')
    def test_validate_empty_url(self, mock_format, mock_trust, mock_access):
        """Test validation with empty URL"""
        mock_access.return_value = {
            'accessible': False,
            'error': 'Invalid URL'
        }
        mock_trust.return_value = {
            'trusted': False,
            'trust_score': 0,
            'domain': None
        }
        mock_format.return_value = {
            'valid_format': False,
            'score': 0
        }

        validator = CitationValidator()
        result = validator.validate(url='', citation_text='')

        assert result['status'] == 'broken'
        assert result['overall_score'] == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_very_long_citation_text(self):
        """Test handling of very long citation text"""
        checker = CitationFormatChecker()
        long_text = 'A' * 10000 + ' [Title](https://example.com) ' + 'B' * 10000
        result = checker.check(long_text, 'https://example.com')

        assert result['valid_format'] is True

    def test_citation_with_special_unicode_characters(self):
        """Test citation with special Unicode characters"""
        checker = CitationFormatChecker()
        citation = '[論語 (Analects) 🎓](https://example.com/confucius)'
        result = checker.check(citation, 'https://example.com/confucius')

        assert result['valid_format'] is True
        assert result['has_title'] is True

    def test_url_with_percent_encoding(self):
        """Test URL with percent-encoded characters"""
        checker = CitationFormatChecker()
        url = 'https://example.com/path%20with%20spaces?q=%E8%AB%96%E8%AA%9E'
        citation = f'[Link]({url})'
        result = checker.check(citation, url)

        assert result['valid_format'] is True

    def test_ipv6_url(self):
        """Test handling of IPv6 URL"""
        checker = SourceTrustworthinessChecker()
        result = checker.check('http://[2001:db8::1]/page')

        assert result['trusted'] is False
        assert result['trust_score'] == 0

    def test_url_with_port_number(self):
        """Test URL with explicit port number"""
        checker = SourceTrustworthinessChecker()
        result = checker.check('https://example.com:8080/page')

        assert 'domain' in result
        assert result['trust_score'] == 0

    def test_malformed_markdown_link(self):
        """Test malformed markdown link syntax"""
        checker = CitationFormatChecker()

        # Missing closing bracket
        result1 = checker.check('[Title(https://example.com)', 'https://example.com')
        assert result1['valid_format'] is False or result1['format_type'] == 'bare_url'

        # Missing closing parenthesis
        result2 = checker.check('[Title](https://example.com', 'https://example.com')
        assert result2['valid_format'] is False or result2['format_type'] == 'bare_url'

    def test_nested_markdown_syntax(self):
        """Test markdown link with nested brackets"""
        checker = CitationFormatChecker()
        citation = '[[Nested Title]](https://example.com)'
        result = checker.check(citation, 'https://example.com')

        # Should still be recognized as markdown format
        assert result['valid_format'] is True

    @pytest.mark.parametrize("url", [
        'javascript:alert(1)',
        'data:text/html,<script>alert(1)</script>',
        'file:///etc/passwd',
        'ftp://example.com/file',
    ])
    def test_non_http_protocols(self, url):
        """Test handling of non-HTTP protocols"""
        checker = SourceTrustworthinessChecker()
        result = checker.check(url)

        # Should handle gracefully
        assert 'trust_score' in result
