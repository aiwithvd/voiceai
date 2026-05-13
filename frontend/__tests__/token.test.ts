import { describe, it, expect, vi, beforeEach } from "vitest";

describe("fetchToken", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("returns token on success", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ token: "test-jwt-token" }),
    } as Response);

    const { fetchToken } = await import("../lib/token");
    const token = await fetchToken("test-room", "test-user");
    expect(token).toBe("test-jwt-token");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8001/token?room=test-room&identity=test-user"
    );
  });

  it("throws on HTTP error", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
    } as Response);

    const { fetchToken } = await import("../lib/token");
    await expect(fetchToken("room", "user")).rejects.toThrow("Failed to fetch token");
  });
});
