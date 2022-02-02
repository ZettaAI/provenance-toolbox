"""Functions for storing useful information in CloudVolume provenance files

It takes significant effort to parse the result of an experiment in a
CloudVolume, and even more effort to remember what was parsed months
ago. Here, we define some simple tools to annotate volumes with a
set of "Notes" that describe the motivation for creating a volume,
the results of an experiment represented by such a volume, or other useful
information. These notes are automatically timestamped to aid interpretation.

Typical usage:

    inference = cv.CloudVolume(cloudpath)
    addmotivation(inference, "testing our segmentation of volume X")

    # Go do a lot of work inspecting the volume

    addresult(inference, "We still see a lot of problems with broken spines")
"""
from __future__ import annotations

import datetime
from enum import Enum
from typing import Optional, Union

import cloudvolume as cv


NOTE_SEP = ' \n '
FIELD_SEP = ';'


__all__ = ['parsenotes', 'note_absent',
           'addmotivation', 'addresult', 'addgeneric']


class NoteType(Enum):
    """An enumeration for classifying note objects.

    This is meant to be useful for visualization that's not implemented yet.
    """
    MOTIVATION = 1
    RESULT = 2
    GENERIC = 3


class Note:
    """A representation of a note added to a provenance file.

    Attributes:
        timestamp: An associated timestamp.
        note_type: A classification of the note's "type".
        content: The written content of the note.
    """
    def __init__(self,
                 timestamp: Union[datetime.datetime, str],
                 note_type: Union[NoteType, int],
                 content: str
                 ):
        """Initializes Notes.

        Attempts to convert the timestamp argument to datetime.datetime,
        and the note_type to a NoteType.

        Args:
            timestamp: An associated timestamp.
            note_type: A classification of the note's "type".
            content: The written content of the note.
        """
        if (timestamp is not None
                and not isinstance(timestamp, datetime.datetime)):
            timestamp = datetime.datetime.fromisoformat(timestamp)

        if not isinstance(note_type, NoteType):
            note_type = NoteType[note_type]

        self.timestamp = timestamp
        self.note_type = note_type
        self.content = content

    def __str__(self):
        """Converts a Note to a continuous string.

        This is used to pack notes within the 'description' field of provenance
        files. Separates the attributes using the field separator defined
        within the notebook module (FIELD_SEP).
        """
        return (f"{str(self.timestamp)}{FIELD_SEP}"
                f"{self.note_type.name}{FIELD_SEP}"
                f"{str(self.content)}")


def parsenotes(cloudvolume: cv.CloudVolume,
               note_sep: str = NOTE_SEP,
               field_sep: str = FIELD_SEP
               ) -> list[Note]:
    """Parses the notes present in a provenance file.

    Creates NoteType.GENERIC notes for text not added by this package (or using
    other separators, etc.).

    Args:
        cloudvolume: A CloudVolume.
        note_sep: The delimeter to use between notes within a provenance
                  file's description field. Defaults to notebook.NOTE_SEP.
        field_sep: The delimeter to use between fields of a note.

    Returns:
        A list of Notes capturing the contents of the current provenance
        description.
    """
    description = cloudvolume.provenance.description

    def hascontent(string: str) -> bool: return len(string) > 0

    possiblenotes = list(filter(hascontent, description.split(note_sep)))

    notes = list()
    for possiblenote in possiblenotes:
        try:
            notes.append(Note(*possiblenote.split(field_sep)))
        except ValueError as e:
            raise(e)
            notes.append(Note(None, NoteType.GENERIC, possiblenote))

    return notes


def addnote(cloudvolume: cv.CloudVolume,
            note_type: NoteType,
            content: str,
            timestamp: Optional[Union[datetime.datetime, str]] = None,
            note_sep: str = NOTE_SEP,
            field_sep: str = FIELD_SEP
            ) -> None:
    """Adds a note to a provenance file.

    This interface is more generic than the other module functions, as it can
    log all kinds of note types.

    Args:
        cloudvolume: A CloudVolume.
        note_type: The type of Note to add.
        content: The content of the note.
        timestamp: The timestamp to associate with the Note.
        note_sep: The delimeter to use between notes within a provenance
                  file's description field. Defaults to notebook.NOTE_SEP.
        field_sep: The delimeter to use between fields of a note.
    """
    timestamp = datetime.datetime.now() if timestamp is None else timestamp
    newnote = Note(timestamp, note_type, content)

    if len(parsenotes(cloudvolume, note_sep, field_sep)) != 0:
        cloudvolume.provenance.description += NOTE_SEP

    cloudvolume.provenance.description += str(newnote)

    cloudvolume.commit_provenance()


def addmotivation(cloudvolume: cv.CloudVolume,
                  content: str,
                  timestamp: Optional[Union[datetime.datetime, str]] = None,
                  note_sep: str = NOTE_SEP,
                  field_sep: str = FIELD_SEP
                  ) -> None:
    """Adds a motivation note to a provenance file.

    Args:
        cloudvolume: A CloudVolume.
        content: The content of the note.
        timestamp: The timestamp to associate with the Note.
        note_sep: The delimeter to use between notes within a provenance
                  file's description field. Defaults to notebook.NOTE_SEP.
        field_sep: The delimeter to use between fields of a note.
    """
    addnote(cloudvolume, NoteType.MOTIVATION, content,
            timestamp, note_sep, field_sep)


def addresult(cloudvolume: cv.CloudVolume,
              content: str,
              timestamp: Optional[Union[datetime.datetime, str]] = None,
              note_sep: str = NOTE_SEP,
              field_sep: str = FIELD_SEP
              ) -> None:
    """Adds a result note to a provenance file.

    Args:
        cloudvolume: A CloudVolume.
        content: The content of the note.
        timestamp: The timestamp to associate with the Note.
        note_sep: The delimeter to use between notes within a provenance
                  file's description field. Defaults to notebook.NOTE_SEP.
        field_sep: The delimeter to use between fields of a note.
    """
    addnote(cloudvolume, NoteType.RESULT, content,
            timestamp, note_sep, field_sep)


def addgeneric(cloudvolume: cv.CloudVolume,
               content: str,
               timestamp: Optional[Union[datetime.datetime, str]] = None,
               note_sep: str = NOTE_SEP,
               field_sep: str = FIELD_SEP
               ) -> None:
    """Adds a generic note to a provenance file.

    Args:
        cloudvolume: A CloudVolume.
        content: The content of the note.
        timestamp: The timestamp to associate with the Note.
        note_sep: The delimeter to use between notes within a provenance
                  file's description field. Defaults to notebook.NOTE_SEP.
        field_sep: The delimeter to use between fields of a note.
    """
    addnote(cloudvolume, NoteType.GENERIC, content,
            timestamp, note_sep, field_sep)


def note_absent(cloudvolume: cv.CloudVolume,
                content: str,
                note_type: Optional[NoteType] = None
                ) -> bool:
    """Checks whether a note is contained in a provenance file.

    Parses the provenance file for a given CloudVolume and determines
    whether a note has already been logged. Returns True if the note
    is absent.

    Args:
        cloudvolume: A CloudVolume.
        content: The content of the Note of interest.
        note_type: The Note's type.

    Returns:
        A bool describing whether or not the note is absent from
        the CloudVolume's provenance log.
    """
    notes = parsenotes(cloudvolume)

    def same_note(note1: Note,
                  content: str,
                  note_type: Optional[NoteType] = None
                  ) -> bool:
        return (note1.content == content
                and (note_type is not None and note1.note_type == note_type))

    filtered = [note for note in notes
                if same_note(note, content, note_type)]

    return len(filtered) == 0
