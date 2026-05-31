import React, { useEffect, useState } from 'react';
import { quizAPI, progressAPI } from '../services/api';
import { HelpCircle, ChevronRight, Check, X, ShieldAlert, Award, RefreshCw, Cpu } from 'lucide-react';

export default function QuizView({ sharedState, setActivePage }) {
  const targetSkill = sharedState?.activeQuizSkill || '';
  
  const [availableSkills, setAvailableSkills] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(targetSkill);
  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [answers, setAnswers] = useState({}); // {question_id: selected_letter}
  const [currentIdx, setCurrentIdx] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    // If no specific skill gap was selected, fetch all missing skills from stats to let them choose
    const fetchAvailableGaps = async () => {
      try {
        const res = await progressAPI.getStats();
        if (res.status === 'success' && res.data?.skills_missing) {
          setAvailableSkills(res.data.skills_missing);
          if (!targetSkill && res.data.skills_missing.length > 0) {
            setSelectedSkill(res.data.skills_missing[0]);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };
    
    if (!targetSkill) {
      fetchAvailableGaps();
    }
  }, [targetSkill]);

  const handleStartQuiz = async (skillName) => {
    if (!skillName) return;
    
    try {
      setLoading(true);
      setErrorMsg('');
      setResults(null);
      setAnswers({});
      setCurrentIdx(0);
      
      const res = await quizAPI.generate(skillName);
      if (res.status === 'success') {
        setQuizData(res.data);
      } else {
        throw new Error(res.message || 'Failed to generate quiz questions');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.message || err.message || 'Error communicating with AI engine.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (targetSkill) {
      handleStartQuiz(targetSkill);
    }
  }, [targetSkill]);

  const handleSelectOption = (qId, optionLetter) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: optionLetter
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!quizData?.quiz_id) return;
    
    // Validate all answered
    const totalQCount = quizData.questions?.length || 0;
    const answeredCount = Object.keys(answers).length;
    if (answeredCount < totalQCount) {
      setErrorMsg('Please answer all questions before submitting.');
      return;
    }
    
    try {
      setSubmitting(true);
      setErrorMsg('');
      const res = await quizAPI.submit(quizData.quiz_id, answers);
      if (res.status === 'success') {
        setResults(res.data);
      } else {
        throw new Error(res.message || 'Submission evaluation failed');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to process quiz answers.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <Cpu className="w-12 h-12 text-cyber-purple animate-spin" />
        <p className="text-gray-400 font-mono tracking-widest text-sm uppercase">Synthesizing dynamic quiz for: {selectedSkill}</p>
      </div>
    );
  }

  // Choose a skill screen if none active
  if (!quizData && !results) {
    return (
      <div className="max-w-md mx-auto glass-panel p-6 rounded-lg space-y-6 animate-fade-in">
        <div className="flex items-center space-x-3 border-b border-slate-800 pb-3">
          <HelpCircle className="w-6 h-6 text-cyber-purple" />
          <h2 className="text-lg font-bold">Skill Assessment Portal</h2>
        </div>
        
        {availableSkills.length > 0 ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="skill-selector" className="text-xs font-mono text-gray-500">SELECT SKILL VECTOR TO ASSESS</label>
              <select
                id="skill-selector"
                value={selectedSkill}
                onChange={(e) => setSelectedSkill(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-4 py-2.5 text-sm focus:outline-none focus:border-cyber-purple text-gray-200 font-mono"
              >
                {availableSkills.map((skill, idx) => (
                  <option key={idx} value={skill}>{skill}</option>
                ))}
              </select>
            </div>
            
            <button
              onClick={() => handleStartQuiz(selectedSkill)}
              className="w-full btn-cyber-blue py-3 rounded text-sm font-semibold flex items-center justify-center space-x-1"
            >
              <span>Launch Assessment</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="text-center text-gray-400 py-6 text-sm">
            No identified skill gaps to assess! Choose a career goal or upload a resume to retrieve gaps.
          </div>
        )}
      </div>
    );
  }

  // Quiz active taking questions
  if (quizData && !results) {
    const questions = quizData.questions || [];
    const activeQ = questions[currentIdx];
    const totalQ = questions.length;
    const selectedAnswer = answers[activeQ?.id];

    return (
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        {/* Progress header */}
        <div className="flex justify-between items-center glass-panel px-6 py-4 rounded-lg">
          <div>
            <span className="text-xs font-mono text-cyber-purple uppercase tracking-wider">Assessment Active</span>
            <h2 className="text-lg font-bold text-white mt-0.5">{quizData.skill_name}</h2>
          </div>
          <span className="text-xs font-mono text-gray-500">QUESTION {currentIdx + 1} OF {totalQ}</span>
        </div>

        {/* Question card */}
        <div className="glass-panel p-6 rounded-lg space-y-6">
          <p className="text-lg font-semibold leading-relaxed text-gray-100">
            {activeQ?.question}
          </p>

          <div className="grid grid-cols-1 gap-3">
            {activeQ?.options && Object.entries(activeQ.options).map(([letter, text]) => {
              const isSelected = selectedAnswer === letter;
              return (
                <button
                  key={letter}
                  onClick={() => handleSelectOption(activeQ.id, letter)}
                  className={`w-full p-4 rounded-lg border text-left flex items-start space-x-3 transition ${
                    isSelected
                      ? 'border-cyber-purple bg-cyber-purple/10 text-white'
                      : 'border-slate-850 bg-slate-900/20 text-gray-400 hover:border-slate-800'
                  }`}
                >
                  <span className={`px-2 py-0.5 rounded font-mono text-xs ${
                    isSelected ? 'bg-cyber-purple text-white' : 'bg-slate-900 border border-slate-850'
                  }`}>
                    {letter}
                  </span>
                  <span className="text-sm font-sans">{text}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation bottom bar */}
        <div className="flex justify-between items-center">
          <button
            onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
            disabled={currentIdx === 0}
            className="btn-cyber-secondary px-5 py-2.5 rounded text-xs disabled:opacity-40"
          >
            Previous
          </button>

          {errorMsg && (
            <span className="text-xs text-red-400 font-mono">{errorMsg}</span>
          )}

          {currentIdx < totalQ - 1 ? (
            <button
              onClick={() => {
                if (!selectedAnswer) {
                  setErrorMsg('Select option before proceeding.');
                  return;
                }
                setErrorMsg('');
                setCurrentIdx((prev) => prev + 1);
              }}
              className="btn-cyber-blue px-6 py-2.5 rounded text-xs"
            >
              Next Question
            </button>
          ) : (
            <button
              onClick={handleSubmitQuiz}
              disabled={submitting}
              className="btn-cyber px-6 py-2.5 rounded text-xs font-semibold flex items-center space-x-1"
            >
              {submitting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Evaluating...</span>
                </>
              ) : (
                <span>Submit Assessment</span>
              )}
            </button>
          )}
        </div>
      </div>
    );
  }

  // Quiz evaluation results display
  if (results) {
    const isPass = results.score >= 70;
    return (
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        {/* Aggregated Score Panel */}
        <div className="glass-panel p-8 rounded-lg text-center space-y-6 border-indigo-500/20 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl -z-10"></div>
          <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto border ${
            isPass
              ? 'bg-cyber-green/10 border-cyber-green/30 text-cyber-green shadow-[0_0_15px_rgba(16,185,129,0.15)]'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            <Award className="w-9 h-9" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Assessment Complete</h2>
            <p className="text-xs text-gray-500 font-mono uppercase tracking-wider mt-1">{results.skill_name}</p>
          </div>

          <div className="flex justify-center space-x-8">
            <div className="text-center">
              <p className="text-4xl font-extrabold neon-text-purple">{results.score}%</p>
              <p className="text-[10px] text-gray-500 font-mono mt-1">SCORE</p>
            </div>
            <div className="text-center border-l border-slate-850 pl-8">
              <p className="text-4xl font-extrabold text-white">
                {results.correct_count}/{results.total_questions}
              </p>
              <p className="text-[10px] text-gray-500 font-mono mt-1">CORRECT</p>
            </div>
          </div>

          <div className="pt-2">
            <span className="inline-block text-xs font-mono text-cyber-green border border-cyber-green/20 bg-cyber-green/5 px-3 py-1 rounded">
              ⭐ Career Readiness boost to: {results.new_readiness_score}%
            </span>
          </div>
        </div>

        {/* Detailed Question Review List */}
        <div className="space-y-4">
          <h3 className="text-xs font-mono text-gray-400 uppercase tracking-widest border-b border-slate-800 pb-1">
            Questions Review
          </h3>
          
          {results.results?.map((resItem, idx) => {
            const isCorrect = resItem.is_correct;
            return (
              <div
                key={idx}
                className={`glass-panel p-5 rounded-lg border space-y-4 ${
                  isCorrect ? 'border-emerald-500/10' : 'border-red-500/10'
                }`}
              >
                <div className="flex justify-between items-start space-x-2">
                  <h4 className="text-sm font-semibold text-gray-200">
                    Q{idx + 1}: {resItem.question}
                  </h4>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono flex items-center space-x-1 ${
                    isCorrect ? 'bg-cyber-green/10 text-cyber-green' : 'bg-red-500/10 text-red-400'
                  }`}>
                    {isCorrect ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                    <span>{isCorrect ? 'CORRECT' : 'INCORRECT'}</span>
                  </span>
                </div>

                {/* Selected answer vs Correct answer review */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                  <div className={`p-2.5 rounded border ${
                    isCorrect 
                      ? 'border-emerald-500/10 bg-emerald-950/5 text-emerald-400' 
                      : 'border-red-500/10 bg-red-950/5 text-red-400'
                  }`}>
                    <span className="font-mono font-bold block mb-0.5 text-slate-500">YOUR RESPONSE</span>
                    <span>{resItem.options[resItem.user_answer] || 'No answer'} ({resItem.user_answer})</span>
                  </div>

                  {!isCorrect && (
                    <div className="p-2.5 rounded border border-emerald-500/10 bg-emerald-950/5 text-emerald-400">
                      <span className="font-mono font-bold block mb-0.5 text-slate-500 font-mono">CORRECT VALUE</span>
                      <span>{resItem.options[resItem.correct_answer]} ({resItem.correct_answer})</span>
                    </div>
                  )}
                </div>

                {/* Explanation text */}
                {resItem.explanation && (
                  <div className="text-xs p-3 rounded bg-slate-950/40 border border-slate-850 text-gray-400 italic">
                    <span className="font-mono font-bold text-[10px] block text-gray-500 not-italic mb-1 uppercase">AI EXPLANATION</span>
                    <span>{resItem.explanation}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom options */}
        <div className="flex space-x-4">
          <button
            onClick={() => handleStartQuiz(results.skill_name)}
            className="btn-cyber-secondary px-5 py-2.5 rounded text-xs"
          >
            Retake Quiz
          </button>
          
          <button
            onClick={() => {
              setQuizData(null);
              setResults(null);
            }}
            className="btn-cyber-secondary px-5 py-2.5 rounded text-xs"
          >
            Test Another Skill
          </button>

          <button
            onClick={() => setActivePage('roadmap')}
            className="btn-cyber-blue px-6 py-2.5 rounded text-xs font-semibold"
          >
            Back to Roadmap
          </button>
        </div>
      </div>
    );
  }
}
