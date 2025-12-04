"""Repository documentation scanner for extracting lessons learned and knowledge"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


@dataclass
class DocumentKnowledge:
    """Represents knowledge extracted from a document"""
    file_path: str
    doc_type: str  # 'readme', 'lessons', 'architecture', 'guide', 'notes', 'postmortem'
    title: Optional[str]
    sections: Dict[str, str]  # section_name -> content
    code_examples: List[Dict[str, str]]  # list of {language, code}
    lessons_learned: List[str]
    decisions: List[Dict[str, str]]  # architectural decisions
    warnings: List[str]  # gotchas, warnings, important notes
    best_practices: List[str]
    metadata: Dict[str, Any]
    extracted_at: str


class DocumentationScanner:
    """Scans repository for documentation and extracts lessons learned"""

    # Document patterns to look for
    DOCUMENT_PATTERNS = [
        "README*.md", "readme*.md",
        "LESSONS*.md", "lessons*.md",
        "LEARNINGS*.md", "learnings*.md",
        "POSTMORTEM*.md", "postmortem*.md",
        "ARCHITECTURE*.md", "architecture*.md",
        "DESIGN*.md", "design*.md",
        "NOTES*.md", "notes*.md",
        "TODO*.md", "todo*.md",
        "DECISIONS*.md", "ADR*.md", "adr*.md",  # Architecture Decision Records
        "CONTRIBUTING*.md", "contributing*.md",
        "DEVELOPMENT*.md", "development*.md",
        "GUIDE*.md", "guide*.md",
        "TROUBLESHOOTING*.md", "troubleshooting*.md",
        "FAQ*.md", "faq*.md",
        "CHANGELOG*.md", "changelog*.md",
        "RETROSPECTIVE*.md", "retrospective*.md"
    ]

    # Additional patterns in docs/ or documentation/ folders
    DOC_FOLDERS = ["docs", "documentation", "doc", ".github", "wiki"]

    # Patterns that indicate lessons learned sections
    LESSONS_PATTERNS = [
        r"#+\s*(lessons?\s+learned|learnings?|takeaways?|retrospective|postmortem)",
        r"#+\s*(what\s+we\s+learned|what\s+went\s+wrong|what\s+went\s+right)",
        r"#+\s*(gotchas?|warnings?|important\s+notes?|caveats?)",
        r"#+\s*(best\s+practices?|recommendations?|tips?)",
        r"#+\s*(mistakes?\s+made|issues?\s+encountered|problems?\s+solved)",
        r"#+\s*(future\s+improvements?|next\s+steps?|action\s+items?)"
    ]

    # Patterns for architectural decisions
    DECISION_PATTERNS = [
        r"#+\s*(decision|adr|architecture\s+decision)",
        r"#+\s*(context|problem|solution|consequences)",
        r"#+\s*(rationale|reasoning|why)"
    ]

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.scanned_files: Set[Path] = set()

    def scan_repository(self, repo_path: str, project_name: Optional[str] = None) -> List[DocumentKnowledge]:
        """Scan entire repository for documentation"""
        repo = Path(repo_path).resolve()
        if not repo.exists():
            console.print(f"[red]Repository path does not exist: {repo}[/red]")
            return []

        if not project_name:
            project_name = repo.name

        console.print(f"[cyan]Scanning repository: {repo}[/cyan]")

        all_docs = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:

            # Find all documentation files
            task = progress.add_task("Finding documentation files...", total=None)
            doc_files = self._find_documentation_files(repo)
            progress.update(task, total=len(doc_files), completed=0)

            # Process each file
            for i, doc_file in enumerate(doc_files):
                progress.update(task, description=f"Processing {doc_file.name}", completed=i)

                knowledge = self._extract_knowledge(doc_file, repo)
                if knowledge:
                    all_docs.append(knowledge)
                    self._store_in_knowledge_base(knowledge, project_name)

            progress.update(task, completed=len(doc_files))

        console.print(f"[green]✓ Scanned {len(doc_files)} files, extracted {len(all_docs)} documents with knowledge[/green]")
        return all_docs

    def _find_documentation_files(self, repo_path: Path) -> List[Path]:
        """Find all documentation files in repository"""
        doc_files = []

        # Ignore common non-documentation directories
        ignore_dirs = {
            'node_modules', 'venv', '.venv', 'env', '.env',
            'dist', 'build', 'target', '.git', '__pycache__',
            'vendor', 'deps', '.pytest_cache', '.tox'
        }

        # Search for documentation patterns
        for pattern in self.DOCUMENT_PATTERNS:
            for doc in repo_path.rglob(pattern):
                if not any(ignored in doc.parts for ignored in ignore_dirs):
                    if doc not in self.scanned_files:
                        doc_files.append(doc)
                        self.scanned_files.add(doc)

        # Search in documentation folders
        for folder_name in self.DOC_FOLDERS:
            for folder in repo_path.rglob(folder_name):
                if folder.is_dir() and not any(ignored in folder.parts for ignored in ignore_dirs):
                    for md_file in folder.rglob("*.md"):
                        if md_file not in self.scanned_files:
                            doc_files.append(md_file)
                            self.scanned_files.add(md_file)

        # Also look for .txt files with relevant names
        for txt_pattern in ["*lessons*.txt", "*notes*.txt", "*learnings*.txt"]:
            for doc in repo_path.rglob(txt_pattern):
                if not any(ignored in doc.parts for ignored in ignore_dirs):
                    if doc not in self.scanned_files:
                        doc_files.append(doc)
                        self.scanned_files.add(doc)

        return sorted(doc_files)

    def _extract_knowledge(self, file_path: Path, repo_path: Path) -> Optional[DocumentKnowledge]:
        """Extract knowledge from a documentation file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            if not content.strip():
                return None

            # Determine document type
            doc_type = self._determine_doc_type(file_path, content)

            # Extract various components
            knowledge = DocumentKnowledge(
                file_path=str(file_path.relative_to(repo_path)),
                doc_type=doc_type,
                title=self._extract_title(content),
                sections=self._extract_sections(content),
                code_examples=self._extract_code_examples(content),
                lessons_learned=self._extract_lessons_learned(content),
                decisions=self._extract_decisions(content),
                warnings=self._extract_warnings(content),
                best_practices=self._extract_best_practices(content),
                metadata=self._extract_metadata(file_path, content),
                extracted_at=datetime.now().isoformat()
            )

            # Only return if we found meaningful content
            if (knowledge.lessons_learned or knowledge.decisions or
                knowledge.warnings or knowledge.best_practices or
                knowledge.code_examples):
                return knowledge

            return None

        except Exception as e:
            console.print(f"[yellow]Warning: Could not process {file_path}: {e}[/yellow]")
            return None

    def _determine_doc_type(self, file_path: Path, content: str) -> str:
        """Determine the type of documentation"""
        name_lower = file_path.name.lower()
        content_lower = content[:1000].lower()  # Check first 1000 chars

        if 'readme' in name_lower:
            return 'readme'
        elif any(x in name_lower for x in ['lesson', 'learning', 'learned']):
            return 'lessons'
        elif any(x in name_lower for x in ['postmortem', 'retrospective']):
            return 'postmortem'
        elif any(x in name_lower for x in ['architecture', 'adr', 'design']):
            return 'architecture'
        elif any(x in name_lower for x in ['guide', 'tutorial', 'howto']):
            return 'guide'
        elif 'troubleshoot' in name_lower:
            return 'troubleshooting'
        elif 'lessons learned' in content_lower or 'what we learned' in content_lower:
            return 'lessons'
        else:
            return 'notes'

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract document title"""
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith('# '):
                return line[2:].strip()
        return None

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract all sections with their content"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split('\n'):
            # Check if it's a header
            if re.match(r'^#{1,6}\s+', line):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = re.sub(r'^#{1,6}\s+', '', line).strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _extract_code_examples(self, content: str) -> List[Dict[str, str]]:
        """Extract code examples from markdown"""
        code_blocks = []
        pattern = r'```(\w+)?\n(.*?)\n```'

        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1) or 'unknown'
            code = match.group(2)
            if code.strip():
                code_blocks.append({
                    'language': language,
                    'code': code.strip()
                })

        return code_blocks

    def _extract_lessons_learned(self, content: str) -> List[str]:
        """Extract lessons learned from content"""
        lessons = []

        for pattern in self.LESSONS_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Extract content after the heading
                start = match.end()
                # Find next heading or end of content
                next_heading = re.search(r'\n#{1,6}\s+', content[start:])
                end = start + next_heading.start() if next_heading else len(content)

                section_content = content[start:end].strip()

                # Extract bullet points or paragraphs
                bullets = re.findall(r'[-*+]\s+(.+)', section_content)
                if bullets:
                    lessons.extend(bullets)
                else:
                    # Add as single lesson if meaningful
                    if len(section_content) > 20:
                        lessons.append(section_content)

        return list(set(lessons))  # Remove duplicates

    def _extract_decisions(self, content: str) -> List[Dict[str, str]]:
        """Extract architectural decisions"""
        decisions = []

        # Look for ADR-style sections
        adr_pattern = r'(?:##?\s*(?:Decision|ADR|Architecture Decision)[:\s]*([^\n]+))'
        matches = re.finditer(adr_pattern, content, re.IGNORECASE)

        for match in matches:
            decision_title = match.group(1).strip()
            start = match.end()

            # Extract context, decision, consequences
            next_section = re.search(r'\n#{1,6}\s+', content[start:])
            end = start + next_section.start() if next_section else len(content)

            decision_content = content[start:end]

            decision = {
                'title': decision_title,
                'content': decision_content.strip()
            }

            # Try to extract structured parts
            context_match = re.search(r'Context:?\s*(.+?)(?=\n(?:Decision|Consequences|$))',
                                     decision_content, re.DOTALL | re.IGNORECASE)
            if context_match:
                decision['context'] = context_match.group(1).strip()

            decisions.append(decision)

        return decisions

    def _extract_warnings(self, content: str) -> List[str]:
        """Extract warnings, gotchas, and important notes"""
        warnings = []

        # Look for warning patterns
        warning_patterns = [
            r'(?:⚠️|⚠|Warning|WARNING|Important|IMPORTANT|Gotcha|GOTCHA|Note|NOTE|Caveat|CAVEAT)[:\s]*([^\n]+)',
            r'>\s*\*\*(?:Warning|Important|Note)\*\*[:\s]*([^\n]+)',
            r'!\[(?:warning|important|note)\]\(.*?\)\s*([^\n]+)'
        ]

        for pattern in warning_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                warning = match.group(1).strip()
                if len(warning) > 10:  # Filter out too short warnings
                    warnings.append(warning)

        return list(set(warnings))

    def _extract_best_practices(self, content: str) -> List[str]:
        """Extract best practices and recommendations"""
        practices = []

        # Patterns for best practices
        practice_patterns = [
            r'(?:Best Practice|Recommendation|Tip|Pro Tip|Should|Must|Always|Never)[:\s]*([^\n]+)',
            r'✅\s*([^\n]+)',
            r'👍\s*([^\n]+)'
        ]

        for pattern in practice_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                practice = match.group(1).strip()
                if len(practice) > 10:
                    practices.append(practice)

        return list(set(practices))

    def _extract_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract metadata about the document"""
        metadata = {
            'file_size': len(content),
            'line_count': len(content.split('\n')),
            'word_count': len(content.split()),
            'has_code_examples': bool(re.search(r'```', content)),
            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }

        # Check for dates in content
        date_pattern = r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})'
        dates = re.findall(date_pattern, content)
        if dates:
            metadata['mentioned_dates'] = dates[:5]  # Keep first 5 dates

        return metadata

    def _store_in_knowledge_base(self, knowledge: DocumentKnowledge, project_name: str):
        """Store extracted documentation in knowledge base"""
        try:
            # Convert to JSON for storage
            doc_data = asdict(knowledge)
            doc_json = json.dumps(doc_data)

            # Store in a new table or as a special pattern type
            self.kb.store_documentation(
                project_name=project_name,
                file_path=knowledge.file_path,
                doc_type=knowledge.doc_type,
                content=doc_json,
                extracted_at=knowledge.extracted_at
            )

            console.print(f"[green]✓ Stored knowledge from {knowledge.file_path}[/green]")

        except Exception as e:
            console.print(f"[red]Failed to store {knowledge.file_path}: {e}[/red]")

    def search_documentation(self, query: str, project_name: Optional[str] = None) -> List[DocumentKnowledge]:
        """Search through stored documentation"""
        results = self.kb.search_documentation(query, project_name)

        docs = []
        for result in results:
            doc_data = json.loads(result['content'])
            docs.append(DocumentKnowledge(**doc_data))

        return docs

    def scrape_documentation(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape documentation from a web URL"""
        try:
            import requests
            from bs4 import BeautifulSoup

            # Fetch the page
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Break into lines and remove leading/trailing space
            lines = (line.strip() for line in text.splitlines())
            # Drop blank lines
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Join with newlines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return {
                'url': url,
                'title': soup.title.string if soup.title else url,
                'content': text
            }

        except ImportError:
            # If requests or beautifulsoup4 not installed, return simple message
            return {
                'url': url,
                'title': 'Web scraping unavailable',
                'content': 'Install requests and beautifulsoup4 to scrape web documentation'
            }
        except Exception as e:
            console.print(f"[red]Error scraping {url}: {e}[/red]")
            return None

    def extract_lessons(self, content: str) -> Dict[str, List]:
        """Extract lessons, warnings, and best practices from documentation content"""
        return {
            'lessons': self._extract_lessons_learned(content),
            'warnings': self._extract_warnings(content),
            'best_practices': self._extract_best_practices(content),
            'code_examples': self._extract_code_examples(content)
        }