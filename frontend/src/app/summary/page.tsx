"use client";

import { useEffect, useState, useRef } from "react";
import ColorBends from "../../components/ColorBends";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

// Fallback mock summary if backend / session is not available
const FALLBACK_ANALYSIS = `
SCORE: 78

STRENGTHS:
- Strong alignment between your past experience and the core responsibilities of this role.
- Clear motivation for working in a mission-driven / sustainability-focused organisation.
- CV structure is clean and easy to scan, with relevant keywords likely to be picked up by ATS systems.
- Demonstrated ownership of projects and measurable impact in previous roles.

IMPROVEMENTS:
- Tailor your profile summary to explicitly mention this company and the role title.
- Reorder experience so the most relevant and recent items for this role appear at the top.
- Add 2–3 bullet points under each role that quantify impact (numbers, % improvements, time saved, revenue, etc.).
- Mirror key terms from the job description (tools, frameworks, responsibilities) where they genuinely match your experience.
- Briefly highlight any sustainability-related initiatives, volunteering or side projects more prominently.

SUMMARY:
- Overall, you are a solid match for this role. With some light tailoring to this specific job description and company, your profile would likely stand out strongly in the initial screening.
- Focus on making your most relevant skills and outcomes impossible to miss in the first half of your CV.
- After these tweaks, your match score would likely increase further and your chances of moving to the interview stage should be significantly higher.
`.trim();

export default function SummaryPage() {
  const [score, setScore] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);

  const router = useRouter();

  // 🔒 guard to avoid double fetch in React StrictMode
  const hasFetchedRef = useRef(false);

  useEffect(() => {
    // prevent running twice in dev StrictMode
    if (hasFetchedRef.current) return;
    hasFetchedRef.current = true;

    const applySummary = (reply: string) => {
      setAnalysis(reply);

      const match = reply.match(/SCORE:\s*(\d{1,3})/i);
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

    const applyFallback = (reason?: string) => {
      if (reason) {
        setError(`${reason} Showing example feedback instead.`);
      } else {
        setError("Using example feedback instead of live analysis.");
      }
      setUsingFallback(true);
      applySummary(FALLBACK_ANALYSIS);
    };

    const fetchSummary = async () => {
      try {
        setIsLoading(true);
        setError(null);
        setUsingFallback(false);

        const sessionId =
          typeof window !== "undefined"
            ? localStorage.getItem("greenpt_session_id")
            : null;

        if (!sessionId) {
          applyFallback(
            "No active session found. Please upload your data again."
          );
          return;
        }

        console.log(`session id: ${sessionId}`);

        const prompt = `
Using the candidate CV, job description and company info already attached to this session, do a focused analysis.

Respond EXACTLY in this format:

SCORE: <number between 0 and 100>

STRENGTHS:
- ...

IMPROVEMENTS:
- ...

SUMMARY:
- ...

Do not ask any questions back, just provide this analysis.
`.trim();

        const res = await fetch(`${API_BASE}/session/${sessionId}/message`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ content: prompt }),
        });

        if (!res.ok) {
          const detail = await res
            .json()
            .catch(() => ({ detail: "Failed to get summary from backend" }));
          throw new Error(
            typeof detail.detail === "string"
              ? detail.detail
              : "Failed to get summary."
          );
        }

        const data: { reply: string } = await res.json();
        const reply = (data.reply || "").trim();

        if (!reply) {
          // Backend responded but with an empty reply — use fallback
          applyFallback("Got an empty response from the backend.");
          return;
        }

        applySummary(reply);
      } catch (err: any) {
        console.error(err);
        applyFallback(err?.message ?? "Failed to load summary.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, []);

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
        <div className="max-w-7xl w-full flex flex-col items-center gap-6 pointer-events-auto">
          {/* Title */}
          <h1 className="text-white text-3xl md:text-4xl font-bold text-center drop-shadow-2xl mt-4">
            Match summary & feedback
          </h1>

          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col items-center gap-3 mt-4">
              <Loader2 className="h-8 w-8 text-white animate-spin" />
              <p className="text-white/80 text-sm">
                Analyzing your CV, job description and company details…
              </p>
            </div>
          )}

          {/* Error banner (but still showing fallback content) */}
          {!isLoading && error && (
            <p className="text-yellow-200 text-sm text-center max-w-xl">
              {error}
              {usingFallback &&
                " This is demo feedback so you can see how the output looks."}
            </p>
          )}

          {/* Main content */}
          {!isLoading &&
            (() => {
              // Parse sections from analysis
              const strengthsMatch = analysis.match(
                /STRENGTHS:([\s\S]*?)(?=IMPROVEMENTS:|$)/i
              );
              const improvementsMatch = analysis.match(
                /IMPROVEMENTS:([\s\S]*?)(?=SUMMARY:|$)/i
              );
              const summaryMatch = analysis.match(/SUMMARY:([\s\S]*?)$/i);

              const strengths = strengthsMatch ? strengthsMatch[1].trim() : "";
              const improvements = improvementsMatch
                ? improvementsMatch[1].trim()
                : "";
              const summary = summaryMatch ? summaryMatch[1].trim() : "";

              return (
                <>
                  {/* Score display (no box) */}
                  <div className="flex flex-col items-center gap-1 mt-2 mb-4">
                    <p className="text-white/60 text-xs uppercase tracking-[0.25em]">
                      Overall match
                    </p>
                    <div className="flex items-baseline gap-3">
                      <span className="text-6xl md:text-7xl font-extrabold text-green-300 drop-shadow-[0_0_25px_rgba(0,255,140,0.8)]">
                        {score !== null ? score : "N/A"}
                      </span>
                      {score !== null && (
                        <span className="text-white/80 text-2xl">/ 100</span>
                      )}
                    </div>
                    {usingFallback && (
                      <p className="text-white/60 text-xs mt-1">
                        Currently showing example score while the live analysis
                        is unavailable.
                      </p>
                    )}
                  </div>

                  {/* Three boxes in a row */}
                  <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Strengths */}
                    {strengths && (
                      <div className="rounded-3xl bg-emerald-950/80 border border-emerald-400/70 shadow-[0_0_40px_rgba(34,197,94,0.5)] backdrop-blur-xl px-7 py-6 min-h-[500px] overflow-y-auto">
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
                      <div className="rounded-3xl bg-amber-950/80 border border-amber-400/70 shadow-[0_0_40px_rgba(245,158,11,0.5)] backdrop-blur-xl px-7 py-6 min-h-[500px] overflow-y-auto">
                        <h3 className="text-yellow-300 text-base font-bold mb-4 uppercase tracking-wider">
                          Improvements
                        </h3>
                        <div className="text-white/90 text-sm whitespace-pre-wrap leading-relaxed">
                          {improvements}
                        </div>
                      </div>
                    )}

                    {/* Summary */}
                    {summary && (
                      <div className="rounded-3xl bg-slate-950/80 border border-white/40 shadow-[0_0_45px_rgba(255,255,255,0.35)] backdrop-blur-xl px-7 py-6 min-h-[500px] overflow-y-auto">
                        <h3 className="text-white/90 text-base font-bold mb-4 uppercase tracking-wider">
                          Summary
                        </h3>
                        <div className="text-white/90 text-sm whitespace-pre-wrap leading-relaxed">
                          {summary}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Go to interview setup button */}
                  <div className="w-full flex justify-center mt-6">
                    <Button
                      size="lg"
                      onClick={() => router.push("/interview-setup")}
                      className="
      mt-2 bg-white text-black hover:bg-gray-200 font-semibold 
      px-12 py-6 text-xl rounded-full shadow-2xl pointer-events-auto 
      disabled:opacity-60 flex items-center gap-3
    "
                    >
                      Configure Interview & Continue
                    </Button>
                  </div>
                </>
              );
            })()}
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
