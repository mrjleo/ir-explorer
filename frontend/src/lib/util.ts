/**
 * Convert an integer to a human-readable string.
 *
 * Numbers below 1000 and are returned directly.
 * Numbers above 10^12 are returned as "> 1T".
 * Other numbers are rounded and returned with an appropriate suffix.
 *
 * @param n - The number to convert.
 * @returns A human-readable version of the input number.
 */
export function toHumanReadable(n: number): string {
  if (n < 1000) return n.toString();
  if (n > 1000000000000) return "> 1T";

  const suffixes = ["", "k", "M", "B"];
  const i = Math.floor(Math.log(n) / Math.log(1000));
  return Math.round(n / Math.pow(1000, i)) + suffixes[i];
}

/**
 * Truncate a piece of text if it exceeds a maximum length.
 *
 * If the text is truncated, 3 dots are appended.
 *
 * @param text - The text to truncate.
 * @param maxLen - The length up to which no truncation happens.
 * @returns The (truncated) text.
 */
export function truncate(text: string, maxLen: number): string {
  if (text.length > maxLen) return text.substring(0, maxLen - 3) + "...";
  return text;
}
