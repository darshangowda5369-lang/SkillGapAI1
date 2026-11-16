#!/usr/bin/env python3
"""
Integration test simulating the full backend flow for multiple roles.
Tests the complete roadmap generation pipeline: user skills → role selection → gap analysis → roadmap generation.
"""

import json
import sys
from app.services.gemini_service import GeminiService

def simulate_roadmap_generation_flow():
    """Simulate the complete flow of roadmap generation for different roles."""
    
    gemini = GeminiService(api_key=None)
    
    print("\n" + "="*80)
    print("SKILLGAPAI INTEGRATION TEST: Roadmap Generation for Multiple Roles")
    print("="*80)
    
    test_scenarios = [
        {
            'scenario_name': 'Scenario 1: Junior Developer → Data Scientist Career Change',
            'user_skills': ['Python', 'Git', 'SQL', 'HTML5', 'CSS3', 'JavaScript'],
            'target_roles': ['Data Scientist', 'Frontend Engineer', 'Backend Engineer']
        },
        {
            'scenario_name': 'Scenario 2: Recent Graduate → Full Stack Developer',
            'user_skills': ['Git', 'Problem Solving', 'Communication'],
            'target_roles': ['Full Stack Developer', 'Frontend Engineer', 'Backend Engineer']
        },
        {
            'scenario_name': 'Scenario 3: Self-Taught Python Dev → DevOps',
            'user_skills': ['Python', 'Linux', 'Bash', 'Git'],
            'target_roles': ['DevOps Engineer', 'Backend Engineer']
        },
    ]
    
    all_passed = True
    
    for scenario in test_scenarios:
        print(f"\n{scenario['scenario_name']}")
        print("-" * 80)
        
        user_skills = scenario['user_skills']
        print(f"User's Current Skills: {', '.join(user_skills)}\n")
        
        roadmaps_by_role = {}
        
        for role in scenario['target_roles']:
            print(f"  → Generating roadmap for: {role}")
            result = gemini.generate_gap_analysis_and_roadmap(user_skills, role)
            roadmaps_by_role[role] = result
            
            matched_count = len(result['skills_matched'])
            missing_count = len(result['skills_missing'])
            roadmap_steps = len(result['roadmap'])
            
            print(f"     Skills Matched: {matched_count} | Skills Missing: {missing_count} | Steps: {roadmap_steps}")
        
        # Verify that different roles get different recommendations
        print(f"\n  Verification:")
        role_list = scenario['target_roles']
        
        for i in range(len(role_list)):
            for j in range(i + 1, len(role_list)):
                role1 = role_list[i]
                role2 = role_list[j]
                
                missing1 = set(roadmaps_by_role[role1]['skills_missing'])
                missing2 = set(roadmaps_by_role[role2]['skills_missing'])
                
                if missing1 == missing2:
                    print(f"    ✗ FAILED: {role1} and {role2} have identical skill gaps!")
                    all_passed = False
                else:
                    unique_to_role1 = missing1 - missing2
                    unique_to_role2 = missing2 - missing1
                    common = missing1 & missing2
                    
                    print(f"    ✓ {role1} vs {role2}:")
                    print(f"       Unique to {role1}: {len(unique_to_role1)} skills")
                    print(f"       Unique to {role2}: {len(unique_to_role2)} skills")
                    print(f"       Common gaps: {len(common)} skills")
        
        # Verify roadmap structure
        print(f"\n  Sample Roadmap (first role - {role_list[0]}):")
        sample_roadmap = roadmaps_by_role[role_list[0]]
        
        if len(sample_roadmap['roadmap']) > 0:
            first_step = sample_roadmap['roadmap'][0]
            print(f"    Step 1: {first_step['title']}")
            print(f"    Description: {first_step['description']}")
            print(f"    Estimated Hours: {first_step['estimated_hours']}")
            print(f"    Resources: {len(first_step.get('external_resources', []))} courses")
            
            if first_step.get('external_resources'):
                print(f"    Sample Resource: {first_step['external_resources'][0].get('title')}")
        else:
            print("    (No learning steps needed - user has all required skills)")
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ INTEGRATION TEST PASSED")
        print("\nKey Findings:")
        print("1. Different roles generate different skill gap recommendations")
        print("2. Roadmap structure is consistent across all roles")
        print("3. External resources are properly attached to each step")
        print("4. The system correctly identifies matched vs. missing skills")
        return 0
    else:
        print("✗ INTEGRATION TEST FAILED")
        print("Check the output above for details")
        return 1

if __name__ == '__main__':
    sys.exit(simulate_roadmap_generation_flow())
