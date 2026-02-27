from datetime import datetime

from .base_operations import BaseAppleScriptOperations
from .note_id_utils import NoteIDUtils

# AppleScript's epoch anchor as a naive local-time datetime.
# "January 1, 2001 00:00:00" in local time matches how AppleScript
# stores and compares dates internally on macOS.
_AS_EPOCH_LOCAL = datetime(2001, 1, 1, 0, 0, 0)


def _to_as_seconds(dt: datetime) -> int:
    """Convert a naive local datetime to seconds since AppleScript's epoch.

    AppleScript's 'date "January 1, 2001"' resolves to midnight local time,
    so we compute the delta in local time — no timezone conversion needed.
    The result is a plain integer we embed directly in the script.
    """
    # Strip any tzinfo so arithmetic stays in local time
    naive = dt.replace(tzinfo=None)
    return int((naive - _AS_EPOCH_LOCAL).total_seconds())


class FindNotesByDateOperations(BaseAppleScriptOperations):
    """Operations for finding Apple Notes by creation or modification date."""

    @staticmethod
    async def find_notes_by_date(
        date_type: str = "modified",
        after: str = "",
        before: str = "",
    ) -> list[dict[str, str]]:
        """Find notes filtered by creation or modification date.

        Uses AppleScript's native 'whose' clause with epoch-based date arithmetic
        to push date filtering into the Notes app query engine — much faster than
        iterating all notes in a loop, especially with large libraries.

        Date literals like date "2026-02-27" are locale-dependent and silently
        fail on many macOS systems. Instead we compute seconds since AppleScript's
        epoch (2001-01-01 UTC) and use:
            (date "January 1, 2001") + N seconds
        which is locale-independent and always works.

        Args:
            date_type: Either "created" or "modified" (default: "modified")
            after:  ISO 8601 date string (e.g. "2024-01-01"). Notes on or after
                    this date are included. Leave empty for no lower bound.
            before: ISO 8601 date string (e.g. "2024-12-31"). Notes on or before
                    this date are included. Leave empty for no upper bound.

        Returns:
            List of dicts with note_id, name, folder, creation_date,
            modification_date — sorted newest first.

        Raises:
            ValueError: If date_type is invalid or date strings are malformed
            RuntimeError: If AppleScript execution fails
        """
        date_type = date_type.strip().lower()
        if date_type not in ("created", "modified"):
            raise ValueError("date_type must be 'created' or 'modified'")

        if not after and not before:
            raise ValueError("At least one of 'after' or 'before' must be provided")

        # Validate and parse date strings
        after_dt: datetime | None = None
        before_dt: datetime | None = None

        if after:
            try:
                after_dt = datetime.fromisoformat(after.strip())
            except ValueError:
                raise ValueError(
                    f"Invalid 'after' date '{after}'. Use ISO 8601 format e.g. '2024-01-15'"
                )

        if before:
            try:
                before_dt = datetime.fromisoformat(before.strip())
            except ValueError:
                raise ValueError(
                    f"Invalid 'before' date '{before}'. Use ISO 8601 format e.g. '2024-12-31'"
                )

        # Build AppleScript date property reference
        if date_type == "created":
            date_property = "creation date"
        else:
            date_property = "modification date"

        # Build locale-independent AppleScript date objects using epoch arithmetic.
        # "January 1, 2001" is AppleScript's fixed epoch anchor — always parseable
        # regardless of system locale. We add the offset in seconds.
        as_epoch_anchor = 'date "January 1, 2001"'
        whose_parts = []
        if after_dt:
            # Start of the given day (00:00:00 local)
            after_start = after_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            after_secs = _to_as_seconds(after_start)
            whose_parts.append(
                f'{date_property} >= ({as_epoch_anchor} + {after_secs})'
            )
        if before_dt:
            # End of the given day (23:59:59 local)
            before_end = before_dt.replace(hour=23, minute=59, second=59, microsecond=0)
            before_secs = _to_as_seconds(before_end)
            whose_parts.append(
                f'{date_property} <= ({as_epoch_anchor} + {before_secs})'
            )

        whose_clause = " and ".join(whose_parts)

        script = f"""
        tell application "Notes"
            try
                set primaryAccount to account "iCloud"
                -- Use 'whose' with epoch-based dates (locale-independent)
                set matchingNotes to (every note of primaryAccount whose {whose_clause})
                set outputLines to {{}}

                repeat with currentNote in matchingNotes
                    set noteName to name of currentNote as string
                    set noteID to id of currentNote as string
                    set noteFolder to "Notes"
                    try
                        set noteFolder to name of container of currentNote as string
                    on error
                        set noteFolder to "Notes"
                    end try
                    set creationDate to creation date of currentNote as string
                    set modDate to modification date of currentNote as string
                    set outputLines to outputLines & {{noteName & "|||" & noteID & "|||" & noteFolder & "|||" & creationDate & "|||" & modDate}}
                end repeat

                set AppleScript's text item delimiters to return
                set outputText to outputLines as string
                set AppleScript's text item delimiters to ""
                return outputText
            on error errMsg
                return "error:iCloud account not available. Please enable iCloud Notes sync - " & errMsg
            end try
        end tell
        """

        result = await FindNotesByDateOperations.execute_applescript(script)

        if result.startswith("error:"):
            raise RuntimeError(f"Failed to find notes by date: {result[6:]}")

        notes = FindNotesByDateOperations._parse_results(result)

        # Sort newest first by the relevant date field
        sort_key = "modification_date" if date_type == "modified" else "creation_date"
        notes.sort(key=lambda n: n.get(sort_key, ""), reverse=True)

        return notes

    @staticmethod
    def _parse_results(result: str) -> list[dict[str, str]]:
        """Parse AppleScript output into list of note dicts."""
        if not result or not result.strip():
            return []

        notes: list[dict[str, str]] = []
        # AppleScript 'return' separator can be \r or \n depending on macOS version
        for line in result.strip().replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("|||")
            if len(parts) < 5:
                continue
            note_name, full_id, folder, creation_date, mod_date = (
                parts[0],
                parts[1],
                parts[2],
                parts[3],
                parts[4],
            )
            notes.append(
                {
                    "note_id": NoteIDUtils.extract_primary_key(full_id),
                    "name": note_name,
                    "folder": folder,
                    "creation_date": creation_date,
                    "modification_date": mod_date,
                }
            )
        return notes

# Made with Bob
