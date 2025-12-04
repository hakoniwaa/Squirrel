# Contributing to TaskMem MCP Server

Thank you for your interest in contributing to TaskMem! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

- 🐛 **Bug Reports**: Report issues you encounter
- 💡 **Feature Requests**: Suggest new functionality
- 📝 **Documentation**: Improve docs and examples
- 🔧 **Code**: Submit bug fixes and new features
- 🧪 **Testing**: Write tests and improve coverage
- 💬 **Community**: Help others in discussions

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- TypeScript knowledge
- Familiarity with MCP protocol

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/TaskMem.git
   cd TaskMem/apps/mcp
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Add your development credentials
   ```

4. **Run in development mode**:
   ```bash
   npm run dev
   ```

## 📋 Development Guidelines

### Code Style

- **TypeScript**: Use strict TypeScript with proper types
- **Formatting**: We use Prettier (run `npm run format`)
- **Linting**: Follow ESLint rules (run `npm run lint`)
- **Naming**: Use descriptive variable and function names

### Tool Development

When adding new MCP tools:

1. **Follow the pattern**:
   ```typescript
   server.tool(
     'tool_name',
     'Clear description of what this tool does and when to use it.',
     {
       param1: z.string().describe('Detailed parameter description with examples'),
       param2: z.number().optional().describe('Optional parameter description'),
     },
     async ({ param1, param2 }) => {
       try {
         // Implementation with proper error handling
         return {
           content: [{
             type: 'text',
             text: '✅ Success message with clear formatting'
           }]
         };
       } catch (error: any) {
         return {
           content: [{
             type: 'text', 
             text: `Error: ${error.message}`
           }]
         };
       }
     }
   );
   ```

2. **Include comprehensive descriptions**:
   - What the tool does
   - When to use it
   - Parameter examples
   - Expected behavior

3. **Add proper error handling**:
   - Try-catch blocks
   - User-friendly error messages
   - Helpful suggestions for fixes

4. **Format responses consistently**:
   - Use emojis for visual clarity
   - Structure with clear sections
   - Include relevant metadata

### Testing

- **Unit Tests**: Write tests for new functionality
- **Integration Tests**: Test MCP protocol compliance
- **Manual Testing**: Test with actual MCP clients

```bash
npm test                 # Run all tests
npm run test:watch      # Watch mode
npm run test:coverage   # Coverage report
```

## 🐛 Bug Reports

When reporting bugs, please include:

- **Environment**: OS, Node.js version, MCP client
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Full error logs
- **Configuration**: Relevant config (redact secrets)

## 💡 Feature Requests

For new features:

- **Use case**: Why is this needed?
- **Scope**: What should it include/exclude?
- **Examples**: How would it work?
- **Alternatives**: Other solutions considered?

## 📝 Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow coding guidelines
   - Add/update tests
   - Update documentation

3. **Test thoroughly**:
   ```bash
   npm run build
   npm test
   npm run lint
   ```

4. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add semantic search improvements
   
   - Enhanced vector search performance
   - Added similarity threshold filtering  
   - Improved error handling for edge cases"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements**:
   - Clear title and description
   - Link related issues
   - Include test results
   - Update documentation

## 🔍 Code Review

We review all PRs for:

- **Functionality**: Does it work as intended?
- **Code Quality**: Clean, readable, maintainable?
- **Performance**: No significant slowdowns?
- **Security**: No vulnerabilities introduced?
- **Tests**: Adequate test coverage?
- **Documentation**: Updated where needed?

## 📖 Documentation

When updating docs:

- **Accuracy**: Keep information current
- **Clarity**: Write for beginners
- **Examples**: Include practical code samples
- **Structure**: Organize logically

## 🏷️ Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## ❓ Questions?

- 💬 **GitHub Discussions**: General questions
- 🐛 **GitHub Issues**: Bug reports
- 📧 **Email**: maintainers@taskmem.com

## 🙏 Recognition

Contributors are recognized:

- **README**: Listed in contributors section
- **Releases**: Mentioned in release notes
- **Community**: Highlighted in discussions

## 📜 Code of Conduct

- **Be respectful**: Treat everyone with kindness
- **Be inclusive**: Welcome diverse perspectives
- **Be constructive**: Provide helpful feedback
- **Be patient**: Help newcomers learn

---

Thank you for contributing to TaskMem! Together we're building better AI memory systems. 🚀