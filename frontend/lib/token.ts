const TOKEN_SERVER = process.env.NEXT_PUBLIC_TOKEN_SERVER || "http://localhost:8001";

export async function fetchToken(room: string = "voice-room", identity: string = "user"): Promise<string> {
  const url = `${TOKEN_SERVER}/token?room=${encodeURIComponent(room)}&identity=${encodeURIComponent(identity)}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("Failed to fetch token");
  const data = await resp.json();
  return data.token;
}
