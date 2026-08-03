import json
from app.models import Progress, Quiz, Goal, Roadmap

class CareerReadinessAnalyzer:
    @staticmethod
    def calculate_readiness_score(user_id, active_goal_id):
        """
        Calculates the Career Readiness Score for a user based on:
        1. Base skill match percentage (60% weight)
        2. Roadmap progress (30% weight)
        3. Quiz performance (10% weight)
        
        Returns a float between 0.0 and 100.0.
        """
        goal = Goal.query.filter_by(id=active_goal_id, user_id=user_id).first()
        if not goal:
            return 0.0

        try:
            req_skills = json.loads(goal.required_skills) if goal.required_skills else []
        except Exception:
            req_skills = []

        if not req_skills:
            return 0.0

        # 1. Fetch user's uploaded resume skills
        from app.models import Resume
        latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
        user_skills = []
        if latest_resume and latest_resume.extracted_skills:
            try:
                user_skills = json.loads(latest_resume.extracted_skills)
            except Exception:
                user_skills = []

        user_skills_set = set(s.lower() for s in user_skills)
        matched_count = sum(1 for s in req_skills if s.lower() in user_skills_set)
        total_skills_count = len(req_skills)
        
        # Base Match Score (out of 100)
        base_match_score = (matched_count / total_skills_count) * 100.0 if total_skills_count > 0 else 0.0

        # 2. Roadmap progress
        roadmap = Roadmap.query.filter_by(goal_id=active_goal_id, user_id=user_id).first()
        progress_score = 0.0
        if roadmap:
            try:
                steps_data = json.loads(roadmap.steps)
                steps_list = steps_data.get('roadmap', [])
            except Exception:
                steps_list = []

            total_steps = len(steps_list)
            if total_steps > 0:
                completed_steps = Progress.query.filter_by(
                    user_id=user_id, 
                    roadmap_id=roadmap.id, 
                    is_completed=True
                ).count()
                progress_score = (completed_steps / total_steps) * 100.0

        # 3. Quiz score
        completed_quizzes = Quiz.query.filter_by(user_id=user_id).filter(Quiz.score.isnot(None)).all()
        quiz_score = 100.0  # default to 100 if no quizzes completed, or 0? Let's use 0.0 if no quizzes, and average score if there are quizzes
        if completed_quizzes:
            total_quiz_score = sum(q.score for q in completed_quizzes)
            quiz_score = total_quiz_score / len(completed_quizzes)
        else:
            quiz_score = 0.0

        # Weighted calculation
        # 60% Skills Match + 30% Progress + 10% Quizzes
        final_score = (base_match_score * 0.6) + (progress_score * 0.3) + (quiz_score * 0.1)

        # If the roadmap is fully complete, keep the reported readiness at 100.0
        # so the dashboard and certificate unlock flow consistently resolve to full completion.
        if progress_score >= 100.0:
            return 100.0

        # If user has 100% skills matched and 100% roadmap done, score should be 100% even without quizzes
        # Let's caps score to 100.0 and round to 1 decimal place
        return round(min(max(final_score, 0.0), 100.0), 1)
