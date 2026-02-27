
from .base_operations import BaseAppleScriptOperations
from .note_id_utils import NoteIDUtils


class ListNotesOperations(BaseAppleScriptOperations):
    """Operations for listing notes across all folders."""

    @staticmethod
    async def list_all_notes() -> list[dict[str, str]]:
        """Get a list of all notes across all folders with their IDs, names,
        folder location, creation date, and modification date.

        Returns:
            List of dictionaries with note_id, name, folder, creation_date,
            and modification_date

        Raises:
            RuntimeError: If AppleScript execution fails
        """
        script = """
        tell application "Notes"
            try
                set outputLines to {}
                set iCloudAccount to account "iCloud"
                repeat with currentFolder in folders of iCloudAccount
                    set folderName to name of currentFolder
                    repeat with currentNote in notes of currentFolder
                        set noteName to name of currentNote
                        set noteID to id of currentNote as string
                        set creationDate to creation date of currentNote as string
                        set modDate to modification date of currentNote as string
                        set outputLines to outputLines & {noteName & "|||" & noteID & "|||" & folderName & "|||" & creationDate & "|||" & modDate}
                    end repeat
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

        result = await ListNotesOperations.execute_applescript(script)

        if result.startswith("error:"):
            raise RuntimeError(f"Failed to list all notes: {result[6:]}")

        return ListNotesOperations._parse_notes_list(result)

    @staticmethod
    def _parse_notes_list(result: str) -> list[dict[str, str]]:
        """Parse the AppleScript result into a list of note dictionaries.

        Args:
            result: Raw AppleScript result string, one note per line in format:
                    "name|||full_id|||folder|||creation_date|||modification_date"

        Returns:
            List of dictionaries with note_id, name, folder, creation_date,
            modification_date
        """
        if not result.strip():
            return []

        notes: list[dict[str, str]] = []
        for line in result.strip().split("\r"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("|||")
            if len(parts) < 5:
                continue
            note_name, full_note_id, folder, creation_date, mod_date = (
                parts[0],
                parts[1],
                parts[2],
                parts[3],
                parts[4],
            )
            notes.append(
                {
                    "note_id": NoteIDUtils.extract_primary_key(full_note_id),
                    "name": note_name,
                    "folder": folder,
                    "creation_date": creation_date,
                    "modification_date": mod_date,
                }
            )

        return notes
