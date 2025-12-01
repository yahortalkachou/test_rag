import re
from typing import Dict, List, Optional, Tuple

class ProjectBlockParser:
    """Parser for detecting and extracting projects block from CV text."""
    
    # Patterns for project block detection
    PROJECT_SECTION_PATTERNS = [
        r'projects?[\s]*:?',
        r'experience[\s]*:?',
        r'work experience[\s]*:?',
        r'project experience[\s]*:?',
        r'проекты?[\s]*:?',
        r'опыт работы[\s]*:?',
    ]
    
    # Patterns for project roles and period
    PROJECT_ROLE_PATTERNS = [
        r'project roles?',
        r'role[s]?',
        r'должность',
        r'роль'
    ]
    
    PROJECT_PERIOD_PATTERNS = [
        r'period',
        r'duration',
        r'время',
        r'период'
    ]
    
    def __init__(self):
        self.compiled_section_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.PROJECT_SECTION_PATTERNS]
        self.compiled_role_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.PROJECT_ROLE_PATTERNS]
        self.compiled_period_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.PROJECT_PERIOD_PATTERNS]
    
    def find_projects_block(self, cv_text: str) -> Dict[str, any]:
        """
        Find and extract projects block from CV text.
        
        Returns:
            Dict with 'found', 'start_pos', 'end_pos', 'projects_text', 'confidence'
        """
        lines = cv_text.split('\n')
        project_start = -1
        project_end = -1
        confidence = 0
        
        # Strategy 1: Look for project section headers
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Check if this line matches project section pattern
            for pattern in self.compiled_section_patterns:
                if pattern.search(line_clean):
                    project_start = i
                    confidence = 0.8
                    break
            
            # Additional confidence if we find project roles/period patterns shortly after
            if project_start != -1 and i > project_start:
                if any(pattern.search(line_clean) for pattern in self.compiled_role_patterns):
                    confidence = min(confidence + 0.1, 1.0)
                if any(pattern.search(line_clean) for pattern in self.compiled_period_patterns):
                    confidence = min(confidence + 0.1, 1.0)
                
                # Look for bullet points or project descriptions
                if re.search(r'^[•\-\*]\s', line.strip()) or re.search(r'^[a-z]\.\s', line.strip()):
                    confidence = min(confidence + 0.1, 1.0)
        
        # Strategy 2: If no clear section header found, look for project-like content
        if project_start == -1:
            for i, line in enumerate(lines):
                if self._looks_like_project_content(line):
                    project_start = i
                    confidence = 0.6
                    break
        
        # Find the end of projects block
        if project_start != -1:
            project_end = self._find_projects_end(lines, project_start)
        
        # Extract projects text
        projects_text = ""
        if project_start != -1 and project_end != -1:
            projects_text = '\n'.join(lines[project_start:project_end])
        
        return {
            'found': project_start != -1,
            'start_pos': project_start,
            'end_pos': project_end,
            'projects_text': projects_text,
            'confidence': confidence,
            'line_count': project_end - project_start if project_end != -1 else 0
        }
    
    def _looks_like_project_content(self, line: str) -> bool:
        """Check if a line looks like project content."""
        line_clean = line.strip().lower()
        
        # Project title indicators (all caps, specific keywords)
        if (line_clean.isupper() and len(line_clean) > 5 and 
            not any(keyword in line_clean for keyword in ['education', 'language', 'domain', 'skill'])):
            return True
        
        # Project role indicators
        if any(pattern.search(line_clean) for pattern in self.compiled_role_patterns):
            return True
        
        # Project period indicators
        if any(pattern.search(line_clean) for pattern in self.compiled_period_patterns):
            return True
        
        # Responsibilities/achievements indicators
        if any(keyword in line_clean for keyword in ['responsibilities', 'achievements', 'duties', 'environment']):
            return True
        
        return False
    
    def _find_projects_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of projects block."""
        end_indicators = [
            'education', 'skills', 'certificates', 'languages', 
            'contact', 'references', 'personal', 'hobbies',
            'образование', 'навыки', 'контакты', 'личные'
        ]
        
        for i in range(start_idx + 1, len(lines)):
            line_clean = lines[i].strip().lower()
            
            # Check for next major section
            if any(indicator in line_clean for indicator in end_indicators):
                return i
            
            # Check for empty lines followed by new section
            if (line_clean == '' and i + 1 < len(lines) and 
                lines[i + 1].strip() != '' and 
                not self._looks_like_project_content(lines[i + 1])):
                return i
        
        return len(lines)


# Usage example with your CV sample
if __name__ == "__main__":
    # Your CV text from earlier
    cv_text = """
Egor
SENIOR AI ENGINEER / MACHINE LEARNING ENGINEER / MLOPS ENGINEER
Education
Computer Science and Software Engineering
Language proficiency
English — B2
Domains
FinTech
eCommerce	Senior AI engineer / Machine Learning engineer / MLOps engineer with 7 years of experience. 
I am a Senior AI/ML Engineer with more than 6 years of experience, specializing in NLP, Generative AI, and Computer Vision across diverse domains like FinTech and eCommerce. I excel in orchestrating the seamless integration of ML models into production, building robust AI solutions with Python, and developing scalable APIs using FastAPI. My expertise includes dealing with SOTA LLMs, architecting advanced agentic workflows with LangGraph, all within Dockerized environments. Proficient in MLOps best practices, I leverage Git and GitLab CI/CD for automated pipelines and deploy serverless applications on AWS. With a strong background in large-scale coding projects and efficient dependency management using Poetry.
Programming Languages
Python.
Data Science
Numpy, Pandas.
Machine Learning
Scikit-learn, XGBoost.
Deep Learning
TensorFlow, Keras, PyTorch, Hugging Face, BitsAndBytes, ONNX, NVIDIA TensorRT, DeepSORT, ByteTrack.
Computer Vision
OpenCV, Ultralytics, MMDetection.
Natural Language Processing
Gensim, Spacy, LlamaIndex, PEFT.
AI Tools
OpenAI API, LangChain, LlamaIndex, LangSmith, LangGraph, RAGAS.
Cloud
AWS (Sagemaker, EKS, ECR, CloudWatch, RedShift, Lambda, KMS, DynamoDB, etc).
MLOps
MLflow.
Backend
FastAPI, SQLAlchemy, Poetry.
Data Engineering
Apache Spark.
Databases
PostgreSQL.
DevOps
Docker, Kubernetes(k8s), GitLab CI, Grafana, Prometheus.
Source control systems
Git, Github, GitLab.

Projects	
REGULATORY TRAINING PLATFORM
Developed an AI based recommendation system for a regulatory training platform .	Project roles
Machine Learning Engineer / MLOps Engineer
Period
03.2024 – till now
Responsibilities & achievements
    • Architected and implemented a high-fidelity, multi-step RAG system designed for complex legal and financial regulatory documents, utilizing techniques like query routing and recursive retrieval to ensure high-quality and relevancy of source material;
    • Engineered a comprehensive document parsing pipeline capable of extracting structured data and text from complex regulatory documents (PDFs, annual reports), ensuring clean data ingestion into the vector database;
    • Established a stringent GenAI evaluation framework using RAGAS to measure the factual accuracy, context adherence, and relevance of the various LLM's generated training content and chatbot responses;
    • Trained and fine-tuned domain-specific LLMs (classic ML ,models and BERT-like architectures for classification, LLMs for content generation) to create an AI-Driven Training Generator that produces role- and risk-based programs in minutes;
    • Developed and optimized scalable ETL pipelines to ingest and process web-scraped regulatory documents, aligning training content requirements with real-time AML governance changes;
    • Implemented an intuitive chatbot UI that integrates directly with the RAG system, allowing users (bank personnel) to query compliance rules and receive instant, grounded answers;
    • Designed, trained, and optimized a multi-criteria recommendation system to match employee roles and assessed risk levels to mandatory training modules, integrating NLP features derived from document parsing;
    • Conducted rigorous ML model experimentation and A/B testing on recommendation and content generation algorithms to maximize the relevance and accuracy of training suggestions;
    • Built FastAPI endpoints to serve low-latency, real-time training recommendations and RAG query services, supporting the platform's API expansion and integration with banks/regulated companies;
    • Implemented CI/CD pipelines (e.g., GitHub Actions or GitLab CI) to automate the building, testing, and deployment of the containerized GenAI services;
    • Established monitoring and alerting dashboards to track recommendation quality (click-through rates, relevance metrics) and detect model/content drift in the live production environment;
Environment
Python, Pandas, NumPy, Scikit-learn, PyTorch, TensorFlow, Keras, OpenAI API, LangChain, LangGraph, LangSmith, LlamaIndex, Hugging Face, BitsAndBytes, PEFT, RAGAS, FastAPI, PostgreSQL, Apache Spark, Docker, Kubernetes(k8s), Poetry, AWS(Sagemaker, EKS, ECR, CloudWatch, RedShift, Lambda, KMS, DynamoDB, etc.), Git, GitLab, GitLab CI.
"""

    parser = ProjectBlockParser()
    result = parser.find_projects_block(cv_text)
    
    print("=== PROJECT BLOCK PARSER RESULTS ===")
    print(f"Found: {result['found']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Position: lines {result['start_pos']}-{result['end_pos']}")
    print(f"Lines found: {result['line_count']}")
    print("\n=== EXTRACTED PROJECTS TEXT ===")
    print(result['projects_text'][:500] + "..." if len(result['projects_text']) > 500 else result['projects_text'])