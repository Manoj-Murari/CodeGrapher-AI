// Minimal ambient module declarations for prismjs components
// This prevents TypeScript errors when importing specific prism components
declare module 'prismjs/components/prism-core' {
  // Export a minimal API used by react-simple-code-editor highlighting
  export function highlight(code: string, grammar: any, language?: string): string;
  export const languages: { [key: string]: any };
  const Prism: { highlight: typeof highlight; languages: typeof languages };
  export default Prism;
}

declare module 'prismjs/components/prism-clike';
declare module 'prismjs/components/prism-javascript';
declare module 'prismjs/components/prism-python';

// Themes are CSS modules / plain CSS — allow importing them
declare module 'prismjs/themes/*.css';
