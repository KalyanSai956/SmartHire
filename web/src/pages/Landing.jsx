import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Check,
  ChevronDown,
  FileSearch,
  BriefcaseBusiness,
  Sparkles,
  BrainCircuit,
  Target,
  Search,
  MapPin,
  Clock3,
  Menu,
  X,
  BarChart3,
  MessageSquare,
  Mic,
  Code2,
  Layers3,
  ShieldCheck,
  Bot,
  UserRound,
  Zap,
  TrendingUp,
  CircleCheck,
} from "lucide-react";
import AuthModal from "../components/AuthModal";
import "../CSS/Landing.css";

const faqs = [
  {
    question: "What is SmartHire?",
    answer:
      "SmartHire is an AI-powered career workspace that brings resume analysis, job matching, career assistance, and interview preparation together in one place.",
  },
  {
    question: "How does SmartHire analyze my resume?",
    answer:
      "SmartHire evaluates your resume across ATS compatibility, keywords, skills, experience, projects, structure, and content quality to provide actionable insights.",
  },
  {
    question: "How does job matching work?",
    answer:
      "SmartHire uses your career profile, resume context, skills, experience, target roles, and job requirements to identify opportunities that are relevant to your profile.",
  },
  {
    question: "Can I use my own AI API key?",
    answer:
      "Yes. SmartHire supports BYOK configuration for supported AI providers through the AI Settings area.",
  },
  {
    question: "Are the job application links official?",
    answer:
      "SmartHire preserves the original application URL provided by the supported job source so you can continue to the employer's application page.",
  },
  {
    question: "Can I prepare for interviews with SmartHire?",
    answer:
      "Yes. SmartHire can be used as part of your interview preparation workflow, including interview questions and AI-assisted preparation.",
  },
  {
    question: "Does SmartHire automatically apply for jobs?",
    answer:
      "No. SmartHire helps you discover and understand opportunities. You decide which opportunities to pursue and apply for.",
  },
  {
    question: "Are saved jobs the same as applications?",
    answer:
      "No. Saving a job simply keeps it available in your SmartHire workspace for later review.",
  },
];

const features = [
  {
    icon: FileSearch,
    number: "01",
    title: "Resume Intelligence",
    description:
      "Understand exactly how your resume performs before sending it to another employer.",
  },
  {
    icon: BriefcaseBusiness,
    number: "02",
    title: "Job Intelligence",
    description:
      "Discover opportunities based on your actual career profile instead of searching blindly.",
  },
  {
    icon: BrainCircuit,
    number: "03",
    title: "AI Career Assistant",
    description:
      "Ask questions about your resume, jobs, skills, interviews, and career direction.",
  },
  {
    icon: Mic,
    number: "04",
    title: "Interview Preparation",
    description:
      "Move from job discovery to interview preparation without leaving your career workspace.",
  },
];

const jobs = [
  {
    title: "Software Development Engineer",
    company: "Amazon",
    location: "India",
    type: "Full-time",
    match: "91%",
    skills: ["Java", "Python", "AWS"],
  },
  {
    title: "Software Engineer",
    company: "Amazon",
    location: "Bengaluru, India",
    type: "Full-time",
    match: "87%",
    skills: ["JavaScript", "React", "APIs"],
  },
  {
    title: "Machine Learning Engineer",
    company: "Amazon",
    location: "Hyderabad, India",
    type: "Full-time",
    match: "82%",
    skills: ["Python", "ML", "SQL"],
  },
];

function ScoreBar({ label, value }) {
  return (
    <div className="lh-score-row">
      <div className="lh-score-top">
        <span>{label}</span>
        <strong>{value}%</strong>
      </div>

      <div className="lh-score-track">
        <div className="lh-score-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function Landing() {
  const [openFaq, setOpenFaq] = useState(null);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [authModal, setAuthModal] = useState(null);

  const openLogin = () => {
    setAuthModal("login");
    setMobileMenu(false);
  };

  const openSignup = () => {
    setAuthModal("signup");
    setMobileMenu(false);
  };

  const closeAuth = () => {
    setAuthModal(null);
  };
  const toggleFaq = (index) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  return (
    <div className="lh-page">
      <header className="lh-navbar">
        <div className="lh-container lh-navbar-inner">
          <Link to="/" className="lh-brand">
            <span>SmartHire</span>
          </Link>

          <nav className={`lh-nav ${mobileMenu ? "lh-nav-open" : ""}`}>
            <a href="#resume" onClick={() => setMobileMenu(false)}>
              Resume
            </a>

            <a href="#jobs" onClick={() => setMobileMenu(false)}>
              Jobs
            </a>

            <a href="#ai" onClick={() => setMobileMenu(false)}>
              AI Assistant
            </a>

            <a href="#interview" onClick={() => setMobileMenu(false)}>
              Interviews
            </a>

            <a href="#faq" onClick={() => setMobileMenu(false)}>
              FAQ
            </a>

            <div className="lh-desktop-actions">
              <button
                type="button"
                className="lh-login-btn"
                onClick={openLogin}
              >
                Login
              </button>

              <button
                type="button"
                className="lh-primary-btn"
                onClick={openSignup}
              >
                Get Started
                <ArrowRight size={15} />
              </button>
            </div>
          </nav>

          <button
            type="button"
            className="lh-menu-btn"
            onClick={() => setMobileMenu(!mobileMenu)}
          >
            {mobileMenu ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </header>

      <main>
        <section className="lh-hero">
          <div className="lh-hero-glow lh-hero-glow-one" />
          <div className="lh-hero-glow lh-hero-glow-two" />

          <div className="lh-container">
            <div className="lh-hero-content">
              <h1>
                Your resume gets you noticed.
                <span>SmartHire helps you move forward.</span>
              </h1>

              <p>
                Analyze your resume, discover jobs that match your profile,
                understand your skill gaps, and prepare for interviews from one
                intelligent career workspace.
              </p>

              <div className="lh-hero-actions">
                <button
                  type="button"
                  className="lh-primary-btn lh-large-btn"
                  onClick={openSignup}
                >
                  Analyze My Resume
                  <ArrowRight size={17} />
                </button>

                <a href="#jobs" className="lh-outline-btn lh-large-btn">
                  Explore Jobs
                </a>
              </div>

              <div className="lh-hero-note">
                <CircleCheck size={16} />
                Built around your resume, skills, experience, and goals.
              </div>
            </div>

            <div className="lh-hero-product">
              <div className="lh-browser">
                <div className="lh-browser-bar">
                  <div className="lh-browser-dots">
                    <span />
                    <span />
                    <span />
                  </div>

                  <div className="lh-browser-url">
                    app.smarthire.ai/dashboard
                  </div>

                  <div className="lh-browser-secure">
                    <ShieldCheck size={12} />
                  </div>
                </div>

                <div className="lh-dashboard">
                  <aside className="lh-dashboard-sidebar">
                    <div className="lh-dashboard-logo">
                      <span>SmartHire</span>
                    </div>

                    <div className="lh-sidebar-section">
                      <span>Workspace</span>

                      <div className="lh-sidebar-active">
                        <BarChart3 size={15} />
                        Overview
                      </div>

                      <div>
                        <FileSearch size={15} />
                        Resume
                      </div>

                      <div>
                        <BriefcaseBusiness size={15} />
                        Jobs
                      </div>

                      <div>
                        <MessageSquare size={15} />
                        AI Assistant
                      </div>
                    </div>

                    <div className="lh-sidebar-section lh-sidebar-bottom">
                      <div>
                        <UserRound size={15} />
                        Profile
                      </div>

                      <div>
                        <ShieldCheck size={15} />
                        AI Settings
                      </div>
                    </div>
                  </aside>

                  <div className="lh-dashboard-main">
                    <div className="lh-dashboard-top">
                      <div>
                        <span>Good morning</span>
                        <h3>Your career overview</h3>
                      </div>

                      <div className="lh-user-avatar">SK</div>
                    </div>

                    <div className="lh-dashboard-grid">
                      <div className="lh-dashboard-score">
                        <div className="lh-card-label">Resume Score</div>

                        <div className="lh-big-score">
                          82
                          <small>/100</small>
                        </div>

                        <div className="lh-score-status">
                          <TrendingUp size={13} />
                          Strong resume foundation
                        </div>

                        <div className="lh-mini-bars">
                          <ScoreBar label="Keywords" value={88} />

                          <ScoreBar label="Skills" value={91} />

                          <ScoreBar label="Projects" value={84} />
                        </div>
                      </div>

                      <div className="lh-dashboard-match">
                        <div className="lh-card-label">Top job match</div>

                        <div className="lh-match-job">
                          <div className="lh-job-mini-logo">
                            <BriefcaseBusiness size={16} />
                          </div>

                          <div>
                            <strong>Software Development Engineer</strong>
                            <span>Amazon · India</span>
                          </div>

                          <div className="lh-match-number">91%</div>
                        </div>

                        <div className="lh-match-skills">
                          <span>Java</span>
                          <span>Python</span>
                          <span>AWS</span>
                        </div>
                      </div>
                    </div>

                    <div className="lh-dashboard-bottom">
                      <div className="lh-dashboard-bottom-title">
                        Recommended for you
                      </div>

                      <div className="lh-recommendation-row">
                        <div className="lh-recommendation-icon">
                          <Target size={15} />
                        </div>

                        <div>
                          <strong>12 opportunities match your profile</strong>
                          <span>Based on your skills and target roles</span>
                        </div>

                        <ArrowRight size={16} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="lh-floating lh-floating-one">
                <div className="lh-floating-icon">
                  <Zap size={15} />
                </div>

                <div>
                  <strong>91% match</strong>
                  <span>Amazon opportunity</span>
                </div>
              </div>

              <div className="lh-floating lh-floating-two">
                <div className="lh-floating-icon">
                  <Check size={15} />
                </div>

                <div>
                  <strong>3 skills matched</strong>
                  <span>Strong profile alignment</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="lh-intro-strip">
          <div className="lh-container">
            <div className="lh-intro-grid">
              <div>
                <strong>Resume</strong>
                <span>Understand your profile</span>
              </div>

              <div>
                <strong>Jobs</strong>
                <span>Find relevant opportunities</span>
              </div>

              <div>
                <strong>AI</strong>
                <span>Get career guidance</span>
              </div>

              <div>
                <strong>Interview</strong>
                <span>Prepare with confidence</span>
              </div>
            </div>
          </div>
        </section>

        <section id="resume" className="lh-section lh-resume-section">
          <div className="lh-container">
            <div className="lh-section-intro">
              <div className="lh-section-number">01</div>

              <div>
                <div className="lh-small-label">
                  <FileSearch size={14} />
                  Resume Intelligence
                </div>

                <h2>
                  Don't just get an ATS score.
                  <span>Understand your resume.</span>
                </h2>

                <p>
                  SmartHire breaks your resume down into the areas that
                  influence how effectively it communicates your skills and
                  experience.
                </p>
              </div>
            </div>

            <div className="lh-resume-layout">
              <div className="lh-resume-preview">
                <div className="lh-resume-paper">
                  <div className="lh-resume-paper-header">
                    <div className="lh-resume-name">SOFTWARE ENGINEER</div>

                    <div className="lh-resume-contact">
                      Hyderabad · India · developer@email.com
                    </div>
                  </div>

                  <div className="lh-resume-line large" />
                  <div className="lh-resume-line" />
                  <div className="lh-resume-line medium" />

                  <div className="lh-resume-block">
                    <strong>EXPERIENCE</strong>
                    <div className="lh-resume-line" />
                    <div className="lh-resume-line medium" />
                    <div className="lh-resume-line" />
                  </div>

                  <div className="lh-resume-block">
                    <strong>PROJECTS</strong>
                    <div className="lh-resume-line large" />
                    <div className="lh-resume-line medium" />
                    <div className="lh-resume-line" />
                  </div>

                  <div className="lh-resume-block">
                    <strong>SKILLS</strong>

                    <div className="lh-resume-tags">
                      <span>Java</span>
                      <span>React</span>
                      <span>Python</span>
                      <span>SQL</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="lh-analysis-panel">
                <div className="lh-analysis-header">
                  <div>
                    <span>Resume analysis</span>
                    <strong>Overall score</strong>
                  </div>

                  <div className="lh-analysis-score">82</div>
                </div>

                <div className="lh-analysis-bars">
                  <ScoreBar label="Keyword Match" value={88} />

                  <ScoreBar label="Skills Match" value={91} />

                  <ScoreBar label="Project Relevance" value={84} />

                  <ScoreBar label="Resume Quality" value={76} />
                </div>

                <div className="lh-insight">
                  <div className="lh-insight-icon">
                    <Sparkles size={15} />
                  </div>

                  <div>
                    <strong>Actionable insight</strong>
                    <p>
                      Your project section is strong. Consider adding measurable
                      outcomes to your experience bullets.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="lh-dark-section">
          <div className="lh-container">
            <div className="lh-dark-intro">
              <div className="lh-small-label lh-light-label">
                <BrainCircuit size={14} />
                Career intelligence
              </div>

              <h2>
                Your resume is more than a document.
                <span>It's your career context.</span>
              </h2>

              <p>
                SmartHire uses the information you provide to create a deeper
                understanding of your career direction, skills, experience, and
                target roles.
              </p>
            </div>

            <div className="lh-context-grid">
              <div className="lh-context-card">
                <UserRound size={19} />
                <strong>Career Profile</strong>
                <span>
                  Your interests, experience, skills, and target roles.
                </span>
              </div>

              <div className="lh-context-card">
                <Layers3 size={19} />
                <strong>Resume Context</strong>
                <span>
                  Projects, experience, achievements, and technical skills.
                </span>
              </div>

              <div className="lh-context-card">
                <Target size={19} />
                <strong>Career Direction</strong>
                <span>Roles and opportunities aligned with your goals.</span>
              </div>
            </div>
          </div>
        </section>

        <section id="jobs" className="lh-section lh-jobs-section">
          <div className="lh-container">
            <div className="lh-section-intro">
              <div className="lh-section-number">02</div>

              <div>
                <div className="lh-small-label">
                  <BriefcaseBusiness size={14} />
                  Job Intelligence
                </div>

                <h2>
                  Stop searching through everything.
                  <span>Find what fits you.</span>
                </h2>

                <p>
                  SmartHire uses your career profile and resume context to
                  identify opportunities that are relevant to your skills,
                  experience, and target roles.
                </p>
              </div>
            </div>

            <div className="lh-jobs-layout">
              <div className="lh-jobs-copy">
                <div className="lh-search-box">
                  <Search size={17} />
                  <span>Search your recommended jobs...</span>
                </div>

                <div className="lh-filter-row">
                  <span>Recommended</span>
                  <span>India</span>
                  <span>Software</span>
                  <span>Full-time</span>
                </div>

                <div className="lh-job-summary">
                  <strong>20</strong>
                  <span>recommended opportunities</span>
                </div>
              </div>

              <div className="lh-job-results">
                {jobs.map((job) => (
                  <article className="lh-job-card" key={job.title}>
                    <div className="lh-job-main">
                      <div className="lh-job-logo">
                        <BriefcaseBusiness size={17} />
                      </div>

                      <div className="lh-job-content">
                        <h3>{job.title}</h3>

                        <strong>{job.company}</strong>

                        <div className="lh-job-meta">
                          <span>
                            <MapPin size={13} />
                            {job.location}
                          </span>

                          <span>
                            <Clock3 size={13} />
                            {job.type}
                          </span>
                        </div>
                      </div>

                      <div className="lh-job-match">
                        <strong>{job.match}</strong>
                        <span>match</span>
                      </div>
                    </div>

                    <div className="lh-job-bottom">
                      <div className="lh-job-skills">
                        {job.skills.map((skill) => (
                          <span key={skill}>{skill}</span>
                        ))}
                      </div>

                      <button type="button">
                        View Job
                        <ArrowRight size={13} />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="ai" className="lh-ai-section">
          <div className="lh-container">
            <div className="lh-ai-layout">
              <div className="lh-ai-copy">
                <div className="lh-section-number">03</div>

                <div className="lh-small-label">
                  <Bot size={14} />
                  AI Career Assistant
                </div>

                <h2>
                  Ask about your career.
                  <span>Get answers with context.</span>
                </h2>

                <p>
                  Instead of starting every career question from scratch,
                  SmartHire can work around your resume, profile, job
                  requirements, and career goals.
                </p>

                <div className="lh-ai-checks">
                  <div>
                    <Check size={15} />
                    Resume-aware conversations
                  </div>

                  <div>
                    <Check size={15} />
                    Job-specific guidance
                  </div>

                  <div>
                    <Check size={15} />
                    Career improvement ideas
                  </div>
                </div>

                <button
                  type="button"
                  className="lh-primary-btn"
                  onClick={openSignup}
                >
                  Talk to SmartHire AI
                  <ArrowRight size={15} />
                </button>
              </div>

              <div className="lh-chat-window">
                <div className="lh-chat-header">
                  <div className="lh-chat-avatar">
                    <Sparkles size={16} />
                  </div>

                  <div>
                    <strong>SmartHire AI</strong>
                    <span>Career Assistant</span>
                  </div>

                  <div className="lh-chat-status">
                    <span />
                    Online
                  </div>
                </div>

                <div className="lh-chat-messages">
                  <div className="lh-message lh-user-message">
                    Am I a good match for this Amazon software engineering role?
                  </div>

                  <div className="lh-message lh-ai-message">
                    <div className="lh-ai-message-label">
                      <Sparkles size={13} />
                      SmartHire AI
                    </div>

                    <p>
                      Your profile shows strong alignment with this role. Your
                      Java, Python, and API experience are relevant.
                    </p>

                    <div className="lh-chat-result">
                      <div>
                        <strong>91%</strong>
                        <span>profile match</span>
                      </div>

                      <div>
                        <strong>8/10</strong>
                        <span>required skills</span>
                      </div>

                      <div>
                        <strong>3</strong>
                        <span>skills to improve</span>
                      </div>
                    </div>
                  </div>

                  <div className="lh-message lh-user-message">
                    What should I improve first?
                  </div>

                  <div className="lh-chat-input">
                    <span>Ask SmartHire anything...</span>
                    <ArrowRight size={15} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="interview" className="lh-section lh-interview-section">
          <div className="lh-container">
            <div className="lh-section-intro">
              <div className="lh-section-number">04</div>

              <div>
                <div className="lh-small-label">
                  <Mic size={14} />
                  Interview Preparation
                </div>

                <h2>
                  Found the job?
                  <span>Prepare for the conversation.</span>
                </h2>

                <p>
                  Turn the job you discovered into focused interview preparation
                  with questions and practice built around the role.
                </p>
              </div>
            </div>

            <div className="lh-interview-grid">
              <div className="lh-interview-card lh-interview-main">
                <div className="lh-interview-card-top">
                  <div className="lh-interview-icon">
                    <Mic size={18} />
                  </div>

                  <span>Mock Interview</span>
                </div>

                <h3>Practice before the real interview.</h3>

                <p>
                  Prepare with role-specific interview questions and structured
                  AI-assisted practice.
                </p>

                <div className="lh-interview-preview">
                  <div className="lh-question-number">Question 03 / 10</div>

                  <strong>
                    Explain a challenging project you worked on and how you
                    solved the problem.
                  </strong>

                  <div className="lh-record-btn">
                    <Mic size={15} />
                    Start answering
                  </div>
                </div>
              </div>

              <div className="lh-interview-side">
                <div className="lh-interview-small-card">
                  <Code2 size={18} />
                  <div>
                    <strong>Technical Questions</strong>
                    <span>Practice questions based on your target role.</span>
                  </div>
                </div>

                <div className="lh-interview-small-card">
                  <MessageSquare size={18} />
                  <div>
                    <strong>Behavioral Questions</strong>
                    <span>
                      Prepare stronger stories for common interview topics.
                    </span>
                  </div>
                </div>

                <div className="lh-interview-small-card">
                  <Target size={18} />
                  <div>
                    <strong>Role Focus</strong>
                    <span>Prepare around the job you actually want.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="lh-workspace-section">
          <div className="lh-container">
            <div className="lh-workspace-heading">
              <div className="lh-small-label lh-light-label">
                <Layers3 size={14} />
                One Career Workspace
              </div>

              <h2>
                Everything connected.
                <span>Nothing scattered.</span>
              </h2>

              <p>
                Your resume, career profile, jobs, AI tools, and interview
                preparation work together inside SmartHire.
              </p>
            </div>

            <div className="lh-workspace-map">
              <div className="lh-workspace-center">
                <strong>SmartHire</strong>
                <span>Career Workspace</span>
              </div>

              <div className="lh-workspace-node lh-node-one">
                <FileSearch size={17} />
                <strong>Resume</strong>
                <span>Analyze</span>
              </div>

              <div className="lh-workspace-node lh-node-two">
                <BriefcaseBusiness size={17} />
                <strong>Jobs</strong>
                <span>Discover</span>
              </div>

              <div className="lh-workspace-node lh-node-three">
                <Bot size={17} />
                <strong>AI</strong>
                <span>Ask</span>
              </div>

              <div className="lh-workspace-node lh-node-four">
                <Mic size={17} />
                <strong>Interviews</strong>
                <span>Prepare</span>
              </div>

              <div className="lh-workspace-line lh-line-one" />
              <div className="lh-workspace-line lh-line-two" />
              <div className="lh-workspace-line lh-line-three" />
              <div className="lh-workspace-line lh-line-four" />
            </div>
          </div>
        </section>

        <section className="lh-byoK-section">
          <div className="lh-container">
            <div className="lh-byok-card">
              <div>
                <div className="lh-small-label">
                  <ShieldCheck size={14} />
                  AI Gateway
                </div>

                <h2>
                  Your AI.
                  <span>Your control.</span>
                </h2>

                <p>
                  Connect supported AI providers through SmartHire's AI Settings
                  when you want to use your own API credentials.
                </p>

                <div className="lh-provider-list">
                  <span>Groq</span>
                  <span>OpenAI</span>
                  <span>Google</span>
                  <span>Anthropic</span>
                </div>

                <button
                  type="button"
                  className="lh-primary-btn"
                  onClick={openSignup}
                >
                  Explore AI Settings
                  <ArrowRight size={15} />
                </button>
              </div>

              <div className="lh-provider-panel">
                <div className="lh-provider-header">
                  <div className="lh-provider-avatar">
                    <BrainCircuit size={17} />
                  </div>

                  <div>
                    <strong>AI Settings</strong>
                    <span>Connected providers</span>
                  </div>
                </div>

                <div className="lh-provider-item">
                  <div>
                    <strong>Google Gemini</strong>
                    <span>Connected</span>
                  </div>

                  <Check size={17} />
                </div>

                <div className="lh-provider-item">
                  <div>
                    <strong>Groq</strong>
                    <span>Available</span>
                  </div>

                  <ArrowRight size={16} />
                </div>

                <div className="lh-provider-item">
                  <div>
                    <strong>OpenAI</strong>
                    <span>Available</span>
                  </div>

                  <ArrowRight size={16} />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="faq" className="lh-section lh-faq-section">
          <div className="lh-container lh-faq-layout">
            <div className="lh-faq-intro">
              <div className="lh-small-label">
                <Search size={14} />
                Frequently Asked Questions
              </div>

              <h2>
                Questions?
                <span>We've got answers.</span>
              </h2>

              <p>
                Everything you need to know before starting your SmartHire
                journey.
              </p>

              <button
                type="button"
                className="lh-outline-btn"
                onClick={openSignup}
              >
                Get Started
                <ArrowRight size={15} />
              </button>
            </div>

            <div className="lh-faq-list">
              {faqs.map((faq, index) => {
                const isOpen = openFaq === index;

                return (
                  <div
                    className={`lh-faq-item ${isOpen ? "lh-faq-open" : ""}`}
                    key={faq.question}
                  >
                    <button
                      type="button"
                      className="lh-faq-question"
                      onClick={() => toggleFaq(index)}
                    >
                      <span>{faq.question}</span>

                      <ChevronDown size={18} className="lh-faq-chevron" />
                    </button>

                    <div className="lh-faq-answer">
                      <p>{faq.answer}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="lh-final-cta">
          <div className="lh-container">
            <div className="lh-final-card">
              <div className="lh-final-pill">
                <Sparkles size={14} />
                Start your SmartHire journey
              </div>

              <h2>
                Your next opportunity
                <span>starts here.</span>
              </h2>

              <p>
                Analyze your resume. Discover relevant jobs. Prepare for
                interviews. Build your career with SmartHire.
              </p>

              <button
                type="button"
                className="lh-white-btn"
                onClick={openSignup}
              >
                Get Started with SmartHire
                <ArrowRight size={17} />
              </button>
            </div>
          </div>
        </section>
      </main>

      <footer className="lh-footer">
        <div className="lh-container">
          <div className="lh-footer-top">
            <div className="lh-footer-brand">
              <Link to="/" className="lh-brand">
                <img src="/smarthire.png" alt="SmartHire" />
                <span>SmartHire</span>
              </Link>

              <p>
                AI-powered resume intelligence, job discovery, career
                assistance, and interview preparation.
              </p>
            </div>

            <div className="lh-footer-links">
              <div>
                <strong>Product</strong>
                <a href="#resume">Resume</a>
                <a href="#jobs">Jobs</a>
                <a href="#ai">AI Assistant</a>
                <a href="#interview">Interviews</a>
              </div>

              <div>
                <strong>Resources</strong>
                <a href="#faq">FAQ</a>
                <a href="#jobs">Job Discovery</a>
                <a href="#resume">Resume Analysis</a>
              </div>

              <div>
                <strong>Account</strong>
                <button type="button" onClick={openLogin}>
                  Login
                </button>

                <button type="button" onClick={openSignup}>
                  Get Started
                </button>
              </div>
            </div>
          </div>

          <div className="lh-footer-bottom">
            <span>
              © {new Date().getFullYear()} SmartHire. All rights reserved.
            </span>

            <span>Built for smarter career decisions.</span>
          </div>
        </div>
      </footer>

      {authModal && (
        <AuthModal
          mode={authModal}
          onClose={closeAuth}
          onModeChange={setAuthModal}
        />
      )}
    </div>
  );
}

export default Landing;
