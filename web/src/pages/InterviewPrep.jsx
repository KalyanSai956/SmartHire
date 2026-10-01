import { useEffect, useState } from "react";
import {
  CalendarCheck,
  Flame,
  Sparkles,
  Clock3,
  RefreshCw,
  ChevronDown,
} from "lucide-react";

import "../CSS/InterviewPrep.css";

const ROLE_OPTIONS = [
  { value: "software-engineer", label: "Software Engineer" },
  { value: "frontend-engineer", label: "Frontend Engineer" },
  { value: "backend-engineer", label: "Backend Engineer" },
  { value: "fullstack-engineer", label: "Full-Stack Engineer" },
  { value: "data-scientist", label: "Data Scientist / ML Engineer" },
  { value: "devops-engineer", label: "DevOps / SRE" },
  { value: "mobile-engineer", label: "Mobile Engineer" },
  { value: "qa-engineer", label: "QA / Test Engineer" },
  { value: "engineering-manager", label: "Engineering Manager" },
];

const STACK_OPTIONS = [
  { value: "frontend", label: "Frontend (React)" },
  { value: "backend", label: "Backend (Node.js)" },
  { value: "fullstack", label: "Full-Stack" },
  { value: "python", label: "Python" },
  { value: "java", label: "Java" },
  { value: "dsa", label: "Data Structures & Algorithms" },
  { value: "system-design", label: "System Design" },
];

const QUESTION_BANK = {
  frontend: [
    {
      text: "What is the virtual DOM, and how does it improve rendering performance?",
      difficulty: "Easy",
      answer:
        "The virtual DOM is a lightweight in-memory copy of the real DOM. React diffs the previous and next virtual trees to calculate the minimal set of changes, then applies only those changes to the actual browser DOM, avoiding expensive, unnecessary manipulations.",
    },
    {
      text: "Explain the difference between controlled and uncontrolled components in React.",
      difficulty: "Medium",
      answer:
        "A controlled component's value is driven entirely by React state via props and onChange handlers, giving full control and easy validation. An uncontrolled component manages its own state internally in the DOM, and you read its value through a ref only when needed.",
    },
    {
      text: "When would you reach for useMemo or useCallback, and what problem do they actually solve?",
      difficulty: "Medium",
      answer:
        "Both avoid unnecessary recalculation between renders — useMemo memoizes an expensive computed value, useCallback memoizes a function reference. They matter most when passing values to memoized children or expensive dependencies, not as a default optimization for every value.",
    },
    {
      text: "How does React's reconciliation algorithm decide what to re-render?",
      difficulty: "Hard",
      answer:
        "React compares the new element tree to the previous one using heuristics like element type and list keys, rather than doing a full tree diff. Matching keys let it reuse and update existing DOM nodes instead of recreating them, keeping updates fast even for large lists.",
    },
    {
      text: "What causes a memory leak in a React component, and how would you find one?",
      difficulty: "Hard",
      answer:
        "A common cause is an async operation, subscription, or timer that still tries to update state after a component has unmounted. You'd typically find it via browser memory profiling or React's warning about updating an unmounted component, then clean up the effect properly.",
    },
    {
      text: "Describe how you'd structure state for a form with deeply nested fields.",
      difficulty: "Medium",
      answer:
        "It often helps to flatten state into a single object keyed by field path rather than deeply nested objects, updating it immutably with a helper function. Libraries like React Hook Form or Formik handle this well for larger forms.",
    },
    {
      text: "What's the difference between CSS specificity and the cascade?",
      difficulty: "Easy",
      answer:
        "Specificity is a scoring system that determines which of several conflicting selectors wins on an element, based on IDs, classes, and element types. The cascade is the broader process that also considers source order and origin when specificity ties.",
    },
  ],
  backend: [
    {
      text: "Walk through what happens between a client request and a Node.js server sending a response.",
      difficulty: "Easy",
      answer:
        "A request travels from the client through the network stack into Node's event loop, where it's routed (often by Express), processed — possibly querying a database — and a response is written back through the same path, all without blocking other requests.",
    },
    {
      text: "How does the Node.js event loop handle concurrent I/O without multiple threads?",
      difficulty: "Medium",
      answer:
        "Node uses a single-threaded event loop with phases like timers, I/O callbacks, poll, and check, delegating blocking work such as file I/O to a thread pool via libuv. This lets it handle many concurrent connections without a thread per request.",
    },
    {
      text: "What's the difference between process.nextTick, setImmediate, and setTimeout?",
      difficulty: "Hard",
      answer:
        "process.nextTick queues a callback to run before the event loop continues, giving it the highest priority. setImmediate runs in the check phase after I/O callbacks, and setTimeout runs after at least its specified delay once its phase is reached.",
    },
    {
      text: "How would you design rate limiting for a public API?",
      difficulty: "Medium",
      answer:
        "A common approach is a token bucket or sliding window counter stored in a fast store like Redis, keyed by client IP or API key. This should sit at the edge, such as an API gateway or middleware, so it protects the service before requests reach business logic.",
    },
    {
      text: "Explain how you'd handle a memory leak in a long-running Express service.",
      difficulty: "Hard",
      answer:
        "Likely culprits are unbounded caches, event listeners never removed, or closures holding onto large objects across requests. You'd confirm it with heap snapshots taken over time, comparing what's retained between snapshots to find the source.",
    },
    {
      text: "What are the trade-offs between REST and GraphQL for a growing API?",
      difficulty: "Medium",
      answer:
        "REST is simple, cacheable, and well understood, but can lead to over- or under-fetching as an app grows. GraphQL lets clients request exactly the fields they need and reduces round trips, at the cost of more complex caching and query cost management.",
    },
  ],
  fullstack: [
    {
      text: "How would you design authentication that works across a React frontend and a Node API?",
      difficulty: "Medium",
      answer:
        "A common pattern is the API issuing short-lived JWT access tokens plus a longer-lived refresh token stored in an httpOnly cookie, with the frontend attaching the access token to calls and silently refreshing it when it expires.",
    },
    {
      text: "Describe how you'd structure a monorepo for a full-stack app with shared types.",
      difficulty: "Medium",
      answer:
        "Tools like Turborepo or Nx let you keep frontend, backend, and a shared types package in one repo, so both sides import the same interfaces and stay in sync automatically when the API shape changes.",
    },
    {
      text: "What's your approach to handling optimistic UI updates when the backend call can fail?",
      difficulty: "Hard",
      answer:
        "Update the UI immediately assuming success, keep a reference to the previous state, and roll back with an error message if the backend call fails. Libraries like React Query make this pattern easier with built-in rollback support.",
    },
    {
      text: "How do you decide what logic belongs on the client versus the server?",
      difficulty: "Easy",
      answer:
        "Anything involving trust, security, or a single source of truth — validation that matters, business rules, data ownership — belongs on the server. The client should handle presentation and non-critical convenience logic like instant form feedback.",
    },
    {
      text: "Explain how you'd debug a bug that only reproduces in production.",
      difficulty: "Hard",
      answer:
        "Start by isolating the exact environment differences — data, config, load — then lean on logging, error tracking tools, and feature flags to identify the trigger without needing to redeploy repeatedly.",
    },
    {
      text: "How would you version an API without breaking existing frontend clients?",
      difficulty: "Medium",
      answer:
        "Common approaches are versioning in the URL path or via a header, keeping old versions running alongside new ones until clients migrate, and deprecating with a clear timeline rather than breaking changes overnight.",
    },
  ],
  python: [
    {
      text: "What's the difference between a list and a generator, and when would you choose each?",
      difficulty: "Easy",
      answer:
        "A list holds all its items in memory at once, while a generator produces items lazily one at a time via yield, which is far more memory-efficient for large or infinite sequences you only need to iterate once.",
    },
    {
      text: "Explain the GIL and how it affects multithreaded Python programs.",
      difficulty: "Hard",
      answer:
        "The Global Interpreter Lock ensures only one thread executes Python bytecode at a time, so CPU-bound multithreaded code doesn't get real parallelism — for that you'd use multiprocessing, while I/O-bound work still benefits from threads since the GIL releases during I/O waits.",
    },
    {
      text: "How do decorators work, and when have you written a custom one?",
      difficulty: "Medium",
      answer:
        "A decorator is a function that wraps another function to extend its behavior without modifying its code, commonly used for logging, timing, or access control — for example wrapping an endpoint to check authentication before calling the original function.",
    },
    {
      text: "What's the difference between @staticmethod, @classmethod, and an instance method?",
      difficulty: "Easy",
      answer:
        "An instance method takes self and operates on a specific object; a classmethod takes cls and operates on the class, often for alternate constructors; a staticmethod takes neither and behaves like a plain function namespaced inside the class.",
    },
    {
      text: "How would you profile a slow Python script and identify the bottleneck?",
      difficulty: "Medium",
      answer:
        "Start with cProfile to find which functions consume the most time, then use line_profiler for a more granular look at hot lines, and memory_profiler if the bottleneck seems memory-related rather than CPU-related.",
    },
    {
      text: "Explain mutable default arguments and why they're a common source of bugs.",
      difficulty: "Medium",
      answer:
        "A mutable default like a list or dict is created once when the function is defined, not each call, so mutations persist across calls unexpectedly. The fix is defaulting to None and creating the mutable object inside the function body.",
    },
  ],
  java: [
    {
      text: "What's the difference between an abstract class and an interface in Java?",
      difficulty: "Easy",
      answer:
        "An abstract class can hold state and partial implementation and supports single inheritance, while an interface defines a contract of methods, with optional default methods, that a class can implement multiple of — making interfaces better for shared capabilities across unrelated classes.",
    },
    {
      text: "How does garbage collection work in the JVM at a high level?",
      difficulty: "Medium",
      answer:
        "The JVM's garbage collector periodically identifies objects no longer reachable from active references and reclaims their memory, typically using a generational approach where short-lived objects are collected frequently in a young generation and long-lived ones move to an older generation collected less often.",
    },
    {
      text: "Explain the difference between == and .equals() for objects.",
      difficulty: "Easy",
      answer:
        "== compares object references, checking whether two variables point to the same object in memory, while .equals() compares logical equality as defined by the class — which is why classes like String override it to compare contents.",
    },
    {
      text: "What problem does the volatile keyword solve in multithreaded code?",
      difficulty: "Hard",
      answer:
        "volatile ensures reads and writes to a variable are visible across threads immediately rather than cached locally per thread, solving visibility issues, though it doesn't provide atomicity for compound operations like increment.",
    },
    {
      text: "How would you design a thread-safe cache in Java?",
      difficulty: "Hard",
      answer:
        "You could use a ConcurrentHashMap for storage paired with computeIfAbsent for atomic get-or-create semantics, adding eviction such as an LRU policy either manually or via a library like Caffeine.",
    },
    {
      text: "What's the difference between checked and unchecked exceptions?",
      difficulty: "Medium",
      answer:
        "Checked exceptions must be declared or caught at compile time and represent recoverable conditions the caller should handle, while unchecked exceptions represent programming errors that aren't required to be declared.",
    },
  ],
  dsa: [
    {
      text: "Given a string, find the length of the longest substring without repeating characters.",
      difficulty: "Medium",
      answer:
        "A sliding window with a hash set or map of last-seen indices works well — expand the window by moving the right pointer, and when a repeat is found, move the left pointer past the previous occurrence, tracking the max window size along the way in O(n) time.",
    },
    {
      text: "How would you detect a cycle in a linked list, and can you do it in O(1) space?",
      difficulty: "Medium",
      answer:
        "Floyd's cycle detection, the tortoise-and-hare approach, uses two pointers moving at different speeds; if they ever meet, there's a cycle. This needs no extra data structure beyond the two pointers, so it runs in O(1) space.",
    },
    {
      text: "Explain the difference between BFS and DFS, and when you'd use each.",
      difficulty: "Easy",
      answer:
        "BFS explores level by level using a queue and suits shortest-path problems in unweighted graphs, while DFS explores as deep as possible using a stack or recursion and suits problems like cycle detection or exploring all paths.",
    },
    {
      text: "How would you find the kth largest element in an unsorted array efficiently?",
      difficulty: "Medium",
      answer:
        "A min-heap of size k gives O(n log k) time — push elements and pop the smallest whenever the heap exceeds size k, leaving the kth largest at the top. Quickselect offers average O(n) time as an alternative.",
    },
    {
      text: "Design an algorithm to merge k sorted linked lists.",
      difficulty: "Hard",
      answer:
        "Using a min-heap that holds the current head of each list gives O(n log k) time — repeatedly pop the smallest node, append it to the result, and push its successor from the same list back onto the heap.",
    },
    {
      text: "What's the time complexity of your favorite sorting algorithm, and why does it matter?",
      difficulty: "Easy",
      answer:
        "A common answer is merge sort at O(n log n) guaranteed time with stable ordering, valuable because it performs consistently regardless of input distribution, unlike quicksort's worst-case O(n²).",
    },
  ],
  "system-design": [
    {
      text: "How would you design a URL shortener that scales to millions of requests a day?",
      difficulty: "Medium",
      answer:
        "Core pieces are a hashing or base62 counter to generate short codes, a key-value store for fast lookups, and horizontal scaling behind a load balancer, with caching for the most frequently accessed links.",
    },
    {
      text: "Walk through how you'd design a rate limiter for a distributed system.",
      difficulty: "Hard",
      answer:
        "A sliding window or token bucket algorithm backed by a shared store like Redis lets multiple service instances share the same rate-limit counters, avoiding the inconsistency you'd get if each instance tracked limits independently.",
    },
    {
      text: "How would you design the backend for a real-time chat application?",
      difficulty: "Hard",
      answer:
        "Typically built on WebSockets or a pub/sub system for message delivery, with a database for message history, presence tracking for online status, and horizontal scaling handled by routing users to specific socket server instances via a connection registry.",
    },
    {
      text: "What factors go into choosing between SQL and NoSQL for a new service?",
      difficulty: "Easy",
      answer:
        "SQL suits data with strong relationships and a need for transactions and consistency, while NoSQL suits flexible or rapidly evolving schemas, very high write throughput, or data that scales naturally as key-value or document stores.",
    },
    {
      text: "How would you design a notification system that supports email, SMS, and push?",
      difficulty: "Medium",
      answer:
        "A queue decouples notification requests from delivery, with separate workers for each channel that can retry independently and respect each provider's rate limits.",
    },
    {
      text: "Explain how you'd shard a database that's outgrown a single instance.",
      difficulty: "Hard",
      answer:
        "You'd pick a shard key that distributes load evenly, such as user ID, split data across multiple database instances accordingly, and add a routing layer so the application knows which shard to query — while planning for the added complexity of cross-shard queries and rebalancing.",
    },
  ],
};

function shuffle(list) {
  const copy = [...list];

  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));

    [copy[i], copy[j]] = [copy[j], copy[i]];
  }

  return copy;
}

export default function DailyQuestions() {
  const [role, setRole] = useState("software-engineer");
  const [stack, setStack] = useState("frontend");

  const [questions, setQuestions] = useState([]);
  const [generatedFor, setGeneratedFor] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [openAnswers, setOpenAnswers] = useState({});

  const [streak, setStreak] = useState(1);

  useEffect(() => {
    const todayStr = new Date().toISOString().slice(0, 10);

    const lastActive = localStorage.getItem("smarthire_last_active");
    const storedStreak = parseInt(
      localStorage.getItem("smarthire_streak") || "0",
      10,
    );

    if (lastActive === todayStr) {
      setStreak(storedStreak || 1);
      return;
    }

    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().slice(0, 10);

    const nextStreak = lastActive === yesterdayStr ? storedStreak + 1 : 1;

    localStorage.setItem("smarthire_last_active", todayStr);
    localStorage.setItem("smarthire_streak", String(nextStreak));

    setStreak(nextStreak);
  }, []);

  function handleGenerate() {
    setGenerating(true);
    setOpenAnswers({});

    const roleLabel =
      ROLE_OPTIONS.find((option) => option.value === role)?.label || role;

    const stackLabel =
      STACK_OPTIONS.find((option) => option.value === stack)?.label || stack;

    // Simulated generation for now — a real model call will replace this
    // once question generation is upgraded.
    setTimeout(() => {
      const pool = QUESTION_BANK[stack] || [];
      const picked = shuffle(pool).slice(0, 5);

      setQuestions(picked);
      setGeneratedFor({ roleLabel, stackLabel });
      setGenerating(false);
    }, 500);
  }

  function toggleAnswer(index) {
    setOpenAnswers((current) => ({
      ...current,
      [index]: !current[index],
    }));
  }

  return (
    <div className="daily-page">
      <div className="daily-container">
        <header className="daily-header">
          <span className="daily-eyebrow">Daily Practice</span>
        </header>

        {/* Daily nudge banner */}

        <div className="daily-nudge-banner">
          <div className="daily-nudge-icon">
            <CalendarCheck size={20} />
          </div>

          <div className="daily-nudge-content">
            <strong>Come back every day for new questions</strong>

            <span>
              Questions refresh daily, so logging in each day keeps your
              practice set current and your skills sharp.
            </span>
          </div>

          <div className="daily-streak-pill">
            <Flame size={14} />
            <span>
              {streak} day{streak !== 1 ? "s" : ""} in a row
            </span>
          </div>
        </div>

        {/* Generator */}

        <section className="daily-section">
          <div className="daily-section-heading">
            <div>
              <h2>Generate today's questions</h2>
              <p>
                Tell us the role and stack, and we'll put together a set to
                practice.
              </p>
            </div>
          </div>

          <div className="daily-generator-form">
            <div className="daily-field">
              <label htmlFor="daily-role">Target role</label>
              <div className="daily-select-wrapper">
                <select
                  id="daily-role"
                  value={role}
                  onChange={(event) => setRole(event.target.value)}
                >
                  {ROLE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="daily-select-caret" />
              </div>
            </div>

            <div className="daily-field">
              <label htmlFor="daily-stack">Stack</label>
              <div className="daily-select-wrapper">
                <select
                  id="daily-stack"
                  value={stack}
                  onChange={(event) => setStack(event.target.value)}
                >
                  {STACK_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="daily-select-caret" />
              </div>
            </div>

            <button
              type="button"
              className="daily-generate-button"
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? (
                <>
                  <RefreshCw size={14} className="daily-spin" />
                  Generating...
                </>
              ) : (
                <>Generate questions</>
              )}
            </button>
          </div>
        </section>

        {/* Question list */}

        <section className="daily-section">
          <div className="daily-section-heading">
            <div>
              <h2>Today's set</h2>
              <p>
                {generatedFor
                  ? `Showing questions for ${generatedFor.roleLabel} · ${generatedFor.stackLabel}`
                  : "Generate a set above to see your questions here."}
              </p>
            </div>
          </div>

          {questions.length === 0 ? (
            <div className="daily-empty-state">
              <Sparkles size={18} />
              <p>
                No questions yet — choose a role and stack, then generate your
                first set.
              </p>
            </div>
          ) : (
            <ol className="daily-question-list">
              {questions.map((question, index) => {
                const isOpen = !!openAnswers[index];

                return (
                  <li className="daily-question-card" key={index}>
                    <span className="daily-question-number">{index + 1}</span>

                    <div className="daily-question-body">
                      <p>{question.text}</p>

                      <div className="daily-question-meta">
                        <span
                          className={`daily-difficulty-pill daily-difficulty-${question.difficulty.toLowerCase()}`}
                        >
                          {question.difficulty}
                        </span>

                        <button
                          type="button"
                          className="daily-answer-toggle"
                          onClick={() => toggleAnswer(index)}
                        >
                          {isOpen ? "Hide answer" : "Show answer"}
                        </button>
                      </div>

                      {isOpen && (
                        <div className="daily-answer">
                          <p>{question.answer}</p>
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </section>

        {/* Mock interviews teaser */}

        <section className="daily-coming-soon">
          <div className="daily-coming-soon-icon">
            <Clock3 size={22} />
          </div>

          <strong>Mock interviews are coming soon</strong>

          <p>
            Live, timed mock interviews with instant feedback are on the way.
            For now, use your daily questions to build up steady practice.
          </p>

          <span className="daily-coming-soon-pill">Coming soon</span>
        </section>
      </div>
    </div>
  );
}
