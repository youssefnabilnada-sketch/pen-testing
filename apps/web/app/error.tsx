'use client';
export default function ErrorBoundary({reset}:{reset:()=>void}){return <main className="auth"><section className="glass panel"><h2>This view could not load.</h2><p>Your assessment state is stored on the server. Retry the view or check service availability.</p><button onClick={reset}>Try again</button></section></main>}
