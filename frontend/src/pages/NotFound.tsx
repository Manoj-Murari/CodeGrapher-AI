import { Link } from "react-router-dom";

const NotFound = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background text-center">
      <h1 className="mb-4 text-6xl font-bold text-primary">404</h1>
      <p className="mb-8 text-xl text-muted-foreground">Oops! Page not found.</p>
      <Link to="/" className="text-primary underline hover:text-primary-hover">
        Return to Home
      </Link>
    </div>
  );
};

export default NotFound;