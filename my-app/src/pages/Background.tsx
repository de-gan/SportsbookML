import { useState, useEffect } from "react";
import MachineLearningBackground from "@/components/Background";

export default function About() {
  const [isDark, setIsDark] = useState(
    () => document.documentElement.classList.contains("dark")
  );
    
  useEffect(() => {
    const observer = new MutationObserver(() =>
      setIsDark(document.documentElement.classList.contains("dark"))
    );
    observer.observe(document.documentElement, { attributes: true });
    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen text-neutral-900 dark:text-neutral-100">
      <MachineLearningBackground density={0.00015} speed={0.5} interactive opacity={0.2} color={isDark ? "#06b6d4" : "#ff0000ff"} nodeColor={isDark ? "#e0f2fe" : "#ff0000ff"}/>
    </div>
  );
}