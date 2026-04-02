import { expect, type Page, type Request } from "@playwright/test";

interface MockRequest {
  method: string;
  pathname: string;
  pathWithSearch: string;
  searchParams: URLSearchParams;
  body: unknown;
  rawBody: string | null;
}

interface MockResponse {
  status?: number;
  body: unknown;
  headers?: Record<string, string>;
}

type RequestMatcher = string | RegExp | ((request: MockRequest) => boolean);

interface Handler {
  method: string;
  matcher: RequestMatcher;
  responder: (request: MockRequest) => MockResponse | Promise<MockResponse>;
}

function matchesRequest(matcher: RequestMatcher, request: MockRequest): boolean {
  if (typeof matcher === "string") {
    if (matcher.includes("?")) {
      return request.pathWithSearch === matcher;
    }
    return request.pathname === matcher;
  }
  if (matcher instanceof RegExp) {
    return matcher.test(request.pathWithSearch);
  }
  return matcher(request);
}

async function toMockRequest(request: Request): Promise<MockRequest> {
  const url = new URL(request.url());
  const rawBody = request.postData();
  let body: unknown = null;
  if (rawBody) {
    try {
      body = JSON.parse(rawBody) as unknown;
    } catch {
      body = rawBody;
    }
  }
  return {
    method: request.method().toUpperCase(),
    pathname: url.pathname.replace(/^\/api\/v1/, ""),
    pathWithSearch: `${url.pathname.replace(/^\/api\/v1/, "")}${url.search}`,
    searchParams: url.searchParams,
    body,
    rawBody
  };
}

function jsonResponse(
  body: unknown,
  status = 200,
  headers?: Record<string, string>
): MockResponse {
  return { status, body, headers };
}

export class ApiMock {
  private readonly handlers: Handler[] = [];
  private readonly calls: string[] = [];
  private readonly unexpected: string[] = [];

  constructor(private readonly page: Page) {}

  async install(): Promise<void> {
    await this.page.route("**/api/v1/**", async (route) => {
      const request = await toMockRequest(route.request());
      const label = `${request.method} ${request.pathWithSearch}`;
      this.calls.push(label);

      const handler = this.handlers.find(
        (candidate) =>
          candidate.method === request.method &&
          matchesRequest(candidate.matcher, request)
      );

      if (!handler) {
        const message = `Unhandled API request: ${label}`;
        this.unexpected.push(message);
        await route.fulfill({
          status: 599,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "unexpected_smoke_request",
              message
            }
          })
        });
        return;
      }

      const response = await handler.responder(request);
      await route.fulfill({
        status: response.status ?? 200,
        headers: response.headers,
        contentType: "application/json",
        body: JSON.stringify(response.body)
      });
    });
  }

  onJson(method: string, matcher: RequestMatcher, body: unknown, status = 200): void {
    this.handlers.push({
      method: method.toUpperCase(),
      matcher,
      responder: async () => jsonResponse(body, status)
    });
  }

  onError(
    method: string,
    matcher: RequestMatcher,
    status: number,
    code: string,
    message: string,
    details?: Record<string, unknown>
  ): void {
    this.handlers.push({
      method: method.toUpperCase(),
      matcher,
      responder: async () =>
        jsonResponse(
          {
            error: {
              code,
              message,
              ...(details ? { details } : {})
            }
          },
          status
        )
    });
  }

  on(
    method: string,
    matcher: RequestMatcher,
    responder: (request: MockRequest) => MockResponse | Promise<MockResponse>
  ): void {
    this.handlers.push({
      method: method.toUpperCase(),
      matcher,
      responder
    });
  }

  assertCalled(matcher: string | RegExp): void {
    const matched =
      typeof matcher === "string"
        ? this.calls.some((call) => call === matcher)
        : this.calls.some((call) => matcher.test(call));
    expect(matched, `Expected API call matching ${String(matcher)}.`).toBe(true);
  }

  assertNoUnexpectedRequests(): void {
    expect(
      this.unexpected,
      this.unexpected.length > 0 ? this.unexpected.join("\n") : undefined
    ).toEqual([]);
  }
}
