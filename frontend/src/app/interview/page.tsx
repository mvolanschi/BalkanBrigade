"use client";

import { useEffect, useRef, useState } from "react";
import ColorBends from "../../components/ColorBends";
import { useRouter } from "next/navigation";
import { Loader2, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

// 3 questions for now
const TOTAL_QUESTIONS = 3;
const QUESTION_DURATION = 15; // seconds

type StartSessionResponse = {
  reply: string;
  raw?: any;
};

// Fallback questions if backend / session is not available
const MOCK_QUESTIONS: string[] = [
  "Tell me about yourself and why you're interested in this role.",
  "Describe a time you faced a major challenge at work. How did you handle it?",
  "What's one sustainability initiative you're proud of contributing to?",
];

export default function InterviewPage() {
  const router = useRouter();


  const [question, setQuestion] = useState<string | null>(null);
  const [questionIndex, setQuestionIndex] = useState(1);
  const [timeLeft, setTimeLeft] = useState<number>(QUESTION_DURATION);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoadingQuestion, setIsLoadingQuestion] = useState(true);
  const [isUploadingAnswer, setIsUploadingAnswer] = useState(false);
  const [isProcessingUpload, setIsProcessingUpload] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFinished, setIsFinished] = useState(false);
  const [responseAIinterview, setResponseAIinterview] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const questionAudioRef = useRef<HTMLAudioElement | null>(null);
  const nextQuestionOverrideRef = useRef<string | null>(null);
  const processingUploadRef = useRef(false);

  // Ask for microphone permission and set up MediaRecorder
  useEffect(() => {
    if (typeof window === "undefined") return;

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;

        recorder.addEventListener("dataavailable", (event) => {
          audioChunksRef.current.push(event.data);
        });

        recorder.addEventListener("stop", () => {
          if (processingUploadRef.current) return;

          const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
          audioChunksRef.current = [];
          uploadAnswer(blob);
        });
      })
      .catch((err) => {
        console.error(err);
        setError(
          "Could not access your microphone. Please allow mic permissions and refresh."
        );
      });
  }, [isProcessingUpload]);

  // Fetch question when page loads and whenever questionIndex changes
  useEffect(() => {
    if (questionIndex > TOTAL_QUESTIONS) {
      setIsFinished(true);
      clearTimer();
      return;
    }

    const fetchQuestion = async () => {
      setIsLoadingQuestion(true);
      setError(null);
      setQuestion(null);
      clearTimer();
      setTimeLeft(QUESTION_DURATION);
      setIsRecording(false);

      const override = nextQuestionOverrideRef.current;
      if (override) {
        nextQuestionOverrideRef.current = null;
        setQuestion(override);
        setIsLoadingQuestion(false);
        return;
      }

      const sessionId =
        typeof window !== "undefined"
          ? localStorage.getItem("greenpt_session_id")
          : null;

      const useMockQuestion = () => {
        const mock =
          MOCK_QUESTIONS[questionIndex - 1] ??
          `Practice question ${questionIndex}`;
        setQuestion(mock);
      };

      // No active session → show mock questions
      if (!sessionId) {
        setError(
          "No active session found. Showing practice questions instead."
        );
        useMockQuestion();
        setIsLoadingQuestion(false);
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/session/${sessionId}/start`, {
          method: "POST",
        });

        if (!res.ok) {
          const detail = await res
            .json()
            .catch(() => ({ detail: "Failed to fetch question. Using mock." }));
          setError(
            typeof detail.detail === "string"
              ? `${detail.detail} Using practice questions instead.`
              : "Failed to fetch question. Using practice questions instead."
          );
          useMockQuestion();
        } else {
          const data: StartSessionResponse = await res.json();
          setQuestion(data.reply || `Question ${questionIndex}`);
        }
      } catch (err: any) {
        console.error(err);
        setError(
          (err?.message ?? "Failed to load question.") +
            " Using practice questions instead."
        );
        useMockQuestion();
      } finally {
        setIsLoadingQuestion(false);
      }
    };

    fetchQuestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionIndex]);

  // Timer logic
  const startTimer = () => {
    clearTimer();
    timerIntervalRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearTimer();
          autoAdvance();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const clearTimer = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
  };

  const autoAdvance = () => {
    const recorder = mediaRecorderRef.current;
    
    if (!recorder) {
      console.warn("No recorder available");
      uploadAnswer(null);
      return;
    }

    if (recorder.state === "recording") {
      console.log("Auto-stopping recording due to timer");
      setIsRecording(false);
      recorder.stop();
      // The 'stop' event listener will handle uploadAnswer with the blob
    } else if (recorder.state === "inactive") {
      console.log("Recorder inactive, moving to next question");
      uploadAnswer(null);
    }
  };

  // const autoAdvance = () => {
  //   if (isRecording && mediaRecorderRef.current) {
  //     // this will trigger uploadAnswer in recorder.onstop
  //     setIsRecording(false);
  //     mediaRecorderRef.current.stop();
  //   } else {
  //     uploadAnswer(null);
  //   }
  // };

  // ONE-SHOT: can only start recording once per question
  const handleToggleRecording = () => {
    if (isUploadingAnswer || isLoadingQuestion) return;

    if (!mediaRecorderRef.current) {
      setError(
        "Microphone is not ready yet. Please check permissions and try again."
      );
      return;
    }

    if (isRecording) {
      // do nothing while recording
      return;
    }

    // start recording + start timer
    audioChunksRef.current = [];
    setIsRecording(true);
    setTimeLeft(QUESTION_DURATION);
    startTimer();
    mediaRecorderRef.current.start();
  };

  const uploadAnswer = async (audioBlob: Blob | null) => {
    console.log("In upload answer");

    if (processingUploadRef.current) {
      console.warn("Upload already in progress; ignoring duplicate call");
      return;
    }

    const sessionId =
      typeof window !== "undefined"
        ? localStorage.getItem("greenpt_session_id")
        : null;

    // If no session, just locally advance questions (still practice)
    if (!sessionId) {
      setQuestionIndex((prev) => prev + 1);
      return;
    }

    console.log("We have session id in upload answer");

    let succeeded = false;

    try {
      processingUploadRef.current = true;
      setIsProcessingUpload(true);
      setIsUploadingAnswer(true);
      setError(null);

      if (!audioBlob || audioBlob.size === 0) {
        throw new Error("No audio captured for this answer. Please re-record.");
      }

      const formData = new FormData();
      formData.append("question_index", String(questionIndex));
      formData.append("audio", audioBlob, `answer-${questionIndex}.webm`);

      console.log(`audio blob =  ${audioBlob}`);

      const res = await fetch(`${API_BASE}/session/${sessionId}/message`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const detail = await res
          .json()
          .catch(() => ({ detail: "Failed to upload answer." }));
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : "Failed to upload answer."
        );
      } else {
        const reply = await res.json();
        const nextQuestion = reply.reply || `Question ${questionIndex + 1}`;
        setResponseAIinterview(nextQuestion);
        nextQuestionOverrideRef.current = nextQuestion;
        succeeded = true;
      }

    } catch (err: any) {
      console.error(err);
      setError(err?.message ?? "Failed to upload answer.");
    } finally {
      setIsUploadingAnswer(false);
      setIsProcessingUpload(false);
      processingUploadRef.current = false;
    }

    if (succeeded) {
      setQuestionIndex((prev) => prev + 1);
    }
  };

  useEffect(() => {
    return () => {
      clearTimer();
      questionAudioRef.current?.pause();
      mediaRecorderRef.current?.stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // Full green at 30s → empty at 0s
  const progressPercent = (timeLeft / QUESTION_DURATION) * 100;

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
            Practice interview
          </h1>

          {!isFinished && (
            <p className="text-white/75 text-sm md:text-base text-center">
              Question {Math.min(questionIndex, TOTAL_QUESTIONS)} of{" "}
              {TOTAL_QUESTIONS}
            </p>
          )}

          {error && (
            <p className="text-red-300 text-sm md:text-base text-center max-w-xl">
              {error}
            </p>
          )}

          {isFinished ? (
            <div className="w-full rounded-3xl bg-black/80 border border-green-400/50 shadow-[0_0_55px_rgba(0,255,140,0.45)] backdrop-blur-xl px-10 md:px-14 py-12 flex flex-col items-center gap-6">
              <p className="text-white text-xl md:text-2xl font-semibold text-center">
                You&apos;re done!
              </p>
              <p className="text-white/75 text-sm md:text-base text-center max-w-lg">
                That was all {TOTAL_QUESTIONS} questions. We&apos;re now
                processing your answers to generate detailed feedback for each
                question and suggestions on how you could improve your
                responses.
              </p>
              <Button
                size="lg"
                className="mt-2 bg-white text-black hover:bg-gray-200 font-semibold px-10 py-4 text-lg rounded-full shadow-2xl"
                onClick={() => router.push("/interview-results")}
              >
                View interview feedback
              </Button>
            </div>
          ) : (
            <>
              {/* BIG TIMER ABOVE THE BOX */}
              <div className="flex flex-col items-center gap-4 mt-2">
                <div className="relative h-32 w-32 flex items-center justify-center">
                  {/* outer ring showing remaining time */}
                  <div
                    className="absolute inset-0 rounded-full"
                    style={{
                      background: `conic-gradient(rgba(74,222,128,0.95) ${progressPercent}%, rgba(255,255,255,0.08) ${progressPercent}% 100%)`,
                    }}
                  />
                  {/* inner circle */}
                  <div className="relative h-24 w-24 rounded-full bg-black border border-white/20 flex items-center justify-center">
                    <span className="text-white text-3xl font-semibold">
                      {timeLeft}s
                    </span>
                  </div>
                </div>
                <p className="text-white/70 text-sm md:text-base text-center">
                  You have 5 seconds to answer after you start recording.
                </p>
              </div>

              {/* QUESTION CARD (only question + mic) */}
              <div className="w-full rounded-3xl bg-black/80 border border-green-400/40 shadow-[0_0_55px_rgba(0,255,140,0.45)] backdrop-blur-xl px-8 md:px-12 py-10 flex flex-col gap-8 items-center">
                {isLoadingQuestion ? (
                  <div className="flex flex-col items-center gap-3 py-8">
                    <Loader2 className="h-8 w-8 text-white animate-spin" />
                    <p className="text-white/80 text-sm">
                      Loading next question…
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Question text */}
                    <div className="w-full">
                      <p className="text-white/80 text-sm uppercase tracking-[0.2em] mb-2">
                        Question
                      </p>
                      <p className="text-white text-lg md:text-xl leading-relaxed">
                        {question}
                      </p>
                    </div>

                    {/* Big mic button */}
                    <div className="flex flex-col items-center gap-3 mt-6">
                      <Button
                        type="button"
                        onClick={handleToggleRecording}
                        disabled={
                          isLoadingQuestion || isUploadingAnswer || isRecording
                        }
                        className={[
                          "rounded-full px-12 py-6 text-xl font-semibold shadow-2xl flex items-center gap-3",
                          isRecording
                            ? "bg-red-500 text-white hover:bg-red-400"
                            : "bg-white text-black hover:bg-gray-200",
                        ].join(" ")}
                      >
                        <Mic className="h-7 w-7" />
                        {isRecording ? "Recording…" : "Start recording"}
                      </Button>
                      <p className="text-white/60 text-xs md:text-sm text-center max-w-sm">
                        Press once to start. We&apos;ll record for 5 seconds
                        and move on automatically when the timer hits zero.
                      </p>
                    </div>

                    {isUploadingAnswer && (
                      <p className="text-white/70 text-xs flex items-center gap-2 mt-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Saving your answer…
                      </p>
                    )}
                  </>
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
