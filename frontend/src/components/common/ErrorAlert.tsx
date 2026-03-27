import { ApiClientError } from "../../lib/api/client";

interface ErrorAlertProps {
  error: unknown;
}

export function ErrorAlert({ error }: ErrorAlertProps) {
  let title = "Request Failed";
  let message = "Unexpected error";
  let details: string | null = null;

  if (error instanceof ApiClientError) {
    title = error.code ? `API Error: ${error.code}` : "API Error";
    message = error.message;
    if (error.status > 0) {
      details = `HTTP status: ${error.status}`;
    }
    if (error.details) {
      try {
        details = `${details ?? ""}${details ? " | " : ""}${JSON.stringify(error.details)}`;
      } catch {
        // Ignore non-serializable details and keep the base message.
      }
    }
  } else if (error instanceof Error) {
    message = error.message;
  }

  return (
    <section className="error-alert" role="alert">
      <h3>{title}</h3>
      <p>{message}</p>
      {details ? <p>{details}</p> : null}
    </section>
  );
}
