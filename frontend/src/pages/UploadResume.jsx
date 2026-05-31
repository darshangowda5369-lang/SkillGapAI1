import React, { useState, useCallback } from 'react';
import { resumeAPI } from '../services/api';
import { Upload, FileText, CheckCircle2, AlertCircle, RefreshCw, Cpu } from 'lucide-react';

export default function UploadResume({ setActivePage, showToast }) {
  const [file, setFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, uploading, parsing, success, error
  const [logMessages, setLogMessages] = useState([]);
  const [extractedSkills, setExtractedSkills] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');

  const addLog = (msg) => {
    setLogMessages((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const handleSeedDemo = async (profileType) => {
    try {
      setFile(null);
      setStatus('uploading');
      setLogMessages([]);
      addLog(`Initializing seed profile sequence: [${profileType.toUpperCase()}]`);
      addLog(`Connecting to Flask database transaction processor...`);
      
      await new Promise(r => setTimeout(r, 600));
      setStatus('parsing');
      addLog(`Injecting cognitive profile text block...`);
      addLog(`Invoking Gemini parser model context...`);
      
      const res = await resumeAPI.seedDemo(profileType);
      if (res.status === 'success') {
        setStatus('success');
        addLog(`Seed successfully parsed!`);
        addLog(`Synchronized ${res.data.extracted_skills?.length || 0} skills.`);
        setExtractedSkills(res.data.extracted_skills || []);
        if (showToast) showToast(`Demo profile '${profileType}' loaded successfully!`, 'success');
      } else {
        throw new Error(res.message);
      }
    } catch (err) {
      console.error(err);
      setStatus('error');
      setErrorMsg(err.message || 'Seeding failed');
      addLog(`CRITICAL: Seeding aborted.`);
      if (showToast) showToast('Failed to seed profile.', 'error');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    const ext = selectedFile.name.split('.').pop().toLowerCase() || '';
    if (ext === 'pdf' || ext === 'docx' || ext === 'txt') {
      setFile(selectedFile);
      setErrorMsg('');
      setStatus('idle');
    } else {
      setErrorMsg('Invalid file type. Please upload a PDF, DOCX, or TXT resume.');
      setFile(null);
    }
  };

  const uploadFile = async () => {
    if (!file) return;

    try {
      setStatus('uploading');
      setLogMessages([]);
      addLog(`Initializing transfer for payload: ${file.name}`);
      addLog(`Payload size: ${(file.size / 1024).toFixed(1)} KB`);
      addLog(`Opening gateway pipeline to backend service...`);

      const formData = new FormData();
      formData.append('file', file);

      // Simulate a small delay for futuristic log experience
      await new Promise(r => setTimeout(r, 600));
      addLog(`Streaming document bits...`);
      setStatus('parsing');
      addLog(`Gateway closed. Document stored successfully.`);
      addLog(`Launching Neural NLP Parser pipeline...`);
      addLog(`Consulting Gemini API knowledge graph...`);

      const res = await resumeAPI.uploadResume(formData);

      if (res.status === 'success') {
        setStatus('success');
        addLog(`Neural parser execution complete.`);
        addLog(`Extracted ${res.data.extracted_skills?.length || 0} skill indicators.`);
        setExtractedSkills(res.data.extracted_skills || []);
      } else {
        throw new Error(res.message || 'Unknown server error');
      }
    } catch (err) {
      console.error(err);
      setStatus('error');
      setErrorMsg(err.response?.data?.message || err.message || 'Handshake failed during parsing');
      addLog(`CRITICAL: Processing aborted. Pipeline threw exception.`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div className="glass-panel p-6 rounded-lg">
        <h1 className="text-2xl font-bold flex items-center space-x-2">
          <Cpu className="w-6 h-6 text-cyber-green" />
          <span className="bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Neural Resume Analyzer
          </span>
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Upload your resume in PDF, DOCX, or TXT format. Our parser extracts technical skills, matching indicators, and conceptual knowledge.
        </p>
      </div>

      {status !== 'success' ? (
        <div className="space-y-6">
          {/* Quick Demo profiles */}
          <div className="glass-panel p-5 rounded-lg border-indigo-500/10 space-y-3.5 animate-scale-in">
            <div className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyber-blue animate-pulse"></span>
              <h3 className="text-xs font-mono text-gray-400 uppercase tracking-widest">Demo Runway: Seed Resume Profiles</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                onClick={() => handleSeedDemo('frontend')}
                disabled={status === 'uploading' || status === 'parsing'}
                className="btn-cyber-secondary p-3 rounded-lg text-left text-xs font-semibold hover:border-cyber-green/50 flex flex-col justify-between h-20 transition disabled:opacity-40"
              >
                <span className="text-slate-200">Jane Smith</span>
                <span className="text-[10px] text-gray-500 font-mono">Junior Frontend Dev</span>
              </button>
              
              <button
                onClick={() => handleSeedDemo('devops')}
                disabled={status === 'uploading' || status === 'parsing'}
                className="btn-cyber-secondary p-3 rounded-lg text-left text-xs font-semibold hover:border-cyber-blue/50 flex flex-col justify-between h-20 transition disabled:opacity-40"
              >
                <span className="text-slate-200">Marcus Vance</span>
                <span className="text-[10px] text-gray-500 font-mono">DevOps Engineer</span>
              </button>
              
              <button
                onClick={() => handleSeedDemo('data_science')}
                disabled={status === 'uploading' || status === 'parsing'}
                className="btn-cyber-secondary p-3 rounded-lg text-left text-xs font-semibold hover:border-cyber-purple/50 flex flex-col justify-between h-20 transition disabled:opacity-40"
              >
                <span className="text-slate-200">Alice Kova</span>
                <span className="text-[10px] text-gray-500 font-mono">Data Scientist</span>
              </button>
            </div>
          </div>

          {/* File Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition cursor-pointer relative overflow-hidden ${
              isDragOver 
                ? 'border-cyber-green bg-cyber-green/5' 
                : 'border-slate-800 bg-cyber-card hover:border-slate-700'
            }`}
          >
            <input
              type="file"
              id="resume-file"
              className="absolute inset-0 opacity-0 cursor-pointer"
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt"
              disabled={status === 'uploading' || status === 'parsing'}
            />
            
            <div className="flex flex-col items-center space-y-4">
              <div className={`p-4 rounded-full border ${isDragOver ? 'bg-cyber-green/20 text-cyber-green' : 'bg-slate-900/50 text-gray-500'}`}>
                <Upload className="w-10 h-10" />
              </div>
              <div>
                <p className="font-semibold text-lg">
                  {file ? file.name : 'Drag & Drop Resume'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Supports PDF, DOCX, or TXT (Max 16MB)
                </p>
              </div>
              {file && status === 'idle' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    uploadFile();
                  }}
                  className="btn-cyber px-6 py-2 rounded text-sm font-semibold relative z-10"
                >
                  Analyze Resume
                </button>
              )}
            </div>
          </div>

          {errorMsg && (
            <div className="flex items-center space-x-2 text-red-400 text-sm glass-panel p-4 rounded-lg border-red-500/20 bg-red-950/5">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Terminal Parser Logs */}
          {(status === 'uploading' || status === 'parsing' || status === 'error') && (
            <div className="glass-panel p-4 rounded-lg bg-black/60 border-slate-900">
              <div className="flex items-center justify-between border-b border-slate-850 pb-2 mb-3">
                <span className="text-xs text-gray-500 font-mono tracking-wider">PROCESS LOG STREAM</span>
                {(status === 'uploading' || status === 'parsing') && (
                  <RefreshCw className="w-3.5 h-3.5 text-cyber-green animate-spin" />
                )}
              </div>
              <div className="space-y-1 font-mono text-xs text-gray-400 max-h-48 overflow-y-auto">
                {logMessages.map((log, idx) => (
                  <div key={idx}>{log}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Success Screen */
        <div className="glass-panel p-8 rounded-lg space-y-6 border-emerald-500/20 text-center animate-scale-in">
          <div className="w-16 h-16 bg-cyber-green/10 border border-cyber-green/30 text-cyber-green rounded-full flex items-center justify-center mx-auto shadow-[0_0_15px_rgba(16,185,129,0.1)]">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Analysis Complete</h2>
            <p className="text-sm text-gray-500 mt-1">
              Your profile has been synchronized with extracted skill tags.
            </p>
          </div>

          {/* Extracted Skills Badges */}
          <div className="max-w-md mx-auto">
            <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-3 text-left border-b border-gray-800 pb-1">
              Extracted Skills ({extractedSkills.length})
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-h-40 overflow-y-auto p-1">
              {extractedSkills.map((skill, index) => (
                <span
                  key={index}
                  className="px-2.5 py-1 text-xs font-mono rounded border border-cyber-green/20 bg-cyber-green/5 text-emerald-400"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          <div className="flex justify-center space-x-4 pt-4">
            <button
              onClick={() => {
                setStatus('idle');
                setFile(null);
              }}
              className="btn-cyber-secondary px-5 py-2.5 rounded text-sm"
            >
              Analyze Another
            </button>
            <button
              onClick={() => setActivePage('goal')}
              className="btn-cyber-blue px-6 py-2.5 rounded text-sm font-semibold"
            >
              Select Career Goal
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
