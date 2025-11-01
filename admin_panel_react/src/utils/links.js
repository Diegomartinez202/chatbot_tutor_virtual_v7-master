// utils/links.js
export const urlRegex = /\bhttps?:\/\/[^\s)]+/gi;

export function extractLinks(text = "") {
    return (text.match(urlRegex) || []);
}
