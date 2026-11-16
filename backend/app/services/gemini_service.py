import os
import json
import logging
import re
from urllib.parse import urlparse

import google.generativeai as genai
from flask import current_app

logger = logging.getLogger(__name__)

class GeminiService:
    SKILL_RESOURCE_MAP = {
        'python': 'https://docs.python.org/3/tutorial/',
        'javascript': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
        'html': 'https://developer.mozilla.org/en-US/docs/Web/HTML',
        'css': 'https://developer.mozilla.org/en-US/docs/Web/CSS',
        'react': 'https://react.dev/learn',
        'typescript': 'https://www.typescriptlang.org/docs/',
        'node.js': 'https://nodejs.org/en/learn/',
        'sql': 'https://www.w3schools.com/sql/',
        'postgresql': 'https://www.postgresql.org/docs/',
        'git': 'https://git-scm.com/doc',
        'docker': 'https://docs.docker.com/get-started/',
        'kubernetes': 'https://kubernetes.io/docs/home/',
        'linux': 'https://www.linuxfoundation.org/blog/what-is-linux/',
        'aws': 'https://docs.aws.amazon.com/',
        'azure': 'https://learn.microsoft.com/azure/',
        'gcp': 'https://cloud.google.com/docs',
        'rest apis': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview',
        'api': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview',
        'statistics': 'https://www.khanacademy.org/math/statistics-probability',
        'machine learning': 'https://scikit-learn.org/stable/tutorial/index.html',
        'pandas': 'https://pandas.pydata.org/docs/getting_started/intro_tutorials/',
        'numpy': 'https://numpy.org/doc/stable/user/quickstart.html',
        'tableau': 'https://www.tableau.com/learn/training',
        'power bi': 'https://learn.microsoft.com/power-bi/',
        'networking': 'https://www.cloudflare.com/learning/network-layer/what-is-a-network/',
        'cybersecurity': 'https://owasp.org/www-project-web-security-testing-guide/',
        'testing': 'https://www.w3.org/WAI/intro/accessibility.php',
        'debugging': 'https://developer.mozilla.org/en-US/docs/Learn/Common_questions/What_are_browser_developer_tools',
        'cloud': 'https://learn.microsoft.com/azure/architecture/cloud-adoption/',
        'devops': 'https://learn.microsoft.com/azure/devops/?view=azure-devops',
        'security': 'https://owasp.org/www-project-top-ten/',
        'communication': 'https://www.coursera.org/specializations/effective-business-communication',
        'problem solving': 'https://www.khanacademy.org/computing/computer-science/algorithms',
        'programming fundamentals': 'https://www.freecodecamp.org/learn/',
        'version control': 'https://git-scm.com/book/en/v2',
        'cloud fundamentals': 'https://cloud.google.com/learn/what-is-cloud-computing',
        'data pipelines': 'https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html',
        'model evaluation': 'https://scikit-learn.org/stable/modules/model_evaluation.html',
        'data visualization': 'https://www.khanacademy.org/math/statistics-probability',
        'accessibility': 'https://www.w3.org/WAI/fundamentals/accessibility-intro/',
        'testing frameworks': 'https://docs.pytest.org/en/stable/getting-started.html',
        'automation': 'https://playwright.dev/docs/intro',
        'observability': 'https://opentelemetry.io/docs/concepts/observability-primer/',
        'incident response': 'https://www.cisa.gov/topics/cyber-threats-and-advisories/incident-response',
        'cryptography': 'https://cryptography.io/en/latest/',
        'terraform': 'https://developer.hashicorp.com/terraform/tutorials',
        'ci/cd': 'https://docs.github.com/en/actions',
        'monitoring': 'https://prometheus.io/docs/introduction/overview/',
        'infrastructure': 'https://developer.hashicorp.com/terraform/intro',
        'security': 'https://owasp.org/www-project-top-ten/',
    }
    ROLE_SKILLS_MAP = {
        'data scientist': ['python', 'statistics', 'probability', 'sql', 'pandas', 'numpy', 'data visualization', 'machine learning', 'feature engineering', 'model evaluation', 'scikit-learn', 'deep learning'],
        'frontend engineer': ['html', 'css', 'javascript', 'react', 'tailwind css', 'typescript', 'git', 'responsive design', 'web accessibility'],
        'full stack developer': ['html', 'css', 'javascript', 'typescript', 'react', 'node.js', 'express', 'rest apis', 'sql', 'databases', 'git', 'authentication', 'deployment', 'testing'],
        'backend engineer': ['python', 'flask', 'sql', 'postgresql', 'rest apis', 'docker', 'git', 'redis', 'databases', 'api design'],
        'cybersecurity engineer': ['networking', 'linux', 'operating systems', 'python', 'security fundamentals', 'cryptography', 'vulnerability assessment', 'penetration testing', 'siem', 'incident response', 'security tools'],
        'devops engineer': ['linux', 'docker', 'kubernetes', 'ci/cd', 'aws', 'terraform', 'git', 'bash', 'infrastructure', 'monitoring'],
        'software tester': ['testing frameworks', 'test automation', 'python', 'javascript', 'selenium', 'jest', 'git', 'bug tracking', 'agile', 'performance testing'],
        'data analyst': ['sql', 'python', 'excel', 'data visualization', 'statistics', 'pandas', 'tableau', 'power bi', 'git', 'communication'],
        'machine learning engineer': ['python', 'statistics', 'probability', 'sql', 'pandas', 'numpy', 'machine learning', 'feature engineering', 'model evaluation', 'scikit-learn', 'deep learning', 'mlops'],
        'data engineer': ['python', 'sql', 'data pipelines', 'databases', 'cloud', 'testing', 'git', 'spark', 'data modeling'],
        'ai engineer': ['python', 'machine learning', 'deep learning', 'data pipelines', 'model evaluation', 'cloud', 'git'],
    }
    ROLE_ALIASES = {
        'frontend developer': 'frontend engineer',
        'front end developer': 'frontend engineer',
        'front end engineer': 'frontend engineer',
        'full stack engineer': 'full stack developer',
        'fullstack developer': 'full stack developer',
        'fullstack engineer': 'full stack developer',
        'qa engineer': 'software tester',
        'qa tester': 'software tester',
        'test automation engineer': 'software tester',
    }

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

    @staticmethod
    def _valid_http_url(url):
        if not isinstance(url, str):
            return False
        parsed = urlparse(url)
        return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)

    @staticmethod
    def _clean_skill_name(value):
        if not isinstance(value, str):
            return ''
        cleaned = value.strip()
        return re.sub(r'\s+', ' ', cleaned)

    @classmethod
    def normalize_skill_name(cls, value):
        skill = cls._clean_skill_name(value).lower()
        aliases = {
            'js': 'javascript', 'reactjs': 'react', 'react.js': 'react',
            'nodejs': 'node.js', 'node': 'node.js', 'ml': 'machine learning',
            'dl': 'deep learning', 'postgres': 'postgresql', 'html5': 'html',
            'css3': 'css', 'ts': 'typescript', 'rest': 'rest apis',
            'rest api': 'rest apis', 'apis': 'rest apis', 'sklearn': 'scikit-learn',
            'scikit learn': 'scikit-learn',
        }
        return aliases.get(skill, skill)

    @classmethod
    def skills_match(cls, first, second):
        first_key = cls.normalize_skill_name(first)
        second_key = cls.normalize_skill_name(second)
        if not first_key or not second_key:
            return False
        if first_key == second_key:
            return True
        return {first_key, second_key} <= {'sql', 'postgresql'}

    @classmethod
    def normalize_role_name(cls, career_goal):
        role = re.sub(r'[^a-z0-9]+', ' ', (career_goal or '').lower()).strip()
        role = re.sub(r'\s+', ' ', role)
        return cls.ROLE_ALIASES.get(role, role)

    @classmethod
    def get_role_required_skills(cls, career_goal, current_skills=None):
        role = cls.normalize_role_name(career_goal)
        skills = cls.ROLE_SKILLS_MAP.get(role)
        if skills is None:
            skills = cls._build_dynamic_required_skills(career_goal, current_skills or [])
        return list(dict.fromkeys(cls.normalize_skill_name(skill) for skill in skills if skill))

    @classmethod
    def _build_skill_topics(cls, skill_name):
        skill = cls._clean_skill_name(skill_name).lower()
        topic_map = {
            'python': ['syntax and data types', 'functions and modules', 'testing and debugging'],
            'javascript': ['variables and functions', 'async programming', 'DOM and browser APIs'],
            'html': ['semantic layout', 'forms and accessibility', 'content structure'],
            'css': ['layout and responsiveness', 'styling systems', 'modern design patterns'],
            'react': ['components and props', 'state management', 'rendering patterns'],
            'sql': ['queries and joins', 'schema design', 'data filtering and aggregation'],
            'git': ['commits and branches', 'merges and conflicts', 'collaborative workflows'],
            'docker': ['containers', 'docker images', 'deployment workflows'],
            'kubernetes': ['pods and services', 'deployments', 'scaling and health checks'],
            'linux': ['filesystem navigation', 'process management', 'shell scripting'],
            'aws': ['core services', 'identity and security', 'deployment patterns'],
            'machine learning': ['feature engineering', 'model training', 'evaluation and tuning'],
            'statistics': ['probability', 'sampling', 'data interpretation'],
            'rest apis': ['HTTP methods', 'resource design', 'authentication and security'],
            'cybersecurity': ['threat modeling', 'identity controls', 'incident response'],
            'testing': ['test design', 'automation', 'quality gates'],
            'debugging': ['root cause analysis', 'logging', 'fault isolation'],
            'communication': ['stakeholder updates', 'documentation', 'clear technical explanation'],
            'problem solving': ['decomposition', 'tradeoff analysis', 'debugging strategies'],
        }
        return topic_map.get(skill, [f'core concepts for {skill}', f'practical application of {skill}', f'best practices for {skill}'])

    @classmethod
    def _fallback_resource_for_skill(cls, skill_name, career_goal='career goal'):
        skill = cls._clean_skill_name(skill_name)
        normalized = skill.lower()
        url = cls.SKILL_RESOURCE_MAP.get(normalized, 'https://www.google.com/search?q=' + skill.replace(' ', '+'))
        return {
            'title': f'Learn {skill}',
            'name': f'Learn {skill}',
            'provider': 'Official Resource',
            'type': 'Documentation',
            'url': url,
            'skills': [skill],
            'level': 'beginner',
            'duration': '8h',
            'prerequisites': []
        }

    @classmethod
    def _sanitize_resource_list(cls, resource_list, skill_name, career_goal):
        if not isinstance(resource_list, list):
            resource_list = []

        sanitized = []
        for resource in resource_list:
            if not isinstance(resource, dict):
                continue
            cleaned = dict(resource)
            url = cleaned.get('url') or cleaned.get('link')
            if not cls._valid_http_url(url):
                cleaned['url'] = cls._fallback_resource_for_skill(skill_name, career_goal)['url']
            cleaned['title'] = cleaned.get('title') or cleaned.get('name') or f'Learn {skill_name}'
            cleaned['name'] = cleaned.get('name') or cleaned['title']
            cleaned['provider'] = cleaned.get('provider') or cleaned.get('type') or 'Official Resource'
            cleaned['type'] = cleaned.get('type') or cleaned['provider']
            resource_skills = cleaned.get('skills') or [skill_name]
            if isinstance(resource_skills, str):
                resource_skills = [resource_skills]
            cleaned['skills'] = resource_skills
            cleaned['level'] = cleaned.get('level') or 'beginner'
            cleaned['duration'] = cleaned.get('duration') or '8h'
            prerequisites = cleaned.get('prerequisites') or []
            cleaned['prerequisites'] = [prerequisites] if isinstance(prerequisites, str) else prerequisites
            sanitized.append(cleaned)

        if not sanitized:
            sanitized.append(cls._fallback_resource_for_skill(skill_name, career_goal))

        return sanitized[:3]

    @classmethod
    def _sanitize_roadmap_result(cls, payload):
        if not isinstance(payload, dict):
            return payload

        cleaned = dict(payload)
        roadmap = cleaned.get('roadmap')
        if not isinstance(roadmap, list):
            return cleaned

        sanitized_steps = []
        for index, step in enumerate(roadmap):
            if not isinstance(step, dict):
                continue

            skills_covered = step.get('skills_covered') or []
            if not isinstance(skills_covered, list) or not skills_covered:
                skills_covered = [f'Skill {index + 1}']

            normalized_skills = [cls._clean_skill_name(s) for s in skills_covered if cls._clean_skill_name(s)]
            primary_skill = normalized_skills[0] if normalized_skills else f'Skill {index + 1}'

            resources = step.get('external_resources', [])
            if not isinstance(resources, list):
                resources = []

            cleaned_resources = []
            for skill_name in normalized_skills:
                skill_matches = [
                    item for item in resources
                    if isinstance(item, dict) and any(cls._clean_skill_name(s).lower() == skill_name.lower() for s in item.get('skills', []) if isinstance(s, str))
                ]
                if skill_matches:
                    cleaned_resources.extend(cls._sanitize_resource_list(skill_matches, skill_name, cleaned.get('goal', 'career goal')))
                else:
                    cleaned_resources.extend(cls._sanitize_resource_list([cls._fallback_resource_for_skill(skill_name, cleaned.get('goal', 'career goal'))], skill_name, cleaned.get('goal', 'career goal')))

            if not cleaned_resources and resources:
                cleaned_resources = cls._sanitize_resource_list(resources, primary_skill, cleaned.get('goal', 'career goal'))
            if not cleaned_resources:
                cleaned_resources = [cls._fallback_resource_for_skill(primary_skill, cleaned.get('goal', 'career goal'))]

            step['skills_covered'] = normalized_skills
            step['topics'] = step.get('topics') or cls._build_skill_topics(primary_skill)
            step['title'] = step.get('title') or f'Learn {primary_skill}'
            step['description'] = step.get('description') or f'Build capability in {primary_skill} for {cleaned.get("goal", "your target role")}. '
            step['estimated_hours'] = step.get('estimated_hours') or 8
            step['external_resources'] = cleaned_resources[:3]
            sanitized_steps.append(step)

        cleaned['roadmap'] = sanitized_steps
        cleaned['skills_missing'] = [cls._clean_skill_name(s) for s in cleaned.get('skills_missing', []) if cls._clean_skill_name(s)]
        cleaned['skills_matched'] = [cls._clean_skill_name(s) for s in cleaned.get('skills_matched', []) if cls._clean_skill_name(s)]
        return cleaned

    @classmethod
    def _align_roadmap_to_gaps(cls, payload, career_goal, skills_matched, skills_missing, current_skills):
        source_steps = payload.get('roadmap', []) if isinstance(payload, dict) else []
        if not isinstance(source_steps, list):
            source_steps = []

        available_skills = [cls.normalize_skill_name(skill) for skill in current_skills or [] if skill]
        aligned_steps = []
        for index, skill in enumerate(skills_missing):
            matching_steps = []
            for step in source_steps:
                if not isinstance(step, dict):
                    continue
                covered_skills = step.get('skills_covered', [])
                if isinstance(covered_skills, str):
                    covered_skills = [covered_skills]
                if any(cls.skills_match(covered, skill) for covered in covered_skills if isinstance(covered, str)):
                    matching_steps.append(step)
            resources = []
            for step in matching_steps:
                step_resources = step.get('external_resources', [])
                if not isinstance(step_resources, list):
                    continue
                for resource in step_resources:
                    if not isinstance(resource, dict):
                        continue
                    resource_skills = resource.get('skills', [])
                    if isinstance(resource_skills, str):
                        resource_skills = [resource_skills]
                    if not any(cls.skills_match(covered, skill) for covered in resource_skills if isinstance(covered, str)):
                        continue
                    prerequisites = resource.get('prerequisites', [])
                    if isinstance(prerequisites, str):
                        prerequisites = [prerequisites]
                    if not isinstance(prerequisites, list):
                        prerequisites = []
                    prerequisites_met = all(
                        any(cls.skills_match(known, prerequisite) for known in available_skills)
                        for prerequisite in prerequisites
                    )
                    if prerequisites_met:
                        resources.append(resource)

            step_source = matching_steps[0] if matching_steps else {}
            resource_list = cls._sanitize_resource_list(resources, skill, career_goal)
            try:
                estimated_hours = max(1, int(step_source.get('estimated_hours', 8)))
            except (TypeError, ValueError):
                estimated_hours = 8

            aligned_steps.append({
                'step_key': f'step_{index + 1}_{re.sub(r"[^a-z0-9]+", "_", skill.lower()).strip("_")}',
                'title': step_source.get('title') or f'Learn {skill.title()}',
                'description': step_source.get('description') or f'Build proficiency in {skill} for {career_goal}.',
                'estimated_hours': estimated_hours,
                'skills_covered': [skill],
                'topics': step_source.get('topics') or cls._build_skill_topics(skill),
                'external_resources': resource_list,
            })
            available_skills.append(cls.normalize_skill_name(skill))

        return {
            'goal': career_goal,
            'skills_matched': skills_matched,
            'skills_missing': skills_missing,
            'roadmap': aligned_steps,
        }

    @classmethod
    def _build_dynamic_required_skills(cls, career_goal, current_skills):
        role = cls.normalize_role_name(career_goal)

        templates = {
            'frontend': ['html', 'css', 'javascript', 'react', 'accessibility', 'git'],
            'backend': ['python', 'sql', 'rest apis', 'databases', 'git', 'docker'],
            'full stack': ['html', 'css', 'javascript', 'react', 'python', 'rest apis', 'sql', 'docker'],
            'data scientist': ['python', 'sql', 'statistics', 'pandas', 'machine learning', 'data visualization', 'git'],
            'data analyst': ['sql', 'python', 'statistics', 'data visualization', 'excel', 'communication'],
            'data engineer': ['python', 'sql', 'data pipelines', 'databases', 'cloud', 'testing', 'git'],
            'devops': ['linux', 'docker', 'kubernetes', 'ci/cd', 'cloud', 'git', 'bash'],
            'cybersecurity': ['linux', 'security', 'networking', 'cryptography', 'incident response', 'testing'],
            'site reliability': ['linux', 'cloud', 'docker', 'kubernetes', 'monitoring', 'observability', 'incident response', 'git'],
            'reliability engineer': ['linux', 'cloud', 'docker', 'kubernetes', 'monitoring', 'observability', 'incident response', 'git'],
            'software tester': ['testing', 'quality assurance', 'automation', 'git', 'debugging', 'api'],
            'machine learning': ['python', 'statistics', 'pandas', 'machine learning', 'model evaluation', 'data visualization', 'git'],
            'ai engineer': ['python', 'machine learning', 'data pipelines', 'model evaluation', 'cloud', 'git'],
            'cloud': ['linux', 'docker', 'cloud', 'security', 'ci/cd', 'terraform', 'git'],
            'product': ['communication', 'problem solving', 'analytics', 'testing', 'stakeholder management'],
        }

        selected = []
        for keyword, skills in templates.items():
            if keyword in role:
                selected.extend(skills)

        if not selected:
            selected = ['programming fundamentals', 'debugging', 'version control', 'testing', 'cloud fundamentals', 'communication', 'problem solving']

        if 'engineer' in role or 'developer' in role or 'analyst' in role or 'specialist' in role:
            selected.extend(['problem solving', 'communication', 'debugging'])

        return list(dict.fromkeys(cls.normalize_skill_name(skill) for skill in selected))

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
            data = json.loads(text_response)
            return self._sanitize_roadmap_result(data) if isinstance(data, dict) and 'roadmap' in data else data
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
                data = json.loads(text_response)
                return self._sanitize_roadmap_result(data) if isinstance(data, dict) and 'roadmap' in data else data
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
        """
        Generate a gap analysis and learning roadmap for the user's target career goal.
        Supports both Gemini API and deterministic fallback modes.
        """
        # Comprehensive course catalog (used in fallback when Gemini unavailable)
        COURSE_CATALOG = {
            'python': [
                {'title': 'Python for Everybody', 'provider': 'Coursera', 'url': 'https://www.coursera.org/specializations/python', 'skills': ['python'], 'level': 'beginner', 'duration': '40h', 'prerequisites': []},
                {'title': 'Intermediate Python', 'provider': 'Real Python', 'url': 'https://realpython.com', 'skills': ['python'], 'level': 'intermediate', 'duration': '20h', 'prerequisites': ['python']}
            ],
            'javascript': [
                {'title': 'JavaScript Basics', 'provider': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide', 'skills': ['javascript'], 'level': 'beginner', 'duration': '30h', 'prerequisites': []},
                {'title': 'Modern JavaScript (ES6+)', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/the-complete-javascript-course', 'skills': ['javascript', 'typescript'], 'level': 'intermediate', 'duration': '40h', 'prerequisites': ['javascript']}
            ],
            'html': [
                {'title': 'HTML & CSS Complete Guide', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/html-css-complete-course', 'skills': ['html', 'css'], 'level': 'beginner', 'duration': '20h', 'prerequisites': []}
            ],
            'css': [
                {'title': 'Advanced CSS', 'provider': 'CSS Tricks', 'url': 'https://css-tricks.com', 'skills': ['css', 'responsive design'], 'level': 'intermediate', 'duration': '15h', 'prerequisites': ['html']}
            ],
            'react': [
                {'title': 'React - The Complete Guide', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/react-the-complete-guide', 'skills': ['react', 'javascript'], 'level': 'beginner', 'duration': '30h', 'prerequisites': ['javascript']}
            ],
            'node.js': [
                {'title': 'Node.js, Express, MongoDB & More', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/nodejs-express-mongodb-bootcamp', 'skills': ['node.js', 'express'], 'level': 'beginner', 'duration': '25h', 'prerequisites': ['javascript']}
            ],
            'express': [
                {'title': 'Express.js Tutorial', 'provider': 'Express', 'url': 'https://expressjs.com', 'skills': ['express', 'node.js'], 'level': 'beginner', 'duration': '15h', 'prerequisites': ['node.js']}
            ],
            'sql': [
                {'title': 'SQL for Data Science', 'provider': 'Coursera', 'url': 'https://www.coursera.org/learn/sql-for-data-science', 'skills': ['sql'], 'level': 'beginner', 'duration': '15h', 'prerequisites': []}
            ],
            'postgresql': [
                {'title': 'PostgreSQL Bootcamp', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/postgresql-bootcamp', 'skills': ['postgresql', 'sql', 'databases'], 'level': 'beginner', 'duration': '20h', 'prerequisites': ['sql']}
            ],
            'docker': [
                {'title': 'Docker for Developers', 'provider': 'Pluralsight', 'url': 'https://www.pluralsight.com/courses/docker', 'skills': ['docker'], 'level': 'beginner', 'duration': '8h', 'prerequisites': []}
            ],
            'kubernetes': [
                {'title': 'Kubernetes Complete Course', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/kubernetes-complete-guide', 'skills': ['kubernetes'], 'level': 'intermediate', 'duration': '20h', 'prerequisites': ['docker']}
            ],
            'statistics': [
                {'title': 'Intro to Statistics', 'provider': 'Khan Academy', 'url': 'https://www.khanacademy.org/math/statistics-probability', 'skills': ['statistics'], 'level': 'beginner', 'duration': '20h', 'prerequisites': []}
            ],
            'pandas': [
                {'title': 'Data Analysis with Python', 'provider': 'freeCodeCamp', 'url': 'https://www.freecodecamp.org/news/data-analysis-with-python/', 'skills': ['pandas', 'numpy', 'python'], 'level': 'beginner', 'duration': '10h', 'prerequisites': ['python']}
            ],
            'machine learning': [
                {'title': 'Machine Learning', 'provider': 'Coursera (Andrew Ng)', 'url': 'https://www.coursera.org/learn/machine-learning', 'skills': ['machine learning'], 'level': 'beginner', 'duration': '55h', 'prerequisites': ['python', 'statistics']}
            ],
            'git': [
                {'title': 'Git & GitHub Complete Guide', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/git-github', 'skills': ['git'], 'level': 'beginner', 'duration': '8h', 'prerequisites': []}
            ],
            'linux': [
                {'title': 'Linux Command Line Basics', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/linux-command-line', 'skills': ['linux', 'bash'], 'level': 'beginner', 'duration': '12h', 'prerequisites': []}
            ],
            'testing frameworks': [
                {'title': 'Jest Testing Framework', 'provider': 'Udemy', 'url': 'https://www.udemy.com/course/jest-testing', 'skills': ['jest', 'testing frameworks'], 'level': 'beginner', 'duration': '10h', 'prerequisites': ['javascript']}
            ]
        }

        # Determine required skills for the selected goal.
        required_skills = self.get_role_required_skills(career_goal, current_skills)

        # Normalize current and required skills
        normalized_user_skills = [self.normalize_skill_name(skill) for skill in current_skills or [] if skill]
        normalized_required = [self.normalize_skill_name(skill) for skill in required_skills]
        
        # Compute matched and missing skills
        skills_matched = [
            required for required in normalized_required
            if any(self.skills_match(current, required) for current in normalized_user_skills)
        ]
        skills_missing = [
            required for required in normalized_required
            if not any(self.skills_match(current, required) for current in normalized_user_skills)
        ]

        # If Gemini API is unavailable, use deterministic fallback
        if not self.initialized:
            roadmap = []
            step_index = 1
            for missing_skill in skills_missing:
                skill_key = self.normalize_skill_name(missing_skill)
                courses = COURSE_CATALOG.get(skill_key, [])
                external_resources = []
                if courses:
                    external_resources = [
                        {
                            **course,
                            'name': course.get('title'),
                            'type': course.get('provider'),
                            'url': course.get('url') if self._valid_http_url(course.get('url')) else self._fallback_resource_for_skill(skill_key, career_goal)['url']
                        }
                        for course in courses[:3]
                    ]
                else:
                    external_resources = [self._fallback_resource_for_skill(skill_key, career_goal)]

                total_hours = 0
                for resource in external_resources:
                    duration = str(resource.get('duration', '8h'))
                    try:
                        total_hours += int(duration.rstrip('h').strip())
                    except Exception:
                        total_hours += 8
                total_hours = max(total_hours, 8)

                step = {
                    'step_key': f'step_{step_index}_{missing_skill.replace(" ", "_")}',
                    'title': f'Master {missing_skill.title()}',
                    'description': f'Build proficiency in {missing_skill} to become a competitive {career_goal}.',
                    'estimated_hours': total_hours,
                    'skills_covered': [missing_skill],
                    'topics': self._build_skill_topics(missing_skill),
                    'external_resources': external_resources
                }
                roadmap.append(step)
                step_index += 1

            result = {
                'goal': career_goal,
                'skills_matched': skills_matched,
                'skills_missing': skills_missing,
                'roadmap': roadmap
            }
            aligned = self._align_roadmap_to_gaps(result, career_goal, skills_matched, skills_missing, current_skills)
            return self._sanitize_roadmap_result(aligned)

        # Gemini API path: use role-specific prompt
        required_skills_str = ', '.join(required_skills)
        skills_str = ", ".join(current_skills) if current_skills else "None listed"
        
        prompt = f"""You are an expert career advisor specialized in {career_goal}.

TARGET ROLE: {career_goal}
REQUIRED CORE SKILLS FOR THIS ROLE: {required_skills_str}
USER'S CURRENT SKILLS: {skills_str}

TASK:
1. Compare the user's current skills against the required skills for {career_goal}.
2. Identify which current skills are MATCHED to the role.
3. Identify which skills are MISSING.
4. Create a 3-6 step learning roadmap that ONLY focuses on the missing skills.
5. For each step, recommend specific courses/resources that teach the missing skills.
6. Ensure all recommendations are SPECIFIC to {career_goal}, not generic.

IMPORTANT: Do not recommend resources for skills the user already has.
Focus entirely on bridging the skill gaps identified above.

Return ONLY a valid JSON object in this format:
{{
  "goal": "{career_goal}",
  "skills_matched": ["SkillA", "SkillB"],
  "skills_missing": ["SkillX", "SkillY"],
  "roadmap": [
    {{
      "step_key": "step_1_skillname",
      "title": "Learn [SkillName]",
      "description": "Focus on mastering [SkillName] required for {career_goal}",
      "estimated_hours": 20,
      "skills_covered": ["SkillName"],
      "topics": ["Topic1", "Topic2"],
      "external_resources": [
        {{
          "title": "Course Name",
          "provider": "Provider Name",
          "url": "https://example.com",
          "skills": ["SkillName"],
          "level": "beginner",
          "duration": "20h",
          "prerequisites": []
        }}
      ]
    }}
  ]
}}
"""

        # Create fallback with role-specific data
        fallback = {
            'goal': career_goal,
            'skills_matched': skills_matched,
            'skills_missing': skills_missing,
            'roadmap': [
                {
                    'step_key': f'step_1_{s.replace(" ", "_")}',
                    'title': f'Learn {s.title()}',
                    'description': f'Build proficiency in {s} for {career_goal}.',
                    'estimated_hours': max(sum([int(c.get('duration', '10h').rstrip('h')) for c in COURSE_CATALOG.get(s, [])]), 8) or 10,
                    'skills_covered': [s],
                    'topics': self._build_skill_topics(s),
                    'external_resources': [
                        {
                            **(COURSE_CATALOG.get(s, [{}])[0] if COURSE_CATALOG.get(s) else {}),
                            'title': (COURSE_CATALOG.get(s, [{}])[0].get('title') if COURSE_CATALOG.get(s) else f'{s.title()} Fundamentals'),
                            'provider': (COURSE_CATALOG.get(s, [{}])[0].get('provider') if COURSE_CATALOG.get(s) else 'Official Resource'),
                            'name': (COURSE_CATALOG.get(s, [{}])[0].get('title') if COURSE_CATALOG.get(s) else f'{s.title()} Fundamentals'),
                            'type': (COURSE_CATALOG.get(s, [{}])[0].get('provider') if COURSE_CATALOG.get(s) else 'Official Resource'),
                            'url': (COURSE_CATALOG.get(s, [{}])[0].get('url') if COURSE_CATALOG.get(s) and self._valid_http_url(COURSE_CATALOG.get(s, [{}])[0].get('url')) else self._fallback_resource_for_skill(s, career_goal)['url']),
                            'skills': [s],
                            'level': 'beginner',
                            'duration': '8h',
                            'prerequisites': []
                        }
                    ]
                }
                for i, s in enumerate(skills_missing, 1)
            ]
        }

        result = self._call_gemini_json(prompt, fallback)
        aligned = self._align_roadmap_to_gaps(result, career_goal, skills_matched, skills_missing, current_skills)
        return self._sanitize_roadmap_result(aligned)

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
        topics = topics if isinstance(topics, list) else []
        topics = [str(topic).strip() for topic in topics if str(topic).strip()]
        topics_str = ", ".join(topics)
        prompt = f"""
        You are a technical educator. Write a detailed, role-relevant in-platform lesson on "{step_title}".
        Cover these topics: {topics_str}.
        Include an introduction, core concepts, a step-by-step walkthrough, a runnable code example when appropriate,
        a practical task with acceptance criteria, a portfolio project with deliverables, and a Quick Check.
        Return ONLY valid JSON with keys: title, content_markdown, summary.
        """

        topic_bullets = "\n".join(f"* {topic}" for topic in topics) or "* foundational concepts"
        concept_sections = "\n\n".join(
            f"### {topic.title()}\nUnderstand the purpose of {topic}, when it is useful, and which failure mode or tradeoff to watch for."
            for topic in topics
        ) or "### Foundations\nConnect the terminology to a small implementation and verify its behavior."

        fallback = {
            "title": step_title,
            "summary": f"A practical lesson on {step_title} covering {topics_str}, followed by an implementation task and portfolio project.",
            "content_markdown": f"""# Learning {step_title}

This module builds working knowledge of **{step_title}** through concepts, implementation, and verification. It covers:
{topic_bullets}

## Introduction
{step_title} is valuable because it helps engineers design, operate, and improve dependable systems. The goal is not to memorize terminology; it is to apply the ideas to a small, testable outcome.

## Core Concepts
{concept_sections}

## Step-by-Step Walkthrough
1. Define the outcome and the inputs your implementation must handle.
2. Build the smallest working version using the concepts above.
3. Add one failure path and make the behavior observable with a log, test, or command.
4. Review the tradeoffs and document what you would change at production scale.

## Code Example
The example below shows a small validation workflow that can be adapted to this module's concepts:

```python
def validate_learning_result(result):
    if not result or not result.get("status"):
        raise ValueError("A completed result must include a status")
    return {{"status": result["status"], "verified": True}}

print(validate_learning_result({{"status": "complete"}}))
```

## Practical Task
Build a small working example related to **{step_title}** using at least two of the topics above.

Acceptance criteria:
* The example runs locally with clear setup instructions.
* It handles one invalid input or failure case.
* It includes a short README explaining the design decision and tradeoff.
* You can demonstrate the result with a test, command output, or screenshot.

## Portfolio Project
Create a focused **{step_title} practice project** that solves one realistic problem in your target role. Deliver a working implementation, a diagram or architecture note, automated checks where appropriate, and a short reflection describing what you would improve in production.

## Quick Check
1. Can you explain the purpose of each topic without relying on a definition?
2. Can you implement the smallest useful version and test a failure case?
3. Can you justify the main design choice in your README?

## Core Takeaways
1. Prefer a small observable implementation over passive reading.
2. Verify behavior with tests, logs, or reproducible commands.
3. Connect each concept to a project artifact you can show.
"""
        }

        return self._call_gemini_json(prompt, fallback)
