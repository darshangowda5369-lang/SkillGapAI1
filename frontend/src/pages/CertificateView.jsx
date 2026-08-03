import React from 'react';
import { Award, Download, ArrowLeft } from 'lucide-react';

export default function CertificateView({ setActivePage, profile, sharedState }) {
  const certificate = sharedState?.certificate || {};
  const userName = profile?.full_name || profile?.username || 'Learner';
  const userEmail = profile?.email || 'learner@skillgap.ai';
  const completionDate = certificate.completion_date || new Date().toLocaleDateString();
  const certificateId = certificate.certificate_id || 'SKG-AUTOMATED-CERT';
  const downloadUrl = certificate.download_url || '/api/progress/certificate/download/1';

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="glass-panel p-6 rounded-lg border border-emerald-500/20">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <p className="text-xs font-mono text-cyber-green uppercase tracking-widest">Certificate</p>
            <h1 className="text-2xl font-extrabold mt-1">Certificate of Completion</h1>
          </div>
          <button
            onClick={() => setActivePage('roadmap')}
            className="btn-cyber px-4 py-2 rounded text-xs font-semibold flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Roadmap</span>
          </button>
        </div>
      </div>

      <div className="glass-panel p-8 rounded-lg border border-slate-800">
        <div className="space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-950/20 px-4 py-1 text-xs text-emerald-300 font-mono">
              <Award className="w-4 h-4" />
              <span>SkillGap AI Learning Course</span>
            </div>
            <h2 className="text-3xl font-extrabold text-white">Certificate of Completion</h2>
            <p className="text-sm text-gray-400 max-w-2xl mx-auto">
              This is to certify that {userName} has successfully completed the SkillGap AI learning course with 100% completion.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
              <p className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">User Name</p>
              <p className="mt-2 text-white font-semibold">{userName}</p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
              <p className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">User Email</p>
              <p className="mt-2 text-white font-semibold">{userEmail}</p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
              <p className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">Completion Date</p>
              <p className="mt-2 text-white font-semibold">{completionDate}</p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
              <p className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">Certificate ID</p>
              <p className="mt-2 text-white font-semibold">{certificateId}</p>
            </div>
          </div>

          <div className="pt-2">
            <a
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-cyber-blue w-full md:w-auto px-5 py-3 rounded-lg font-semibold text-sm flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>Download Certificate as PDF</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
