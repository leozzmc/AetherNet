"use client";

import { useState, useEffect } from "react";

export function useStoryPlayer(steps: any[], isPresentation: boolean) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loop, setLoop] = useState(true);

  // Kiosk Mode: Auto start
  useEffect(() => {
    if (isPresentation) {
      setPlaying(true);
    }
  }, [isPresentation]);

  useEffect(() => {
    setIndex(0);
    if (!isPresentation) setPlaying(false);
  }, [steps, isPresentation]);

  useEffect(() => {
    if (!playing) return;
    if (!steps || steps.length === 0) return;

    if (index >= steps.length - 1) {
      if (loop) {
        const timer = setTimeout(() => setIndex(0), 2000); // Wait longer at the end before looping
        return () => clearTimeout(timer);
      } else {
        setPlaying(false);
        return;
      }
    }

    const timer = setTimeout(() => {
      setIndex((i) => i + 1);
    }, 1500); // Cinematic timing

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
      setPlaying(isPresentation);
    },
  };
}