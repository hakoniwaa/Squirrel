#!/usr/bin/env python3
"""
Reusable prompt templates for consistent AI interactions
Optimized for high-quality responses from GPT-4, o3, and other models
"""

from typing import List, Optional


class PromptTemplates:
    """Collection of optimized prompt templates"""

    # ============================================================
    # Code Review Templates
    # ============================================================

    CODE_REVIEW_TEMPLATE = """
You are a senior software engineer conducting a thorough code review.
Your review should be constructive, specific, and actionable.

**Code to Review:**
```{language}
{code}
```

**Review Criteria:**
{review_criteria}

**Additional Context:**
{context}

Please provide a comprehensive review covering:

1. **Code Quality**
   - Readability and clarity
   - Naming conventions
   - Code organization
   - DRY principle adherence

2. **Functionality**
   - Correctness of implementation
   - Edge case handling
   - Error handling completeness
   - Input validation

3. **Performance**
   - Algorithm efficiency
   - Resource usage
   - Potential bottlenecks
   - Optimization opportunities

4. **Security**
   - Input sanitization
   - Authentication/authorization
   - Data exposure risks
   - Dependency vulnerabilities

5. **Maintainability**
   - Test coverage needs
   - Documentation quality
   - Modularity
   - Technical debt

Format your response as:
- **Summary**: Brief overview of the code quality
- **Strengths**: What's done well
- **Critical Issues**: Must-fix problems with severity levels
- **Suggestions**: Improvements with examples
- **Code Examples**: Specific refactoring suggestions
"""

    PR_REVIEW_TEMPLATE = """
Review this pull request as a senior developer on the team.

**PR Title:** {pr_title}
**Description:** {pr_description}
**Changed Files:** {file_count}
**Lines Changed:** +{additions} -{deletions}

**Diff:**
```diff
{diff}
```

**Review Focus Areas:** {focus_areas}

Provide a structured review:

1. **Overall Assessment** (1-2 sentences)
2. **Architecture Impact** (if any)
3. **Breaking Changes** (if any)
4. **Security Considerations**
5. **Performance Impact**
6. **Testing Coverage**
7. **Specific Issues** (with line numbers)
8. **Positive Highlights**
9. **Requested Changes** (must fix)
10. **Suggestions** (nice to have)

Use constructive language and provide code examples for suggested changes.
"""

    # ============================================================
    # Code Analysis Templates
    # ============================================================

    SECURITY_ANALYSIS_TEMPLATE = """
Perform a comprehensive security analysis as a security expert.

**Code:**
```{language}
{code}
```

**Environment:** {environment}
**Dependencies:** {dependencies}

Analyze for:

1. **Input Validation**
   - SQL injection vulnerabilities
   - XSS vulnerabilities
   - Command injection risks
   - Path traversal issues

2. **Authentication & Authorization**
   - Weak authentication methods
   - Missing authorization checks
   - Session management issues
   - Token security

3. **Data Security**
   - Sensitive data exposure
   - Insecure data storage
   - Weak encryption
   - Information leakage

4. **Dependencies**
   - Known vulnerabilities (CVEs)
   - Outdated packages
   - Unnecessary permissions

5. **Security Best Practices**
   - OWASP Top 10 compliance
   - Secure coding standards
   - Error handling (no stack traces)
   - Logging sensitive data

Output format (JSON):
{
  "risk_level": "critical|high|medium|low",
  "vulnerabilities": [
    {
      "type": "string",
      "severity": "critical|high|medium|low",
      "description": "string",
      "location": "line numbers or function names",
      "remediation": "string",
      "code_example": "string"
    }
  ],
  "secure_practices": ["list of good practices found"],
  "recommendations": ["prioritized list of security improvements"]
}
"""

    PERFORMANCE_ANALYSIS_TEMPLATE = """
Analyze code performance as a performance engineering expert.

**Code:**
```{language}
{code}
```

**Performance Context:**
- Expected load: {expected_load}
- Critical paths: {critical_paths}
- SLA requirements: {sla_requirements}

Analyze:

1. **Algorithm Complexity**
   - Time complexity (Big O)
   - Space complexity
   - Nested loops analysis
   - Recursive call optimization

2. **Resource Usage**
   - Memory allocation patterns
   - CPU-intensive operations
   - I/O operations
   - Network calls

3. **Bottlenecks**
   - Database queries (N+1 problems)
   - Synchronous blocking operations
   - Inefficient data structures
   - Unnecessary computations

4. **Caching Opportunities**
   - Computation results
   - Database queries
   - External API calls
   - Static resources

5. **Optimization Suggestions**
   - Algorithm improvements
   - Data structure changes
   - Parallelization opportunities
   - Lazy loading possibilities

Provide specific, measurable improvements with before/after examples.
"""

    ARCHITECTURE_ANALYSIS_TEMPLATE = """
Analyze the software architecture as a principal architect.

**Code Structure:**
```{language}
{code}
```

**Project Context:**
- Design patterns used: {patterns}
- Architecture style: {architecture_style}
- Scale requirements: {scale_requirements}

Evaluate:

1. **Design Principles**
   - SOLID principles adherence
   - DRY (Don't Repeat Yourself)
   - KISS (Keep It Simple)
   - YAGNI (You Aren't Gonna Need It)

2. **Architecture Patterns**
   - Pattern appropriateness
   - Implementation correctness
   - Consistency across codebase
   - Anti-patterns present

3. **Modularity & Coupling**
   - Module cohesion
   - Inter-module dependencies
   - Interface design
   - Abstraction levels

4. **Scalability**
   - Horizontal scaling readiness
   - Stateless design
   - Database design
   - Caching strategy

5. **Maintainability**
   - Code organization
   - Naming conventions
   - Documentation needs
   - Test structure

Provide architectural recommendations with diagrams (in Mermaid format) where helpful.
"""

    # ============================================================
    # Code Generation Templates
    # ============================================================

    CODE_GENERATION_TEMPLATE = """
Generate production-ready {language} code based on these requirements.

**Requirements:**
{requirements}

**Technical Constraints:**
- Language version: {language_version}
- Framework/Libraries: {frameworks}
- Style guide: {style_guide}
- Performance requirements: {performance_reqs}

**Context:**
{context}

**Existing Code Patterns:**
```{language}
{code_patterns}
```

Generate code that:
1. Follows established patterns in the codebase
2. Includes comprehensive error handling
3. Has proper logging at appropriate levels
4. Includes type hints/annotations
5. Is well-documented with docstrings
6. Includes unit test examples
7. Follows security best practices
8. Is optimized for readability and performance

Structure the response as:
1. Main implementation
2. Error handling utilities
3. Test examples
4. Usage documentation
5. Integration notes
"""

    TEST_GENERATION_TEMPLATE = """
Generate comprehensive tests as a QA engineer with deep testing expertise.

**Code to Test:**
```{language}
{code}
```

**Testing Framework:** {framework}
**Coverage Target:** {coverage_target}%
**Test Strategy:** {test_strategy}

Generate tests covering:

1. **Unit Tests**
   - All public methods/functions
   - Happy path scenarios
   - Edge cases
   - Error conditions
   - Boundary values

2. **Integration Tests** (if applicable)
   - Component interactions
   - External dependencies
   - Database operations
   - API endpoints

3. **Test Fixtures**
   - Mock objects
   - Test data factories
   - Setup/teardown helpers
   - Reusable assertions

4. **Special Scenarios**
   - Concurrency issues
   - Performance benchmarks
   - Security test cases
   - Regression tests

5. **Test Organization**
   - Clear test names (Given-When-Then)
   - Grouped by functionality
   - Isolated and independent
   - Fast execution

Include comments explaining the testing strategy and any complex test setups.
"""

    REFACTORING_TEMPLATE = """
Refactor this code as a senior developer focused on clean code principles.

**Original Code:**
```{language}
{code}
```

**Refactoring Goals:**
{refactoring_goals}

**Constraints:**
- Maintain backward compatibility: {backward_compatible}
- Performance requirements: {performance_reqs}
- Timeline: {timeline}

Apply these refactoring techniques as appropriate:

1. **Code Smells to Fix**
   - Long methods → Extract methods
   - Large classes → Split responsibilities
   - Duplicate code → Extract common functionality
   - Complex conditionals → Simplify or use polymorphism
   - Dead code → Remove

2. **Design Patterns to Apply**
   - Identify applicable patterns
   - Implement cleanly
   - Document pattern usage

3. **Modernization**
   - Update to modern language features
   - Improve type safety
   - Enhance error handling
   - Add async/await where beneficial

4. **Performance Improvements**
   - Algorithm optimization
   - Reduce memory allocation
   - Minimize I/O operations
   - Add caching where appropriate

Provide:
- Refactored code with clear comments on changes
- Migration guide if breaking changes
- Performance comparison
- Test updates needed
"""

    # ============================================================
    # Documentation Templates
    # ============================================================

    DOCUMENTATION_TEMPLATE = """
Create comprehensive documentation as a technical writer.

**Code to Document:**
```{language}
{code}
```

**Documentation Type:** {doc_type}
**Target Audience:** {audience}
**Documentation Style:** {style_guide}

Create documentation including:

1. **Overview**
   - Purpose and goals
   - Key features
   - Architecture overview
   - Dependencies

2. **API Documentation**
   - Class/function descriptions
   - Parameters with types
   - Return values
   - Exceptions raised
   - Usage examples

3. **Code Examples**
   - Basic usage
   - Advanced scenarios
   - Error handling
   - Best practices

4. **Integration Guide**
   - Setup instructions
   - Configuration options
   - Integration patterns
   - Troubleshooting

5. **Additional Sections**
   - Performance considerations
   - Security notes
   - Migration guides
   - FAQ section

Use clear, concise language with proper formatting and code highlighting.
"""

    API_DOCUMENTATION_TEMPLATE = """
Document this API as a technical writer specializing in developer documentation.

**API Code:**
```{language}
{code}
```

**API Type:** {api_type}
**Version:** {version}

Generate OpenAPI/Swagger-compatible documentation including:

1. **Endpoint Documentation**
   - HTTP method and path
   - Purpose and description
   - Authentication requirements
   - Rate limiting info

2. **Request Details**
   - Headers required
   - Path parameters
   - Query parameters
   - Request body schema
   - Content types

3. **Response Details**
   - Success responses (2xx)
   - Error responses (4xx, 5xx)
   - Response schemas
   - Response headers

4. **Code Examples**
   - cURL examples
   - Language-specific examples ({languages})
   - SDK usage
   - Error handling

5. **Additional Information**
   - Versioning strategy
   - Deprecation notices
   - Changelog references
   - Related endpoints

Format as both human-readable and OpenAPI spec.
"""

    # ============================================================
    # Debugging Templates
    # ============================================================

    DEBUG_ANALYSIS_TEMPLATE = """
Debug this issue as an expert debugging engineer.

**Error Information:**
- Error Message: {error_message}
- Error Type: {error_type}
- Stack Trace:
```
{stack_trace}
```

**Problematic Code:**
```{language}
{code}
```

**Environment:**
- Language Version: {language_version}
- Dependencies: {dependencies}
- OS: {operating_system}
- Recent Changes: {recent_changes}

Provide debugging analysis:

1. **Root Cause Analysis**
   - Primary cause identification
   - Contributing factors
   - Why it occurs in this context

2. **Step-by-Step Debugging**
   - How to reproduce
   - Debugging commands/tools
   - What to look for
   - Expected vs actual behavior

3. **Solution**
   - Immediate fix
   - Code changes needed
   - Configuration updates
   - Workarounds available

4. **Prevention**
   - How to prevent recurrence
   - Tests to add
   - Monitoring to implement
   - Best practices to follow

5. **Related Issues**
   - Similar problems to check
   - Potential cascading effects
   - Performance impact

Include specific code fixes with explanations.
"""

    ERROR_EXPLANATION_TEMPLATE = """
Explain this error in detail for a {experience_level} developer.

**Error:** {error_message}
**Context:** {error_context}
**Code Section:**
```{language}
{code_snippet}
```

Explain:
1. What the error means in simple terms
2. Why it's happening in this specific case
3. Common causes of this error
4. How to fix it (step by step)
5. How to prevent it in the future
6. Helpful resources or documentation

Use analogies and examples appropriate for {experience_level} level.
"""

    # ============================================================
    # Code Conversion Templates
    # ============================================================

    LANGUAGE_CONVERSION_TEMPLATE = """
Convert this code from {source_language} to {target_language} as a polyglot programmer.

**Source Code ({source_language}):**
```{source_language}
{source_code}
```

**Conversion Requirements:**
- Maintain exact functionality
- Use idiomatic {target_language} patterns
- Preserve comments (translated)
- Handle language-specific differences
- Optimize for {target_language} performance

**Target Environment:**
- Version: {target_version}
- Framework: {target_framework}
- Style Guide: {style_guide}

Provide:
1. **Converted Code**
   - Full implementation
   - Idiomatic style
   - Proper error handling
   - Type annotations (if applicable)

2. **Migration Notes**
   - Key differences explained
   - Potential gotchas
   - Performance considerations
   - Testing recommendations

3. **Dependencies**
   - Required packages
   - Installation instructions
   - Version compatibility

Include comments explaining non-obvious conversions.
"""

    MODERNIZATION_TEMPLATE = """
Modernize this legacy code to current best practices.

**Legacy Code:**
```{language}
{code}
```

**Current Version:** {current_version}
**Target Version:** {target_version}
**Modernization Goals:** {goals}

Modernize by:

1. **Language Features**
   - Update syntax to modern standards
   - Use new language features
   - Remove deprecated methods
   - Improve type safety

2. **Patterns & Practices**
   - Apply modern design patterns
   - Update to current best practices
   - Improve error handling
   - Add proper logging

3. **Dependencies**
   - Update to current libraries
   - Remove obsolete dependencies
   - Use modern alternatives
   - Security updates

4. **Performance**
   - Use modern APIs
   - Optimize algorithms
   - Improve memory usage
   - Add caching

5. **Testing & Documentation**
   - Add modern test patterns
   - Update documentation
   - Add type hints
   - Improve comments

Provide a migration guide with step-by-step instructions.
"""

    # ============================================================
    # Utility Methods
    # ============================================================

    @staticmethod
    def format_code_review(
        code: str,
        language: str,
        review_criteria: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Format a code review prompt"""
        criteria = review_criteria or ["correctness", "performance", "security", "maintainability"]
        return PromptTemplates.CODE_REVIEW_TEMPLATE.format(
            language=language,
            code=code,
            review_criteria="\n".join(f"- {c}" for c in criteria),
            context=context or "No additional context provided",
        )

    @staticmethod
    def format_test_generation(
        code: str,
        language: str,
        framework: str,
        coverage_target: int = 80,
        test_strategy: Optional[str] = None,
    ) -> str:
        """Format a test generation prompt"""
        return PromptTemplates.TEST_GENERATION_TEMPLATE.format(
            language=language,
            code=code,
            framework=framework,
            coverage_target=coverage_target,
            test_strategy=test_strategy or "unit and integration testing",
        )

    @staticmethod
    def format_security_analysis(
        code: str,
        language: str,
        environment: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """Format a security analysis prompt"""
        return PromptTemplates.SECURITY_ANALYSIS_TEMPLATE.format(
            language=language,
            code=code,
            environment=environment or "production",
            dependencies=", ".join(dependencies) if dependencies else "none specified",
        )

    @staticmethod
    def format_debug_analysis(
        error_message: str, error_type: str, stack_trace: str, code: str, language: str, **kwargs
    ) -> str:
        """Format a debugging prompt"""
        return PromptTemplates.DEBUG_ANALYSIS_TEMPLATE.format(
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            code=code,
            language=language,
            language_version=kwargs.get("language_version", "latest"),
            dependencies=kwargs.get("dependencies", "not specified"),
            operating_system=kwargs.get("operating_system", "unknown"),
            recent_changes=kwargs.get("recent_changes", "none provided"),
        )

    @staticmethod
    def format_refactoring(
        code: str,
        language: str,
        goals: Optional[List[str]] = None,
        backward_compatible: bool = True,
        **kwargs,
    ) -> str:
        """Format a refactoring prompt"""
        refactoring_goals = goals or [
            "improve readability",
            "reduce complexity",
            "enhance performance",
        ]
        return PromptTemplates.REFACTORING_TEMPLATE.format(
            language=language,
            code=code,
            refactoring_goals="\n".join(f"- {g}" for g in refactoring_goals),
            backward_compatible="Yes" if backward_compatible else "No",
            performance_reqs=kwargs.get("performance_reqs", "standard"),
            timeline=kwargs.get("timeline", "flexible"),
        )


# ============================================================
# Specialized Prompt Collections
# ============================================================


class ArchitecturePrompts:
    """Prompts for architectural analysis and design"""

    MICROSERVICE_DESIGN = """
Design a microservice architecture for these requirements:
{requirements}

Consider:
- Service boundaries and responsibilities
- Communication patterns (sync/async)
- Data consistency strategies
- Service discovery and routing
- Fault tolerance and resilience
- Monitoring and observability
"""

    SYSTEM_DESIGN = """
Design a system architecture for:
{system_description}

Requirements:
- Scale: {scale_requirements}
- Performance: {performance_requirements}
- Availability: {availability_requirements}

Provide:
1. High-level architecture diagram (Mermaid)
2. Component descriptions
3. Technology choices with rationale
4. Scaling strategy
5. Failure scenarios and mitigation
"""


class SecurityPrompts:
    """Security-focused prompt templates"""

    THREAT_MODELING = """
Perform threat modeling using STRIDE methodology:
{system_description}

Identify:
- Spoofing threats
- Tampering threats
- Repudiation threats
- Information disclosure threats
- Denial of service threats
- Elevation of privilege threats

For each threat, provide:
- Description
- Attack vectors
- Impact assessment
- Mitigation strategies
"""

    SECURITY_CHECKLIST = """
Generate a security checklist for:
{application_type}

Include checks for:
- Authentication and authorization
- Input validation and sanitization
- Cryptography usage
- Session management
- Error handling and logging
- Third-party dependencies
- Infrastructure security
"""


class OptimizationPrompts:
    """Performance optimization prompt templates"""

    DATABASE_OPTIMIZATION = """
Optimize this database query/schema:
{database_code}

Database: {database_type}
Current performance: {current_metrics}

Analyze and suggest:
1. Query optimization
2. Index strategies
3. Schema improvements
4. Caching opportunities
5. Partitioning strategies
"""

    ALGORITHM_OPTIMIZATION = """
Optimize this algorithm:
{algorithm_code}

Current complexity: {current_complexity}
Constraints: {constraints}

Provide:
1. Optimized implementation
2. Complexity analysis
3. Trade-offs
4. Benchmark comparison
5. When to use each approach
"""
