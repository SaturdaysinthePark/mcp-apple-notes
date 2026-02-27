import asyncio


# Default timeout for AppleScript calls (seconds).
# Large note libraries can cause Notes.app to respond slowly.
APPLESCRIPT_TIMEOUT = 60


class BaseAppleScriptOperations:
    """Base class with common AppleScript execution functionality."""

    @staticmethod
    async def execute_applescript(script: str, timeout: float = APPLESCRIPT_TIMEOUT) -> str:
        """Execute AppleScript and return result.

        Args:
            script: The AppleScript to execute
            timeout: Maximum seconds to wait before raising TimeoutError (default 60s)

        Raises:
            TimeoutError: If the script takes longer than `timeout` seconds
            RuntimeError: If AppleScript returns a non-zero exit code
        """
        process = await asyncio.create_subprocess_exec(
            "osascript",
            "-e",
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            raise TimeoutError(
                f"AppleScript timed out after {timeout}s. "
                "Apple Notes may be slow due to a large number of notes. "
                "Try a more specific query (e.g. search_notes or find_notes_by_title) "
                "instead of listing all notes."
            )

        if process.returncode != 0:
            raise RuntimeError(f"AppleScript error: {stderr.decode()}")

        return stdout.decode().strip()
