export function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return null;
}

export function formatNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return "n/a";
  }
  return value.toFixed(digits);
}

export function formatPercent(value: number | null, digits = 2): string {
  if (value === null) {
    return "n/a";
  }
  return `${value.toFixed(digits)}%`;
}

export function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}
