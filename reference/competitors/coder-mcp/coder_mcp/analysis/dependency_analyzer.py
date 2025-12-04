#!/usr/bin/env python3
"""
Dependency Analysis Module
Provides comprehensive dependency tracking, version analysis, and security scanning
"""

import json
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

try:
    import toml
except ImportError:
    toml = None  # type: ignore

logger = logging.getLogger(__name__)


class DependencyAnalysisError(Exception):
    """Custom exception for dependency analysis errors"""

    pass


class DependencyAnalyzer:
    """Specialized analyzer for project dependencies with security and update checking"""

    def __init__(self, workspace_root: Path):
        """Initialize dependency analyzer

        Args:
            workspace_root: Root directory of the workspace to analyze
        """
        self.workspace_root = Path(workspace_root)
        self._last_api_call: Dict[str, float] = {}  # Rate limiting tracking
        self._api_cache: Dict[str, Any] = {}  # Simple API response cache

    async def analyze(
        self, check_updates: bool = True, security_scan: bool = False
    ) -> Dict[str, Any]:
        """Analyze project dependencies comprehensively

        Args:
            check_updates: Whether to check for outdated packages
            security_scan: Whether to scan for security vulnerabilities

        Returns:
            Dictionary containing dependency analysis results
        """
        try:
            # Initialize result structure
            result = self._initialize_result()

            # Detect project type
            project_type = self._detect_project_type()
            result["project_type"] = project_type

            if project_type == "unknown":
                logger.warning("No recognized dependency files found")
                return self._add_recommendations_and_return(result)

            # Parse dependency files
            dependencies = self._parse_dependencies(project_type)
            result["dependencies"] = dependencies
            result["total_dependencies"] = len(dependencies)

            # Check for updates if requested and dependencies exist
            if check_updates and dependencies:
                await self._check_for_updates(result, project_type)

            # Security scan if requested
            if security_scan and dependencies:
                await self._scan_for_vulnerabilities(result, project_type)

            return self._add_recommendations_and_return(result)

        except Exception as e:
            logger.error("Dependency analysis failed: %s", e)
            return self._safe_fallback_response(str(e))

    def _initialize_result(self) -> Dict[str, Any]:
        """Initialize the result structure with safe defaults"""
        return {
            "project_type": "unknown",
            "dependencies": {},
            "total_dependencies": 0,
            "outdated": [],
            "outdated_count": 0,
            "vulnerabilities": [],
            "vulnerability_count": 0,
            "recommendations": [],
            "analysis_timestamp": time.time(),
            "errors": [],
        }

    def _detect_project_type(self) -> str:
        """Detect project type from dependency files with validation"""
        try:
            indicators = {
                "python": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
                "javascript": ["package.json", "yarn.lock", "package-lock.json"],
                "typescript": ["package.json", "tsconfig.json"],
                "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
                "go": ["go.mod", "go.sum"],
                "rust": ["Cargo.toml", "Cargo.lock"],
                "php": ["composer.json", "composer.lock"],
                "ruby": ["Gemfile", "Gemfile.lock"],
                "csharp": ["*.csproj", "packages.config", "*.sln"],
            }

            for lang, files in indicators.items():
                for file_pattern in files:
                    if file_pattern.startswith("*"):
                        # Handle glob patterns
                        if list(self.workspace_root.glob(file_pattern)):
                            return lang
                    else:
                        if (self.workspace_root / file_pattern).exists():
                            return lang

            return "unknown"
        except Exception as e:
            logger.warning("Error detecting project type: %s", e)
            return "unknown"

    def _parse_dependencies(self, project_type: str) -> Dict[str, str]:
        """Parse dependencies based on project type with robust error handling"""
        try:
            if project_type == "python":
                return self._parse_python_dependencies()
            elif project_type in ["javascript", "typescript"]:
                return self._parse_javascript_dependencies()
            elif project_type == "go":
                return self._parse_go_dependencies()
            elif project_type == "rust":
                return self._parse_rust_dependencies()
            elif project_type == "java":
                return self._parse_java_dependencies()
            elif project_type == "php":
                return self._parse_php_dependencies()
            elif project_type == "ruby":
                return self._parse_ruby_dependencies()
            else:
                logger.warning("Unsupported project type: %s", project_type)
                return {}
        except Exception as e:
            logger.error("Failed to parse %s dependencies: %s", project_type, e)
            return {}

    def _parse_python_dependencies(self) -> Dict[str, str]:
        """Parse Python dependencies with multiple file format support"""
        dependencies: Dict[str, str] = {}

        # Priority order: pyproject.toml, requirements.txt, setup.py, Pipfile
        parsers = [
            ("pyproject.toml", self._parse_pyproject_toml),
            ("requirements.txt", self._parse_requirements_txt),
            ("setup.py", self._parse_setup_py),
            ("Pipfile", self._parse_pipfile),
        ]

        for filename, parser in parsers:
            file_path = self.workspace_root / filename
            if file_path.exists():
                try:
                    parsed_deps = parser(file_path)
                    if parsed_deps:
                        dependencies.update(parsed_deps)
                        logger.info("Parsed %d dependencies from %s", len(parsed_deps), filename)
                except Exception as e:
                    logger.warning("Failed to parse %s: %s", filename, e)

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> Dict[str, str]:
        """Parse pyproject.toml with comprehensive format support"""
        if toml is None:
            logger.warning("toml library not available, cannot parse pyproject.toml")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = toml.load(f)

            dependencies: Dict[str, str] = {}

            # Handle Poetry format
            if "tool" in data and "poetry" in data["tool"]:
                self._parse_poetry_dependencies(data["tool"]["poetry"], dependencies)

            # Handle PEP 621 format
            elif "project" in data:
                self._parse_pep621_dependencies(data["project"], dependencies)

            return dependencies

        except Exception as e:
            logger.error("Failed to parse pyproject.toml: %s", e)
            return {}

    def _parse_poetry_dependencies(
        self, poetry_data: Dict[str, Any], dependencies: Dict[str, str]
    ) -> None:
        """Parse Poetry format dependencies"""
        # Main dependencies
        if "dependencies" in poetry_data:
            for dep, version in poetry_data["dependencies"].items():
                if dep != "python":  # Skip Python version constraint
                    dependencies[dep] = self._normalize_version_spec(version)

        # Dev dependencies
        if "dev-dependencies" in poetry_data:
            for dep, version in poetry_data["dev-dependencies"].items():
                dependencies[f"{dep} (dev)"] = self._normalize_version_spec(version)

        # Group dependencies (Poetry 1.2+)
        if "group" in poetry_data:
            for group_name, group_data in poetry_data["group"].items():
                if "dependencies" in group_data:
                    for dep, version in group_data["dependencies"].items():
                        dependencies[f"{dep} ({group_name})"] = self._normalize_version_spec(
                            version
                        )

    def _parse_pep621_dependencies(
        self, project_data: Dict[str, Any], dependencies: Dict[str, str]
    ) -> None:
        """Parse PEP 621 format dependencies"""
        # Main dependencies
        if "dependencies" in project_data:
            for dep_spec in project_data["dependencies"]:
                name, version = self._parse_requirement_spec(dep_spec)
                if name:
                    dependencies[name] = version

        # Optional dependencies
        if "optional-dependencies" in project_data:
            for group_name, group_deps in project_data["optional-dependencies"].items():
                for dep_spec in group_deps:
                    name, version = self._parse_requirement_spec(dep_spec)
                    if name:
                        dependencies[f"{name} ({group_name})"] = version

    def _parse_requirements_txt(self, file_path: Path) -> Dict[str, str]:
        """Parse requirements.txt with comprehensive format support"""
        dependencies: Dict[str, str] = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    self._process_requirements_line(line, line_no, dependencies)

            return dependencies

        except Exception as e:
            logger.error("Failed to parse requirements.txt: %s", e)
            return {}

    def _process_requirements_line(
        self, line: str, line_no: int, dependencies: Dict[str, str]
    ) -> None:
        """Process a single line from requirements.txt"""
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return

        # Handle -r includes (recursive requirements)
        if line.startswith("-r "):
            include_file = self.workspace_root / line[3:].strip()
            if include_file.exists():
                try:
                    included_deps = self._parse_requirements_txt(include_file)
                    dependencies.update(included_deps)
                except Exception as e:
                    logger.warning("Failed to parse included requirements %s: %s", include_file, e)
            return

        # Handle -e editable installs
        if line.startswith("-e "):
            line = line[3:].strip()

        # Parse requirement specification
        name, version = self._parse_requirement_spec(line)
        if name:
            dependencies[name] = version
        else:
            logger.warning("Could not parse requirement at line %d: %s", line_no, line)

    def _parse_setup_py(self, file_path: Path) -> Dict[str, str]:
        """Parse setup.py (basic extraction)"""
        dependencies: Dict[str, str] = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract install_requires
            install_requires_match = re.search(
                r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
            )
            if install_requires_match:
                reqs_str = install_requires_match.group(1)
                # Extract quoted strings
                for match in re.finditer(r'["\']([^"\']+)["\']', reqs_str):
                    req_spec = match.group(1)
                    name, version = self._parse_requirement_spec(req_spec)
                    if name:
                        dependencies[name] = version

            return dependencies

        except Exception as e:
            logger.error("Failed to parse setup.py: %s", e)
            return {}

    def _parse_pipfile(self, file_path: Path) -> Dict[str, str]:
        """Parse Pipfile"""
        if toml is None:
            logger.warning("toml library not available, cannot parse Pipfile")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = toml.load(f)

            dependencies: Dict[str, str] = {}

            # Parse packages
            if "packages" in data:
                for dep, version in data["packages"].items():
                    dependencies[dep] = self._normalize_version_spec(version)

            # Parse dev-packages
            if "dev-packages" in data:
                for dep, version in data["dev-packages"].items():
                    dependencies[f"{dep} (dev)"] = self._normalize_version_spec(version)

            return dependencies

        except Exception as e:
            logger.error("Failed to parse Pipfile: %s", e)
            return {}

    def _parse_javascript_dependencies(self) -> Dict[str, str]:
        """Parse JavaScript/TypeScript dependencies"""
        dependencies: Dict[str, str] = {}

        package_json = self.workspace_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Parse different dependency types
                dep_types = [
                    "dependencies",
                    "devDependencies",
                    "peerDependencies",
                    "optionalDependencies",
                ]
                for dep_type in dep_types:
                    if dep_type in data:
                        suffix = f" ({dep_type[:-12]})" if dep_type != "dependencies" else ""
                        for dep, version in data[dep_type].items():
                            dependencies[f"{dep}{suffix}"] = str(version)

            except Exception as e:
                logger.error("Failed to parse package.json: %s", e)

        return dependencies

    def _parse_go_dependencies(self) -> Dict[str, str]:
        """Parse Go dependencies from go.mod"""
        dependencies: Dict[str, str] = {}

        go_mod = self.workspace_root / "go.mod"
        if go_mod.exists():
            try:
                with open(go_mod, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse require blocks
                require_pattern = r"require\s*\((.*?)\)"
                require_blocks = re.findall(require_pattern, content, re.DOTALL)

                for block in require_blocks:
                    for line in block.strip().split("\n"):
                        line = line.strip()
                        if line and not line.startswith("//"):
                            parts = line.split()
                            if len(parts) >= 2:
                                pkg_name = parts[0]
                                version = parts[1]
                                dependencies[pkg_name] = version

                # Parse single require statements
                single_require_pattern = r"require\s+([^\s]+)\s+([^\s]+)"
                for match in re.finditer(single_require_pattern, content):
                    pkg_name = match.group(1)
                    version = match.group(2)
                    dependencies[pkg_name] = version

            except Exception as e:
                logger.error("Failed to parse go.mod: %s", e)

        return dependencies

    def _parse_rust_dependencies(self) -> Dict[str, str]:
        """Parse Rust dependencies from Cargo.toml"""
        if toml is None:
            logger.warning("toml library not available, cannot parse Cargo.toml")
            return {}

        dependencies: Dict[str, str] = {}

        cargo_toml = self.workspace_root / "Cargo.toml"
        if cargo_toml.exists():
            try:
                with open(cargo_toml, "r", encoding="utf-8") as f:
                    data = toml.load(f)

                # Parse different dependency sections
                dep_sections = ["dependencies", "dev-dependencies", "build-dependencies"]
                for section in dep_sections:
                    if section in data:
                        suffix = f" ({section.split('-')[0]})" if section != "dependencies" else ""
                        for dep, version in data[section].items():
                            dependencies[f"{dep}{suffix}"] = self._normalize_version_spec(version)

            except Exception as e:
                logger.error("Failed to parse Cargo.toml: %s", e)

        return dependencies

    def _parse_java_dependencies(self) -> Dict[str, str]:
        """Parse Java dependencies (basic Maven support)"""
        dependencies: Dict[str, str] = {}

        pom_xml = self.workspace_root / "pom.xml"
        if pom_xml.exists():
            try:
                with open(pom_xml, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract dependencies using regex (basic approach)
                dep_pattern = (
                    r"<dependency>.*?<groupId>(.*?)</groupId>.*?"
                    r"<artifactId>(.*?)</artifactId>.*?"
                    r"<version>(.*?)</version>.*?</dependency>"
                )
                for match in re.finditer(dep_pattern, content, re.DOTALL):
                    group_id = match.group(1).strip()
                    artifact_id = match.group(2).strip()
                    version = match.group(3).strip()
                    dependencies[f"{group_id}:{artifact_id}"] = version

            except Exception as e:
                logger.error("Failed to parse pom.xml: %s", e)

        return dependencies

    def _parse_php_dependencies(self) -> Dict[str, str]:
        """Parse PHP dependencies from composer.json"""
        dependencies: Dict[str, str] = {}

        composer_json = self.workspace_root / "composer.json"
        if composer_json.exists():
            try:
                with open(composer_json, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Parse different dependency types
                dep_types = ["require", "require-dev"]
                for dep_type in dep_types:
                    if dep_type in data:
                        suffix = " (dev)" if dep_type == "require-dev" else ""
                        for dep, version in data[dep_type].items():
                            if not dep.startswith("php"):  # Skip PHP version constraints
                                dependencies[f"{dep}{suffix}"] = str(version)

            except Exception as e:
                logger.error("Failed to parse composer.json: %s", e)

        return dependencies

    def _parse_ruby_dependencies(self) -> Dict[str, str]:
        """Parse Ruby dependencies from Gemfile"""
        dependencies: Dict[str, str] = {}

        gemfile = self.workspace_root / "Gemfile"
        if gemfile.exists():
            try:
                with open(gemfile, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse gem statements
                gem_pattern = (
                    r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?"
                    r"(?:\s*,\s*:?(\w+)\s*=>\s*['\"]?([^'\"]+)['\"]?)?"
                )
                for match in re.finditer(gem_pattern, content):
                    gem_name = match.group(1)
                    version = match.group(2) or "*"
                    group = match.group(3)

                    if group and group in ["group", "groups"]:
                        suffix = f" ({match.group(4)})"
                    else:
                        suffix = ""

                    dependencies[f"{gem_name}{suffix}"] = version

            except Exception as e:
                logger.error("Failed to parse Gemfile: %s", e)

        return dependencies

    def _parse_requirement_spec(self, req_spec: str) -> Tuple[str, str]:
        """Parse a requirement specification into name and version"""
        try:
            # Handle different URL types
            if req_spec.startswith("git+"):
                return self._parse_git_url(req_spec)
            elif req_spec.startswith(("http://", "https://")):
                return self._parse_http_url(req_spec)
            elif req_spec.startswith(("./", "../", "/")):
                return self._parse_local_path(req_spec)
            else:
                return self._parse_standard_requirement(req_spec)

        except Exception as e:
            logger.warning("Failed to parse requirement spec '%s': %s", req_spec, e)
            return "", ""

    def _parse_git_url(self, req_spec: str) -> Tuple[str, str]:
        """Parse git URL requirement"""
        # Extract package name from git URL
        if "@" in req_spec:
            url_part = req_spec.split("@")[0]
        else:
            url_part = req_spec

        # Try to extract package name from URL
        if "/" in url_part:
            name = url_part.split("/")[-1].replace(".git", "")
        else:
            name = "unknown-git-package"

        return name, req_spec

    def _parse_http_url(self, req_spec: str) -> Tuple[str, str]:
        """Parse HTTP URL requirement"""
        # Extract package name from URL
        if "/" in req_spec:
            name = req_spec.split("/")[-1].split("#")[0]
        else:
            name = "unknown-url-package"
        return name, req_spec

    def _parse_local_path(self, req_spec: str) -> Tuple[str, str]:
        """Parse local path requirement"""
        name = req_spec.split("/")[-1]
        return name, req_spec

    def _parse_standard_requirement(self, req_spec: str) -> Tuple[str, str]:
        """Parse standard requirement specification"""
        # Match patterns like: package>=1.0.0, package==1.0.0, package~=1.0.0
        match = re.match(r"^([a-zA-Z0-9_.-]+)([>=<~!].*)?$", req_spec.strip())
        if match:
            name = match.group(1).strip()
            version = match.group(2).strip() if match.group(2) else "*"
            return name, version

        # If no version specified, assume any version
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "", req_spec.strip())
        if clean_name:
            return clean_name, "*"

        return "", ""

    def _normalize_version_spec(self, version: Union[str, Dict[str, Any]]) -> str:
        """Normalize version specification from various formats"""
        if isinstance(version, dict):
            # Handle complex dependency specs (git, path, etc.)
            if "git" in version:
                git_url = version.get("git", "")
                if "tag" in version:
                    return f"git+{git_url}@{version['tag']}"
                elif "branch" in version:
                    return f"git+{git_url}@{version['branch']}"
                elif "rev" in version:
                    return f"git+{git_url}@{version['rev']}"
                else:
                    return f"git+{git_url}"
            elif "path" in version:
                return f"file://{version['path']}"
            elif "version" in version:
                return str(version["version"])
            else:
                return str(version)
        else:
            return str(version) if version is not None else "*"

    async def _check_for_updates(self, result: Dict[str, Any], project_type: str) -> None:
        """Check for outdated packages with proper error handling"""
        try:
            if project_type == "python":
                await self._check_python_updates(result)
            elif project_type in ["javascript", "typescript"]:
                await self._check_npm_updates(result)
            elif project_type == "go":
                await self._check_go_updates(result)
            # Add more language support as needed

        except Exception as e:
            logger.warning("Failed to check for updates: %s", e)
            result["errors"].append(f"Update check failed: {str(e)}")

    async def _check_python_updates(self, result: Dict[str, Any]) -> None:
        """Check for outdated Python packages"""
        try:
            # Use pip list --outdated for installed packages
            cmd = ["pip", "list", "--outdated", "--format=json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if proc.returncode == 0 and proc.stdout:
                outdated_packages = json.loads(proc.stdout)

                for pkg in outdated_packages:
                    pkg_name = pkg.get("name", "unknown")
                    if pkg_name in result["dependencies"]:
                        outdated_info = {
                            "name": pkg_name,
                            "current_version": pkg.get("version", "unknown"),
                            "latest_version": pkg.get("latest_version", "unknown"),
                            "type": pkg.get("latest_filetype", "unknown"),
                        }
                        result["outdated"].append(outdated_info)

                result["outdated_count"] = len(result["outdated"])

            elif proc.returncode != 0:
                logger.warning("pip list --outdated failed: %s", proc.stderr)
                result["errors"].append("Could not check for outdated packages")

        except subprocess.TimeoutExpired:
            logger.warning("pip list --outdated timed out")
            result["errors"].append("Package update check timed out")
        except Exception as e:
            logger.warning("Failed to check Python updates: %s", e)
            result["errors"].append(f"Python update check failed: {str(e)}")

    async def _check_npm_updates(self, result: Dict[str, Any]) -> None:
        """Check for outdated npm packages"""
        try:
            cmd = ["npm", "outdated", "--json"]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.workspace_root, timeout=30
            )

            # npm outdated returns exit code 1 when there are outdated packages
            if proc.stdout:
                try:
                    outdated_data = json.loads(proc.stdout)

                    for pkg_name, info in outdated_data.items():
                        outdated_info = {
                            "name": pkg_name,
                            "current_version": info.get("current", "unknown"),
                            "latest_version": info.get("latest", "unknown"),
                            "wanted_version": info.get("wanted", "unknown"),
                            "type": info.get("type", "unknown"),
                        }
                        result["outdated"].append(outdated_info)

                    result["outdated_count"] = len(result["outdated"])

                except json.JSONDecodeError:
                    logger.warning("Failed to parse npm outdated output")
                    result["errors"].append("Could not parse npm outdated output")

        except subprocess.TimeoutExpired:
            logger.warning("npm outdated timed out")
            result["errors"].append("npm update check timed out")
        except Exception as e:
            logger.warning("Failed to check npm updates: %s", e)
            result["errors"].append(f"npm update check failed: {str(e)}")

    async def _check_go_updates(self, result: Dict[str, Any]) -> None:
        """Check for outdated Go modules"""
        try:
            cmd = ["go", "list", "-u", "-m", "all"]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.workspace_root, timeout=30
            )

            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    if "[" in line:  # Has update available
                        parts = line.split()
                        if len(parts) >= 3:
                            pkg_name = parts[0]
                            current = parts[1]
                            latest = parts[2].strip("[]")

                            outdated_info = {
                                "name": pkg_name,
                                "current_version": current,
                                "latest_version": latest,
                                "type": "module",
                            }
                            result["outdated"].append(outdated_info)

                result["outdated_count"] = len(result["outdated"])

        except subprocess.TimeoutExpired:
            logger.warning("go list -u -m all timed out")
            result["errors"].append("Go update check timed out")
        except Exception as e:
            logger.warning("Failed to check Go updates: %s", e)
            result["errors"].append(f"Go update check failed: {str(e)}")

    async def _scan_for_vulnerabilities(self, result: Dict[str, Any], project_type: str) -> None:
        """Scan for security vulnerabilities"""
        try:
            if project_type == "python":
                await self._scan_python_vulnerabilities(result)
            elif project_type in ["javascript", "typescript"]:
                await self._scan_npm_vulnerabilities(result)
            # Add more language support as needed

        except Exception as e:
            logger.warning("Failed to scan for vulnerabilities: %s", e)
            result["errors"].append(f"Vulnerability scan failed: {str(e)}")

    async def _scan_python_vulnerabilities(self, result: Dict[str, Any]) -> None:
        """Scan for Python security vulnerabilities"""
        try:
            # Try safety first
            cmd = ["safety", "check", "--json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if proc.returncode == 0 and proc.stdout:
                try:
                    vulns = json.loads(proc.stdout)
                    for vuln in vulns:
                        vuln_info = {
                            "package": vuln.get("package", "unknown"),
                            "vulnerability": vuln.get("vulnerability", "unknown"),
                            "severity": vuln.get("severity", "unknown"),
                            "id": vuln.get("id", "unknown"),
                            "affected_versions": vuln.get("affected_versions", "unknown"),
                        }
                        result["vulnerabilities"].append(vuln_info)

                except json.JSONDecodeError:
                    logger.warning("Failed to parse safety output")
                    result["errors"].append("Could not parse safety scan output")

            elif proc.returncode != 0:
                if "not found" in proc.stderr:
                    logger.info("safety not installed, skipping vulnerability scan")
                else:
                    logger.warning("safety check failed: %s", proc.stderr)
                    result["errors"].append("Safety vulnerability scan failed")

            result["vulnerability_count"] = len(result["vulnerabilities"])

        except subprocess.TimeoutExpired:
            logger.warning("safety check timed out")
            result["errors"].append("Vulnerability scan timed out")
        except Exception as e:
            logger.warning("Failed to scan Python vulnerabilities: %s", e)
            result["errors"].append(f"Python vulnerability scan failed: {str(e)}")

    async def _scan_npm_vulnerabilities(self, result: Dict[str, Any]) -> None:
        """Scan for npm security vulnerabilities"""
        try:
            cmd = ["npm", "audit", "--json"]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.workspace_root, timeout=30
            )

            if proc.stdout:
                try:
                    audit_data = json.loads(proc.stdout)
                    self._parse_npm_audit_data(audit_data, result)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse npm audit output")
                    result["errors"].append("Could not parse npm audit output")

            result["vulnerability_count"] = len(result["vulnerabilities"])

        except subprocess.TimeoutExpired:
            logger.warning("npm audit timed out")
            result["errors"].append("npm audit timed out")
        except Exception as e:
            logger.warning("Failed to scan npm vulnerabilities: %s", e)
            result["errors"].append(f"npm vulnerability scan failed: {str(e)}")

    def _parse_npm_audit_data(self, audit_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Parse npm audit data and extract vulnerability information"""
        # Handle different npm audit output formats
        if "advisories" in audit_data:
            # npm 6 format
            for advisory in audit_data["advisories"].values():
                vuln_info = {
                    "package": advisory.get("module_name", "unknown"),
                    "vulnerability": advisory.get("title", "unknown"),
                    "severity": advisory.get("severity", "unknown"),
                    "id": advisory.get("id", "unknown"),
                    "url": advisory.get("url", ""),
                }
                result["vulnerabilities"].append(vuln_info)

        elif "vulnerabilities" in audit_data:
            # npm 7+ format
            for vuln_name, vuln_data in audit_data["vulnerabilities"].items():
                vuln_info = {
                    "package": vuln_name,
                    "vulnerability": vuln_data.get("title", "unknown"),
                    "severity": vuln_data.get("severity", "unknown"),
                    "id": vuln_data.get("id", "unknown"),
                    "url": vuln_data.get("url", ""),
                }
                result["vulnerabilities"].append(vuln_info)

    def _add_recommendations_and_return(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations and return final result"""
        self._generate_recommendations(result)
        return result

    def _generate_recommendations(self, result: Dict[str, Any]) -> None:
        """Generate actionable recommendations based on analysis"""
        recommendations: List[str] = []

        self._add_dependency_recommendations(result, recommendations)
        self._add_update_recommendations(result, recommendations)
        self._add_security_recommendations(result, recommendations)
        self._add_best_practices_recommendations(result, recommendations)
        self._add_error_recommendations(result, recommendations)

        result["recommendations"] = recommendations

    def _add_dependency_recommendations(
        self, result: Dict[str, Any], recommendations: List[str]
    ) -> None:
        """Add dependency-related recommendations"""
        if result["total_dependencies"] == 0:
            recommendations.append(
                "No dependencies found. Consider adding a dependency management file."
            )
        elif result["total_dependencies"] > 100:
            recommendations.append(
                "Large number of dependencies detected. Consider reviewing for unused packages."
            )

    def _add_update_recommendations(
        self, result: Dict[str, Any], recommendations: List[str]
    ) -> None:
        """Add update-related recommendations"""
        if result["outdated_count"] > 0:
            if result["outdated_count"] == 1:
                recommendations.append(
                    "1 outdated dependency found. Consider updating to get "
                    "bug fixes and security patches."
                )
            else:
                recommendations.append(
                    f"{result['outdated_count']} outdated dependencies found. "
                    "Consider updating to get bug fixes and security patches."
                )

            # Specific high-priority updates
            critical_packages = ["openssl", "urllib3", "requests", "express", "lodash", "axios"]
            outdated_critical = [
                pkg
                for pkg in result["outdated"]
                if any(critical in pkg["name"].lower() for critical in critical_packages)
            ]

            if outdated_critical:
                critical_names = ", ".join([pkg["name"] for pkg in outdated_critical])
                recommendations.append(f"⚠️ Critical packages need updates: {critical_names}")

    def _add_security_recommendations(
        self, result: Dict[str, Any], recommendations: List[str]
    ) -> None:
        """Add security-related recommendations"""
        if result["vulnerability_count"] > 0:
            high_vuln = sum(
                1
                for v in result["vulnerabilities"]
                if v.get("severity", "").lower() in ["high", "critical"]
            )

            if high_vuln > 0:
                recommendations.append(
                    f"🚨 {high_vuln} high/critical security vulnerabilities found. "
                    "Update immediately!"
                )

            medium_vuln = sum(
                1 for v in result["vulnerabilities"] if v.get("severity", "").lower() == "medium"
            )

            if medium_vuln > 0:
                recommendations.append(
                    f"⚠️ {medium_vuln} medium severity vulnerabilities found. Plan updates soon."
                )

            low_vuln = result["vulnerability_count"] - high_vuln - medium_vuln
            if low_vuln > 0:
                recommendations.append(
                    f"ℹ️ {low_vuln} low severity vulnerabilities found. Update when convenient."
                )

    def _add_best_practices_recommendations(
        self, result: Dict[str, Any], recommendations: List[str]
    ) -> None:
        """Add best practices recommendations"""
        if result["project_type"] == "python":
            if (
                not (self.workspace_root / "requirements.txt").exists()
                and not (self.workspace_root / "pyproject.toml").exists()
            ):
                recommendations.append(
                    "Consider adding requirements.txt or pyproject.toml for "
                    "better dependency management."
                )

        elif result["project_type"] in ["javascript", "typescript"]:
            if (
                not (self.workspace_root / "package-lock.json").exists()
                and not (self.workspace_root / "yarn.lock").exists()
            ):
                recommendations.append(
                    "Consider using npm ci or yarn install --frozen-lockfile "
                    "for reproducible builds."
                )

    def _add_error_recommendations(
        self, result: Dict[str, Any], recommendations: List[str]
    ) -> None:
        """Add error-related recommendations"""
        if result["errors"]:
            recommendations.append(
                f"⚠️ {len(result['errors'])} errors occurred during analysis. "
                "Check logs for details."
            )

    def _safe_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """Return a safe fallback response when analysis fails"""
        return {
            "project_type": "unknown",
            "dependencies": {},
            "total_dependencies": 0,
            "outdated": [],
            "outdated_count": 0,
            "vulnerabilities": [],
            "vulnerability_count": 0,
            "recommendations": [
                "⚠️ Dependency analysis failed. Please check your dependency files and try again.",
                "Ensure you have the necessary tools installed (pip, npm, etc.) for your project.",
                f"Error details: {error_message}",
            ],
            "analysis_timestamp": time.time(),
            "errors": [error_message],
            "status": "failed",
        }
