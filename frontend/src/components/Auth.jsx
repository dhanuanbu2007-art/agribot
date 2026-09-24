import React, { useState } from "react";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  sendPasswordResetEmail,
} from "firebase/auth";
import {
  Sprout,
  Leaf,
  Mail,
  Lock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Eye,
  EyeOff,
} from "lucide-react";
import { auth } from "../firebase";
import "./Auth.css";

export default function Auth({ onLogin }) {
  const [isSignup, setIsSignup] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const clearMessages = () => {
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    clearMessages();

    const cleanEmail = email.trim();

    if (!cleanEmail || !password) {
      setError("Please enter your email and password.");
      return;
    }

    if (isSignup && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (isSignup && password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    try {
      setLoading(true);

      let userCredential;

      if (isSignup) {
        userCredential = await createUserWithEmailAndPassword(
          auth,
          cleanEmail,
          password
        );
      } else {
        userCredential = await signInWithEmailAndPassword(
          auth,
          cleanEmail,
          password
        );
      }

      if (onLogin && userCredential?.user) {
        onLogin(userCredential.user);
      }
    } catch (firebaseError) {
      console.error("[AgriGuide Auth Error]", firebaseError);

      switch (firebaseError.code) {
        case "auth/email-already-in-use":
          setError("An account already exists with this email address.");
          break;
        case "auth/invalid-email":
          setError("Please enter a valid email address.");
          break;
        case "auth/weak-password":
          setError("Password is too weak. Please use at least 6 characters.");
          break;
        case "auth/invalid-credential":
        case "auth/user-not-found":
        case "auth/wrong-password":
          setError("Incorrect email or password. Please verify your credentials.");
          break;
        case "auth/too-many-requests":
          setError("Too many attempts. Please wait a few moments and try again.");
          break;
        default:
          setError("Authentication failed. Please check your network and try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    clearMessages();

    const cleanEmail = email.trim();

    if (!cleanEmail) {
      setError("Enter your email address above to receive a password reset link.");
      return;
    }

    try {
      setResetLoading(true);
      await sendPasswordResetEmail(auth, cleanEmail);
      setSuccess("Password reset instructions sent. Please check your email inbox.");
    } catch (firebaseError) {
      console.error("[AgriGuide Password Reset]", firebaseError);

      if (firebaseError.code === "auth/invalid-email") {
        setError("Please enter a valid email address.");
      } else if (firebaseError.code === "auth/user-not-found") {
        setError("No account found with this email address.");
      } else {
        setError("Unable to send reset email. Please try again later.");
      }
    } finally {
      setResetLoading(false);
    }
  };

  const switchMode = () => {
    setIsSignup((current) => !current);
    setPassword("");
    setConfirmPassword("");
    clearMessages();
  };

  return (
    <main className="auth-split-page">
      {/* ── LEFT HERO PANEL: Agriculture Image & Brand Story ── */}
      <section className="auth-hero-panel" aria-label="Agriculture Overview">
        <div className="auth-hero-bg-wrapper">
          <img
            src="/agriculture-login-bg.jpg"
            alt="Farmer in lush green agricultural field"
            className="auth-hero-img"
          />
          <div className="auth-hero-overlay" />
        </div>

        <div className="auth-hero-content">
          <div className="auth-hero-brand">
            <div className="auth-hero-logo-box">
              <Sprout size={28} strokeWidth={2.4} />
            </div>
            <div>
              <span className="auth-hero-brand-name">AgriGuide</span>
              <span className="auth-hero-brand-tag">Intelligent Agriculture Advisory</span>
            </div>
          </div>

          <div className="auth-hero-center">
            <div className="auth-pill-badge">
              <Sparkles size={14} />
              <span>RAG-Powered Farming Intelligence</span>
            </div>

            <h1 className="auth-hero-headline">
              Smarter farming for a greener tomorrow.
            </h1>

            <p className="auth-hero-description">
              Empowering farmers with instant guidance on crop cultivation, soil health,
              disease management, pest control, and government subsidies.
            </p>

            {/* Feature Highlights */}
            <div className="auth-feature-list">
              <div className="auth-feature-item">
                <div className="auth-feature-icon">🌾</div>
                <div className="auth-feature-text">
                  <strong>Crop Cultivation & Yield</strong>
                  <span>Best sowing methods, irrigation, and nutrition schedules</span>
                </div>
              </div>

              <div className="auth-feature-item">
                <div className="auth-feature-icon">🔬</div>
                <div className="auth-feature-text">
                  <strong>Disease & Pest Identification</strong>
                  <span>Rapid detection and eco-friendly bio-control measures</span>
                </div>
              </div>

              <div className="auth-feature-item">
                <div className="auth-feature-icon">🏛️</div>
                <div className="auth-feature-text">
                  <strong>Government Schemes & Grants</strong>
                  <span>Up-to-date subsidy information and financial support</span>
                </div>
              </div>
            </div>
          </div>

          <div className="auth-hero-footer">
            <ShieldCheck size={18} className="shield-icon" />
            <span>Secure farmer access powered by Firebase Authentication</span>
          </div>
        </div>
      </section>

      {/* ── RIGHT PANEL: Clean Agriculture Login / Signup Form ── */}
      <section className="auth-form-panel" aria-label="Sign In or Sign Up">
        <div className="auth-form-card">
          {/* Header */}
          <div className="auth-form-header">
            <div className="auth-logo-badge">
              <Leaf size={24} className="leaf-icon" />
            </div>
            <h2 className="auth-title">
              {isSignup ? "Create your account" : "Welcome to AgriGuide"}
            </h2>
            <p className="auth-subtitle">
              {isSignup
                ? "Join AgriGuide to access personalized farming knowledge"
                : "Your intelligent agriculture assistant"}
            </p>
          </div>

          {/* Form */}
          <form className="auth-actual-form" onSubmit={handleSubmit} noValidate>
            {/* Email Field */}
            <div className="auth-form-group">
              <label htmlFor="auth-email">Email Address</label>
              <div className="auth-input-wrapper">
                <Mail size={18} className="auth-input-icon" />
                <input
                  id="auth-email"
                  type="email"
                  placeholder="farmer@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  disabled={loading || resetLoading}
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="auth-form-group">
              <div className="auth-label-row">
                <label htmlFor="auth-password">Password</label>
                {!isSignup && (
                  <button
                    type="button"
                    className="auth-forgot-btn"
                    onClick={handleForgotPassword}
                    disabled={loading || resetLoading}
                  >
                    {resetLoading ? "Sending link..." : "Forgot password?"}
                  </button>
                )}
              </div>
              <div className="auth-input-wrapper">
                <Lock size={18} className="auth-input-icon" />
                <input
                  id="auth-password"
                  type={showPassword ? "text" : "password"}
                  placeholder={isSignup ? "Create a secure password" : "Enter your password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={isSignup ? "new-password" : "current-password"}
                  disabled={loading || resetLoading}
                  required
                />
                <button
                  type="button"
                  className="auth-eye-btn"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Confirm Password (Sign up mode) */}
            {isSignup && (
              <div className="auth-form-group">
                <label htmlFor="auth-confirm-password">Confirm Password</label>
                <div className="auth-input-wrapper">
                  <Lock size={18} className="auth-input-icon" />
                  <input
                    id="auth-confirm-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Repeat your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                    disabled={loading || resetLoading}
                    required
                  />
                </div>
              </div>
            )}

            {/* Alert Messages */}
            {error && (
              <div className="auth-alert error" role="alert">
                <AlertCircle size={18} className="alert-icon" />
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div className="auth-alert success" role="status">
                <CheckCircle2 size={18} className="alert-icon" />
                <span>{success}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading || resetLoading}
            >
              {loading ? (
                <span className="auth-btn-loading">
                  <span className="auth-spinner" />
                  {isSignup ? "Setting up account..." : "Logging in..."}
                </span>
              ) : (
                <span className="auth-btn-text">
                  <span>{isSignup ? "Create Account" : "Log In to AgriGuide"}</span>
                  <ArrowRight size={18} className="btn-arrow" />
                </span>
              )}
            </button>
          </form>

          {/* Toggle between Login and Signup */}
          <div className="auth-switch-box">
            <span className="auth-switch-text">
              {isSignup ? "Already have an account?" : "New to AgriGuide?"}
            </span>
            <button
              type="button"
              className="auth-switch-btn"
              onClick={switchMode}
              disabled={loading || resetLoading}
            >
              {isSignup ? "Sign in instead" : "Create an account"}
            </button>
          </div>

          {/* Clean Agriculture Guarantee */}
          <div className="auth-footer-note">
            <span className="leaf-dot">🌱</span>
            <span>Dedicated AI assistance for farmers & agricultural researchers</span>
          </div>
        </div>
      </section>
    </main>
  );
}