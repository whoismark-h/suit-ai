# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Context Rule

**ALWAYS refer to these specification documents when gathering context:**
- `specs/PRD.md` - Product Requirements Document with features, use cases, and success metrics
- `specs/TECHNICAL_SPECS.md` - Technical specifications with architecture and implementation details

## Project Overview

suit-ai is a legal AI assistant project using Node.js with CommonJS module system. It provides AI-powered legal research, document analysis, and legal writing capabilities.

## Development Commands

Currently, the project has minimal setup:
- No build command configured
- No lint command configured
- Test command exists but is not implemented: `npm test` (currently exits with error)

## Project Structure

The project is in its initial state with only basic configuration files:
- `package.json` - Basic npm configuration with CommonJS module type
- `.mcp.json` - MCP server configuration for Claude Code integrations
- `specs/PRD.md` - Product Requirements Document for the legal AI assistant MVP

## MCP Server Integrations

The project is configured with several MCP servers:
- **context7**: For retrieving up-to-date documentation and code examples
- **supabase**: Connected to project ref `yctmxqturmkjaanarcib` (requires SUPABASE_ACCESS_TOKEN environment variable)
- **n8n-mcp**: For n8n workflow automation tools
- **n8n-workflows-docs**: Documentation for n8n workflows

## Next Steps

When developing this project, you'll need to:
1. Install necessary dependencies based on the project requirements
2. Set up build, lint, and test configurations
3. Create the initial project structure and components
4. Configure the Supabase integration for RAG database functionality
5. Implement web crawling for legal resources
6. Set up Graph RAG for legal document relationships