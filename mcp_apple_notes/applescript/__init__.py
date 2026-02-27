"""
AppleScript operations for Apple Notes integration.
"""

from .base_operations import BaseAppleScriptOperations
from .create_folder import CreateFolderOperations
from .create_note import CreateNoteOperations
from .delete_folder import DeleteFolderOperations
from .delete_note import DeleteNoteOperations
from .find_notes_by_date import FindNotesByDateOperations
from .find_notes_by_title import FindNotesByTitleOperations
from .folder_structure import FolderStructureOperations
from .list_notes import ListNotesOperations
from .move_folder import MoveFolderOperations
from .move_note import MoveNoteOperations
from .note_id_utils import NoteIDUtils
from .notes_structure import NotesStructureOperations
from .read_folder import ReadFolderOperations
from .read_note import ReadNoteOperations
from .rename_folder import RenameFolderOperations
from .search_notes import SearchNotesOperations
from .update_note import UpdateNoteOperations
from .validation_utils import ValidationUtils

__all__ = [
    "BaseAppleScriptOperations",
    "CreateNoteOperations",
    "CreateFolderOperations",
    "FindNotesByDateOperations",
    "FindNotesByTitleOperations",
    "ReadNoteOperations",
    "ReadFolderOperations",
    "DeleteFolderOperations",
    "RenameFolderOperations",
    "MoveFolderOperations",
    "FolderStructureOperations",
    "NotesStructureOperations",
    "UpdateNoteOperations",
    "DeleteNoteOperations",
    "ValidationUtils",
    "NoteIDUtils",
    "MoveNoteOperations",
    "ListNotesOperations",
    "SearchNotesOperations",
]
