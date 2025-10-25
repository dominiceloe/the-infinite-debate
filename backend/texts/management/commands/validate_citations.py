"""
Django management command to validate Primary Text citations.

Usage:
    python manage.py validate_citations [--output PATH] [--persona NAME]

This command:
1. Scans persona markdown files for Primary Text links
2. Queries database for stored PrimaryText URLs
3. Validates each link using 4 criteria
4. Generates a markdown report with findings
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models

from texts.models import PrimaryText
from personas.models import Persona
from texts.validators import CitationValidator


class Command(BaseCommand):
    help = 'Validate Primary Text citations from markdown files and database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output path for validation report (default: ideas/philosophical-debates/CITATION_VALIDATION_REPORT.md)'
        )
        parser.add_argument(
            '--persona',
            type=str,
            default=None,
            help='Validate citations for specific persona only (by slug or name)'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = CitationValidator()
        self.citations = []
        self.stats = {
            'total': 0,
            'valid': 0,
            'broken': 0,
            'suspicious': 0,
            'by_source': defaultdict(lambda: {'total': 0, 'valid': 0, 'broken': 0, 'suspicious': 0}),
            'by_persona': defaultdict(lambda: {'total': 0, 'valid': 0, 'broken': 0, 'suspicious': 0})
        }

    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(self.style.SUCCESS('Starting citation validation...\n'))

        # Determine output path
        if options['output']:
            output_path = Path(options['output'])
        else:
            # Default: ideas/philosophical-debates/CITATION_VALIDATION_REPORT.md
            base_path = Path(settings.BASE_DIR).parent
            output_path = base_path / 'CITATION_VALIDATION_REPORT.md'

        # Step 1: Collect citations from markdown files
        self.stdout.write('📚 Scanning persona markdown files...')
        markdown_citations = self.scan_markdown_files(options.get('persona'))
        self.stdout.write(
            self.style.SUCCESS(f'   Found {len(markdown_citations)} citations in markdown files\n')
        )

        # Step 2: Collect citations from database
        self.stdout.write('🗄️  Querying database for PrimaryText records...')
        db_citations = self.scan_database(options.get('persona'))
        self.stdout.write(
            self.style.SUCCESS(f'   Found {len(db_citations)} citations in database\n')
        )

        # Combine and deduplicate
        all_citations = self.merge_citations(markdown_citations, db_citations)
        self.stdout.write(
            self.style.SUCCESS(f'📊 Total unique citations to validate: {len(all_citations)}\n')
        )

        # Step 3: Validate each citation
        self.stdout.write('🔍 Validating citations...\n')
        validated_citations = []

        for i, citation in enumerate(all_citations, 1):
            self.stdout.write(f'   [{i}/{len(all_citations)}] {citation["url"][:60]}...')

            result = self.validator.validate(
                url=citation['url'],
                citation_text=citation.get('citation_text', ''),
                title=citation.get('title'),
                author=citation.get('author')
            )

            # Add metadata
            result['persona'] = citation.get('persona', 'Unknown')
            result['source_type'] = citation.get('source_type', 'markdown')
            result['title'] = citation.get('title')
            result['author'] = citation.get('author')

            validated_citations.append(result)

            # Update stats
            self.update_stats(result)

            # Show status
            status_symbol = {
                'valid': '✅',
                'broken': '❌',
                'suspicious': '⚠️'
            }.get(result['status'], '?')

            self.stdout.write(
                self.style.SUCCESS(f' {status_symbol} {result["status"].upper()} ({result["overall_score"]}/100)')
            )

        # Step 4: Generate report
        self.stdout.write(f'\n📝 Generating validation report...')
        self.generate_report(validated_citations, output_path)
        self.stdout.write(
            self.style.SUCCESS(f'   Report saved to: {output_path}\n')
        )

        # Step 5: Print summary
        self.print_summary()

        return f'Validation complete! Report: {output_path}'

    def scan_markdown_files(self, persona_filter: str = None) -> List[Dict]:
        """
        Scan persona markdown files for Primary Text links.

        Returns list of:
        {
            'persona': str,
            'url': str,
            'citation_text': str,
            'title': str (if extractable),
            'author': str (persona name),
            'source_type': 'markdown'
        }
        """
        citations = []

        # Find persona markdown files
        # BASE_DIR is backend/, so we need to go up to philosophical-debates/, then up to ideas/, then up to LLM_PLAYGROUND/
        base_path = Path(settings.BASE_DIR).parent.parent.parent / '.claude' / 'lib' / 'personas'

        if not base_path.exists():
            self.stdout.write(
                self.style.WARNING(f'Persona directory not found: {base_path}')
            )
            return citations

        # Scan all .md files recursively
        md_files = list(base_path.rglob('*.md'))

        for md_file in md_files:
            # Skip README files
            if md_file.name == 'README.md':
                continue

            # Extract persona name from filename
            persona_name = md_file.stem.replace('-', ' ').replace('_', ' ').title()

            # Skip if filtering by persona
            if persona_filter and persona_filter.lower() not in persona_name.lower():
                continue

            # Read file content
            try:
                content = md_file.read_text(encoding='utf-8')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not read {md_file}: {e}')
                )
                continue

            # Extract links from "External Links" or similar sections
            # Look for ### External Links or similar headers
            external_links_match = re.search(
                r'###\s*(External Links|Primary Works|Sources|Bibliography)\s*\n(.*?)(?=\n###|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )

            if external_links_match:
                links_section = external_links_match.group(2)

                # Extract markdown links: [text](url)
                markdown_links = re.findall(
                    r'\[([^\]]+)\]\((https?://[^\)]+)\)',
                    links_section
                )

                for link_text, url in markdown_links:
                    citations.append({
                        'persona': persona_name,
                        'url': url.strip(),
                        'citation_text': f'[{link_text}]({url})',
                        'title': link_text.strip(),
                        'author': persona_name,
                        'source_type': 'markdown'
                    })

                # Also extract bare URLs with labels (e.g., **Wikipedia:** https://...)
                labeled_links = re.findall(
                    r'\*\*([^:]+):\*\*\s+(https?://[^\s\n]+)',
                    links_section
                )

                for label, url in labeled_links:
                    citations.append({
                        'persona': persona_name,
                        'url': url.strip(),
                        'citation_text': f'**{label}:** {url}',
                        'title': label.strip(),
                        'author': persona_name,
                        'source_type': 'markdown'
                    })

        return citations

    def scan_database(self, persona_filter: str = None) -> List[Dict]:
        """
        Scan database for PrimaryText URLs and Persona external_links.

        Returns same structure as scan_markdown_files.
        """
        citations = []

        # Query PrimaryText model
        texts = PrimaryText.objects.filter(source_url__isnull=False)
        if persona_filter:
            texts = texts.filter(author__icontains=persona_filter)

        for text in texts:
            if text.source_url:
                citations.append({
                    'persona': text.author,
                    'url': text.source_url,
                    'citation_text': f'{text.title} ({text.source_type})',
                    'title': text.title,
                    'author': text.author,
                    'source_type': f'database_primarytext'
                })

        # Query Persona model external_links field
        personas = Persona.objects.exclude(external_links={})
        if persona_filter:
            personas = personas.filter(
                models.Q(name__icontains=persona_filter) |
                models.Q(slug__icontains=persona_filter)
            )

        for persona in personas:
            external_links = persona.external_links

            # Check for primary_works list
            if 'primary_works' in external_links and isinstance(external_links['primary_works'], list):
                for work_url in external_links['primary_works']:
                    if isinstance(work_url, str) and work_url.startswith('http'):
                        citations.append({
                            'persona': persona.name,
                            'url': work_url,
                            'citation_text': f'Primary work: {work_url}',
                            'title': None,
                            'author': persona.name,
                            'source_type': 'database_persona_external_links'
                        })

            # Check for other external link fields (wikipedia, stanford, etc.)
            for key, value in external_links.items():
                if key != 'primary_works' and isinstance(value, str) and value.startswith('http'):
                    citations.append({
                        'persona': persona.name,
                        'url': value,
                        'citation_text': f'{key.replace("_", " ").title()}: {value}',
                        'title': key.replace('_', ' ').title(),
                        'author': persona.name,
                        'source_type': f'database_persona_{key}'
                    })

        return citations

    def merge_citations(self, markdown_citations: List[Dict], db_citations: List[Dict]) -> List[Dict]:
        """Merge and deduplicate citations from markdown and database."""
        # Use URL as key for deduplication
        citations_dict = {}

        for citation in markdown_citations + db_citations:
            url = citation['url']

            # If URL already exists, prefer more complete metadata
            if url in citations_dict:
                existing = citations_dict[url]
                # Prefer citation with title
                if citation.get('title') and not existing.get('title'):
                    citations_dict[url] = citation
                # Prefer database source if title is same
                elif citation.get('source_type', '').startswith('database'):
                    citations_dict[url] = citation
            else:
                citations_dict[url] = citation

        return list(citations_dict.values())

    def update_stats(self, result: Dict):
        """Update validation statistics."""
        self.stats['total'] += 1
        self.stats[result['status']] += 1

        # By source
        source = result['trustworthiness']['source_name']
        self.stats['by_source'][source]['total'] += 1
        self.stats['by_source'][source][result['status']] += 1

        # By persona
        persona = result.get('persona', 'Unknown')
        self.stats['by_persona'][persona]['total'] += 1
        self.stats['by_persona'][persona][result['status']] += 1

    def generate_report(self, validated_citations: List[Dict], output_path: Path):
        """Generate markdown validation report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_lines = [
            '# Primary Text Citation Validation Report',
            f'**Generated:** {timestamp}',
            f'**Total Citations:** {self.stats["total"]}',
            f'**Valid:** {self.stats["valid"]} ({self.stats["valid"]/max(self.stats["total"], 1)*100:.1f}%)',
            f'**Broken:** {self.stats["broken"]} ({self.stats["broken"]/max(self.stats["total"], 1)*100:.1f}%)',
            f'**Suspicious:** {self.stats["suspicious"]} ({self.stats["suspicious"]/max(self.stats["total"], 1)*100:.1f}%)',
            '',
            '---',
            '',
            '## Summary by Source',
            ''
        ]

        # Sort sources by total citations
        sorted_sources = sorted(
            self.stats['by_source'].items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )

        for source, counts in sorted_sources:
            valid_pct = counts['valid'] / max(counts['total'], 1) * 100
            status = '✅' if valid_pct > 90 else '⚠️' if valid_pct > 70 else '❌'
            report_lines.append(
                f"- **{source}**: {counts['total']} citations "
                f"({counts['valid']} valid, {counts['broken']} broken) {status}"
            )

        # Broken links section
        report_lines.extend(['', '---', '', '## Broken Links (Immediate Action Required)', ''])

        broken = [c for c in validated_citations if c['status'] == 'broken']
        if broken:
            for citation in broken:
                report_lines.extend([
                    f"### {citation['persona']} - {citation.get('title') or 'Untitled'}",
                    f"- **URL:** {citation['url']}",
                    f"- **Status:** {citation['accessibility'].get('error', 'Inaccessible')}",
                    ''
                ])
        else:
            report_lines.append('*No broken links found! 🎉*\n')

        # Suspicious links section
        report_lines.extend(['---', '', '## Suspicious Links (Review Recommended)', ''])

        suspicious = [c for c in validated_citations if c['status'] == 'suspicious']
        if suspicious:
            for citation in suspicious:
                report_lines.extend([
                    f"### {citation['persona']} - {citation.get('title') or 'Untitled'}",
                    f"- **URL:** {citation['url']}",
                    f"- **Score:** {citation['overall_score']}/100",
                    f"- **Source:** {citation['trustworthiness']['source_name']} (Trust: {citation['trustworthiness']['trust_score']}/100)",
                    f"- **Issues:**"
                ])
                for rec in citation['recommendations']:
                    report_lines.append(f"  {rec}")
                report_lines.append('')
        else:
            report_lines.append('*No suspicious links found! 🎉*\n')

        # Validation by persona
        report_lines.extend(['---', '', '## Validation by Persona', ''])

        sorted_personas = sorted(
            self.stats['by_persona'].items(),
            key=lambda x: x[0]
        )

        for persona, counts in sorted_personas:
            report_lines.append(f"### {persona} ({counts['total']} citations)")

            # Find all citations for this persona
            persona_citations = [c for c in validated_citations if c.get('persona') == persona]

            for citation in sorted(persona_citations, key=lambda x: -x['overall_score']):
                status_symbol = {
                    'valid': '✅',
                    'broken': '❌',
                    'suspicious': '⚠️'
                }[citation['status']]

                title = citation.get('title') or 'Untitled'
                source = citation['trustworthiness']['source_name']

                report_lines.append(
                    f"{status_symbol} **{title}** ({source}) - {citation['overall_score']}/100"
                )

            report_lines.append('')

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('\n'.join(report_lines), encoding='utf-8')

    def print_summary(self):
        """Print summary statistics to console."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n📊 VALIDATION SUMMARY\n'))
        self.stdout.write('='*60 + '\n')

        self.stdout.write(f"Total Citations: {self.stats['total']}")
        self.stdout.write(
            self.style.SUCCESS(f"✅ Valid: {self.stats['valid']} ({self.stats['valid']/max(self.stats['total'], 1)*100:.1f}%)")
        )
        self.stdout.write(
            self.style.ERROR(f"❌ Broken: {self.stats['broken']} ({self.stats['broken']/max(self.stats['total'], 1)*100:.1f}%)")
        )
        self.stdout.write(
            self.style.WARNING(f"⚠️  Suspicious: {self.stats['suspicious']} ({self.stats['suspicious']/max(self.stats['total'], 1)*100:.1f}%)")
        )
        self.stdout.write('')
