import React, { useState } from 'react';
import { Cpu, Mail, Lock, ArrowRight } from 'lucide-react';
import { authAPI } from '../services/api';

export default function LoginPage({ onAuthenticated, switchMode }) {
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await authAPI.login(form.email, form.password);
      if (res.status === 'success') {
        onAuthenticated(res.data.user, res.data.token);
      } else {
        setError(res.message || 'Login failed.');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Unable to log in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md glass-panel rounded-2xl border border-slate-900 p-6">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 rounded-lg bg-cyber-green/10 border border-cyber-green/20">
            <Cpu className="w-6 h-6 text-cyber-green" />
          </div>
          <div>
            <div className="text-xs font-mono text-cyber-green uppercase tracking-wider">Secure Access</div>
            <div className="text-2xl font-extrabold tracking-tight">SkillGap AI</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-mono text-gray-400 uppercase tracking-widest">Email Address</label>
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2">
              <Mail className="w-4 h-4 text-gray-500" />
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full bg-transparent outline-none text-white"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-mono text-gray-400 uppercase tracking-widest">Password</label>
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2">
              <Lock className="w-4 h-4 text-gray-500" />
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full bg-transparent outline-none text-white"
                placeholder="Enter your password"
                required
              />
            </div>
          </div>

          {error && <p className="text-xs text-red-300">{error}</p>}

          <button type="submit" disabled={loading} className="btn-cyber w-full px-4 py-3 rounded-lg font-semibold text-sm flex items-center justify-center gap-2">
            {loading ? 'Signing in...' : 'Login'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-4 text-center text-xs text-gray-400">
          New to SkillGap AI?{' '}
          <button onClick={switchMode} className="text-cyber-blue hover:underline">Create an account</button>
        </div>
      </div>
    </div>
  );
}
