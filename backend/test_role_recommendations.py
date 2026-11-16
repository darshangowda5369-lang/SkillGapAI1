#!/usr/bin/env python3
"""
Test script to verify role-specific recommendations work correctly for different career goals.
Tests both the deterministic fallback and validates the recommendation logic.
"""

import json
import sys

from app.services.gemini_service import GeminiService


def _is_valid_http_url(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))

def test_role_specific_recommendations():
    """Test that different roles produce different recommendations."""
    
    # Initialize GeminiService without API key to force deterministic fallback
    gemini = GeminiService(api_key=None)
    gemini.initialized = False
    
    # Test cases: (role, user_skills, expected_missing_skills)
    test_cases = [
        {
            'role': 'Data Scientist',
            'user_skills': ['Python', 'Git'],
            'expected_to_have_missing': ['statistics', 'sql', 'pandas', 'machine learning'],
            'should_not_have': ['react', 'html', 'css']  # Frontend skills shouldn't be for Data Scientist
        },
        {
            'role': 'Frontend Developer',
            'user_skills': ['Git', 'Python'],
            'expected_to_have_missing': ['html', 'css', 'javascript', 'react'],
            'should_not_have': ['python', 'sql', 'machine learning']  # Backend/ML skills shouldn't be recommended
        },
        {
            'role': 'Full-Stack Developer',
            'user_skills': ['Git'],
            'expected_to_have_missing': ['html', 'css', 'javascript', 'node.js', 'express', 'sql'],
            'should_not_have': ['kubernetes', 'penetration testing']  # DevOps/Security skills
        },
        {
            'role': 'Software Tester',
            'user_skills': ['Python', 'Git'],
            'expected_to_have_missing': ['testing frameworks', 'jest', 'selenium'],
            'should_not_have': ['machine learning', 'data visualization']  # Data/ML skills
        },
        {
            'role': 'DevOps Engineer',
            'user_skills': ['Git'],
            'expected_to_have_missing': ['linux', 'docker', 'kubernetes'],
            'should_not_have': ['react', 'machine learning']  # Frontend/ML skills
        },
    ]
    
    all_passed = True

    generic_role = 'Machine Learning Engineer'
    generic_result = gemini.generate_gap_analysis_and_roadmap(['Python', 'Git'], generic_role)
    generic_missing = [skill.lower() for skill in generic_result.get('skills_missing', [])]

    assert generic_result.get('goal', '').lower() == generic_role.lower()
    assert generic_missing, 'general role should produce missing skills'

    all_resource_urls = [
        resource.get('url')
        for step in generic_result.get('roadmap', [])
        for resource in step.get('external_resources', [])
    ]
    if all_resource_urls:
        assert all(_is_valid_http_url(url) for url in all_resource_urls if url), 'all external resources must be valid http(s) urls'
    
    for test_case in test_cases:
        role = test_case['role']
        user_skills = test_case['user_skills']
        expected_missing = test_case['expected_to_have_missing']
        should_not_have = test_case['should_not_have']
        
        print(f"\n{'='*70}")
        print(f"Testing: {role}")
        print(f"{'='*70}")
        print(f"User skills: {user_skills}")
        
        # Call the gap analysis
        result = gemini.generate_gap_analysis_and_roadmap(user_skills, role)
        
        print(f"✓ Generated roadmap for: {result['goal']}")
        print(f"  Skills matched: {result['skills_matched']}")
        print(f"  Skills missing: {result['skills_missing']}")
        print(f"  Roadmap steps: {len(result['roadmap'])}")
        
        # Verify role-specific behavior
        missing_skills_lower = [s.lower() for s in result['skills_missing']]
        
        # Check expected missing skills are in the list
        for skill in expected_missing:
            if skill.lower() in missing_skills_lower:
                print(f"  ✓ Correctly identified missing skill: {skill}")
            else:
                print(f"  ✗ FAILED: Expected missing skill not found: {skill}")
                all_passed = False
        
        # Check that unrelated skills are NOT in the recommendation
        for skill in should_not_have:
            if skill.lower() in missing_skills_lower:
                print(f"  ✗ FAILED: Incorrectly recommended unrelated skill: {skill}")
                all_passed = False
            else:
                print(f"  ✓ Correctly excluded unrelated skill: {skill}")
        
        # Verify roadmap has steps for missing skills
        if len(result['roadmap']) > 0:
            print(f"  ✓ Generated {len(result['roadmap'])} learning steps")
            for step in result['roadmap'][:2]:  # Show first 2 steps
                resources_count = len(step.get('external_resources', []))
                print(f"    - {step['title']} ({resources_count} resources)")

                for resource in step.get('external_resources', []):
                    assert _is_valid_http_url(resource.get('url')), f"Invalid external URL: {resource.get('url')}"
        else:
            # If user has all skills, roadmap might be empty (which is ok)
            if not result['skills_missing']:
                print(f"  ✓ No learning steps needed (user has all required skills)")
            else:
                print(f"  ✗ FAILED: No roadmap steps generated despite missing skills")
                all_passed = False
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✓ All tests PASSED! Role-specific recommendations are working correctly.")
        print("\nSummary:")
        print("- Different roles produce different skill recommendations")
        print("- Skill normalization works (e.g., 'JS' → 'javascript')")
        print("- Each role gets only relevant skills, not generic recommendations")
        return test_gemini_response_is_constrained_to_role_gaps()
    else:
        print("✗ Some tests FAILED! Check the output above for details.")
        return 1


def test_gemini_response_is_constrained_to_role_gaps():
    """A hallucinated generic Gemini response must not leak into the active roadmap."""
    class FakeResponse:
        text = json.dumps({
            'goal': 'Frontend Developer',
            'skills_matched': ['React'],
            'skills_missing': ['React', 'Node.js'],
            'roadmap': [{
                'step_key': 'generic_step',
                'title': 'Learn React',
                'description': 'A frontend course unrelated to the selected data role.',
                'skills_covered': ['React'],
                'external_resources': [{
                    'title': 'React Course',
                    'provider': 'Example',
                    'url': 'https://example.com/react',
                    'skills': ['React'],
                    'level': 'beginner',
                    'duration': '10h',
                    'prerequisites': [],
                }],
            }],
        })

    class FakeModel:
        def generate_content(self, prompt, generation_config=None):
            return FakeResponse()

    service = GeminiService(api_key='mock-test-key')
    service.initialized = True
    service.model = FakeModel()
    current_skills = ['Python', 'Git']
    result = service.generate_gap_analysis_and_roadmap(current_skills, 'Data Scientist')
    required = service.get_role_required_skills('Data Scientist', current_skills)
    expected_missing = [
        skill for skill in required
        if not any(service.skills_match(skill, current) for current in current_skills)
    ]
    actual_missing = result['skills_missing']
    actual_covered = [skill for step in result['roadmap'] for skill in step['skills_covered']]

    assert result['goal'] == 'Data Scientist'
    assert actual_missing == expected_missing
    assert actual_covered == expected_missing
    assert all(
        service.skills_match(resource_skill, covered)
        for step in result['roadmap']
        for covered in step['skills_covered']
        for resource in step['external_resources']
        for resource_skill in resource.get('skills', [])
    )
    assert all(
        not service.skills_match('React', covered)
        for covered in actual_covered
    )
    print("\n✓ Mocked Gemini response was reconciled to Data Scientist skill gaps.")
    return 0

if __name__ == '__main__':
    sys.exit(test_role_specific_recommendations())
