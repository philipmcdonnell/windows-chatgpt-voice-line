# Contributing

Issues and pull requests are welcome for reproducible Windows defects, documentation improvements, accessibility, privacy, and latency improvements.

Please do not commit model files, local configuration, authentication data, recordings, logs, or personal memory-vault content. Run these checks before submitting:

```powershell
.\verify-package.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Adaptations must retain the attribution and CC BY-NC-SA 4.0 license.
