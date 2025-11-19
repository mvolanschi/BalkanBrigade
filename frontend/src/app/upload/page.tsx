"use client";

import ColorBends from "../../components/ColorBends";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { FileText, FileSearch, Building2, Loader2 } from "lucide-react";

export default function UploadPage() {
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [companyDetails, setCompanyDetails] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cvInputRef = useRef<HTMLInputElement | null>(null);

  const handleSubmit = async () => {
    setError(null);

    if (!cvFile) {
      setError("Please upload your CV first.");
      return;
    }
    if (!jobDescription.trim()) {
      setError("Please paste the job description.");
      return;
    }

    try {
      setIsLoading(true);

      const formData = new FormData();
      formData.append("cv", cvFile);
      formData.append("job_description", jobDescription);
      formData.append("company_info", companyDetails);

      const res = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      console.log("Analysis result:", data);
      // later: router.push("/results")
    } catch (err: any) {
      console.error(err);
      setError("Something went wrong while sending data.");
    } finally {
      setIsLoading(false);
    }
  };

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
        className="absolute inset-0 flex flex-col items-center justify-center px-4 pointer-events-none"
        style={{ zIndex: 999 }}
      >
        <div className="max-w-6xl w-full flex flex-col items-center gap-8 -translate-y-6">
          {/* Title */}
          <h1 className="text-white text-5xl md:text-6xl font-bold text-center drop-shadow-2xl pointer-events-auto">
            Upload your data to start the analysis
          </h1>

          {/* Error message */}
          {error && (
            <p className="text-red-300 text-lg pointer-events-auto">{error}</p>
          )}

          {/* Grid of 3 LARGER, FANCY boxes */}
          <div className="grid gap-10 w-full max-w-6xl md:grid-cols-3 pointer-events-auto">
            {/* Upload CV */}
            <div className="rounded-3xl bg-black/65 border border-white/15 p-10 backdrop-blur-xl min-h-[330px] shadow-[0_0_35px_rgba(0,0,0,0.8)] transition-transform transition-shadow duration-300 hover:-translate-y-2 hover:border-green-400/80 hover:shadow-[0_0_45px_rgba(0,255,140,0.35)]">
              <div className="flex items-center gap-3 mb-4">
                <FileText className="h-7 w-7 text-green-300" />
                <h2 className="text-white text-2xl font-bold">Upload CV</h2>
              </div>

              <p className="text-base text-white/80 mb-6">
                PDF or DOCX. We’ll extract your skills, experience and
                education.
              </p>

              <input
                ref={cvInputRef} // 👈 attach ref
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                className="block w-full text-base text-white file:mr-3 file:rounded-xl file:border-0 file:bg-white file:px-4 file:py-2 file:text-sm file:font-semibold file:text-black hover:file:bg-gray-200 cursor-pointer"
              />

              {cvFile && (
                <div className="mt-4 flex items-center justify-between bg-white/5 border border-white/10 rounded-xl px-4 py-3">
                  <p className="text-sm text-green-300 truncate">
                    {cvFile.name}
                  </p>

                  {/* Remove file button */}
                  <button
                    onClick={() => {
                      setCvFile(null);
                      if (cvInputRef.current) {
                        cvInputRef.current.value = ""; // 👈 clear the native input
                      }
                    }}
                    className="ml-4 text-red-300 hover:text-red-400 text-xl font-bold transition pointer-events-auto"
                  >
                    ×
                  </button>
                </div>
              )}
            </div>

            {/* Job Description */}
            <div className="rounded-3xl bg-black/65 border border-white/15 p-10 backdrop-blur-xl min-h-[330px] shadow-[0_0_35px_rgba(0,0,0,0.8)] transition-transform transition-shadow duration-300 hover:-translate-y-2 hover:border-green-400/80 hover:shadow-[0_0_45px_rgba(0,255,140,0.35)]">
              <div className="flex items-center gap-3 mb-4">
                <FileSearch className="h-7 w-7 text-green-300" />
                <h2 className="text-white text-2xl font-bold">
                  Job Description
                </h2>
              </div>

              <p className="text-base text-white/80 mb-4">
                Paste the role description — we’ll score the match and generate
                targeted interview questions.
              </p>

              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={9}
                className="w-full text-base rounded-xl bg-black/70 border border-white/20 px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-green-400/70"
                placeholder="Paste the job description here..."
              />
            </div>

            {/* Company Details */}
            <div className="rounded-3xl bg-black/65 border border-white/15 p-10 backdrop-blur-xl min-h-[330px] shadow-[0_0_35px_rgba(0,0,0,0.8)] transition-transform transition-shadow duration-300 hover:-translate-y-2 hover:border-green-400/80 hover:shadow-[0_0_45px_rgba(0,255,140,0.35)]">
              <div className="flex items-center gap-3 mb-4">
                <Building2 className="h-7 w-7 text-green-300" />
                <h2 className="text-white text-2xl font-bold">
                  Company Details or Website
                </h2>
              </div>

              <p className="text-base text-white/80 mb-4">
                Paste the company website OR add details about the team, stack,
                culture and values.
              </p>

              <textarea
                value={companyDetails}
                onChange={(e) => setCompanyDetails(e.target.value)}
                rows={9}
                className="w-full text-base rounded-xl bg-black/70 border border-white/20 px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-green-400/70"
                placeholder="Paste company website or details..."
              />
            </div>
          </div>

          {/* Button */}
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={isLoading}
            className="mt-2 bg-white text-black hover:bg-gray-200 font-semibold px-12 py-6 text-xl rounded-full shadow-2xl pointer-events-auto disabled:opacity-60 flex items-center gap-3"
          >
            {isLoading && <Loader2 className="h-6 w-6 animate-spin" />}
            {isLoading ? "Analyzing..." : "Analyze & Continue"}
          </Button>
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
