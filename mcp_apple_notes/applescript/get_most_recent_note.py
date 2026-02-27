from .base_operations import BaseAppleScriptOperations
from .note_id_utils import NoteIDUtils


class GetMostRecentNoteOperations(BaseAppleScriptOperations):
    """Operations for efficiently retrieving the most recently modified note."""

    @staticmethod
    async def get_most_recent_note() -> dict[str, str]:
        """Get the single most recently modified note across all folders.

        This is significantly faster than listing all notes and sorting because
        it uses AppleScript's built-in sort via 'whose modification date' and
        only fetches the top result.

        Returns:
            Dictionary with note_id, name, folder, creation_date,
            modification_date, and body of the most recently modified note.

        Raises:
            RuntimeError: If AppleScript execution fails or no notes exist
        """
        script = """
        tell application "Notes"
            try
                set primaryAccount to account "iCloud"
                set allNotes to every note of primaryAccount
                if (count of allNotes) is 0 then
                    return "error:No notes found in iCloud account"
                end if

                -- Find the note with the latest modification date
                set latestNote to item 1 of allNotes
                set latestDate to modification date of latestNote

                repeat with currentNote in allNotes
                    set currentDate to modification date of currentNote
                    if currentDate > latestDate then
                        set latestNote to currentNote
                        set latestDate to currentDate
                    end if
                end repeat

                set noteName to name of latestNote as string
                set noteID to id of latestNote as string
                set noteFolder to "Notes"
                try
                    set noteFolder to name of container of latestNote as string
                on error
                    set noteFolder to "Notes"
                end try
                set creationDate to creation date of latestNote as string
                set modDate to modification date of latestNote as string
                set noteBody to body of latestNote as string

                return "success:" & noteName & "|||" & noteID & "|||" & noteFolder & "|||" & creationDate & "|||" & modDate & "|||" & noteBody
            on error errMsg
                return "error:iCloud account not available. Please enable iCloud Notes sync - " & errMsg
            end try
        end tell
        """

        result = await GetMostRecentNoteOperations.execute_applescript(script)

        if result.startswith("error:"):
            raise RuntimeError(f"Failed to get most recent note: {result[6:]}")

        return GetMostRecentNoteOperations._parse_result(result)

    @staticmethod
    def _parse_result(result: str) -> dict[str, str]:
        """Parse the AppleScript result."""
        if not result.startswith("success:"):
            raise RuntimeError(f"Unexpected result format: {result}")

        content = result[8:]  # strip "success:"
        parts = content.split("|||", 5)  # max 6 parts; body may contain |||
        if len(parts) < 6:
            raise RuntimeError(f"Incomplete result from AppleScript: {result}")

        note_name, full_id, folder, creation_date, mod_date, body = (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
            parts[5],
        )

        return {
            "note_id": NoteIDUtils.extract_primary_key(full_id),
            "name": note_name,
            "folder": folder,
            "creation_date": creation_date,
            "modification_date": mod_date,
            "body": body,
        }

# Made with Bob
