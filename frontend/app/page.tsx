"use client";

import { useEffect, useState, useMemo } from "react";
import { TokenSource } from "livekit-client";
import { useSession, useAgent, useSessionContext, useSessionMessages } from "@livekit/components-react";
import { AgentSessionProvider } from "@/components/agents-ui/agent-session-provider";
import { AgentControlBar } from "@/components/agents-ui/agent-control-bar";
import { AgentChatTranscript } from "@/components/agents-ui/agent-chat-transcript";
import { AgentAudioVisualizerBar } from "@/components/agents-ui/agent-audio-visualizer-bar";
import { StartAudioButton } from "@/components/agents-ui/start-audio-button";
import { fetchToken } from "@/lib/token";

function AgentUI() {
  const session = useSessionContext();
  const agent = useAgent(session);
  const messages = useSessionMessages(session);

  return (
    <div className="flex flex-col items-center gap-6 p-8 min-h-screen bg-black text-white">
      <h1 className="text-2xl font-semibold">Voice AI Demo</h1>

      <div className="w-full max-w-md">
        {agent.audioTrack ? (
          <AgentAudioVisualizerBar
            audioTrack={agent.audioTrack}
            state={agent.state}
            barCount={5}
          />
        ) : (
          <div className="h-20 flex items-center justify-center text-gray-400">
            {agent.state === "connecting" ? "Connecting..." : "Press mic to start"}
          </div>
        )}
      </div>

      <AgentChatTranscript messages={messages} agentState={agent.state} />

      <AgentControlBar
        variant="livekit"
        isConnected={session.isConnected}
        controls={{ microphone: true, camera: false, screenShare: false }}
      />

      <StartAudioButton label="Start audio" />
    </div>
  );
}

function VoiceChat({ token }: { token: string }) {
  const tokenSource = useMemo(() => TokenSource.fromToken(token), [token]);
  const session = useSession(tokenSource);

  useEffect(() => {
    session.start();
    return () => { session.end(); };
  }, [session]);

  return (
    <AgentSessionProvider session={session}>
      <AgentUI />
    </AgentSessionProvider>
  );
}

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchToken()
      .then(setToken)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white gap-4">
        <p className="text-red-400">Failed to connect: {error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-white text-black rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black text-white">
        Connecting to agent...
      </div>
    );
  }

  return <VoiceChat token={token} />;
}
