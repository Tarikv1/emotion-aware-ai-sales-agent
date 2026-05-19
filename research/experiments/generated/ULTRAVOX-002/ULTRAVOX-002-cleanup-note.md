# ULTRAVOX-002 Cleanup Note

The first approved synthetic live smoke created one UltraVox call and the runner attempted deletion immediately after closing the WebSocket.

Initial delete result in the live smoke artifact:

```text
status: 425
deleted: false
message: Cannot delete an ongoing (or unbilled) call. Wait until the call has ended.
```

Follow-up cleanup:

```text
python scripts\cleanup_ultravox_call_by_suffix.py --suffix f69f9413 --retries 6 --sleep-seconds 4
```

Result:

```text
matched_recent_call: true
delete_attempt: 1 status: 204 deleted: true
```

No API key, full call ID, join URL, or customer audio is recorded in this note.
