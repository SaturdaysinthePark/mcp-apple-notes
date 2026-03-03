from .base_operations import BaseAppleScriptOperations
from .note_id_utils import NoteIDUtils


class SearchNotesOperations(BaseAppleScriptOperations):
    """Operations for searching notes in Apple Notes."""

    @staticmethod
    async def search_notes(
        keywords: list[str], max_results: int = 50
    ) -> list[dict[str, str]]:
        """Search for notes where any keyword appears in the title OR body.

        Uses a two-phase strategy for performance:
        1. Fast title search using native 'whose' filtering
        2. Selective body search with result limiting

        Uses a safe ||| delimiter in AppleScript output to avoid the
        comma-splitting bug that broke results for notes/folders containing
        commas.

        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of results to return (default 50)

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

        # Build the AppleScript command with two-phase search strategy
        # Phase 1: Fast title search using native filtering
        # Phase 2: Selective body search (only if needed and time permits)
        script = f"""
        tell application "Notes"
            try
                set primaryAccount to account "iCloud"
                set keywords to {{{keywords_str}}}
                set maxResults to {max_results}
                set outputLines to {{}}
                set resultCount to 0
                
                -- PHASE 1: Fast title search using native filtering
                -- This is FAST because AppleScript filters server-side
                set titleMatchedNotes to {{}}
                repeat with kw in keywords
                    set kwStr to kw as string
                    try
                        set matches to (every note of primaryAccount whose name contains kwStr)
                        repeat with matchedNote in matches
                            -- Check if we already have this note (deduplication)
                            set noteID to id of matchedNote as string
                            set alreadyAdded to false
                            repeat with existingNote in titleMatchedNotes
                                if id of existingNote as string is noteID then
                                    set alreadyAdded to true
                                    exit repeat
                                end if
                            end repeat
                            
                            if not alreadyAdded then
                                set end of titleMatchedNotes to matchedNote
                            end if
                        end repeat
                    on error
                        -- Continue if filtering fails for this keyword
                    end try
                end repeat
                
                -- Add title matches to output
                repeat with matchedNote in titleMatchedNotes
                    if resultCount >= maxResults then
                        exit repeat
                    end if
                    
                    set noteName to name of matchedNote as string
                    set noteID to id of matchedNote as string
                    
                    -- Get the folder name
                    set noteFolder to "Notes"
                    try
                        set noteFolder to name of container of matchedNote as string
                    on error
                        set noteFolder to "Notes"
                    end try
                    
                    -- Find which keyword matched
                    set matchedKeyword to ""
                    repeat with kw in keywords
                        set kwStr to kw as string
                        if noteName contains kwStr then
                            set matchedKeyword to kwStr
                            exit repeat
                        end if
                    end repeat
                    
                    set outputLines to outputLines & {{noteName & "|||" & noteID & "|||" & noteFolder & "|||" & matchedKeyword}}
                    set resultCount to resultCount + 1
                end repeat
                
                -- PHASE 2: Body search (only if we haven't hit max_results)
                -- Only search bodies of notes NOT already matched by title
                if resultCount < maxResults then
                    set remainingSlots to maxResults - resultCount
                    set allNotes to every note of primaryAccount
                    set bodySearchCount to 0
                    
                    repeat with currentNote in allNotes
                        if bodySearchCount >= remainingSlots then
                            exit repeat
                        end if
                        
                        -- Skip if already in title matches
                        set noteID to id of currentNote as string
                        set alreadyMatched to false
                        repeat with titleNote in titleMatchedNotes
                            if id of titleNote as string is noteID then
                                set alreadyMatched to true
                                exit repeat
                            end if
                        end repeat
                        
                        if not alreadyMatched then
                            -- Only NOW do we fetch the body (expensive operation)
                            set noteBody to body of currentNote as string
                            set noteName to name of currentNote as string
                            
                            -- Check if any keyword matches body
                            set foundKeyword to ""
                            repeat with kw in keywords
                                set kwStr to kw as string
                                if noteBody contains kwStr then
                                    set foundKeyword to kwStr
                                    exit repeat
                                end if
                            end repeat
                            
                            if foundKeyword is not "" then
                                -- Get the folder name
                                set noteFolder to "Notes"
                                try
                                    set noteFolder to name of container of currentNote as string
                                on error
                                    set noteFolder to "Notes"
                                end try
                                
                                set outputLines to outputLines & {{noteName & "|||" & noteID & "|||" & noteFolder & "|||" & foundKeyword}}
                                set bodySearchCount to bodySearchCount + 1
                                set resultCount to resultCount + 1
                            end if
                        end if
                    end repeat
                end if
                
                set AppleScript's text item delimiters to return
                set outputText to outputLines as string
                set AppleScript's text item delimiters to ""
                return outputText
            on error errMsg
                return "error:iCloud account not available. Please enable iCloud Notes sync - " & errMsg
            end try
        end tell
        """

        # Use shorter timeout for search operations
        result = await SearchNotesOperations.execute_applescript(script, timeout=30)

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
