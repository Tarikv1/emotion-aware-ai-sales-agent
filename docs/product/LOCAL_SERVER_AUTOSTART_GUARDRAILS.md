# Local Server Auto-Start Guardrails

## Purpose

Codex may auto-start local prototype servers when it is necessary for testing or demonstration, but only through bounded guardrails.

The goal is to avoid foreground server commands that can hang the session.

## Rule

Do not run long-lived local servers directly from Codex with a normal foreground command.

Use:

```powershell
python scripts\start_guarded_local_server.py `
  --name VOICE-004 `
  --host 127.0.0.1 `
  --port 8765 `
  --startup-timeout 8 `
  --pid-out research\experiments\generated\VOICE-004-server.pid `
  --stdout-log research\experiments\generated\VOICE-004-server.stdout.log `
  --stderr-log research\experiments\generated\VOICE-004-server.stderr.log `
  -- python scripts\run_browser_speech_demo.py
```

## Required Guardrails

- Start the server as a child process with `shell=False`.
- Return control to Codex after startup verification.
- Check the expected TCP port with a short startup timeout.
- Write a PID file.
- Write stdout and stderr logs.
- Kill the child process if the port does not open before timeout.
- Do not rely on the shell command timeout as the only protection.
- Do not start or restart servers unless they are needed for the task.

## Current VOICE-004 Command

VOICE-004 can be started with:

```powershell
python scripts\start_guarded_local_server.py `
  --name VOICE-004 `
  --host 127.0.0.1 `
  --port 8765 `
  --startup-timeout 8 `
  --pid-out research\experiments\generated\VOICE-004-server.pid `
  --stdout-log research\experiments\generated\VOICE-004-server.stdout.log `
  --stderr-log research\experiments\generated\VOICE-004-server.stderr.log `
  -- python scripts\run_browser_speech_demo.py
```

Expected output is JSON with:

- `status: started`
- `pid`
- `url`
- `stdout_log`
- `stderr_log`
- `shell_used: false`

## Validation

Run:

```powershell
python scripts\validate_guarded_local_server_launcher.py
```

The validator starts a temporary local HTTP server, verifies the launcher returns while the server remains alive, then stops the test process. It also checks the failure path where the child process never opens the expected port.
