"""Auto-configuration for new projects"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.prompt import Confirm

console = Console()


class AutoConfigurator:
    """Automatically configure Claude Cache for new projects"""

    def __init__(self):
        self.project_indicators = {
            'javascript': ['package.json', 'node_modules', '.js', '.jsx'],
            'typescript': ['tsconfig.json', '.ts', '.tsx'],
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', '.py'],
            'ruby': ['Gemfile', '.rb'],
            'go': ['go.mod', 'go.sum', '.go'],
            'rust': ['Cargo.toml', '.rs'],
            'java': ['pom.xml', 'build.gradle', '.java'],
            'php': ['composer.json', '.php'],
            'react': ['package.json', '.jsx', 'src/App.js'],
            'vue': ['vue.config.js', '.vue'],
            'django': ['manage.py', 'settings.py'],
            'rails': ['Gemfile', 'config.ru'],
            'nextjs': ['next.config.js', 'pages/', 'app/'],
            'express': ['app.js', 'server.js', 'routes/']
        }

    def auto_detect_project(self, project_path: Path = None) -> Dict:
        """Auto-detect project configuration"""
        if project_path is None:
            project_path = Path.cwd()

        detected_stacks = self._detect_tech_stacks(project_path)
        framework = self._detect_framework(project_path)
        testing = self._detect_testing_framework(project_path)

        config = {
            'project_name': project_path.name,
            'detected_stacks': detected_stacks,
            'framework': framework,
            'testing': testing,
            'auto_detected': True,
            'timestamp': datetime.now().isoformat()
        }

        return config

    def _detect_tech_stacks(self, project_path: Path) -> List[str]:
        """Detect which tech stacks are used in the project"""
        detected = []

        for stack, indicators in self.project_indicators.items():
            for indicator in indicators:
                if indicator.startswith('.'):
                    # File extension
                    if list(project_path.glob(f'**/*{indicator}')):
                        detected.append(stack)
                        break
                else:
                    # File or directory
                    if (project_path / indicator).exists():
                        detected.append(stack)
                        break

        return list(set(detected))  # Remove duplicates

    def _detect_framework(self, project_path: Path) -> Optional[str]:
        """Detect the main framework being used"""
        # Check for specific framework files
        framework_files = {
            'next.config.js': 'nextjs',
            'nuxt.config.js': 'nuxt',
            'angular.json': 'angular',
            'vue.config.js': 'vue',
            'manage.py': 'django',
            'config.ru': 'rails',
            'laravel': 'artisan'
        }

        for file, framework in framework_files.items():
            if (project_path / file).exists():
                return framework

        # Check package.json for framework
        package_json = project_path / 'package.json'
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}

                if 'next' in deps:
                    return 'nextjs'
                elif 'vue' in deps:
                    return 'vue'
                elif '@angular/core' in deps:
                    return 'angular'
                elif 'react' in deps:
                    return 'react'

        return None

    def _detect_testing_framework(self, project_path: Path) -> Optional[str]:
        """Detect testing framework"""
        # Check for test configuration files
        test_configs = {
            'jest.config.js': 'jest',
            'cypress.config.js': 'cypress',
            '.rspec': 'rspec',
            'pytest.ini': 'pytest',
            'phpunit.xml': 'phpunit'
        }

        for file, framework in test_configs.items():
            if (project_path / file).exists():
                return framework

        # Check package.json
        package_json = project_path / 'package.json'
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}

                for test_lib in ['jest', 'mocha', 'vitest', 'cypress', 'playwright']:
                    if test_lib in deps:
                        return test_lib

        return None

    def generate_optimized_config(self, detected_config: Dict) -> Dict:
        """Generate optimized configuration based on detection"""
        stacks = detected_config.get('detected_stacks', [])
        framework = detected_config.get('framework')

        # Start with base config
        config = {
            'global': {
                'min_success_score': 0.7,
                'monitoring_interval': 1,
                'database_path': '~/.claude/knowledge/cache.db'
            },
            'project': {
                'name': detected_config['project_name'],
                'primary_stack': stacks[0] if stacks else 'general',
                'framework': framework
            }
        }

        # Add stack-specific optimizations
        if 'typescript' in stacks or 'javascript' in stacks:
            config['stack_weights'] = {
                'frontend': {
                    'component_renders': 0.3,
                    'no_console_errors': 0.3,
                    'tests_pass': 0.2,
                    'user_satisfied': 0.2
                }
            }

        if 'python' in stacks:
            config['stack_weights'] = {
                'backend': {
                    'tests_pass': 0.35,
                    'api_working': 0.3,
                    'no_errors': 0.2,
                    'performance': 0.15
                }
            }

        # Add framework-specific patterns
        if framework == 'nextjs':
            config['custom_patterns'] = {
                'nextjs_success': {
                    'keywords': [
                        'page renders',
                        'SSR working',
                        'API route works',
                        'ISR configured'
                    ],
                    'weight': 1.3
                }
            }

        return config

    def save_config(self, config: Dict, path: Path = None):
        """Save configuration to file"""
        if path is None:
            path = Path('config.yaml')

        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]✓ Configuration saved to {path}[/green]")

    def setup_new_project(self, project_path: Path = None, interactive: bool = True):
        """Set up Claude Cache for a new project"""
        if project_path is None:
            project_path = Path.cwd()

        console.print(f"\n[cyan]🔍 Analyzing project: {project_path.name}[/cyan]")

        # Detect configuration
        detected = self.auto_detect_project(project_path)

        console.print("\n[green]✓ Detection complete![/green]")
        console.print(f"  Tech stacks: {', '.join(detected['detected_stacks'])}")
        console.print(f"  Framework: {detected['framework'] or 'None detected'}")
        console.print(f"  Testing: {detected['testing'] or 'None detected'}")

        # Generate optimized config
        config = self.generate_optimized_config(detected)

        if interactive:
            if Confirm.ask("\n[yellow]Save this configuration?[/yellow]"):
                self.save_config(config)
                console.print("\n[bold green]🎉 Project configured successfully![/bold green]")
                console.print("[cyan]Run 'cache start' to begin caching patterns[/cyan]")
        else:
            self.save_config(config)

        return config

    def check_for_new_project(self, project_path: Path) -> bool:
        """Check if this is a new unconfigured project"""
        config_file = project_path / 'config.yaml'
        claude_dir = project_path / '.claude'

        # Project is new if no config and no .claude directory
        return not config_file.exists() and not claude_dir.exists()


from datetime import datetime


def auto_configure_if_needed():
    """Run auto-configuration if needed for current project"""
    configurator = AutoConfigurator()
    current_dir = Path.cwd()

    if configurator.check_for_new_project(current_dir):
        console.print("\n[yellow]📦 New project detected![/yellow]")
        configurator.setup_new_project(current_dir)