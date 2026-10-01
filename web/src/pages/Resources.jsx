import { useState } from "react";
import {
  FileText,
  BookOpen,
  Code2,
  Network,
  ArrowUpRight,
  CheckCircle2,
  XCircle,
  Map,
  Layers,
  Database,
  Timer,
  MessagesSquare,
  Users,
} from "lucide-react";
import "../CSS/Resources.css";

const ROADMAP = [
  {
    phase: "Foundation",
    duration: "Months 1–3",
    focus: "Programming fundamentals",
    items: [
      "Pick one language (Python, Java or C++) and get fluent in it",
      "Data types, control flow, functions, recursion",
      "Basic Git and command-line workflow",
    ],
  },
  {
    phase: "Core CS",
    duration: "Months 3–6",
    focus: "Data structures & fundamentals",
    items: [
      "Arrays, linked lists, stacks, queues, trees, graphs, hash maps",
      "Time & space complexity (Big-O)",
      "OOP, DBMS basics, and one course on Operating Systems",
    ],
  },
  {
    phase: "Application",
    duration: "Months 6–9",
    focus: "Projects & problem solving",
    items: [
      "Build 2–3 projects with a real README and deployed link",
      "150–200 curated DSA problems across all patterns",
      "Contribute to one open-source repo or hackathon",
    ],
  },
  {
    phase: "Interview Ready",
    duration: "Months 9–12",
    focus: "Mock interviews & systems thinking",
    items: [
      "Timed mock interviews (DSA + behavioral)",
      "System design basics for entry-level SDE roles",
      "Resume tailored per job description, applied weekly",
    ],
  },
];

const ATS_RULES = [
  {
    title: "Use standard section names",
    body: "Stick to headings ATS parsers recognize: Education, Experience, Projects, Skills, Certifications. Creative labels like 'My Journey' get misread or dropped.",
  },
  {
    title: "Match relevant keywords",
    body: "Mirror the exact terms in the job description (e.g. 'REST APIs', not 'web services') — but only if you genuinely have that skill.",
  },
  {
    title: "Keep formatting parser-safe",
    body: "Avoid tables, text boxes, columns, icons, and headers/footers for content. Most ATS software reads left-to-right, top-to-bottom, plain text only.",
  },
  {
    title: "Quantify your impact",
    body: "Replace duty statements with outcomes: 'Optimized query performance, reducing average response time from 800ms to 150ms.'",
  },
  {
    title: "One page, reverse-chronological",
    body: "For students and early-career candidates, one page is standard. List most recent experience first within each section.",
  },
  {
    title: "Save and name the file correctly",
    body: "Submit as PDF unless told otherwise, named 'FirstName_LastName_Resume.pdf' — not 'Resume_final_v3.pdf'.",
  },
  {
    title: "Action verbs, past tense, no pronouns",
    body: "Start every bullet with a strong verb (Built, Designed, Automated, Led) and drop 'I' / 'my' entirely.",
  },
  {
    title: "Proofread for consistency",
    body: "Same tense throughout, same date format, same punctuation style. Inconsistency reads as carelessness to a recruiter.",
  },
];

const BULLET_EXAMPLE = {
  weak: "Worked on a project to manage student data using Python and MySQL.",
  strong:
    "Built a student-record system (Python, MySQL) handling 5,000+ records, cutting manual data-entry time by 40%.",
};

const DSA_PATTERNS = [
  {
    pattern: "Two Pointers",
    complexity: "O(n)",
    use: "Sorted array pair sums, removing duplicates",
  },
  {
    pattern: "Sliding Window",
    complexity: "O(n)",
    use: "Longest substring, max sum subarray of size k",
  },
  {
    pattern: "Binary Search",
    complexity: "O(log n)",
    use: "Search in sorted/rotated arrays, search space reduction",
  },
  {
    pattern: "Hashing",
    complexity: "O(1) avg lookup",
    use: "Frequency counts, two-sum, grouping",
  },
  {
    pattern: "DFS / BFS",
    complexity: "O(V + E)",
    use: "Graph/tree traversal, shortest path (unweighted)",
  },
  {
    pattern: "Dynamic Programming",
    complexity: "O(n·m) typical",
    use: "Knapsack, LCS, edit distance, path counting",
  },
  {
    pattern: "Greedy",
    complexity: "O(n log n)",
    use: "Interval scheduling, minimum coins (constraints permitting)",
  },
  {
    pattern: "Backtracking",
    complexity: "Exponential",
    use: "Permutations, N-Queens, Sudoku solvers",
  },
];

const CS_FUNDAMENTALS = [
  {
    title: "Operating Systems",
    points: [
      "Process vs thread",
      "Deadlock & synchronization",
      "Paging & virtual memory",
      "Scheduling algorithms",
    ],
  },
  {
    title: "DBMS",
    points: [
      "Normalization (1NF–3NF)",
      "Indexes & joins",
      "ACID properties",
      "Transactions & isolation levels",
    ],
  },
  {
    title: "Networking",
    points: [
      "OSI vs TCP/IP model",
      "TCP vs UDP",
      "DNS resolution flow",
      "HTTP status codes & methods",
    ],
  },
  {
    title: "OOP",
    points: [
      "Encapsulation, inheritance, polymorphism",
      "Abstraction vs interface",
      "SOLID principles",
      "Composition over inheritance",
    ],
  },
];

const STAR_STEPS = [
  {
    letter: "S",
    label: "Situation",
    body: "Set the scene: what was the context, team, or problem?",
  },
  {
    letter: "T",
    label: "Task",
    body: "What was your specific responsibility or goal?",
  },
  {
    letter: "A",
    label: "Action",
    body: "What did you personally do — decisions, trade-offs, tools used?",
  },
  {
    letter: "R",
    label: "Result",
    body: "What changed? Quantify it, and name what you learned.",
  },
];

const SYSTEM_CONCEPTS = [
  {
    icon: Layers,
    title: "Scalability",
    body: "Vertical scaling adds power to one machine (simpler, has a ceiling). Horizontal scaling adds more machines (more complex, near-limitless) — most large systems favor horizontal.",
  },
  {
    icon: Database,
    title: "SQL vs NoSQL",
    body: "SQL (Postgres, MySQL) enforces schema and relationships — strong consistency, complex queries. NoSQL (MongoDB, DynamoDB) trades some consistency for flexible schema and horizontal scale.",
  },
  {
    icon: Timer,
    title: "Caching",
    body: "Store frequently-read data in fast memory (Redis, Memcached) to reduce database load. Common strategies: cache-aside, write-through, and TTL-based eviction.",
  },
  {
    icon: MessagesSquare,
    title: "Message queues",
    body: "Decouple producers from consumers (Kafka, RabbitMQ, SQS) so slow or failing downstream services don't block the request path — enables async processing and retries.",
  },
];

/* =========================================================
   SMALL DIAGRAM COMPONENTS (inline SVG, no external assets)
   ========================================================= */

function RequestFlowDiagram() {
  return (
    <svg
      viewBox="0 0 760 220"
      className="diagram-svg"
      role="img"
      aria-label="Diagram of a client request flowing through a load balancer to app servers, a cache, and a database"
    >
      {/* connecting lines */}
      <line x1="115" y1="110" x2="195" y2="110" className="diagram-line" />
      <line x1="295" y1="110" x2="345" y2="60" className="diagram-line" />
      <line x1="295" y1="110" x2="345" y2="110" className="diagram-line" />
      <line x1="295" y1="110" x2="345" y2="160" className="diagram-line" />
      <line x1="445" y1="60" x2="500" y2="80" className="diagram-line" />
      <line x1="445" y1="110" x2="500" y2="90" className="diagram-line" />
      <line x1="445" y1="160" x2="500" y2="100" className="diagram-line" />
      <line x1="600" y1="90" x2="650" y2="70" className="diagram-line" />
      <line x1="600" y1="90" x2="650" y2="150" className="diagram-line" />

      {/* Client */}
      <rect
        x="20"
        y="85"
        width="95"
        height="50"
        rx="8"
        className="diagram-node diagram-node--accent"
      />
      <text x="67" y="115" className="diagram-label">
        Client
      </text>

      {/* Load balancer */}
      <rect
        x="195"
        y="85"
        width="100"
        height="50"
        rx="8"
        className="diagram-node"
      />
      <text x="245" y="108" className="diagram-label">
        Load
      </text>
      <text x="245" y="122" className="diagram-label">
        Balancer
      </text>

      {/* App servers */}
      <rect
        x="345"
        y="35"
        width="100"
        height="50"
        rx="8"
        className="diagram-node"
      />
      <text x="395" y="64" className="diagram-label">
        App Server 1
      </text>
      <rect
        x="345"
        y="85"
        width="100"
        height="50"
        rx="8"
        className="diagram-node"
      />
      <text x="395" y="114" className="diagram-label">
        App Server 2
      </text>
      <rect
        x="345"
        y="135"
        width="100"
        height="50"
        rx="8"
        className="diagram-node"
      />
      <text x="395" y="164" className="diagram-label">
        App Server 3
      </text>

      {/* Cache */}
      <rect
        x="500"
        y="65"
        width="100"
        height="50"
        rx="8"
        className="diagram-node diagram-node--muted"
      />
      <text x="550" y="94" className="diagram-label">
        Cache
      </text>

      {/* DB */}
      <rect
        x="650"
        y="45"
        width="95"
        height="50"
        rx="8"
        className="diagram-node diagram-node--muted"
      />
      <text x="697" y="74" className="diagram-label">
        Primary DB
      </text>
      <rect
        x="650"
        y="125"
        width="95"
        height="50"
        rx="8"
        className="diagram-node diagram-node--muted"
      />
      <text x="697" y="154" className="diagram-label">
        Replica DB
      </text>
    </svg>
  );
}

function BigODiagram() {
  const curves = [
    { d: "M40,170 L340,170", label: "O(1)", color: "#16a36a", ly: 168 },
    {
      d: "M40,170 C 140,168 240,140 340,95",
      label: "O(log n)",
      color: "#0ea5a4",
      ly: 90,
    },
    { d: "M40,170 L340,60", label: "O(n)", color: "#002a9d", ly: 55 },
    {
      d: "M40,170 C 160,168 260,90 340,20",
      label: "O(n log n)",
      color: "#d97706",
      ly: 15,
    },
    {
      d: "M40,170 C 120,170 260,20 340,-30",
      label: "O(n²)",
      color: "#dc2626",
      ly: -12,
    },
  ];

  return (
    <svg
      viewBox="0 0 400 190"
      className="diagram-svg diagram-svg--chart"
      role="img"
      aria-label="Chart comparing algorithmic growth rates from constant to quadratic time as input size increases"
    >
      <line x1="40" y1="10" x2="40" y2="170" className="diagram-axis" />
      <line x1="40" y1="170" x2="360" y2="170" className="diagram-axis" />
      <text x="200" y="186" className="diagram-axis-label">
        input size (n)
      </text>
      <text
        x="14"
        y="90"
        className="diagram-axis-label"
        transform="rotate(-90 14 90)"
      >
        time
      </text>

      {curves.map((c) => (
        <path
          key={c.label}
          d={c.d}
          className="diagram-curve"
          style={{ stroke: c.color }}
        />
      ))}
      {curves.map((c) => (
        <text
          key={c.label}
          x="345"
          y={Math.max(12, Math.min(168, c.ly + 90))}
          className="diagram-curve-label"
          style={{ fill: c.color }}
        >
          {c.label}
        </text>
      ))}
    </svg>
  );
}

/* =========================================================
   MAIN COMPONENT
   ========================================================= */

export default function Resources() {
  const [activeSection, setActiveSection] = useState("roadmap");

  const scrollToSection = (id) => {
    setActiveSection(id);
    document
      .getElementById(id)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="workspace">
      <div className="resources-page">
        {/* NAV */}
        <nav className="resources-nav">
          <button
            className={activeSection === "roadmap" ? "active" : ""}
            onClick={() => scrollToSection("roadmap")}
          >
            <Map size={16} /> Roadmap
          </button>
          <button
            className={activeSection === "ats-templates" ? "active" : ""}
            onClick={() => scrollToSection("ats-templates")}
          >
            <FileText size={16} /> ATS Templates
          </button>
          <button
            className={activeSection === "ats-guide" ? "active" : ""}
            onClick={() => scrollToSection("ats-guide")}
          >
            <BookOpen size={16} /> Resume Guide
          </button>
          <button
            className={activeSection === "interview-prep" ? "active" : ""}
            onClick={() => scrollToSection("interview-prep")}
          >
            <Code2 size={16} /> Interview Prep
          </button>
          <button
            className={activeSection === "system-design" ? "active" : ""}
            onClick={() => scrollToSection("system-design")}
          >
            <Network size={16} /> System Design
          </button>
        </nav>

        {/* =====================================================
          LEARNING ROADMAP
          ===================================================== */}
        <section id="roadmap" className="resource-section">
          <div className="resource-section-heading">
            <div className="resource-section-icon">
              <Map size={19} />
            </div>
            <div>
              <span>WHERE TO START</span>
              <h2>A 12-Month Learning Roadmap</h2>
            </div>
          </div>
          <p className="resource-section-description">
            If you're not sure where to begin, follow this order. Each phase
            builds on the last — skipping straight to interview problems without
            the foundation underneath tends to stall out around
            medium-difficulty problems.
          </p>

          <div className="roadmap-timeline">
            {ROADMAP.map((phase, i) => (
              <div className="roadmap-step" key={phase.phase}>
                <div className="roadmap-step-marker">
                  <span>{i + 1}</span>
                </div>
                <div className="roadmap-step-body">
                  <span className="roadmap-duration">{phase.duration}</span>
                  <h3>{phase.phase}</h3>
                  <p className="roadmap-focus">{phase.focus}</p>
                  <ul>
                    {phase.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* =====================================================
          ATS TEMPLATES
          ===================================================== */}
        <section id="ats-templates" className="resource-section">
          <div className="resource-section-heading">
            <div className="resource-section-icon">
              <FileText size={19} />
            </div>
            <div>
              <span>RESUME RESOURCES</span>
              <h2>ATS Templates</h2>
            </div>
          </div>
          <p className="resource-section-description">
            Resume structures designed to keep your information readable,
            searchable, and easy for Applicant Tracking Systems to parse.
          </p>

          <div className="resource-template-grid">
            <div className="resource-template-card">
              <div>
                <span className="template-type">ENTRY LEVEL</span>
                <h3>Fresher Resume</h3>
                <p>
                  For students and recent graduates with limited professional
                  experience. Leads with education and projects instead of work
                  history.
                </p>
              </div>
              <button>
                View Template <ArrowUpRight size={15} />
              </button>
            </div>

            <div className="resource-template-card">
              <div>
                <span className="template-type">SOFTWARE</span>
                <h3>Software Developer</h3>
                <p>
                  Focused on technical skills, projects, internships, and
                  software development experience, with a dedicated tech-stack
                  line.
                </p>
              </div>
              <button>
                View Template <ArrowUpRight size={15} />
              </button>
            </div>

            <div className="resource-template-card">
              <div>
                <span className="template-type">DATA / AI</span>
                <h3>AI & ML Resume</h3>
                <p>
                  Highlights machine learning projects, model performance
                  metrics, datasets used, and relevant coursework or research.
                </p>
              </div>
              <button>
                View Template <ArrowUpRight size={15} />
              </button>
            </div>
          </div>
        </section>

        {/* =====================================================
          ATS RESUME GUIDE
          ===================================================== */}
        <section id="ats-guide" className="resource-section">
          <div className="resource-section-heading">
            <div className="resource-section-icon">
              <BookOpen size={19} />
            </div>
            <div>
              <span>RESUME KNOWLEDGE</span>
              <h2>ATS Resume Guide</h2>
            </div>
          </div>
          <p className="resource-section-description">
            Follow these principles when creating or improving your resume for
            Applicant Tracking Systems and human reviewers alike.
          </p>

          <div className="ats-rules-grid">
            {ATS_RULES.map((rule) => (
              <div className="ats-rule" key={rule.title}>
                <CheckCircle2 size={17} />
                <div>
                  <h3>{rule.title}</h3>
                  <p>{rule.body}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="bullet-compare">
            <div className="bullet-example bullet-example--weak">
              <span className="bullet-tag">
                <XCircle size={14} /> Weak bullet
              </span>
              <p>{BULLET_EXAMPLE.weak}</p>
            </div>
            <div className="bullet-example bullet-example--strong">
              <span className="bullet-tag">
                <CheckCircle2 size={14} /> Strong bullet
              </span>
              <p>{BULLET_EXAMPLE.strong}</p>
            </div>
          </div>
        </section>

        {/* =====================================================
          INTERVIEW PREP
          ===================================================== */}
        <section id="interview-prep" className="resource-section">
          <div className="resource-section-heading">
            <div className="resource-section-icon">
              <Code2 size={19} />
            </div>
            <div>
              <span>TECHNICAL PREPARATION</span>
              <h2>Interview Prep</h2>
            </div>
          </div>
          <p className="resource-section-description">
            Build your technical foundation through structured problem solving,
            core CS subjects, and behavioral storytelling.
          </p>

          <h3 className="subsection-title">
            DSA Patterns &amp; When to Use Them
          </h3>
          <div className="table-wrapper">
            <table className="dsa-table">
              <thead>
                <tr>
                  <th>Pattern</th>
                  <th>Typical Complexity</th>
                  <th>Use it for</th>
                </tr>
              </thead>
              <tbody>
                {DSA_PATTERNS.map((row) => (
                  <tr key={row.pattern}>
                    <td>{row.pattern}</td>
                    <td>
                      <span className="complexity-pill">{row.complexity}</span>
                    </td>
                    <td>{row.use}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="diagram-block">
            <h3 className="subsection-title">Big-O Growth, Visually</h3>
            <p className="resource-section-description">
              When two approaches both "work," this is what separates a pass
              from a fail at scale. Always state the complexity of your solution
              out loud before you start coding.
            </p>
            <BigODiagram />
          </div>

          <h3 className="subsection-title">
            Core CS Subjects Interviewers Actually Ask
          </h3>
          <div className="resource-card-grid">
            {CS_FUNDAMENTALS.map((subject) => (
              <div className="resource-info-card" key={subject.title}>
                <h3>{subject.title}</h3>
                <ul className="fundamentals-list">
                  {subject.points.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <h3 className="subsection-title">
            The STAR Method for Behavioral Rounds
          </h3>
          <div className="star-grid">
            {STAR_STEPS.map((step) => (
              <div className="star-step" key={step.letter}>
                <div className="star-letter">{step.letter}</div>
                <div>
                  <h3>{step.label}</h3>
                  <p>{step.body}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="callout">
            <Users size={17} />
            <p>
              Keep a running document of 6–8 stories (a bug you fixed, a
              conflict with a teammate, a deadline you missed) — most behavioral
              questions map onto one of these with a small reframe.
            </p>
          </div>
        </section>

        {/* =====================================================
          SYSTEM DESIGN
          ===================================================== */}
        <section id="system-design" className="resource-section">
          <div className="resource-section-heading">
            <div className="resource-section-icon">
              <Network size={19} />
            </div>
            <div>
              <span>ENGINEERING KNOWLEDGE</span>
              <h2>System Design</h2>
            </div>
          </div>
          <p className="resource-section-description">
            Understand the building blocks used to design scalable software
            systems — even at an entry level, interviewers expect you to reason
            about these trade-offs.
          </p>

          <div className="diagram-block">
            <h3 className="subsection-title">Anatomy of a Web Request</h3>
            <p className="resource-section-description">
              A single request rarely hits just one machine. Tracing this path
              is the starting point for almost every system design answer.
            </p>
            <RequestFlowDiagram />
          </div>

          <h3 className="subsection-title">Core Concepts</h3>
          <div className="concept-grid">
            {SYSTEM_CONCEPTS.map((c) => (
              <div className="concept-card" key={c.title}>
                <div className="concept-icon">
                  <c.icon size={18} />
                </div>
                <h3>{c.title}</h3>
                <p>{c.body}</p>
              </div>
            ))}
          </div>

          <h3 className="subsection-title">Practice Designing These Systems</h3>
          <div className="resource-card-grid">
            <div className="resource-info-card">
              <h3>URL Shortener</h3>
              <p>
                Covers hashing/base62 encoding, read-heavy caching, and a
                key-value store.
              </p>
            </div>
            <div className="resource-info-card">
              <h3>Chat Application</h3>
              <p>
                Covers WebSockets, message ordering, delivery guarantees, and
                presence status.
              </p>
            </div>
            <div className="resource-info-card">
              <h3>Notification System</h3>
              <p>
                Covers message queues, fan-out delivery, retries, and rate
                limiting per user.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
