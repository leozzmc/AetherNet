"use client"

import { useEffect, useState } from "react"

export function usePresentation() {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch("/presentation.json")
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to fetch presentation.json: ${res.statusText}`);
        }
        return res.json();
      })
      .then(setData)
      .catch(err => setError(err.message));
  }, [])

  return { data, error }
}