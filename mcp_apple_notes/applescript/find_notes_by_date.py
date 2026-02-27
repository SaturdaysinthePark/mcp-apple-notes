from datetime import datetime

from .base_operations import BaseAppleScriptOperations
from .note_id_utils import NoteIDUtils


class FindNotesByDateOperations(BaseAppleScriptOperations):
    """Operations for finding Apple Notes by creation or modification date."""

    @staticmethod
    async def find_notes_by_date(
        date_type: str = "modified",
        after: str = "",
        before: str = "",
    ) -> list[dict[str, str]]:
        """Find notes filtered by creation or modification date.

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

        # Build AppleScript date filter conditions using string comparison on
        # the ISO-formatted date portion (first 10 chars of the date string).
        # AppleScript date arithmetic is fragile across locales, so we compare
        # the date string prefix which is locale-independent when cast via
        # "as string" in the format "YYYY-MM-DD ..." on macOS.
        # We use a helper that extracts YYYY-MM-DD from the AppleScript date string.
        conditions = []
        if after_dt:
            after_str = after_dt.strftime("%Y-%m-%d")
            conditions.append(
                f'text 1 thru 10 of (noteDate as string) >= "{after_str}"'
            )
        if before_dt:
            before_str = before_dt.strftime("%Y-%m-%d")
            conditions.append(
                f'text 1 thru 10 of (noteDate as string) <= "{before_str}"'
            )

        filter_condition = " and ".join(conditions)

        script = f"""
        tell application "Notes"
            try
                set primaryAccount to account "iCloud"
                set outputLines to {{}}

                repeat with currentNote in every note of primaryAccount
                    set noteDate to {date_property} of currentNote
                    -- noteDate as string on macOS is "YYYY-MM-DD HH:MM:SS +ZZZZ"
                    set noteDateStr to noteDate as string
                    if {filter_condition} then
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
                    end if
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
        for line in result.strip().split("\r"):
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
