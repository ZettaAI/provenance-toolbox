'''
notebook.py

Lab notebook functions for storing useful information in
CloudVolume provenance files
'''
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
    MOTIVATION = 1
    RESULT = 2
    GENERIC = 3


class Note:
    'A representation of a note added to a provenance file'
    def __init__(self,
                 timestamp: Union[datetime.datetime, str],
                 note_type: Union[NoteType, int],
                 content: str
                 ):
        if (timestamp is not None
                and not isinstance(timestamp, datetime.datetime)):
            timestamp = datetime.datetime.fromisoformat(timestamp)

        if not isinstance(note_type, NoteType):
            note_type = NoteType[note_type]

        self.timestamp = timestamp
        self.note_type = note_type
        self.content = content

    def __str__(self):
        return (f"{str(self.timestamp)}{FIELD_SEP}"
                f"{self.note_type.name}{FIELD_SEP}"
                f"{str(self.content)}")


def parsenotes(cloudvolume: cv.CloudVolume,
               note_sep: str = NOTE_SEP,
               field_sep: str = FIELD_SEP
               ) -> list[Note]:
    '''
    Parses the notes present in a provenance file. Creates generic notes
    for text not added by this package (or using other separators, etc.).
    '''
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
    'Flexible interface for adding notes to a provenance file'
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
    'Adds a MOTIVATION note to a CloudVolume'
    addnote(cloudvolume, NoteType.MOTIVATION, content,
            timestamp, note_sep, field_sep)


def addresult(cloudvolume: cv.CloudVolume,
              content: str,
              timestamp: Optional[Union[datetime.datetime, str]] = None,
              note_sep: str = NOTE_SEP,
              field_sep: str = FIELD_SEP
              ) -> None:
    'Adds a RESULT note to a CloudVolume'
    addnote(cloudvolume, NoteType.RESULT, content,
            timestamp, note_sep, field_sep)


def addgeneric(cloudvolume: cv.CloudVolume,
               content: str,
               timestamp: Optional[Union[datetime.datetime, str]] = None,
               note_sep: str = NOTE_SEP,
               field_sep: str = FIELD_SEP
               ) -> None:
    'Adds a GENERIC note to a CloudVolume'
    addnote(cloudvolume, NoteType.GENERIC, content,
            timestamp, note_sep, field_sep)


def note_absent(cloudvolume: cv.CloudVolume,
                content: str,
                note_type: Optional[NoteType] = None
                ) -> bool:
    '''
    Checks whether a note has already been added to the description.
    Returns True if not.
    '''
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
