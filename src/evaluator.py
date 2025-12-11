import json
import logging
from typing import Dict, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import Config

logger = logging.getLogger(__name__)

class DocumentEvaluator:
    def __init__(self):
        self.ai_provider = Config.AI_PROVIDER
        
        try:
            if self.ai_provider == "gemini":
                # Gemini API
                import google.generativeai as genai
                if not Config.GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY is not configured")
                genai.configure(api_key=Config.GEMINI_API_KEY)
                # Use correct Gemini model name (no "models/" prefix)
                model_name = Config.GEMINI_MODEL.replace("models/", "")
                self.client = genai.GenerativeModel(model_name)
                self.use_json_mode = False
                logger.info(f"Initialized Gemini with model: {model_name}")
            elif self.ai_provider == "deepseek":
                # DeepSeek API
                if not Config.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is not configured for DeepSeek")
                self.client = OpenAI(
                    api_key=Config.OPENAI_API_KEY,
                    base_url="https://api.deepseek.com"
                )
                self.use_json_mode = False
            elif Config.OPENAI_API_KEY and Config.OPENAI_API_KEY.startswith('pplx-'):
                # Perplexity API
                self.client = OpenAI(
                    api_key=Config.OPENAI_API_KEY,
                    base_url="https://api.perplexity.ai"
                )
                self.use_json_mode = False
            else:
                # OpenAI API
                if not Config.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is not configured")
                self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.use_json_mode = True
            
            self.rubric = self.load_rubric()
            logger.info("Document evaluator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize evaluator: {e}")
            raise ValueError(f"AI Provider initialization failed: {str(e)}. Please check your API keys.")
    
    def load_rubric(self) -> str:
        """Load evaluation rubric from JSON or use default"""
        rubric_file = Config.RUBRICS_DIR / "default_rubric.json"
        
        if rubric_file.exists():
            with open(rubric_file, 'r') as f:
                rubric_data = json.load(f)
                return self.format_rubric(rubric_data)
        
        # Default rubric
        return self.get_default_rubric()
    
    @staticmethod
    def format_rubric(rubric_data: Dict) -> str:
        """Format rubric JSON into prompt text"""
        criteria = rubric_data.get("criteria", [])
        rubric_text = "Evaluate the following document according to these criteria:\n\n"
        
        for item in criteria:
            rubric_text += f"{item['name']} ({item['points']} points): {item['description']}\n"
        
        rubric_text += f"\nTotal possible points: {rubric_data.get('total_points', 100)}\n"
        return rubric_text
    
    @staticmethod
    def get_default_rubric() -> str:
        """Default evaluation rubric - 4 tabs × 25 marks = 100 total"""
        return """Evaluate the following document according to these criteria:

RUBRIC STRUCTURE: 4 Tabs, Each worth 25 marks = 100 Total

============================================================
TAB 1: CREATE AND INSERT SCRIPTS (25 marks)
============================================================

Evaluation Criteria:
- Scripts must be WORKING and EXECUTABLE
- Check if CREATE TABLE statements run without errors
- Check if INSERT statements populate data successfully
- Verify table structures are logical and complete
- Verify data is realistic and demonstrates relationships

Scoring:
- 25 marks: All CREATE and INSERT scripts work perfectly. Tables properly defined with correct data types, constraints (PK, FK, NOT NULL, CHECK, UNIQUE). Realistic, diverse sample data demonstrating all relationships.
- 20 marks: Scripts mostly work with minor issues (1-2 syntax errors or missing constraints). Good data coverage.
- 15 marks: Scripts work but have several issues. Some constraints missing or incorrect. Data is basic but functional.
- 10 marks: Scripts have significant problems. Multiple errors, poor constraint usage, minimal data.
- 5 marks: Scripts barely work. Major structural issues, very limited data.
- 0 marks: Scripts don't work or are missing.

============================================================
TAB 2: ER MODEL (25 marks)
============================================================

Evaluation Criteria:
- Clear ER diagram must be present (not just text description)
- Foreign keys must be correct and viable
- Check for normalization issues (partial/transitive dependencies)
- **DEDUCT 5 marks for EACH partial or transitive dependency found**
- ER model should be normalized to 3NF

Scoring:
- Start with 25 marks
- Check if clear ER diagram exists (if only text description: deduct 10 marks)
- Verify Foreign Keys are correct and viable (if incorrect FKs: deduct 5-10 marks)
- **CRITICAL: Check for normalization violations:**
  - **Partial Dependency**: Non-prime attribute depends on part of composite key → DEDUCT 5 marks per occurrence
  - **Transitive Dependency**: Non-prime attribute depends on another non-prime attribute → DEDUCT 5 marks per occurrence
  - If fully normalized to 3NF with correct FKs and clear diagram: FULL 25 marks

Examples of violations:
- Partial: In table with composite key (StudentID, CourseID), if StudentName depends only on StudentID
- Transitive: If StudentID → DepartmentID → DepartmentName (DepartmentName transitively depends on StudentID)

Final Score = 25 - (number_of_violations × 5)

============================================================
TAB 3: INDEXES (25 marks)
============================================================

Evaluation Criteria:
- Indexes must be correctly placed according to the queries provided
- Check if indexes support WHERE clauses, JOIN conditions, ORDER BY, and frequently queried columns
- Verify index placement makes sense for query optimization

Scoring:
- 25 marks: All indexes are correctly placed according to queries. Perfect alignment with WHERE/JOIN/ORDER BY usage. Demonstrates clear understanding of query optimization.
- 20 marks: Most indexes correct, 1-2 minor misalignments or missed opportunities.
- 15 marks: Good attempt, but several indexes could be better placed or some important indexes missing.
- 10 marks: Basic indexing present but weak alignment with actual query patterns.
- 5 marks: Very few indexes or mostly incorrect placement.
- 0 marks: No indexes or completely wrong placement.

============================================================
TAB 4: DESCRIPTION/DOCUMENTATION (25 marks)
============================================================

Evaluation Criteria:
- Description must be appropriate and complete
- Should explain the application scenario, design decisions, normalization process
- Should justify entity/attribute choices and optimization strategies

Scoring:
- 25 marks: Excellent, comprehensive description. Clear application scenario, detailed justification for all design decisions, normalization steps explained, optimization strategy documented.
- 20 marks: Good description with most elements present. Minor gaps in justification or explanation.
- 15 marks: Adequate description. Covers basics but lacks depth in some areas.
- 10 marks: Basic description. Missing significant justifications or explanations.
- 5 marks: Minimal description. Very incomplete.
- 0 marks: No description or completely inadequate.

============================================================
TOTAL: 100 marks (Sum of all 4 tabs)
============================================================

CRITICAL SCORING RULES:
1. Each tab is independent and worth exactly 25 marks
2. Tab 2 (ER Model) uses DEDUCTION method: Start at 25, subtract 5 for each normalization violation
3. Be DETERMINISTIC: Same document = Same score every time
4. Do NOT invent problems that don't exist
5. Base scores on ACTUAL evidence in the document
6. Follow this rubric EXACTLY - do not deviate
"""
    
    @retry(stop=stop_after_attempt(Config.RETRY_ATTEMPTS), 
           wait=wait_exponential(multiplier=1, min=2, max=30))
    def evaluate(self, document_text: str, student_name: Optional[str] = None) -> Dict:
        """Evaluate document using AI API (OpenAI/Gemini/DeepSeek/Perplexity)"""
        try:
            system_prompt = """You are a DETERMINISTIC, PRECISE academic grading system following a strict 4-tab rubric. You MUST be FACTUALLY ACCURATE and produce identical scores for identical documents.

CRITICAL ACCURACY RULES:
1. ONLY mention features that ACTUALLY EXIST in the document
2. DO NOT claim formatting errors that aren't present
3. DO NOT exaggerate functionality - be honest about what works
4. DO NOT claim ER diagrams exist if only text descriptions are present
5. Count normalization violations EXACTLY - deduct 5 marks per violation
6. Be SPECIFIC with evidence - cite actual examples from the document

RUBRIC: 4 TABS × 25 MARKS = 100 TOTAL

============================================================
TAB 1: CREATE AND INSERT SCRIPTS (25 marks)
============================================================
EVALUATE:
- Do CREATE TABLE scripts work without errors?
- Do INSERT statements successfully populate data?
- Are table structures logical with proper constraints (PK, FK, NOT NULL, CHECK, UNIQUE)?
- Is sample data realistic and demonstrates relationships?

SCORING SCALE:
- 25: Scripts work perfectly, all constraints present, excellent realistic data
- 20: Scripts mostly work, minor issues (1-2 errors), good data coverage
- 15: Scripts work with several issues, some constraints missing, basic data
- 10: Scripts have significant problems, poor constraint usage, minimal data
- 5: Scripts barely work, major issues, very limited data
- 0: Scripts don't work or are missing

============================================================
TAB 2: ER MODEL (25 marks) - USES DEDUCTION METHOD
============================================================
START WITH 25 MARKS, THEN DEDUCT:

STEP 1: Check if ER diagram exists
- If ONLY text description (no visual diagram): DEDUCT 10 marks
- If clear visual ER diagram present: no deduction

STEP 2: Check Foreign Keys
- If Foreign Keys are incorrect or not viable: DEDUCT 5-10 marks
- If all Foreign Keys are correct and viable: no deduction

STEP 3: Check for Normalization Violations (CRITICAL)
**DEDUCT 5 MARKS FOR EACH VIOLATION FOUND:**

A) PARTIAL DEPENDENCY (violates 2NF):
   - Occurs when non-prime attribute depends on PART of a composite key
   - Example: Table(StudentID, CourseID, StudentName) - StudentName depends only on StudentID, not full key
   - Count each occurrence and deduct 5 marks

B) TRANSITIVE DEPENDENCY (violates 3NF):
   - Occurs when non-prime attribute depends on another non-prime attribute
   - Example: Table(StudentID, DepartmentID, DepartmentName) - DepartmentName transitively depends on StudentID through DepartmentID
   - Count each occurrence and deduct 5 marks

FINAL SCORE = 25 - (ER_diagram_deduction) - (FK_deduction) - (5 × number_of_normalization_violations)

Examples:
- Perfect: Visual ER diagram, correct FKs, fully normalized to 3NF = 25 marks
- Good: Visual ER diagram, correct FKs, 1 transitive dependency = 25 - 5 = 20 marks
- Fair: Text only, correct FKs, 2 violations = 25 - 10 - 10 = 5 marks

============================================================
TAB 3: INDEXES (25 marks)
============================================================
EVALUATE:
- Are indexes correctly placed according to the queries provided?
- Do indexes support WHERE clauses, JOIN conditions, ORDER BY?
- Does index placement make sense for query optimization?

SCORING SCALE:
- 25: Perfect index placement, all align with queries, excellent optimization understanding
- 20: Most indexes correct, 1-2 minor misalignments or missed opportunities
- 15: Good attempt, several indexes could be better placed or some missing
- 10: Basic indexing present but weak alignment with query patterns
- 5: Very few indexes or mostly incorrect placement
- 0: No indexes or completely wrong placement

============================================================
TAB 4: DESCRIPTION/DOCUMENTATION (25 marks)
============================================================
EVALUATE:
- Is description appropriate and complete?
- Does it explain application scenario, design decisions, normalization?
- Are entity/attribute choices and optimization strategies justified?

SCORING SCALE:
- 25: Excellent comprehensive description, clear scenario, detailed justifications, normalization steps, optimization strategy
- 20: Good description, most elements present, minor gaps
- 15: Adequate description, covers basics but lacks depth
- 10: Basic description, missing significant justifications
- 5: Minimal description, very incomplete
- 0: No description or completely inadequate

============================================================
DETERMINISTIC GRADING ALGORITHM:
============================================================
1. READ document thoroughly
2. For TAB 1: Check if scripts work, count constraints, evaluate data quality → assign 0/5/10/15/20/25
3. For TAB 2: Start at 25, count each normalization violation, check ER diagram and FKs → deduct accordingly
4. For TAB 3: Count indexes, check query alignment → assign 0/5/10/15/20/25
5. For TAB 4: Assess documentation completeness → assign 0/5/10/15/20/25
6. TOTAL = tab1 + tab2 + tab3 + tab4 (must equal 0-100)
7. Write EVIDENCE-BASED feedback citing specific examples

FEEDBACK ACCURACY RULES:
- Cite actual table names, query numbers, specific features
- Be specific about violations found (e.g., "Table X has transitive dependency: Y→Z→W")
- Give concrete recommendations with examples
- NEVER invent problems that don't exist

OUTPUT (pure JSON, no markdown):
{
  "total_score": <sum of 4 tabs, 0-100>,
  "breakdown": {
    "tab1_create_insert": <0|5|10|15|20|25>,
    "tab2_er_model": <0-25, calculated using deduction method>,
    "tab3_indexes": <0|5|10|15|20|25>,
    "tab4_description": <0|5|10|15|20|25>
  },
  "tab2_deductions": {
    "missing_visual_diagram": <0 or 10>,
    "incorrect_foreign_keys": <0, 5, or 10>,
    "partial_dependencies_count": <number>,
    "transitive_dependencies_count": <number>,
    "total_deducted": <sum of all deductions>
  },
  "strengths": "<specific features with examples from each tab>",
  "weaknesses": "<specific gaps or violations found in each tab>",
  "recommendations": "<concrete actions for improvement>",
  "plagiarism_flags": "None detected"
}
"""
            
            user_prompt = (
                f"{self.rubric}\n\n"
                f"{'Student: ' + student_name if student_name else ''}\n\n"
                f"DOCUMENT TO EVALUATE:\n\n{document_text[:15000]}"
            )
            
            
            if self.ai_provider == "gemini":
                # Gemini API - Deterministic settings
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = self.client.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": 0,
                        "top_p": 1,
                        "response_mime_type": "application/json"
                    }
                )
                content = response.text
            elif self.use_json_mode:
                # OpenAI API - supports json_object - Deterministic settings
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
            else:
                # Perplexity/DeepSeek API - no response_format parameter - Deterministic settings
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                content = response.choices[0].message.content
            # Try to extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            logger.info(f"Evaluation completed: Score {result.get('total_score')}")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            logger.error(f"Response content: {content[:500]}")
            return self.get_error_result("JSON parsing error")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Evaluation failed: {error_msg}")
            
            # Check for common API errors
            if "403" in error_msg or "leaked" in error_msg.lower():
                return self.get_error_result("API key is invalid or has been revoked. Please generate a new key.")
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                return self.get_error_result("API authentication failed. Check your API key.")
            elif "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                return self.get_error_result("API rate limit exceeded. Gemini free tier allows only 5 requests per minute. Please wait and retry.")
            else:
                return self.get_error_result(f"Evaluation error: {error_msg}")
    
    @staticmethod
    def get_error_result(error_msg: str) -> Dict:
        """Return error result structure"""
        return {
            "total_score": "ERROR",
            "breakdown": {},
            "strengths": "",
            "weaknesses": "",
            "recommendations": f"Evaluation failed: {error_msg}",
            "plagiarism_flags": "Not assessed"
        }
    
    @staticmethod
    def format_feedback(evaluation: Dict) -> str:
        """Format evaluation into readable feedback"""
        if evaluation.get("total_score") == "ERROR":
            return evaluation.get("recommendations", "Evaluation failed")
        
        feedback_parts = []
        
        if evaluation.get("strengths"):
            feedback_parts.append(f"Strengths: {evaluation['strengths']}")
        
        if evaluation.get("weaknesses"):
            feedback_parts.append(f"Areas for Improvement: {evaluation['weaknesses']}")
        
        if evaluation.get("recommendations"):
            feedback_parts.append(f"Recommendations: {evaluation['recommendations']}")
        
        if Config.INCLUDE_PLAGIARISM_CHECK and evaluation.get("plagiarism_flags"):
            feedback_parts.append(f"Plagiarism Check: {evaluation['plagiarism_flags']}")
        
        return " | ".join(feedback_parts)
