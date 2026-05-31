import React, { useEffect, useState } from 'react';
import { progressAPI } from '../services/api';
import { BookOpen, AlertCircle, RefreshCw, CheckCircle2, ChevronLeft, Award } from 'lucide-react';

export default function Learn({ sharedState, setActivePage }) {
  const stepInfo = sharedState?.activeLessonStep;
  
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [markingDone, setMarkingDone] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const fetchLesson = async () => {
    if (!stepInfo) return;
    
    try {
      setLoading(true);
      setErrorMsg('');
      const res = await progressAPI.getLesson(
        stepInfo.roadmap_id,
        stepInfo.step_key,
        stepInfo.title,
        stepInfo.topics
      );
      if (res.status === 'success') {
        setLesson(res.data);
      } else {
        throw new Error(res.message || 'Failed to generate lesson content');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.message || err.message || 'Failed to connect to AI server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLesson();
  }, [stepInfo]);

  const handleMarkComplete = async () => {
    if (!stepInfo || markingDone) return;
    
    try {
      setMarkingDone(true);
      const res = await progressAPI.toggleStep(stepInfo.roadmap_id, stepInfo.step_key, true);
      if (res.status === 'success') {
        setIsCompleted(true);
        // Show success, then redirect back to roadmap after short delay
        setTimeout(() => {
          setActivePage('roadmap');
        }, 1200);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setMarkingDone(false);
    }
  };

  // Simple custom markdown renderer to display headers, bullets, and code blocks beautifully
  const renderMarkdown = (text) => {
    if (!text) return null;
    
    const lines = text.split('\n');
    let inCodeBlock = false;
    let codeContent = [];
    let renderedElements = [];

    lines.forEach((line, idx) => {
      // Code block detection
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          // Close block
          renderedElements.push(
            <pre key={`code-${idx}`} className="bg-black/80 border border-slate-800 p-4 rounded-lg font-mono text-xs text-cyber-green overflow-x-auto my-4 max-w-full">
              <code>{codeContent.join('\n')}</code>
            </pre>
          );
          codeContent = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
        }
        return;
      }

      if (inCodeBlock) {
        codeContent.push(line);
        return;
      }

      const trimmed = line.trim();
      
      // H1 Header
      if (trimmed.startsWith('# ')) {
        renderedElements.push(
          <h1 key={idx} className="text-2xl font-extrabold text-white mt-6 mb-3 border-b border-slate-850 pb-2">
            {trimmed.substring(2)}
          </h1>
        );
      }
      // H2 Header
      else if (trimmed.startsWith('## ')) {
        renderedElements.push(
          <h2 key={idx} className="text-xl font-bold text-cyber-blue mt-5 mb-2.5">
            {trimmed.substring(3)}
          </h2>
        );
      }
      // H3 Header
      else if (trimmed.startsWith('### ')) {
        renderedElements.push(
          <h3 key={idx} className="text-lg font-semibold text-cyber-purple mt-4 mb-2">
            {trimmed.substring(4)}
          </h3>
        );
      }
      // Bullets
      else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        renderedElements.push(
          <li key={idx} className="text-gray-300 text-sm list-disc list-inside ml-4 my-1.5 font-sans leading-relaxed">
            {trimmed.substring(2)}
          </li>
        );
      }
      // Empty line
      else if (trimmed === '') {
        renderedElements.push(<div key={idx} className="h-2"></div>);
      }
      // Normal paragraph
      else {
        // Simple inline bold parser **text**
        const parts = trimmed.split('**');
        const formatted = parts.map((part, pIdx) => {
          if (pIdx % 2 === 1) {
            return <strong key={pIdx} className="text-white font-semibold">{part}</strong>;
          }
          return part;
        });

        renderedElements.push(
          <p key={idx} className="text-gray-300 text-sm leading-relaxed my-2.5 font-sans">
            {formatted}
          </p>
        );
      }
    });

    return <div className="space-y-1">{renderedElements}</div>;
  };

  if (!stepInfo) {
    return (
      <div className="max-w-md mx-auto glass-panel p-6 rounded-lg text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-gray-500 mx-auto" />
        <h2 className="text-lg font-bold">No Active Lesson Node</h2>
        <p className="text-gray-400 text-sm">
          Please select a learning milestone step inside your active roadmap tree to begin inside-platform lessons.
        </p>
        <button
          onClick={() => setActivePage('roadmap')}
          className="btn-cyber-blue px-6 py-2.5 rounded text-sm w-full font-semibold"
        >
          View Roadmap Tree
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="w-12 h-12 text-cyber-green animate-spin" />
        <p className="text-gray-400 font-mono tracking-widest text-sm uppercase">Retrieving and assembling AI lesson stream...</p>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="glass-panel p-6 max-w-lg mx-auto text-center border-red-500/20">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold">Failed to sync lesson</h3>
        <p className="text-gray-400 text-sm mb-4">{errorMsg}</p>
        <div className="flex space-x-3 justify-center">
          <button onClick={() => setActivePage('roadmap')} className="btn-cyber-secondary px-4 py-2 rounded text-xs">
            Back to Roadmaps
          </button>
          <button onClick={fetchLesson} className="btn-cyber px-4 py-2 rounded text-xs font-semibold">
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Top back bar */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => setActivePage('roadmap')}
          className="flex items-center space-x-1 text-xs text-gray-500 hover:text-white transition font-mono"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>BACK TO TIMELINE</span>
        </button>

        {isCompleted && (
          <span className="text-xs font-mono text-cyber-green flex items-center space-x-1 animate-pulse">
            <CheckCircle2 className="w-4 h-4" />
            <span>PROGRESS LOGGED SUCCESS</span>
          </span>
        )}
      </div>

      {/* Lesson viewport */}
      <div className="glass-panel p-8 rounded-lg space-y-6 border-indigo-500/10">
        {/* Header tag */}
        <div className="flex items-center space-x-2.5 text-xs text-gray-500 font-mono border-b border-slate-850 pb-3">
          <BookOpen className="w-4 h-4 text-cyber-green" />
          <span>MICRO-LEARNING MODULE</span>
          <span className="text-slate-800">|</span>
          <span className="text-cyber-green">ACTIVE SESSION</span>
        </div>

        {/* Dynamic Markdown Output */}
        <div className="prose prose-invert max-w-none">
          {lesson?.content_markdown ? (
            renderMarkdown(lesson.content_markdown)
          ) : (
            <p className="text-gray-400 text-sm italic">Synthesizing lesson contents...</p>
          )}
        </div>
      </div>

      {/* Lesson action footer */}
      <div className="flex justify-between items-center bg-slate-950/40 border border-slate-900 rounded-lg p-4">
        <div className="text-left max-w-sm hidden sm:block">
          <h4 className="font-semibold text-xs text-gray-400 uppercase font-mono">Module summary</h4>
          <p className="text-[10px] text-gray-500 mt-0.5 leading-relaxed">{lesson?.summary || "Study concepts above and test knowledge via quiz."}</p>
        </div>

        <button
          onClick={handleMarkComplete}
          disabled={markingDone || isCompleted}
          className="w-full sm:w-auto btn-cyber px-6 py-3 rounded text-xs font-bold flex items-center justify-center space-x-2"
        >
          {markingDone ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Logging Complete...</span>
            </>
          ) : isCompleted ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-black" />
              <span>Stage Verified Done</span>
            </>
          ) : (
            <>
              <Award className="w-3.5 h-3.5" />
              <span>Verify Module Complete & Boost Readiness</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
