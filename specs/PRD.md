# Product Requirements Document (PRD)
## Legal AI Assistant - MVP

### Product Overview
suit-ai is an AI-powered legal assistant designed to streamline legal research, document analysis, and legal writing tasks for law professionals.

### Target Users
- **Primary**: Lawyers and attorneys
- **Secondary**: Paralegals and legal researchers
- **Tertiary**: Legal departments in corporations

### Core Features (MVP)

#### 1. Legal Resource Crawling
- Authenticate and access legal web resources
- Extract structured content from legal databases
- Maintain compliance with data access policies

#### 2. RAG Database Storage
- Store legal content using Supabase vector store
- Implement Graph RAG for relationship mapping between laws, cases, and precedents
- Enable efficient retrieval and cross-referencing

#### 3. Legal Information Retrieval
- Query the RAG database for relevant legal information
- Return contextually accurate results with source citations
- Support complex legal queries with multiple parameters

#### 4. Legal Opinion Generation
- Generate well-reasoned legal opinions based on retrieved information
- Structure opinions with proper legal formatting
- Include relevant case law and statute citations

#### 5. Memo Drafting
- Create professional legal memoranda
- Support various memo types (research, client advisory, internal)
- Maintain consistent legal writing standards

#### 6. Document Red Flag Detection
- Analyze legal documents for potential issues
- Highlight problematic clauses or missing elements
- Provide risk assessment summaries

#### 7. Law Referencing System
- Automatically cite relevant laws and regulations
- Maintain proper legal citation format
- Cross-reference related legal provisions

### Use Cases

#### Legal Research
- **Scenario**: Attorney needs to research precedents for a contract dispute
- **Flow**: Query → RAG retrieval → Relevant cases and statutes → Formatted results

#### Document Review
- **Scenario**: Review a complex commercial agreement
- **Flow**: Upload document → Analysis → Red flags identified → Risk report generated

#### Memo Creation
- **Scenario**: Draft a client advisory on new regulations
- **Flow**: Topic input → Research → Draft generation → Citations included

### Success Metrics
- **Accuracy**: 95%+ accuracy in legal citations and references
- **Time Savings**: Reduce research time by 70%
- **User Satisfaction**: 4.5+ star rating from legal professionals
- **Adoption Rate**: 80% daily active usage among target users

### Key Differentiators
- Authenticated access to premium legal databases
- Graph-based relationship mapping for comprehensive legal analysis
- Real-time law updates and tracking
- Professional-grade legal document generation

### Constraints & Considerations
- Must maintain attorney-client privilege standards
- Compliance with legal data protection requirements
- Cannot replace legal judgment - tool for assistance only
- Jurisdiction-specific customization required