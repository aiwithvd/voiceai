import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/token", () => ({
  fetchToken: vi.fn().mockRejectedValue(new Error("no server")),
}));

vi.mock("@/components/agents-ui/agent-session-provider", () => ({
  AgentSessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/agents-ui/agent-control-bar", () => ({
  AgentControlBar: () => <div data-testid="control-bar" />,
}));

vi.mock("@/components/agents-ui/agent-chat-transcript", () => ({
  AgentChatTranscript: () => <div data-testid="chat-transcript" />,
}));

vi.mock("@/components/agents-ui/agent-audio-visualizer-bar", () => ({
  AgentAudioVisualizerBar: () => <div data-testid="visualizer" />,
}));

vi.mock("@/components/agents-ui/start-audio-button", () => ({
  StartAudioButton: () => <div data-testid="start-audio" />,
}));

vi.mock("@livekit/components-react", () => ({
  useSession: vi.fn(),
  useAgent: vi.fn(),
  useSessionContext: vi.fn(),
  useSessionMessages: vi.fn(),
}));

import Home from "@/app/page";

describe("Home page", () => {
  it("shows connecting state initially", () => {
    render(<Home />);
    expect(screen.getByText(/Connecting to agent/)).toBeTruthy();
  });

  it("shows error state when token fetch fails", async () => {
    render(<Home />);
    const errorMsg = await screen.findByText(/Failed to connect/);
    expect(errorMsg).toBeTruthy();
  });
});
