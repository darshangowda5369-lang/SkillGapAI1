import os
import json
import logging
import google.generativeai as genai
from flask import current_app

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        self.initialized = False
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {str(e)}")

    def _call_gemini_json(self, prompt, fallback_data):
        """
        Helper method to call Gemini, enforcing a JSON response, with a mock fallback.
        """
        if not self.initialized:
            logger.warning("Gemini API not configured. Using mock data.")
            return fallback_data

        try:
            # Enforce JSON output format
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            text_response = response.text.strip()
            return json.loads(text_response)
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            # Try once without response_mime_type in case of system issue
            try:
                response = self.model.generate_content(prompt + " Return the response ONLY as a valid JSON string.")
                text_response = response.text.strip()
                # Clean markdown wrapper if any
                if text_response.startswith("```json"):
                    text_response = text_response.split("```json")[1].split("```")[0].strip()
                elif text_response.startswith("```"):
                    text_response = text_response.split("```")[1].split("```")[0].strip()
                return json.loads(text_response)
            except Exception as inner_e:
                logger.error(f"Fallback Gemini API call failed: {str(inner_e)}")
                return fallback_data

    def extract_skills_from_resume(self, resume_text):
        prompt = f"""
        Analyze the following resume text and extract all technical and soft skills.
        Return a JSON object in the exact format:
        {{
          "skills": ["Skill1", "Skill2", "Skill3", ...]
        }}
        Provide a comprehensive list containing programming languages, frameworks, developer tools, libraries, methodologies, cloud platforms, databases, and soft skills mentioned.
        
        Resume text:
        {resume_text}
        """
        
        fallback = {
            "skills": [
                "Python", "JavaScript", "SQL", "Git", "HTML5", "CSS3", 
                "Communication", "Problem Solving", "Agile Methodologies"
            ]
        }
        return self._call_gemini_json(prompt, fallback)

    def extract_skills_from_pdf_bytes(self, pdf_bytes):
        prompt = """
        Analyze the attached PDF resume document and extract all technical and soft skills.
        Return a JSON object in the exact format:
        {
          "skills": ["Skill1", "Skill2", "Skill3", ...]
        }
        Provide a comprehensive list containing programming languages, frameworks, developer tools, libraries, methodologies, cloud platforms, databases, and soft skills mentioned.
        """
        if not self.initialized:
            logger.warning("Gemini API not configured. Using mock data for scanned PDF.")
            return {
                "skills": [
                    "Python", "JavaScript", "SQL", "Git", "HTML5", "CSS3", 
                    "Communication", "Problem Solving", "Agile Methodologies"
                ]
            }
        try:
            response = self.model.generate_content([
                {"mime_type": "application/pdf", "data": pdf_bytes},
                prompt
            ], generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text.strip())
        except Exception as e:
            logger.error(f"Gemini PDF bytes parsing failed: {str(e)}")
            # Try fallback once without JSON MIME enforce
            try:
                response = self.model.generate_content([
                    {"mime_type": "application/pdf", "data": pdf_bytes},
                    prompt + " Return response ONLY as valid JSON."
                ])
                text_response = response.text.strip()
                if text_response.startswith("```json"):
                    text_response = text_response.split("```json")[1].split("```")[0].strip()
                elif text_response.startswith("```"):
                    text_response = text_response.split("```")[1].split("```")[0].strip()
                return json.loads(text_response)
            except Exception as inner_e:
                logger.error(f"Fallback Gemini PDF bytes parsing failed: {str(inner_e)}")
                return {
                    "skills": [
                        "Python", "JavaScript", "SQL", "Git", "HTML5", "CSS3", 
                        "Communication", "Problem Solving", "Agile Methodologies"
                    ]
                }

    def generate_gap_analysis_and_roadmap(self, current_skills, career_goal):
        skills_str = ", ".join(current_skills)
        prompt = f"""
        You are an expert career advisor.
        Target Job/Career Goal: "{career_goal}"
        Current User Skills: {skills_str}
        
        Perform a gap analysis:
        1. Identify which of the user's current skills match or are relevant to the career goal.
        2. Identify the critical skill gaps (skills they need but do not have).
        3. Create a structured step-by-step learning roadmap of 3 to 6 steps to bridge the gap.
           For each step in the roadmap, outline the title, description, estimated study hours, sub-topics, covered skills, and external recommendations (like specific documentation, free youtube courses, or platform names).
        
        Return the result ONLY as a JSON object matching this schema:
        {{
          "goal": "{career_goal}",
          "skills_matched": ["SkillA", "SkillB", ...],
          "skills_missing": ["SkillX", "SkillY", ...],
          "roadmap": [
            {{
              "step_key": "step_1_unique_id",
              "title": "Step Title",
              "description": "Short explanation of the step",
              "estimated_hours": 10,
              "skills_covered": ["SkillX"],
              "topics": ["Sub-topic 1", "Sub-topic 2"],
              "external_resources": [
                {{
                  "name": "Resource Name (e.g., Python Official Docs / freeCodeCamp Tutorial)",
                  "url": "https://example.com/learn",
                  "type": "Documentation | Course | Video"
                }}
              ]
            }}
          ]
        }}
        """
        
        # Comprehensive fallback depending on the goal name
        fallback = {
            "goal": career_goal,
            "skills_matched": [s for s in current_skills if s in ["Python", "JavaScript", "SQL", "Git", "HTML5", "CSS3"]],
            "skills_missing": ["React", "Node.js", "Docker", "REST APIs", "Tailwind CSS"],
            "roadmap": [
                {
                  "step_key": "step_1_frontend",
                  "title": "Mastering Frontend Development with React",
                  "description": "Learn building modern components, hooks, routing, and styling with Tailwind CSS.",
                  "estimated_hours": 20,
                  "skills_covered": ["React", "Tailwind CSS"],
                  "topics": ["JSX", "Components & Props", "useState & useEffect Hooks", "Tailwind styling utility classes"],
                  "external_resources": [
                    {"name": "React Documentation", "url": "https://react.dev", "type": "Documentation"},
                    {"name": "Tailwind CSS Crash Course", "url": "https://tailwindcss.com/docs", "type": "Documentation"},
                    {"name": "React Course - freeCodeCamp", "url": "https://www.youtube.com/watch?v=bMknfKXIFA8", "type": "Video"}
                  ]
                },
                {
                  "step_key": "step_2_backend",
                  "title": "REST API Development with Node.js & Express",
                  "description": "Understand backend routing, middlewares, and integrating with databases.",
                  "estimated_hours": 15,
                  "skills_covered": ["Node.js", "REST APIs"],
                  "topics": ["Node runtime", "Express routing", "JSON APIs", "Error Handling"],
                  "external_resources": [
                    {"name": "Express.js Documentation", "url": "https://expressjs.com", "type": "Documentation"},
                    {"name": "Node.js Ultimate Guide - YouTube", "url": "https://www.youtube.com/watch?v=32M1al-c6yY", "type": "Video"}
                  ]
                },
                {
                  "step_key": "step_3_devops",
                  "title": "Containerization with Docker",
                  "description": "Deploy code consistently across systems using Docker containers.",
                  "estimated_hours": 8,
                  "skills_covered": ["Docker"],
                  "topics": ["Dockerfile creation", "Docker Hub", "Running containers", "Compose setup"],
                  "external_resources": [
                    {"name": "Docker Getting Started Guide", "url": "https://docs.docker.com/get-started", "type": "Documentation"}
                  ]
                }
            ]
        }
        return self._call_gemini_json(prompt, fallback)

    def generate_quiz_for_skill(self, skill_name):
        prompt = f"""
        Generate an interactive multiple-choice quiz of 5 questions to test knowledge in the skill: "{skill_name}".
        Return the response ONLY as a JSON object in this format:
        {{
          "skill_name": "{skill_name}",
          "questions": [
            {{
              "id": 1,
              "question": "The question text?",
              "options": {{
                "A": "Option A text",
                "B": "Option B text",
                "C": "Option C text",
                "D": "Option D text"
              }},
              "correct_answer": "A",
              "explanation": "Detailed explanation of why A is correct and others are not."
            }}
          ]
        }}
        Provide high-quality technical questions ranging from beginner to intermediate difficulty.
        """
        
        fallback = {
            "skill_name": skill_name,
            "questions": [
                {
                    "id": 1,
                    "question": f"What is the primary purpose of {skill_name}?",
                    "options": {
                        "A": f"It is a runtime engine for scripting.",
                        "B": f"It solves problems in building responsive components.",
                        "C": f"It is a core industry tool/methodology used for managing development lifecycle.",
                        "D": f"All of the above."
                    },
                    "correct_answer": "D",
                    "explanation": f"{skill_name} plays an essential role across modern developer setups and supports the full lifecycle of software engineering."
                },
                {
                    "id": 2,
                    "question": f"Which of the following is a standard practice when working with {skill_name}?",
                    "options": {
                        "A": "Avoiding source control entirely",
                        "B": "Following DRY (Don't Repeat Yourself) principles",
                        "C": "Re-writing database logic from scratch inside view files",
                        "D": "Exposing private keys in client-side bundles"
                    },
                    "correct_answer": "B",
                    "explanation": "DRY is a fundamental practice in software engineering that applies to all programming frameworks and tooling."
                },
                {
                    "id": 3,
                    "question": f"Which command is commonly associated with starting a project or setting up environment files in {skill_name}?",
                    "options": {
                        "A": "start --now",
                        "B": "make build",
                        "C": "It varies, but typically utilizes initialization commands provided by standard package managers or runtime setups.",
                        "D": "sys.exit()"
                    },
                    "correct_answer": "C",
                    "explanation": f"Most modern tooling for {skill_name} uses ecosystem-standard initializers."
                },
                {
                    "id": 4,
                    "question": "What is the best way to handle asynchronous errors or operations in this ecosystem?",
                    "options": {
                        "A": "Ignoring them completely",
                        "B": "Using structured error handling (try/catch or promise catching) to fail gracefully",
                        "C": "Terminating the server on any error",
                        "D": "Rebooting the client device"
                    },
                    "correct_answer": "B",
                    "explanation": "Graceful handling prevents application crashes and provides a much better user experience."
                },
                {
                    "id": 5,
                    "question": "How do developers ensure scalable architecture when structuring projects?",
                    "options": {
                        "A": "Putting all codebase files into a single huge file",
                        "B": "Separating responsibilities cleanly into services, controllers, and database access models",
                        "C": "Forcing the client to do all calculations with no backend validation",
                        "D": "Hardcoding configurations inside service functions"
                    },
                    "correct_answer": "B",
                    "explanation": "Separation of concerns allows developers to scale modules independently, write unit tests, and maintain clean code."
                }
            ]
        }
        return self._call_gemini_json(prompt, fallback)

    def generate_lesson_for_node(self, step_title, topics):
        topics_str = ", ".join(topics)
        prompt = f"""
        You are a technical educator. Write a concise, highly engaging in-platform learning lesson on the topic: "{step_title}".
        The topics to cover are: {topics_str}.
        
        Write in Markdown format. The lesson should include:
        1. A brief introduction.
        2. Clean code examples (using formatting: Python, JavaScript, CSS, or Bash depending on context) or step-by-step conceptual walkthroughs.
        3. A "Quick Check" summary of key takeaways.
        
        Return the response ONLY as a JSON object in this format:
        {{
          "title": "{step_title}",
          "content_markdown": "Write the markdown text here. Escape double quotes and newlines properly.",
          "summary": "One or two sentence summary of the lesson."
        }}
        """
        
        fallback = {
            "title": step_title,
            "summary": f"A micro-lesson introducing key concepts about {step_title} including {topics_str}.",
            "content_markdown": f"""# Learning {step_title}

Welcome to this in-platform learning module! Here, we break down the core details of **{step_title}** covering:
{chr(10).join([f'* {t}' for t in topics])}

## Introduction
Modern software platforms require modularity, clarity, and robust structures. Understanding these topics helps bridge the gap to becoming an advanced engineer.

## Code Example / Walkthrough
Here is a conceptual example displaying best practices:

```javascript
// Example component or script showing how to manage state
function handleResource(status) {{
  if (!status) {{
    console.warn("Invalid resource operation");
    return;
  }}
  console.log("Success! Processing resource update.");
}}
```

## Core Takeaways
1. Always split code logic from presentation details.
2. Read docs and verify APIs before integration.
3. Test edge cases locally.
"""
        }
        
        return self._call_gemini_json(prompt, fallback)
