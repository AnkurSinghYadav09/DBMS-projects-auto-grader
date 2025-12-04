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
                # Don't add models/ prefix - use model name directly
                self.client = genai.GenerativeModel(Config.GEMINI_MODEL)
                self.use_json_mode = False
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
        """Default evaluation rubric"""
        return """Evaluate the following document according to these criteria:



SQL Implementation (25 points)
1. Table Creation Scripts (8 points)
   - 8: All 8 tables properly defined with correct data types, PK/FK, NOT NULL, CHECK, logical structure.
   - 6: Mostly correct, minor constraint or datatype issues.
   - 4: Significant issues with constraints or relationships.
   - 2: Basic structure only, major issues.
   - 0: Missing or severely flawed tables.

2. Insert Scripts & Sample Data (5 points)
   - 5: Realistic, diverse data demonstrating relationships.
   - 4: Good data, minor logic issues.
   - 3: Basic data, weak relationships.
   - 1: Minimal or unrealistic data.
   - 0: No or inappropriate data.

3. Index Creation Strategy (7 points)
   - 7: Strategic indexes on frequently queried columns; proper composite indexes.
   - 5: Good attempt, some optimization missed.
   - 3: Basic indexes with poor placement.
   - 1: Few or ineffective indexes.
   - 0: No useful indexes.

4. SQL Code Quality (5 points)
   - 5: Clean, well-formatted, consistent naming, proper SQL usage.
   - 4: Minor formatting issues.
   - 3: Functional but inconsistent.
   - 1: Poorly organized.
   - 0: Unreadable or non-functional.

------------------------------------------------------------

ER Model & Database Design (20 points)
1. ER Diagram Completeness (8 points)
   - 8: All entities, attributes, relationships clearly shown, correct notation.
   - 6: Mostly complete, minor notation/clarity issues.
   - 4: Basic, missing key elements.
   - 2: Incomplete/confusing.
   - 0: Missing/incorrect.

2. Relationship & Cardinality Accuracy (7 points)
   - 7: All relationships correct with accurate cardinality.
   - 5: Mostly correct with 1–2 errors.
   - 3: Several mistakes.
   - 1: Major misunderstanding.
   - 0: Missing/wrong.

3. Normalization (to 3NF) (5 points)
   - 5: Properly normalized to 3NF; no redundancy.
   - 4: Mostly normalized, minor issues.
   - 3: Only up to 2NF.
   - 1: Only 1NF or major violations.
   - 0: Not normalized.

------------------------------------------------------------

Query Design & Optimization (25 points)
1. Query Functionality & Correctness (10 points)
   - 10: All 5 queries correct and meaningful.
   - 8: Minor issues or 1 problematic query.
   - 6: 2+ queries flawed.
   - 3: Several incorrect.
   - 0: Missing/broken.

2. Query Complexity & Relevance (8 points)
   - 8: Uses joins, subqueries, aggregation; solves real problems.
   - 6: Good complexity, some simple queries.
   - 4: Mostly basic SELECTs.
   - 2: Very simple queries.
   - 0: No meaningful queries.

3. Index–Query Alignment (7 points)
   - 7: Indexes directly support WHERE/JOIN/ORDER BY usage.
   - 5: Good but missed opportunities.
   - 3: Weak alignment.
   - 1: Little connection.
   - 0: No optimization strategy.

------------------------------------------------------------

Design Documentation & Justification (20 points)
1. Application Scenario Understanding (5 points)
   - 5: Clear scenario, realistic roles, solid requirements.
   - 4: Good scenario, some missing details.
   - 3: Basic description.
   - 1: Minimal understanding.
   - 0: No or unrealistic scenario.

2. Entity & Attribute Justification (5 points)
   - 5: Detailed justification with logical rationale.
   - 4: Mostly justified.
   - 3: Basic, incomplete reasoning.
   - 1: Very little justification.
   - 0: None.

3. Normalization Explanation (5 points)
   - 5: Clear step-by-step explanation with dependency examples.
   - 4: Good explanation, lacks examples.
   - 3: Basic but weak explanation.
   - 1: Minimal or incorrect.
   - 0: Missing.

4. Optimization Strategy Explanation (5 points)
   - 5: Clear explanation per index linked to query patterns.
   - 4: Good but some missing connections.
   - 3: Basic explanation.
   - 1: Minimal reasoning.
   - 0: None.

------------------------------------------------------------

Originality & Authenticity (10 points)
1. Human Authenticity Markers (5 points)
   - 5: Natural inconsistencies, personal voice, realistic corrections.
   - 4: Mostly human but polished.
   - 2: Suspiciously perfect.
   - 0: Strong AI indicators.

2. Creative Problem-Solving (5 points)
   - 5: Unique, justified design choices.
   - 4: Some creativity.
   - 2: Generic tutorial-like work.
   - 0: No originality.

------------------------------------------------------------

Total possible points: 100

Additional considerations:
  "Scoring Rules:
- Sum the rubric categories exactly.
- Do NOT change scoring logic across runs.
- Follow the rubric strictly."
- Check for potential plagiarism indicators (unusual style changes, citations missing)
- Assess overall coherence and logical flow
- Note any exceptional strengths or critical weaknesses
"""
    
    @retry(stop=stop_after_attempt(Config.RETRY_ATTEMPTS), 
           wait=wait_exponential(multiplier=1, min=2, max=30))
    def evaluate(self, document_text: str, student_name: Optional[str] = None) -> Dict:
        """Evaluate document using AI API (OpenAI/Gemini/DeepSeek/Perplexity)"""
        try:
            system_prompt = """You are a DETERMINISTIC, PRECISE academic grading system. You MUST be FACTUALLY ACCURATE and produce identical scores for identical documents.

CRITICAL ACCURACY RULES:
1. ONLY mention features that ACTUALLY EXIST in the document
2. DO NOT claim formatting errors that aren't present (e.g., "NOTNULL" or "UNIQUENOTNULL")
3. DO NOT exaggerate query complexity - be honest about simple vs. complex queries
4. DO NOT claim ER diagrams exist if only text descriptions are present
5. Verify ACTUAL constraint usage (NOT NULL, CHECK, UNIQUE) - don't assume they're everywhere
6. Be SPECIFIC with evidence - cite actual table names, query numbers, constraint examples

EVIDENCE-BASED SCORING METHOD:
Count and verify actual features present in the document:

1. sql_implementation (0-25):
   COUNT EXACTLY:
   - Number of CREATE TABLE statements with proper structure
   - Actual PRIMARY KEY and FOREIGN KEY declarations present
   - Actual NOT NULL constraints (count them, don't assume)
   - Actual CHECK constraints or ENUM types present
   - UNIQUE constraints present
   - Realistic INSERT data (check if data makes sense)
   - Index definitions (CREATE INDEX statements)
   
   SCORING:
   - 25: 8+ tables, ALL constraints properly used (PK, FK, NOT NULL on critical fields, CHECK/ENUM present), realistic diverse data, 5+ strategic indexes, clean formatting
   - 19: 6-7 tables, good constraint usage, decent data quality, 3-4 indexes, minor issues only
   - 13: 4-5 tables, basic constraints (PK/FK only), simple data, 1-2 indexes, several issues
   - 6: 2-3 tables, minimal constraints, poor data quality
   - 0: 0-1 tables or fundamentally broken SQL

2. er_model (0-20):
   VERIFY ACTUAL PRESENCE:
   - Is there an ACTUAL ER diagram image/visual (not just text description)?
   - Count entities actually shown in diagram
   - Count relationships with cardinality notation
   - Check normalization evidence (separate junction tables, no transitive dependencies)
   
   SCORING:
   - 20: Complete ER diagram VISIBLE with all entities, all relationships with cardinality, full 3NF normalization proven
   - 15: Diagram present, most entities/relationships shown, 2NF or approaching 3NF
   - 10: Basic diagram OR detailed text description only (no visual), 1NF level
   - 5: Incomplete text description, missing key relationships, normalization unclear
   - 0: No ER model or description provided

3. query_design (0-25):
   ANALYZE ACTUAL QUERY COMPLEXITY (be honest):
   - Count total queries provided
   - SIMPLE query = basic SELECT with 1-2 table joins, simple WHERE
   - MODERATE query = 2-3 table joins, GROUP BY with aggregate functions, ORDER BY
   - COMPLEX query = nested subqueries (IN with SELECT), multiple joins (4+ tables), HAVING clauses, window functions, CTEs
   
   SCORING:
   - 25: 5+ queries, at least 3 are COMPLEX (nested subqueries/4+ joins/window functions), all syntactically correct, well-optimized
   - 19: 5 queries, 2 COMPLEX, rest MODERATE, all functional
   - 13: 3-4 queries, mostly MODERATE (2-3 joins, GROUP BY), maybe 1 simple, all work
   - 6: 2-3 queries, mostly SIMPLE (basic SELECT/single joins), or queries with errors
   - 0: 0-1 queries or broken syntax

4. documentation (0-20):
   CHECK ACTUAL SECTIONS PRESENT:
   - Design rationale: explanation of why entities/attributes were chosen
   - Normalization explanation: step-by-step 1NF→2NF→3NF with dependency examples
   - Optimization strategy: explanation of why each index was created
   
   SCORING:
   - 20: All 3 sections present with detailed explanations (2+ paragraphs each), clear reasoning, specific examples
   - 15: All 3 sections present, good explanations (1 paragraph each), some examples
   - 10: 2 sections present OR all 3 but brief/superficial
   - 5: Only 1 section present or very minimal documentation
   - 0: No documentation

5. originality (0-10):
   DETECT ACTUAL AUTHENTICITY:
   - Human markers: minor typos, informal language, personal reasoning, realistic mistakes
   - AI markers: perfect grammar throughout, generic explanations, tutorial-like structure, overly polished
   
   SCORING:
   - 10: Clear human work (natural imperfections, personal style, unique choices)
   - 8: Mostly human, slightly polished
   - 5: Generic but acceptable, could be tutorial-based
   - 2: Strong AI indicators (too perfect, generic reasoning)
   - 0: Obviously copied or AI-generated

GRADING ALGORITHM:
1. READ the entire document carefully
2. COUNT actual occurrences of each feature (tables, constraints, queries, sections)
3. CLASSIFY query complexity honestly (simple/moderate/complex)
4. MATCH your counts to the score bands above
5. SELECT the ONE score from allowed values: [25,19,13,6,0], [20,15,10,5,0], etc.
6. SUM all 5 scores for total_score
7. WRITE EVIDENCE-BASED feedback citing specific examples from document

FEEDBACK ACCURACY RULES:
- In "strengths": cite actual table names, query numbers, specific features found
- In "weaknesses": be specific about what's missing (e.g., "No CHECK constraints found" not "minor issues")
- In "recommendations": give concrete actions (e.g., "Add indexes on frequently joined columns like user_id" not "consider optimization")
- NEVER mention formatting errors that don't exist
- NEVER exaggerate complexity

OUTPUT (pure JSON, no markdown):
{
  "total_score": <sum of 5 categories>,
  "breakdown": {
    "sql_implementation": <25|19|13|6|0>,
    "er_model": <20|15|10|5|0>,
    "query_design": <25|19|13|6|0>,
    "documentation": <20|15|10|5|0>,
    "originality": <10|8|5|2|0>
  },
  "strengths": "<specific features with examples: 'Table X has proper FK to Y', 'Query 3 uses complex 4-table join'>",
  "weaknesses": "<specific gaps: 'No CHECK constraints found', 'Queries 1-2 are simple SELECTs only', 'ER diagram not visible, only text description'>",
  "recommendations": "<concrete actions: 'Add CHECK constraint to limit age 18-100', 'Create composite index on (user_id, date)', 'Include visual ER diagram'>",
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
            elif "quota" in error_msg.lower() or "429" in error_msg:
                return self.get_error_result("API quota exceeded. Please try again later.")
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
