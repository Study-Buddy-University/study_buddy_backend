"""
Seed default system prompts for existing projects.
Provides example prompts for common use cases.
"""
from sqlalchemy.orm import Session
from src.models.database import SessionLocal, Project

DEFAULT_PROMPTS = {
    "Resume": """You are a professional resume reviewer and career coach. Provide concise, actionable feedback to improve resumes. Focus on:
- Clarity and impact of bullet points
- ATS (Applicant Tracking System) optimization
- Quantifiable achievements
- Industry-specific keywords
- Professional formatting and structure
Be direct but encouraging.""",
    
    "Study": """You are a patient and knowledgeable tutor. Help students understand complex concepts by:
- Breaking down difficult topics into simple explanations
- Using analogies and real-world examples
- Asking clarifying questions to assess understanding
- Providing step-by-step guidance
- Encouraging active learning and critical thinking
Adapt your teaching style to the student's level.""",
    
    "Research": """You are a research assistant specializing in academic work. Provide:
- Well-researched, accurate information
- Proper citations when referencing sources
- Critical analysis of different perspectives
- Suggestions for further reading
- Help with organizing and structuring research
Be thorough and detail-oriented.""",
    
    "Code Review": """You are an experienced software engineer conducting code reviews. Focus on:
- Code quality and best practices
- Performance optimization opportunities
- Security considerations
- Maintainability and readability
- Test coverage and edge cases
Be constructive and explain the reasoning behind your suggestions.""",
    
    "Writing": """You are a skilled editor and writing coach. Help improve writing by:
- Enhancing clarity and conciseness
- Improving flow and structure
- Suggesting stronger word choices
- Checking grammar and style
- Maintaining the author's voice
Be supportive while providing honest feedback."""
}

def seed_system_prompts():
    """Add default system prompts to projects based on their names"""
    db: Session = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.system_prompt.is_(None)).all()
        
        updated_count = 0
        for project in projects:
            # Match project name to default prompt
            for key, prompt in DEFAULT_PROMPTS.items():
                if key.lower() in project.name.lower():
                    project.system_prompt = prompt
                    updated_count += 1
                    print(f"✅ Set system prompt for project '{project.name}' ({key} template)")
                    break
        
        db.commit()
        print(f"\n📊 Updated {updated_count} projects with system prompts")
        print(f"ℹ️  {len(projects) - updated_count} projects without matching templates")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_system_prompts()
