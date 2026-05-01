"use client";

import { useState, useEffect } from "react";

export function useStoryPlayer(steps: any[]) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  // When scenario changes, steps change. Reset the player.
  useEffect(() => {
    setIndex(0);
    setPlaying(false);
  }, [steps]);

  useEffect(() => {
    if (!playing) return;
    if (!steps || steps.length === 0) return;

    if (index >= steps.length - 1) {
      setPlaying(false);
      return;
    }

    const timer = setTimeout(() => {
      setIndex((i) => i + 1);
    }, 1500); // 1.5s per frame for cinematic timing

    return () => clearTimeout(timer);
  }, [playing, index, steps]);

  return {
    step: steps ? steps[index] : null,
    index,
    total: steps ? steps.length : 0,
    playing,
    setPlaying,
    next: () => {
      if (steps && index < steps.length - 1) setIndex(index + 1);
    },
    reset: () => {
      setIndex(0);
      setPlaying(false);
    },
  };
}