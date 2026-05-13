class FakeSTT:
    def __init__(self):
        self.capabilities = {"streaming": False}

    async def recognize(self, audio):
        return "this is a test transcription"

    def stream(self):
        return self


class FakeLLM:
    async def chat(self, chat_ctx):
        return "This is a test LLM response."

    def chat_stream(self, chat_ctx):
        class FakeStream:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration
        return FakeStream()


class FakeTTS:
    async def synthesize(self, text: str):
        import struct as s
        duration_ms = 1000
        sample_rate = 24000
        num_samples = int(sample_rate * duration_ms / 1000)
        audio_data = s.pack(f"<{num_samples}h", *([0] * num_samples))
        return audio_data
