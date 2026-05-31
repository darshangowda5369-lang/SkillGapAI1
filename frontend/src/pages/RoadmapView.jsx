import React, { useEffect, useState } from 'react';
import { roadmapAPI, progressAPI } from '../services/api';
import { Compass, CheckCircle2, Circle, Clock, BookOpen, HelpCircle, ExternalLink, RefreshCw, AlertCircle, Award } from 'lucide-react';

export default function RoadmapView({ setActivePage, setSharedState }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [expandedStep, setExpandedStep] = useState(null);
  const [toggling, setToggling] = useState(false);

  const fetchActiveRoadmap = async () => {
    try {
      setLoading(true);
      const res = await roadmapAPI.getActive();
      if (res.status === 'success') {
        setData(res.data);
        if (res.data?.roadmap && res.data.roadmap.length > 0) {
          // Expand first step by default
          setExpandedStep(res.data.roadmap[0].step_key);
        }
      } else {
        setErrorMsg(res.message || 'Failed to retrieve active roadmap.');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg('Flask server connection failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveRoadmap();
  }, []);

  const handleToggleStep = async (stepKey, currentStatus) => {
    if (!data?.roadmap_id || toggling) return;

    try {
      setToggling(true);
      const res = await progressAPI.toggleStep(data.roadmap_id, stepKey, !currentStatus);
      if (res.status === 'success') {
        // Update local state without refetching fully
        setData((prev) => {
          const updatedRoadmap = prev.roadmap.map((step) => {
            if (step.step_key === stepKey) {
              return { ...step, completed: !currentStatus };
            }
            return step;
          });
          return {
            ...prev,
            roadmap: updatedRoadmap,
            readiness_score: res.data.new_readiness_score
          };
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setToggling(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="w-12 h-12 text-cyber-blue animate-spin" />
        <p className="text-gray-400 font-mono tracking-widest text-sm">SYNCHRONIZING PATH TIMELINE...</p>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="glass-panel p-8 max-w-lg mx-auto text-center border-red-500/30">
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold mb-2">Sync Interrupted</h3>
        <p className="text-gray-400 mb-6">{errorMsg}</p>
        <button onClick={fetchActiveRoadmap} className="btn-cyber-blue px-6 py-2 rounded">
          Sync Gateway
        </button>
      </div>
    );
  }

  if (!data || !data.roadmap || data.roadmap.length === 0) {
    return (
      <div className="glass-panel p-8 max-w-md mx-auto text-center space-y-6">
        <Compass className="w-16 h-16 text-gray-600 mx-auto" />
        <div>
          <h2 className="text-xl font-bold">No Active Roadmap</h2>
          <p className="text-gray-400 text-sm mt-2">
            You need to select a career goal or upload a resume to construct a customized roadmap.
          </p>
        </div>
        <button
          onClick={() => setActivePage('goal')}
          className="btn-cyber-blue px-6 py-2.5 rounded font-semibold w-full"
        >
          Select Career Goal
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header Panel */}
      <div className="glass-panel p-6 rounded-lg flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            {data.goal_title} Learning Roadmap
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Follow the chronological path vectors below to resolve your skill gaps.
          </p>
        </div>
        
        {/* Readiness Score Status */}
        <div className="flex items-center space-x-3 px-4 py-2 rounded-lg bg-slate-900/50 border border-slate-800">
          <Award className="w-5 h-5 text-cyber-green" />
          <div className="text-left">
            <p className="text-[10px] text-gray-500 font-mono">CURRENT READINESS</p>
            <p className="text-sm font-extrabold text-white">{data.readiness_score}%</p>
          </div>
        </div>
      </div>

      {/* Timeline Steps Stack */}
      <div className="relative pl-6 md:pl-8 border-l border-slate-800 space-y-8 ml-2">
        {data.roadmap.map((step, idx) => {
          const isExpanded = expandedStep === step.step_key;
          const isCompleted = step.completed;

          return (
            <div key={step.step_key} className="relative group">
              {/* Timeline Indicator Node */}
              <div 
                onClick={() => handleToggleStep(step.step_key, isCompleted)}
                className={`absolute -left-[35px] md:-left-[43px] top-1 w-8 h-8 rounded-full border cursor-pointer flex items-center justify-center transition-all duration-300 z-10 ${
                  isCompleted
                    ? 'border-cyber-green bg-cyber-green/10 text-cyber-green shadow-[0_0_10px_rgba(16,185,129,0.3)] hover:scale-105'
                    : 'border-slate-800 bg-slate-950 text-gray-600 hover:border-slate-600 hover:scale-105'
                }`}
                title={isCompleted ? "Mark Step Incomplete" : "Mark Step Complete"}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <Circle className="w-4 h-4" />
                )}
              </div>

              {/* Step Card Box */}
              <div className={`glass-panel p-5 rounded-lg border transition ${
                isCompleted 
                  ? 'border-emerald-500/10 hover:border-emerald-500/25 bg-emerald-950/2'
                  : isExpanded 
                  ? 'border-indigo-500/20 bg-indigo-950/2'
                  : 'hover:border-slate-700'
              }`}>
                {/* Header Row */}
                <div 
                  onClick={() => setExpandedStep(isExpanded ? null : step.step_key)}
                  className="flex justify-between items-start cursor-pointer"
                >
                  <div className="space-y-1 pr-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-xs font-mono text-gray-500">STAGE {idx + 1}</span>
                      <span className="flex items-center space-x-1 text-xs text-gray-500 font-mono">
                        <Clock className="w-3.5 h-3.5" />
                        <span>~{step.estimated_hours} hrs</span>
                      </span>
                    </div>
                    <h3 className={`text-lg font-bold transition ${isCompleted ? 'text-emerald-400 line-through' : 'text-white'}`}>
                      {step.title}
                    </h3>
                  </div>
                  <button className="text-xs text-cyber-blue font-mono hover:underline">
                    {isExpanded ? 'COLLAPSE' : 'EXPAND'}
                  </button>
                </div>

                {/* Expanded content details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-850 space-y-5 animate-slide-down">
                    <p className="text-sm text-gray-400 font-sans leading-relaxed">
                      {step.description}
                    </p>

                    {/* Sub-topics covered */}
                    <div className="space-y-2">
                      <p className="text-xs font-mono text-gray-500 uppercase tracking-wider">Key Concepts</p>
                      <div className="flex flex-wrap gap-2">
                        {step.topics?.map((topic, index) => (
                          <span 
                            key={index}
                            className="px-2.5 py-0.5 text-xs rounded-full bg-slate-900 border border-slate-800 text-gray-300 font-mono"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Target skills matching */}
                    <div className="space-y-2">
                      <p className="text-xs font-mono text-gray-500 uppercase tracking-wider">Skill Resolutions</p>
                      <div className="flex flex-wrap gap-2">
                        {step.skills_covered?.map((skill, index) => (
                          <span 
                            key={index}
                            className="px-2 py-0.5 text-xs font-mono text-cyan-400 bg-cyan-950/20 border border-cyan-900/50 rounded"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* External curated resources */}
                    {step.external_resources && step.external_resources.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-mono text-gray-500 uppercase tracking-wider">Recommended Resources</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {step.external_resources.map((res, index) => (
                            <a
                              key={index}
                              href={res.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center justify-between p-2.5 rounded bg-slate-950/50 border border-slate-850 hover:border-slate-750 transition text-xs group"
                            >
                              <div className="space-y-0.5">
                                <p className="font-semibold text-gray-300 group-hover:text-cyber-blue transition">{res.name}</p>
                                <p className="text-[10px] text-gray-500 font-mono uppercase">{res.type}</p>
                              </div>
                              <ExternalLink className="w-3.5 h-3.5 text-gray-600 group-hover:text-cyber-blue transition" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Platform Actions Row */}
                    <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4 pt-2">
                      <button
                        onClick={() => {
                          setSharedState({
                            activeLessonStep: {
                              roadmap_id: data.roadmap_id,
                              step_key: step.step_key,
                              title: step.title,
                              topics: step.topics
                            }
                          });
                          setActivePage('learn');
                        }}
                        className="btn-cyber px-5 py-2.5 rounded text-xs font-semibold flex items-center justify-center space-x-1.5"
                      >
                        <BookOpen className="w-4 h-4" />
                        <span>Study Lesson Inside Platform</span>
                      </button>

                      {step.skills_covered && step.skills_covered.length > 0 && (
                        <button
                          onClick={() => {
                            setSharedState({ activeQuizSkill: step.skills_covered[0] });
                            setActivePage('quiz');
                          }}
                          className="btn-cyber-blue px-5 py-2.5 rounded text-xs font-semibold flex items-center justify-center space-x-1.5"
                        >
                          <HelpCircle className="w-4 h-4" />
                          <span>Assess with AI Quiz</span>
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
