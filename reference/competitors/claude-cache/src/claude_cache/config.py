"""Configuration for specialized pattern detection"""

from typing import Dict, List, Any

class DetectionConfig:
    """Configurable detection patterns for different tech stacks"""

    def __init__(self):
        self.stack_patterns = {
            'frontend': {
                'keywords': ['react', 'vue', 'angular', 'component', 'jsx', 'tsx', 'css', 'tailwind', 'mui', 'antd'],
                'file_patterns': ['*.jsx', '*.tsx', '*.vue', '*.css', '*.scss'],
                'success_indicators': [
                    'component renders', 'styled correctly', 'responsive', 'accessibility',
                    'lighthouse score', 'no console errors', 'tests pass'
                ],
                'common_issues': ['hydration', 'state management', 're-render', 'styling']
            },

            'backend': {
                'keywords': ['api', 'endpoint', 'route', 'controller', 'middleware', 'auth', 'jwt'],
                'file_patterns': ['*.py', '*.js', '*.go', '*.rs', 'routes/*', 'controllers/*'],
                'success_indicators': [
                    'endpoint works', 'returns 200', 'authenticated', 'validated',
                    'tests pass', 'no 500 errors', 'performant'
                ],
                'common_issues': ['cors', 'authentication', 'validation', 'rate limiting']
            },

            'database': {
                'keywords': ['query', 'migration', 'schema', 'index', 'sql', 'orm', 'prisma', 'sequelize'],
                'file_patterns': ['*.sql', 'migrations/*', 'schema.*', 'models/*'],
                'success_indicators': [
                    'migration successful', 'query optimized', 'index added',
                    'no n+1', 'transaction completed', 'backup restored'
                ],
                'common_issues': ['n+1 queries', 'deadlock', 'slow query', 'migration']
            },

            'devops': {
                'keywords': ['docker', 'kubernetes', 'ci/cd', 'deploy', 'pipeline', 'terraform'],
                'file_patterns': ['Dockerfile', '*.yaml', '*.yml', '.github/*', 'terraform/*'],
                'success_indicators': [
                    'build successful', 'deployed', 'pipeline green', 'tests pass',
                    'container running', 'health check passing'
                ],
                'common_issues': ['build failure', 'deployment', 'secrets', 'permissions']
            },

            'testing': {
                'keywords': ['test', 'spec', 'jest', 'pytest', 'mocha', 'cypress', 'playwright'],
                'file_patterns': ['*.test.*', '*.spec.*', 'tests/*', '__tests__/*'],
                'success_indicators': [
                    'all tests pass', 'coverage increased', 'e2e successful',
                    'no flaky tests', 'mocked correctly'
                ],
                'common_issues': ['flaky test', 'mock', 'async', 'timeout']
            },

            'mobile': {
                'keywords': ['react native', 'expo', 'flutter', 'swift', 'kotlin', 'ios', 'android'],
                'file_patterns': ['*.swift', '*.kt', '*.dart', 'ios/*', 'android/*'],
                'success_indicators': [
                    'builds on device', 'no crashes', 'responsive', 'performs well',
                    'passes app store review'
                ],
                'common_issues': ['native module', 'permissions', 'platform specific', 'performance']
            }
        }

        self.framework_specific = {
            'nextjs': {
                'success_patterns': ['getServerSideProps', 'getStaticProps', 'app router', 'middleware'],
                'common_wins': ['ISR working', 'SSG optimized', 'middleware auth']
            },
            'django': {
                'success_patterns': ['migration', 'admin panel', 'DRF serializer', 'signals'],
                'common_wins': ['admin customized', 'permissions working', 'signals connected']
            },
            'rails': {
                'success_patterns': ['activerecord', 'controller', 'migration', 'sidekiq'],
                'common_wins': ['background job', 'mailer working', 'cache hit']
            },
            'express': {
                'success_patterns': ['middleware', 'router', 'error handler', 'validation'],
                'common_wins': ['rate limiting', 'cors fixed', 'auth middleware']
            }
        }

        self.quality_indicators = {
            'performance': ['optimized', 'faster', 'reduced', 'cached', 'lazy load', 'debounced'],
            'security': ['sanitized', 'validated', 'authenticated', 'authorized', 'encrypted'],
            'maintainability': ['refactored', 'documented', 'typed', 'tested', 'linted'],
            'user_experience': ['accessible', 'responsive', 'intuitive', 'feedback', 'loading state']
        }

    def get_stack_for_file(self, file_path: str) -> List[str]:
        """Identify which tech stacks a file belongs to"""
        stacks = []
        for stack_name, config in self.stack_patterns.items():
            for pattern in config['file_patterns']:
                if self._matches_pattern(file_path, pattern):
                    stacks.append(stack_name)
                    break
        return stacks

    def get_success_weight(self, content: str, stack: str) -> float:
        """Calculate success weight based on stack-specific indicators"""
        if stack not in self.stack_patterns:
            return 1.0

        indicators = self.stack_patterns[stack]['success_indicators']
        content_lower = content.lower()

        matches = sum(1 for indicator in indicators if indicator in content_lower)
        weight = 1.0 + (matches * 0.2)  # Each match adds 20% weight

        return min(weight, 2.0)  # Cap at 2x weight

    def detect_framework(self, files: List[str], content: str) -> str:
        """Detect specific framework being used"""
        content_lower = content.lower()

        for framework, config in self.framework_specific.items():
            for pattern in config['success_patterns']:
                if pattern in content_lower:
                    return framework

        return 'unknown'

    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches a pattern"""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)

    def get_custom_success_rules(self) -> Dict[str, Any]:
        """Get custom success detection rules"""
        return {
            'min_success_score': 0.7,
            'stack_weights': {
                'frontend': {'user_satisfied': 0.3, 'no_console_errors': 0.2},
                'backend': {'tests_passed': 0.4, 'endpoint_working': 0.3},
                'database': {'query_optimized': 0.3, 'no_errors': 0.3},
                'testing': {'all_tests_pass': 0.5, 'coverage': 0.2}
            },
            'bonus_patterns': {
                'performance_improvement': 0.3,
                'bug_fixed': 0.25,
                'feature_complete': 0.35,
                'refactored': 0.15
            }
        }