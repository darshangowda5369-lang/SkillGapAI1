import React, { useEffect, useState } from 'react';
import { progressAPI } from '../services/api';
import { Award, BookOpen, CheckCircle, AlertTriangle, Play, HelpCircle, RefreshCw } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, Cell, XAxis, YAxis, Tooltip } from 'recharts';


export default function Dashboard({ setActivePage, setSharedState }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await progressAPI.getStats();
      if (res.status === 'success') {
        setStats(res.data);
      } else {
        setError(res.message || 'Failed to fetch stats');
      }
    } catch (err) {
      console.error(err);
      setError('Connection to backend failed. Make sure Flask server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-12 h-12 text-cyber-green animate-spin" />
        <p className="text-gray-400 font-mono tracking-widest text-sm">LOADING DISCOVERY STREAM...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel p-8 max-w-lg mx-auto mt-12 text-center border-red-500/30">
        <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h3 className="text-xl font-bold mb-2">System Offline</h3>
        <p className="text-gray-400 mb-6">{error}</p>
        <button onClick={fetchStats} className="btn-cyber px-6 py-2 rounded">
          Retry Handshake
        </button>
      </div>
    );
  }

  const {
    user,
    goal_title,
    skills_extracted_count,
    skills_matched_count,
    skills_missing_count,
    skills_matched,
    skills_missing,
    roadmap_progress,
    quiz_average,
    quizzes_taken,
    readiness_score
  } = stats || {};

  const normalizedRoadmapProgress = typeof roadmap_progress === 'number' ? roadmap_progress : 0;
  const isRoadmapComplete = normalizedRoadmapProgress >= 100;
  const displayedReadinessScore = isRoadmapComplete ? 100 : Math.round(readiness_score || 0);

  // Formulate data for Radar Chart
  const totalSkills = skills_matched_count + skills_missing_count;
  const radarData = [
    { subject: 'Skills Matched', A: totalSkills > 0 ? (skills_matched_count / totalSkills) * 100 : 0, fullMark: 100 },
    { subject: 'Roadmap Progress', A: normalizedRoadmapProgress, fullMark: 100 },
    { subject: 'Quiz Performance', A: quizzes_taken > 0 ? quiz_average : 0, fullMark: 100 },
    { subject: 'Readiness Score', A: displayedReadinessScore, fullMark: 100 },
  ];

  const barData = [
    { name: 'Extracted', value: skills_extracted_count || 0, color: '#3b82f6' },
    { name: 'Matched', value: skills_matched_count || 0, color: '#10b981' },
    { name: 'Missing Gaps', value: skills_missing_count || 0, color: '#f59e0b' },
    { name: 'Quiz Avg %', value: quizzes_taken > 0 ? quiz_average : 0, color: '#8b5cf6' },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center glass-panel p-6 rounded-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -z-10"></div>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-cyber-green animate-ping"></span>
            <span className="text-xs font-mono text-cyber-green uppercase tracking-wider">Session Active</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            Welcome back, {user?.username || 'Learner'}
          </h1>
          <p className="text-gray-400 text-sm">
            {goal_title 
              ? `Target Role: ${goal_title}` 
              : 'Initialize your profile by selecting a career goal or uploading a resume.'}
          </p>
        </div>
        
        {!goal_title && (
          <div className="mt-4 md:mt-0 flex space-x-4">
            <button 
              onClick={() => setActivePage('upload')} 
              className="btn-cyber px-5 py-2.5 rounded text-sm font-semibold"
            >
              Upload Resume
            </button>
            <button 
              onClick={() => setActivePage('goal')} 
              className="btn-cyber-blue px-5 py-2.5 rounded text-sm font-semibold"
            >
              Choose Career Goal
            </button>
          </div>
        )}
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-lg flex items-center space-x-4">
          <div className="p-3 bg-cyber-blue/10 rounded-lg text-cyber-blue border border-cyber-blue/20">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono">EXTRACTED SKILLS</p>
            <p className="text-2xl font-bold">{skills_extracted_count || 0}</p>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-lg flex items-center space-x-4">
          <div className="p-3 bg-cyber-green/10 rounded-lg text-cyber-green border border-cyber-green/20">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono">MATCHED SKILLS</p>
            <p className="text-2xl font-bold">{skills_matched_count || 0}</p>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-lg flex items-center space-x-4">
          <div className="p-3 bg-yellow-500/10 rounded-lg text-cyber-yellow border border-cyber-yellow/20">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono">SKILL GAPS</p>
            <p className="text-2xl font-bold">{skills_missing_count || 0}</p>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-lg flex items-center space-x-4">
          <div className="p-3 bg-cyber-purple/10 rounded-lg text-cyber-purple border border-cyber-purple/20">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono">QUIZ AVERAGE</p>
            <p className="text-2xl font-bold">{quizzes_taken > 0 ? `${quiz_average}%` : 'N/A'}</p>
          </div>
        </div>
      </div>

      {/* Main Score & Chart Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Career Readiness Score Radial Panel */}
        <div className="glass-panel p-6 rounded-lg flex flex-col items-center justify-center text-center relative overflow-hidden lg:col-span-1 border-emerald-500/15">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl -z-10"></div>
          <div className="flex flex-col items-center gap-2 mb-6">
            <h2 className="text-sm font-mono text-gray-400 uppercase tracking-widest">Career Readiness</h2>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-950/20 px-3 py-1 text-[10px] text-emerald-300 font-mono uppercase tracking-[0.24em]">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
              {isRoadmapComplete ? '100% Completed' : `${Math.round(normalizedRoadmapProgress)}% Completed`}
            </span>
          </div>
          
          <div className="relative flex items-center justify-center w-40 h-40">
            {/* SVG Circle Progress */}
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="80"
                cy="80"
                r="70"
                className="stroke-slate-800"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="80"
                cy="80"
                r="70"
                className="stroke-cyber-green"
                strokeWidth="10"
                fill="transparent"
                strokeDasharray={440}
                strokeDashoffset={440 - (440 * displayedReadinessScore) / 100}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-4xl font-extrabold neon-text-green">{displayedReadinessScore}%</span>
              <span className="text-xs text-gray-500 font-mono mt-1">READINESS</span>
            </div>
          </div>

          <div className="mt-6 space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-950/20 px-3 py-1 text-[10px] text-emerald-300 font-mono uppercase tracking-[0.24em]">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
              {isRoadmapComplete ? '100% Completed' : `${Math.round(normalizedRoadmapProgress)}% Completed`}
            </div>
            <p className="text-sm text-gray-400">
              {readiness_score >= 80 
                ? 'Excellent match! You are battle-ready.' 
                : readiness_score >= 50 
                ? 'Moderate readiness. Target missing skill nodes.'
                : goal_title 
                ? 'Significant gaps found. Begin learning roadmap.'
                : 'Upload resume and set career goal to evaluate.'}
            </p>
          </div>
        </div>

        {/* Skill Analytics Radar */}
        <div className="glass-panel p-6 rounded-lg lg:col-span-2">
          <h2 className="text-sm font-mono text-gray-400 uppercase tracking-widest mb-4">Competency Map</h2>
          <div className="w-full h-64 flex items-center justify-center">
            {totalSkills > 0 || roadmap_progress > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                  <PolarGrid stroke="#1e1b4b" />
                  <PolarAngleAxis dataKey="subject" stroke="#94a3b8" fontSize={11} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" tickCount={3} />
                  <Radar
                    name="User"
                    dataKey="A"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-500 font-mono py-12 flex flex-col items-center">
                <HelpCircle className="w-10 h-10 mb-2 opacity-50" />
                <span>Map becomes active after goal analysis</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Skills Detail Lists */}
      {goal_title && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Matched Skills */}
          <div className="glass-panel p-6 rounded-lg border-emerald-500/10">
            <div className="flex items-center justify-between mb-4 border-b border-gray-800 pb-2">
              <h3 className="font-bold flex items-center space-x-2 text-cyber-green text-sm uppercase font-mono">
                <CheckCircle className="w-4 h-4" />
                <span>Verified Match ({skills_matched_count})</span>
              </h3>
            </div>
            {skills_matched && skills_matched.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {skills_matched.map((skill, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 text-xs rounded border border-cyber-green/30 bg-cyber-green/5 text-emerald-400 font-mono"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No exact skills matched yet. Adjust resume content.</p>
            )}
          </div>

          {/* Missing Skills */}
          <div className="glass-panel p-6 rounded-lg border-yellow-500/10">
            <div className="flex items-center justify-between mb-4 border-b border-gray-800 pb-2">
              <h3 className="font-bold flex items-center space-x-2 text-cyber-yellow text-sm uppercase font-mono">
                <AlertTriangle className="w-4 h-4" />
                <span>Identified Gaps ({skills_missing_count})</span>
              </h3>
              {skills_missing_count > 0 && (
                <button 
                  onClick={() => setActivePage('roadmap')}
                  className="text-xs text-cyber-blue hover:underline flex items-center space-x-1"
                >
                  <span>Go to Roadmap</span>
                  <Play className="w-3 h-3" />
                </button>
              )}
            </div>
            {skills_missing && skills_missing.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {skills_missing.map((skill, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-2 px-3 py-1 text-xs rounded border border-cyber-yellow/20 bg-cyber-yellow/5 text-amber-400 font-mono"
                  >
                    <span>{skill}</span>
                    <button
                      onClick={() => {
                        setSharedState({ activeQuizSkill: skill });
                        setActivePage('quiz');
                      }}
                      className="hover:text-white text-cyber-blue transition"
                      title="Launch Quiz"
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-emerald-400 text-sm font-mono">No gaps identified! You cover all required skills.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
