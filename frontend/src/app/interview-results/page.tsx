"use client";

import { useEffect, useRef, useState } from "react";
import ColorBends from "../../components/ColorBends";
import { Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function InterviewResultsPage() {
  const [summary, setSummary] = useState<string | null>(null);
  const [score, setScore] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 👇 guard so we only fetch once even if React runs effects twice in dev
  const hasFetchedSummaryRef = useRef(false);

  // fallback demonstration content
  const FALLBACK_SUMMARY = `
Your interview summary is not available, so here is an example:

SCORE: 72

STRENGTHS:
- You communicate clearly and stay on topic.
- You provide relevant examples that match the questions.
- Your motivation for the role comes across as genuine.

IMPROVEMENTS:
- Add more concrete metrics and outcomes to your stories.
- Use a clearer structure (STAR) for behavioral questions.
- Make the link between your experience and this specific role more explicit.

SUMMARY:
Overall, you have a strong foundation and good communication skills. With a bit more focus on structure, impact, and tailoring your answers to the job description, you can significantly improve your interview performance.
  `.trim();

  useEffect(() => {
    // 🔒 Prevent double fetch in React Strict Mode (dev)
    if (hasFetchedSummaryRef.current) return;
    hasFetchedSummaryRef.current = true;

    const applySummary = (reply: string) => {
      // ❌ Strip markdown bold markers so we never render ** in UI
      const cleaned = reply.replace(/\*\*/g, "").trim();
      setSummary(cleaned);

      // extract SCORE from cleaned text
      const match = cleaned.match(/SCORE:\s*(\d{1,3})/i);
      if (match) {
        const n = parseInt(match[1], 10);
        if (!Number.isNaN(n)) {
          const clamped = Math.max(0, Math.min(100, n));
          setScore(clamped);
        } else {
          setScore(null);
        }
      } else {
        setScore(null);
      }
    };

    const fetchSummary = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const sessionId =
          typeof window !== "undefined"
            ? localStorage.getItem("greenpt_session_id")
            : null;

        if (!sessionId) {
          setError("No active session found.");
          applySummary(FALLBACK_SUMMARY);
          return;
        }

        // IMPORTANT: this is a GET and backend returns { reply, pairs_summarized }
        const res = await fetch(`${API_BASE}/session/${sessionId}/summary`);

        if (!res.ok) {
          const detail = await res
            .json()
            .catch(() => ({ detail: "Failed to fetch interview summary." }));
          throw new Error(
            typeof detail.detail === "string"
              ? detail.detail
              : "Failed to fetch interview summary."
          );
        }

        const data: { reply?: string; pairs_summarized?: number } =
          await res.json();

        if (!data.reply || typeof data.reply !== "string") {
          setError("Invalid summary format from backend.");
          applySummary(FALLBACK_SUMMARY);
          return;
        }

        applySummary(data.reply);
      } catch (err: any) {
        console.error(err);
        setError(err?.message || "Failed to load interview summary.");
        applySummary(FALLBACK_SUMMARY);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, [FALLBACK_SUMMARY]);

  // Parse strengths / improvements / summary out of the big string
  let strengths = "";
  let improvements = "";
  let overallSummary = "";

  if (summary) {
    const strengthsMatch = summary.match(
      /STRENGTHS:([\s\S]*?)(?=IMPROVEMENTS:|$)/i
    );
    const improvementsMatch = summary.match(
      /IMPROVEMENTS:([\s\S]*?)(?=SUMMARY:|$)/i
    );
    const summaryMatch = summary.match(/SUMMARY:([\s\S]*?)$/i);

    strengths = strengthsMatch ? strengthsMatch[1].trim() : "";
    improvements = improvementsMatch ? improvementsMatch[1].trim() : "";
    overallSummary = summaryMatch
      ? summaryMatch[1].trim()
      : summary?.trim() ?? "";
  }

  return (
    <div className="relative w-full h-screen overflow-hidden bg-black">
      {/* Background */}
      <ColorBends
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 0 }}
        colors={["#00cc00", "#00aa00", "#00dd44", "#00bb55"]}
        rotation={45}
        autoRotate={1}
        speed={0.2}
        scale={1.0}
        frequency={1.2}
        warpStrength={1.0}
        mouseInfluence={0.8}
        parallax={0.5}
        noise={0.05}
        transparent={false}
      />

      {/* Content */}
      <div
        className="absolute inset-0 flex flex-col items-center px-4 py-8 pointer-events-none overflow-y-auto"
        style={{ zIndex: 999 }}
      >
        <div className="max-w-6xl w-full flex flex-col items-center gap-6 pointer-events-auto">
          {/* Title */}
          <h1 className="text-white text-3xl md:text-4xl font-bold text-center drop-shadow-2xl mt-4">
            Interview Summary
          </h1>
          <p className="text-white/75 text-sm md:text-base text-center max-w-2xl">
            Here&apos;s your overall interview performance summary, including
            score, strengths, and areas to improve.
          </p>

          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col items-center gap-3 mt-4">
              <Loader2 className="h-8 w-8 text-white animate-spin" />
              <p className="text-white/80 text-sm">
                Fetching your interview summary…
              </p>
            </div>
          )}

          {/* Error */}
          {!isLoading && error && (
            <p className="text-yellow-200 text-sm text-center max-w-xl">
              {error}
            </p>
          )}

          {/* Main content */}
          {!isLoading && summary && (
            <>
              {/* Score display (same vibe as summary page) */}
              <div className="flex flex-col items-center gap-1 mt-2 mb-4">
                <p className="text-white/60 text-xs uppercase tracking-[0.25em]">
                  Overall interview score
                </p>
                <div className="flex items-baseline gap-3">
                  <span className="text-6xl md:text-7xl font-extrabold text-green-300 drop-shadow-[0_0_25px_rgba(0,255,140,0.8)]">
                    {score !== null ? score : "N/A"}
                  </span>
                  {score !== null && (
                    <span className="text-white/80 text-2xl">/ 100</span>
                  )}
                </div>
              </div>

              {/* Three boxes: strengths, improvements, summary */}
              <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                {/* Strengths */}
                {strengths && (
                  <div className="rounded-3xl bg-emerald-950/80 border border-emerald-400/70 shadow-[0_0_40px_rgba(34,197,94,0.5)] backdrop-blur-xl px-7 py-6 min-h-[280px] overflow-y-auto">
                    <h3 className="text-green-300 text-base font-bold mb-4 uppercase tracking-wider">
                      Strengths
                    </h3>
                    <div className="text-white/90 text-sm whitespace-pre-wrap leading-relaxed">
                      {strengths}
                    </div>
                  </div>
                )}

                {/* Improvements */}
                {improvements && (
                  <div className="rounded-3xl bg-amber-950/80 border border-amber-400/70 shadow-[0_0_40px_rgba(245,158,11,0.5)] backdrop-blur-xl px-7 py-6 min-h-[280px] overflow-y-auto">
                    <h3 className="text-yellow-300 text-base font-bold mb-4 uppercase tracking-wider">
                      Improvements
                    </h3>
                    <div className="text-white/90 text-sm whitespace-pre-wrap leading-relaxed">
                      {improvements}
                    </div>
                  </div>
                )}

                {/* Summary */}
                {overallSummary && (
                  <div className="rounded-3xl bg-slate-950/80 border border-white/40 shadow-[0_0_45px_rgba(255,255,255,0.35)] backdrop-blur-xl px-7 py-6 min-h-[280px] overflow-y-auto">
                    <h3 className="text-white/90 text-base font-bold mb-4 uppercase tracking-wider">
                      Summary
                    </h3>
                    <div className="text-white/90 text-sm whitespace-pre-wrap leading-relaxed">
                      {overallSummary}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Powered by GreenPT */}
      <div className="absolute bottom-6 left-6" style={{ zIndex: 999 }}>
        <p className="text-white/95 text-2xl md:text-3xl font-extrabold drop-shadow-[0_0_15px_rgba(0,255,100,0.5)] tracking-wide">
          Powered by <span className="text-green-300 font-black">GreenPT</span>
        </p>
      </div>
    </div>
  );
}
