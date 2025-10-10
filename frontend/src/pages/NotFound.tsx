import { Link } from "react-router-dom";

const NotFound = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-lg rounded-2xl border bg-surface p-8 text-center shadow-sm">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10">
          <span className="text-2xl font-bold text-primary">404</span>
        </div>
        <h1 className="mb-2 text-2xl font-semibold">Page not found</h1>
        <p className="mb-6 text-muted-foreground">The page you are looking for might have been removed or had its name changed.</p>
        <div className="flex items-center justify-center gap-3">
          <Link
            to="/"
            className="inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-hover"
          >
            Go back home
          </Link>
          <Link
            to="/"
            className="inline-flex items-center rounded-lg border px-4 py-2 text-sm font-medium hover:bg-surface-alt"
          >
            Contact support
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFound;