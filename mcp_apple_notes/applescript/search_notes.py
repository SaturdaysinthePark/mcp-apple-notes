from .base_operations import BaseAppleScriptOperations
from .note_id_utils import NoteIDUtils


class SearchNotesOperations(BaseAppleScriptOperations):
    """Operations for searching notes in Apple Notes."""

    @staticmethod
    async def search_notes(keywords: list[str]) -> list[dict[str, str]]:
        """Search for notes where any keyword appears in the title OR body.

        Uses a safe ||| delimiter in AppleScript output to avoid the
        comma-splitting bug that broke results for notes/folders containing
        commas.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of dictionaries with note_id, name, folder, and matched_keyword
        """
        if not keywords:
            return []

        # Escape each keyword for AppleScript string literals
        escaped_keywords = [
            kw.replace("\\", "\\\\").replace('"', '\\"') for kw in keywords
        ]
        keywords_str = ", ".join([f'"{kw}"' for kw in escaped_keywords])

        # Build the AppleScript command.
        # Each matching note is emitted as a single line:
        #   noteName|||noteID|||noteFolder|||matchedKeyword
        # Lines are joined with the ASCII record separator (return) so the
        # result is unambiguous regardless of commas in note/folder names.
        script = f"""
        tell application "Notes"
            try
                set primaryAccount to account "iCloud"
                set keywords to {{{keywords_str}}}
                set outputLines to {{}}

                repeat with currentNote in every note of primaryAccount
                    set noteName to name of currentNote as string
                    set noteID to id of currentNote as string
                    set noteBody to body of currentNote as string

                    -- Get the folder name for this note
                    set noteFolder to "Notes"
                    try
                        set noteFolder to name of container of currentNote as string
                    on error
                        set noteFolder to "Notes"
                    end try

                    -- Check if any keyword matches title OR body
                    set foundKeyword to ""
                    repeat with kw in keywords
                        set kwStr to kw as string
                        if noteName contains kwStr or noteBody contains kwStr then
                            set foundKeyword to kwStr
                            exit repeat
                        end if
                    end repeat

                    -- If keyword found, emit a delimited line
                    if foundKeyword is not "" then
                        set outputLines to outputLines & {{noteName & "|||" & noteID & "|||" & noteFolder & "|||" & foundKeyword}}
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

        result = await SearchNotesOperations.execute_applescript(script)

        if result.startswith("error:"):
            raise RuntimeError(f"Failed to search notes: {result[6:]}")

        return SearchNotesOperations._parse_search_results(result)

    @staticmethod
    def _parse_search_results(result: str) -> list[dict[str, str]]:
        """Parse AppleScript result into list of search result dictionaries.

        Each line of the result is in the format:
            noteName|||noteID|||noteFolder|||matchedKeyword

        Args:
            result: Raw AppleScript result (newline-separated lines)

        Returns:
            List of dictionaries with note_id, name, folder, and matched_keyword
        """
        notes: list[dict[str, str]] = []

        if not result or not result.strip():
            return notes

        for line in result.strip().split("\r"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("|||")
            if len(parts) < 4:
                continue
            note_name, full_note_id, folder_name, matched_keyword = (
                parts[0],
                parts[1],
                parts[2],
                parts[3],
            )
            short_id = NoteIDUtils.extract_primary_key(full_note_id)
            if short_id and note_name:
                notes.append(
                    {
                        "note_id": short_id,
                        "name": note_name,
                        "folder": folder_name,
                        "matched_keyword": matched_keyword,
                    }
                )

        return notes
