# In coder_mcp/analysis/metrics/coverage_reader.py
import json
import logging
from pathlib import Path
from typing import Optional

try:
    from defusedxml.ElementTree import parse as ET_parse
except ImportError:
    # Fallback to standard library with warning - only for development/testing
    import xml.etree.ElementTree as ET  # nosec B405

    ET_parse = ET.parse
    logging.warning(
        "defusedxml not available, using standard xml.etree.ElementTree (security risk)"
    )

logger = logging.getLogger(__name__)


class CoverageReader:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def read_coverage(self) -> Optional[float]:
        """Read coverage from multiple possible sources"""
        # Try coverage.json first (most detailed)
        coverage = self._read_json_coverage()
        if coverage is not None:
            return coverage

        # Try coverage.xml
        coverage = self._read_xml_coverage()
        if coverage is not None:
            return coverage

        # Try .coverage file (requires coverage.py library)
        coverage = self._read_coverage_file()
        if coverage is not None:
            return coverage

        # If no coverage files exist, try to run tests
        return self._run_coverage_analysis()

    def _read_json_coverage(self) -> Optional[float]:
        """Read from coverage.json"""
        coverage_file = self.workspace_root / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    data = json.load(f)
                    # Handle different JSON formats
                    if "totals" in data:
                        if "percent_covered" in data["totals"]:
                            return float(data["totals"]["percent_covered"])
                        elif "percent_covered_display" in data["totals"]:
                            return float(data["totals"]["percent_covered_display"].rstrip("%"))
                    elif "summary" in data:
                        percent_covered = data["summary"].get("percent_covered", 0)
                        return float(percent_covered) if percent_covered is not None else None
            except Exception as e:
                logger.warning(f"Failed to read coverage.json: {e}")
        return None

    def _read_xml_coverage(self) -> Optional[float]:
        """Read from coverage.xml using secure XML parser"""
        coverage_file = self.workspace_root / "coverage.xml"
        if coverage_file.exists():
            try:
                tree = ET_parse(coverage_file)
                root = tree.getroot()
                # Look for coverage percentage in XML
                if "line-rate" in root.attrib:
                    return float(root.attrib["line-rate"]) * 100
            except Exception as e:
                logger.warning(f"Failed to read coverage.xml: {e}")
        return None

    def _read_coverage_file(self) -> Optional[float]:
        """Read from .coverage file using coverage.py library"""
        coverage_file = self.workspace_root / ".coverage"
        if coverage_file.exists():
            try:
                import coverage

                cov = coverage.Coverage(data_file=str(coverage_file))
                cov.load()
                # Get the total coverage percentage
                total = cov.report(show_missing=False, skip_covered=False, file=None)
                return float(total) if total is not None else None
            except ImportError:
                logger.warning("coverage.py library not available to read .coverage file")
            except Exception as e:
                logger.warning(f"Failed to read .coverage file: {e}")
        return None

    def _run_coverage_analysis(self) -> Optional[float]:
        """Run pytest with coverage if possible"""
        try:
            import shutil
            import subprocess

            # Check if pytest is available in PATH
            pytest_path = shutil.which("pytest")
            if not pytest_path:
                logger.warning("pytest not found in PATH, skipping coverage analysis")
                return None

            # Use full path to pytest for security
            result = subprocess.run(  # nosec B603
                [pytest_path, "--cov=coder_mcp", "--cov-report=json", "--no-cov-on-fail"],
                cwd=self.workspace_root,
                capture_output=True,
                timeout=30,
                check=False,  # Don't raise on non-zero exit
            )
            if result.returncode == 0:
                return self._read_json_coverage()
        except Exception as e:
            logger.warning(f"Failed to run coverage analysis: {e}")
        return None
