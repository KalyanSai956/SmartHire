import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Briefcase,
  Check,
  FileText,
  GraduationCap,
  Plus,
  Target,
  Upload,
  X,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

import {
  analyzeResume,
  completeOnboarding,
  getProfile,
  saveOnboardingProgress,
  uploadProfileResume,
} from "../services/api";

import "../CSS/Onboarding.css";

const EXPERIENCE_OPTIONS = [
  "Student",
  "Fresher",
  "Less than 1 year",
  "1–2 years",
  "2–5 years",
  "5+ years",
];

const INTEREST_SUGGESTIONS = [
  "Artificial Intelligence",
  "Machine Learning",
  "Software Development",
  "Data Science",
  "Web Development",
  "Backend Engineering",
  "Cloud & DevOps",
  "Cybersecurity",
];

const SPECIALIZATION_SUGGESTIONS = [
  "AI/ML",
  "Generative AI",
  "NLP",
  "Computer Vision",
  "Full Stack",
  "Backend",
  "Frontend",
  "Data Engineering",
];

const TOTAL_STEPS = 7;

export default function Onboarding() {
  const navigate = useNavigate();

  const { accessToken, user } = useAuth();

  const [step, setStep] = useState(1);

  const [username, setUsername] = useState(
    user?.user_metadata?.full_name || user?.email?.split("@")[0] || "",
  );

  const [careerInterests, setCareerInterests] = useState([]);
  const [interestInput, setInterestInput] = useState("");

  const [specializations, setSpecializations] = useState([]);
  const [specializationInput, setSpecializationInput] = useState("");

  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState("");

  const [targetRoles, setTargetRoles] = useState([]);
  const [roleInput, setRoleInput] = useState("");

  const [experience, setExperience] = useState("");
  const [graduationYear, setGraduationYear] = useState("");

  const [resume, setResume] = useState(null);

  const [loadingProfile, setLoadingProfile] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  /*
   * ----------------------------------------------------
   * LOAD SAVED ONBOARDING PROGRESS
   * ----------------------------------------------------
   */
  useEffect(() => {
    let active = true;

    async function loadProfile() {
      if (!accessToken) {
        if (active) {
          setLoadingProfile(false);
        }

        return;
      }

      try {
        const profile = await getProfile(accessToken);

        if (!active) return;

        /*
         * If onboarding is already completed,
         * the user does not need to see onboarding again.
         */
        if (profile?.onboarding_completed) {
          navigate("/dashboard", {
            replace: true,
          });

          return;
        }

        /*
         * Restore the exact saved step.
         */
        const savedStep = Number(profile?.onboarding_step);

        if (
          Number.isInteger(savedStep) &&
          savedStep >= 1 &&
          savedStep <= TOTAL_STEPS
        ) {
          setStep(savedStep);
        }

        /*
         * Restore saved profile information.
         */
        if (profile?.username) {
          setUsername(profile.username);
        }

        if (Array.isArray(profile?.career_interests)) {
          setCareerInterests(profile.career_interests);
        }

        if (Array.isArray(profile?.specializations)) {
          setSpecializations(profile.specializations);
        }

        if (Array.isArray(profile?.skills)) {
          setSkills(profile.skills);
        }

        if (Array.isArray(profile?.target_roles)) {
          setTargetRoles(profile.target_roles);
        }

        if (profile?.experience) {
          setExperience(profile.experience);
        }

        if (profile?.graduation_year) {
          setGraduationYear(String(profile.graduation_year));
        }
      } catch (err) {
        console.error("Failed to load onboarding progress:", err);

        if (active) {
          setError(
            err.message || "Could not load your saved onboarding progress.",
          );
        }
      } finally {
        if (active) {
          setLoadingProfile(false);
        }
      }
    }

    loadProfile();

    return () => {
      active = false;
    };
  }, [accessToken, navigate]);

  /*
   * ----------------------------------------------------
   * HELPERS
   * ----------------------------------------------------
   */

  function addUniqueValue(input, setter, setInput) {
    const value = input.trim();

    if (!value) return;

    setter((current) => {
      const exists = current.some(
        (item) => item.toLowerCase() === value.toLowerCase(),
      );

      if (exists) {
        return current;
      }

      return [...current, value];
    });

    setInput("");
  }

  function removeValue(value, setter) {
    setter((current) => current.filter((item) => item !== value));
  }

  function handleEnter(event, callback) {
    if (event.key === "Enter") {
      event.preventDefault();
      callback();
    }
  }

  function addInterest() {
    addUniqueValue(interestInput, setCareerInterests, setInterestInput);
  }

  function addSpecialization() {
    addUniqueValue(
      specializationInput,
      setSpecializations,
      setSpecializationInput,
    );
  }

  function addSkill() {
    addUniqueValue(skillInput, setSkills, setSkillInput);
  }

  function addRole() {
    addUniqueValue(roleInput, setTargetRoles, setRoleInput);
  }

  function toggleSuggestion(value, values, setter) {
    setter((current) => {
      const exists = current.some(
        (item) => item.toLowerCase() === value.toLowerCase(),
      );

      if (exists) {
        return current.filter(
          (item) => item.toLowerCase() !== value.toLowerCase(),
        );
      }

      return [...current, value];
    });
  }

  /*
   * ----------------------------------------------------
   * VALIDATION
   * ----------------------------------------------------
   */

  function validateStep() {
    setError("");

    if (step === 1) {
      if (!username.trim()) {
        setError("Please enter a username.");
        return false;
      }

      if (username.trim().length < 2) {
        setError("Username must contain at least 2 characters.");
        return false;
      }
    }

    if (step === 2) {
      if (!careerInterests.length) {
        setError("Add at least one career interest.");
        return false;
      }
    }

    if (step === 3) {
      if (!specializations.length) {
        setError("Add at least one specialization.");
        return false;
      }
    }

    if (step === 4) {
      if (!skills.length) {
        setError("Add at least one skill.");
        return false;
      }
    }

    if (step === 5) {
      if (!targetRoles.length) {
        setError("Add at least one target role.");
        return false;
      }
    }

    if (step === 6) {
      if (!experience) {
        setError("Please select your experience level.");
        return false;
      }

      const year = Number(graduationYear);

      if (
        !graduationYear ||
        !Number.isInteger(year) ||
        year < 1950 ||
        year > 2100
      ) {
        setError("Please enter a valid graduation year.");
        return false;
      }
    }

    if (step === 7) {
      if (!resume) {
        setError("Please upload your resume.");
        return false;
      }
    }

    return true;
  }

  /*
   * ----------------------------------------------------
   * SAVE CURRENT ONBOARDING PROGRESS
   * ----------------------------------------------------
   */
  async function saveCurrentProgress(nextStep) {
    await saveOnboardingProgress({
      step: nextStep,
      username: username.trim(),
      careerInterests,
      specializations,
      skills,
      targetRoles,
      experience,
      graduationYear: graduationYear === "" ? null : Number(graduationYear),
      token: accessToken,
    });
  }

  /*
   * ----------------------------------------------------
   * NEXT STEP
   * ----------------------------------------------------
   */
  async function nextStep() {
    if (!validateStep()) {
      return;
    }

    setBusy(true);
    setError("");

    try {
      /*
       * Step 1 -> 2
       * Step 2 -> 3
       * ...
       * Step 6 -> 7
       *
       * Save the CURRENT data while recording
       * the NEXT step.
       */
      if (step < TOTAL_STEPS) {
        const nextStepNumber = step + 1;

        await saveCurrentProgress(nextStepNumber);

        setStep(nextStepNumber);

        return;
      }

      /*
       * ------------------------------------------------
       * STEP 7
       * ------------------------------------------------
       */

      /*
       * 1. Save the complete profile information.
       *
       * The backend already has the progress from
       * previous steps.
       */

      await saveOnboardingProgress({
        step: 7,
        username: username.trim(),
        careerInterests,
        specializations,
        skills,
        targetRoles,
        experience,
        graduationYear: Number(graduationYear),
        token: accessToken,
      });

      /*
       * 2. Upload the exact resume selected by
       * the user.
       */
      await uploadProfileResume({
        file: resume,
        token: accessToken,
      });

      const analysis = await analyzeResume({
        file: resume,
        jobDescription: "",
        token: accessToken,
      });

      await completeOnboarding(accessToken);

      /*
       * 5. Keep the existing cache for any other
       * part of the application that may still use it.
       */
      sessionStorage.setItem("smarthire_onboarding_completed", "true");

      /*
       * 6. Go directly to the analysis page.
       */
      navigate("/analysis/new", {
        replace: true,
        state: {
          analysis,
          filename: resume.name,
          isNew: true,
          fromOnboarding: true,
        },
      });
    } catch (err) {
      console.error("Onboarding error:", err);

      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  /*
   * ----------------------------------------------------
   * PREVIOUS STEP
   * ----------------------------------------------------
   *
   * We do not save here because the current step
   * was already persisted when the user entered it.
   */
  function previousStep() {
    setError("");

    setStep((current) => Math.max(1, current - 1));
  }

  /*
   * ----------------------------------------------------
   * RESUME UPLOAD
   * ----------------------------------------------------
   */
  function handleResumeChange(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    const validExtension = /\.(pdf|docx)$/i.test(file.name);

    if (!validExtension || !validTypes.includes(file.type)) {
      setError("Please upload a PDF or DOCX file.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Resume must be smaller than 5 MB.");
      return;
    }

    setError("");
    setResume(file);
  }

  const progress = `${(step / TOTAL_STEPS) * 100}%`;

  /*
   * ----------------------------------------------------
   * PROFILE LOADING SCREEN
   * ----------------------------------------------------
   */
  if (loadingProfile) {
    return (
      <div className="route-loader">
        <span className="loading-spinner" />
        <span>Restoring your career profile...</span>
      </div>
    );
  }

  /*
   * ----------------------------------------------------
   * UI
   * ----------------------------------------------------
   */
  return (
    <div className="onboarding-page">
      <main className="onboarding-content">
        <section className="onboarding-card">
          {/* LOGO + STEP COUNTER (inside the form card) */}
          <div className="onboarding-card-head">
            <img
              src="/hi-logo-nav.svg"
              alt="SmartHire"
              className="brand-logo"
              width="34"
              height="28"
            />

            <span className="onboarding-step">
              Step {step} of {TOTAL_STEPS}
            </span>
          </div>

          <div className="onboarding-progress">
            <div
              className="onboarding-progress-fill"
              style={{
                width: progress,
              }}
            />
          </div>

          <div className="onboarding-header">
            <p className="eyebrow">BUILD YOUR CAREER PROFILE</p>
          </div>

          {/* STEP 1 */}
          {step === 1 && (
            <div className="onboarding-section">
              <h2>What should we call you?</h2>

              <label className="auth-field">
                <span>Username</span>

                <div>
                  <input
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder="e.g. Sai Kalyan"
                    autoFocus
                  />
                </div>
              </label>
            </div>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <Target size={22} />
              </span>

              <h2>What are you interested in?</h2>

              <p>Tell SmartHire the career areas you want to explore.</p>

              <div className="suggestion-grid">
                {INTEREST_SUGGESTIONS.map((item) => {
                  const selected = careerInterests.some(
                    (value) => value.toLowerCase() === item.toLowerCase(),
                  );

                  return (
                    <button
                      type="button"
                      key={item}
                      className={
                        selected
                          ? "suggestion-chip selected"
                          : "suggestion-chip"
                      }
                      onClick={() =>
                        toggleSuggestion(
                          item,
                          careerInterests,
                          setCareerInterests,
                        )
                      }
                    >
                      {item}
                    </button>
                  );
                })}
              </div>

              <div className="tag-input">
                <input
                  value={interestInput}
                  onChange={(event) => setInterestInput(event.target.value)}
                  onKeyDown={(event) => handleEnter(event, addInterest)}
                  placeholder="Other career interest..."
                  autoFocus
                />

                <button
                  type="button"
                  className="button secondary"
                  onClick={addInterest}
                >
                  <Plus size={16} />
                  Add
                </button>
              </div>

              <div className="onboarding-tags">
                {careerInterests.map((item) => (
                  <span className="onboarding-tag" key={item}>
                    {item}

                    <button
                      type="button"
                      onClick={() => removeValue(item, setCareerInterests)}
                    >
                      <X size={13} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <Briefcase size={22} />
              </span>

              <h2>What is your specialization?</h2>

              <p>
                Select the technical areas you want SmartHire to use when
                finding opportunities.
              </p>

              <div className="suggestion-grid">
                {SPECIALIZATION_SUGGESTIONS.map((item) => {
                  const selected = specializations.some(
                    (value) => value.toLowerCase() === item.toLowerCase(),
                  );

                  return (
                    <button
                      type="button"
                      key={item}
                      className={
                        selected
                          ? "suggestion-chip selected"
                          : "suggestion-chip"
                      }
                      onClick={() =>
                        toggleSuggestion(
                          item,
                          specializations,
                          setSpecializations,
                        )
                      }
                    >
                      {item}
                    </button>
                  );
                })}
              </div>

              <div className="tag-input">
                <input
                  value={specializationInput}
                  onChange={(event) =>
                    setSpecializationInput(event.target.value)
                  }
                  onKeyDown={(event) => handleEnter(event, addSpecialization)}
                  placeholder="Other specialization..."
                  autoFocus
                />

                <button
                  type="button"
                  className="button secondary"
                  onClick={addSpecialization}
                >
                  <Plus size={16} />
                  Add
                </button>
              </div>

              <div className="onboarding-tags">
                {specializations.map((item) => (
                  <span className="onboarding-tag" key={item}>
                    {item}

                    <button
                      type="button"
                      onClick={() => removeValue(item, setSpecializations)}
                    >
                      <X size={13} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* STEP 4 */}
          {step === 4 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <Plus size={22} />
              </span>

              <h2>What skills do you have?</h2>

              <p>Add your current technical and professional skills.</p>

              <div className="tag-input">
                <input
                  value={skillInput}
                  onChange={(event) => setSkillInput(event.target.value)}
                  onKeyDown={(event) => handleEnter(event, addSkill)}
                  placeholder="Python, React, FastAPI..."
                  autoFocus
                />

                <button
                  type="button"
                  className="button secondary"
                  onClick={addSkill}
                >
                  <Plus size={16} />
                  Add
                </button>
              </div>

              <div className="onboarding-tags">
                {skills.map((skill) => (
                  <span className="onboarding-tag" key={skill}>
                    {skill}

                    <button
                      type="button"
                      onClick={() => removeValue(skill, setSkills)}
                    >
                      <X size={13} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* STEP 5 */}
          {step === 5 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <ArrowRight size={22} />
              </span>

              <h2>What roles are you targeting?</h2>

              <p>Tell SmartHire which roles you're interested in.</p>

              <div className="tag-input">
                <input
                  value={roleInput}
                  onChange={(event) => setRoleInput(event.target.value)}
                  onKeyDown={(event) => handleEnter(event, addRole)}
                  placeholder="AI Engineer, Software Engineer..."
                  autoFocus
                />

                <button
                  type="button"
                  className="button secondary"
                  onClick={addRole}
                >
                  <Plus size={16} />
                  Add
                </button>
              </div>

              <div className="onboarding-tags">
                {targetRoles.map((role) => (
                  <span className="onboarding-tag" key={role}>
                    {role}

                    <button
                      type="button"
                      onClick={() => removeValue(role, setTargetRoles)}
                    >
                      <X size={13} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* STEP 6 */}
          {step === 6 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <GraduationCap size={22} />
              </span>

              <h2>Tell us about your experience</h2>

              <p>This helps SmartHire match jobs.</p>

              <div className="experience-options">
                {EXPERIENCE_OPTIONS.map((option) => (
                  <button
                    type="button"
                    key={option}
                    className={
                      experience === option
                        ? "experience-option selected"
                        : "experience-option"
                    }
                    onClick={() => setExperience(option)}
                  >
                    <span>{option}</span>

                    {experience === option && <Check size={17} />}
                  </button>
                ))}
              </div>

              <label className="auth-field">
                <span>Graduation Year</span>

                <div>
                  <input
                    type="number"
                    min="1950"
                    max="2100"
                    value={graduationYear}
                    onChange={(event) => setGraduationYear(event.target.value)}
                    placeholder="2026"
                  />
                </div>
              </label>
            </div>
          )}

          {/* STEP 7 */}
          {step === 7 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <FileText size={22} />
              </span>

              <h2>Upload your resume</h2>

              <p>
                SmartHire will analyze your resume and use it as the foundation
                for your career workspace.
              </p>

              <label className="resume-upload-box">
                <input
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleResumeChange}
                  hidden
                />

                {resume ? (
                  <>
                    <FileText size={28} />

                    <strong>{resume.name}</strong>

                    <span>{(resume.size / 1024 / 1024).toFixed(2)} MB</span>
                  </>
                ) : (
                  <>
                    <Upload size={28} />

                    <strong>Choose your resume</strong>

                    <span>PDF or DOCX · Maximum 5 MB</span>
                  </>
                )}
              </label>
            </div>
          )}

          {error && <div className="auth-error onboarding-error">{error}</div>}

          <div className="onboarding-actions">
            {step > 1 ? (
              <button
                type="button"
                className="button secondary"
                onClick={previousStep}
                disabled={busy}
              >
                Back
              </button>
            ) : (
              <span />
            )}

            <button
              type="button"
              className="button primary"
              onClick={nextStep}
              disabled={busy}
            >
              {busy
                ? step === 7
                  ? "Analyzing resume..."
                  : "Saving..."
                : step === 7
                  ? "Analyze Resume"
                  : "Continue"}

              <ArrowRight size={16} />
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
