@echo off
set HTTP_PROXY=http://127.0.0.1:1111
set HTTPS_PROXY=http://127.0.0.1:1111

set NO_PROXY=localhost,127.0.0.1

echo Starting Codex CLI with proxy settings...
echo  HTTP_PROXY=%HTTP_PROXY%
echo  HTTPS_PROXY=%HTTPS_PROXY%
echo  NO_PROXY=%NO_PROXY%

codex %*