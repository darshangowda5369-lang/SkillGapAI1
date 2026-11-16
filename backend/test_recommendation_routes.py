import json
import os
import unittest
from unittest.mock import patch

from app import create_app
from app.config import Config
from app.database import db
from app.models import Resume, User
from app.services.gemini_service import GeminiService


class RecommendationRouteTests(unittest.TestCase):
    def setUp(self):
        self.api_key_patch = patch.dict(os.environ, {'GEMINI_API_KEY': ''})
        self.api_key_patch.start()

        class TestConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = 'sqlite://'

        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

        self.token = 'recommendation-test-token'
        user = User(
            username='recommendationtester',
            email='recommendation@example.com',
            session_token=self.token,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(Resume(
            user_id=user.id,
            filename='resume.txt',
            raw_text='Frontend and backend experience',
            extracted_skills=json.dumps(['JS', 'ReactJS', 'NodeJS', 'PostgreSQL', 'Git']),
        ))
        db.session.commit()
        self.client = self.app.test_client()
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.api_key_patch.stop()

    def test_generate_and_active_routes_keep_role_specific_gaps(self):
        roles = [
            'Data Scientist',
            'Frontend Developer',
            'Full-Stack Developer',
            'Software Tester',
        ]
        role_gap_sets = []

        for role in roles:
            response = self.client.post(
                '/api/roadmap/generate',
                json={'goal_title': role},
                headers=self.headers,
            )
            self.assertEqual(response.status_code, 200, response.get_json())
            generated = response.get_json()['data']
            role_gap_sets.append(tuple(generated['skills_missing']))

            required = GeminiService.get_role_required_skills(role, ['JS', 'ReactJS', 'NodeJS', 'PostgreSQL', 'Git'])
            expected_missing = [
                skill for skill in required
                if not any(GeminiService.skills_match(skill, current) for current in ['JS', 'ReactJS', 'NodeJS', 'PostgreSQL', 'Git'])
            ]
            self.assertEqual(generated['skills_missing'], expected_missing)
            self.assertEqual(
                [skill for step in generated['roadmap'] for skill in step['skills_covered']],
                expected_missing,
            )
            learned_skills = ['JS', 'ReactJS', 'NodeJS', 'PostgreSQL', 'Git']
            for step in generated['roadmap']:
                self.assertTrue(step['external_resources'])
                for resource in step['external_resources']:
                    self.assertTrue(resource.get('provider'))
                    self.assertTrue(resource.get('level'))
                    self.assertTrue(resource.get('duration'))
                    self.assertIsInstance(resource.get('prerequisites'), list)
                    self.assertTrue(any(
                        GeminiService.skills_match(resource_skill, step['skills_covered'][0])
                        for resource_skill in resource.get('skills', [])
                    ))
                    for prerequisite in resource['prerequisites']:
                        self.assertTrue(any(
                            GeminiService.skills_match(prerequisite, learned)
                            for learned in learned_skills
                        ))
                learned_skills.extend(step['skills_covered'])

            active_response = self.client.get('/api/roadmap/active', headers=self.headers)
            self.assertEqual(active_response.status_code, 200, active_response.get_json())
            active = active_response.get_json()['data']
            self.assertEqual(active['goal_title'], role)
            self.assertEqual(active['skills_missing'], expected_missing)
            self.assertEqual(
                [skill for step in active['roadmap'] for skill in step['skills_covered']],
                expected_missing,
            )

        self.assertEqual(len(set(role_gap_sets)), len(roles))


if __name__ == '__main__':
    unittest.main()
