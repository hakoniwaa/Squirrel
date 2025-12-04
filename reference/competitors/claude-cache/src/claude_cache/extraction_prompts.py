"""Structured extraction prompts for different pattern types"""

from typing import Dict, List, Any
from datetime import datetime


class ExtractionPrompts:
    """Centralized prompt engineering for pattern extraction"""

    def __init__(self):
        # Base prompt templates for different pattern types
        self.prompt_templates = {
            'success_pattern': {
                'system_prompt': """You are a coding pattern extraction expert. Your job is to analyze successful development sessions and extract reusable patterns that led to success.

Focus on:
- What specific approach was taken
- Key decision points that led to success
- Technical techniques used
- Workflow patterns that worked well
- Why this approach was effective

Be precise and actionable in your analysis.""",

                'extraction_prompt': """Analyze this successful coding session and extract the key success pattern:

SESSION CONTEXT:
- Project: {project_name}
- Domains: {tech_domains}
- Tools Used: {tools_used}
- Session Complexity: {session_complexity}

SESSION DATA:
{session_summary}

Extract the following:

1. PROBLEM SOLVED:
   - What was the user trying to achieve?
   - What was the core challenge?

2. SUCCESSFUL APPROACH:
   - What specific approach was taken?
   - What tools/techniques were used?
   - What was the sequence of actions?

3. KEY SUCCESS FACTORS:
   - What made this approach work?
   - What were the critical decisions?
   - What expertise was applied?

4. TRANSFERABILITY:
   - Can this approach work in other contexts?
   - What are the prerequisites?
   - What would need to be adapted?

5. LESSONS LEARNED:
   - What insights emerged?
   - What would you do differently?
   - What best practices were demonstrated?

Provide a structured, actionable pattern that can be reused."""
            },

            'anti_pattern': {
                'system_prompt': """You are an expert at identifying anti-patterns and failure modes in software development. Your job is to analyze failed attempts and extract what went wrong so it can be avoided in the future.

Focus on:
- What approach was attempted but failed
- Why it failed (root causes)
- Warning signs that preceded the failure
- Better alternatives that should be used instead

Be specific about failure modes and prevention strategies.""",

                'extraction_prompt': """Analyze this failed/problematic coding session and extract the anti-pattern:

SESSION CONTEXT:
- Project: {project_name}
- Domains: {tech_domains}
- Error Context: {error_context}

FAILURE DATA:
{session_summary}

Extract the following:

1. ATTEMPTED APPROACH:
   - What was tried?
   - What was the reasoning behind this approach?

2. FAILURE MODE:
   - How did it fail?
   - What were the symptoms?
   - What errors occurred?

3. ROOT CAUSES:
   - Why did this approach fail?
   - What assumptions were wrong?
   - What was missing or misunderstood?

4. WARNING SIGNS:
   - What early indicators suggested this wouldn't work?
   - What red flags were present?

5. PREVENTION STRATEGY:
   - How can this failure be avoided?
   - What should be done instead?
   - What checks/validations would prevent this?

Provide a clear anti-pattern definition with prevention guidance."""
            },

            'journey_pattern': {
                'system_prompt': """You are a development journey analyst. Your job is to extract the complete problem-solving journey, including failed attempts, pivots, and eventual success.

Focus on:
- The complete sequence from problem to solution
- Learning and adaptation throughout the process
- What worked, what didn't, and why
- The evolution of understanding

Capture the full narrative of problem-solving.""",

                'extraction_prompt': """Analyze this complete development journey from problem to solution:

JOURNEY CONTEXT:
- Project: {project_name}
- Journey Type: {journey_type}
- Total Attempts: {attempt_count}
- Final Outcome: {final_outcome}

JOURNEY DATA:
{session_summary}

Extract the following:

1. INITIAL PROBLEM:
   - What was the starting challenge?
   - What was understood initially?
   - What was the original plan?

2. JOURNEY PHASES:
   - What were the major phases/attempts?
   - How did understanding evolve?
   - What pivots or changes occurred?

3. LEARNING PROGRESSION:
   - What was learned at each step?
   - How did failures inform the next approach?
   - What insights emerged?

4. SUCCESS FACTORS:
   - What finally worked and why?
   - What was the breakthrough moment?
   - What knowledge/skills were key?

5. JOURNEY WISDOM:
   - What does this journey teach about problem-solving?
   - What patterns of thinking were effective?
   - How can this journey guide similar problems?

Provide a narrative that captures the full learning arc."""
            },

            'cross_project_pattern': {
                'system_prompt': """You are a cross-project pattern analyst. Your job is to identify patterns that can transfer across different projects and technology stacks.

Focus on:
- Universal principles and approaches
- Technology-agnostic solutions
- Patterns that scale across contexts
- Adaptation strategies for different environments

Extract transferable wisdom.""",

                'extraction_prompt': """Analyze this session for cross-project transferable patterns:

TRANSFERABILITY CONTEXT:
- Source Project: {project_name}
- Technology Stack: {tech_stack}
- Pattern Category: {pattern_category}
- Transferability Score: {transferability_score}

SESSION DATA:
{session_summary}

Extract the following:

1. UNIVERSAL PRINCIPLE:
   - What core principle/approach was used?
   - Why is this approach universally applicable?

2. TECHNOLOGY ABSTRACTION:
   - What parts are technology-specific?
   - What parts are technology-agnostic?
   - How can this be generalized?

3. ADAPTATION REQUIREMENTS:
   - What needs to change for different stacks?
   - What prerequisites must be met?
   - What are the variation points?

4. TRANSFER STRATEGY:
   - How should this pattern be adapted?
   - What examples work in different contexts?
   - What pitfalls should be avoided in transfer?

5. UNIVERSAL VALUE:
   - Why is this pattern worth reusing?
   - What benefits does it provide consistently?
   - What makes it resilient across contexts?

Provide a transferable pattern with adaptation guidance."""
            },

            'efficiency_pattern': {
                'system_prompt': """You are an efficiency pattern analyst. Your job is to identify patterns that lead to faster, more effective development workflows.

Focus on:
- Time-saving techniques
- Workflow optimizations
- Tool usage patterns
- Process improvements

Extract actionable efficiency gains.""",

                'extraction_prompt': """Analyze this session for efficiency patterns and optimizations:

EFFICIENCY CONTEXT:
- Session Duration: {session_duration}
- Task Complexity: {task_complexity}
- Tools Efficiency: {tools_efficiency}
- Success Speed: {success_speed}

SESSION DATA:
{session_summary}

Extract the following:

1. EFFICIENCY GAINS:
   - What made this session efficient?
   - What time was saved and how?

2. WORKFLOW PATTERNS:
   - What workflow was used?
   - What sequence of actions was optimal?
   - What parallel processing occurred?

3. TOOL MASTERY:
   - What tools were used effectively?
   - What tool combinations worked well?
   - What automation was leveraged?

4. PROCESS OPTIMIZATIONS:
   - What process improvements were evident?
   - What redundancy was avoided?
   - What shortcuts were effective?

5. SCALABLE EFFICIENCY:
   - How can this efficiency be replicated?
   - What principles can be generalized?
   - What setup enables this efficiency?

Provide actionable efficiency patterns."""
            }
        }

        # Context-specific prompt modifiers
        self.context_modifiers = {
            'frontend': {
                'focus_areas': ['component design', 'styling approaches', 'state management', 'user interaction'],
                'technical_context': 'React/Frontend development context'
            },
            'backend': {
                'focus_areas': ['API design', 'database patterns', 'authentication', 'performance'],
                'technical_context': 'Backend/API development context'
            },
            'database': {
                'focus_areas': ['query optimization', 'schema design', 'migrations', 'performance'],
                'technical_context': 'Database development context'
            },
            'devops': {
                'focus_areas': ['deployment strategies', 'infrastructure patterns', 'automation', 'monitoring'],
                'technical_context': 'DevOps/Infrastructure context'
            },
            'testing': {
                'focus_areas': ['test strategies', 'coverage patterns', 'test organization', 'quality assurance'],
                'technical_context': 'Testing/QA context'
            }
        }

    def generate_extraction_prompt(self, pattern_type: str, session_data: Dict, context: Dict = None) -> str:
        """Generate a structured extraction prompt for a specific pattern type"""

        if pattern_type not in self.prompt_templates:
            raise ValueError(f"Unknown pattern type: {pattern_type}")

        template = self.prompt_templates[pattern_type]

        # Prepare context variables
        prompt_context = {
            'project_name': context.get('project_name', 'Unknown') if context else 'Unknown',
            'tech_domains': ', '.join(context.get('tech_domains', [])) if context else 'Unknown',
            'tools_used': ', '.join(context.get('tools_used', [])) if context else 'Unknown',
            'session_complexity': context.get('complexity_indicators', {}).get('session_complexity', 'medium') if context else 'medium',
            'session_summary': self._format_session_summary(session_data),
            'timestamp': datetime.now().isoformat()
        }

        # Add pattern-specific context
        if pattern_type == 'anti_pattern':
            prompt_context['error_context'] = self._extract_error_context(session_data)
        elif pattern_type == 'journey_pattern':
            prompt_context.update(self._extract_journey_context(session_data))
        elif pattern_type == 'cross_project_pattern':
            prompt_context.update(self._extract_transferability_context(session_data, context))
        elif pattern_type == 'efficiency_pattern':
            prompt_context.update(self._extract_efficiency_context(session_data, context))

        # Apply domain-specific modifiers
        if context and context.get('tech_domains'):
            prompt_context = self._apply_domain_modifiers(prompt_context, context['tech_domains'])

        # Format the prompt
        extraction_prompt = template['extraction_prompt'].format(**prompt_context)

        return f"{template['system_prompt']}\n\n{extraction_prompt}"

    def _format_session_summary(self, session_data: Dict) -> str:
        """Format session data into a readable summary"""
        summary_parts = []

        # Add user requests
        if 'user_requests' in session_data:
            summary_parts.append("USER REQUESTS:")
            for req in session_data['user_requests'][:3]:  # Limit to first 3
                summary_parts.append(f"- {req}")

        # Add key actions
        if 'key_actions' in session_data:
            summary_parts.append("\nKEY ACTIONS:")
            for action in session_data['key_actions'][:5]:  # Limit to first 5
                summary_parts.append(f"- {action}")

        # Add outcomes
        if 'outcomes' in session_data:
            summary_parts.append("\nOUTCOMES:")
            for outcome in session_data['outcomes'][:3]:
                summary_parts.append(f"- {outcome}")

        return '\n'.join(summary_parts) if summary_parts else "Session data summary not available"

    def _extract_error_context(self, session_data: Dict) -> str:
        """Extract error context for anti-pattern analysis"""
        errors = session_data.get('errors', [])
        if errors:
            return f"Errors encountered: {'; '.join(errors[:3])}"
        return "Error context not available"

    def _extract_journey_context(self, session_data: Dict) -> Dict:
        """Extract journey-specific context"""
        return {
            'journey_type': session_data.get('journey_type', 'unknown'),
            'attempt_count': session_data.get('attempt_count', 0),
            'final_outcome': session_data.get('final_outcome', 'unknown')
        }

    def _extract_transferability_context(self, session_data: Dict, context: Dict) -> Dict:
        """Extract transferability context for cross-project patterns"""
        return {
            'tech_stack': ', '.join(context.get('file_types', [])) if context else 'unknown',
            'pattern_category': session_data.get('pattern_category', 'general'),
            'transferability_score': session_data.get('transferability_score', 0.5)
        }

    def _extract_efficiency_context(self, session_data: Dict, context: Dict) -> Dict:
        """Extract efficiency context"""
        return {
            'session_duration': session_data.get('duration', 'unknown'),
            'task_complexity': context.get('complexity_indicators', {}).get('session_complexity', 'medium') if context else 'medium',
            'tools_efficiency': session_data.get('tools_efficiency', 'standard'),
            'success_speed': session_data.get('success_speed', 'standard')
        }

    def _apply_domain_modifiers(self, prompt_context: Dict, domains: List[str]) -> Dict:
        """Apply domain-specific modifications to the prompt context"""
        # Find the most relevant domain
        primary_domain = domains[0] if domains else None

        if primary_domain in self.context_modifiers:
            modifier = self.context_modifiers[primary_domain]

            # Add domain-specific focus areas
            focus_areas = ', '.join(modifier['focus_areas'])
            prompt_context['domain_focus'] = f"\nDomain-specific focus areas: {focus_areas}"
            prompt_context['technical_context'] = modifier['technical_context']
        else:
            prompt_context['domain_focus'] = ""
            prompt_context['technical_context'] = "General development context"

        return prompt_context

    def get_system_prompt(self, pattern_type: str) -> str:
        """Get the system prompt for a specific pattern type"""
        if pattern_type not in self.prompt_templates:
            return "You are a coding pattern extraction expert."

        return self.prompt_templates[pattern_type]['system_prompt']

    def get_available_pattern_types(self) -> List[str]:
        """Get list of available pattern types"""
        return list(self.prompt_templates.keys())

    def validate_pattern_type(self, pattern_type: str) -> bool:
        """Validate that a pattern type is supported"""
        return pattern_type in self.prompt_templates

    def get_prompt_template_info(self) -> Dict[str, Dict]:
        """Get information about all available prompt templates"""
        info = {}
        for pattern_type, template in self.prompt_templates.items():
            info[pattern_type] = {
                'description': template['system_prompt'].split('.')[0] + '.',
                'focus_areas': self._extract_focus_areas_from_prompt(template['system_prompt'])
            }
        return info

    def _extract_focus_areas_from_prompt(self, system_prompt: str) -> List[str]:
        """Extract focus areas from system prompt"""
        # Simple extraction based on bullet points
        focus_areas = []
        lines = system_prompt.split('\n')
        in_focus_section = False

        for line in lines:
            line = line.strip()
            if 'Focus on:' in line:
                in_focus_section = True
                continue
            elif in_focus_section and line.startswith('-'):
                focus_areas.append(line[1:].strip())
            elif in_focus_section and not line.startswith('-') and line:
                break

        return focus_areas