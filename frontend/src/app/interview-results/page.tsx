"use client";

import { useEffect, useState } from "react";
import ColorBends from "../../components/ColorBends";
import { Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type QuestionFeedback = {
  question: string;
  feedback: string;
  suggested_answer?: string;
};

// Mock feedback if backend / session not available
const MOCK_FEEDBACK: QuestionFeedback[] = [
  {
    question: "Tell me about yourself and why you’re interested in this role.",
    feedback:
      "You gave a solid overview, but you could tie your story more clearly to this specific role and company. Focus on 2–3 key themes in your background that line up with the job description, and end with why this opportunity excites you.",
    suggested_answer:
      "A stronger answer would briefly cover your current role, 1–2 relevant achievements, then connect those to the mission and responsibilities of this job, finishing with a clear statement of motivation.",
  },
  {
    question:
      "Describe a time you faced a major challenge at work. How did you handle it?",
    feedback:
      "Your example was relevant, but the structure could be sharper. Use a clear STAR format (Situation, Task, Action, Result) and spend most of the time on your actions and the measurable outcome.",
    suggested_answer:
      "Pick one concrete project, explain the challenge in 1–2 sentences, then describe 3–4 specific actions you took and finish with numbers (time saved, improvement %, impact on team or customer).",
  },
  {
    question:
      "What’s one sustainability initiative you’re proud of contributing to?",
    feedback:
      "You mentioned good intentions, but the impact could be more tangible. Interviewers are looking for concrete contributions, metrics, and your personal role rather than just team-level efforts.",
    suggested_answer:
      "Describe the initiative, your exact responsibilities, how you measured success and what changed as a result (e.g. reduction in waste/emissions, increased participation, process improvements).",
  },
];

export default function InterviewResultsPage() {
  const [items, setItems] = useState<QuestionFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);

  useEffect(() => {
    const applyFeedback = (parsed: QuestionFeedback[]) => {
      if (!parsed || parsed.length === 0) {
        setItems(MOCK_FEEDBACK);
        setUsingFallback(true);
      } else {
        setItems(parsed);
      }
    };

    const applyFallback = (reason?: string) => {
      if (reason) {
        setError(
          `${reason} Showing example interview feedback so you can see how this page will look.`
        );
      } else {
        setError("Using example interview feedback instead of live analysis.");
      }
      setUsingFallback(true);
      setItems(MOCK_FEEDBACK);
    };

    const fetchFeedback = async () => {
      try {
        setIsLoading(true);
        setError(null);
        setUsingFallback(false);

        const sessionId =
          typeof window !== "undefined"
            ? localStorage.getItem("greenpt_session_id")
            : null;

        if (!sessionId) {
          applyFallback("No active session found.");
          return;
        }

        const prompt = `
Using the interview audio answers and questions already attached to this session, generate specific feedback for each question.

Respond EXACTLY in this JSON format and nothing else:

{
  "items": [
    {
      "question": "Original question text here",
      "feedback": "Concrete feedback on how the candidate could improve their answer.",
      "suggested_answer": "An example of a stronger, more structured answer in 3–6 sentences."
    }
  ]
}

Do not include any additional commentary outside the JSON.
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
            .catch(() => ({ detail: "Failed to get interview feedback." }));
          throw new Error(
            typeof detail.detail === "string"
              ? detail.detail
              : "Failed to get interview feedback."
          );
        }

        const data: { reply: string } = await res.json();
        const raw = (data.reply || "").trim();

        if (!raw) {
          applyFallback("Got an empty response from the backend.");
          return;
        }

        // Try to parse JSON; if it fails, fall back to mock
        try {
          const parsed = JSON.parse(raw) as { items?: QuestionFeedback[] };
          if (!parsed.items || !Array.isArray(parsed.items)) {
            applyFallback("Unexpected feedback format from backend.");
            return;
          }
          applyFeedback(parsed.items);
        } catch (e) {
          console.error("Failed to parse feedback JSON", e);
          applyFallback("Could not parse interview feedback from backend.");
        }
      } catch (err: any) {
        console.error(err);
        applyFallback(err?.message ?? "Failed to load interview feedback.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeedback();
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
        <div className="max-w-5xl w-full flex flex-col items-center gap-6 pointer-events-auto">
          {/* Title */}
          <h1 className="text-white text-3xl md:text-4xl font-bold text-center drop-shadow-2xl mt-4">
            Interview feedback
          </h1>
          <p className="text-white/75 text-sm md:text-base text-center max-w-2xl">
            Here&apos;s how your answers performed, question by question. Use
            the suggestions and example responses below to sharpen your story
            for real interviews.
          </p>

          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col items-center gap-3 mt-4">
              <Loader2 className="h-8 w-8 text-white animate-spin" />
              <p className="text-white/80 text-sm">
                Analyzing your interview answers and generating feedback…
              </p>
            </div>
          )}

          {/* Error banner */}
          {!isLoading && error && (
            <p className="text-yellow-200 text-sm text-center max-w-xl">
              {error}
            </p>
          )}

          {/* Feedback list */}
          {!isLoading && items.length > 0 && (
            <div className="w-full flex flex-col gap-5 mt-2 pb-10">
              {items.map((item, idx) => (
                <div
                  key={`${idx}-${item.question.slice(0, 20)}`}
                  className="w-full rounded-3xl bg-black/80 border border-green-400/35 shadow-[0_0_45px_rgba(0,255,140,0.35)] backdrop-blur-xl px-6 md:px-8 py-6 flex flex-col gap-4"
                >
                  <div className="flex flex-col gap-1">
                    <p className="text-green-300 text-xs uppercase tracking-[0.25em]">
                      Question {idx + 1}
                    </p>
                    <p className="text-white text-base md:text-lg leading-relaxed">
                      {item.question}
                    </p>
                  </div>

                  <div className="flex flex-col gap-1">
                    <p className="text-white/80 text-xs uppercase tracking-[0.2em]">
                      How you could improve
                    </p>
                    <p className="text-white/90 text-sm md:text-base leading-relaxed">
                      {item.feedback}
                    </p>
                  </div>

                  {item.suggested_answer && (
                    <div className="flex flex-col gap-1">
                      <p className="text-white/80 text-xs uppercase tracking-[0.2em]">
                        Example stronger answer
                      </p>
                      <p className="text-white/85 text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                        {item.suggested_answer}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {usingFallback && !isLoading && (
            <p className="text-white/60 text-xs text-center mb-6">
              Currently showing example feedback while live interview analysis
              is still being wired up.
            </p>
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
