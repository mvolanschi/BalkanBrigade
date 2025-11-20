"use client";

import { useEffect, useRef, useState } from "react";
import ColorBends from "../../components/ColorBends";
import { Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function InterviewResultsPage() {
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 👇 NEW: guard so we only fetch once even if React runs effects twice in dev
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
          setSummary(FALLBACK_SUMMARY);
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
          setSummary(FALLBACK_SUMMARY);
          return;
        }

        setSummary(data.reply.trim());
      } catch (err: any) {
        console.error(err);
        setError(err?.message || "Failed to load interview summary.");
        setSummary(FALLBACK_SUMMARY);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, [FALLBACK_SUMMARY]);

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
        <div className="max-w-4xl w-full flex flex-col items-center gap-6 pointer-events-auto">
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

          {/* Centered Summary Box */}
          {!isLoading && summary && (
            <div className="w-full max-w-3xl mx-auto mt-4 mb-10 rounded-3xl bg-black/80 border border-green-400/45 shadow-[0_0_55px_rgba(0,255,140,0.45)] backdrop-blur-xl px-8 md:px-10 py-8">
              <p className="text-white/80 text-xs uppercase tracking-[0.25em] mb-3">
                Overall Summary
              </p>
              <p className="text-white/90 text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                {summary}
              </p>
            </div>
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
