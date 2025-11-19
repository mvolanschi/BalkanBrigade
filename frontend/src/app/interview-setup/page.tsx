"use client";

import { useState } from "react";
import ColorBends from "../../components/ColorBends";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

const interviewerBehaviorOptions = [
  "Supportive & coaching",
  "Neutral & professional",
  "Challenging & direct",
];

const difficultyOptions = [
  "Easy / warm-up",
  "Standard role-level",
  "Hard / stretch",
];

const focusOptions = ["More behavioral", "Balanced", "More technical"];

export default function InterviewSetupPage() {
  const router = useRouter();

  const [interviewerBehavior, setInterviewerBehavior] = useState<string | null>(
    null
  );
  const [difficulty, setDifficulty] = useState<string | null>(null);
  const [focus, setFocus] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleStartInterview = async () => {
    setError(null);

    if (!interviewerBehavior || !difficulty || !focus) {
      setError("Please choose an option for each setting before starting.");
      return;
    }

    const sessionId =
      typeof window !== "undefined"
        ? localStorage.getItem("greenpt_session_id")
        : null;

    if (!sessionId) {
      setError("No active session found. Please upload your data again first.");
      return;
    }

    try {
      setIsSubmitting(true);

      // Example backend call – adjust the endpoint to your backend implementation
      const res = await fetch(
        `${API_BASE}/session/${sessionId}/interview-config`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify([
            focusOptions.indexOf(focus!) + 1,
            interviewerBehaviorOptions.indexOf(interviewerBehavior!) + 1,
            difficultyOptions.indexOf(difficulty!) + 1,
          ]),
        }
      );

      if (!res.ok) {
        const detail = await res
          .json()
          .catch(() => ({ detail: "Failed to save interview settings." }));
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : "Failed to save interview settings."
        );
      }

      // On success, go to the interview page
      router.push("/interview");
    } catch (err: any) {
      console.error(err);
      setError(err?.message ?? "Something went wrong starting the interview.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderOptionGroup = (
    label: string,
    description: string,
    options: string[],
    selected: string | null,
    onSelect: (value: string) => void
  ) => (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-white text-lg font-semibold uppercase tracking-[0.15em]">
          {label}
        </p>
        <p className="text-white/70 text-sm mt-2">{description}</p>
      </div>

      <div className="flex flex-wrap gap-3">
        {options.map((opt) => {
          const isActive = selected === opt;
          return (
            <button
              key={opt}
              type="button"
              onClick={() => onSelect(opt)}
              className={[
                "px-5 py-3 rounded-full text-sm md:text-base font-medium border transition-all",
                "backdrop-blur-md",
                isActive
                  ? "bg-green-400/90 text-black border-green-300 shadow-[0_0_18px_rgba(74,222,128,0.8)] scale-[1.02]"
                  : "bg-black/60 text-white/80 border-white/20 hover:border-green-300/80 hover:bg-black/80",
              ].join(" ")}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );

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
            Configure your interview
          </h1>
          <p className="text-white/75 text-sm md:text-base text-center max-w-xl">
            Choose how you want your AI interviewer to behave. We&apos;ll use
            these settings to tailor the questions and tone for your practice
            session.
          </p>

          {/* Card */}
          <div
            className="
              w-full rounded-3xl bg-black/80 border border-green-400/50 
              shadow-[0_0_55px_rgba(0,255,140,0.45)] backdrop-blur-xl 
              px-10 md:px-14 py-10 flex flex-col gap-12
            "
          >
            {renderOptionGroup(
              "Focus of questions",
              "Should we lean more into technical depth or behavioral / soft skills?",
              focusOptions,
              focus,
              setFocus
            )}
            {renderOptionGroup(
              "Interviewer behaviour",
              "Pick the style that best matches what you want to practice for.",
              interviewerBehaviorOptions,
              interviewerBehavior,
              setInterviewerBehavior
            )}

            {renderOptionGroup(
              "Difficulty of questions",
              "Control how challenging the interview will feel.",
              difficultyOptions,
              difficulty,
              setDifficulty
            )}

            {error && (
              <p className="text-red-300 text-sm md:text-base mt-1">{error}</p>
            )}
          </div>
          <div className="w-full flex justify-center mt-8">
            <Button
              size="lg"
              onClick={handleStartInterview}
              disabled={isSubmitting}
              className="
                  bg-white text-black hover:bg-gray-200 font-semibold
                  px-12 py-6 text-xl rounded-full shadow-2xl
                  flex items-center gap-3 pointer-events-auto disabled:opacity-60
                "
            >
              {isSubmitting && <Loader2 className="h-6 w-6 animate-spin" />}
              {isSubmitting ? "Starting interview..." : "Begin interview"}
            </Button>
          </div>
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
