"use client";

import { useState, useEffect } from "react";

export function useStoryPlayer(steps: any[]) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loop, setLoop] = useState(true);

  // 當 Scenario 切換時，重置播放器
  useEffect(() => {
    setIndex(0);
    setPlaying(false);
  }, [steps]);

  useEffect(() => {
    if (!playing) return;
    if (!steps || steps.length === 0) return;

    if (index >= steps.length - 1) {
      if (loop) {
        const timer = setTimeout(() => setIndex(0), 1500);
        return () => clearTimeout(timer);
      } else {
        setPlaying(false);
        return;
      }
    }

    const timer = setTimeout(() => {
      setIndex((i) => i + 1);
    }, 1200); // Cinematic transition timing

    return () => clearTimeout(timer);
  }, [playing, index, steps, loop]);

  return {
    step: steps ? steps[index] : null,
    index,
    total: steps ? steps.length : 0,
    playing,
    setPlaying,
    loop,
    setLoop,
    next: () => {
      if (steps && index < steps.length - 1) setIndex(index + 1);
    },
    reset: () => {
      setIndex(0);
      setPlaying(false);
    },
  };
}