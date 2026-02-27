from .base_operations import BaseAppleScriptOperations
from .note_id_utils import NoteIDUtils


class FindNotesByTitleOperations(BaseAppleScriptOperations):
    """Operations for finding Apple Notes by title/name."""

    @staticmethod
    async def find_notes_by_title(
        title: str, exact: bool = False
    ) -> list[dict[str, str]]:
        """Find notes whose title contains (or exactly matches) the given string.

        Args:
            title: The title text to search for
            exact: If True, requires an exact case-sensitive match.
                   If False (default), performs a case-insensitive contains search.

        Returns:
            List of dictionaries with note_id, name, folder, creation_date,
            modification_date

        Raises:
            RuntimeError: If AppleScript execution fails
        """
        if not title or not title.strip():
            raise ValueError("Title search string cannot be empty")

        title = title.strip()
        # Escape double quotes for AppleScript string literal
        escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')

        if exact:
            match_condition = f'noteName is equal to "{escaped_title}"'
        else:
            # AppleScript `contains` is case-insensitive by default
            match_condition = f'noteName contains "{escaped_title}"'

        script = f"""
        tell application "Notes"
            try
                set primaryAccount to account "iCloud"
                set outputLines to {{}}

                repeat with currentNote in every note of primaryAccount
                    set noteName to name of currentNote as string
                    if {match_condition} then
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

        result = await FindNotesByTitleOperations.execute_applescript(script)

        if result.startswith("error:"):
            raise RuntimeError(f"Failed to find notes by title: {result[6:]}")

        return FindNotesByTitleOperations._parse_results(result)

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
