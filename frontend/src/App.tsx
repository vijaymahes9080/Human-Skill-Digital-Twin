import React, { useState, useEffect } from 'react';
import { 
  Brain, BookOpen, GraduationCap, Award, Compass, MessageSquare, 
  User, CheckCircle2, AlertTriangle, Play, RefreshCw, BarChart2, 
  HelpCircle, Shield, LogOut, ChevronRight, Check, Activity, Save,
  Target
} from 'lucide-react';

// Custom SVG Chart helper for local-first reliability
function SimpleLineChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) return null;
  const width = 500;
  const height = 150;
  const padding = 20;
  
  const maxVal = 1.0;
  const points = data.map((d, i) => {
    const x = padding + (i * (width - padding * 2)) / (data.length - 1);
    const y = height - padding - (d.mastery * (height - padding * 2)) / maxVal;
    return `${x},${y}`;
  }).join(' ');

  const retPoints = data.map((d, i) => {
    const x = padding + (i * (width - padding * 2)) / (data.length - 1);
    const y = height - padding - (d.retention * (height - padding * 2)) / maxVal;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-40 bg-slate-900/60 rounded-xl p-2 border border-slate-700/50">
      {/* Grid Lines */}
      <line x1={padding} y1={padding} x2={width-padding} y2={padding} stroke="#334155" strokeDasharray="4" />
      <line x1={padding} y1={height/2} x2={width-padding} y2={height/2} stroke="#334155" strokeDasharray="4" />
      <line x1={padding} y1={height-padding} x2={width-padding} y2={height-padding} stroke="#475569" />
      
      {/* Lines */}
      <polyline fill="none" stroke="#6366f1" strokeWidth="3" points={points} />
      <polyline fill="none" stroke="#10b981" strokeWidth="2" strokeDasharray="3" points={retPoints} />
      
      {/* Legend */}
      <text x="30" y="25" fill="#818cf8" fontSize="10" fontWeight="bold">Simulated Mastery</text>
      <text x="180" y="25" fill="#34d399" fontSize="10" fontWeight="bold">Simulated Memory Retention</text>
    </svg>
  );
}

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('dt_token'));
  const [activeTab, setActiveTab] = useState<'dashboard' | 'graph' | 'mentor' | 'simulator' | 'decisions' | 'reflections' | 'arena'>('dashboard');
  
  // Auth Form State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [authError, setAuthError] = useState('');

  // Twin & API States
  const [twin, setTwin] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);

  
  // Interactive Graph selection details
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedNodeGaps, setSelectedNodeGaps] = useState<any[]>([]);
  const [selectedNodePath, setSelectedNodePath] = useState<any[]>([]);

  // Practice session logging
  const [sessionType, setSessionType] = useState('coding');
  const [sessionDuration, setSessionDuration] = useState('30');
  const [sessionScore, setSessionScore] = useState('0.85');
  const [sessionConcept, setSessionConcept] = useState('');
  const [sessionTags, setSessionTags] = useState('');
  const [logSuccess, setLogSuccess] = useState(false);

  // Active Quiz Modal state
  const [activeQuiz, setActiveQuiz] = useState<any[] | null>(null);
  const [quizConcept, setQuizConcept] = useState<string>('');
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({});
  const [quizResult, setQuizResult] = useState<any | null>(null);

  // AI Mentor Chat State
  const [chatMessages, setChatMessages] = useState<any[]>([
    { role: 'assistant', content: "Hello Alex! I've loaded your Digital Twin parameters. Ask me about your 'career readiness', 'learning bottlenecks', or check your 'today's study plan'." }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [injectedTwin, setInjectedTwin] = useState<any>(null);

  // Decision Register State
  const [decisionTitle, setDecisionTitle] = useState('');
  const [decisionDesc, setDecisionDesc] = useState('');
  const [decisionChoice, setDecisionChoice] = useState('');
  const [decisionRisk, setDecisionRisk] = useState('medium');
  const [decisionConfidence, setDecisionConfidence] = useState(0.8);
  const [decisionEvidence, setDecisionEvidence] = useState('');
  const [decisionLogs, setDecisionLogs] = useState<any[]>([]);
  const [decisionSuccess, setDecisionSuccess] = useState(false);

  // Simulation State
  const [simMinutes, setSimMinutes] = useState(45);
  const [simPractice, setSimPractice] = useState('weekly');
  const [simSkipRevision, setSimSkipRevision] = useState(false);
  const [simStrategy, setSimStrategy] = useState('mixed');
  const [simResult, setSimResult] = useState<any>(null);

  // Reflections State
  const [reflectionLogs, setReflectionLogs] = useState<any[]>([]);
  const [reflectionSuccess, setReflectionSuccess] = useState('');

  // Cognitive Arena State
  const [arenaScenarios, setArenaScenarios] = useState<any[]>([]);
  const [activeScenario, setActiveScenario] = useState<any | null>(null);
  const [arenaStepIndex, setArenaStepIndex] = useState(0);
  const [arenaEvidence, setArenaEvidence] = useState<string[]>([]);
  const [arenaResponses, setArenaResponses] = useState<any[]>([]);
  const [arenaStepStartTime, setArenaStepStartTime] = useState(0);
  const [arenaConfidence, setArenaConfidence] = useState(0.8);
  const [arenaResult, setArenaResult] = useState<any | null>(null);
  const [arenaSubmitting, setArenaSubmitting] = useState(false);
  const [arenaError, setArenaError] = useState('');

  // 1. Fetch wrapper helper
  const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    };
    
    const isStaticDeploy = window.location.hostname.includes("github.io");
    if (isStaticDeploy) {
      console.info("Static GitHub Pages deployment detected. Serving fallback mocks.");
      return getMockFallbackData(endpoint, options);
    }

    try {
      const res = await fetch(`/api/v1${endpoint}`, { ...options, headers });
      if (res.status === 401) {
        handleLogout();
        throw new Error("Session expired.");
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "API Error" }));
        throw new Error(err.detail || "API Error");
      }
      return await res.json();
    } catch (error) {
      console.warn("Fetch failed, activating offline/static mock fallback for:", endpoint);
      return getMockFallbackData(endpoint, options);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('dt_token');
    setToken(null);
    setTwin(null);
  };

  // 2. Fetch User Dashboard Data
  const loadDashboardData = async () => {
    if (!token) return;
    try {
      const twinData = await apiFetch('/twin');
      setTwin(twinData);
      
      const planData = await apiFetch('/learning/plan');
      setPlan(planData);

      await apiFetch('/predictions');
 
       const graphData = await apiFetch('/knowledge/graph');
       setGraph(graphData);
 
       // Fetch weaknesses directly from DB diagnostics endpoint by default
       await apiFetch('/knowledge/gaps?target_concept_id=neural_networks');

      const decData = await apiFetch('/decisions');
      setDecisionLogs(decData);

      const refData = await apiFetch('/reflections');
      setReflectionLogs(refData);

      const arenaData = await apiFetch('/arena/scenarios');
      setArenaScenarios(arenaData);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (token) {
      loadDashboardData();
    }
  }, [token]);

  // Handle Authentication
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      if (isRegister) {
        await apiFetch('/auth/register', {
          method: 'POST',
          body: JSON.stringify({ email, password, full_name: fullName })
        });
        setIsRegister(false);
        setAuthError('Registration completed. Log in using your credentials.');
      } else {
        const data = await apiFetch('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password })
        });
        localStorage.setItem('dt_token', data.access_token);
        setToken(data.access_token);
      }
    } catch (err: any) {
      setAuthError(err.message || "Authentication failed.");
    }
  };

  // Interactive Graph Node Selection
  const handleNodeClick = async (conceptId: string, nodeData: any) => {
    setSelectedNode(nodeData);
    try {
      const gaps = await apiFetch(`/knowledge/gaps?target_concept_id=${conceptId}`);
      setSelectedNodeGaps(gaps);

      const path = await apiFetch(`/knowledge/path/${conceptId}`);
      setSelectedNodePath(path);
    } catch (e) {
      console.error(e);
    }
  };

  // Log active study sessions
  const handleLogSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setLogSuccess(false);
    try {
      await apiFetch('/sessions', {
        method: 'POST',
        body: JSON.stringify({
          session_type: sessionType,
          data: {
            concept_id: sessionConcept || 'python_basics',
            score: parseFloat(sessionScore),
            tags: sessionTags.split(',').map(x => x.trim())
          }
        })
      });
      setLogSuccess(true);
      loadDashboardData();
    } catch (e) {
      console.error(e);
    }
  };

  // Load adaptive quiz questions
  const startQuiz = async (conceptId: string) => {
    setQuizResult(null);
    setQuizAnswers({});
    setQuizConcept(conceptId);
    try {
      const questions = await apiFetch(`/assessment/quiz?concept_id=${conceptId}`);
      setActiveQuiz(questions);
    } catch (e) {
      console.error(e);
    }
  };

  // Submit assessment answers
  const submitQuizAnswers = async () => {
    try {
      const results = await apiFetch(`/assessment/submit?concept_id=${quizConcept}`, {
        method: 'POST',
        body: JSON.stringify(quizAnswers)
      });
      setQuizResult(results);
      loadDashboardData();
    } catch (e) {
      console.error(e);
    }
  };

  // Run Simulator
  const runSimulator = async () => {
    try {
      const results = await apiFetch('/simulator/run', {
        method: 'POST',
        body: JSON.stringify({
          study_minutes_daily: simMinutes,
          practice_frequency: simPractice,
          skip_revision: simSkipRevision,
          strategy: simStrategy
        })
      });
      setSimResult(results);
    } catch (e) {
      console.error(e);
    }
  };

  // Send AI Mentor messages
  const sendMentorMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMsg = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await apiFetch('/mentor/chat', {
        method: 'POST',
        body: JSON.stringify({
          messages: [...chatMessages, userMsg]
        })
      });
      setChatMessages(prev => [...prev, { role: 'assistant', content: res.message }]);
      if (res.twin_parameters_injected) {
        setInjectedTwin(res.twin_parameters_injected);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setChatLoading(false);
    }
  };

  // Log new decision
  const logDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    setDecisionSuccess(false);
    try {
      await apiFetch('/decisions', {
        method: 'POST',
        body: JSON.stringify({
          title: decisionTitle,
          description: decisionDesc,
          choice_made: decisionChoice,
          risk_level: decisionRisk,
          confidence: decisionConfidence,
          evidence_collected: decisionEvidence.split(',').map(x => x.trim()),
          decision_speed_seconds: 30.0
        })
      });
      setDecisionSuccess(true);
      setDecisionTitle('');
      setDecisionChoice('');
      setDecisionDesc('');
      setDecisionEvidence('');
      loadDashboardData();
    } catch (e) {
      console.error(e);
    }
  };

  // Trigger cognitive reflections
  const triggerReflection = async (type: string) => {
    setReflectionSuccess('');
    try {
      await apiFetch(`/reflections?reflection_type=${type}`, { method: 'POST' });
      setReflectionSuccess(`Successful. Generated a new ${type} reflection.`);
      loadDashboardData();
    } catch (e) {
      console.error(e);
    }
  };

  // Arena Gameplay Handlers
  const startArenaScenario = (scenario: any) => {
    setActiveScenario(scenario);
    setArenaStepIndex(0);
    setArenaEvidence([]);
    setArenaResponses([]);
    setArenaStepStartTime(performance.now());
    setArenaConfidence(0.8);
    setArenaResult(null);
    setArenaError('');
  };

  const handleArenaClueClick = (clueId: string) => {
    if (!arenaEvidence.includes(clueId)) {
      setArenaEvidence(prev => [...prev, clueId]);
    }
  };

  const handleArenaSubmitStep = async (optionId: string) => {
    const timeSpent = (performance.now() - arenaStepStartTime) / 1000.0;
    const stepResponse = {
      step_id: activeScenario.steps[arenaStepIndex].step_id,
      option_selected: optionId,
      confidence: arenaConfidence,
      time_spent_seconds: timeSpent,
      evidence_collected: [...arenaEvidence]
    };
    const updatedResponses = [...arenaResponses, stepResponse];
    setArenaResponses(updatedResponses);

    if (arenaStepIndex + 1 < activeScenario.steps.length) {
      setArenaStepIndex(prev => prev + 1);
      setArenaEvidence([]);
      setArenaStepStartTime(performance.now());
      setArenaConfidence(0.8);
    } else {
      setArenaSubmitting(true);
      try {
        const res = await apiFetch('/arena/submit', {
          method: 'POST',
          body: JSON.stringify({
            scenario_id: activeScenario.id,
            steps: updatedResponses
          })
        });
        setArenaResult(res);
        loadDashboardData();
      } catch (err: any) {
        setArenaError(err.message || "Failed to submit arena scenario.");
      } finally {
        setArenaSubmitting(false);
      }
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#090d16] p-4">
        <div className="w-full max-w-md bg-slate-900/80 p-8 rounded-2xl border border-slate-800 backdrop-blur-md shadow-2xl">
          <div className="flex justify-center items-center gap-3 mb-8">
            <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-xl animate-glow">
              <Brain className="w-8 h-8" />
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
              DIGITAL TWIN
            </h1>
          </div>

          <h2 className="text-xl font-bold text-center mb-6 text-gray-200">
            {isRegister ? "Create Digital Twin Core Account" : "Access Your Digital Twin"}
          </h2>

          {authError && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg mb-4 text-center">
              {authError}
            </div>
          )}

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">FULL NAME</label>
                <input 
                  type="text" 
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-950/80 border border-slate-800 rounded-lg text-gray-200 focus:outline-none focus:border-indigo-500 text-sm"
                  placeholder="Alex Mercer"
                  required
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1">EMAIL ADDRESS</label>
              <input 
                type="email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-slate-950/80 border border-slate-800 rounded-lg text-gray-200 focus:outline-none focus:border-indigo-500 text-sm"
                placeholder="demo@digitaltwin.ai"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1">SECURE PASSWORD</label>
              <input 
                type="password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-4 py-2 bg-slate-950/80 border border-slate-800 rounded-lg text-gray-200 focus:outline-none focus:border-indigo-500 text-sm"
                placeholder="••••••••"
                required
              />
            </div>

            <button 
              type="submit"
              className="w-full py-2 bg-gradient-to-r from-indigo-500 to-emerald-500 hover:from-indigo-600 hover:to-emerald-600 font-bold rounded-lg transition-all shadow-lg text-sm text-slate-950"
            >
              {isRegister ? "Register Credentials" : "Boot Engine Client"}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button 
              onClick={() => setIsRegister(!isRegister)}
              className="text-xs font-semibold text-indigo-400 hover:underline"
            >
              {isRegister ? "Already registered? Login here" : "Need an open-source account? Register here"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#090d16] text-gray-100">
      
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 p-6 flex flex-col justify-between">
        <div className="space-y-8">
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-indigo-400" />
            <div>
              <h2 className="text-sm font-extrabold tracking-widest text-indigo-400">HUMAN TWIN</h2>
              <p className="text-[10px] text-gray-500">OPEN-SOURCE ENGINE</p>
            </div>
          </div>

          <nav className="space-y-2">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === 'dashboard' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-gray-400 hover:bg-slate-900'}`}
            >
              <Award className="w-4 h-4" />
              Digital Twin Core
            </button>
            <button 
              onClick={() => setActiveTab('graph')}
              className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === 'graph' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-gray-400 hover:bg-slate-900'}`}
            >
              <Compass className="w-4 h-4" />
              Knowledge Graph
            </button>
            <button 
              onClick={() => setActiveTab('mentor')}
              className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === 'mentor' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-gray-400 hover:bg-slate-900'}`}
            >
              <MessageSquare className="w-4 h-4" />
              AI Mentor Panel
            </button>
            <button 
              onClick={() => setActiveTab('simulator')}
              className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === 'simulator' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-gray-400 hover:bg-slate-900'}`}
            >
              <Activity className="w-4 h-4" />
              Learning Simulator
            </button>
            <button 
              onClick={() => setActiveTab('decisions')}
              className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === 'decisions' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-gray-400 hover:bg-slate-900'}`}
            >
              <Shield className="w-4 h-4" />
              Decisions Intelligence
            </button>
            <button 
              onClick={() => setActiveTab('reflections')}
              className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === 'reflections' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-gray-400 hover:bg-slate-900'}`}
            >
              <GraduationCap className="w-4 h-4" />
              Reflections Log
            </button>
            <button 
              onClick={() => setActiveTab('arena')}
              className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === 'arena' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-gray-400 hover:bg-slate-900'}`}
            >
              <Target className="w-4 h-4" />
              Cognitive Arena
            </button>
          </nav>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-3 p-3 bg-slate-900 rounded-xl border border-slate-800">
            <User className="w-8 h-8 text-emerald-400 bg-slate-800 p-1.5 rounded-full" />
            <div className="truncate">
              <p className="text-xs font-bold text-gray-300">Alex Mercer</p>
              <p className="text-[10px] text-gray-500 truncate">demo@digitaltwin.ai</p>
            </div>
          </div>

          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-2 border border-slate-800 hover:border-red-500/30 text-gray-400 hover:text-red-400 text-xs font-bold rounded-xl transition-all"
          >
            <LogOut className="w-4 h-4" />
            Disconnect Core
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-8 overflow-y-auto max-h-screen">
        
        {/* TAB 1: DASHBOARD */}
        {activeTab === 'dashboard' && twin && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-extrabold tracking-tight">Digital Twin Core Console</h1>
                <p className="text-gray-400 text-sm mt-1">Real-time status metrics of your active learning identity.</p>
              </div>
              <div className="flex gap-4">
                <div className="px-4 py-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-xl text-sm font-bold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Streak: {twin.state.habits?.study_streak || 0} Days
                </div>
                <div className="px-4 py-2 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-xl text-sm font-bold flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Focus: {roundTo(twin.state.habits?.total_focus_hours || 0, 1)} hrs
                </div>
              </div>
            </div>

            {/* Grid metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Learning DNA */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <h3 className="text-lg font-bold flex items-center gap-2 text-indigo-400">
                  <BookOpen className="w-5 h-5" /> Learning DNA Profile
                </h3>
                <div className="space-y-3">
                  {Object.entries(twin.state.learning_dna || {}).slice(0, 5).map(([style, data]: any) => (
                    <div key={style} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="capitalize">{style}</span>
                        <span className="text-gray-400">{intPercent(data.score)}% (conf: {intPercent(data.confidence)}%)</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${data.score * 100}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Memory Indexes */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <h3 className="text-lg font-bold flex items-center gap-2 text-emerald-400">
                  <Brain className="w-5 h-5" /> Memory Diagnostics
                </h3>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-[10px] text-gray-400 font-bold">LONG-TERM RETENTION</p>
                    <p className="text-3xl font-extrabold text-emerald-400 mt-1">{intPercent(twin.state.memory_profile?.overall_retention || 0.8)}%</p>
                  </div>
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-[10px] text-gray-400 font-bold">RECALL SPEED INDEX</p>
                    <p className="text-3xl font-extrabold text-indigo-400 mt-1">{intPercent(twin.state.memory_profile?.recall_speed_score || 0.7)}%</p>
                  </div>
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-[10px] text-gray-400 font-bold">DECAY COEFFICIENT</p>
                    <p className="text-3xl font-extrabold text-red-400 mt-1">{(twin.state.memory_profile?.average_decay_rate || 0.05).toFixed(3)}</p>
                  </div>
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-[10px] text-gray-400 font-bold">REVISION ADHERENCE</p>
                    <p className="text-3xl font-extrabold text-amber-400 mt-1">{intPercent(twin.state.habits?.revision_delay_adherence || 0.8)}%</p>
                  </div>
                </div>
              </div>

              {/* Skill Masteries */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <h3 className="text-lg font-bold flex items-center gap-2 text-indigo-400">
                  <Award className="w-5 h-5" /> Skill Proficiencies
                </h3>
                <div className="space-y-3 max-h-56 overflow-y-auto pr-2">
                  {Object.entries(twin.state.skills || {}).slice(0, 6).map(([skill, data]: any) => (
                    <div key={skill} className="flex justify-between items-center text-xs p-2 bg-slate-900/40 rounded-lg border border-slate-800">
                      <span className="font-bold capitalize">{skill.replace('_', ' ')}</span>
                      <div className="flex gap-2">
                        <span className="px-2 py-0.5 bg-indigo-500/10 text-indigo-400 rounded-md font-bold">Mastery: {intPercent(data.level)}%</span>
                        <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded-md font-bold">Conf: {intPercent(data.confidence)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Bottom Section: Plan & Session Logging */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Daily Learning Plan */}
              {plan && (
                <div className="glass-panel-glow p-6 rounded-2xl space-y-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-100 flex items-center gap-2">
                      <Compass className="w-5 h-5 text-indigo-400" /> Personalized Daily Roadmap
                    </h3>
                    <p className="text-xs text-indigo-300 mt-1">{plan.style_fit_explanation}</p>
                  </div>

                  <div className="space-y-3">
                    {plan.daily_plan?.map((task: any, idx: number) => (
                      <div key={idx} className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="px-2 py-0.5 bg-indigo-500/20 text-indigo-300 text-[10px] uppercase font-extrabold rounded-md">{task.type}</span>
                          <span className="text-xs text-gray-500 font-medium">{task.duration_est}</span>
                        </div>
                        <h4 className="text-sm font-bold text-gray-200">{task.title}</h4>
                        <p className="text-xs text-gray-400 leading-relaxed">{task.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Log Practice Session */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <h3 className="text-lg font-bold text-gray-100 flex items-center gap-2">
                  <Save className="w-5 h-5 text-emerald-400" /> Record Focused Study Session
                </h3>

                {logSuccess && (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-lg text-center">
                    Session successfully saved to Digital Twin Event broker queue!
                  </div>
                )}

                <form onSubmit={handleLogSession} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 mb-1">ACTIVITY TYPE</label>
                      <select 
                        value={sessionType}
                        onChange={e => setSessionType(e.target.value)}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                      >
                        <option value="coding">Coding Sandbox Practice</option>
                        <option value="reading">Foundational Reading</option>
                        <option value="video">Visual Walkthrough</option>
                        <option value="quiz">Interactive Quiz</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 mb-1">CONCEPT KEYWORD</label>
                      <input 
                        type="text"
                        value={sessionConcept}
                        onChange={e => setSessionConcept(e.target.value)}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                        placeholder="python_basics, calculus, etc"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 mb-1">DURATION (MINUTES)</label>
                      <input 
                        type="number"
                        value={sessionDuration}
                        onChange={e => setSessionDuration(e.target.value)}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 mb-1">PERFORMANCE SCORE (0 - 1)</label>
                      <input 
                        type="number"
                        step="0.05"
                        value={sessionScore}
                        onChange={e => setSessionScore(e.target.value)}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 mb-1">ADDITIONAL TAGS (COMMA SEPARATED)</label>
                    <input 
                      type="text"
                      value={sessionTags}
                      onChange={e => setSessionTags(e.target.value)}
                      className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                      placeholder="oop, matrix, tensor"
                    />
                  </div>

                  <button 
                    type="submit"
                    className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-lg text-xs transition-all"
                  >
                    Commit Event Log
                  </button>
                </form>
              </div>

            </div>
          </div>
        )}

        {/* TAB 2: KNOWLEDGE GRAPH */}
        {activeTab === 'graph' && graph && (
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight">Interactive Knowledge Map</h1>
              <p className="text-gray-400 text-sm mt-1">Topological representation of prerequisite maps. Click a concept node to evaluate path prerequisites.</p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
              
              {/* Canvas Renderer */}
              <div className="xl:col-span-2 glass-panel p-6 rounded-2xl min-h-[500px] flex items-center justify-center relative overflow-hidden">
                <svg viewBox="0 0 900 450" className="w-full h-[400px]">
                  {/* Draw connection edges */}
                  {graph.edges?.map((e: any) => {
                    const sourceNode = graph.nodes.find((n: any) => n.id === e.source);
                    const targetNode = graph.nodes.find((n: any) => n.id === e.target);
                    if (!sourceNode || !targetNode) return null;
                    return (
                      <g key={e.id}>
                        <line 
                          x1={sourceNode.position.x} 
                          y1={sourceNode.position.y} 
                          x2={targetNode.position.x} 
                          y2={targetNode.position.y} 
                          stroke={targetNode.data.mastery > 0.1 ? "#6366f1" : "#334155"} 
                          strokeWidth="2" 
                        />
                        {/* Direction Arrow */}
                        <polygon 
                          points="0,-4 -4,4 4,4" 
                          fill={targetNode.data.mastery > 0.1 ? "#6366f1" : "#334155"}
                          transform={`translate(${(sourceNode.position.x + targetNode.position.x)/2}, ${(sourceNode.position.y + targetNode.position.y)/2}) rotate(${Math.atan2(targetNode.position.y - sourceNode.position.y, targetNode.position.x - sourceNode.position.x) * 180 / Math.PI + 90})`} 
                        />
                      </g>
                    );
                  })}

                  {/* Draw concept nodes */}
                  {graph.nodes?.map((n: any) => {
                    const isSelected = selectedNode?.concept_id === n.id;
                    let color = "fill-slate-800 stroke-slate-700";
                    if (n.data.status === "mastered") color = "fill-indigo-950/90 stroke-indigo-500";
                    else if (n.data.status === "in_progress") color = "fill-emerald-950/90 stroke-emerald-500";
                    
                    return (
                      <g 
                        key={n.id} 
                        transform={`translate(${n.position.x}, ${n.position.y})`}
                        onClick={() => handleNodeClick(n.id, { concept_id: n.id, ...n.data })}
                        className="cursor-pointer group"
                      >
                        <circle 
                          r={isSelected ? "26" : "22"} 
                          className={`${color} stroke-[3] transition-all hover:scale-115`} 
                        />
                        <text 
                          textAnchor="middle" 
                          y="5" 
                          className="fill-gray-200 font-bold text-[9px] pointer-events-none"
                        >
                          {n.data.title.split(' ')[0]}
                        </text>
                      </g>
                    );
                  })}
                </svg>
                
                {/* Visual Legend overlays */}
                <div className="absolute bottom-4 left-4 flex gap-4 text-xs font-bold bg-slate-950/80 px-4 py-2 rounded-lg border border-slate-800">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-indigo-500 rounded-full"></span> Mastered
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-emerald-500 rounded-full"></span> In Progress
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-slate-800 rounded-full border border-slate-700"></span> Locked
                  </div>
                </div>
              </div>

              {/* Node Inspector Side Panel */}
              <div className="space-y-6">
                {selectedNode ? (
                  <div className="glass-panel p-6 rounded-2xl space-y-6">
                    <div>
                      <h3 className="text-xl font-bold text-gray-200">{selectedNode.title}</h3>
                      <p className="text-xs text-gray-500 font-semibold mt-1 uppercase">Concept ID: {selectedNode.concept_id}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-center">
                        <p className="text-[9px] text-gray-500 font-extrabold uppercase">MASTERY</p>
                        <p className="text-2xl font-black text-indigo-400 mt-1">{intPercent(selectedNode.mastery)}%</p>
                      </div>
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-center">
                        <p className="text-[9px] text-gray-500 font-extrabold uppercase">CONFIDENCE</p>
                        <p className="text-2xl font-black text-emerald-400 mt-1">{intPercent(selectedNode.confidence)}%</p>
                      </div>
                    </div>

                    <button 
                      onClick={() => startQuiz(selectedNode.concept_id)}
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-all"
                    >
                      <Play className="w-4 h-4" /> Start Adaptive quiz check
                    </button>

                    {/* Gap analysis diagnostics */}
                    <div className="space-y-3 pt-2">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Gap Analysis Diagnostics</h4>
                      {selectedNodeGaps.length > 0 ? (
                        selectedNodeGaps.map((gap, i) => (
                          <div key={i} className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl flex gap-2">
                            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-bold">{gap.title}</p>
                              <p className="text-[10px] text-red-400/80 mt-1">{gap.reason}</p>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-gray-400 flex items-center gap-2">
                          <Check className="w-4 h-4 text-emerald-400" /> Prerequisite checklist cleared. Ready for study.
                        </p>
                      )}
                    </div>

                    {/* Topological Learning path sequence */}
                    <div className="space-y-3 pt-2">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Topological learning path</h4>
                      <div className="space-y-2">
                        {selectedNodePath.map((step, i) => (
                          <div key={i} className="flex items-center justify-between text-xs p-2 bg-slate-900/60 rounded-lg border border-slate-800">
                            <span className="font-medium text-gray-300">{i+1}. {step.title}</span>
                            {step.mastery >= 0.75 ? (
                              <span className="px-2 py-0.5 bg-indigo-500/10 text-indigo-400 text-[9px] font-extrabold rounded">Mastered</span>
                            ) : step.status === "in_progress" ? (
                              <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[9px] font-extrabold rounded">Active</span>
                            ) : (
                              <span className="px-2 py-0.5 bg-slate-800 text-gray-500 text-[9px] font-extrabold rounded">Locked</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="glass-panel p-8 rounded-2xl text-center text-gray-400 h-64 flex flex-col justify-center items-center">
                    <HelpCircle className="w-8 h-8 text-indigo-400 mb-2" />
                    <p className="font-semibold text-sm">No Concept Selected</p>
                    <p className="text-xs mt-1">Select a circle node in the graph map to load metrics.</p>
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* QUIZ MODAL CONTAINER */}
        {activeQuiz && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl w-full max-w-xl shadow-2xl space-y-6">
              <div className="flex justify-between items-center pb-4 border-b border-slate-800">
                <h3 className="text-xl font-bold text-gray-100 uppercase">Adaptive Assessment Check: {quizConcept.replace('_', ' ')}</h3>
                <button 
                  onClick={() => setActiveQuiz(null)}
                  className="text-gray-400 hover:text-white font-bold"
                >
                  Close
                </button>
              </div>

              {!quizResult ? (
                <div className="space-y-6">
                  {activeQuiz.map((q, idx) => (
                    <div key={q.id} className="space-y-3">
                      <p className="text-sm font-bold text-gray-300">{idx+1}. {q.question}</p>
                      
                      {q.type === 'coding' ? (
                        <div className="space-y-2">
                          <pre className="text-xs p-3 bg-slate-950 rounded-xl border border-slate-800 text-indigo-300 font-mono">{q.template}</pre>
                          <textarea 
                            onChange={e => setQuizAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
                            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-gray-200 focus:outline-none focus:border-indigo-500" 
                            rows={3}
                            placeholder="Write code response snippet..."
                          />
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 gap-2">
                          {q.options?.map((opt: string) => (
                            <label key={opt} className="flex items-center gap-3 p-3 bg-slate-950/60 hover:bg-slate-950 border border-slate-850 rounded-xl text-xs cursor-pointer">
                              <input 
                                type="radio" 
                                name={`q-${q.id}`} 
                                value={opt}
                                onChange={e => setQuizAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
                                className="accent-indigo-500"
                              />
                              {opt}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}

                  <button 
                    onClick={submitQuizAnswers}
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs transition-all"
                  >
                    Submit Answers to Digital Twin
                  </button>
                </div>
              ) : (
                <div className="space-y-6 text-center">
                  <div className="p-4 bg-indigo-950/60 rounded-xl border border-indigo-850">
                    <p className="text-xs text-gray-400 font-bold uppercase">SCORE ACHIEVED</p>
                    <p className="text-5xl font-black text-indigo-400 mt-1">{intPercent(quizResult.score)}%</p>
                    <p className="text-[10px] text-emerald-400 mt-2 font-bold">SM-2 Spaced Interval: Grade {quizResult.grade_sm2}/5</p>
                  </div>

                  <div className="text-left space-y-3">
                    <h4 className="text-xs font-bold text-slate-400 uppercase">Question Breakdown</h4>
                    {Object.entries(quizResult.feedback).map(([q_id, feed]: any) => (
                      <div key={q_id} className={`p-3 rounded-lg border text-xs ${feed.status === 'correct' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                        <p className="font-bold uppercase">Question ID: {q_id} - {feed.status}</p>
                        <p className="mt-1 opacity-90">{feed.explanation}</p>
                      </div>
                    ))}
                  </div>

                  <button 
                    onClick={() => {
                      setActiveQuiz(null);
                      setQuizResult(null);
                    }}
                    className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-gray-300 font-bold rounded-xl text-xs transition-all"
                  >
                    Finish Verification
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: AI MENTOR PANEL */}
        {activeTab === 'mentor' && (
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight">AI Cognitive Mentor</h1>
              <p className="text-gray-400 text-sm mt-1">Tailored advice utilizing active Knowledge, Skills, and memory profiles.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* Chat panel */}
              <div className="lg:col-span-2 glass-panel rounded-2xl flex flex-col h-[500px]">
                
                {/* Messages scroll box */}
                <div className="flex-1 p-6 overflow-y-auto space-y-4">
                  {chatMessages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-md p-4 rounded-2xl text-xs leading-relaxed ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-gray-200 rounded-tl-none border border-slate-750'}`}>
                        <p className="font-bold text-[9px] opacity-60 mb-1 uppercase tracking-wider">{m.role === 'user' ? 'User Identity' : 'Cognitive AI Mentor'}</p>
                        <div className="whitespace-pre-line">{m.content}</div>
                      </div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="flex justify-start">
                      <div className="bg-slate-800/60 text-gray-400 p-4 rounded-xl text-xs flex items-center gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" /> Thinking... Ingesting Twin parameters...
                      </div>
                    </div>
                  )}
                </div>

                {/* Form Input */}
                <form onSubmit={sendMentorMessage} className="p-4 border-t border-slate-800 bg-slate-950/60 rounded-b-2xl flex gap-3">
                  <input 
                    type="text" 
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    className="flex-1 px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                    placeholder="Ask about your study plan, weaknesses or carrier alignment..."
                  />
                  <button 
                    type="submit"
                    className="px-6 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs transition-all flex items-center gap-1.5"
                  >
                    Send Context
                  </button>
                </form>
              </div>

              {/* Explainable AI Dashboard Sidepanel */}
              <div className="glass-panel p-6 rounded-2xl space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-gray-200 flex items-center gap-2">
                    <BarChart2 className="w-5 h-5 text-indigo-400" /> Explainable Prompt Logs
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">Visual proof detailing the exact Digital Twin parameters injected as context.</p>
                </div>

                {injectedTwin ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-indigo-950/60 rounded-xl border border-indigo-850 space-y-3">
                      <h4 className="text-xs font-bold text-indigo-300 uppercase">Context Parameters Injected</h4>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                          <span className="text-gray-500 font-semibold block uppercase text-[8px]">Dominant Style</span>
                          <span className="font-bold text-gray-300 capitalize">{injectedTwin.dominant_style}</span>
                        </div>
                        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                          <span className="text-gray-500 font-semibold block uppercase text-[8px]">Career Target</span>
                          <span className="font-bold text-gray-300 truncate block">{injectedTwin.target_role}</span>
                        </div>
                        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                          <span className="text-gray-500 font-semibold block uppercase text-[8px]">Career Readiness</span>
                          <span className="font-bold text-gray-300">{intPercent(injectedTwin.readiness_score)}%</span>
                        </div>
                        <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                          <span className="text-gray-500 font-semibold block uppercase text-[8px]">Weakness Bottlenecks</span>
                          <span className="font-bold text-gray-300">{injectedTwin.weaknesses_count} Concepts</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2 text-xs">
                      <div className="flex gap-2">
                        <span className="font-extrabold text-[10px] text-indigo-400 uppercase">Evidence:</span>
                        <span className="text-gray-400">Queried databases containing User node masteries and SM-2 logs.</span>
                      </div>
                      <div className="flex gap-2">
                        <span className="font-extrabold text-[10px] text-emerald-400 uppercase">Reasoning:</span>
                        <span className="text-gray-400">Injected twin states into LLM agent to enforce contextual guidance constraints.</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-gray-500 leading-relaxed text-center py-12">
                    <HelpCircle className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                    Send a message to see the active twin context variables mapped dynamically!
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* TAB 4: SIMULATOR */}
        {activeTab === 'simulator' && (
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight">Cognitive Growth Simulator</h1>
              <p className="text-gray-400 text-sm mt-1">Run forward Monte Carlo projections of your masteries and forgetting intervals under custom regimes.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* Sliders Configuration */}
              <div className="glass-panel p-6 rounded-2xl space-y-6">
                <h3 className="text-lg font-bold text-gray-200">Simulation Variables</h3>
                
                <div className="space-y-4 text-xs font-semibold">
                  
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <label className="text-gray-400">DAILY STUDY MINUTES</label>
                      <span className="text-indigo-400 font-bold">{simMinutes} Mins</span>
                    </div>
                    <input 
                      type="range" 
                      min="10" 
                      max="180" 
                      step="5"
                      value={simMinutes}
                      onChange={e => setSimMinutes(parseInt(e.target.value))}
                      className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-gray-400 block mb-1">PRACTICE DENSITY FREQUENCY</label>
                    <select 
                      value={simPractice}
                      onChange={e => setSimPractice(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                    >
                      <option value="never">Never (Theory Only)</option>
                      <option value="weekly">Weekly Practice Weekend Checkpoints</option>
                      <option value="daily">Daily Coding Sandbox Workload</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-gray-400 block mb-1">LEARNING STRATEGY MODEL</label>
                    <select 
                      value={simStrategy}
                      onChange={e => setSimStrategy(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                    >
                      <option value="mixed">Mixed Balanced Style</option>
                      <option value="project">Project Sandbox Heavy (Practical)</option>
                      <option value="visual">Visual Animation Heavy (Intuitive)</option>
                    </select>
                  </div>

                  <label className="flex items-center gap-3 p-3 bg-slate-950 rounded-xl border border-slate-850 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={simSkipRevision}
                      onChange={e => setSimSkipRevision(e.target.checked)}
                      className="accent-indigo-500 rounded"
                    />
                    <div>
                      <p className="text-xs font-bold text-gray-300">Skip Spaced Revisions</p>
                      <p className="text-[10px] text-slate-500 mt-0.5 leading-tight">Neglect SM-2 schedules, causing exponential decay.</p>
                    </div>
                  </label>

                </div>

                <button 
                  onClick={runSimulator}
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-xl text-xs transition-all"
                >
                  Run Simulation Projections
                </button>
              </div>

              {/* Projections View Graphs */}
              <div className="lg:col-span-2 space-y-6">
                {simResult ? (
                  <div className="glass-panel p-6 rounded-2xl space-y-6">
                    <div className="flex justify-between items-center pb-4 border-b border-slate-800">
                      <h3 className="text-lg font-bold text-gray-200">Trajectory Forecast (12 Months)</h3>
                      <div className="flex gap-4 text-xs font-bold">
                        <span className="text-indigo-400">Final Mastery: {intPercent(simResult.final_mastery)}%</span>
                        <span className="text-emerald-400">Final Retention: {intPercent(simResult.final_retention)}%</span>
                      </div>
                    </div>

                    <SimpleLineChart data={simResult.time_series} />

                    {/* Bottlenecks prediction alerts */}
                    {simResult.predicted_weaknesses?.length > 0 && (
                      <div className="space-y-3 pt-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Projected Weakness Vulnerabilities</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {simResult.predicted_weaknesses.map((w: string, i: number) => (
                            <div key={i} className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl flex gap-2">
                              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                              <span className="font-semibold">{w}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Explanations block */}
                    <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-850 text-xs leading-relaxed space-y-2">
                      <p className="font-bold text-indigo-400">Explainable Analysis:</p>
                      <p className="text-gray-300 font-medium">{simResult.explaination.analysis}</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2 pt-2 border-t border-slate-900">
                        <div>
                          <p className="text-[10px] text-emerald-400 font-bold uppercase">ADVANTAGES</p>
                          <ul className="list-disc pl-4 space-y-1 mt-1 text-gray-400">
                            {simResult.explaination.advantages.map((adv: string, i: number) => <li key={i}>{adv}</li>)}
                          </ul>
                        </div>
                        <div>
                          <p className="text-[10px] text-red-400 font-bold uppercase">DISADVANTAGES</p>
                          <ul className="list-disc pl-4 space-y-1 mt-1 text-gray-400">
                            {simResult.explaination.disadvantages.map((dis: string, i: number) => <li key={i}>{dis}</li>)}
                          </ul>
                        </div>
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="glass-panel p-12 rounded-2xl text-center text-gray-400 h-64 flex flex-col justify-center items-center">
                    <Activity className="w-8 h-8 text-indigo-400 mb-2" />
                    <p className="font-semibold text-sm">Simulator Awaiting Trigger</p>
                    <p className="text-xs mt-1">Configure variables and click Run Simulation.</p>
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* TAB 5: DECISIONS */}
        {activeTab === 'decisions' && (
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight">Decision Intelligence Register</h1>
              <p className="text-gray-400 text-sm mt-1">Add details of engineering or architecture choices. The engine scans logs to expose heuristics & cognitive bias.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* Form panel */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <h3 className="text-lg font-bold text-gray-200">Log New Decision</h3>
                
                {decisionSuccess && (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-lg text-center font-bold">
                    Decision logged. Analytics updated.
                  </div>
                )}

                <form onSubmit={logDecision} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 mb-1">DECISION TITLE</label>
                    <input 
                      type="text" 
                      value={decisionTitle}
                      onChange={e => setDecisionTitle(e.target.value)}
                      className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs" 
                      placeholder="e.g. AWS vs GCP for clusters" 
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 mb-1">CHOICE MADE</label>
                    <input 
                      type="text" 
                      value={decisionChoice}
                      onChange={e => setDecisionChoice(e.target.value)}
                      className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs" 
                      placeholder="e.g. Google Cloud Run" 
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 mb-1">DESCRIPTION</label>
                    <textarea 
                      value={decisionDesc}
                      onChange={e => setDecisionDesc(e.target.value)}
                      className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs" 
                      rows={3} 
                      placeholder="Context details..."
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 mb-1">RISK TOLERANCE</label>
                      <select 
                        value={decisionRisk}
                        onChange={e => setDecisionRisk(e.target.value)}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                      >
                        <option value="low">Low Risk</option>
                        <option value="medium">Medium Risk</option>
                        <option value="high">High Risk</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 mb-1">CONFIDENCE</label>
                      <input 
                        type="number" 
                        step="0.05"
                        min="0.1"
                        max="1.0"
                        value={decisionConfidence}
                        onChange={e => setDecisionConfidence(parseFloat(e.target.value))}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 mb-1">EVIDENCE ITEMS (COMMA SEPARATED)</label>
                    <input 
                      type="text" 
                      value={decisionEvidence}
                      onChange={e => setDecisionEvidence(e.target.value)}
                      className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs" 
                      placeholder="item1, item2" 
                    />
                  </div>

                  <button 
                    type="submit" 
                    className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-lg text-xs transition-all"
                  >
                    Commit to Decision Engine
                  </button>
                </form>
              </div>

              {/* History list */}
              <div className="lg:col-span-2 space-y-4 max-h-[550px] overflow-y-auto pr-2">
                {decisionLogs.map((log: any) => (
                  <div key={log.id} className="glass-panel p-5 rounded-2xl space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-sm text-gray-200">{log.title}</h4>
                        <p className="text-[10px] text-gray-500 mt-0.5">Logged: {new Date(log.created_at).toLocaleDateString()}</p>
                      </div>
                      <span className={`px-2 py-0.5 text-[9px] font-extrabold uppercase rounded ${log.risk_level === 'high' ? 'bg-red-500/15 text-red-400' : 'bg-emerald-500/15 text-emerald-400'}`}>{log.risk_level} Risk</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <p className="text-[9px] text-gray-500 font-bold">CHOICE DECIDED</p>
                        <p className="font-semibold text-indigo-300 mt-0.5">{log.choice_made}</p>
                      </div>
                      <div>
                        <p className="text-[9px] text-gray-500 font-bold">EVIDENCE COLLECTED</p>
                        <p className="font-semibold text-emerald-300 mt-0.5">{log.evidence_collected?.length || 0} Factors</p>
                      </div>
                    </div>

                    {/* Detected bias warning checks */}
                    {log.bias_detected && Object.keys(log.bias_detected).length > 0 && (
                      <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs rounded-xl flex gap-2">
                        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold uppercase text-[9px]">Potential Bias Check Flagged</p>
                          {Object.entries(log.bias_detected).map(([key, value]: any) => (
                            <p key={key} className="text-[10px] mt-0.5">{value.description}</p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

            </div>
          </div>
        )}

        {/* TAB 6: REFLECTIONS */}
        {activeTab === 'reflections' && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-extrabold tracking-tight">Growth Reflection Logs</h1>
                <p className="text-gray-400 text-sm mt-1">Review summaries of cognitive improvement, streak achievements, and action tasks.</p>
              </div>
              <div className="flex gap-3">
                <button 
                  onClick={() => triggerReflection('daily')}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-all"
                >
                  Compile Daily Reflection
                </button>
                <button 
                  onClick={() => triggerReflection('weekly')}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg transition-all"
                >
                  Compile Weekly Reflection
                </button>
              </div>
            </div>

            {reflectionSuccess && (
              <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs rounded-lg text-center font-bold">
                {reflectionSuccess}
              </div>
            )}

            <div className="space-y-4">
              {reflectionLogs.map((log: any) => (
                <div key={log.id} className="glass-panel p-6 rounded-2xl space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <span className="px-2.5 py-0.5 bg-indigo-500/20 text-indigo-300 text-[10px] uppercase font-black rounded-md">{log.reflection_type} Reflection</span>
                    <span className="text-xs text-gray-500 font-medium">Logged on: {new Date(log.reflection_date).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-line">{log.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 7: COGNITIVE ARENA */}
        {activeTab === 'arena' && (
          <div className="space-y-8 animate-fadeIn">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight">Cognitive Decision Arena</h1>
              <p className="text-gray-400 text-sm mt-1">Stress-test your system design and engineering decision workflows against common heuristic biases.</p>
            </div>

            {!activeScenario ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {arenaScenarios.map((sc: any) => (
                  <div key={sc.id} className="glass-panel p-6 rounded-2xl flex flex-col justify-between space-y-4 border border-slate-800 hover:border-indigo-500/50 transition-all duration-300">
                    <div className="space-y-2">
                      <div className="p-2 bg-indigo-500/10 text-indigo-400 w-10 h-10 rounded-xl flex items-center justify-center font-bold">
                        <Target className="w-5 h-5" />
                      </div>
                      <h3 className="text-lg font-bold text-gray-200">{sc.title}</h3>
                      <p className="text-xs text-gray-400 leading-relaxed">{sc.description}</p>
                    </div>
                    <button 
                      onClick={() => startArenaScenario(sc)}
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs transition-all flex items-center justify-center gap-2"
                    >
                      <Play className="w-4 h-4" /> Enter Scenario
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Active Game Window */}
                <div className="lg:col-span-2 glass-panel p-6 rounded-2xl space-y-6 flex flex-col justify-between min-h-[450px]">
                  
                  {!arenaResult ? (
                    <div className="space-y-6">
                      {/* Step Indicator */}
                      <div className="flex justify-between items-center pb-4 border-b border-slate-800">
                        <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">
                          Step {arenaStepIndex + 1} of {activeScenario.steps.length}
                        </span>
                        <span className="text-xs text-gray-550 flex items-center gap-1.5 font-semibold">
                          <Activity className="w-4 h-4 text-emerald-400" /> Outage Timer Active
                        </span>
                      </div>

                      {/* Scenario Situation */}
                      <div className="space-y-2">
                        <p className="text-sm font-bold text-gray-200 leading-relaxed">
                          {activeScenario.steps[arenaStepIndex].situation}
                        </p>
                      </div>

                      {/* Evidence Gathering Section */}
                      <div className="space-y-3">
                        <h4 className="text-xs font-extrabold text-gray-400 uppercase tracking-wider">
                          Uncover Diagnostic Evidence (Optional)
                        </h4>
                        <p className="text-[10px] text-gray-550">Click to reveal details. Each clue read adds evidence points but increases time spent.</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {activeScenario.steps[arenaStepIndex].clues.map((clue: any) => {
                            const isRevealed = arenaEvidence.includes(clue.id);
                            return (
                              <div 
                                key={clue.id}
                                onClick={() => handleArenaClueClick(clue.id)}
                                className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${isRevealed ? 'bg-slate-900/80 border-indigo-500/30' : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700'}`}
                              >
                                <div className="flex justify-between items-center">
                                  <span className="font-bold text-gray-300">{clue.title}</span>
                                  {isRevealed ? (
                                    <span className="text-[9px] text-indigo-400 font-extrabold uppercase bg-indigo-500/10 px-1.5 py-0.5 rounded">Revealed</span>
                                  ) : (
                                    <span className="text-[9px] text-gray-500 font-extrabold uppercase bg-slate-800 px-1.5 py-0.5 rounded">Click to inspect</span>
                                  )}
                                </div>
                                {isRevealed && (
                                  <p className="mt-2 text-[11px] text-gray-400 leading-relaxed font-medium">
                                    {clue.content}
                                  </p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Choices */}
                      <div className="space-y-3">
                        <h4 className="text-xs font-extrabold text-gray-400 uppercase tracking-wider">
                          Select Decisive Action
                        </h4>
                        <div className="grid grid-cols-1 gap-2.5">
                          {activeScenario.steps[arenaStepIndex].options.map((opt: any) => (
                            <button 
                              key={opt.id}
                              onClick={() => handleArenaSubmitStep(opt.id)}
                              disabled={arenaSubmitting}
                              className="w-full text-left p-3.5 bg-slate-950 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 rounded-xl text-xs text-gray-300 font-medium transition-all flex justify-between items-center group"
                            >
                              <span>{opt.text}</span>
                              <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-indigo-400 transition-all" />
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Confidence Slider */}
                      <div className="space-y-2 pt-2 border-t border-slate-800/60">
                        <div className="flex justify-between text-xs font-semibold">
                          <label className="text-gray-400 uppercase">Rate Your Decision Confidence</label>
                          <span className="text-indigo-400 font-bold">{Math.round(arenaConfidence * 100)}% Confidence</span>
                        </div>
                        <input 
                          type="range" 
                          min="0.1" 
                          max="1.0" 
                          step="0.05"
                          value={arenaConfidence}
                          onChange={e => setArenaConfidence(parseFloat(e.target.value))}
                          className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-6 text-center py-6">
                      <div className="p-5 bg-indigo-950/40 rounded-2xl border border-indigo-850 max-w-md mx-auto">
                        <p className="text-[10px] text-gray-400 font-bold uppercase">DECISION QUALITY SCORE</p>
                        <p className="text-6xl font-black text-indigo-400 mt-1">{Math.round(arenaResult.score * 100)}%</p>
                      </div>

                      <div className="text-left space-y-4">
                        <h4 className="text-sm font-bold text-gray-300 border-b border-slate-800 pb-2">Cognitive Analysis Report</h4>
                        <p className="text-xs text-gray-450 leading-relaxed whitespace-pre-line">
                          {arenaResult.feedback}
                        </p>
                        <div className="text-[11px] text-gray-500 space-y-1">
                          <p><span className="font-extrabold text-indigo-400">EVIDENCE:</span> {arenaResult.explanation.evidence}</p>
                          <p><span className="font-extrabold text-emerald-400">REASONING:</span> {arenaResult.explanation.reasoning}</p>
                        </div>
                      </div>

                      <button 
                        onClick={() => {
                          setActiveScenario(null);
                          setArenaResult(null);
                        }}
                        className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-gray-200 font-bold rounded-xl text-xs transition-all"
                      >
                        Finish and Exit Scenario
                      </button>
                    </div>
                  )}

                  {arenaError && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl text-center">
                      {arenaError}
                    </div>
                  )}
                </div>

                {/* Dashboard Metrics Sidepanel */}
                <div className="glass-panel p-6 rounded-2xl space-y-6 flex flex-col justify-between">
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-bold text-gray-200 flex items-center gap-2">
                        <BarChart2 className="w-5 h-5 text-indigo-400" /> Cognitive Radar Map
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">Real-time parameters of active heuristic biases.</p>
                    </div>

                    {arenaResult ? (
                      <ArenaRadarChart metrics={arenaResult.metrics} />
                    ) : twin?.state?.decision_profile ? (
                      <ArenaRadarChart metrics={twin.state.decision_profile} />
                    ) : (
                      <div className="text-center py-12 text-xs text-gray-500">
                        <HelpCircle className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                        Complete a scenario to map your decision heuristics.
                      </div>
                    )}

                    {/* Bias Warnings Alert */}
                    {arenaResult?.biases_detected && Object.keys(arenaResult.biases_detected).length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider">Heuristic Biases Flagged</h4>
                        <div className="space-y-2">
                          {Object.entries(arenaResult.biases_detected).map(([key, bias]: any) => (
                            <div key={key} className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs rounded-xl flex gap-2">
                              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                              <div>
                                <p className="font-bold capitalize">{key.replace('_', ' ')} (Severity: {Math.round(bias.severity * 100)}%)</p>
                                <p className="text-[10px] text-amber-400/80 mt-1">{bias.description}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="text-[10px] text-gray-550 bg-slate-950/40 p-3 rounded-xl border border-slate-900 leading-relaxed">
                    <strong>Mitigation Suggestion:</strong> To reduce overconfidence bias, actively seek disconfirming data before finalizing production modifications.
                  </div>
                </div>

              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}

// Helpers
function roundTo(num: number, dec: number) {
  return parseFloat(num.toFixed(dec));
}
function intPercent(num: number) {
  return Math.round(num * 100);
}
function ArenaRadarChart({ metrics }: { metrics: Record<string, number> }) {
  const cx = 150;
  const cy = 150;
  const r = 100;
  
  const keys = [
    { label: "Analytical", key: "analytical_thinking" },
    { label: "Risk Appetite", key: "risk_tolerance" },
    { label: "Impulsiveness", key: "impulsiveness" },
    { label: "Sunk Cost", key: "sunk_cost" },
    { label: "Confirmation Bias", key: "confirmation_bias" },
    { label: "Overconfidence", key: "overconfidence" }
  ];
  
  // Outer polygon and grid lines
  const gridLevels = [0.25, 0.5, 0.75, 1.0];
  const gridPolygons = gridLevels.map(level => {
    return keys.map((_, i) => {
      const angle = (i * Math.PI) / 3 - Math.PI / 2;
      const x = cx + r * level * Math.cos(angle);
      const y = cy + r * level * Math.sin(angle);
      return `${x},${y}`;
    }).join(' ');
  });

  // User value polygon
  const valuePoints = keys.map((k, i) => {
    const val = metrics[k.key] ?? 0.5;
    const angle = (i * Math.PI) / 3 - Math.PI / 2;
    const x = cx + r * val * Math.cos(angle);
    const y = cy + r * val * Math.sin(angle);
    return `${x},${y}`;
  }).join(' ');

  // Labels coordinates
  const labels = keys.map((k, i) => {
    const angle = (i * Math.PI) / 3 - Math.PI / 2;
    const x = cx + r * 1.3 * Math.cos(angle);
    const y = cy + r * 1.15 * Math.sin(angle);
    return { label: k.label, x, y };
  });

  return (
    <svg viewBox="0 0 300 320" className="w-full max-w-xs mx-auto bg-slate-950/60 rounded-2xl p-2 border border-slate-800/80">
      {gridPolygons.map((points, idx) => (
        <polygon 
          key={idx} 
          points={points} 
          fill="none" 
          stroke="#334155" 
          strokeWidth="1" 
          strokeDasharray={idx < 3 ? "2" : "none"} 
        />
      ))}
      
      {keys.map((_, i) => {
        const angle = (i * Math.PI) / 3 - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return (
          <line 
            key={i} 
            x1={cx} 
            y1={cy} 
            x2={x} 
            y2={y} 
            stroke="#1e293b" 
            strokeWidth="1.5" 
          />
        );
      })}

      <polygon 
        points={valuePoints} 
        fill="rgba(99, 102, 241, 0.2)" 
        stroke="#6366f1" 
        strokeWidth="3" 
      />
      
      {keys.map((k, i) => {
        const val = metrics[k.key] ?? 0.5;
        const angle = (i * Math.PI) / 3 - Math.PI / 2;
        const x = cx + r * val * Math.cos(angle);
        const y = cy + r * val * Math.sin(angle);
        return (
          <circle 
            key={i} 
            cx={x} 
            cy={y} 
            r="4" 
            className="fill-indigo-400 stroke-indigo-600 stroke-2" 
          />
        );
      })}

      {labels.map((l, i) => {
        let textAnchor: "middle" | "start" | "end" = "middle";
        if (l.x > cx + 10) textAnchor = "start";
        if (l.x < cx - 10) textAnchor = "end";
        return (
          <text 
            key={i} 
            x={l.x} 
            y={l.y} 
            textAnchor={textAnchor}
            className="fill-gray-400 font-bold text-[8px] uppercase tracking-wider"
          >
            {l.label}
          </text>
        );
      })}
    </svg>
  );
}

const MOCK_SCENARIOS = [
  {
    "id": "production_outage",
    "title": "The Production Outage Panic",
    "description": "A business-critical payment processing API is dropping 45% of customer transactions. Alerts are firing. You need to triage and resolve the issue under intense time pressure without causing data corruption.",
    "steps": [
      {
        "step_id": 1,
        "situation": "Multiple customer payment requests are failing with HTTP 500 errors. The support channel is flooded. What is your first step?",
        "clues": [
          {"id": "logs", "title": "Inspect Microservice Logs", "content": "Database connection pool saturated with 150 pending transactions waiting for database locks."},
          {"id": "infra", "title": "Check Infrastructure Status", "content": "CPU usage is 18%, memory is 42% (perfectly normal)."},
          {"id": "git", "title": "Check Git Deployment History", "content": "A deployment happened 15 minutes ago by another dev, altering default database pool timeouts from 30s to 5s."}
        ],
        "options": [
          {"id": "A", "text": "Reboot all API containers immediately to clear connection pool memory state.", "risk_level": "medium", "feedback": "Containers rebooted, but database connection pool saturated again within 30 seconds. Outage continues."},
          {"id": "B", "text": "Roll back the git deployment immediately.", "risk_level": "high", "feedback": "Deployment rolled back, but database sessions are still locked by orphaned connection threads. Outage persists."},
          {"id": "C", "text": "Analyze active database connections to identify lock origins.", "risk_level": "low", "feedback": "You find a long-running migrator transaction holding an exclusive lock on the 'transactions' table."}
        ]
      },
      {
        "step_id": 2,
        "situation": "You've identified that a background data-migration job (running on a backup thread) is holding a lock on the 'transactions' table. The migration has been running for 4.2 hours and is 90% complete. What do you do?",
        "clues": [
          {"id": "migration_code", "title": "Inspect Migration Script", "content": "The script runs within a single large transaction block. Terminating it forcefully will trigger a rollback that may take up to an hour."},
          {"id": "traffic", "title": "Analyze Live Traffic Patterns", "content": "90% of failures are retries. Rate-limiting incoming retries would alleviate server overload."}
        ],
        "options": [
          {"id": "A", "text": "Kill the PostgreSQL process ID (PID) of the migration job immediately.", "risk_level": "high", "feedback": "Process terminated. Postgres starts rolling back the uncommitted transaction. Database remains locked and unresponsive."},
          {"id": "B", "text": "Enable temporary API rate-limiting and wait for the migration to finish gracefully (estimated 15 minutes).", "risk_level": "low", "feedback": "Temporary rate-limits reduce database load. 12 minutes later, the migration completes, locks release, and traffic flows normally."},
          {"id": "C", "text": "Pause the database server and perform an emergency database scaling operation.", "risk_level": "high", "feedback": "Database restarted and instance size scaled up. However, upon boot, Postgres still enters crash recovery to roll back the migrator task, keeping locks held."}
        ]
      },
      {
        "step_id": 3,
        "situation": "With the database locks finally released and transactions flowing again, how do you prevent this issue in the post-mortem phase?",
        "clues": [
          {"id": "db_config", "title": "Inspect DB Locks Configuration", "content": "Postgres default lock wait timeout is unlimited, meaning a migrator will block all read/write clients forever if it gets stuck."},
          {"id": "docs", "title": "Review Engineering Playbook", "content": "Playbook suggests always wrapping schema migrations in dry-run checks and locking timeouts."}
        ],
        "options": [
          {"id": "A", "text": "Deploy a quick patch to set lock_timeout = 10000 (10s) globally on the database.", "risk_level": "medium", "feedback": "Patch deployed. Fast and dirty, but setting global database timeouts might break valid long-running analytical queries later."},
          {"id": "B", "text": "Establish a policy: all schema migrations must run in tiny batched transactions with dedicated statement timeouts.", "risk_level": "low", "feedback": "Perfect. Migrations are now decoupled and non-blocking, ensuring safe and resilient continuous delivery."},
          {"id": "C", "text": "Upgrade the database replica count and blame the cloud provider's network delay in the incident report.", "risk_level": "low", "feedback": "Incident report closed, but core locking issue is unaddressed. High likelihood of recurrence."}
        ]
      }
    ]
  },
  {
    "id": "legacy_refactoring",
    "title": "The Legacy Refactoring Trap",
    "description": "Your core subscription billing engine is 8 years old, written in procedural PHP. Your team has spent 9 months refactoring it to a microservices architecture. It has blown past its budget, is still buggy, and is delaying crucial new features.",
    "steps": [
      {
        "step_id": 1,
        "situation": "The business demands that you ship 'Enterprise Custom Tiers' in 4 weeks. Your refactored billing service is only 75% complete and is failing edge-case tax audits. The team is exhausted. What do you do?",
        "clues": [
          {"id": "budget", "title": "Check Budget Spent", "content": "95% of the refactoring budget has been exhausted. Sunk cost is $120,000."},
          {"id": "diff", "title": "Examine Code Complexity", "content": "The legacy billing file is 14,000 lines long, but handles custom enterprise tiers using simple database column overrides."}
        ],
        "options": [
          {"id": "A", "text": "Double down: pause all new feature requests and commit 100% team bandwidth to complete the refactored billing microservice.", "risk_level": "high", "feedback": "You commit more resources, but the complexity of edge-case tax calculations continues to push back completion. The business misses the custom tiers deadline."},
          {"id": "B", "text": "Implement the 'Enterprise Custom Tiers' inside the legacy engine directly as a fast patch, while keeping the refactor on a low-priority background thread.", "risk_level": "low", "feedback": "Feature shipped on time using legacy overrides. Business objectives met, and team gets breathing room to properly solve the refactoring challenges."},
          {"id": "C", "text": "Hire an external agency to write the remaining 25% of the refactored microservice.", "risk_level": "medium", "feedback": "Agency onboarded. They take 3 weeks just to understand the architecture, exceeding budget, and deliver code that still fails tax checks."}
        ]
      },
      {
        "step_id": 2,
        "situation": "A junior engineer suggests scrapping the refactored billing service altogether and using a third-party billing platform (e.g. Stripe Billing) to handle all custom and standard tiers, which would replace 90% of local code.",
        "clues": [
          {"id": "cost", "title": "Review Third-Party Fees", "content": "Stripe charges 0.5% per invoice. Your current transaction volume means transaction fees will cost $4,000/month, but saves 1 full-time dev salary ($10,000/month)."},
          {"id": "migration", "title": "Examine Migration Effort", "content": "Integrating Stripe Billing takes 3 weeks of API work and supports all tax edge-cases automatically."}
        ],
        "options": [
          {"id": "A", "text": "Reject third-party tools. 'We spent 9 months building our custom system, we should not throw away our hard work.'", "risk_level": "medium", "feedback": "Refuse to migrate. The custom billing engine drags on, consuming developer maintenance hours indefinitely."},
          {"id": "B", "text": "Initiate a migration to Stripe Billing, writing off the 9-month refactor as a learning experience.", "risk_level": "low", "feedback": "Migration successfully completed in 3 weeks. Developer workload drops, allowing focus on core product features."},
          {"id": "C", "text": "Build a wrapper that tries to sync the half-finished custom microservice with Stripe Billing in parallel.", "risk_level": "high", "feedback": "Sync complexity leads to double-billing bugs and severe customer complaints. High risk realized."}
        ]
      },
      {
        "step_id": 3,
        "situation": "After resolving the refactoring dilemma, you need to set up a legacy refactoring decision framework. How do you assess future 're-write' proposals?",
        "clues": [
          {"id": "industry", "title": "Check Refactoring Standards", "content": "Industry data shows 70% of complete system rewrites exceed time estimations by over 100%."}
        ],
        "options": [
          {"id": "A", "text": "Mandate that no rewrites are allowed. All legacy systems must be patched forever.", "risk_level": "low", "feedback": "Technical debt accumulates until the application becomes completely unmaintainable years later."},
          {"id": "B", "text": "Implement a Strangler Fig Application Pattern rule: all rewrites must be done incrementally, feature by feature, behind a routing proxy.", "risk_level": "low", "feedback": "Excellent policy. Promotes iterative, low-risk modular modernization."},
          {"id": "C", "text": "Approve rewrites based on developer excitement and stack modernization desires.", "risk_level": "high", "feedback": "Leading to constant churn of half-finished frameworks and unstable architectures."}
        ]
      }
    ]
  },
  {
    "id": "architecture_choice",
    "title": "The Hype-Driven Architecture Dilemma",
    "description": "A new decentralized serverless database technology is trending. It promises 10x write performance. The development team is highly eager to adopt it for a standard relational Customer Relationship Management (CRM) project.",
    "steps": [
      {
        "step_id": 1,
        "situation": "The CRM project requires standard complex relational queries (e.g. joins, nested filters, transactional safety). The team wants to use the new serverless DB. What is your evaluation strategy?",
        "clues": [
          {"id": "spec", "title": "Check Database Spec", "content": "The database is non-relational, lacks transactional ACID guarantees, and doesn't support joins natively."},
          {"id": "community", "title": "Evaluate Ecosystem Activity", "content": "The database has only 1.2k stars on GitHub and has zero production case-studies outside of developer blogs."}
        ],
        "options": [
          {"id": "A", "text": "Adopt the serverless database to make the stack modern and attract talent.", "risk_level": "high", "feedback": "Database adopted. The team struggles to implement relational joins in application code, dragging down performance and velocity."},
          {"id": "B", "text": "Stick with PostgreSQL. Relational databases are a proven fit for CRM workloads.", "risk_level": "low", "feedback": "PostgreSQL adopted. Joins and queries are executed in microseconds with solid transactional integrity."},
          {"id": "C", "text": "Run a 2-day hackathon benchmark comparing PostgreSQL with the new database on CRM query shapes.", "risk_level": "low", "feedback": "Benchmark reveals that while writes are fast, complex reads are 25x slower due to manual application joins. The team agrees to stick with SQL."}
        ]
      },
      {
        "step_id": 2,
        "situation": "Your choice of PostgreSQL is finalized, but the team now wants to implement a highly complex microservices architecture (splitting CRM into 12 services) with Kubernetes orchestration, for a system expected to serve 500 active users.",
        "clues": [
          {"id": "ops", "title": "Analyze Ops Overhead", "content": "Managing Kubernetes for a small user base consumes 40% of operations capacity. A single monolithic backend takes 5% of ops capacity."},
          {"id": "perf_scale", "title": "Check Load Projections", "content": "500 active users will produce peak load of 10 requests per second, which a single virtual machine ($10/month) can handle at 5% CPU."}
        ],
        "options": [
          {"id": "A", "text": "Approve Kubernetes microservices. 'We must build for scale from day one.'", "risk_level": "high", "feedback": "System is highly complex. Developers spend more time fixing Kubernetes network configurations than shipping product features."},
          {"id": "B", "text": "Build a modular monolith and host it on a single Docker-compose virtual machine with automated backups.", "risk_level": "low", "feedback": "System is simple, robust, and fast. Operational overhead is virtually zero, allowing developers to ship features daily."},
          {"id": "C", "text": "Adopt serverless functions (lambda) for every single API endpoint.", "risk_level": "medium", "feedback": "Lambda functions suffer from cold starts and database connection saturation due to lack of a shared pool, causing random lag spikes."}
        ]
      },
      {
        "step_id": 3,
        "situation": "Months later, the project is a success. The team wants to incorporate machine learning (LLM-based lead scoring). How do you integrate it?",
        "clues": [
          {"id": "ml_needs", "title": "Evaluate ML Requirements", "content": "A simple heuristic scoring system (assigning points based on job title/company size) works in 95% of cases. Training an LLM classifier costs $15,000 in GPU time."}
        ],
        "options": [
          {"id": "A", "text": "Deploy a local PyTorch neural network lead classifier.", "risk_level": "medium", "feedback": "Neural network works, but requires continuous fine-tuning and debugging, creating support overhead."},
          {"id": "B", "text": "Start with a simple relational database SQL query scoring heuristic, and only build ML models if data shows the heuristic is failing.", "risk_level": "low", "feedback": "The heuristic works perfectly, takes 2 hours to code, costs zero dollars, and is instantly transparent to business analysts."},
          {"id": "C", "text": "Integrate a paid third-party enterprise AI CRM platform API.", "risk_level": "low", "feedback": "API works but adds monthly subscription fees, reducing margins for a feature that could be solved locally."}
        ]
      }
    ]
  }
];

function getMockFallbackData(endpoint: string, options: any) {
  const e = endpoint.toLowerCase();
  
  if (e.includes("/auth/login")) {
    return { "access_token": "mock_static_demo_token" };
  }
  if (e.includes("/auth/register")) {
    return { "status": "success" };
  }
  
  if (e.includes("/twin")) {
    return {
      "id": 1,
      "user_id": 1,
      "updated_at": "2026-07-19T10:00:00Z",
      "state": {
        "learning_dna": {
          "visual": {"score": 0.72, "confidence": 0.85},
          "reading": {"score": 0.45, "confidence": 0.7},
          "project": {"score": 0.88, "confidence": 0.9},
          "discussion": {"score": 0.6, "confidence": 0.8}
        },
        "memory_profile": {
          "overall_retention": 0.84,
          "recall_speed_score": 0.78,
          "average_decay_rate": 0.042,
          "revision_delay_adherence": 0.88
        },
        "skills": {
          "programming": {"level": 0.85, "confidence": 0.9},
          "problem_solving": {"level": 0.8, "confidence": 0.85},
          "system_design": {"level": 0.7, "confidence": 0.8},
          "data_structures": {"level": 0.75, "confidence": 0.85}
        },
        "habits": {
          "study_streak": 5,
          "total_focus_hours": 42.5,
          "revision_delay_adherence": 0.88
        },
        "decision_profile": {
          "risk_tolerance": 0.5,
          "analytical_thinking": 0.75,
          "intuition": 0.5,
          "evidence_collection_speed": 0.5,
          "decision_speed": 0.65,
          "bias_index": 0.15,
          "consistency": 0.8,
          "tradeoff_handling": 0.5,
          "decision_confidence": 0.8
        }
      }
    };
  }
  
  if (e.includes("/learning/plan")) {
    return {
      "style_fit_explanation": "Based on your high project and visual preferences, we suggest hands-on execution and graphical walkthroughs.",
      "daily_plan": [
        {
          "type": "practice",
          "duration_est": "30 mins",
          "title": "Implement Neural Network Forward Pass",
          "description": "Code a clean forward propagation loop from scratch using raw numpy arrays."
        },
        {
          "type": "revision",
          "duration_est": "15 mins",
          "title": "Recall Backpropagation Gradient Flow",
          "description": "Quick check on gradient flow bottlenecks and vanishing gradient nodes."
        }
      ]
    };
  }
  
  if (e.includes("/predictions")) {
    return {
      "burnout_risk": 0.12,
      "velocity_score": 0.85,
      "forgetting_rate_monthly": 0.08,
      "predicted_concepts_to_forget": ["backpropagation", "learning_rates"],
      "readiness_career": {"AI Engineer": 0.75, "Data Scientist": 0.65},
      "explanations": {}
    };
  }
  
  if (e.includes("/knowledge/graph")) {
    return {
      "nodes": [
        {"id": "python_basics", "data": {"title": "Python Basics", "mastery": 0.95, "status": "mastered", "difficulty": 1.0}, "position": {"x": 150, "y": 100}},
        {"id": "numpy_arrays", "data": {"title": "NumPy Arrays", "mastery": 0.85, "status": "mastered", "difficulty": 2.0}, "position": {"x": 300, "y": 100}},
        {"id": "calculus", "data": {"title": "Calculus Foundations", "mastery": 0.7, "status": "in_progress", "difficulty": 3.0}, "position": {"x": 200, "y": 250}},
        {"id": "neural_networks", "data": {"title": "Neural Networks", "mastery": 0.4, "status": "in_progress", "difficulty": 4.0}, "position": {"x": 500, "y": 200}}
      ],
      "edges": [
        {"id": "e1", "source": "python_basics", "target": "numpy_arrays"},
        {"id": "e2", "source": "numpy_arrays", "target": "neural_networks"},
        {"id": "e3", "source": "calculus", "target": "neural_networks"}
      ]
    };
  }
  
  if (e.includes("/knowledge/gaps")) {
    return [
      {"concept_id": "calculus", "title": "Calculus Foundations", "reason": "Low mastery (70%) inhibits partial derivatives calculations."}
    ];
  }
  
  if (e.includes("/knowledge/path")) {
    return [
      {"title": "Python Basics", "mastery": 0.95, "status": "mastered"},
      {"title": "NumPy Arrays", "mastery": 0.85, "status": "mastered"},
      {"title": "Calculus Foundations", "mastery": 0.7, "status": "in_progress"},
      {"title": "Neural Networks", "mastery": 0.4, "status": "in_progress"}
    ];
  }
  
  if (e.includes("/decisions")) {
    return [
      {
        "id": 1,
        "title": "AWS Lambda vs ECS for serving microservice",
        "choice_made": "AWS ECS Container",
        "risk_level": "medium",
        "evidence_collected": ["Step 1 Option A", "Step 2 Option B"],
        "bias_detected": {},
        "decision_speed_seconds": 12.5,
        "confidence": 0.8,
        "created_at": "2026-07-19T09:00:00Z"
      }
    ];
  }
  
  if (e.includes("/reflections")) {
    return [
      {
        "id": 1,
        "reflection_type": "weekly",
        "content": "Focus has been consistent on machine learning. Recommend revising calculus foundations to unlock neural networks.",
        "reflection_date": "2026-07-19T08:00:00Z",
        "digital_twin_snapshot": {}
      }
    ];
  }
  
  if (e.includes("/arena/scenarios")) {
    return MOCK_SCENARIOS;
  }
  
  if (e.includes("/arena/submit")) {
    const body = JSON.parse(options.body || "{}");
    const steps = body.steps || [];
    let analyticalSum = 0;
    let impulsivenessSum = 0;
    let confidenceSum = 0;
    let cluesCount = 0;
    
    steps.forEach((s: any) => {
      confidenceSum += s.confidence;
      cluesCount += s.evidence_collected.length;
      if (s.option_selected === 'A') {
        impulsivenessSum += 0.8;
        analyticalSum += 0.3;
      } else if (s.option_selected === 'B') {
        analyticalSum += 0.5;
      } else {
        analyticalSum += 0.9;
      }
    });
    
    const avgConfidence = confidenceSum / (steps.length || 1);
    const avgAnalytical = analyticalSum / (steps.length || 1);
    const avgImpulsive = impulsivenessSum / (steps.length || 1);
    const avgOverconfidence = avgConfidence * (1.0 - (cluesCount / 6.0));
    const score = (avgAnalytical + (1.0 - avgImpulsive) + (1.0 - avgOverconfidence)) / 3.0;

    return {
      score: score,
      feedback: "Complete! You achieved a decision score of " + Math.round(score * 100) + "% on our static simulator client.",
      metrics: {
        analytical_thinking: avgAnalytical,
        risk_tolerance: 0.4,
        impulsiveness: avgImpulsive,
        sunk_cost: 0.3,
        confirmation_bias: 0.2,
        overconfidence: avgOverconfidence
      },
      biases_detected: avgOverconfidence > 0.5 ? {
        overconfidence: { severity: avgOverconfidence, description: "Demo bias flag: High confidence with minimal clues." }
      } : {},
      explanation: {
        evidence: "Static client session capture.",
        reasoning: "Computed metrics entirely client-side for GitHub Pages portability.",
        confidence: 0.9
      }
    };
  }

  if (e.includes("/mentor/chat")) {
    return {
      "message": "Welcome! You are accessing the static demo of the AI Mentor. Please run the backend locally to use dynamic Ollama model queries.",
      "twin_parameters_injected": {
        "dominant_style": "project",
        "readiness_score": 0.75,
        "target_role": "AI Engineer",
        "weaknesses_count": 1
      },
      "explanation": {
        "evidence": "Static environment detection.",
        "reasoning": "Serving default demo response.",
        "confidence": 1.0
      }
    };
  }

  return {};
}
