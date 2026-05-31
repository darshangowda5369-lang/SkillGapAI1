import React, { useEffect, useState } from 'react';
import { roadmapAPI } from '../services/api';
import { Target, ArrowRight, ShieldAlert, Cpu, Sparkles, RefreshCw } from 'lucide-react';

export default function CareerGoal({ setActivePage }) {
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [customGoal, setCustomGoal] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingPresets, setFetchingPresets] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [currentStep, setCurrentStep] = useState(0);

  const loadingSteps = [
    "Spinning up Career Advisor engine...",
    "Querying target industry baseline requirements...",
    "Retrieving active resume skills map...",
    "Running gap analysis matrix...",
    "Synthesizing customized timeline steps...",
    "Compiling learning nodes & external materials..."
  ];

  useEffect(() => {
    let interval;
    if (loading) {
      setCurrentStep(0);
      interval = setInterval(() => {
        setCurrentStep((prev) => (prev < loadingSteps.length - 1 ? prev + 1 : prev));
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    const fetchGoals = async () => {
      try {
        setFetchingPresets(true);
        const res = await roadmapAPI.getGoals();
        if (res.status === 'success') {
          setPresets(res.data.presets || []);
        }
      } catch (err) {
        console.error(err);
        setErrorMsg('Failed to pull presets. Please ensure the Flask app is online.');
      } finally {
        setFetchingPresets(false);
      }
    };
    fetchGoals();
  }, []);

  const handleSelectPreset = (title) => {
    setSelectedPreset(title);
    setCustomGoal('');
    setErrorMsg('');
  };

  const handleCustomChange = (e) => {
    setCustomGoal(e.target.value);
    setSelectedPreset(null);
    setErrorMsg('');
  };

  const handleGenerate = async () => {
    const targetGoal = selectedPreset || customGoal.strip?.() || customGoal.trim();
    if (!targetGoal) {
      setErrorMsg('Please select a preset role or enter a custom goal.');
      return;
    }

    try {
      setLoading(true);
      setErrorMsg('');
      const res = await roadmapAPI.generate(targetGoal);
      if (res.status === 'success') {
        // Go directly to roadmap view page
        setActivePage('roadmap');
      } else {
        throw new Error(res.message || 'Generation failed');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.message || err.message || 'Error occurred generating roadmap');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-6 max-w-md mx-auto text-center animate-pulse-cyber">
        <Sparkles className="w-16 h-16 text-cyber-green animate-spin" />
        <div className="space-y-2">
          <h2 className="text-xl font-bold font-mono tracking-widest text-cyber-green">AI SYNTHESIZER RUNNING</h2>
          <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden border border-slate-800">
            <div 
              className="bg-cyber-green h-full rounded-full transition-all duration-1000" 
              style={{ width: `${((currentStep + 1) / loadingSteps.length) * 100}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 font-mono italic mt-2 min-h-6">
            {loadingSteps[currentStep]}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      <div className="glass-panel p-6 rounded-lg">
        <h1 className="text-2xl font-bold flex items-center space-x-2">
          <Target className="w-6 h-6 text-cyber-blue" />
          <span className="bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Define Target Career Goal
          </span>
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Select one of our preset career paths, or type your own custom goal. Our AI compiles required skill maps and evaluates your readiness.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Preset list */}
        <div className="glass-panel p-6 rounded-lg space-y-4">
          <h2 className="text-sm font-mono text-gray-400 uppercase tracking-widest border-b border-slate-800 pb-1.5">
            Path Presets
          </h2>
          
          {fetchingPresets ? (
            <div className="flex items-center space-x-2 justify-center py-12 text-gray-500">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Querying presets...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-2.5">
              {presets.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectPreset(preset.title)}
                  className={`w-full p-4 rounded-lg border text-left flex justify-between items-center transition ${
                    selectedPreset === preset.title
                      ? 'border-cyber-blue bg-cyber-blue/5 text-white'
                      : 'border-slate-850 bg-slate-900/30 text-gray-400 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <p className="font-semibold text-sm">{preset.title}</p>
                    <p className="text-[10px] text-gray-500 font-mono mt-0.5 max-w-[200px] truncate">
                      {preset.skills.join(', ')}
                    </p>
                  </div>
                  <ArrowRight className={`w-4 h-4 transition ${selectedPreset === preset.title ? 'text-cyber-blue translate-x-1' : 'text-gray-600'}`} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Custom path input & action */}
        <div className="glass-panel p-6 rounded-lg flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <h2 className="text-sm font-mono text-gray-400 uppercase tracking-widest border-b border-slate-800 pb-1.5">
              Custom Path Vector
            </h2>
            <div className="space-y-2">
              <label htmlFor="custom-goal-input" className="text-xs font-mono text-gray-500">
                Type Job Title
              </label>
              <input
                id="custom-goal-input"
                type="text"
                value={customGoal}
                onChange={handleCustomChange}
                placeholder="e.g. Machine Learning Engineer"
                className="w-full bg-slate-950 border border-slate-800 rounded px-4 py-3 text-sm focus:outline-none focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue transition font-sans"
              />
            </div>
            
            <p className="text-xs text-gray-500 font-mono">
              💡 Tip: Enter specific roles. Examples: "Flutter Developer", "Cybersecurity Analyst", "Site Reliability Engineer".
            </p>
          </div>

          <div className="space-y-4 pt-4 border-t border-slate-850">
            {errorMsg && (
              <div className="flex items-center space-x-2 text-red-400 text-xs glass-panel p-3 rounded-lg border-red-500/20 bg-red-950/5">
                <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <button
              onClick={handleGenerate}
              className="w-full btn-cyber-blue py-3 rounded-lg text-sm font-bold flex items-center justify-center space-x-2"
            >
              <Cpu className="w-4 h-4" />
              <span>Initialize Neural Roadmap Analysis</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
