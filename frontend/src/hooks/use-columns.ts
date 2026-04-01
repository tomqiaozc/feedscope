"use client";

import { useSyncExternalStore } from "react";

const BREAKPOINTS = ["(min-width: 768px)", "(min-width: 1024px)", "(min-width: 1280px)"];

function getSnapshot(): number {
  if (window.matchMedia(BREAKPOINTS[2]).matches) return 4;
  if (window.matchMedia(BREAKPOINTS[1]).matches) return 3;
  if (window.matchMedia(BREAKPOINTS[0]).matches) return 2;
  return 1;
}

function getServerSnapshot(): number {
  return 1;
}

function subscribe(cb: () => void) {
  const mqls = BREAKPOINTS.map((bp) => window.matchMedia(bp));
  mqls.forEach((mql) => mql.addEventListener("change", cb));
  return () => mqls.forEach((mql) => mql.removeEventListener("change", cb));
}

export function useColumns(): number {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
